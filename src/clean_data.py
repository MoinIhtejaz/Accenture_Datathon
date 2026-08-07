"""
NovaCorp People Analytics Challenge — Data Cleaning Pipeline
==============================================================

Reproducible cleaning pipeline built strictly on findings from the completed
data-quality audit (`outputs/reports/data_quality_report.md`,
`outputs/tables/data_quality_issues.csv`) and the proposed handling in
`docs/decision_log.md`. Every transformation below traces back to a specific
audit finding — nothing is "cleaned" speculatively.

Non-negotiable design choices (all deliberate, all documented inline):

1. Raw source files (employees.csv, attrition_log.csv, engagement.csv,
   performance.csv) are NEVER written to. This module only reads them.
2. Rows are never silently deleted. Every cleaned output keeps the SAME row
   count as its raw source; unusable rows are marked `excluded=True` with an
   `exclusion_reason`, so nothing disappears without a trace. Downstream
   analysis filters with `df[~df.excluded]`.
3. No missing value is ever imputed. Nulls that the audit classified as
   EXPECTED MISSINGNESS (still-active employees' exit_date, the CEO's null
   manager_id, non-respondents' engagement scores) are left exactly as null.
4. Fields the audit found unreliable (tenure_months, review_cycle) are never
   overwritten. A corrected/derived column is added alongside the original,
   plus a boolean reliability flag, per docs/decision_log.md DEC-001/DEC-002.
5. Everything is re-run from scratch each execution: outputs are overwritten,
   not appended to, so a run is always reproducible from the current raw CSVs.

Outputs:
  - data_clean/{employees,attrition_log,engagement,performance}_clean.csv
  - outputs/tables/cleaning_summary.csv
  - outputs/logs/clean_data.log

Run: `python src/clean_data.py` from anywhere.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from load_data import (
    CLEAN_DATA_DIR,
    COMPA_RATIO_PLAUSIBLE_RANGE,
    CYCLE_GRACE_DAYS,
    CYCLE_WINDOWS,
    DATE_COLUMNS,
    ENGAGEMENT_DIMENSIONS,
    ENGAGEMENT_SCALE_RANGE,
    EXPECTED_CATEGORIES,
    GOAL_ACHIEVEMENT_RANGE,
    OUTPUT_LOGS_DIR,
    OUTPUT_TABLES_DIR,
    ROLE_LEVEL_RANGE,
    STRING_ID_COLUMNS,
    WINDOW_END,
    WINDOW_START,
    load_raw_strings,
)
from validation import ValidationFailure, validate_all

CLEANING_SUMMARY_PATH = OUTPUT_TABLES_DIR / "cleaning_summary.csv"
LOG_PATH = OUTPUT_LOGS_DIR / "clean_data.log"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger() -> logging.Logger:
    OUTPUT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("clean_data")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # reproducible: no duplicate handlers on re-import

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    return logger


logger = setup_logger()


# ---------------------------------------------------------------------------
# Exclusion / flag bookkeeping
# ---------------------------------------------------------------------------

def init_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["excluded"] = False
    df["exclusion_reason"] = pd.array([None] * len(df), dtype="string")
    return df


def mark_excluded(df: pd.DataFrame, mask: pd.Series, reason: str, rule_name: str,
                   exclusion_counts: dict) -> int:
    """Mark rows as excluded, without overwriting a reason already set by an
    earlier rule (first applicable reason wins; a row is never double-counted
    across rules)."""
    newly = mask & (~df["excluded"])
    n = int(newly.sum())
    df.loc[newly, "excluded"] = True
    df.loc[newly, "exclusion_reason"] = reason
    exclusion_counts[rule_name] = exclusion_counts.get(rule_name, 0) + n
    level = logging.WARNING if n else logging.INFO
    logger.log(level, f"[{rule_name}] excluded {n} row(s) — {reason}")
    return n


def add_flag(df: pd.DataFrame, mask: pd.Series, flag_col: str, description: str) -> int:
    """Non-destructive flag: marks rows for downstream caution without
    excluding them. Column defaults False everywhere else."""
    if flag_col not in df.columns:
        df[flag_col] = False
    df.loc[mask, flag_col] = True
    n = int(mask.sum())
    level = logging.WARNING if n else logging.INFO
    logger.log(level, f"[{flag_col}] flagged {n} row(s) — {description}")
    return n


# ---------------------------------------------------------------------------
# Step 1: explicit date parsing
# ---------------------------------------------------------------------------

def parse_dates_explicitly(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Parse every documented date column explicitly (not silently inside a
    generic loader), logging any value that fails to parse. raw[*] columns are
    strings (load_data.load_raw_strings()); this function converts date columns
    to datetime64 and leaves every other column untouched."""
    parsed = {}
    for name, df in raw.items():
        df = df.copy()
        for col in DATE_COLUMNS[name]:
            raw_col = df[col]
            had_value = raw_col.notna() & (raw_col.str.strip() != "")
            parsed_col = pd.to_datetime(raw_col, errors="coerce")
            n_failed = int((had_value & parsed_col.isna()).sum())
            if n_failed:
                logger.error(
                    f"[date_parsing] {name}.{col}: {n_failed} non-empty value(s) "
                    "failed to parse as a date and became NaT."
                )
            else:
                logger.info(
                    f"[date_parsing] {name}.{col}: parsed cleanly "
                    f"({int(had_value.sum())} non-null values, 0 failures)."
                )
            df[col] = parsed_col
        parsed[name] = df
    return parsed


