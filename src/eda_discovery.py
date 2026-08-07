"""
NovaCorp People Analytics Challenge — Broad Discovery EDA
============================================================

Systematic, hypothesis-register-driven exploratory analysis over
outputs/tables/employee_analytics_master.csv. This script computes every
statistic reported in docs/findings_register.md — nothing in that document is
invented; every number traces back to a run of this file.

This is Phase 1 (broad descriptive scan) per docs/analysis_plan.md: it
produces candidate findings and effect sizes, not final conclusions. No
storyline is selected here. Multiple-comparison correction (Benjamini-Hochberg)
is applied within each family of related tests, per analysis_plan.md Section 7.

Run: `python src/eda_discovery.py` from anywhere. Writes a full log to
outputs/logs/eda_discovery.log (this is the primary evidence trail — the
console output is a duplicate of it).
"""

from __future__ import annotations

import logging
import sys

import numpy as np
import pandas as pd
from scipy import stats

from load_data import OUTPUT_LOGS_DIR, OUTPUT_TABLES_DIR, ENGAGEMENT_DIMENSIONS

MASTER_PATH = OUTPUT_TABLES_DIR / "employee_analytics_master.csv"
LOG_PATH = OUTPUT_LOGS_DIR / "eda_discovery.log"

MIN_CELL_N = 30  # per analysis_plan.md Section 7 minimum-sample-size rule


def setup_logger():
    OUTPUT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("eda_discovery")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(message)s")
    fh = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


logger = setup_logger()


def hdr(title):
    logger.info("")
    logger.info("=" * 90)
    logger.info(title)
    logger.info("=" * 90)


def sub(title):
    logger.info("")
    logger.info("-" * 70)
    logger.info(title)
    logger.info("-" * 70)


# ---------------------------------------------------------------------------
# Generic stat helpers
# ---------------------------------------------------------------------------

def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    denom = 1 + z**2 / n
    centre = p + z**2 / (2 * n)
    adj = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)
    return ((centre - adj) / denom, (centre + adj) / denom)


def rate_table(df, group_col, outcome_col, min_n=MIN_CELL_N):
    """Rate of outcome_col (bool) by group_col, with Wilson 95% CI and n."""
    rows = []
    for g, sub_df in df.groupby(group_col, observed=True):
        n = len(sub_df)
        k = int(sub_df[outcome_col].sum())
        rate = k / n if n else np.nan
        lo, hi = wilson_ci(k, n)
        rows.append({group_col: g, "n": n, "k": k, "rate": rate,
                     "ci_lo": lo, "ci_hi": hi, "adequate_n": n >= min_n})
    return pd.DataFrame(rows).sort_values("rate", ascending=False)


def chi2_effect(df, group_col, outcome_col):
    ct = pd.crosstab(df[group_col], df[outcome_col])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    n = ct.values.sum()
    k = min(ct.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * k)) if k > 0 else np.nan
    return chi2, p, cramers_v, n


