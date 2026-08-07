"""
NovaCorp People Analytics Challenge — Employee-Level Master Analytical Dataset
================================================================================

Builds ONE ROW PER EMPLOYEE from the four cleaned tables in `data_clean/`
(produced by `src/clean_data.py` — this module never reads the raw CSVs
directly, and never writes back to `data_clean/` or the raw files).

Governing design rule (see docs/decision_log.md, CLAUDE.md Section 18, and the
hypothesis register's leakage-risk fields on every hypothesis): every
engagement and performance record used to build a feature for a given employee
must be dated on or before that employee's own CUTOFF DATE —

    cutoff_date = exit_date                  if the employee departed
                = 2025-12-31 (WINDOW_END)     if the employee is still active

and never before their hire_date. This is computed once per employee and
enforced identically for every feature in this module. No feature anywhere in
this table can "see" a wave or review that happened after the employee left
(or, for the still-active population, after the observation window closes).

Retrospective attrition fields — examined explicitly, not assumed:
`regrettable_flag`, `performance_band_at_exit`, `stated_exit_reason`,
`pathway`, `notice_period_served`, `salary_at_exit`, and `manager_id_at_exit`
are all recorded at or after the exit event (CLAUDE.md Section 18). None of
them can ever be known before an employee leaves, so none of them appear as
PREDICTOR/feature columns in this table. They appear ONLY inside the clearly
separated OUTCOME block at the end of the table (see docs/feature_dictionary.md),
used to construct labels for what already happened, never to explain or
predict it.

One-to-many joins (engagement: up to 5 rows/employee; performance: up to 3
rows/employee) are never merged directly into the employee grain. Each is
first filtered to the leakage-safe eligible window, then AGGREGATED to exactly
one row per employee_id (with an explicit uniqueness assertion immediately
after aggregation), and only then left-joined onto the employee base — so the
final table can never fan out beyond one row per employee.

Outputs:
  - outputs/tables/employee_analytics_master.csv
  - outputs/logs/features.log

Run: `python src/features.py` from anywhere.
"""

from __future__ import annotations

import logging
import sys

import numpy as np
import pandas as pd

from load_data import (
    CLEAN_DATA_DIR,
    ENGAGEMENT_DIMENSIONS,
    OUTPUT_LOGS_DIR,
    OUTPUT_TABLES_DIR,
    WINDOW_END,
)
from validation import check_no_orphans, check_unique_key

MASTER_PATH = OUTPUT_TABLES_DIR / "employee_analytics_master.csv"
LOG_PATH = OUTPUT_LOGS_DIR / "features.log"

# 1-5 scale midpoint is 3; "low" is anything at or below the point just under
# the midpoint. Documented, not hidden — same screening-threshold spirit as
# docs/decision_log.md DEC-007.
LOW_SCORE_THRESHOLD = 2

RATING_ORDINAL = {
    "Unsatisfactory": 1,
    "Below Expectations": 2,
    "Meets Expectations": 3,
    "High Performer": 4,
    "Outstanding": 5,
}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger() -> logging.Logger:
    OUTPUT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("features")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


logger = setup_logger()


# ---------------------------------------------------------------------------
# Loading (from data_clean/, never from raw CSVs)
# ---------------------------------------------------------------------------

def load_cleaned_datasets() -> dict[str, pd.DataFrame]:
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
    dfs = {}
    for name in ["employees", "attrition_log", "engagement", "performance"]:
        path = CLEAN_DATA_DIR / f"{name}_clean.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found — run `python src/clean_data.py` first."
            )
        dfs[name] = pd.read_csv(
            path,
            dtype={c: "string" for c in id_cols[name]},
            parse_dates=date_cols[name],
        )
    return dfs


# ---------------------------------------------------------------------------
# Cutoff / eligibility
# ---------------------------------------------------------------------------

