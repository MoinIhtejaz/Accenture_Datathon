"""
Adversarial stress-test of the top-10 discovery findings (docs/findings_register.md).
One-off analytical script (not part of the reusable pipeline) — run once, results
transcribed into the findings register verdicts. Every check below targets a named
threat: confounding, Simpson's paradox, denominator/exposure-time errors,
composition effects, selection/survivorship bias.
"""
import numpy as np
import pandas as pd
from scipy import stats

pd.set_option("display.width", 200)
m = pd.read_csv("outputs/tables/employee_analytics_master.csv",
                 parse_dates=["hire_date", "exit_date", "cutoff_date"], low_memory=False)
for c in ["voluntary_exit", "regrettable_voluntary_exit", "hipo_flag", "departed"]:
    m[c] = m[c].astype(bool)


def hdr(t):
    print("\n" + "=" * 90 + f"\n{t}\n" + "=" * 90)


# ===========================================================================
hdr("FR-01 stress test: HiPo composition confounds")
print("HiPo rate by department:")
print(m.groupby("department", observed=True)["hipo_flag"].mean().sort_values(ascending=False))
print("\nHiPo rate by legacy_entity:")
print(m.groupby("legacy_entity", observed=True)["hipo_flag"].mean().sort_values(ascending=False))
print("\nHiPo rate by role_level:")
print(m.groupby("role_level", observed=True)["hipo_flag"].mean())
print("\nMedian tenure_months: HiPo vs not:")
print(m.groupby("hipo_flag")["tenure_months"].median())
print("\nRegrettable exit rate by hipo_flag WITHIN role_level (Simpson check):")
for lvl in sorted(m["role_level"].unique()):
    sub = m[m["role_level"] == lvl]
    if sub["hipo_flag"].sum() < 20 or (~sub["hipo_flag"]).sum() < 20:
        continue
    r_hipo = sub.loc[sub["hipo_flag"], "regrettable_voluntary_exit"].mean()
    r_not = sub.loc[~sub["hipo_flag"], "regrettable_voluntary_exit"].mean()
    n_hipo = sub["hipo_flag"].sum()
    print(f"  level {lvl}: hipo n={n_hipo} rate={r_hipo:.4f} | not-hipo rate={r_not:.4f}")
print("\nLogistic-style stratified check by department (Simpson):")
for dept in m["department"].unique():
    sub = m[m["department"] == dept]
    if sub["hipo_flag"].sum() < 15:
        continue
    r_hipo = sub.loc[sub["hipo_flag"], "regrettable_voluntary_exit"].mean()
    r_not = sub.loc[~sub["hipo_flag"], "regrettable_voluntary_exit"].mean()
    print(f"  {dept}: hipo n={sub['hipo_flag'].sum()} rate={r_hipo:.4f} | not-hipo rate={r_not:.4f}")

# ===========================================================================
hdr("FR-09 stress test: acquisition hire_source / hire_date semantics")
acq = m[m["hire_source"] == "acquisition"]
print("hire_date distribution for ALL Entity_C acquisition-sourced employees (not just early exits):")
print(acq[acq["legacy_entity"] == "Entity_C"]["hire_date"].dt.to_period("Q").value_counts().sort_index())
print("\nSame for Entity_B (all, not just early exits):")
print(acq[acq["legacy_entity"] == "Entity_B"]["hire_date"].dt.to_period("Q").value_counts().sort_index())
print("\nWhat are the 496 NovaCorp-Origin 'acquisition' hire_source employees? hire_date spread:")
novaorigin_acq = acq[acq["legacy_entity"] == "NovaCorp-Origin"]
print(novaorigin_acq["hire_date"].dt.year.value_counts().sort_index())
print("\nTotal company-wide early voluntary exits (tenure<12mo) vs this subgroup's share:")
total_early = (m["voluntary_exit"] & (m["tenure_months"] < 12)).sum()
acq_early = (acq["voluntary_exit"] & (acq["tenure_months"] < 12)).sum()
print(f"total early exits={total_early}, acquisition-sourced early exits={acq_early}, share={acq_early/total_early:.1%}")
print("\nNon-acquisition-sourced early exit rate for comparison (all other sources combined):")
non_acq = m[m["hire_source"] != "acquisition"]
print(f"n={len(non_acq)}, early exit rate={(non_acq['voluntary_exit'] & (non_acq['tenure_months']<12)).mean():.4f}")