# ---------------------------------------------------------------------------
# Step 2: duplicate handling
# ---------------------------------------------------------------------------

DUPLICATE_KEYS = {
    "employees": ["employee_id"],
    "attrition_log": ["employee_id"],
    "engagement": ["employee_id", "wave_number"],
    "performance": ["employee_id", "review_cycle"],
}
# For key files (one row per entity), an ambiguous duplicate excludes ALL
# copies rather than arbitrarily keeping one. For repeatable-observation
# files, the first occurrence is kept deterministically.
AMBIGUOUS_ALL_COPIES = {"employees", "attrition_log"}


def handle_duplicates(dfs: dict[str, pd.DataFrame], exclusion_counts: dict) -> None:
    for name, df in dfs.items():
        n_exact = int(df.duplicated().sum())
        exact_mask = df.duplicated(keep="first")
        mark_excluded(df, exact_mask, "exact duplicate row (kept first occurrence)",
                      f"{name}: exact_duplicate_rows", exclusion_counts)

        key = DUPLICATE_KEYS[name]
        remaining = ~df["excluded"]
        key_dupe_any = df.duplicated(subset=key, keep=False) & remaining
        key_dupe_extra = df.duplicated(subset=key, keep="first") & remaining

        if name in AMBIGUOUS_ALL_COPIES:
            reason = f"duplicate {'+'.join(key)} with differing data — ambiguous, all copies excluded pending manual review"
            mark_excluded(df, key_dupe_any, reason, f"{name}: ambiguous_key_duplicates", exclusion_counts)
        else:
            reason = f"duplicate {'+'.join(key)} — kept first occurrence, excluded later copy"
            mark_excluded(df, key_dupe_extra, reason, f"{name}: key_duplicates_extra_copies", exclusion_counts)


# ---------------------------------------------------------------------------
# Step 3: referential integrity
# ---------------------------------------------------------------------------

def handle_referential_integrity(dfs: dict[str, pd.DataFrame], exclusion_counts: dict) -> None:
    emp = dfs["employees"]
    all_employee_ids = set(emp["employee_id"].dropna())  # existence, not exclusion status

    for name in ("attrition_log", "engagement", "performance"):
        df = dfs[name]
        orphan_mask = ~df["employee_id"].isin(all_employee_ids)
        mark_excluded(df, orphan_mask,
                      "employee_id not found in employees.csv (orphaned reference)",
                      f"{name}: orphan_employee_id", exclusion_counts)

    # Secondary reference fields: flag, never exclude the row for these.
    mgr_orphan = ~emp["manager_id"].isin(all_employee_ids) & emp["manager_id"].notna()
    add_flag(emp, mgr_orphan, "manager_id_orphan_flag",
             "manager_id does not resolve to a known employee_id")
    self_managed = (emp["manager_id"] == emp["employee_id"]) & emp["manager_id"].notna()
    add_flag(emp, self_managed, "self_managed_flag",
             "employee_id equals their own manager_id")

    perf = dfs["performance"]
    rev_orphan = ~perf["reviewer_id"].isin(all_employee_ids) & perf["reviewer_id"].notna()
    add_flag(perf, rev_orphan, "reviewer_id_orphan_flag",
             "reviewer_id does not resolve to a known employee_id")

    att = dfs["attrition_log"]
    mgr_exit_orphan = ~att["manager_id_at_exit"].isin(all_employee_ids) & att["manager_id_at_exit"].notna()
    add_flag(att, mgr_exit_orphan, "manager_id_at_exit_orphan_flag",
             "manager_id_at_exit does not resolve to a known employee_id")


