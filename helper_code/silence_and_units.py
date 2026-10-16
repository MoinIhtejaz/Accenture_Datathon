"""
silence_and_units.py — the two strongest surviving signals, pushed until they break.

  A. SURVEY SILENCE. In the wave risk-set this was the single largest predictor of exit
     (OR 2.25 all staff, 1.66 HiPo). Test whether it is a warning shot or just a symptom:
     does the silence arrive before the resignation, and how much before?
  B. UNIT-LEVEL CO-MOVEMENT. 112 people had a manager who also departed; 75% of them left
     voluntarily against an 8.5% baseline, with no lead-lag order. That looks like whole
     teams unwinding. Find out which teams and whether the department effect is just this.
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
line = lambda t: print(f"\n{'='*104}\n{t}\n{'='*104}")

# ================================================================== A. survey silence
line("A1. SILENCE AS A LEADING INDICATOR — exit within 180 days of each wave")
for name, sub in [("ALL", rs), ("HIPO", rs[rs.hipo == 1]), ("NON-HIPO", rs[rs.hipo == 0])]:
    ct = pd.crosstab(sub["nonresponse"], sub["exit_180"])
    orr, p = stats.fisher_exact(ct.values)
    a, b, c, d = ct.values.ravel()
    se = np.sqrt(1/a + 1/b + 1/c + 1/d)
    r = sub.groupby("nonresponse")["exit_180"].mean()
    print(f"  {name:<9} answered {r[0]:.2%} -> silent {r[1]:.2%}   OR={orr:.2f} "
          f"[{np.exp(np.log(orr)-1.96*se):.2f}-{np.exp(np.log(orr)+1.96*se):.2f}]  "
          f"p={p:.3g}   person-waves n={len(sub):,}")

print("\n  Adjusted (logit, clustered on employee, wave + department + level fixed effects):")
m = smf.logit("exit_180 ~ nonresponse + hipo + tenure_years + compa_ratio + role_level "
              "+ C(department) + C(wave_number)", data=rs).fit(
              disp=0, cov_type="cluster", cov_kwds={"groups": rs["employee_id"]})
for t in ["nonresponse", "hipo"]:
    print(f"    {t:<14} OR={np.exp(m.params[t]):.3f} "
          f"[{np.exp(m.conf_int().loc[t,0]):.3f}-{np.exp(m.conf_int().loc[t,1]):.3f}] "
          f"p={m.pvalues[t]:.3g}")
mi = smf.logit("exit_180 ~ nonresponse * hipo + tenure_years + role_level + C(department) "
               "+ C(wave_number)", data=rs).fit(disp=0, cov_type="cluster",
               cov_kwds={"groups": rs["employee_id"]})
print(f"    nonresponse:hipo interaction OR={np.exp(mi.params['nonresponse:hipo']):.3f} "
      f"p={mi.pvalues['nonresponse:hipo']:.3f}")

line("A2. HOW EARLY IS THE WARNING? (silent waves only, by lead time to exit)")
sil = rs[rs["nonresponse"] == 1].copy()
sil["lead"] = pd.cut(sil["days_to_exit"], [0, 90, 180, 270, 365, 10000],
                     labels=["0-90d", "90-180d", "180-270d", "270-365d", ">365d"])
base = rs.loc[rs.nonresponse == 0, "exit_180"].mean()
for h, hn in [(None, "ALL"), (1, "HIPO")]:
    d = rs if h is None else rs[rs.hipo == 1]
    out = []
    for horizon in [90, 180, 270, 365]:
        d2 = d.copy()
        d2["ev"] = ((d2["voluntary"] == 1) & (d2["days_to_exit"] <= horizon)).astype(int)
        ct = pd.crosstab(d2["nonresponse"], d2["ev"])
        if ct.shape != (2, 2):
            continue
        orr, p = stats.fisher_exact(ct.values)
        r = d2.groupby("nonresponse")["ev"].mean()
        out.append(f"{horizon:>4}d: {r[0]:.2%}->{r[1]:.2%} OR={orr:.2f} p={p:.2g}")
    print(f"  {hn:<6} " + " | ".join(out))

print("\n  Of the people who eventually left voluntarily, what did they do in their LAST survey?")
last_wave = (rs.sort_values("survey_date").groupby("employee_id")
               .agg(last_silent=("nonresponse", "last"), voluntary=("voluntary", "first"),
                    hipo=("hipo", "first"), regrettable=("regrettable", "first"),
                    n_waves=("wave_number", "size")))
lw = last_wave[last_wave["n_waves"] >= 2]
print(lw.groupby(["hipo", "voluntary"])["last_silent"].agg(["mean", "size"])
        .rename(columns={"mean": "went_silent_in_final_survey"}).to_string(
        float_format=lambda x: f"{x:.3f}"))
ct = pd.crosstab(lw["last_silent"], lw["voluntary"])
print(f"  Fisher OR={stats.fisher_exact(ct.values)[0]:.2f}, p={stats.fisher_exact(ct.values)[1]:.3g}")

line("A3. SILENCE vs LOW SCORES — which is the better flag?")
d = rs.copy()
d["low_score"] = (d["eng_index"] < d["eng_index"].quantile(0.25)).astype(float)
d.loc[d["nonresponse"] == 1, "low_score"] = np.nan
for name, cond, lab in [("silent", d["nonresponse"] == 1, "did not respond"),
                        ("bottom-quartile scorer", d["low_score"] == 1, "responded, scored low"),
                        ("everyone else", (d["nonresponse"] == 0) & (d["low_score"] == 0), "responded, scored ok")]:
    s = d[cond]
    print(f"  {name:<24} n={len(s):>6,}  exit within 180d = {s['exit_180'].mean():.2%}  "
          f"({lab})")

# ============================================================ B. unit-level co-movement
line("B1. WHO ARE THE 112? — employees whose manager also departed")
d = e[e["mgr_departed"] == 1].copy()
print(f"  n={len(d)}  voluntary={int(d.voluntary.sum())} ({d.voluntary.mean():.0%})  "
      f"hipo={int(d.hipo.sum())}  regrettable={int(d.regrettable.sum())}")
print("\n  department mix vs company:")
cmp_ = pd.DataFrame({"cascade_%": d["department"].value_counts(normalize=True),
                     "company_%": e["department"].value_counts(normalize=True)})
print(cmp_.round(3).to_string())
print("\n  legacy entity mix:")
print(pd.DataFrame({"cascade_%": d["legacy_entity_code"].value_counts(normalize=True),
                    "company_%": e["legacy_entity_code"].value_counts(normalize=True)}
                   ).round(3).to_string())
print("\n  stated exit reason (cascade leavers vs all voluntary leavers):")
print(pd.DataFrame({"cascade_%": d.loc[d.voluntary == 1, "stated_exit_reason"].value_counts(normalize=True),
                    "all_vol_%": e.loc[e.voluntary == 1, "stated_exit_reason"].value_counts(normalize=True)}
                   ).round(3).to_string())
print("\n  pathway:")
print(pd.DataFrame({"cascade_%": d.loc[d.voluntary == 1, "pathway"].value_counts(normalize=True),
                    "all_vol_%": e.loc[e.voluntary == 1, "pathway"].value_counts(normalize=True)}
                   ).round(3).to_string())

line("B2. DOES THE DEPARTMENT EFFECT SURVIVE REMOVING THE CASCADE GROUP?")
h = e[e.hipo == 1]
for lab, sub in [("all HiPos", h), ("HiPos excl. cascade", h[h.mgr_departed == 0])]:
    ct = pd.crosstab(sub["department"], sub["voluntary"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    r = sub.groupby("department")["voluntary"].mean().sort_values(ascending=False)
    print(f"  {lab:<22} chi2={chi2:.2f} p={p:.4g}  "
          f"top={r.index[0][:20]} {r.iloc[0]:.1%}  bottom={r.index[-1][:20]} {r.iloc[-1]:.1%}")

line("B3. IS THE MANAGER-DEPARTURE EFFECT JUST SPAN? (tiny teams unwind more easily)")
print(e.groupby("mgr_departed")[["mgr_span", "tenure_years", "compa_ratio", "hipo"]]
        .mean().round(3).to_string())
sub = e[e["mgr_span"] <= 3]
ct = pd.crosstab(sub["mgr_departed"], sub["voluntary"])
print(f"  within small teams (span<=3): OR={stats.fisher_exact(ct.values)[0]:.1f} "
      f"p={stats.fisher_exact(ct.values)[1]:.3g}")
sub = e[e["mgr_span"] > 3]
ct = pd.crosstab(sub["mgr_departed"], sub["voluntary"])
print(f"  within larger teams (span>3):  OR={stats.fisher_exact(ct.values)[0]:.1f} "
      f"p={stats.fisher_exact(ct.values)[1]:.3g}")
