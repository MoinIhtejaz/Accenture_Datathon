"""
NovaCorp People Analytics Challenge — Validation / Integrity Checks
====================================================================

Reusable, dataset-agnostic assertion helpers, plus a schema-aware orchestrator
(`validate_all`) wired specifically to employees.csv / attrition_log.csv /
engagement.csv / performance.csv.

Design intent: every individual `assert_*` function takes plain DataFrames/columns
and is independent of "cleaning" — they can be run against raw data, cleaned data,
or any future dataset with a similar shape. `validate_all` is what `clean_data.py`
calls after cleaning to confirm the pipeline did what it claims; it collects every
failure before raising, so a single run reports everything wrong at once rather
than stopping at the first problem.

Also runnable standalone: `python src/validation.py` re-validates whatever is
currently in `data_clean/` against the raw source files, without re-running the
cleaning pipeline. Useful as an independent check that cleaned outputs still match
their contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from load_data import (
    CLEAN_DATA_DIR,
    COMPA_RATIO_PLAUSIBLE_RANGE,
    CYCLE_GRACE_DAYS,
    CYCLE_WINDOWS,
    ENGAGEMENT_DIMENSIONS,
    ENGAGEMENT_SCALE_RANGE,
    EXPECTED_CATEGORIES,
    GOAL_ACHIEVEMENT_RANGE,
    ROLE_LEVEL_RANGE,
    WINDOW_END,
    WINDOW_START,
    load_raw_datasets,
)


class ValidationFailure(Exception):
    """Raised by validate_all() when one or more integrity checks fail. Carries
    the full list of individual failure messages, not just the first."""


# ---------------------------------------------------------------------------
# Generic, dataset-agnostic assertion helpers
# Each returns a (passed: bool, message: str) pair rather than raising directly,
# so the orchestrator can collect every failure before deciding whether to raise.
# ---------------------------------------------------------------------------

def check_unique_key(df: pd.DataFrame, cols: list[str], name: str,
                      active_mask: pd.Series | None = None) -> tuple[bool, str]:
    """No duplicate combinations of `cols` among rows where active_mask is True
    (default: all rows). Use active_mask to check uniqueness only among
    not-excluded rows post-cleaning."""
    subset = df if active_mask is None else df[active_mask]
    n_dupes = int(subset.duplicated(subset=cols).sum())
    ok = n_dupes == 0
    msg = f"{name}: {'OK' if ok else f'{n_dupes} duplicate rows on {cols}'}"
    return ok, msg


def check_no_orphans(child_df: pd.DataFrame, child_col: str,
                      parent_ids: set, name: str,
                      active_mask: pd.Series | None = None) -> tuple[bool, str]:
    """Every non-null value in child_df[child_col] (among active_mask rows)
    exists in parent_ids."""
    subset = child_df if active_mask is None else child_df[active_mask]
    vals = subset[child_col].dropna()
    n_orphan = int((~vals.isin(parent_ids)).sum())
    ok = n_orphan == 0
    msg = f"{name}: {'OK' if ok else f'{n_orphan} orphaned {child_col} values'}"
    return ok, msg


def check_date_order(df: pd.DataFrame, start_col: str, end_col: str,
                      name: str, active_mask: pd.Series | None = None) -> tuple[bool, str]:
    """start_col <= end_col wherever both are non-null (among active_mask rows)."""
    subset = df if active_mask is None else df[active_mask]
    both_present = subset[start_col].notna() & subset[end_col].notna()
    n_bad = int((subset.loc[both_present, start_col] > subset.loc[both_present, end_col]).sum())
    ok = n_bad == 0
    msg = f"{name}: {'OK' if ok else f'{n_bad} rows with {start_col} after {end_col}'}"
    return ok, msg


def check_within_range(df: pd.DataFrame, col: str, lo, hi, name: str,
                        active_mask: pd.Series | None = None) -> tuple[bool, str]:
    """Non-null values of df[col] (among active_mask rows) fall within [lo, hi]."""
    subset = df if active_mask is None else df[active_mask]
    vals = subset[col].dropna()
    n_bad = int((~vals.between(lo, hi)).sum())
    ok = n_bad == 0
    msg = f"{name}: {'OK' if ok else f'{n_bad} values of {col} outside [{lo}, {hi}]'}"
    return ok, msg


def check_category_membership(df: pd.DataFrame, col: str, allowed: set, name: str,
                               active_mask: pd.Series | None = None) -> tuple[bool, str]:
    """Non-null values of df[col] (among active_mask rows) are all in `allowed`."""
    subset = df if active_mask is None else df[active_mask]
    vals = subset[col].dropna()
    unexpected = set(vals.unique()) - allowed
    ok = len(unexpected) == 0
    msg = f"{name}: {'OK' if ok else f'unexpected values in {col}: {sorted(unexpected)}'}"
    return ok, msg


def check_no_post_exit_events(event_df: pd.DataFrame, event_date_col: str,
                               employees_df: pd.DataFrame, name: str,
                               active_mask: pd.Series | None = None) -> tuple[bool, str]:
    """Direct enforcement of the standing rule: no event may be dated after the
    employee's own exit_date, or before their own hire_date. This is the
    temporal-leakage guard — the single most important check in this module."""
    subset = event_df if active_mask is None else event_df[active_mask]
    merged = subset.merge(
        employees_df[["employee_id", "hire_date", "exit_date"]],
        on="employee_id", how="left",
    )
    after_exit = int((merged[event_date_col] > merged["exit_date"]).sum())
    before_hire = int((merged[event_date_col] < merged["hire_date"]).sum())
    ok = (after_exit == 0) and (before_hire == 0)
    detail = f"{after_exit} events after exit_date, {before_hire} events before hire_date"
    msg = f"{name}: {'OK' if ok else detail}"
    return ok, msg


def check_row_reconciliation(original_n: int, excluded_n: int, final_n: int,
                              name: str) -> tuple[bool, str]:
    """original_n == excluded_n + final_n — guards against silent row loss or
    double-counting anywhere in the pipeline."""
    ok = original_n == excluded_n + final_n
    msg = (f"{name}: {'OK' if ok else 'MISMATCH'} "
           f"(original={original_n}, excluded={excluded_n}, final={final_n})")
    return ok, msg


def check_expected_missingness_invariant(n_missing: int, n_expected: int,
                                          name: str) -> tuple[bool, str]:
    """A documented EXPECTED MISSINGNESS pattern (e.g. exit_date null count ==
    active headcount) still holds exactly. If this ever fails, the missingness
    is no longer 'expected' and must be re-investigated, not waved through."""
    ok = n_missing == n_expected
    msg = (f"{name}: {'OK' if ok else 'MISMATCH'} "
           f"(n_missing={n_missing}, expected={n_expected})")
    return ok, msg


# ---------------------------------------------------------------------------
# Orchestrator: wires the generic helpers to the specific 4-file schema
# ---------------------------------------------------------------------------

def validate_all(cleaned: dict[str, pd.DataFrame], raw_row_counts: dict[str, int],
                  excluded_counts: dict[str, int]) -> list[str]:
    """Run every integrity check relevant to the cleaned NovaCorp datasets.
    Returns the list of passing/failing messages (for logging) and raises
    ValidationFailure if anything failed. `cleaned` dicts must include the
    `excluded` boolean column produced by clean_data.py."""
    emp = cleaned["employees"]
    att = cleaned["attrition_log"]
    eng = cleaned["engagement"]
    perf = cleaned["performance"]

    active_emp = ~emp["excluded"]
    active_att = ~att["excluded"]
    active_eng = ~eng["excluded"]
    active_perf = ~perf["excluded"]

    emp_ids = set(emp.loc[active_emp, "employee_id"])

    results: list[tuple[bool, str]] = []

    # Primary-key uniqueness (among not-excluded rows only)
    results.append(check_unique_key(emp, ["employee_id"], "employees.employee_id unique", active_emp))
    results.append(check_unique_key(att, ["employee_id"], "attrition_log.employee_id unique", active_att))
    results.append(check_unique_key(eng, ["employee_id", "wave_number"], "engagement.(employee_id,wave_number) unique", active_eng))
    results.append(check_unique_key(perf, ["employee_id", "review_cycle"], "performance.(employee_id,review_cycle) unique", active_perf))

    # Referential integrity (among not-excluded rows only)
    results.append(check_no_orphans(att, "employee_id", emp_ids, "attrition_log.employee_id -> employees", active_att))
    results.append(check_no_orphans(eng, "employee_id", emp_ids, "engagement.employee_id -> employees", active_eng))
    results.append(check_no_orphans(perf, "employee_id", emp_ids, "performance.employee_id -> employees", active_perf))

    # Date ordering (core identity fields only; among not-excluded rows)
    results.append(check_date_order(emp, "hire_date", "exit_date", "employees.hire_date <= exit_date", active_emp))

    # Window bounds
    results.append(check_within_range(emp, "exit_date", WINDOW_START, WINDOW_END,
                                       "employees.exit_date within observation window",
                                       active_emp & emp["exit_date"].notna()))
    results.append(check_within_range(att, "exit_date", WINDOW_START, WINDOW_END,
                                       "attrition_log.exit_date within observation window", active_att))
    results.append(check_within_range(eng, "survey_date", WINDOW_START, WINDOW_END,
                                       "engagement.survey_date within observation window", active_eng))
    results.append(check_within_range(perf, "review_date", WINDOW_START, WINDOW_END,
                                       "performance.review_date within observation window", active_perf))

    # Value ranges
    results.append(check_within_range(emp, "role_level", *ROLE_LEVEL_RANGE, "employees.role_level in range", active_emp))
    results.append(check_within_range(emp, "salary", 0.01, float("inf"), "employees.salary positive", active_emp))
    results.append(check_within_range(perf, "goal_achievement_score", *GOAL_ACHIEVEMENT_RANGE, "performance.goal_achievement_score in range", active_perf))
    responded = active_eng & eng["response_flag"]
    for dim in ENGAGEMENT_DIMENSIONS:
        results.append(check_within_range(eng, dim, *ENGAGEMENT_SCALE_RANGE, f"engagement.{dim} in 1-5 (responded rows)", responded))
    results.append(check_within_range(emp, "compa_ratio", *COMPA_RATIO_PLAUSIBLE_RANGE,
                                       "employees.compa_ratio within screening band (indicative only, see DEC-007)", active_emp))

    # Derived-flag recomputation checks: confirm clean_data.py's flags are
    # actually reproducible from the raw inputs, not just self-consistent.
    if "tenure_months_recomputed" in emp.columns:
        end_dates = emp["exit_date"].fillna(WINDOW_END)
        expected_tenure = (
            (end_dates.dt.year - emp["hire_date"].dt.year) * 12
            + (end_dates.dt.month - emp["hire_date"].dt.month) + 1
        )
        n_mismatch = int((emp["tenure_months_recomputed"] != expected_tenure).sum())
        results.append((n_mismatch == 0,
                         f"employees.tenure_months_recomputed reproducible from hire/exit dates: "
                         f"{'OK' if n_mismatch == 0 else f'{n_mismatch} mismatches'}"))
        expected_reliable = (emp["tenure_months"] - expected_tenure).abs().le(1)
        n_flag_mismatch = int((emp["tenure_months_reliable"] != expected_reliable).sum())
        results.append((n_flag_mismatch == 0,
                         f"employees.tenure_months_reliable flag reproducible: "
                         f"{'OK' if n_flag_mismatch == 0 else f'{n_flag_mismatch} mismatches'}"))

    if "review_cycle_reliable" in perf.columns:
        def _in_window_with_grace(row):
            lo, hi = CYCLE_WINDOWS[row["review_cycle"]]
            return lo <= row["review_date"] <= hi + pd.Timedelta(days=CYCLE_GRACE_DAYS)
        expected_reliable = perf.apply(_in_window_with_grace, axis=1)
        n_mismatch = int((perf["review_cycle_reliable"] != expected_reliable).sum())
        results.append((n_mismatch == 0,
                         f"performance.review_cycle_reliable flag reproducible: "
                         f"{'OK' if n_mismatch == 0 else f'{n_mismatch} mismatches'}"))

    # Category membership
    for dataset_name, df, active_mask in [
        ("employees", emp, active_emp), ("attrition_log", att, active_att),
        ("performance", perf, active_perf),
    ]:
        for col, allowed in EXPECTED_CATEGORIES.get(dataset_name, {}).items():
            results.append(check_category_membership(df, col, allowed, f"{dataset_name}.{col} category membership", active_mask))

    # Temporal leakage guard — the standing "never use post-exit information" rule
    results.append(check_no_post_exit_events(eng, "survey_date", emp, "engagement: no survey after exit / before hire", active_eng))
    results.append(check_no_post_exit_events(perf, "review_date", emp, "performance: no review after exit / before hire", active_perf))

    # Row-count reconciliation (original = excluded + final, per dataset)
    for name, cdf in cleaned.items():
        n_excluded = int(cdf["excluded"].sum())
        n_final = int((~cdf["excluded"]).sum())
        results.append(check_row_reconciliation(raw_row_counts[name], n_excluded, n_final, f"{name} row reconciliation"))
        # cross-check against what clean_data.py itself reported excluding
        ok = n_excluded == excluded_counts[name]
        results.append((ok, f"{name}: exclusion count matches cleaning log "
                             f"({'OK' if ok else f'{n_excluded} vs {excluded_counts[name]} reported'})"))

    # Documented EXPECTED MISSINGNESS invariants still hold post-cleaning
    n_active = int((emp["status"] == "active").sum())
    results.append(check_expected_missingness_invariant(
        int(emp["exit_date"].isna().sum()), n_active, "employees.exit_date null count == active headcount"))
    results.append(check_expected_missingness_invariant(
        int(emp["manager_id"].isna().sum()), 1, "employees.manager_id null count == 1 (top of hierarchy)"))
    n_non_respondents = int((~eng["response_flag"]).sum())
    for dim in ENGAGEMENT_DIMENSIONS:
        results.append(check_expected_missingness_invariant(
            int(eng[dim].isna().sum()), n_non_respondents, f"engagement.{dim} null count == non-respondent count"))

    messages = [m for _, m in results]
    failures = [m for ok, m in results if not ok]
    if failures:
        raise ValidationFailure(
            f"{len(failures)} of {len(results)} validation checks failed:\n  - "
            + "\n  - ".join(failures)
        )
    return messages


# ---------------------------------------------------------------------------
# Standalone entry point: re-validate whatever is currently in data_clean/
# ---------------------------------------------------------------------------

def _load_cleaned_from_disk() -> dict[str, pd.DataFrame]:
    paths = {
        "employees": CLEAN_DATA_DIR / "employees_clean.csv",
        "attrition_log": CLEAN_DATA_DIR / "attrition_log_clean.csv",
        "engagement": CLEAN_DATA_DIR / "engagement_clean.csv",
        "performance": CLEAN_DATA_DIR / "performance_clean.csv",
    }
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Cleaned data not found. Run `python src/clean_data.py` first. "
            f"Missing: {missing}"
        )
    date_cols = {
        "employees": ["hire_date", "exit_date"],
        "attrition_log": ["exit_date"],
        "engagement": ["survey_date"],
        "performance": ["review_date"],
    }
    id_cols = {
        "employees": ["employee_id", "manager_id"],
        "attrition_log": ["employee_id", "manager_id_at_exit"],
        "engagement": ["employee_id"],
        "performance": ["employee_id", "reviewer_id"],
    }
    return {
        name: pd.read_csv(
            path,
            dtype={c: "string" for c in id_cols[name]},
            parse_dates=date_cols[name],
        )
        for name, path in paths.items()
    }


def main():
    raw = load_raw_datasets(parse_dates=True)
    raw_row_counts = {name: len(df) for name, df in raw.items()}
    cleaned = _load_cleaned_from_disk()
    excluded_counts = {name: int(df["excluded"].sum()) for name, df in cleaned.items()}

    try:
        messages = validate_all(cleaned, raw_row_counts, excluded_counts)
    except ValidationFailure as e:
        print("VALIDATION FAILED")
        print(str(e))
        sys.exit(1)

    print(f"All {len(messages)} validation checks passed.")
    for m in messages:
        print(f"  - {m}")


if __name__ == "__main__":
    main()