# ---------------------------------------------------------------------------
# Step 4: impossible-value handling
# ---------------------------------------------------------------------------

def handle_impossible_values(dfs: dict[str, pd.DataFrame], exclusion_counts: dict) -> None:
    emp, att, eng, perf = dfs["employees"], dfs["attrition_log"], dfs["engagement"], dfs["performance"]

    # --- employees: core-identity violations -> exclude the row ---
    mark_excluded(emp, ~emp["role_level"].between(*ROLE_LEVEL_RANGE),
                  f"role_level outside documented range {ROLE_LEVEL_RANGE}",
                  "employees: role_level_out_of_range", exclusion_counts)
    mark_excluded(emp, emp["salary"] <= 0,
                  "salary is zero or negative — unusable for any financial costing",
                  "employees: non_positive_salary", exclusion_counts)
    hire_after_exit = emp["exit_date"].notna() & (emp["hire_date"] > emp["exit_date"])
    mark_excluded(emp, hire_after_exit,
                  "hire_date is after exit_date — internally impossible record",
                  "employees: hire_after_exit", exclusion_counts)
    active_with_exit = (emp["status"] == "active") & emp["exit_date"].notna()
    mark_excluded(emp, active_with_exit,
                  "status is 'active' but exit_date is populated — status/exit_date contradiction",
                  "employees: active_status_with_exit_date", exclusion_counts)
    departed_no_exit = (emp["status"] == "departed") & emp["exit_date"].isna()
    mark_excluded(emp, departed_no_exit,
                  "status is 'departed' but exit_date is null — cannot determine tenure-at-exit",
                  "employees: departed_status_missing_exit_date", exclusion_counts)
    exit_outside_window = emp["exit_date"].notna() & (
        (emp["exit_date"] < WINDOW_START) | (emp["exit_date"] > WINDOW_END)
    )
    mark_excluded(emp, exit_outside_window,
                  "exit_date falls outside the 2024-01-01 to 2025-12-31 observation window",
                  "employees: exit_date_outside_window", exclusion_counts)

    # --- employees: secondary-field violations -> null the field, flag the row ---
    bad_dtf = emp["days_to_fill"] < 0
    n = add_flag(emp, bad_dtf, "days_to_fill_invalid",
                 "days_to_fill is negative — nulled, excluded from hiring-efficiency analysis only")
    emp.loc[bad_dtf, "days_to_fill"] = np.nan

    implausible_compa = ~emp["compa_ratio"].between(*COMPA_RATIO_PLAUSIBLE_RANGE)
    add_flag(emp, implausible_compa, "compa_ratio_outside_screening_band",
             "compa_ratio outside the 0.3-2.5 screening band (indicative only, no official band table — DEC-007)")

    # --- attrition_log: window bound -> exclude ---
    att_outside_window = (att["exit_date"] < WINDOW_START) | (att["exit_date"] > WINDOW_END)
    mark_excluded(att, att_outside_window,
                  "exit_date falls outside the 2024-01-01 to 2025-12-31 observation window",
                  "attrition_log: exit_date_outside_window", exclusion_counts)

    # --- engagement: window bound -> exclude ---
    eng_outside_window = (eng["survey_date"] < WINDOW_START) | (eng["survey_date"] > WINDOW_END)
    mark_excluded(eng, eng_outside_window,
                  "survey_date falls outside the 2024-01-01 to 2025-12-31 observation window",
                  "engagement: survey_date_outside_window", exclusion_counts)

    # --- engagement: per-dimension range + response_flag consistency -> null the value, flag the row ---
    for dim in ENGAGEMENT_DIMENSIONS:
        responded = eng["response_flag"]
        out_of_range = responded & ~eng[dim].between(*ENGAGEMENT_SCALE_RANGE) & eng[dim].notna()
        n = add_flag(eng, out_of_range, f"{dim}_out_of_range",
                     f"{dim} outside 1-5 for a responded row — value nulled")
        eng.loc[out_of_range, dim] = np.nan

        stray_score = (~responded) & eng[dim].notna()
        n2 = add_flag(eng, stray_score, f"{dim}_stray_score_nulled",
                      f"response_flag is False but {dim} was populated — contradicts documented "
                      "null-on-non-response rule; value nulled to restore the invariant")
        eng.loc[stray_score, dim] = np.nan

    # --- performance: window bound -> exclude ---
    perf_outside_window = (perf["review_date"] < WINDOW_START) | (perf["review_date"] > WINDOW_END)
    mark_excluded(perf, perf_outside_window,
                  "review_date falls outside the 2024-01-01 to 2025-12-31 observation window",
                  "performance: review_date_outside_window", exclusion_counts)

    bad_goal = ~perf["goal_achievement_score"].between(*GOAL_ACHIEVEMENT_RANGE)
    add_flag(perf, bad_goal, "goal_achievement_score_invalid",
             f"goal_achievement_score outside documented range {GOAL_ACHIEVEMENT_RANGE} — value nulled")
    perf.loc[bad_goal, "goal_achievement_score"] = np.nan