def compute_cutoff_dates(base: pd.DataFrame) -> pd.Series:
    """cutoff_date = exit_date for departed employees, WINDOW_END for active
    ones. This is the single leakage boundary every feature below respects."""
    return base["exit_date"].fillna(WINDOW_END)


def filter_eligible(events: pd.DataFrame, date_col: str,
                     employee_bounds: pd.DataFrame) -> pd.DataFrame:
    """Keep only event rows dated within [hire_date, cutoff_date] for their own
    employee. `employee_bounds` must have employee_id, hire_date, cutoff_date."""
    merged = events.merge(employee_bounds, on="employee_id", how="inner")
    eligible = merged[
        (merged[date_col] >= merged["hire_date"]) & (merged[date_col] <= merged["cutoff_date"])
    ].copy()
    n_dropped_future = int((merged[date_col] > merged["cutoff_date"]).sum())
    n_dropped_prehire = int((merged[date_col] < merged["hire_date"]).sum())
    logger.info(
        f"[eligibility:{date_col}] {len(merged)} candidate rows -> {len(eligible)} eligible "
        f"({n_dropped_future} dropped as post-cutoff, {n_dropped_prehire} dropped as pre-hire — "
        "both expected to be 0 per the audit, kept as a live safety net)."
    )
    return eligible


# ---------------------------------------------------------------------------
# Generic trend helper
# ---------------------------------------------------------------------------

def compute_slope(x, y) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~np.isnan(y) & ~np.isnan(x)
    x, y = x[mask], y[mask]
    if len(x) < 2 or np.ptp(x) == 0:
        return np.nan
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)


# ---------------------------------------------------------------------------
# Engagement features
# ---------------------------------------------------------------------------

def _engagement_dimension_features(scored: pd.DataFrame, dim: str) -> dict:
    """scored: this employee's eligible, responded rows with a non-null `dim`
    value, sorted by wave_number ascending."""
    n = len(scored)
    prefix = dim
    if n == 0:
        return {
            f"{prefix}_latest_score": np.nan, f"{prefix}_earliest_score": np.nan,
            f"{prefix}_abs_change": np.nan, f"{prefix}_slope_per_wave": np.nan,
            f"{prefix}_volatility": np.nan, f"{prefix}_persistent_low_flag": np.nan,
            f"{prefix}_consecutive_deterioration_flag": np.nan,
        }
    values = scored[dim].to_numpy()
    waves = scored["wave_number"].to_numpy()
    out = {
        f"{prefix}_latest_score": float(values[-1]),
        f"{prefix}_earliest_score": float(values[0]),
        f"{prefix}_abs_change": float(values[-1] - values[0]) if n >= 2 else np.nan,
        f"{prefix}_slope_per_wave": compute_slope(waves, values) if n >= 2 else np.nan,
        f"{prefix}_volatility": float(np.std(values, ddof=1)) if n >= 2 else np.nan,
        f"{prefix}_persistent_low_flag": bool(np.sum(values <= LOW_SCORE_THRESHOLD) >= 2),
    }
    if n >= 2:
        diffs = np.diff(values)
        run = longest = 0
        for d in diffs:
            run = run + 1 if d < 0 else 0
            longest = max(longest, run)
        out[f"{prefix}_consecutive_deterioration_flag"] = bool(longest >= 2)
    else:
        out[f"{prefix}_consecutive_deterioration_flag"] = np.nan
    return out