# ===========================================================================
hdr("FR-03 stress test: exposure-time (n_reviews_available) confound")
m8 = m[m["performance_promotion_recommendation_ever"].notna()].copy()
m8["promo_ever"] = m8["performance_promotion_recommendation_ever"].astype(bool)
print("n_reviews_available by legacy_entity:")
print(m8.groupby("legacy_entity", observed=True)["performance_n_reviews_available"].describe()[["mean","50%","count"]])
print("\nPromotion rate PER REVIEW (count/n_reviews) by entity, vs 'ever' rate:")
m8["promo_rate_per_review"] = m8["performance_promotion_recommendation_count"] / m8["performance_n_reviews_available"]
print(m8.groupby("legacy_entity", observed=True)[["promo_rate_per_review", "promo_ever"]].mean())
print("\nRestrict to employees with exactly 3 reviews available (equal exposure) -- does gap persist?")
m8_eq = m8[m8["performance_n_reviews_available"] == 3]
print(m8_eq.groupby("legacy_entity", observed=True)["promo_ever"].agg(["mean", "count"]))
print("\nWithin role_level 1 AND exactly 3 reviews (tightest control):")
m8_eq1 = m8_eq[m8_eq["role_level"] == 1]
print(m8_eq1.groupby("legacy_entity", observed=True)["promo_ever"].agg(["mean", "count"]))
print("\nTenure (months) by entity, restricted to role_level 1:")
print(m[m["role_level"] == 1].groupby("legacy_entity", observed=True)["tenure_months"].median())

# ===========================================================================
hdr("FR-06/FR-18 stress test: exposure-time and composition confound (stalled vs advancing)")
m9 = m8.copy()
m9["high_perf"] = m9["performance_latest_rating"].isin(["High Performer", "Outstanding"])
stalled = m9[(m9["promotion_eligible"]) & (m9["high_perf"]) & (~m9["promo_ever"])]
advancing = m9[(m9["promotion_eligible"]) & (m9["high_perf"]) & (m9["promo_ever"])]
print("n_reviews_available: stalled vs advancing")
print("stalled:", stalled["performance_n_reviews_available"].describe()[["mean","50%"]].to_dict())
print("advancing:", advancing["performance_n_reviews_available"].describe()[["mean","50%"]].to_dict())
print("\ndepartment mix: stalled vs advancing")
print(pd.concat([stalled["department"].value_counts(normalize=True).rename("stalled"),
                 advancing["department"].value_counts(normalize=True).rename("advancing")], axis=1).round(3))
print("\nrole_level mix: stalled vs advancing")
print(pd.concat([stalled["role_level"].value_counts(normalize=True).rename("stalled"),
                 advancing["role_level"].value_counts(normalize=True).rename("advancing")], axis=1).round(3))
print("\ntenure: stalled vs advancing")
print("stalled median tenure:", stalled["tenure_months"].median(), "advancing median tenure:", advancing["tenure_months"].median())
print("\nRestrict to n_reviews_available==3 only (equal exposure): does the exit-rate gap persist?")
stalled_eq = stalled[stalled["performance_n_reviews_available"] == 3]
advancing_eq = advancing[advancing["performance_n_reviews_available"] == 3]
print(f"stalled(n_rev=3): n={len(stalled_eq)}, voluntary_exit rate={stalled_eq['voluntary_exit'].mean():.4f}")
print(f"advancing(n_rev=3): n={len(advancing_eq)}, voluntary_exit rate={advancing_eq['voluntary_exit'].mean():.4f}")
if len(stalled_eq) >= 20 and len(advancing_eq) >= 20:
    combo = pd.concat([stalled_eq.assign(g="s"), advancing_eq.assign(g="a")])
    ct = pd.crosstab(combo["g"], combo["voluntary_exit"])
    chi2, p, _, _ = stats.chi2_contingency(ct)
    print(f"chi2={chi2:.2f} p={p:.4f}")

# ===========================================================================
hdr("FR-04 stress test: Simpson's paradox check (department/role_level strata)")
print("compa_ratio and trust for Entity_B vs NovaCorp-Origin WITHIN each department:")
for dept in m["department"].unique():
    sub = m[(m["department"] == dept) & (m["legacy_entity"].isin(["Entity_B", "NovaCorp-Origin"]))]
    g = sub.groupby("legacy_entity", observed=True).agg(
        compa=("compa_ratio", "median"), trust=("senior_leadership_trust_latest_score", "mean"), n=("employee_id", "count"))
    if (g["n"] >= 30).all():
        print(f"-- {dept} --")
        print(g)

