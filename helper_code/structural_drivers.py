"""
structural_drivers.py — if engagement scores don't explain HiPo exit, what does?

The wave risk-set showed the eight survey dimensions are flat for HiPos. So the driver, if there
is one, is structural: pay position, promotion, org unit, manager, provenance.

Three designs here, each answering a different question:
  A. Review-level risk set  — does a review with no promotion recommendation predict exit in the
     next 180 days? This is the exposure-fair version of the findings_04 claim, which compared
     "ever recommended" across people who had wildly different numbers of reviews.
  B. Interaction tests      — is HiPo status a multiplier on any structural disadvantage?
  C. Multivariate + survival— what survives together, and how fast do people go.
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "original_csv", ROOT / "eddited_csv"
emp = pd.read_csv(OUT / "master_features.csv", low_memory=False)
emp["exit_dt"] = pd.to_datetime(emp["exit_dt"])
line = lambda t: print(f"\n{'='*104}\n{t}\n{'='*104}")

# ============================================================ A. review-level risk set
line("A. PROMOTION — review-level risk set (the exposure-fair test)")
perf = pd.read_csv(RAW / "performance.csv", parse_dates=["review_date"])
pr = perf.merge(emp[["employee_id", "exit_dt", "voluntary", "regrettable", "hipo",
                     "compa_ratio", "department", "role_level", "tenure_years"]],
                on="employee_id", how="left")
pr = pr[pr["exit_dt"].isna() | (pr["exit_dt"] > pr["review_date"])].copy()
pr["days_to_exit"] = (pr["exit_dt"] - pr["review_date"]).dt.days
pr["exit_180"] = ((pr["voluntary"] == 1) & (pr["days_to_exit"] <= 180)).astype(int)
pr["no_promo"] = (~pr["promotion_recommendation"].astype(bool)).astype(int)

print(f"review-level rows: {len(pr):,}, exits within 180d: {pr.exit_180.sum():,}")
for name, sub in [("ALL", pr), ("HIPO", pr[pr.hipo == 1]), ("NON-HIPO", pr[pr.hipo == 0])]:
    ct = pd.crosstab(sub["no_promo"], sub["exit_180"])
    if ct.shape != (2, 2):
        continue
    orr, p = stats.fisher_exact(ct.values)
    r = sub.groupby("no_promo")["exit_180"].mean()
    print(f"  {name:<9} recommended {r.get(0,np.nan):.2%} vs not-recommended {r.get(1,np.nan):.2%} "
          f"exit in 180d   OR={orr:.2f}  p={p:.3g}  n={len(sub):,}")

# and the same on goal achievement / rating, review-level
for v in ["goal_achievement_score"]:
    for name, sub in [("ALL", pr), ("HIPO", pr[pr.hipo == 1])]:
        a = sub.loc[sub.exit_180 == 1, v].dropna(); b = sub.loc[sub.exit_180 == 0, v].dropna()
        t, p = stats.ttest_ind(a, b, equal_var=False)
        print(f"  {name:<9} {v}: pre-exit {a.mean():.1f} vs staying {b.mean():.1f}  p={p:.3g}")

# ================================================================= B. interaction tests
line("B. IS HIPO A MULTIPLIER ON STRUCTURAL DISADVANTAGE?")
e = emp.copy()
e["underpaid"] = (e["compa_ratio"] < 0.90).astype(int)
e["acquired"] = (e["legacy_entity_code"] != "NovaCorp-Origin").astype(int)
e["acting"] = e["acting_appointment"].astype(int)
e["agency_hire"] = (e["hire_source"] == "agency").astype(int)
e["slow_fill"] = (e["days_to_fill"] > e["days_to_fill"].median()).astype(int)

rows = []
for v in ["underpaid", "acquired", "acting", "agency_hire", "slow_fill"]:
    tab = e.groupby(["hipo", v])["voluntary"].agg(["mean", "size"])
    try:
        m = smf.logit(f"voluntary ~ hipo * {v} + tenure_years + C(department) + role_level",
                      data=e).fit(disp=0)
        term = f"hipo:{v}"
        p = m.pvalues.get(term, np.nan); orr = np.exp(m.params.get(term, np.nan))
    except Exception:
        p, orr = np.nan, np.nan
    # simple stratified rates
    r = {}
    for h in (0, 1):
        for k in (0, 1):
            try:
                r[(h, k)] = tab.loc[(h, k), "mean"]
            except KeyError:
                r[(h, k)] = np.nan
    rows.append(dict(var=v, nonhipo_no=r[(0, 0)], nonhipo_yes=r[(0, 1)],
                     hipo_no=r[(1, 0)], hipo_yes=r[(1, 1)],
                     interaction_OR=orr, interaction_p=p))
inter = pd.DataFrame(rows)
inter["q"] = multipletests(inter["interaction_p"].fillna(1), method="fdr_bh")[1]
print(inter.to_string(index=False, float_format=lambda x: f"{x:.4g}"))

# ------------------------------------------------- HiPo exit rate by structural segment
line("B2. HIPO VOLUNTARY EXIT RATE BY SEGMENT (with chi-square vs the rest of HiPos)")
h = e[e.hipo == 1]
for v in ["department", "role_level", "hire_source", "legacy_entity_code", "contract_type",
          "age_band", "gender", "acting", "underpaid"]:
    ct = pd.crosstab(h[v], h["voluntary"])
    if ct.shape[0] < 2:
        continue
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    r = h.groupby(v)["voluntary"].agg(["mean", "size"]).sort_values("mean", ascending=False)
    top, bot = r.index[0], r.index[-1]
    print(f"  {v:<20} chi2={chi2:6.2f} p={p:<9.3g}  highest {str(top)[:26]:<26}"
          f"{r.iloc[0]['mean']:.1%} (n={int(r.iloc[0]['size'])})   lowest {str(bot)[:22]:<22}"
          f"{r.iloc[-1]['mean']:.1%} (n={int(r.iloc[-1]['size'])})")

# ============================================ C. multivariate + tenure survival for HiPo
line("C. MULTIVARIATE — HiPo voluntary exit, employee level")
m = e[e.hipo == 1].copy()
m["nonresp"] = (m["nonresponse_rate"] > 0).astype(int)
f = ("voluntary ~ compa_ratio + tenure_years + role_level + acquired + acting + underpaid"
     " + nonresp + slow_fill + C(department) + C(hire_source) + C(contract_type)")
fit = smf.logit(f, data=m).fit(disp=0)
res = pd.DataFrame({"OR": np.exp(fit.params), "lo": np.exp(fit.conf_int()[0]),
                    "hi": np.exp(fit.conf_int()[1]), "p": fit.pvalues})
print(res[~res.index.str.startswith(("C(", "Intercept"))]
      .sort_values("p").to_string(float_format=lambda x: f"{x:.4g}"))
print(f"n={int(fit.nobs)}  pseudo-R2={fit.prsquared:.4f}")

line("C2. TENURE AT EXIT — how fast do HiPos go?")
lv = e[(e.voluntary == 1)]
for g, name in [(lv[lv.hipo == 1], "HiPo leavers"), (lv[lv.hipo == 0], "non-HiPo leavers")]:
    print(f"  {name:<18} n={len(g):<5} median tenure {g.tenure_years.median():.1f}y  "
          f"mean {g.tenure_years.mean():.1f}y  <2y: {(g.tenure_years<2).mean():.1%}")
a = lv.loc[lv.hipo == 1, "tenure_years"]; b = lv.loc[lv.hipo == 0, "tenure_years"]
print(f"  Mann-Whitney p = {stats.mannwhitneyu(a, b)[1]:.3g}")

# exit rate by tenure band, HiPo vs not
e["tenure_band"] = pd.cut(e["tenure_years"], [0, 1, 2, 3, 5, 10, 100],
                          labels=["<1y", "1-2y", "2-3y", "3-5y", "5-10y", "10y+"])
piv = e.pivot_table(index="tenure_band", columns="hipo", values="voluntary",
                    aggfunc=["mean", "size"], observed=True)
print("\n", piv.round(4).to_string())
e.to_csv(OUT / "master_plus.csv", index=False)
pr.to_csv(OUT / "review_risk_set.csv", index=False)
print("\nwrote eddited_csv/master_plus.csv + review_risk_set.csv")
