"""
deep_dive.py — round two, chasing the four threads that survived the confound audit.

  1. Promotion, review-level, split by BOTH definitions of "skilled" (hipo_flag and
     performance rating). findings_04 used "ever recommended", which is exposure-biased —
     a 2024 leaver had one shot at a recommendation, a stayer had three. Redo it fairly.
  2. The tenure shape. HiPo exit is not flat across tenure; it looks bimodal.
  3. Manager clustering and the departure cascade.
  4. The pay paradox: compa-ratio predicts regrettable exit but not HiPo exit. Which is it?
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eddited_csv"
e = pd.read_csv(OUT / "master_plus.csv", low_memory=False)
pr = pd.read_csv(OUT / "review_risk_set.csv", low_memory=False)
e["exit_dt"] = pd.to_datetime(e["exit_dt"])
line = lambda t: print(f"\n{'='*104}\n{t}\n{'='*104}")

RATING_ORD = {"Unsatisfactory": 1, "Below Expectations": 2, "Meets Expectations": 3,
              "High Performer": 4, "Outstanding": 5}
pr["rating_num"] = pr["performance_rating"].map(RATING_ORD)
pr["top_perf"] = (pr["rating_num"] >= 4).astype(int)
pr["outstanding"] = (pr["rating_num"] == 5).astype(int)

# ------------------------------------------------------------------- 1. promotion, fair
line("1. PROMOTION BLOCK — review-level, exposure-fair, by definition of 'skilled'")
defs = [("hipo_flag = True", pr.hipo == 1), ("hipo_flag = False", pr.hipo == 0),
        ("rating >= High Perf", pr.top_perf == 1), ("rating <= Meets", pr.top_perf == 0),
        ("rating = Outstanding", pr.outstanding == 1),
        ("HiPo AND top-rated", (pr.hipo == 1) & (pr.top_perf == 1))]
print(f"{'cohort':<22}{'n reviews':>10}{'rec %':>9}{'not-rec %':>11}{'OR':>8}{'95% CI':>18}{'p':>10}")
for name, mask in defs:
    s = pr[mask]
    ct = pd.crosstab(s["no_promo"], s["exit_180"])
    if ct.shape != (2, 2) or ct.values.min() < 3:
        print(f"{name:<22}{len(s):>10,}   (too sparse)"); continue
    orr, p = stats.fisher_exact(ct.values)
    a, b, c, d = ct.values.ravel()
    se = np.sqrt(1/a + 1/b + 1/c + 1/d)
    lo, hi = np.exp(np.log(orr) - 1.96*se), np.exp(np.log(orr) + 1.96*se)
    r = s.groupby("no_promo")["exit_180"].mean()
    print(f"{name:<22}{len(s):>10,}{r.get(0,np.nan):>9.2%}{r.get(1,np.nan):>11.2%}"
          f"{orr:>8.2f}{f'[{lo:.2f}-{hi:.2f}]':>18}{p:>10.4f}")

print("\n  Formal interaction test (review level, clustered SEs on employee):")
m = smf.logit("exit_180 ~ no_promo * hipo + tenure_years + compa_ratio + role_level "
              "+ C(department) + C(review_cycle)", data=pr).fit(disp=0, cov_type="cluster",
              cov_kwds={"groups": pr["employee_id"]})
for t in ["no_promo", "hipo", "no_promo:hipo"]:
    print(f"    {t:<16} OR={np.exp(m.params[t]):.3f}  "
          f"[{np.exp(m.conf_int().loc[t,0]):.3f}-{np.exp(m.conf_int().loc[t,1]):.3f}]  "
          f"p={m.pvalues[t]:.4f}")

# --------------------------------------------------------------------- 2. tenure shape
line("2. TENURE SHAPE — where in the lifecycle do HiPos go?")
e["tenure_band"] = pd.cut(e["tenure_years"], [0, 1, 2, 3, 5, 10, 100],
                          labels=["<1y", "1-2y", "2-3y", "3-5y", "5-10y", "10y+"])
tab = e.pivot_table(index="tenure_band", columns="hipo", values="voluntary",
                    aggfunc=["mean", "size"], observed=True)
tab.columns = ["nonhipo_rate", "hipo_rate", "nonhipo_n", "hipo_n"]
tab["ratio"] = tab["hipo_rate"] / tab["nonhipo_rate"]
res = []
for b in tab.index:
    s = e[e.tenure_band == b]
    ct = pd.crosstab(s["hipo"], s["voluntary"])
    if ct.shape == (2, 2) and ct.values.min() >= 1:
        orr, p = stats.fisher_exact(ct.values)
    else:
        orr, p = np.nan, np.nan
    res.append((orr, p))
tab["OR"], tab["p"] = [r[0] for r in res], [r[1] for r in res]
print(tab.to_string(float_format=lambda x: f"{x:.4g}"))
m2 = smf.logit("voluntary ~ hipo * C(tenure_band) + C(department) + role_level",
               data=e).fit(disp=0)
inter_p = [p for t, p in m2.pvalues.items() if t.startswith("hipo:")]
print(f"\n  interaction terms hipo x tenure_band, min p = {min(inter_p):.4f}")
lr = 2 * (m2.llf - smf.logit("voluntary ~ hipo + C(tenure_band) + C(department) + role_level",
                             data=e).fit(disp=0).llf)
print(f"  LR test for the whole interaction block: LR={lr:.2f}, df=5, "
      f"p={stats.chi2.sf(lr, 5):.4f}")

# --------------------------------------------------------------- 3. manager clustering
line("3. MANAGER CLUSTERING")
mg = e.groupby("manager_id").agg(span=("employee_id", "size"), vol=("voluntary", "sum"),
                                 hipo_n=("hipo", "sum"),
                                 hipo_vol=("employee_id", lambda s: 0))
mg["hipo_vol"] = e[e.hipo == 1].groupby("manager_id")["voluntary"].sum().reindex(mg.index).fillna(0)
big = mg[mg["span"] >= 5]
# Is exit over-dispersed relative to binomial? (i.e. is it clustered at all)
p_bar = e["voluntary"].mean()
obs_var = big["vol"].var()
exp_var = (big["span"] * p_bar * (1 - p_bar)).mean()
print(f"  managers with span>=5: {len(big)}   pooled exit rate {p_bar:.3f}")
print(f"  variance of team exit counts: observed {obs_var:.3f} vs binomial {exp_var:.3f} "
      f"-> dispersion ratio {obs_var/exp_var:.2f}")
chi2 = ((big["vol"] - big["span"]*p_bar)**2 / (big["span"]*p_bar*(1-p_bar))).sum()
print(f"  overdispersion chi2 = {chi2:.0f} on {len(big)-1} df, "
      f"p = {stats.chi2.sf(chi2, len(big)-1):.3g}")
print(f"  teams (span>=5) with 0 voluntary exits: {(big['vol']==0).mean():.1%}; "
      f"with >=3: {(big['vol']>=3).mean():.1%}")
hot = big[big["vol"] >= 3]
print(f"  the {len(hot)} 'hot' teams hold {hot['vol'].sum()}/{big['vol'].sum()} "
      f"({hot['vol'].sum()/big['vol'].sum():.1%}) of exits from {hot['span'].sum()}/"
      f"{big['span'].sum()} ({hot['span'].sum()/big['span'].sum():.1%}) of headcount")

line("3b. MANAGER DEPARTURE — timing")
d = e[e["mgr_departed"] == 1].copy()
d["mgr_exit"] = d["manager_id"].map(e.set_index("employee_id")["exit_dt"])
d["gap"] = (d["exit_dt"] - d["mgr_exit"]).dt.days
lv = d[d.voluntary == 1]
print(f"  n with departed manager = {len(d)}, of whom voluntary = {len(lv)} ({len(lv)/len(d):.0%})")
print(f"  vs baseline {e.voluntary.mean():.1%}  ->  Fisher OR "
      f"{stats.fisher_exact(pd.crosstab(e.mgr_departed, e.voluntary).values)[0]:.1f}")
print(f"  of those, left AFTER the manager: {(lv['gap']>0).sum()} "
      f"({(lv['gap']>0).mean():.0%})  |  BEFORE: {(lv['gap']<=0).sum()}")
print(f"  a coin flip would give 50%. Binomial p = "
      f"{stats.binomtest(int((lv['gap']>0).sum()), int(lv['gap'].notna().sum()), 0.5).pvalue:.3f}")
print("  -> the manager is not leading the exodus; the whole unit unwinds together.")

# ------------------------------------------------------------------- 4. the pay paradox
line("4. PAY POSITION — resolving the contradiction")
for label, sub, out in [("all staff -> voluntary", e, "voluntary"),
                        ("HiPo -> voluntary", e[e.hipo == 1], "voluntary"),
                        ("all staff -> regrettable", e, "regrettable"),
                        ("voluntary leavers -> regrettable", e[e.voluntary == 1], "regrettable")]:
    a = sub.loc[sub[out] == 1, "compa_ratio"].dropna()
    b = sub.loc[sub[out] == 0, "compa_ratio"].dropna()
    t, p = stats.ttest_ind(a, b, equal_var=False)
    print(f"  {label:<34} event {a.mean():.3f} vs non-event {b.mean():.3f}  "
          f"diff {a.mean()-b.mean():+.4f}  p={p:.3g}  n_ev={len(a)}")
print("\n  Same test controlling for role_level and department (OLS on compa):")
for label, sub, out in [("HiPo -> voluntary", e[e.hipo == 1], "voluntary"),
                        ("voluntary leavers -> regrettable", e[e.voluntary == 1], "regrettable")]:
    mm = smf.ols(f"compa_ratio ~ {out} + role_level + C(department)", data=sub).fit()
    print(f"    {label:<34} beta={mm.params[out]:+.4f}  p={mm.pvalues[out]:.3g}")

# department deep dive
line("5. DEPARTMENT — HiPo exit rate, with headcount and cost weight")
dep = e.groupby("department").agg(
    n=("employee_id", "size"), hipo_n=("hipo", "sum"),
    hipo_exit=("employee_id", lambda s: 0), all_exit=("voluntary", "mean"),
    med_salary=("salary", "median"))
dep["hipo_exit"] = e[e.hipo == 1].groupby("department")["voluntary"].mean()
dep["hipo_leavers"] = e[(e.hipo == 1) & (e.voluntary == 1)].groupby("department").size()
dep["lift_vs_all"] = dep["hipo_exit"] / dep["all_exit"]
print(dep.sort_values("hipo_exit", ascending=False).to_string(float_format=lambda x: f"{x:.4g}"))