# ===========================================================================
hdr("FR-05 stress test: does non-response predict exit WITHIN NovaCorp-Origin alone (remove entity confound)?")
for ent in ["NovaCorp-Origin", "Entity_A", "Entity_B", "Entity_C"]:
    sub = m[(m["legacy_entity"] == ent) & (m["engagement_n_waves_available"] > 0)].copy()
    sub["never_responded"] = sub["engagement_n_responses_available"] == 0
    if sub["never_responded"].sum() < 20:
        continue
    r_never = sub.loc[sub["never_responded"], "voluntary_exit"].mean()
    r_resp = sub.loc[~sub["never_responded"], "voluntary_exit"].mean()
    ct = pd.crosstab(sub["never_responded"], sub["voluntary_exit"])
    chi2, p, _, _ = stats.chi2_contingency(ct)
    print(f"{ent}: never_responded n={sub['never_responded'].sum()}, rate={r_never:.4f} vs responded rate={r_resp:.4f}, chi2 p={p:.4g}")

# ===========================================================================
hdr("FR-02 stress test: cell sizes underlying the '5 of 6 departments' claim")
for dept in m["department"].unique():
    sub = m[m["department"] == dept]
    if sub["legacy_entity"].nunique() < 2:
        continue
    g = sub.groupby("legacy_entity", observed=True)["voluntary_exit"].agg(["sum", "count"])
    g["rate"] = g["sum"] / g["count"]
    print(f"-- {dept} --")
    print(g)

# ===========================================================================
hdr("FR-07 stress test: department+entity-adjusted manager variance")
m["dept_entity_cell"] = m["department"].astype(str) + "|" + m["legacy_entity"].astype(str)
cell_mean = m.groupby("dept_entity_cell")["voluntary_exit"].transform("mean")
m["resid_exit"] = m["voluntary_exit"].astype(float) - cell_mean
mgr = m.groupby("manager_id", observed=True).agg(
    team_size=("employee_id", "count"),
    resid_mean=("resid_exit", "mean"),
    raw_mean=("voluntary_exit", "mean"),
).reset_index()
mgr_valid = mgr[mgr["team_size"] >= 5]
pool = m[m["manager_id"].isin(mgr_valid["manager_id"])]
grand_mean_raw = pool["voluntary_exit"].mean()
ss_between_raw = (mgr_valid.set_index("manager_id")["team_size"] *
                   (mgr_valid.set_index("manager_id")["raw_mean"] - grand_mean_raw) ** 2).sum()
ss_total_raw = ((pool["voluntary_exit"] - grand_mean_raw) ** 2).sum()
print(f"RAW (unadjusted) R2-like: {ss_between_raw/ss_total_raw:.4f}")

grand_mean_resid = 0  # residuals are mean-zero within cell by construction, but not globally; compute properly
pool_resid = pool.merge(mgr_valid[["manager_id", "resid_mean"]], on="manager_id")
grand_mean_resid = pool["resid_exit"].mean()
ss_between_resid = (mgr_valid.set_index("manager_id")["team_size"] *
                     (mgr_valid.set_index("manager_id")["resid_mean"] - grand_mean_resid) ** 2).sum()
ss_total_resid = ((pool["resid_exit"] - grand_mean_resid) ** 2).sum()
print(f"DEPT+ENTITY-ADJUSTED R2-like (on residuals): {ss_between_resid/ss_total_resid:.4f}")
print(f"n managers={len(mgr_valid)}, n employees={len(pool)}")

# ===========================================================================
hdr("FR-11 stress test: hire_source composition confounds")
print("hire_source x role_level (% level 1):")
print(pd.crosstab(m["hire_source"], m["role_level"] == 1, normalize="index").round(3))
print("\nMedian tenure by hire_source:")
print(m.groupby("hire_source", observed=True)["tenure_months"].median())
print("\nhire_source x department:")
print(pd.crosstab(m["hire_source"], m["department"], normalize="index").round(3))
print("\nVoluntary exit rate by hire_source, restricted to role_level==1 only (equal seniority):")
lvl1 = m[m["role_level"] == 1]
t = lvl1.groupby("hire_source", observed=True)["voluntary_exit"].agg(["sum", "count"])
t["rate"] = t["sum"] / t["count"]
print(t.sort_values("rate", ascending=False))
print("\nVoluntary exit rate by hire_source, restricted to tenure > 24 months (removes early-tenure/graduate-age confound):")
mature = m[m["tenure_months"] > 24]
t2 = mature.groupby("hire_source", observed=True)["voluntary_exit"].agg(["sum", "count"])
t2["rate"] = t2["sum"] / t2["count"]
print(t2.sort_values("rate", ascending=False))