# ---------------------------------------------------------------------------
# Step 5: category normalisation
# ---------------------------------------------------------------------------

def normalize_categories(dfs: dict[str, pd.DataFrame]) -> None:
    """Strip whitespace and case-normalise against the documented vocabulary for
    every categorical field the audit checked. The audit found zero anomalies
    in the current data (outputs/reports/data_quality_report.md Section 6), so
    this step is expected to be a no-op today — it exists so a future data
    refresh with real casing/whitespace drift is caught and corrected the same
    way, rather than requiring a new one-off script."""
    for dataset_name, fields in EXPECTED_CATEGORIES.items():
        df = dfs[dataset_name]
        for col, allowed in fields.items():
            canonical_by_normal = {str(v).strip().lower(): v for v in allowed}
            values = df[col]
            normal = values.astype("string").str.strip().str.lower()
            mapped = normal.map(canonical_by_normal)

            changed = mapped.notna() & (mapped != values) & values.notna()
            n_changed = int(changed.sum())
            if n_changed:
                df.loc[changed, col] = mapped[changed]
            logger.info(f"[category_normalisation] {dataset_name}.{col}: "
                        f"{n_changed} value(s) normalised to canonical form.")

            still_unexpected = values.notna() & mapped.isna()
            flag_col = f"{col}_category_anomaly"
            df[flag_col] = False
            df.loc[still_unexpected, flag_col] = True
            n_anomaly = int(still_unexpected.sum())
            level = logging.WARNING if n_anomaly else logging.INFO
            logger.log(level, f"[category_normalisation] {dataset_name}.{col}: "
                               f"{n_anomaly} value(s) remain unrecognised after normalisation.")


# ---------------------------------------------------------------------------
# Step 6: cross-file consistency flags
# ---------------------------------------------------------------------------

def handle_cross_file_consistency(dfs: dict[str, pd.DataFrame], exclusion_counts: dict) -> None:
    emp, att = dfs["employees"], dfs["attrition_log"]

    departed_ids = set(emp.loc[(emp["status"] == "departed") & (~emp["excluded"]), "employee_id"])
    attrition_ids = set(att.loc[~att["excluded"], "employee_id"])

    missing_from_log = emp["employee_id"].isin(departed_ids - attrition_ids)
    add_flag(emp, missing_from_log, "attrition_log_missing_flag",
             "employee marked 'departed' with no corresponding attrition_log.csv record "
             "— exit_type/voluntary-involuntary cannot be determined")

    # An attrition_log row for an employee not consistently marked 'departed' cannot
    # be trusted as a coherent exit record (unlike a simple missing counterpart on
    # the employees side, which just limits what CAN be said, not what's asserted).
    inconsistent_status = att["employee_id"].isin(attrition_ids - departed_ids)
    mark_excluded(att, inconsistent_status,
                  "employee is not consistently marked 'departed' in employees.csv — "
                  "exit record cannot be trusted as coherent",
                  "attrition_log: status_inconsistent_with_employees", exclusion_counts)

    sal_merge = emp.loc[~emp["excluded"], ["employee_id", "salary"]].merge(
        att.loc[~att["excluded"], ["employee_id", "salary_at_exit"]], on="employee_id")
    mismatch_ids = set(sal_merge.loc[sal_merge["salary"] != sal_merge["salary_at_exit"], "employee_id"])
    add_flag(emp, emp["employee_id"].isin(mismatch_ids), "salary_mismatch_flag",
              "salary differs from attrition_log.salary_at_exit for this employee")
    add_flag(att, att["employee_id"].isin(mismatch_ids), "salary_mismatch_flag",
              "salary_at_exit differs from employees.csv.salary for this employee")


