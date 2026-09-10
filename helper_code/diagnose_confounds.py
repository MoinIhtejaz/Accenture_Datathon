"""
diagnose_confounds.py — before believing anything in sweep_results.csv, kill the artefacts.

Three of the strongest "findings" from the raw sweep are measurement artefacts, and one is
almost too strong to be real. This script separates them.

  1. n_reviews / n_promo_rec  — exposure bias. A 2024 leaver could only ever have 1 review.
  2. mgr_team_vol_rate        — contains the employee's own exit. Rebuild leave-one-out.
  3. mgr_departed             — 75% of employees with a departed manager left voluntarily.
                                Real cascade, or does the generator delete whole teams?
                                Test = did the report leave AFTER the manager?
  4. nonresponse              — leavers were offered fewer waves, so raw counts mislead.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "eddited_csv" / "master_features.csv", low_memory=False)
df["exit_dt"] = pd.to_datetime(df["exit_dt"])
emp_exit = df.set_index("employee_id")["exit_dt"]
emp_vol = df.set_index("employee_id")["voluntary"]

line = lambda t: print(f"\n{'='*100}\n{t}\n{'='*100}")

# ---------------------------------------------------------------- 1. exposure bias proof
line("1. EXPOSURE BIAS — n_reviews and n_promo_rec are not findings")
df["obs_days"] = (df["exit_dt"].fillna(pd.Timestamp("2025-12-31"))
                  - pd.Timestamp("2024-01-01")).dt.days.clip(lower=1)
print(df.groupby("status")[["obs_days", "n_reviews", "waves_offered"]].mean().round(2))
df["promo_rate"] = df["n_promo_rec"] / df["n_reviews"].replace(0, np.nan)
for pop, name in [(df[df.hipo == 1], "HiPo cohort"), (df, "All staff")]:
    a = pop.loc[pop.voluntary == 1, "promo_rate"].dropna()
    b = pop.loc[pop.voluntary == 0, "promo_rate"].dropna()
    t, p = stats.ttest_ind(a, b, equal_var=False)
    print(f"  {name}: promo recs PER REVIEW  leavers {a.mean():.3f} vs stayers {b.mean():.3f}  "
          f"t={t:.2f} p={p:.2e}  n={len(a)}/{len(b)}")

# --------------------------------------------------- 2. leave-one-out manager exit rate
line("2. MANAGER TEAM EXIT RATE — leave-one-out rebuild")
g = df.groupby("manager_id")["voluntary"]
tot, cnt = g.transform("sum"), g.transform("size")
df["mgr_vol_loo"] = np.where(cnt > 1, (tot - df["voluntary"]) / (cnt - 1), np.nan)
sub = df.dropna(subset=["mgr_vol_loo"])
a = sub.loc[sub.voluntary == 1, "mgr_vol_loo"]
b = sub.loc[sub.voluntary == 0, "mgr_vol_loo"]
t, p = stats.ttest_ind(a, b, equal_var=False)
print(f"  ALL: leaver's teammates' exit rate {a.mean():.3f} vs stayer's {b.mean():.3f}  "
      f"t={t:.2f} p={p:.2e}")
h = sub[sub.hipo == 1]
a2 = h.loc[h.voluntary == 1, "mgr_vol_loo"]; b2 = h.loc[h.voluntary == 0, "mgr_vol_loo"]
t2, p2 = stats.ttest_ind(a2, b2, equal_var=False)
print(f"  HiPo: {a2.mean():.3f} vs {b2.mean():.3f}  t={t2:.2f} p={p2:.2e}  n={len(a2)}/{len(b2)}")

# how concentrated is attrition across managers?
mg = df.groupby("manager_id").agg(span=("employee_id", "size"), vol=("voluntary", "sum"))
mg = mg[mg["span"] >= 3].sort_values("vol", ascending=False)
tot_vol = mg["vol"].sum()
for k in [10, 25, 50, 100]:
    print(f"  top {k:>3} managers (of {len(mg)} with span>=3) hold "
          f"{mg['vol'].head(k).sum()/tot_vol:.1%} of their pooled voluntary exits")
print(f"  managers with zero voluntary exits: {(mg['vol']==0).mean():.1%}")

# ------------------------------------------------------ 3. manager departure — cascade?
line("3. MANAGER DEPARTURE CASCADE — does the report leave AFTER the manager?")
d = df[df["mgr_departed"] == 1].copy()
d["mgr_exit"] = d["manager_id"].map(emp_exit)
d["mgr_vol"] = d["manager_id"].map(emp_vol)
d["gap_days"] = (d["exit_dt"] - d["mgr_exit"]).dt.days
left = d[d["voluntary"] == 1]
print(f"  employees whose manager departed: {len(d)}   of whom left voluntarily: {len(left)} "
      f"({len(left)/len(d):.1%})   baseline voluntary rate: {df.voluntary.mean():.1%}")
print(f"  report left AFTER manager: {(left['gap_days'] > 0).sum()} / {left['gap_days'].notna().sum()}")
print(f"  gap in days — median {left['gap_days'].median():.0f}, "
      f"IQR {left['gap_days'].quantile(.25):.0f} to {left['gap_days'].quantile(.75):.0f}")
print(f"  within 90 days of manager exit: {(left['gap_days'].between(0,90)).sum()}")
print(f"  within 180 days: {(left['gap_days'].between(0,180)).sum()}")
ct = pd.crosstab(df["mgr_departed"], df["voluntary"])
orr, pf = stats.fisher_exact(ct.values)
print(f"  Fisher OR = {orr:.1f}, p = {pf:.2e}")
print(f"  regrettable among cascade leavers: {left['regrettable'].mean():.1%} "
      f"vs {df.loc[df.voluntary==1,'regrettable'].mean():.1%} of all voluntary exits")
print(f"  hipo among cascade leavers: {left['hipo'].mean():.1%} vs {df.hipo.mean():.1%} overall")

# --------------------------------------------------------- 4. non-response, exposure-fair
line("4. NON-RESPONSE — compare only people offered the same number of waves")
for w in [3, 4, 5]:
    s = df[df["waves_offered"] == w]
    if len(s) < 100:
        continue
    ct = pd.crosstab(s["ever_nonresponder"], s["voluntary"])
    if ct.shape != (2, 2):
        continue
    orr, p = stats.fisher_exact(ct.values)
    r = s.groupby("ever_nonresponder")["voluntary"].mean()
    print(f"  offered {w} waves (n={len(s)}): exit rate responder {r.get(0,np.nan):.1%} "
          f"vs non-responder {r.get(1,np.nan):.1%}  OR={orr:.2f} p={p:.3f}")

df[["employee_id", "mgr_vol_loo", "promo_rate", "obs_days"]].to_csv(
    ROOT / "eddited_csv" / "confound_adjusted.csv", index=False)
print("\nwrote eddited_csv/confound_adjusted.csv")
