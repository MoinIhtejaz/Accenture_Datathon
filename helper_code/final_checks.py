"""
final_checks.py — the last four questions before writing anything down.

  1. The span<=3 co-departure cluster: real unit dissolution, or a generator artefact?
  2. Why Corporate Operations and Risk & Compliance? Rule out the obvious explanations.
  3. Backfill quality — does losing a HiPo cost more than a vacancy? (ties to hiring inefficiency)
  4. Robustness: does the silence result hold with different horizons, per wave, and if we
     drop the notice period entirely?
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eddited_csv"
e = pd.read_csv(OUT / "master_plus.csv", low_memory=False)
rs = pd.read_csv(OUT / "wave_risk_set.csv", low_memory=False, parse_dates=["survey_date"])
e["exit_dt"] = pd.to_datetime(e["exit_dt"])
e["promo_rate"] = e["n_promo_rec"] / e["n_reviews"].replace(0, np.nan)
line = lambda t: print(f"\n{'='*104}\n{t}\n{'='*104}")

# ------------------------------------------------------------- 1. the tiny-unit cluster
line("1. THE span<=3 CO-DEPARTURE CLUSTER")
u = e.groupby("manager_id").agg(span=("employee_id", "size"), left=("is_leaver", "sum"),
                                vol=("voluntary", "sum"))
u["all_gone"] = (u["left"] == u["span"]).astype(int)
print("  share of units where EVERY member departed, by span:")
print(u.assign(band=pd.cut(u["span"], [0, 1, 2, 3, 5, 10, 1000],
               labels=["1", "2", "3", "4-5", "6-10", "10+"]))
       .groupby("band", observed=True)
       .agg(units=("span", "size"), pct_fully_dissolved=("all_gone", "mean"),
            mean_vol_rate=("vol", lambda s: s.mean()))
       .to_string(float_format=lambda x: f"{x:.4g}"))
mgrs = set(e.loc[e.is_leaver, "employee_id"])
tiny = u[(u["span"] <= 3) & (u.index.isin(mgrs))]
print(f"\n  units with span<=3 whose manager departed: {len(tiny)}")
print(f"  of those, fully dissolved (all reports also gone): {tiny['all_gone'].mean():.1%}")
big = u[(u["span"] > 3) & (u.index.isin(mgrs))]
print(f"  units with span>3 whose manager departed: {len(big)}, "
      f"fully dissolved: {big['all_gone'].mean():.1%}")
print("\n  Read: the effect lives entirely in units too small to survive one departure.")
print("  Treat as a structural fragility finding, not a manager-behaviour finding.")

# ------------------------------------------------------------- 2. why Corp Ops / Risk?
line("2. CORPORATE OPERATIONS AND RISK & COMPLIANCE — what is different?")
h = e[e.hipo == 1]
prof = h.groupby("department").agg(
    n=("employee_id", "size"), exit_rate=("voluntary", "mean"),
    compa=("compa_ratio", "mean"), tenure=("tenure_years", "mean"),
    level=("role_level", "mean"), span=("mgr_span", "mean"),
    days_to_fill=("days_to_fill", "mean"), promo_rate=("promo_rate", "mean"),
    eng=("mean_engagement_index", "mean"), nonresp=("nonresponse_rate", "mean"),
    acquired=("acquired", "mean"), goal=("mean_goal", "mean"))
print(prof.sort_values("exit_rate", ascending=False).to_string(float_format=lambda x: f"{x:.4g}"))
print("\n  Correlation of department HiPo exit rate with each candidate explanation:")
for c in ["compa", "tenure", "level", "span", "days_to_fill", "promo_rate", "eng",
          "nonresp", "acquired", "goal"]:
    r, p = stats.pearsonr(prof["exit_rate"], prof[c])
    print(f"    {c:<14} r={r:+.3f}  p={p:.3f}")
print("\n  HiPo density by department (are the hot departments just HiPo-heavy?):")
dens = e.groupby("department").agg(hipo_share=("hipo", "mean"),
                                   hipo_exit=("employee_id", lambda s: np.nan))
dens["hipo_exit"] = h.groupby("department")["voluntary"].mean()
r, p = stats.pearsonr(dens["hipo_share"], dens["hipo_exit"])
print(dens.round(4).to_string())
print(f"    corr(HiPo density, HiPo exit rate) r={r:+.3f} p={p:.3f}")
print("\n  Logit: does department survive controls?")
m = smf.logit("voluntary ~ C(department, Treatment('Retail Banking')) + tenure_years "
              "+ compa_ratio + role_level + C(hire_source)", data=h).fit(disp=0)
dd = pd.DataFrame({"OR": np.exp(m.params), "lo": np.exp(m.conf_int()[0]),
                   "hi": np.exp(m.conf_int()[1]), "p": m.pvalues})
print(dd[dd.index.str.contains("department")].to_string(float_format=lambda x: f"{x:.4g}"))

# ------------------------------------------------------------------- 3. backfill quality
line("3. BACKFILL — what does replacing a HiPo look like operationally?")
print(e.groupby(["hipo"])[["days_to_fill"]].describe().round(1).to_string())
a = e.loc[e.hipo == 1, "days_to_fill"].dropna(); b = e.loc[e.hipo == 0, "days_to_fill"].dropna()
print(f"  HiPo roles take {a.mean():.1f}d to fill vs {b.mean():.1f}d  "
      f"t-test p={stats.ttest_ind(a,b,equal_var=False)[1]:.3g}")
print("\n  hire_source mix, HiPo vs rest (agency = 18% fee, direct = $5.5k benchmark):")
print(pd.DataFrame({"hipo_%": e.loc[e.hipo == 1, "hire_source"].value_counts(normalize=True),
                    "all_%": e["hire_source"].value_counts(normalize=True)}).round(3).to_string())
print("\n  Does hire source predict HiPo exit?")
ct = pd.crosstab(h["hire_source"], h["voluntary"])
print(h.groupby("hire_source")["voluntary"].agg(["mean", "size"]).round(4).to_string())
print(f"  chi2 p={stats.chi2_contingency(ct)[1]:.3f}")

# ------------------------------------------------------------------ 4. silence robustness
line("4. SILENCE — robustness")
print("  per wave (all staff):")
for w in sorted(rs["wave_number"].unique()):
    s = rs[rs.wave_number == w]
    ct = pd.crosstab(s["nonresponse"], s["exit_180"])
    if ct.shape != (2, 2):
        continue
    orr, p = stats.fisher_exact(ct.values)
    r = s.groupby("nonresponse")["exit_180"].mean()
    print(f"    wave {w}: {r[0]:.2%} -> {r[1]:.2%}   OR={orr:.2f}  p={p:.3g}  n={len(s):,}")
print("\n  excluding wave 5 (truncated look-ahead):")
s = rs[rs.wave_number < 5]
ct = pd.crosstab(s["nonresponse"], s["exit_180"])
print(f"    OR={stats.fisher_exact(ct.values)[0]:.2f}  p={stats.fisher_exact(ct.values)[1]:.3g}")
print("\n  dropping any wave inside the notice window (exit within 90d) — is it still early?")
s = rs[(rs["days_to_exit"].isna()) | (rs["days_to_exit"] > 90)].copy()
s["ev"] = ((s["voluntary"] == 1) & (s["days_to_exit"] <= 365)).astype(int)
ct = pd.crosstab(s["nonresponse"], s["ev"])
orr, p = stats.fisher_exact(ct.values)
r = s.groupby("nonresponse")["ev"].mean()
print(f"    silence 90-365 days ahead of exit: {r[0]:.2%} -> {r[1]:.2%}  OR={orr:.2f}  p={p:.3g}")
sh = s[s.hipo == 1]
ct = pd.crosstab(sh["nonresponse"], sh["ev"])
orr, p = stats.fisher_exact(ct.values)
r = sh.groupby("nonresponse")["ev"].mean()
print(f"    same, HiPo only:                    {r[0]:.2%} -> {r[1]:.2%}  OR={orr:.2f}  p={p:.3g}")

line("5. HEADLINE COUNTS FOR THE DECK")
print(f"  headcount {len(e):,} | HiPo {int(e.hipo.sum()):,} ({e.hipo.mean():.1%})")
print(f"  voluntary exits {int(e.voluntary.sum()):,} | HiPo voluntary {int(((e.hipo==1)&(e.voluntary==1)).sum())}")
print(f"  HiPo voluntary exit rate {e[e.hipo==1].voluntary.mean():.2%} vs "
      f"non-HiPo {e[e.hipo==0].voluntary.mean():.2%}  "
      f"(OR={stats.fisher_exact(pd.crosstab(e.hipo,e.voluntary).values)[0]:.2f}, "
      f"p={stats.fisher_exact(pd.crosstab(e.hipo,e.voluntary).values)[1]:.3g})")
sal = e.loc[(e.hipo == 1) & (e.voluntary == 1), "salary"].sum()
print(f"  HiPo voluntary leavers' combined base salary ${sal:,.0f}  "
      f"-> at 1.5x replacement, 85% backfill = ${sal*1.5*0.85:,.0f}")