# ---------------------------------------------------------------------------
# Step 7: derived corrections (DEC-001, DEC-002)
# ---------------------------------------------------------------------------

def add_tenure_recomputation(emp: pd.DataFrame) -> None:
    """DEC-001: never trust tenure_months at face value. Recompute from
    hire_date and (exit_date or window end), keep the original column
    unchanged alongside it, and flag rows where the two disagree by more than
    1 month."""
    end_dates = emp["exit_date"].fillna(WINDOW_END)
    recomputed = (
        (end_dates.dt.year - emp["hire_date"].dt.year) * 12
        + (end_dates.dt.month - emp["hire_date"].dt.month) + 1
    )
    emp["tenure_months_recomputed"] = recomputed
    emp["tenure_months_reliable"] = (emp["tenure_months"] - recomputed).abs().le(1)
    n_unreliable = int((~emp["tenure_months_reliable"]).sum())
    logger.warning(
        f"[tenure_recomputation] {n_unreliable} of {len(emp)} rows have "
        "tenure_months differing from the recomputed value by more than 1 month "
        "(see docs/decision_log.md DEC-001). tenure_months is retained unchanged; "
        "use tenure_months_recomputed for any time-sensitive analysis."
    )


def add_review_cycle_reliability(perf: pd.DataFrame) -> None:
    """DEC-002: never relabel review_cycle. Flag rows whose review_date falls
    outside the nominal cycle window (+grace period) so downstream code can
    choose to exclude them from cycle-based aggregation without losing the
    row entirely."""
    def in_window_with_grace(row):
        lo, hi = CYCLE_WINDOWS[row["review_cycle"]]
        return lo <= row["review_date"] <= hi + pd.Timedelta(days=CYCLE_GRACE_DAYS)

    perf["review_cycle_reliable"] = perf.apply(in_window_with_grace, axis=1)
    n_unreliable = int((~perf["review_cycle_reliable"]).sum())
    logger.warning(
        f"[review_cycle_reliability] {n_unreliable} of {len(perf)} rows have a "
        "review_date inconsistent with their review_cycle label (see "
        "docs/decision_log.md DEC-002). review_cycle is retained unchanged; "
        "always sequence/filter performance records by review_date, never by "
        "review_cycle."
    )


# ---------------------------------------------------------------------------
# Step 8: missing-value handling (documentation only — no imputation)
# ---------------------------------------------------------------------------

