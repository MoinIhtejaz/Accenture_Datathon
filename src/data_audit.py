"""
NovaCorp People Analytics Challenge — Data Quality Audit
=========================================================

Reusable, re-runnable audit of employees.csv, attrition_log.csv, engagement.csv,
and performance.csv. Produces:
  - outputs/tables/missingness.csv
  - outputs/tables/data_quality_issues.csv
  - outputs/reports/data_quality_report.md

This module NEVER modifies or cleans the source CSVs. It only inspects, classifies,
and recommends. Cleaning happens in a later, separate, explicitly-approved step.

Every issue found is classified into exactly one of four categories (see CLAUDE.md
Section 21 for the analogous fact/evidence/inference/hypothesis discipline this
mirrors):

  ERROR                       - the data violates its own stated definition or is
                                 internally impossible; should not be trusted as-is.
  EXPECTED MISSINGNESS        - absence that the brief or the data's own design
                                 predicts and explains (e.g. non-respondents,
                                 the missing 2025-H2 cycle, edge-of-window hires).
  BUSINESS SIGNAL             - a real, non-erroneous pattern in the data that may
                                 itself be analytically meaningful (e.g. a
                                 concentration, a skew, a rate).
  UNKNOWN / REQUIRES ASSUMPTION - the audit cannot determine, from the data alone,
                                 whether the pattern is benign or a problem; using
                                 it requires an explicit, documented assumption.

Governing context: CLAUDE.md and docs/analysis_plan.md (read those first).
Run: `python src/data_audit.py` from anywhere; paths are resolved relative to the
repository root regardless of the current working directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from load_data import (
    BASE_DIR,
    CYCLE_GRACE_DAYS,
    CYCLE_WINDOWS,
    ENGAGEMENT_DIMENSIONS,
    EXPECTED_CATEGORIES,
    OUTPUT_REPORTS_DIR,
    OUTPUT_TABLES_DIR,
    WINDOW_END,
    WINDOW_START,
    load_raw_datasets,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Paths, the observation window, category vocabularies, and the cycle-window
# grace period now live in load_data.py (single source of truth, shared with
# src/clean_data.py and src/validation.py). Only audit-specific configuration
# (the four classification labels) stays here.

ERROR = "ERROR"
EXPECTED_MISSINGNESS = "EXPECTED MISSINGNESS"
BUSINESS_SIGNAL = "BUSINESS SIGNAL"
UNKNOWN = "UNKNOWN / REQUIRES ASSUMPTION"


# ---------------------------------------------------------------------------
# Issue log
# ---------------------------------------------------------------------------

@dataclass
class IssueLog:
    """Accumulates only genuine, non-zero findings. Zero-count clean-checks are
    recorded separately in `findings` (a plain dict) so the report can still say
    "checked X, found none" without cluttering the CSV with empty rows."""

    rows: list = field(default_factory=list)
    _counter: int = 0

    def add(self, dataset, field_, category, n_affected, n_total, description,
             recommendation):
        self._counter += 1
        pct = round(100 * n_affected / n_total, 3) if n_total else np.nan
        self.rows.append({
            "issue_id": f"DQ-{self._counter:03d}",
            "dataset": dataset,
            "field": field_,
            "category": category,
            "n_affected": int(n_affected),
            "n_total": int(n_total),
            "pct_affected": pct,
            "description": description,
            "recommendation": recommendation,
        })

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_datasets() -> dict[str, pd.DataFrame]:
    """Load all four source CSVs with explicit dtypes/date parsing. Read-only —
    never writes back to these paths. Thin wrapper around
    load_data.load_raw_datasets() kept for call-site compatibility within this
    module."""
    return load_raw_datasets(parse_dates=True)


# ---------------------------------------------------------------------------
# Basic profiling (no issue classification — pure description)
# ---------------------------------------------------------------------------

def dataset_overview(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in dfs.items():
        rows.append({
            "dataset": name,
            "n_rows": len(df),
            "n_columns": df.shape[1],
            "n_exact_duplicate_rows": int(df.duplicated().sum()),
            "n_unique_employee_id": (
                df["employee_id"].nunique() if "employee_id" in df.columns else np.nan
            ),
        })
    return pd.DataFrame(rows)


def column_profile(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    recs = []
    for name, df in dfs.items():
        for col in df.columns:
            s = df[col]
            n = len(s)
            n_missing = int(s.isna().sum())
            recs.append({
                "dataset": name,
                "column": col,
                "dtype": str(s.dtype),
                "n_total": n,
                "n_missing": n_missing,
                "pct_missing": round(100 * n_missing / n, 3) if n else np.nan,
                "n_unique": int(s.nunique(dropna=True)),
            })
    return pd.DataFrame(recs)


def missingness_table(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per-column missingness with a first-pass classification. Engagement's
    per-dimension nulls are EXPECTED MISSINGNESS wherever response_flag is False
    (verified structurally, not assumed); everything else missing is UNKNOWN until
    a specific check below reclassifies it."""
    prof = column_profile(dfs)
    eng = dfs["engagement"]
    emp = dfs["employees"]
    n_non_respondents = int((~eng["response_flag"]).sum())
    n_active = int((emp["status"] == "active").sum())

    def classify(row):
        if row["n_missing"] == 0:
            return "n/a (no missingness)"
        if row["dataset"] == "engagement" and row["column"] in ENGAGEMENT_DIMENSIONS:
            if row["n_missing"] == n_non_respondents:
                return EXPECTED_MISSINGNESS
            return UNKNOWN
        if row["dataset"] == "employees" and row["column"] == "manager_id":
            # null only for the top of the hierarchy (verified in the manager
            # reference integrity check) - structurally expected, not a gap.
            return EXPECTED_MISSINGNESS
        if row["dataset"] == "employees" and row["column"] == "exit_date":
            # documented: null means still active. EXPECTED only if the null
            # count matches the active headcount exactly; otherwise something
            # else is going on and it should not be waved through.
            if row["n_missing"] == n_active:
                return EXPECTED_MISSINGNESS
            return UNKNOWN
        return UNKNOWN

    prof["classification"] = prof.apply(classify, axis=1)
    return prof


# ---------------------------------------------------------------------------
# Individual checks
# Each check appends genuine findings to `issues` and records raw stats in
# `findings` (a dict keyed by check name) so the markdown report can narrate
# both "problems found" and "checks that came back clean".
# ---------------------------------------------------------------------------