def _survey_response_features(g: pd.DataFrame) -> dict:
    """g: ALL of this employee's eligible engagement rows (responded or not),
    sorted by wave_number ascending — response-behaviour is a wave-level fact,
    not a per-dimension one (response_flag is recorded once per wave for all
    8 dimensions simultaneously), so this is computed once, not per dimension."""
    n_waves = len(g)
    if n_waves == 0:
        return {
            "engagement_n_waves_available": 0, "engagement_n_responses_available": 0,
            "engagement_response_rate": np.nan, "engagement_recent_non_response_flag": np.nan,
            "engagement_consecutive_non_responses": np.nan,
            "engagement_responder_to_nonresponder_transition_flag": np.nan,
        }
    flags = g["response_flag"].astype(bool).tolist()
    n_resp = sum(flags)
    streak = 0
    for f in reversed(flags):
        if not f:
            streak += 1
        else:
            break
    transition = (
        any(flags[i] and not flags[i + 1] for i in range(len(flags) - 1))
        if n_waves >= 2 else np.nan
    )
    return {
        "engagement_n_waves_available": n_waves,
        "engagement_n_responses_available": n_resp,
        "engagement_response_rate": n_resp / n_waves,
        "engagement_recent_non_response_flag": bool(not flags[-1]),
        "engagement_consecutive_non_responses": streak,
        "engagement_responder_to_nonresponder_transition_flag": transition,
    }


def aggregate_engagement_features(eligible_eng: pd.DataFrame) -> pd.DataFrame:
    """One row per employee_id — asserted immediately below."""
    records = []
    for emp_id, g in eligible_eng.sort_values("wave_number").groupby("employee_id", sort=False):
        row = {"employee_id": emp_id}
        row.update(_survey_response_features(g))
        responded = g[g["response_flag"].astype(bool)]
        for dim in ENGAGEMENT_DIMENSIONS:
            scored = responded.loc[responded[dim].notna(), ["wave_number", dim]]
            row.update(_engagement_dimension_features(scored, dim))
        records.append(row)
    result = pd.DataFrame(records)
    ok, msg = check_unique_key(result, ["employee_id"], "engagement_features aggregation")
    assert ok, msg
    logger.info(f"[aggregate] engagement_features: {len(result)} employees, {result.shape[1]} columns. {msg}")
    return result


# ---------------------------------------------------------------------------
# Performance features
# ---------------------------------------------------------------------------

def _performance_features(g: pd.DataFrame) -> dict:
    """g: this employee's eligible performance rows, sorted by review_date
    ascending."""
    n = len(g)
    if n == 0:
        return {
            "performance_n_reviews_available": 0,
            "performance_latest_rating": np.nan, "performance_previous_rating": np.nan,
            "performance_rating_change_ordinal": np.nan,
            "performance_goal_achievement_latest": np.nan,
            "performance_goal_achievement_trend": np.nan,
            "performance_promotion_recommendation_count": 0,
            "performance_promotion_recommendation_rate": np.nan,
            "performance_promotion_recommendation_ever": np.nan,
        }
    latest = g.iloc[-1]
    out = {
        "performance_n_reviews_available": n,
        "performance_latest_rating": latest["performance_rating"],
        "performance_goal_achievement_latest": latest["goal_achievement_score"],
    }
    if n >= 2:
        prev = g.iloc[-2]
        out["performance_previous_rating"] = prev["performance_rating"]
        lo = RATING_ORDINAL.get(latest["performance_rating"])
        po = RATING_ORDINAL.get(prev["performance_rating"])
        out["performance_rating_change_ordinal"] = (lo - po) if (lo is not None and po is not None) else np.nan
        goal_scores = g["goal_achievement_score"].dropna().to_numpy()
        out["performance_goal_achievement_trend"] = (
            compute_slope(np.arange(len(goal_scores)), goal_scores) if len(goal_scores) >= 2 else np.nan
        )
    else:
        out["performance_previous_rating"] = np.nan
        out["performance_rating_change_ordinal"] = np.nan
        out["performance_goal_achievement_trend"] = np.nan

    n_promo = int(g["promotion_recommendation"].astype(bool).sum())
    out["performance_promotion_recommendation_count"] = n_promo
    out["performance_promotion_recommendation_rate"] = n_promo / n
    out["performance_promotion_recommendation_ever"] = bool(n_promo > 0)
    return out