def document_missing_value_handling(dfs: dict[str, pd.DataFrame]) -> None:
    emp, eng = dfs["employees"], dfs["engagement"]
    n_active = int((emp["status"] == "active").sum())
    n_exit_null = int(emp["exit_date"].isna().sum())
    logger.info(
        f"[missing_values] employees.exit_date: {n_exit_null} nulls, "
        f"{n_active} active employees — {'MATCHES' if n_exit_null == n_active else 'MISMATCH'} "
        "(EXPECTED MISSINGNESS: null means still active; never imputed)."
    )
    n_mgr_null = int(emp["manager_id"].isna().sum())
    logger.info(
        f"[missing_values] employees.manager_id: {n_mgr_null} null(s) "
        "(EXPECTED MISSINGNESS: top of hierarchy has no manager; never imputed)."
    )
    n_non_respondents = int((~eng["response_flag"]).sum())
    for dim in ENGAGEMENT_DIMENSIONS:
        n_null = int(eng[dim].isna().sum())
        logger.info(
            f"[missing_values] engagement.{dim}: {n_null} nulls, "
            f"{n_non_respondents} non-respondents — "
            f"{'MATCHES' if n_null == n_non_respondents else 'MISMATCH (see flags added above)'} "
            "(EXPECTED MISSINGNESS: null means the employee did not respond to this "
            "dimension; never imputed)."
        )
    logger.info(
        "[missing_values] No missing value in any of the four files has been "
        "imputed, interpolated, or filled anywhere in this pipeline."
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def clean_all() -> tuple[dict[str, pd.DataFrame], dict, dict, dict]:
    logger.info("=" * 70)
    logger.info("Starting NovaCorp data cleaning pipeline")
    logger.info("=" * 70)

    raw_strings = load_raw_strings()
    original_rows = {name: len(df) for name, df in raw_strings.items()}
    original_columns = {name: list(df.columns) for name, df in raw_strings.items()}
    logger.info(f"[load] raw row counts: {original_rows}")

    dfs = parse_dates_explicitly(raw_strings)
    # Note: load_raw_strings() only suppresses parsing of the documented DATE
    # columns (left as raw strings for the explicit-parsing step above). Every
    # other column — booleans, ints, floats — is already correctly typed by
    # pandas' normal read_csv inference regardless of that flag, so no
    # additional dtype restoration is needed or performed here.

    for name in dfs:
        dfs[name] = init_flags(dfs[name])

    exclusion_counts: dict = {}
    handle_duplicates(dfs, exclusion_counts)
    handle_referential_integrity(dfs, exclusion_counts)
    handle_impossible_values(dfs, exclusion_counts)
    normalize_categories(dfs)
    handle_cross_file_consistency(dfs, exclusion_counts)
    add_tenure_recomputation(dfs["employees"])
    add_review_cycle_reliability(dfs["performance"])
    document_missing_value_handling(dfs)

    return dfs, original_rows, exclusion_counts, original_columns


def write_cleaned_outputs(dfs: dict[str, pd.DataFrame]) -> None:
    CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in dfs.items():
        path = CLEAN_DATA_DIR / f"{name}_clean.csv"
        df.to_csv(path, index=False)
        logger.info(f"[write] {path} ({len(df)} rows, {df.shape[1]} columns)")


# Pipeline-added columns where True means "reliable / no problem" — the
# opposite polarity of every other flag this pipeline adds (where True means
# "something needs attention"). Handled separately so a generic "any flag is
# True" scan doesn't undercount problems or, worse, miscategorise an original
# data column that happens to share a naming pattern (e.g. the source
# `hipo_flag` column, which is not something this pipeline added).
INVERTED_RELIABILITY_FLAGS = {"tenure_months_reliable", "review_cycle_reliable"}
NON_FLAG_DERIVED_COLUMNS = {"tenure_months_recomputed"}


def build_cleaning_summary(dfs: dict[str, pd.DataFrame], original_rows: dict,
                            exclusion_counts: dict, original_columns: dict) -> pd.DataFrame:
    rows = []
    for name, df in dfs.items():
        n_excluded = int(df["excluded"].sum())
        n_final = int((~df["excluded"]).sum())
        rule_prefix = f"{name}:"
        by_rule = {k.split(": ", 1)[1]: v for k, v in exclusion_counts.items() if k.startswith(rule_prefix)}

        pipeline_added = (set(df.columns) - set(original_columns[name])
                           - {"excluded", "exclusion_reason"} - NON_FLAG_DERIVED_COLUMNS)
        problem_flags = pipeline_added - INVERTED_RELIABILITY_FLAGS
        reliability_flags = pipeline_added & INVERTED_RELIABILITY_FLAGS

        any_problem = pd.Series(False, index=df.index)
        if problem_flags:
            any_problem = any_problem | df[list(problem_flags)].any(axis=1)
        for col in reliability_flags:
            any_problem = any_problem | (~df[col])

        n_flagged_not_excluded = int((any_problem & ~df["excluded"]).sum())
        rows.append({
            "dataset": name,
            "original_rows": original_rows[name],
            "rows_excluded": n_excluded,
            "final_usable_rows": n_final,
            "pct_excluded": round(100 * n_excluded / original_rows[name], 4) if original_rows[name] else 0.0,
            "rows_flagged_not_excluded": n_flagged_not_excluded,
            "flag_columns_checked": "; ".join(sorted(pipeline_added)) or "none",
            "exclusion_reasons_breakdown": "; ".join(f"{k}={v}" for k, v in by_rule.items()) or "none",
        })
    return pd.DataFrame(rows)


def main():
    try:
        dfs, original_rows, exclusion_counts, original_columns = clean_all()
        write_cleaned_outputs(dfs)

        summary = build_cleaning_summary(dfs, original_rows, exclusion_counts, original_columns)
        OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
        summary.to_csv(CLEANING_SUMMARY_PATH, index=False)
        logger.info(f"[write] {CLEANING_SUMMARY_PATH}")

        logger.info("=" * 70)
        logger.info("Running post-cleaning validation (src/validation.py)")
        logger.info("=" * 70)
        messages = validate_all(dfs, original_rows,
                                 {name: int(df["excluded"].sum()) for name, df in dfs.items()})
        for m in messages:
            logger.info(f"[validate] {m}")
        logger.info(f"All {len(messages)} validation checks passed.")

    except ValidationFailure as e:
        logger.error(f"VALIDATION FAILED:\n{e}")
        sys.exit(1)

    print()
    print(summary.to_string(index=False))
    return dfs, summary


if __name__ == "__main__":
    main()