def bh_correct(pvals):
    pvals = np.asarray(pvals, dtype=float)
    n = len(pvals)
    order = np.argsort(pvals)
    ranked = pvals[order]
    q = ranked * n / (np.arange(n) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    q_full = np.empty(n)
    q_full[order] = np.clip(q, 0, 1)
    return q_full


def mannwhitney(a, b):
    a = pd.Series(a).dropna()
    b = pd.Series(b).dropna()
    if len(a) < 5 or len(b) < 5:
        return np.nan, np.nan, len(a), len(b)
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    return u, p, len(a), len(b)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_master() -> pd.DataFrame:
    bool_like = [
        "departed", "voluntary_exit", "regrettable_exit", "regrettable_voluntary_exit",
        "pull_exit", "hipo_flag", "promotion_eligible", "acting_appointment",
        "tenure_months_raw_reliable_flag", "compa_ratio_outside_screening_band",
    ]
    df = pd.read_csv(MASTER_PATH, parse_dates=["hire_date", "exit_date", "cutoff_date"],
                      low_memory=False)
    for c in bool_like:
        df[c] = df[c].astype(bool)
    return df


# ===========================================================================
# ATTRITION
# ===========================================================================

def section_attrition(m: pd.DataFrame):
    hdr("ATTRITION")
    dims = ["department", "role_family", "role_level", "hire_source", "legacy_entity"]
    for dim in dims:
        sub(f"Voluntary exit rate by {dim}")
        t = rate_table(m, dim, "voluntary_exit")
        logger.info(t.to_string(index=False))
        if t["adequate_n"].all() and m[dim].nunique() > 1:
            chi2, p, v, n = chi2_effect(m, dim, "voluntary_exit")
            logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

        sub(f"Regrettable-voluntary exit rate by {dim}")
        t2 = rate_table(m, dim, "regrettable_voluntary_exit")
        logger.info(t2.to_string(index=False))

    sub("acting_appointment x voluntary_exit")
    t = rate_table(m, "acting_appointment", "voluntary_exit")
    logger.info(t.to_string(index=False))
    chi2, p, v, n = chi2_effect(m, "acting_appointment", "voluntary_exit")
    logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

    sub("hipo_flag x voluntary_exit / regrettable_voluntary_exit")
    for outcome in ["voluntary_exit", "regrettable_voluntary_exit"]:
        t = rate_table(m, "hipo_flag", outcome)
        logger.info(f"-- {outcome} --")
        logger.info(t.to_string(index=False))
        chi2, p, v, n = chi2_effect(m, "hipo_flag", outcome)
        logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

    sub("promotion_eligible x voluntary_exit")
    t = rate_table(m, "promotion_eligible", "voluntary_exit")
    logger.info(t.to_string(index=False))
    chi2, p, v, n = chi2_effect(m, "promotion_eligible", "voluntary_exit")
    logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

    sub("performance_latest_rating (High Performer/Outstanding) x voluntary_exit")
    m2 = m.copy()
    m2["high_performer"] = m2["performance_latest_rating"].isin(["High Performer", "Outstanding"])
    m2 = m2[m2["performance_latest_rating"].notna()]
    t = rate_table(m2, "high_performer", "voluntary_exit")
    logger.info(t.to_string(index=False))
    chi2, p, v, n = chi2_effect(m2, "high_performer", "voluntary_exit")
    logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")
    t2 = rate_table(m2, "high_performer", "regrettable_voluntary_exit")
    logger.info("-- regrettable_voluntary_exit --")
    logger.info(t2.to_string(index=False))

    sub("Tenure (months, recomputed) — leavers vs stayers")
    left = m.loc[m["voluntary_exit"], "tenure_months"]
    stayed = m.loc[~m["departed"], "tenure_months"]
    u, p, na, nb = mannwhitney(left, stayed)
    logger.info(f"voluntary leavers: median={left.median():.1f}, IQR=[{left.quantile(.25):.1f},{left.quantile(.75):.1f}], n={na}")
    logger.info(f"active stayers:    median={stayed.median():.1f}, IQR=[{stayed.quantile(.25):.1f},{stayed.quantile(.75):.1f}], n={nb}")
    logger.info(f"Mann-Whitney U p={p:.2e}")

    sub("Tenure band x voluntary exit rate (early attrition check)")
    m3 = m.copy()
    m3["tenure_band"] = pd.cut(m3["tenure_months"], bins=[-1, 6, 12, 24, 60, 10000],
                                labels=["0-6mo", "7-12mo", "13-24mo", "25-60mo", "60mo+"])
    t = rate_table(m3, "tenure_band", "voluntary_exit")
    logger.info(t.to_string(index=False))

    sub("Salary / compa_ratio — voluntary leavers vs stayers")
    for col in ["salary", "compa_ratio"]:
        left = m.loc[m["voluntary_exit"], col]
        stayed = m.loc[~m["departed"], col]
        u, p, na, nb = mannwhitney(left, stayed)
        logger.info(f"{col}: leavers median={left.median():.3f} vs stayers median={stayed.median():.3f}, "
                    f"Mann-Whitney p={p:.2e}, n_leavers={na}, n_stayers={nb}")

    sub("compa_ratio quartile x voluntary_exit rate (controlling loosely for role_level via quartile-within-level)")
    m4 = m.copy()

    def _safe_qcut(s):
        try:
            codes = pd.qcut(s, 4, labels=False, duplicates="drop")
        except ValueError:
            return pd.Series(np.nan, index=s.index)
        return codes

    label_map = {0: "Q1(low)", 1: "Q2", 2: "Q3", 3: "Q4(high)"}
    m4["compa_quartile_within_level"] = (
        m4.groupby("role_level")["compa_ratio"].transform(_safe_qcut).map(label_map)
    )
    t = rate_table(m4.dropna(subset=["compa_quartile_within_level"]), "compa_quartile_within_level", "voluntary_exit")
    logger.info(t.to_string(index=False))

    sub("days_to_fill x hire_source (context for hiring section)")
    logger.info(m.groupby("hire_source", observed=True)["hire_source"].count().to_string())


# ===========================================================================
# ENGAGEMENT
# ===========================================================================

def section_engagement(m: pd.DataFrame):
    hdr("ENGAGEMENT")

    sub("Response rate distribution & non-response x voluntary_exit")
    t = rate_table(m.dropna(subset=["engagement_recent_non_response_flag"]).assign(
        recent_non_resp=lambda d: d["engagement_recent_non_response_flag"].astype(bool)),
        "recent_non_resp", "voluntary_exit")
    logger.info(t.to_string(index=False))
    m5 = m.dropna(subset=["engagement_recent_non_response_flag"]).copy()
    m5["recent_non_resp"] = m5["engagement_recent_non_response_flag"].astype(bool)
    chi2, p, v, n = chi2_effect(m5, "recent_non_resp", "voluntary_exit")
    logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

    sub("Never-responded-of-surveyed x voluntary_exit")
    m6 = m[m["engagement_n_waves_available"] > 0].copy()
    m6["never_responded"] = m6["engagement_n_responses_available"] == 0
    t = rate_table(m6, "never_responded", "voluntary_exit")
    logger.info(t.to_string(index=False))
    chi2, p, v, n = chi2_effect(m6, "never_responded", "voluntary_exit")
    logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

    sub("Response rate by legacy_entity (bias check)")
    t = m.groupby("legacy_entity", observed=True)["engagement_response_rate"].agg(["mean", "count"])
    logger.info(t.to_string())

    pvals = []
    dim_effects = []
    for dim in ENGAGEMENT_DIMENSIONS:
        latest_col = f"{dim}_latest_score"
        left = m.loc[m["voluntary_exit"], latest_col]
        stayed = m.loc[~m["departed"], latest_col]
        u, p, na, nb = mannwhitney(left, stayed)
        if not np.isnan(p):
            pvals.append(p)
            dim_effects.append((dim, left.median(), stayed.median(), na, nb, p))
    sub("Latest engagement score (each dimension): voluntary leavers vs stayers")
    qvals = bh_correct(pvals)
    for (dim, lm, sm, na, nb, p), q in zip(dim_effects, qvals):
        logger.info(f"{dim}: leaver_median={lm:.2f} stayer_median={sm:.2f} diff={lm-sm:+.2f} "
                    f"n_leaver={na} n_stayer={nb} p={p:.2e} q={q:.2e}")

    sub("persistent_low_flag (each dimension) x voluntary_exit")
    pvals = []
    plf_effects = []
    for dim in ENGAGEMENT_DIMENSIONS:
        col = f"{dim}_persistent_low_flag"
        sub_df = m[m[col].notna()].copy()
        sub_df[col] = sub_df[col].astype(bool)
        if sub_df[col].sum() < MIN_CELL_N:
            continue
        chi2, p, v, n = chi2_effect(sub_df, col, "voluntary_exit")
        t = rate_table(sub_df, col, "voluntary_exit")
        rate_low = t.loc[t[col] == True, "rate"].values
        rate_not = t.loc[t[col] == False, "rate"].values
        pvals.append(p)
        plf_effects.append((dim, rate_low[0] if len(rate_low) else np.nan,
                             rate_not[0] if len(rate_not) else np.nan, v, n, p))
    if pvals:
        qvals = bh_correct(pvals)
        for (dim, rl, rn, v, n, p), q in zip(plf_effects, qvals):
            logger.info(f"{dim}: rate|persistent_low={rl:.3f} rate|not={rn:.3f} CramersV={v:.3f} n={n} p={p:.2e} q={q:.2e}")

    sub("consecutive_deterioration_flag (each dimension) x voluntary_exit")
    pvals = []
    cd_effects = []
    for dim in ENGAGEMENT_DIMENSIONS:
        col = f"{dim}_consecutive_deterioration_flag"
        sub_df = m[m[col].notna()].copy()
        sub_df[col] = sub_df[col].astype(bool)
        if sub_df[col].sum() < MIN_CELL_N:
            continue
        chi2, p, v, n = chi2_effect(sub_df, col, "voluntary_exit")
        t = rate_table(sub_df, col, "voluntary_exit")
        rate_yes = t.loc[t[col] == True, "rate"].values
        rate_no = t.loc[t[col] == False, "rate"].values
        pvals.append(p)
        cd_effects.append((dim, rate_yes[0] if len(rate_yes) else np.nan,
                            rate_no[0] if len(rate_no) else np.nan, v, n, p))
    if pvals:
        qvals = bh_correct(pvals)
        for (dim, ry, rn, v, n, p), q in zip(cd_effects, qvals):
            logger.info(f"{dim}: rate|consec_deterioration={ry:.3f} rate|not={rn:.3f} CramersV={v:.3f} n={n} p={p:.2e} q={q:.2e}")

    sub("Volatility (each dimension): voluntary leavers vs stayers")
    for dim in ENGAGEMENT_DIMENSIONS:
        col = f"{dim}_volatility"
        left = m.loc[m["voluntary_exit"], col]
        stayed = m.loc[~m["departed"], col]
        u, p, na, nb = mannwhitney(left, stayed)
        if not np.isnan(p):
            logger.info(f"{dim}: leaver_median_vol={left.median():.3f} stayer_median_vol={stayed.median():.3f} "
                        f"n_leaver={na} n_stayer={nb} p={p:.2e}")

    sub("Responder->non-responder transition x voluntary_exit")
    m7 = m[m["engagement_responder_to_nonresponder_transition_flag"].notna()].copy()
    m7["transition"] = m7["engagement_responder_to_nonresponder_transition_flag"].astype(bool)
    t = rate_table(m7, "transition", "voluntary_exit")
    logger.info(t.to_string(index=False))
    chi2, p, v, n = chi2_effect(m7, "transition", "voluntary_exit")
    logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")


# ===========================================================================
# CAREER
# ===========================================================================

def section_career(m: pd.DataFrame):
    hdr("CAREER")

    sub("promotion_eligible x promotion_recommendation_ever")
    m8 = m[m["performance_promotion_recommendation_ever"].notna()].copy()
    m8["promo_rec_ever"] = m8["performance_promotion_recommendation_ever"].astype(bool)
    t = rate_table(m8, "promotion_eligible", "promo_rec_ever")
    logger.info(t.to_string(index=False))

    sub("promotion_eligible & high performer, but 0 promotion recommendations -> subsequent voluntary_exit")
    m9 = m8.copy()
    m9["high_perf"] = m9["performance_latest_rating"].isin(["High Performer", "Outstanding"])
    stalled = m9[(m9["promotion_eligible"]) & (m9["high_perf"]) & (~m9["promo_rec_ever"])]
    advancing = m9[(m9["promotion_eligible"]) & (m9["high_perf"]) & (m9["promo_rec_ever"])]
    logger.info(f"stalled (eligible, high-perf, never recommended): n={len(stalled)}, "
                f"voluntary_exit rate={stalled['voluntary_exit'].mean():.3f}")
    logger.info(f"advancing (eligible, high-perf, recommended): n={len(advancing)}, "
                f"voluntary_exit rate={advancing['voluntary_exit'].mean():.3f}")
    if len(stalled) >= MIN_CELL_N and len(advancing) >= MIN_CELL_N:
        combo = pd.concat([stalled.assign(grp="stalled"), advancing.assign(grp="advancing")])
        chi2, p, v, n = chi2_effect(combo, "grp", "voluntary_exit")
        logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

    sub("hipo_flag x promo_rec_ever, and hipo x acting_appointment")
    t = rate_table(m8, "hipo_flag", "promo_rec_ever")
    logger.info(t.to_string(index=False))
    t2 = rate_table(m, "hipo_flag", "acting_appointment")
    logger.info(t2.to_string(index=False))

    sub("acting_appointment x promotion_recommendation_ever, and x voluntary_exit")
    t = rate_table(m8, "acting_appointment", "promo_rec_ever")
    logger.info(t.to_string(index=False))
    t2 = rate_table(m, "acting_appointment", "voluntary_exit")
    logger.info(t2.to_string(index=False))

    sub("Promotion recommendation rate by role_level (bottleneck localisation)")
    t = m8.groupby("role_level", observed=True)["promo_rec_ever"].agg(["mean", "count"])
    logger.info(t.to_string())

    sub("Promotion recommendation rate by legacy_entity, controlling loosely for role_level")
    for level in sorted(m8["role_level"].unique()):
        sub_df = m8[m8["role_level"] == level]
        if sub_df["legacy_entity"].nunique() < 2:
            continue
        t = sub_df.groupby("legacy_entity", observed=True)["promo_rec_ever"].agg(["mean", "count"])
        if (t["count"] >= 15).any():
            logger.info(f"-- role_level {level} --")
            logger.info(t.to_string())


# ===========================================================================
# MANAGERS (privacy-safe: only aggregate manager-level statistics, never IDs)
# ===========================================================================

def section_managers(m: pd.DataFrame):
    hdr("MANAGERS (aggregated only — no individual manager identified anywhere below)")

    mgr = m.groupby("manager_id", observed=True).agg(
        team_size=("employee_id", "count"),
        voluntary_exit_rate=("voluntary_exit", "mean"),
        regrettable_rate=("regrettable_voluntary_exit", "mean"),
        avg_latest_mgr_eff=("manager_effectiveness_latest_score", "mean"),
    ).reset_index()
    mgr_valid = mgr[mgr["team_size"] >= 5].copy()

    sub(f"Manager-level distribution (n={len(mgr_valid)} managers with >=5 reports)")
    logger.info(mgr_valid[["team_size", "voluntary_exit_rate", "regrettable_rate", "avg_latest_mgr_eff"]].describe().to_string())

    # Simple one-way ANOVA-style variance decomposition proxy: between-manager
    # variance vs total variance in voluntary_exit, restricted to managers with >=5 reports
    pool = m[m["manager_id"].isin(mgr_valid["manager_id"])]
    grand_mean = pool["voluntary_exit"].mean()
    between = mgr_valid.set_index("manager_id")["voluntary_exit_rate"]
    sizes = mgr_valid.set_index("manager_id")["team_size"]
    ss_between = (sizes * (between - grand_mean) ** 2).sum()
    ss_total = ((pool["voluntary_exit"] - grand_mean) ** 2).sum()
    r2_like = ss_between / ss_total if ss_total > 0 else np.nan
    sub("Manager-level 'explained variance' proxy for voluntary_exit (SS_between/SS_total)")
    logger.info(f"n_managers={len(mgr_valid)}, n_employees_in_pool={len(pool)}, R2-like={r2_like:.4f}")

    sub("Concentration: top decile of managers by regrettable rate — share of total regrettable exits")
    mgr_valid = mgr_valid.sort_values("regrettable_rate", ascending=False)
    top_decile_n = max(1, int(len(mgr_valid) * 0.1))
    top_managers = mgr_valid.head(top_decile_n)["manager_id"]
    total_regrettable = pool["regrettable_voluntary_exit"].sum()
    top_regrettable = m[m["manager_id"].isin(top_managers)]["regrettable_voluntary_exit"].sum()
    share = top_regrettable / total_regrettable if total_regrettable else np.nan
    logger.info(f"top decile ({top_decile_n} managers) hold {share:.1%} of all regrettable voluntary exits "
                f"(vs {top_decile_n/len(mgr_valid):.1%} of managers) — total_regrettable={total_regrettable}")

    sub("acting_appointment manager x team avg engagement (manager_effectiveness)")
    m10 = m.dropna(subset=["manager_effectiveness_latest_score"])
    acting_mgr_ids = set(m.loc[m["acting_appointment"], "employee_id"])
    team_acting = m10[m10["manager_id"].isin(acting_mgr_ids)]
    team_substantive = m10[~m10["manager_id"].isin(acting_mgr_ids) & m10["manager_id"].notna()]
    u, p, na, nb = mannwhitney(team_acting["manager_effectiveness_latest_score"],
                                team_substantive["manager_effectiveness_latest_score"])
    logger.info(f"teams under an acting manager: median mgr_effectiveness={team_acting['manager_effectiveness_latest_score'].median():.2f}, n={na}")
    logger.info(f"teams under a substantive manager: median mgr_effectiveness={team_substantive['manager_effectiveness_latest_score'].median():.2f}, n={nb}")
    logger.info(f"Mann-Whitney p={p:.2e}")

    sub("Span of control vs voluntary_exit rate and manager_effectiveness (correlation)")
    valid = mgr_valid.dropna(subset=["avg_latest_mgr_eff"])
    if len(valid) >= 10:
        r, p = stats.spearmanr(valid["team_size"], valid["voluntary_exit_rate"])
        logger.info(f"team_size vs voluntary_exit_rate: spearman r={r:.3f}, p={p:.2e}, n={len(valid)}")
        r2, p2 = stats.spearmanr(valid["team_size"], valid["avg_latest_mgr_eff"])
        logger.info(f"team_size vs avg_manager_effectiveness: spearman r={r2:.3f}, p={p2:.2e}, n={len(valid)}")


# ===========================================================================
# ACQUISITIONS
# ===========================================================================

def section_acquisitions(m: pd.DataFrame):
    hdr("ACQUISITIONS (legacy_entity)")

    sub("Voluntary exit rate by legacy_entity")
    t = rate_table(m, "legacy_entity", "voluntary_exit")
    logger.info(t.to_string(index=False))
    chi2, p, v, n = chi2_effect(m, "legacy_entity", "voluntary_exit")
    logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

    sub("compa_ratio by legacy_entity (median, IQR)")
    logger.info(m.groupby("legacy_entity", observed=True)["compa_ratio"].describe()[["count", "25%", "50%", "75%"]].to_string())

    sub("Voluntary exit rate by legacy_entity, controlled loosely within department (Entity_B focus)")
    for dept in m["department"].unique():
        sub_df = m[m["department"] == dept]
        if sub_df["legacy_entity"].nunique() < 2:
            continue
        t = rate_table(sub_df, "legacy_entity", "voluntary_exit", min_n=15)
        if (t["n"] >= 15).any():
            logger.info(f"-- {dept} --")
            logger.info(t.to_string(index=False))

    sub("compa_ratio x voluntary_exit within Entity_B specifically, controlling for role_level")
    entb = m[m["legacy_entity"] == "Entity_B"].copy()
    for level in sorted(entb["role_level"].unique()):
        sub_df = entb[entb["role_level"] == level]
        if len(sub_df) < 20:
            continue
        left = sub_df.loc[sub_df["voluntary_exit"], "compa_ratio"]
        stayed = sub_df.loc[~sub_df["departed"], "compa_ratio"]
        if len(left) >= 5 and len(stayed) >= 5:
            u, p, na, nb = mannwhitney(left, stayed)
            logger.info(f"Entity_B role_level {level}: leaver compa median={left.median():.3f} (n={na}), "
                        f"stayer compa median={stayed.median():.3f} (n={nb}), p={p:.2e}")

    sub("Engagement trajectory by legacy_entity (latest senior_leadership_trust, career_development)")
    for dim in ["senior_leadership_trust", "career_development"]:
        t = m.groupby("legacy_entity", observed=True)[f"{dim}_latest_score"].agg(["mean", "count"])
        logger.info(f"-- {dim}_latest_score --")
        logger.info(t.to_string())

    sub("Promotion recommendation rate by legacy_entity (overall, unadjusted)")
    m8 = m[m["performance_promotion_recommendation_ever"].notna()].copy()
    m8["promo_rec_ever"] = m8["performance_promotion_recommendation_ever"].astype(bool)
    t = m8.groupby("legacy_entity", observed=True)["promo_rec_ever"].agg(["mean", "count"])
    logger.info(t.to_string())

    sub("Time-since-acquisition proxy: voluntary exit rate by hire_date year within each acquired entity")
    m["hire_year"] = m["hire_date"].dt.year
    for ent in ["Entity_A", "Entity_B", "Entity_C"]:
        sub_df = m[m["legacy_entity"] == ent]
        t = sub_df.groupby("hire_year", observed=True)["voluntary_exit"].agg(["mean", "count"])
        t = t[t["count"] >= 15]
        if len(t):
            logger.info(f"-- {ent} --")
            logger.info(t.to_string())

    sub("Performance rating mix by legacy_entity")
    t = pd.crosstab(m["legacy_entity"], m["performance_latest_rating"], normalize="index").round(3)
    logger.info(t.to_string())


# ===========================================================================
# HIRING
# ===========================================================================

def section_hiring(m: pd.DataFrame):
    hdr("HIRING")

    sub("Early attrition (tenure < 12mo, voluntary) rate by hire_source")
    m["early_voluntary_exit"] = m["voluntary_exit"] & (m["tenure_months"] < 12)
    t = rate_table(m, "hire_source", "early_voluntary_exit")
    logger.info(t.to_string(index=False))
    chi2, p, v, n = chi2_effect(m, "hire_source", "early_voluntary_exit")
    logger.info(f"chi2={chi2:.2f}, p={p:.2e}, Cramers V={v:.3f}, n={n}")

    sub("Overall voluntary exit rate by hire_source (all tenure)")
    t = rate_table(m, "hire_source", "voluntary_exit")
    logger.info(t.to_string(index=False))

    sub("performance_latest_rating mix by hire_source")
    t = pd.crosstab(m["hire_source"], m["performance_latest_rating"], normalize="index").round(3)
    logger.info(t.to_string())

    sub("regrettable_voluntary_exit rate by hire_source")
    t = rate_table(m, "hire_source", "regrettable_voluntary_exit")
    logger.info(t.to_string(index=False))

    sub("days_to_fill (employees.csv-level, not master) by department/role_level — see note")
    logger.info("days_to_fill was not carried into the master dataset (not in the requested "
                "employee-characteristics list); recruiting-bottleneck analysis (HI-2) would "
                "re-merge employees_clean.csv directly, deferred to a targeted hypothesis test.")


# ===========================================================================
# TIME
# ===========================================================================

def section_time(m: pd.DataFrame):
    hdr("TIME")

    sub("Voluntary exits by exit year")
    dep = m[m["departed"]].copy()
    dep["exit_year"] = dep["exit_date"].dt.year
    t = dep.groupby("exit_year", observed=True).agg(
        n_exits=("employee_id", "count"),
        voluntary=("voluntary_exit", "sum"),
        regrettable=("regrettable_voluntary_exit", "sum"),
    )
    logger.info(t.to_string())

    sub("Engagement level trend across waves — company average latest-available score is wave-blind; "
        "use raw eligible-wave averages instead (recomputed here from engagement_clean-equivalent logic is out of scope; "
        "see docs/analysis_plan.md DP-4 for the full wave-indexed version). Reporting cutoff-blind summary only:")
    for dim in ["senior_leadership_trust", "wellbeing"]:
        logger.info(f"{dim}_earliest_score company mean: {m[f'{dim}_earliest_score'].mean():.3f}")
        logger.info(f"{dim}_latest_score company mean:   {m[f'{dim}_latest_score'].mean():.3f}")

    sub("Pre-exit trajectory: abs_change in senior_leadership_trust and wellbeing, leavers vs stayers")
    for dim in ["senior_leadership_trust", "wellbeing", "confidence_in_role_future"]:
        col = f"{dim}_abs_change"
        left = m.loc[m["voluntary_exit"], col]
        stayed = m.loc[~m["departed"], col]
        u, p, na, nb = mannwhitney(left, stayed)
        logger.info(f"{dim}: leaver median change={left.median():+.3f} (n={na}), "
                    f"stayer median change={stayed.median():+.3f} (n={nb}), p={p:.2e}")


def main():
    m = load_master()
    hdr(f"MASTER DATASET LOADED: {m.shape[0]} rows x {m.shape[1]} columns")
    section_attrition(m)
    section_engagement(m)
    section_career(m)
    section_managers(m)
    section_acquisitions(m)
    section_hiring(m)
    section_time(m)
    hdr("DISCOVERY SCAN COMPLETE")
    logger.info(f"Full log: {LOG_PATH}")


if __name__ == "__main__":
    main()