def aggregate_performance_features(eligible_perf: pd.DataFrame) -> pd.DataFrame:
    """One row per employee_id — asserted immediately below."""
    records = []
    for emp_id, g in eligible_perf.sort_values("review_date").groupby("employee_id", sort=False):
        row = {"employee_id": emp_id}
        row.update(_performance_features(g))
        records.append(row)
    result = pd.DataFrame(records)
    ok, msg = check_unique_key(result, ["employee_id"], "performance_features aggregation")
    assert ok, msg
    logger.info(f"[aggregate] performance_features: {len(result)} employees, {result.shape[1]} columns. {msg}")
    return result


# ---------------------------------------------------------------------------
# Attrition outcome labels — OUTCOMES ONLY, never predictors (see module docstring)
# ---------------------------------------------------------------------------

def compute_attrition_outcomes(base: pd.DataFrame, att: pd.DataFrame) -> pd.DataFrame:
    ok, msg = check_unique_key(att, ["employee_id"], "attrition_log (pre-outcome-merge)")
    assert ok, msg

    ok, msg = check_no_orphans(att, "employee_id", set(base["employee_id"]), "attrition_log -> employees")
    assert ok, msg

    out = base[["employee_id", "status"]].merge(att, on="employee_id", how="left")

    out["departed"] = out["status"] == "departed"
    out["voluntary_exit"] = out["exit_type"] == "voluntary"
    is_regrettable = out["regrettable_flag"] == True  # noqa: E712 — NaN (active employees) -> False, cleanly, no fillna downcast warning
    out["regrettable_exit"] = out["departed"] & is_regrettable
    out["regrettable_voluntary_exit"] = out["voluntary_exit"] & is_regrettable
    out["pull_exit"] = out["departed"] & (out["pathway"] == "pull")

    n_reg = int(out["regrettable_exit"].sum())
    n_reg_vol = int(out["regrettable_voluntary_exit"].sum())
    identical = n_reg == n_reg_vol
    logger.info(
        f"[outcomes] regrettable_exit (n={n_reg}) vs regrettable_voluntary_exit (n={n_reg_vol}): "
        f"{'IDENTICAL — confirmed empirically, every regrettable exit in this data is voluntary' if identical else 'DIFFER — some regrettable exits are involuntary, kept as distinct labels'}."
    )

    keep_cols = [
        "employee_id", "departed", "voluntary_exit", "regrettable_exit",
        "regrettable_voluntary_exit", "pull_exit",
        "exit_type", "pathway", "stated_exit_reason", "performance_band_at_exit",
    ]
    return out[keep_cols]


# ---------------------------------------------------------------------------
# Integrity checks
# ---------------------------------------------------------------------------