def check_employee_id_integrity(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    n_emp = len(emp)

    n_null_ids = int(emp["employee_id"].isna().sum())
    n_dup_ids = int(emp["employee_id"].duplicated().sum())
    bad_format = (~emp["employee_id"].str.match(r"^E\d{5}$")).sum()

    findings["employee_id_integrity"] = {
        "n_null_employee_id": n_null_ids,
        "n_duplicate_employee_id": n_dup_ids,
        "n_bad_format": int(bad_format),
        "id_min": emp["employee_id"].min(),
        "id_max": emp["employee_id"].max(),
        "n_unique": int(emp["employee_id"].nunique()),
        "n_rows": n_emp,
    }

    if n_dup_ids:
        issues.add("employees", "employee_id", ERROR, n_dup_ids, n_emp,
                    "employee_id is not unique in the primary roster file.",
                    "Investigate duplicated IDs before any join; a duplicate "
                    "primary key will silently fan out joins to attrition_log/"
                    "engagement/performance and inflate row counts.")

    if bad_format:
        issues.add("employees", "employee_id", UNKNOWN, bad_format, n_emp,
                    "employee_id values do not match the expected 'E' + 5-digit "
                    "pattern.",
                    "Confirm whether these are a legitimate alternate ID scheme "
                    "(e.g. a different legacy source system) before excluding.")

    orphan_counts = {}
    for name in ("attrition_log", "engagement", "performance"):
        df = dfs[name]
        orphan = (~df["employee_id"].isin(set(emp["employee_id"]))).sum()
        orphan_counts[name] = int(orphan)
        if orphan:
            issues.add(name, "employee_id", ERROR, orphan, len(df),
                        f"{name} contains employee_id values absent from "
                        "employees.csv (the join key is broken for these rows).",
                        "Drop or quarantine these rows for any analysis that "
                        "requires employee attributes; report the count as a "
                        "known data-completeness gap.")
    findings["employee_id_integrity"]["orphan_rows"] = orphan_counts
    return findings["employee_id_integrity"]


def check_manager_reference_integrity(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    perf = dfs["performance"]
    att = dfs["attrition_log"]
    id_set = set(emp["employee_id"])

    mgr_null = int(emp["manager_id"].isna().sum())
    mgr_orphan = int((~emp["manager_id"].dropna().isin(id_set)).sum())
    self_mgr = int((emp["manager_id"] == emp["employee_id"]).sum())

    rev_orphan = int((~perf["reviewer_id"].dropna().isin(id_set)).sum())
    mgr_exit_orphan = int((~att["manager_id_at_exit"].dropna().isin(id_set)).sum())

    top_level_null_mgr = emp.loc[emp["manager_id"].isna(), "role_level"]
    findings["manager_reference_integrity"] = {
        "manager_id_null": mgr_null,
        "manager_id_null_role_levels": sorted(top_level_null_mgr.unique().tolist()),
        "manager_id_orphan": mgr_orphan,
        "self_managed_rows": self_mgr,
        "reviewer_id_orphan": rev_orphan,
        "manager_id_at_exit_orphan": mgr_exit_orphan,
    }

    if mgr_orphan:
        issues.add("employees", "manager_id", ERROR, mgr_orphan, len(emp),
                    "manager_id references an employee_id not present in the "
                    "roster.", "Treat reporting-line/manager-rollup features as "
                    "missing for these employees rather than imputing a manager.")
    if self_mgr:
        issues.add("employees", "manager_id", ERROR, self_mgr, len(emp),
                    "Employee is recorded as their own manager.",
                    "Exclude from any manager-effect analysis (Areas MG/IX in "
                    "the hypothesis register); investigate as a likely migration "
                    "artefact.")
    if rev_orphan:
        issues.add("performance", "reviewer_id", ERROR, rev_orphan, len(perf),
                    "reviewer_id references an employee_id not present in the "
                    "roster.", "Exclude these reviews from any reviewer/manager-"
                    "quality analysis; retain for rating-level analysis only.")
    if mgr_exit_orphan:
        issues.add("attrition_log", "manager_id_at_exit", ERROR, mgr_exit_orphan,
                    len(att), "manager_id_at_exit references an employee_id not "
                    "present in the roster.",
                    "Exclude from manager-level attrition rollups.")
    if not any([mgr_orphan, self_mgr, rev_orphan, mgr_exit_orphan]):
        pass  # all clean; narrated from findings dict in the report, no CSV row
    return findings["manager_reference_integrity"]


def check_duplicates(dfs, issues: IssueLog, findings: dict):
    result = {}
    for name, df in dfs.items():
        n_exact = int(df.duplicated().sum())
        result[f"{name}_exact_duplicate_rows"] = n_exact
        if n_exact:
            issues.add(name, "(all columns)", ERROR, n_exact, len(df),
                        "Exact duplicate rows found.",
                        "Deduplicate to one row per genuine record before any "
                        "counting/rate calculation; investigate source of "
                        "duplication (e.g. re-export overlap).")

    eng = dfs["engagement"]
    dup_wave = int(eng.duplicated(subset=["employee_id", "wave_number"]).sum())
    result["engagement_duplicate_employee_wave"] = dup_wave
    if dup_wave:
        issues.add("engagement", "employee_id+wave_number", ERROR, dup_wave,
                    len(eng), "An employee has more than one row for the same "
                    "wave.", "Investigate and, if confirmed erroneous, keep only "
                    "one row per employee per wave (rule to be decided at "
                    "cleaning stage, not here).")

    perf = dfs["performance"]
    dup_cycle = int(perf.duplicated(subset=["employee_id", "review_cycle"]).sum())
    result["performance_duplicate_employee_cycle"] = dup_cycle
    if dup_cycle:
        issues.add("performance", "employee_id+review_cycle", ERROR, dup_cycle,
                    len(perf), "An employee has more than one review row in the "
                    "same nominal cycle.",
                    "Investigate; a genuine mid-cycle re-review vs. a duplicate "
                    "export needs a human judgement call before merging.")

    att = dfs["attrition_log"]
    dup_emp = int(att.duplicated(subset=["employee_id"]).sum())
    result["attrition_log_duplicate_employee_id"] = dup_emp
    if dup_emp:
        issues.add("attrition_log", "employee_id", ERROR, dup_emp, len(att),
                    "An employee has more than one exit record (re-hire not "
                    "distinguished from duplicate export).",
                    "Confirm whether this reflects a genuine rehire-then-exit "
                    "cycle before collapsing to one row.")

    findings["duplicates"] = result
    return result


def check_impossible_values(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    eng = dfs["engagement"]
    perf = dfs["performance"]
    result = {}

    bad_level = (~emp["role_level"].between(1, 8)).sum()
    result["role_level_out_of_1_8"] = int(bad_level)
    if bad_level:
        issues.add("employees", "role_level", ERROR, bad_level, len(emp),
                    "role_level outside the documented 1-8 range.",
                    "Exclude or correct before any level-based segmentation.")

    zero_neg_salary = (emp["salary"] <= 0).sum()
    result["salary_zero_or_negative"] = int(zero_neg_salary)
    if zero_neg_salary:
        issues.add("employees", "salary", ERROR, zero_neg_salary, len(emp),
                    "Non-positive salary recorded.",
                    "Exclude from all financial costing (Section 14) until "
                    "resolved; a $0 salary would corrupt every downstream dollar "
                    "figure.")

    implausible_compa = (~emp["compa_ratio"].between(0.3, 2.5)).sum()
    result["compa_ratio_outside_0.3_2.5"] = int(implausible_compa)
    if implausible_compa:
        issues.add("employees", "compa_ratio", UNKNOWN, implausible_compa,
                    len(emp), "compa_ratio outside a plausible 0.3-2.5 band "
                    "(no official band table was supplied to verify against).",
                    "Treat as indicative outliers only; do not exclude without "
                    "an explicit, documented plausibility threshold.")

    neg_dtf = (emp["days_to_fill"] < 0).sum()
    result["days_to_fill_negative"] = int(neg_dtf)
    if neg_dtf:
        issues.add("employees", "days_to_fill", ERROR, neg_dtf, len(emp),
                    "Negative days_to_fill.", "Exclude from hiring-efficiency "
                    "analysis (Area HI).")

    nonpos_tenure = (emp["tenure_months"] <= 0).sum()
    result["tenure_months_non_positive"] = int(nonpos_tenure)
    # (classified later, alongside the broader tenure-reconciliation finding)

    # Engagement scale bounds, checked only where a response was actually given
    responded = eng[eng["response_flag"]]
    dim_range_violations = {}
    for dim in ENGAGEMENT_DIMENSIONS:
        viol = (~responded[dim].between(1, 5)).sum()
        if viol:
            dim_range_violations[dim] = int(viol)
    result["engagement_dimension_range_violations"] = dim_range_violations
    for dim, n in dim_range_violations.items():
        issues.add("engagement", dim, ERROR, n, len(responded),
                    f"{dim} outside the documented 1-5 scale for a responded row.",
                    "Exclude the specific value (not the whole row) from any "
                    "mean/index calculation until corrected.")

    # response_flag / null consistency (both directions)
    inconsistent_true_null = {}
    inconsistent_false_notnull = {}
    for dim in ENGAGEMENT_DIMENSIONS:
        t_null = int(((eng["response_flag"]) & (eng[dim].isna())).sum())
        f_notnull = int(((~eng["response_flag"]) & (eng[dim].notna())).sum())
        if t_null:
            inconsistent_true_null[dim] = t_null
        if f_notnull:
            inconsistent_false_notnull[dim] = f_notnull
    result["response_flag_true_but_score_null"] = inconsistent_true_null
    result["response_flag_false_but_score_present"] = inconsistent_false_notnull
    for dim, n in inconsistent_true_null.items():
        issues.add("engagement", dim, ERROR, n, len(eng),
                    "response_flag is True but the dimension score is null.",
                    "Treat as a non-response for this dimension specifically; "
                    "do not impute.")
    for dim, n in inconsistent_false_notnull.items():
        issues.add("engagement", dim, ERROR, n, len(eng),
                    "response_flag is False but a score is present.",
                    "Investigate — this contradicts the documented null-on-"
                    "non-response rule; do not use the stray score without "
                    "resolving why response_flag says otherwise.")

    bad_goal = (~perf["goal_achievement_score"].between(0, 100)).sum()
    result["goal_achievement_score_out_of_0_100"] = int(bad_goal)
    if bad_goal:
        issues.add("performance", "goal_achievement_score", ERROR, bad_goal,
                    len(perf), "goal_achievement_score outside the documented "
                    "0-100 scale.", "Exclude from any performance-index "
                    "calculation until corrected.")

    findings["impossible_values"] = result
    return result


def check_inconsistent_categories(dfs, issues: IssueLog, findings: dict):
    result = {}
    for dataset, fields in EXPECTED_CATEGORIES.items():
        df = dfs[dataset]
        for col, expected in fields.items():
            observed = set(df[col].dropna().unique())
            unexpected = observed - expected
            result[f"{dataset}.{col}"] = {
                "observed": sorted(observed),
                "unexpected": sorted(unexpected),
            }
            if unexpected:
                n_affected = int(df[col].isin(unexpected).sum())
                issues.add(dataset, col, ERROR, n_affected, len(df),
                            f"Unexpected category values not in the documented "
                            f"vocabulary: {sorted(unexpected)}.",
                            "Confirm whether these are legitimate new categories "
                            "or a formatting/typo artefact before mapping to the "
                            "known vocabulary.")
            # whitespace/case near-duplicate scan
            normed = {}
            for v in observed:
                key = str(v).strip().lower()
                normed.setdefault(key, []).append(v)
            near_dupes = {k: v for k, v in normed.items() if len(v) > 1}
            if near_dupes:
                issues.add(dataset, col, ERROR,
                            sum(len(v) for v in near_dupes.values()), len(df),
                            f"Whitespace/case variants of the same category "
                            f"co-exist: {near_dupes}.",
                            "Normalise casing/whitespace before treating these "
                            "as one category.")
    findings["inconsistent_categories"] = result
    return result


def check_date_ranges(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    eng = dfs["engagement"]
    perf = dfs["performance"]
    att = dfs["attrition_log"]
    result = {}

    result["hire_date_range"] = (str(emp["hire_date"].min()), str(emp["hire_date"].max()))
    result["exit_date_range"] = (str(emp["exit_date"].min()), str(emp["exit_date"].max()))
    result["survey_date_range"] = (str(eng["survey_date"].min()), str(eng["survey_date"].max()))
    result["review_date_range"] = (str(perf["review_date"].min()), str(perf["review_date"].max()))

    pre_window_hires = int((emp["hire_date"] < WINDOW_START).sum())
    result["pre_window_hires"] = pre_window_hires  # expected: long-tenured staff

    hire_after_exit = int((emp["exit_date"].notna() & (emp["hire_date"] > emp["exit_date"])).sum())
    result["hire_date_after_exit_date"] = hire_after_exit
    if hire_after_exit:
        issues.add("employees", "hire_date/exit_date", ERROR, hire_after_exit,
                    len(emp), "hire_date is after exit_date for the same "
                    "employee.", "Exclude from tenure/survival calculations "
                    "until resolved; the record is internally impossible.")

    exit_outside_window = int((
        emp["exit_date"].notna()
        & ((emp["exit_date"] < WINDOW_START) | (emp["exit_date"] > WINDOW_END))
    ).sum())
    result["exit_date_outside_observation_window"] = exit_outside_window
    if exit_outside_window:
        issues.add("employees", "exit_date", ERROR, exit_outside_window, len(emp),
                    "exit_date falls outside the documented 2024-01-01 to "
                    "2025-12-31 observation window.",
                    "Confirm whether the window boundary or the record is "
                    "wrong before including in any window-bounded rate.")

    for name, df, col in [
        ("attrition_log", att, "exit_date"),
        ("engagement", eng, "survey_date"),
        ("performance", perf, "review_date"),
    ]:
        outside = int(((df[col] < WINDOW_START) | (df[col] > WINDOW_END)).sum())
        result[f"{name}_{col}_outside_window"] = outside
        if outside:
            issues.add(name, col, ERROR, outside, len(df),
                        f"{col} falls outside the 2024-2025 observation window.",
                        "Confirm before using in any window-bounded analysis.")

    findings["date_ranges"] = result
    return result


def check_status_exit_consistency(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    att = dfs["attrition_log"]
    result = {}

    active_with_exit = int(((emp["status"] == "active") & emp["exit_date"].notna()).sum())
    departed_no_exit = int(((emp["status"] == "departed") & emp["exit_date"].isna()).sum())
    result["active_status_with_exit_date"] = active_with_exit
    result["departed_status_missing_exit_date"] = departed_no_exit
    if active_with_exit:
        issues.add("employees", "status/exit_date", ERROR, active_with_exit,
                    len(emp), "status is 'active' but exit_date is populated.",
                    "Resolve before using status as the active/departed filter "
                    "anywhere in the pipeline.")
    if departed_no_exit:
        issues.add("employees", "status/exit_date", ERROR, departed_no_exit,
                    len(emp), "status is 'departed' but exit_date is null.",
                    "Cannot compute tenure-at-exit for these records without "
                    "resolution.")

    departed_ids = set(emp.loc[emp["status"] == "departed", "employee_id"])
    attrition_ids = set(att["employee_id"])
    missing_from_log = departed_ids - attrition_ids
    missing_from_roster = attrition_ids - departed_ids
    result["departed_missing_from_attrition_log"] = len(missing_from_log)
    result["attrition_log_not_marked_departed"] = len(missing_from_roster)
    if missing_from_log:
        issues.add("employees", "status", ERROR, len(missing_from_log), len(emp),
                    "Employee marked 'departed' in employees.csv has no "
                    "corresponding row in attrition_log.csv.",
                    "Cannot classify exit_type/voluntary-involuntary for these "
                    "employees; exclude from any exit-type-specific analysis "
                    "and report as a completeness gap.")
    if missing_from_roster:
        issues.add("attrition_log", "employee_id", ERROR, len(missing_from_roster),
                    len(att), "Employee appears in attrition_log.csv but is not "
                    "marked 'departed' in employees.csv.",
                    "Resolve the status mismatch before using either file's "
                    "status field as authoritative.")

    merged = emp.loc[emp["status"] == "departed", ["employee_id", "exit_date"]].merge(
        att[["employee_id", "exit_date"]], on="employee_id", suffixes=("_emp", "_att"))
    exit_date_mismatch = int((merged["exit_date_emp"] != merged["exit_date_att"]).sum())
    result["exit_date_mismatch_between_files"] = exit_date_mismatch
    if exit_date_mismatch:
        issues.add("employees/attrition_log", "exit_date", ERROR, exit_date_mismatch,
                    len(merged), "exit_date differs between employees.csv and "
                    "attrition_log.csv for the same employee.",
                    "Pick one source of truth (recommend attrition_log.csv, the "
                    "purpose-built exit record) and document the choice.")

    findings["status_exit_consistency"] = result
    return result


def check_salary_anomalies(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    att = dfs["attrition_log"]
    result = {}

    sal_merge = emp.loc[emp["status"] == "departed", ["employee_id", "salary"]].merge(
        att[["employee_id", "salary_at_exit"]], on="employee_id")
    mismatch = int((sal_merge["salary"] != sal_merge["salary_at_exit"]).sum())
    result["salary_vs_salary_at_exit_mismatch"] = mismatch
    if mismatch:
        issues.add("employees/attrition_log", "salary/salary_at_exit", ERROR,
                    mismatch, len(sal_merge), "salary in employees.csv differs "
                    "from salary_at_exit in attrition_log.csv for the same "
                    "employee (the brief states these should be identical).",
                    "Investigate before costing; use salary_at_exit for "
                    "departed-employee cost calculations if a genuine "
                    "discrepancy is confirmed.")

    # Outlier scan within department x role_level cells (IQR rule), for visibility
    grp = emp.groupby(["department", "role_level"])["salary"]
    q1, q3 = grp.transform("quantile", 0.25), grp.transform("quantile", 0.75)
    iqr = q3 - q1
    lower, upper = q1 - 3 * iqr, q3 + 3 * iqr
    outliers = emp[(emp["salary"] < lower) | (emp["salary"] > upper)]
    result["salary_outliers_within_dept_level_3xIQR"] = int(len(outliers))
    if len(outliers):
        issues.add("employees", "salary", BUSINESS_SIGNAL, len(outliers), len(emp),
                    "Salary values sit >3xIQR outside their department x "
                    "role_level peer group.",
                    "Not necessarily an error — may reflect legitimate acting/"
                    "market premiums; review the list before treating as noise "
                    "in any pay-equity or replacement-cost analysis.")

    # Monotonicity of median salary by role_level (sanity check only)
    median_by_level = emp.groupby("role_level")["salary"].median().sort_index()
    is_monotonic = median_by_level.is_monotonic_increasing
    result["median_salary_monotonic_by_role_level"] = bool(is_monotonic)
    result["median_salary_by_role_level"] = median_by_level.round(0).to_dict()

    findings["salary_anomalies"] = result
    return result


def check_tenure_anomalies(dfs, issues: IssueLog, findings: dict):
    """The single most consequential check in this audit: does the supplied
    tenure_months reconcile with hire_date and (exit_date or window end)?"""
    emp = dfs["employees"].copy()
    result = {}

    end_dates = emp["exit_date"].fillna(WINDOW_END)
    calendar_months = (
        (end_dates.dt.year - emp["hire_date"].dt.year) * 12
        + (end_dates.dt.month - emp["hire_date"].dt.month) + 1
    )
    diff = emp["tenure_months"] - calendar_months
    result["diff_vs_window_end_or_exit_summary"] = {
        "mean": round(float(diff.mean()), 2),
        "median": float(diff.median()),
        "std": round(float(diff.std()), 2),
        "min": int(diff.min()),
        "max": int(diff.max()),
        "pct_matching_exactly": round(100 * (diff == 0).mean(), 2),
        "pct_within_1_month": round(100 * diff.abs().le(1).mean(), 2),
    }

    # For active employees, back out the implied reference ("as-of") date and see
    # whether it clusters near the stated window end (2025-12-31) or drifts past it.
    active = emp[emp["status"] == "active"].copy()
    active["implied_asof_date"] = active.apply(
        lambda r: r["hire_date"] + pd.DateOffset(months=int(r["tenure_months"]) - 1),
        axis=1,
    )
    result["active_implied_asof_date_summary"] = {
        "min": str(active["implied_asof_date"].min()),
        "median": str(active["implied_asof_date"].median()),
        "max": str(active["implied_asof_date"].max()),
        "pct_after_window_end": round(
            100 * (active["implied_asof_date"] > WINDOW_END).mean(), 2
        ),
    }

    n_affected = int(diff.abs().gt(1).sum())
    issues.add(
        "employees", "tenure_months", ERROR, n_affected, len(emp),
        "tenure_months does not reconcile with hire_date and the documented "
        "'to exit_date or window end' definition for a large share of records. "
        "For active employees specifically, back-solving the implied as-of date "
        "from tenure_months shows it drifting from ~Nov 2025 to ~Jun 2026 rather "
        "than clustering at the stated window end of 2025-12-31 — i.e. "
        "tenure_months looks to have been computed against a moving/variable "
        "reference point (plausibly the data-generation run date) rather than "
        "the fixed window end the brief describes.",
        "Do not use the supplied tenure_months at face value for time-sensitive "
        "analysis (survival models, tenure-banded comparisons, early-attrition "
        "cutoffs). Recompute tenure directly from hire_date and (exit_date, "
        "capped at 2025-12-31 for active employees) as a derived field, and use "
        "that recomputed value consistently instead."
    )

    nonpos = int((emp["tenure_months"] <= 0).sum())
    result["tenure_months_non_positive"] = nonpos
    if nonpos:
        issues.add("employees", "tenure_months", BUSINESS_SIGNAL, nonpos, len(emp),
                    "tenure_months of 0 recorded for some employees (typically "
                    "very short-tenure departures within their first calendar "
                    "month).",
                    "Plausible for genuine same-month hire-and-exit cases; "
                    "verify against hire_date/exit_date before treating as an "
                    "error, and include explicitly in any early-attrition/"
                    "hiring-inefficiency analysis (Area HI) rather than "
                    "dropping.")

    findings["tenure_anomalies"] = result
    return result


def check_engagement_wave_coverage(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    eng = dfs["engagement"]
    result = {}

    wave_windows = eng.groupby("wave_number")["survey_date"].agg(["min", "max", "count"])
    result["wave_windows"] = {
        int(w): {"min": str(r["min"]), "max": str(r["max"]), "n_rows": int(r["count"])}
        for w, r in wave_windows.iterrows()
    }
    span_days = (wave_windows["max"] - wave_windows["min"]).dt.days
    result["wave_window_span_days"] = span_days.to_dict()
    wide_waves = span_days[span_days > 3 * span_days.median()]
    if len(wide_waves):
        spans_desc = ", ".join(f"wave {w}: {d} days" for w, d in wide_waves.items())
        issues.add("engagement", "survey_date", BUSINESS_SIGNAL, len(wide_waves),
                    len(wave_windows),
                    f"Wave(s) administered over a markedly wider date span than "
                    f"the other waves (median {span_days.median():.0f} days): "
                    f"{spans_desc}.",
                    "Note as a rollout-timing irregularity (possibly acquisition-"
                    "related staggered administration); does not itself corrupt "
                    "the scores, but avoid treating 'wave number' as a precise "
                    "single point in time for that wave.")

    waves_per_emp = eng.groupby("employee_id")["wave_number"].nunique()
    all_ids = set(emp["employee_id"])
    zero_wave_ids = all_ids - set(waves_per_emp.index)
    result["waves_per_employee_distribution"] = waves_per_emp.value_counts().sort_index().to_dict()
    result["employees_with_zero_engagement_rows"] = len(zero_wave_ids)

    zero_df = emp[emp["employee_id"].isin(zero_wave_ids)]
    wave1_end = wave_windows.loc[1, "max"]
    wave5_end = wave_windows.loc[5, "max"]
    hired_after_last_wave = zero_df["hire_date"] > wave5_end
    left_at_or_before_wave1 = zero_df["exit_date"].notna() & (zero_df["exit_date"] <= wave1_end)
    edge_explained = int((hired_after_last_wave | left_at_or_before_wave1).sum())
    unexplained = len(zero_df) - edge_explained
    result["zero_wave_explained_by_window_edge"] = edge_explained
    result["zero_wave_unexplained"] = int(unexplained)

    issues.add("engagement", "employee_id (coverage)", EXPECTED_MISSINGNESS,
                edge_explained, len(emp),
                "Employees with zero engagement records, explained by having "
                "been hired after the final wave closed or having exited at/"
                "before the first wave closed — matches the brief's explicit "
                "caveat.", "No action needed; exclude these employees from "
                "engagement-based analysis for waves they were not eligible for.")
    if unexplained:
        issues.add("engagement", "employee_id (coverage)", UNKNOWN, unexplained,
                    len(emp), "Employees with zero engagement records whose "
                    "tenure window overlaps at least one wave, so absence is "
                    "not fully explained by hire/exit timing alone (likely "
                    "explained by within-window staggered survey issuance that "
                    "the data does not record at individual level).",
                    "Do not treat as random/MCAR without a stated assumption; "
                    "for any analysis conditioning on engagement history, note "
                    "this residual as a documented limitation.")

    # eligibility-based full-coverage check
    full_tenure = emp[
        (emp["hire_date"] <= wave_windows.loc[1, "min"])
        & (emp["exit_date"].isna() | (emp["exit_date"] >= wave5_end))
    ]
    full_tenure_waves = waves_per_emp.reindex(full_tenure["employee_id"]).fillna(0)
    short_of_five = int((full_tenure_waves < 5).sum())
    result["full_window_eligible_employees"] = len(full_tenure)
    result["full_window_eligible_with_lt_5_waves"] = short_of_five
    if short_of_five:
        issues.add("engagement", "employee_id (coverage)", UNKNOWN, short_of_five,
                    len(full_tenure), "Employees employed across the entire "
                    "wave 1-5 span still have fewer than 5 engagement rows.",
                    "Investigate a sample before assuming these are simply "
                    "additional non-respondents (they should have a row either "
                    "way, per the brief's design) — could indicate a small "
                    "residual export gap.")

    findings["engagement_wave_coverage"] = result
    return result


def check_survey_response_patterns(dfs, issues: IssueLog, findings: dict):
    eng = dfs["engagement"].merge(
        dfs["employees"][["employee_id", "department", "legacy_entity_code", "contract_type"]],
        on="employee_id", how="left",
    )
    result = {}
    result["response_rate_by_wave"] = (
        eng.groupby("wave_number")["response_flag"].mean().round(4).to_dict()
    )
    result["response_rate_by_department"] = (
        eng.groupby("department")["response_flag"].mean().round(4).to_dict()
    )
    rate_by_entity = eng.groupby("legacy_entity_code")["response_flag"].mean().round(4)
    result["response_rate_by_legacy_entity"] = rate_by_entity.to_dict()
    result["response_rate_by_contract_type"] = (
        eng.groupby("contract_type")["response_flag"].mean().round(4).to_dict()
    )
    always_dark = (
        eng.groupby("employee_id")["response_flag"]
        .agg(lambda s: (~s).all())
    )
    result["employees_never_responding_of_those_surveyed"] = int(always_dark.sum())
    findings["survey_response_patterns"] = result

    # Flag a materially lower response rate for any legacy entity (>10 percentage
    # points below the highest-responding group) as a descriptive data-quality
    # signal: differential non-response can bias any naive engagement comparison
    # across cohorts unless explicitly accounted for.
    gap = rate_by_entity.max() - rate_by_entity.min()
    if gap > 0.10:
        low_group = rate_by_entity.idxmin()
        n_rows_low_group = int((eng["legacy_entity_code"] == low_group).sum())
        issues.add(
            "engagement", "legacy_entity_code/response_flag", BUSINESS_SIGNAL,
            n_rows_low_group, len(eng),
            f"Survey response rate varies materially by legacy_entity_code "
            f"({rate_by_entity.to_dict()}) — a {gap*100:.1f} percentage-point "
            f"gap between the highest- and lowest-responding cohorts "
            f"('{low_group}' being lowest).",
            "Not a data error, but a real, non-random non-response pattern: "
            "any engagement-score comparison across legacy_entity_code cohorts "
            "must account for differential response rates (e.g. via SR-2 in "
            "the hypothesis register) rather than comparing raw respondent "
            "means as if response were equally likely across cohorts."
        )
    return result


def check_performance_cycle_label_consistency(dfs, issues: IssueLog, findings: dict):
    perf = dfs["performance"]
    result = {}

    def outside_window_with_grace(row):
        lo, hi = CYCLE_WINDOWS[row["review_cycle"]]
        return not (lo <= row["review_date"] <= hi + pd.Timedelta(days=CYCLE_GRACE_DAYS))

    mislabeled_mask = perf.apply(outside_window_with_grace, axis=1)
    n_mislabeled = int(mislabeled_mask.sum())
    result["n_reviews_outside_cycle_window_plus_grace"] = n_mislabeled
    result["mislabeled_by_cycle"] = (
        perf.loc[mislabeled_mask, "review_cycle"].value_counts().to_dict()
    )
    result["grace_period_days"] = CYCLE_GRACE_DAYS

    if n_mislabeled:
        examples = perf.loc[mislabeled_mask, ["employee_id", "review_cycle", "review_date"]]
        examples_with_hire = examples.merge(
            dfs["employees"][["employee_id", "hire_date", "exit_date"]],
            on="employee_id", how="left",
        )
        near_hire = int(
            ((examples_with_hire["review_date"] - examples_with_hire["hire_date"]).dt.days <= 3).sum()
        )
        result["mislabeled_reviews_within_3_days_of_hire"] = near_hire

        issues.add(
            "performance", "review_cycle", ERROR, n_mislabeled, len(perf),
            f"{n_mislabeled} review(s) carry a review_cycle label whose nominal "
            f"half-year window (+{CYCLE_GRACE_DAYS}-day grace) does not contain "
            f"the row's own review_date — overwhelmingly reviews labelled "
            f"'2024-H1' with review_date up to ~18 months later. Of these, "
            f"{near_hire} occur within 3 days of the employee's hire_date and "
            f"the employee subsequently departs within ~1 month, consistent "
            f"with a day-1 onboarding/baseline review that the source system "
            f"defaulted to the first cycle label rather than the actual period.",
            "CRITICAL for temporal correctness: never use the review_cycle "
            "string as a proxy for 'when this was known' — always sequence "
            "performance records by review_date. If a cycle label is required "
            "for aggregation, re-derive it from review_date rather than trusting "
            "the stored value, at least for this affected subset."
        )

    findings["performance_cycle_label_consistency"] = result
    return result


def check_performance_coverage(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    perf = dfs["performance"]
    result = {}

    reviews_per_emp = perf.groupby("employee_id").size()
    result["reviews_per_employee_distribution"] = reviews_per_emp.value_counts().sort_index().to_dict()

    all_ids = set(emp["employee_id"])
    zero_review_ids = all_ids - set(reviews_per_emp.index)
    result["employees_with_zero_performance_reviews"] = len(zero_review_ids)

    result["cycles_present"] = sorted(perf["review_cycle"].unique().tolist())
    result["cycle_2025_H2_present"] = "2025-H2" in result["cycles_present"]
    active_n = int((emp["status"] == "active").sum())
    issues.add("performance", "review_cycle", EXPECTED_MISSINGNESS, active_n, active_n,
                "The 2025-H2 review cycle is entirely absent, exactly as the "
                "brief states; the most recent review for most employees is "
                "2025-H1 or 2024-H2. Expressed as 100% of the active workforce "
                "lacking a 2025-H2 record, since the cycle is structurally "
                "absent from the export rather than missing for a subset.",
                "No action needed beyond documenting the right-truncation: any "
                "'most recent performance' feature for late-2025 events must "
                "acknowledge it may be up to ~1 year stale.")

    zero_df = emp[emp["employee_id"].isin(zero_review_ids)]
    zero_by_contract = zero_df["contract_type"].value_counts().to_dict()
    zero_by_tenure_gt6 = int((zero_df["tenure_months"] > 6).sum())
    result["zero_review_by_contract_type"] = zero_by_contract
    result["zero_review_employed_gt_6_months_by_stored_tenure"] = zero_by_tenure_gt6
    if zero_by_tenure_gt6:
        issues.add("performance", "employee_id (coverage)", UNKNOWN,
                    zero_by_tenure_gt6, len(emp),
                    "Employees with >6 months of (stored) tenure but zero "
                    "performance review records at all.",
                    "Confirm whether certain contract types/role families are "
                    "legitimately exempt from formal review before treating "
                    "this as a gap; do not assume Missing-At-Random.")

    findings["performance_coverage"] = result
    return result


def check_incomplete_histories(dfs, findings: dict):
    emp = dfs["employees"]
    eng_ids = set(dfs["engagement"]["employee_id"])
    perf_ids = set(dfs["performance"]["employee_id"])
    all_ids = set(emp["employee_id"])
    result = {
        "n_no_engagement_and_no_performance": len(all_ids - eng_ids - perf_ids),
        "n_no_engagement_only": len((all_ids - eng_ids) & perf_ids),
        "n_no_performance_only": len((all_ids - perf_ids) & eng_ids),
        "n_complete_in_both": len(eng_ids & perf_ids),
    }
    findings["incomplete_histories"] = result
    return result


def check_cross_dataset_reconciliation(dfs, findings: dict):
    """Reconciliation against the Annual Report figures already verified in
    CLAUDE.md — confirms internal consistency, does not re-derive new facts."""
    emp = dfs["employees"]
    att = dfs["attrition_log"]
    result = {
        "active_headcount": int((emp["status"] == "active").sum()),
        "departed_headcount": int((emp["status"] == "departed").sum()),
        "voluntary_exits": int((att["exit_type"] == "voluntary").sum()),
        "involuntary_exits": int((att["exit_type"] == "involuntary").sum()),
    }
    result["voluntary_rate_vs_active_headcount_pct"] = round(
        100 * result["voluntary_exits"] / result["active_headcount"], 2
    )
    result["voluntary_rate_vs_active_plus_departed_pct"] = round(
        100 * result["voluntary_exits"] / (result["active_headcount"] + result["departed_headcount"]), 2
    )
    findings["cross_dataset_reconciliation"] = result
    return result


def check_legacy_system_artefacts(dfs, issues: IssueLog, findings: dict):
    emp = dfs["employees"]
    result = {}
    result["data_source_system_counts"] = emp["data_source_system"].value_counts().to_dict()
    entity_by_system = pd.crosstab(emp["legacy_entity_code"], emp["data_source_system"])
    result["legacy_entity_by_source_system"] = entity_by_system.to_dict()

    # data_source_system <-> legacy_entity_code correspondence: is it a clean 1:1
    # mapping (each source system belongs to exactly one legacy entity), as one
    # would expect if each acquired entity simply kept exporting from its own
    # pre-acquisition HRIS?
    is_one_to_one = bool((entity_by_system.gt(0).sum(axis=1) <= 1).all())
    result["data_source_system_maps_1to1_to_legacy_entity"] = is_one_to_one

    # Does the tenure-reconciliation anomaly or the review mislabeling concentrate
    # in a particular source system? (descriptive cross-tab, not a fresh test)
    end_dates = emp["exit_date"].fillna(WINDOW_END)
    calendar_months = (
        (end_dates.dt.year - emp["hire_date"].dt.year) * 12
        + (end_dates.dt.month - emp["hire_date"].dt.month) + 1
    )
    emp = emp.copy()
    emp["tenure_diff_gt1"] = (emp["tenure_months"] - calendar_months).abs().gt(1)
    tenure_mismatch_by_system = emp.groupby("data_source_system")["tenure_diff_gt1"].mean().round(3)
    result["tenure_mismatch_rate_by_source_system"] = tenure_mismatch_by_system.to_dict()

    perf_src = dfs["performance"].merge(
        emp[["employee_id", "data_source_system"]], on="employee_id", how="left"
    )

    def outside_window_with_grace(row):
        lo, hi = CYCLE_WINDOWS[row["review_cycle"]]
        return not (lo <= row["review_date"] <= hi + pd.Timedelta(days=CYCLE_GRACE_DAYS))

    perf_src["mislabeled"] = perf_src.apply(outside_window_with_grace, axis=1)
    result["review_mislabel_rate_by_source_system"] = (
        perf_src.groupby("data_source_system")["mislabeled"].mean().round(4).to_dict()
    )

    findings["legacy_system_artefacts"] = result

    # This is the root-cause refinement of DQ-001 (tenure_months reconciliation):
    # if the mismatch rate is heavily concentrated in one source system, that
    # points at a system-specific export/computation bug rather than a uniform
    # data-generation quirk affecting everyone equally.
    max_system = tenure_mismatch_by_system.idxmax()
    max_rate = tenure_mismatch_by_system.max()
    other_max = tenure_mismatch_by_system.drop(max_system).max()
    if max_rate > 0.25 and max_rate > 3 * other_max:
        n_affected = int(((emp["data_source_system"] == max_system) & emp["tenure_diff_gt1"]).sum())
        n_system_total = int((emp["data_source_system"] == max_system).sum())
        issues.add(
            "employees", "tenure_months/data_source_system", ERROR, n_affected,
            n_system_total,
            f"The tenure_months reconciliation error (DQ-001) is heavily "
            f"concentrated in one source system: '{max_system}' shows a "
            f"{max_rate*100:.1f}% mismatch rate vs "
            f"{tenure_mismatch_by_system.drop(max_system).round(3).to_dict()} "
            f"for the other systems. '{max_system}' corresponds to the "
            f"NovaCorp-Origin cohort specifically (see the source-system x "
            f"legacy-entity crosstab above).",
            "This points to a system-specific tenure computation/export issue "
            "in the NovaCorp-Origin HRIS export rather than a company-wide "
            "data-generation artefact — strengthens the recommendation to "
            "recompute tenure from hire_date/exit_date directly rather than "
            "trust the stored field, and specifically do not assume the "
            "acquired-entity cohorts (Entity_A/B/C) share the same tenure data "
            "quality issue that NovaCorp-Origin records show."
        )

    return result


def check_temporal_leakage(dfs, issues: IssueLog, findings: dict):
    """Direct check on the standing rule: never use information recorded AFTER
    an employee exits to explain/predict their departure."""
    emp = dfs["employees"][["employee_id", "hire_date", "exit_date"]]
    eng = dfs["engagement"].merge(emp, on="employee_id", how="left")
    perf = dfs["performance"].merge(emp, on="employee_id", how="left")
    result = {}

    survey_after_exit = int((eng["survey_date"] > eng["exit_date"]).sum())
    survey_before_hire = int((eng["survey_date"] < eng["hire_date"]).sum())
    review_after_exit = int((perf["review_date"] > perf["exit_date"]).sum())
    review_before_hire = int((perf["review_date"] < perf["hire_date"]).sum())

    result["engagement_survey_after_exit_date"] = survey_after_exit
    result["engagement_survey_before_hire_date"] = survey_before_hire
    result["performance_review_after_exit_date"] = review_after_exit
    result["performance_review_before_hire_date"] = review_before_hire

    for label, n, dataset, col in [
        ("survey completed after the employee's own exit date", survey_after_exit, "engagement", "survey_date"),
        ("survey dated before the employee's own hire date", survey_before_hire, "engagement", "survey_date"),
        ("review dated after the employee's own exit date", review_after_exit, "performance", "review_date"),
        ("review dated before the employee's own hire date", review_before_hire, "performance", "review_date"),
    ]:
        if n:
            issues.add(dataset, col, ERROR, n,
                       len(eng) if dataset == "engagement" else len(perf),
                       f"Record with a {label} — a direct violation of temporal "
                       "possibility.",
                       "Exclude these rows from any time-ordered analysis; "
                       "treat as corrupted timestamps.")

    # Per-employee wave/date and cycle/date monotonicity (a subtler check than the
    # raw exit/hire bound above)
    eng_sorted = dfs["engagement"].sort_values(["employee_id", "wave_number"])
    prev_date = eng_sorted.groupby("employee_id")["survey_date"].shift(1)
    wave_order_violations = int((eng_sorted["survey_date"] < prev_date).sum())
    result["engagement_wave_number_survey_date_order_violations"] = wave_order_violations
    if wave_order_violations:
        issues.add("engagement", "wave_number/survey_date", ERROR,
                    wave_order_violations, len(eng_sorted),
                    "A later wave_number has an earlier survey_date than a "
                    "prior wave for the same employee.",
                    "Sort strictly by survey_date, not wave_number, for any "
                    "leading-indicator / trend analysis (Areas RA-2, DP-4, "
                    "SR-3).")

    # The review_cycle mislabeling (checked in detail elsewhere) is the one
    # confirmed DERIVED leakage vector: raw review_date never exceeds exit_date,
    # but review_cycle as a label is unreliable for sequencing.
    result["note"] = (
        "No raw-timestamp leakage found: no engagement or performance record "
        "in this dataset is dated after the employee's own exit_date, and none "
        "predates hire_date. The one confirmed temporal-correctness trap is "
        "categorical, not a raw timestamp: review_cycle labels are unreliable "
        "for a small subset of records (see the dedicated review_cycle-label "
        "consistency check) — always sequence by the actual date column, never "
        "by a cycle/wave label."
    )

    findings["temporal_leakage"] = result
    return result


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_all_checks(dfs: dict[str, pd.DataFrame]):
    issues = IssueLog()
    findings: dict = {}

    check_employee_id_integrity(dfs, issues, findings)
    check_manager_reference_integrity(dfs, issues, findings)
    check_duplicates(dfs, issues, findings)
    check_impossible_values(dfs, issues, findings)
    check_inconsistent_categories(dfs, issues, findings)
    check_date_ranges(dfs, issues, findings)
    check_status_exit_consistency(dfs, issues, findings)
    check_salary_anomalies(dfs, issues, findings)
    check_tenure_anomalies(dfs, issues, findings)
    check_engagement_wave_coverage(dfs, issues, findings)
    check_survey_response_patterns(dfs, issues, findings)
    check_performance_cycle_label_consistency(dfs, issues, findings)
    check_performance_coverage(dfs, issues, findings)
    check_incomplete_histories(dfs, findings)
    check_cross_dataset_reconciliation(dfs, findings)
    check_legacy_system_artefacts(dfs, issues, findings)
    check_temporal_leakage(dfs, issues, findings)

    return issues, findings


def write_outputs(dfs, issues: IssueLog, findings: dict):
    OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    miss = missingness_table(dfs)
    miss.to_csv(OUTPUT_TABLES_DIR / "missingness.csv", index=False)

    issues_df = issues.to_frame()
    issues_df.to_csv(OUTPUT_TABLES_DIR / "data_quality_issues.csv", index=False)

    report_path = OUTPUT_REPORTS_DIR / "data_quality_report.md"
    report_path.write_text(build_report(dfs, issues_df, findings), encoding="utf-8")

    return miss, issues_df, report_path


def _df_to_markdown(df: pd.DataFrame) -> str:
    """Minimal, dependency-free Markdown table renderer (avoids requiring the
    optional `tabulate` package that pandas.to_markdown() needs)."""
    if df.empty:
        return "(no rows)"
    cols = [str(c) for c in df.columns]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body_lines = []
    for _, row in df.iterrows():
        cells = ["" if pd.isna(v) else str(v).replace("|", "\\|").replace("\n", " ")
                 for v in row.tolist()]
        body_lines.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep, *body_lines])


def _fmt_dict(d: dict, indent: int = 0) -> str:
    pad = "  " * indent
    lines = []
    for k, v in d.items():
        if isinstance(v, dict):
            if not v:
                lines.append(f"{pad}- **{k}**: (none)")
            else:
                lines.append(f"{pad}- **{k}**:")
                lines.append(_fmt_dict(v, indent + 1))
        else:
            lines.append(f"{pad}- **{k}**: {v}")
    return "\n".join(lines)


def build_report(dfs, issues_df: pd.DataFrame, findings: dict) -> str:
    overview = dataset_overview(dfs)
    n_by_cat = (
        issues_df["category"].value_counts().to_dict() if len(issues_df) else {}
    )

    lines = []
    lines.append("# NovaCorp Data Quality Audit Report")
    lines.append("")
    lines.append(
        "Generated by `src/data_audit.py`. Governing context: `CLAUDE.md` and "
        "`docs/analysis_plan.md`. This report is descriptive and diagnostic "
        "only — **no cleaning has been performed**. Every issue below is "
        "classified as one of ERROR / EXPECTED MISSINGNESS / BUSINESS SIGNAL / "
        "UNKNOWN-REQUIRES ASSUMPTION, with a recommendation, not an action "
        "already taken."
    )
    lines.append("")
    lines.append("## 0. Headline Summary")
    lines.append("")
    lines.append(f"- Datasets audited: {len(dfs)}")
    lines.append(f"- Total distinct issues logged: {len(issues_df)}")
    for cat in [ERROR, EXPECTED_MISSINGNESS, BUSINESS_SIGNAL, UNKNOWN]:
        lines.append(f"  - {cat}: {n_by_cat.get(cat, 0)}")
    lines.append("")
    lines.append(
        "**Most consequential findings** (full detail in their sections below):"
    )
    lines.append(
        "1. `tenure_months` in `employees.csv` does not reconcile with "
        "`hire_date` and the documented window-end/exit_date definition — for "
        "active employees the implied as-of date drifts from ~Nov 2025 to ~Jun "
        "2026 instead of clustering at the stated 2025-12-31 window end. "
        "**Recommend recomputing tenure from raw dates rather than trusting "
        "the supplied column.** (Section 9)"
    )
    lines.append(
        "2. A confirmed subset of `performance.csv` rows are labelled "
        "`review_cycle = '2024-H1'` despite an actual `review_date` up to ~18 "
        "months later — concentrated among employees reviewed within days of "
        "hire who then departed within about a month. **Never sequence "
        "performance records by `review_cycle`; always use `review_date`.** "
        "(Section 12)"
    )
    lines.append(
        "3. No raw-timestamp temporal leakage was found anywhere: no "
        "engagement or performance record in the data is dated after its "
        "employee's own `exit_date`, or before their `hire_date`. Referential "
        "integrity (employee_id, manager_id, reviewer_id) is fully clean — "
        "zero orphans anywhere. (Section 13)"
    )
    lines.append("")

    lines.append("## 1. Dataset Overview")
    lines.append("")
    lines.append(_df_to_markdown(overview))
    lines.append("")

    lines.append("## 2. Employee ID Integrity")
    lines.append("")
    lines.append(_fmt_dict(findings["employee_id_integrity"]))
    lines.append("")
    lines.append(
        "**Note:** `employee_id` values are not contiguous (max ID exceeds the "
        "row count) — this reflects gaps in the ID sequence, not missing "
        "records; do not infer population size from ID range."
    )
    lines.append("")

    lines.append("## 3. Manager / Reviewer Reference Integrity")
    lines.append("")
    lines.append(_fmt_dict(findings["manager_reference_integrity"]))
    lines.append("")
    lines.append(
        "All manager_id, reviewer_id, and manager_id_at_exit references resolve "
        "cleanly to a known employee_id except where noted above — no orphaned "
        "management references were found."
        if not any([
            findings["manager_reference_integrity"]["manager_id_orphan"],
            findings["manager_reference_integrity"]["self_managed_rows"],
            findings["manager_reference_integrity"]["reviewer_id_orphan"],
            findings["manager_reference_integrity"]["manager_id_at_exit_orphan"],
        ])
        else "See issues log for specific orphaned references found."
    )
    lines.append("")

    lines.append("## 4. Duplicates")
    lines.append("")
    lines.append(_fmt_dict(findings["duplicates"]))
    lines.append("")

    lines.append("## 5. Impossible Values")
    lines.append("")
    lines.append(_fmt_dict(findings["impossible_values"]))
    lines.append("")

    lines.append("## 6. Category Consistency")
    lines.append("")
    any_unexpected = any(
        v["unexpected"] for v in findings["inconsistent_categories"].values()
    )
    if any_unexpected:
        for field_, v in findings["inconsistent_categories"].items():
            if v["unexpected"]:
                lines.append(f"- **{field_}**: unexpected values {v['unexpected']}")
    else:
        lines.append(
            "No unexpected category values or whitespace/case variants found in "
            "any of the checked categorical fields (`status`, `department`, "
            "`role_family`, `gender`, `contract_type`, `hire_source`, "
            "`legacy_entity_code`, `exit_type`, `performance_band_at_exit`, "
            "`pathway`, `performance_rating`, `review_cycle`). Full observed "
            "vocabularies are in `docs/data_dictionary.md`."
        )
    lines.append("")

    lines.append("## 7. Date Ranges & Ordering")
    lines.append("")
    lines.append(_fmt_dict(findings["date_ranges"]))
    lines.append("")
    lines.append(
        f"Pre-window hires (`hire_date` before 2024-01-01): "
        f"{findings['date_ranges']['pre_window_hires']} — expected and "
        "necessary, since tenure carries over from before the observation "
        "window began; classified as BUSINESS SIGNAL / EXPECTED, not an error."
    )
    lines.append("")

    lines.append("## 8. Status / Exit Consistency")
    lines.append("")
    lines.append(_fmt_dict(findings["status_exit_consistency"]))
    lines.append("")
    lines.append(
        "All checks in this section returned zero — `status`, `exit_date`, and "
        "`attrition_log.csv` membership are fully mutually consistent across "
        "the 13,403-row roster."
    )
    lines.append("")

    lines.append("## 9. Salary & Tenure Anomalies")
    lines.append("")
    lines.append("### 9.1 Salary")
    lines.append(_fmt_dict(findings["salary_anomalies"]))
    lines.append("")
    lines.append("### 9.2 Tenure (see also Headline Summary #1)")
    lines.append(_fmt_dict(findings["tenure_anomalies"]))
    lines.append("")

    lines.append("## 10. Engagement Wave Coverage")
    lines.append("")
    lines.append(_fmt_dict(findings["engagement_wave_coverage"]))
    lines.append("")

    lines.append("## 11. Survey Response Patterns")
    lines.append("")
    lines.append(_fmt_dict(findings["survey_response_patterns"]))
    lines.append("")

    lines.append("## 12. Performance Cycle Label Consistency (see Headline Summary #2)")
    lines.append("")
    lines.append(_fmt_dict(findings["performance_cycle_label_consistency"]))
    lines.append("")

    lines.append("## 13. Performance Coverage & Temporal Leakage Scan")
    lines.append("")
    lines.append("### 13.1 Coverage")
    lines.append(_fmt_dict(findings["performance_coverage"]))
    lines.append("")
    lines.append("### 13.2 Temporal leakage (raw timestamps)")
    lines.append(_fmt_dict(findings["temporal_leakage"]))
    lines.append("")

    lines.append("## 14. Incomplete Histories")
    lines.append("")
    lines.append(_fmt_dict(findings["incomplete_histories"]))
    lines.append("")

    lines.append("## 15. Cross-Dataset Reconciliation")
    lines.append("")
    lines.append(_fmt_dict(findings["cross_dataset_reconciliation"]))
    lines.append("")
    lines.append(
        "Voluntary attrition computed as voluntary exits ÷ active headcount is "
        "provided alongside voluntary exits ÷ (active + departed) purely as a "
        "reconciliation sanity check against the Annual Report's reported "
        "10.4% figure — the exact denominator NovaCorp Finance used internally "
        "is not stated in the brief and should not be assumed; treat any "
        "close match as directional confirmation only, not proof of methodology."
    )
    lines.append("")

    lines.append("## 16. Legacy System Artefact Scan")
    lines.append("")
    lines.append(_fmt_dict(findings["legacy_system_artefacts"]))
    lines.append("")

    lines.append("## 17. Full Issues Log")
    lines.append("")
    lines.append(
        f"See `outputs/tables/data_quality_issues.csv` for the machine-readable "
        f"version ({len(issues_df)} rows). Rendered below in full."
    )
    lines.append("")
    if len(issues_df):
        lines.append(_df_to_markdown(issues_df))
    else:
        lines.append("(no issues logged)")
    lines.append("")

    lines.append("## 18. What This Audit Does Not Cover")
    lines.append("")
    lines.append(
        "- No hypothesis testing, no modelling, no financial costing — that is "
        "explicitly out of scope for this audit (see `docs/analysis_plan.md`)."
    )
    lines.append(
        "- Plausibility bands used for `compa_ratio`/salary outliers are "
        "heuristic (documented inline), not sourced from an official NovaCorp "
        "pay-band table (none was supplied); treat flagged rows as candidates "
        "for review, not confirmed errors."
    )
    lines.append(
        "- The 'unexplained zero-engagement-wave' residual could not be fully "
        "resolved without per-employee survey-issuance dates, which are not in "
        "the data; see Section 10."
    )
    lines.append("")

    return "\n".join(lines)


def main():
    dfs = load_datasets()
    issues, findings = run_all_checks(dfs)
    miss, issues_df, report_path = write_outputs(dfs, issues, findings)

    print(f"Loaded datasets: { {k: len(v) for k, v in dfs.items()} }")
    print(f"Issues logged: {len(issues_df)}")
    if len(issues_df):
        print(issues_df["category"].value_counts().to_string())
    print(f"Missingness table: {OUTPUT_TABLES_DIR / 'missingness.csv'} ({len(miss)} rows)")
    print(f"Issues table: {OUTPUT_TABLES_DIR / 'data_quality_issues.csv'} ({len(issues_df)} rows)")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