def run_integrity_checks(master: pd.DataFrame, base: pd.DataFrame,
                          eligible_eng: pd.DataFrame, eligible_perf: pd.DataFrame) -> list[str]:
    messages = []

    # 1. One row per employee
    ok = master["employee_id"].is_unique
    messages.append(f"master.employee_id unique: {'OK' if ok else 'FAIL'}")
    assert ok, "master_dataset has duplicate employee_id — one-row-per-employee contract broken"

    ok = len(master) == len(base)
    messages.append(f"master row count == base employee count ({len(base)}): {'OK' if ok else f'FAIL ({len(master)})'}")
    assert ok, f"master has {len(master)} rows, expected {len(base)} (no fan-out, no drops)"

    ok = set(master["employee_id"]) == set(base["employee_id"])
    messages.append(f"master employee_id set == base employee_id set: {'OK' if ok else 'FAIL'}")
    assert ok, "master's employee_id set does not exactly match the base population"

    # 2. No unintended duplication from the one-to-many sources
    ok, msg = check_unique_key(eligible_eng, ["employee_id", "wave_number"],
                                "eligible_eng (employee_id, wave_number) still unique pre-aggregation")
    messages.append(msg)
    assert ok, msg

    ok, msg = check_unique_key(eligible_perf, ["employee_id", "review_date"],
                                "eligible_perf (employee_id, review_date) still unique pre-aggregation")
    messages.append(msg)
    assert ok, msg

    # 3. Correct temporal boundaries — re-verify directly on the eligible tables
    bad_eng = eligible_eng[(eligible_eng["survey_date"] > eligible_eng["cutoff_date"]) |
                            (eligible_eng["survey_date"] < eligible_eng["hire_date"])]
    ok = len(bad_eng) == 0
    messages.append(f"eligible_eng respects [hire_date, cutoff_date] for every row: {'OK' if ok else f'FAIL ({len(bad_eng)} violations)'}")
    assert ok, f"{len(bad_eng)} engagement rows used outside their own employee's valid window — leakage"

    bad_perf = eligible_perf[(eligible_perf["review_date"] > eligible_perf["cutoff_date"]) |
                              (eligible_perf["review_date"] < eligible_perf["hire_date"])]
    ok = len(bad_perf) == 0
    messages.append(f"eligible_perf respects [hire_date, cutoff_date] for every row: {'OK' if ok else f'FAIL ({len(bad_perf)} violations)'}")
    assert ok, f"{len(bad_perf)} performance rows used outside their own employee's valid window — leakage"

    # 4. Joins behaved as expected (no null keys, no silent row loss anywhere)
    ok = master["employee_id"].notna().all()
    messages.append(f"master has no null employee_id: {'OK' if ok else 'FAIL'}")
    assert ok, "master contains null employee_id after merges"

    for col in ["departed", "voluntary_exit"]:
        ok = master[col].notna().all()
        messages.append(f"master.{col} populated for every employee: {'OK' if ok else 'FAIL'}")
        assert ok, f"master.{col} has unexpected nulls — outcome merge did not cover the full base population"

    return messages


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_master_dataset() -> tuple[pd.DataFrame, dict]:
    logger.info("=" * 70)
    logger.info("Building employee-level master analytical dataset")
    logger.info("=" * 70)

    dfs = load_cleaned_datasets()
    emp = dfs["employees"]
    base = emp.loc[~emp["excluded"]].copy()
    logger.info(f"[load] base population (employees_clean, excluded==False): {len(base)} rows")

    base["cutoff_date"] = compute_cutoff_dates(base)
    employee_bounds = base[["employee_id", "hire_date", "cutoff_date"]]

    eng = dfs["engagement"]
    eng_usable = eng.loc[~eng["excluded"]]
    eligible_eng = filter_eligible(eng_usable, "survey_date", employee_bounds)

    perf = dfs["performance"]
    perf_usable = perf.loc[~perf["excluded"]]
    eligible_perf = filter_eligible(perf_usable, "review_date", employee_bounds)

    engagement_features = aggregate_engagement_features(eligible_eng)
    performance_features = aggregate_performance_features(eligible_perf)

    att = dfs["attrition_log"]
    att_usable = att.loc[~att["excluded"]]
    outcomes = compute_attrition_outcomes(base, att_usable)

    # --- Assemble: every merge is LEFT from `base`, so base's row count is invariant ---
    n0 = len(base)
    master = base.merge(engagement_features, on="employee_id", how="left")
    assert len(master) == n0, "engagement merge changed row count — fan-out or drop occurred"
    master = master.merge(performance_features, on="employee_id", how="left")
    assert len(master) == n0, "performance merge changed row count — fan-out or drop occurred"
    master = master.merge(outcomes, on="employee_id", how="left")
    assert len(master) == n0, "outcomes merge changed row count — fan-out or drop occurred"

    # Denominator/count columns are known-zero (not unknown) when an employee has
    # no eligible records at all — everything else stays NaN (genuinely unknown).
    for col in ["engagement_n_waves_available", "engagement_n_responses_available"]:
        master[col] = master[col].fillna(0).astype(int)
    for col in ["performance_n_reviews_available", "performance_promotion_recommendation_count"]:
        master[col] = master[col].fillna(0).astype(int)

    # Employee characteristics rename/selection (per the requested feature list)
    master = master.rename(columns={
        "tenure_months": "tenure_months_raw",
        "tenure_months_recomputed": "tenure_months",
        "tenure_months_reliable": "tenure_months_raw_reliable_flag",
        "legacy_entity_code": "legacy_entity",
    })

    id_cols = ["employee_id", "manager_id"]
    context_cols = [
        "status", "hire_date", "exit_date", "cutoff_date",
        "tenure_months", "tenure_months_raw", "tenure_months_raw_reliable_flag",
        "salary", "compa_ratio", "compa_ratio_outside_screening_band",
        "role_family", "job_title", "role_level", "department",
        "hire_source", "legacy_entity", "contract_type",
        "hipo_flag", "promotion_eligible", "acting_appointment",
        "data_source_system",
    ]
    fairness_audit_only_cols = ["gender", "age_band", "cultural_background"]
    engagement_meta_cols = [
        "engagement_n_waves_available", "engagement_n_responses_available",
        "engagement_response_rate", "engagement_recent_non_response_flag",
        "engagement_consecutive_non_responses",
        "engagement_responder_to_nonresponder_transition_flag",
    ]
    engagement_dim_cols = [
        f"{dim}{suffix}"
        for dim in ENGAGEMENT_DIMENSIONS
        for suffix in ["_latest_score", "_earliest_score", "_abs_change", "_slope_per_wave",
                       "_volatility", "_persistent_low_flag", "_consecutive_deterioration_flag"]
    ]
    performance_cols = [
        "performance_n_reviews_available", "performance_latest_rating", "performance_previous_rating",
        "performance_rating_change_ordinal", "performance_goal_achievement_latest",
        "performance_goal_achievement_trend", "performance_promotion_recommendation_count",
        "performance_promotion_recommendation_rate", "performance_promotion_recommendation_ever",
    ]
    outcome_cols = [
        "departed", "voluntary_exit", "regrettable_exit", "regrettable_voluntary_exit", "pull_exit",
        "exit_type", "pathway", "stated_exit_reason", "performance_band_at_exit",
    ]

    ordered_cols = (id_cols + context_cols + fairness_audit_only_cols
                    + engagement_meta_cols + engagement_dim_cols
                    + performance_cols + outcome_cols)
    missing = set(ordered_cols) - set(master.columns)
    assert not missing, f"Expected columns missing from assembled master: {missing}"
    master = master[ordered_cols]

    logger.info(f"[assemble] master dataset: {master.shape[0]} rows x {master.shape[1]} columns")

    messages = run_integrity_checks(master, base, eligible_eng, eligible_perf)
    for m in messages:
        logger.info(f"[integrity] {m}")
    logger.info(f"All {len(messages)} integrity checks passed.")

    stats = {
        "n_employees": len(master),
        "n_columns": master.shape[1],
        "n_departed": int(master["departed"].sum()),
        "n_active": int((~master["departed"]).sum()),
        "n_voluntary_exit": int(master["voluntary_exit"].sum()),
        "n_regrettable_exit": int(master["regrettable_exit"].sum()),
        "n_regrettable_voluntary_exit": int(master["regrettable_voluntary_exit"].sum()),
        "n_pull_exit": int(master["pull_exit"].sum()),
        "n_zero_engagement_history": int((master["engagement_n_waves_available"] == 0).sum()),
        "n_zero_performance_history": int((master["performance_n_reviews_available"] == 0).sum()),
    }
    return master, stats


def main():
    master, stats = build_master_dataset()
    OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    master.to_csv(MASTER_PATH, index=False)
    logger.info(f"[write] {MASTER_PATH} ({master.shape[0]} rows, {master.shape[1]} columns)")

    print()
    print(f"Master dataset shape: {master.shape[0]} rows x {master.shape[1]} columns")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    return master, stats


if __name__ == "__main__":
    main()
