"""
wave_risk_set.py — the clean design. Everything above this point compared leavers to stayers
using whatever data each happened to have, which conflates "left early" with "was different".

Discrete-time survival instead. For each of the five survey waves:
    risk set   = everyone employed on the survey date
    exposure   = what they said (or refused to say) in that wave
    outcome    = did they exit voluntarily within the next 180 days
Same calendar moment, same look-ahead, same exposure window for everyone in the row. A leaver
and a stayer contribute on equal terms until the leaver drops out of the risk set.

Run separately for the HiPo cohort and for everyone, and with regrettable exit as the outcome.
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "original_csv", ROOT / "eddited_csv"

DIMS = ["manager_effectiveness", "psychological_safety", "recognition", "career_development",
        "senior_leadership_trust", "purpose_meaning", "wellbeing", "confidence_in_role_future"]
HORIZON = 180

emp = pd.read_csv(ROOT / "eddited_csv" / "master_features.csv", low_memory=False)
emp["exit_dt"] = pd.to_datetime(emp["exit_dt"])
eng = pd.read_csv(RAW / "engagement.csv", parse_dates=["survey_date"])

keep = ["employee_id", "exit_dt", "voluntary", "regrettable", "hipo", "compa_ratio",
        "compa_vs_peer", "tenure_years", "role_level", "department", "salary",
        "hire_source", "acting_appointment", "manager_id"]
rs = eng.merge(emp[keep], on="employee_id", how="left")

# in the risk set only if still employed on the survey date
rs = rs[rs["exit_dt"].isna() | (rs["exit_dt"] > rs["survey_date"])].copy()
rs["days_to_exit"] = (rs["exit_dt"] - rs["survey_date"]).dt.days
rs["exit_180"] = ((rs["voluntary"] == 1) & (rs["days_to_exit"] <= HORIZON)).astype(int)
rs["regret_180"] = ((rs["regrettable"] == 1) & (rs["days_to_exit"] <= HORIZON)).astype(int)
rs["nonresponse"] = (~rs["response_flag"].astype(bool)).astype(int)
rs["eng_index"] = rs[DIMS].mean(axis=1)

# wave 5 (Jul-Aug 2025) has only ~150 days of look-ahead before the 31-Dec-2025 censor.
# Keeping it would understate exits; flag it so we can test with and without.
rs["truncated_window"] = (rs["wave_number"] == 5).astype(int)

print(f"risk-set rows: {len(rs):,}   exits within {HORIZON}d: {rs.exit_180.sum():,}"
      f"   regrettable: {rs.regret_180.sum():,}")
print(rs.groupby("wave_number").agg(n=("employee_id", "size"), exits=("exit_180", "sum"),
                                    rate=("exit_180", "mean")).round(4))

# ---------------------------------------------------------------- per-dimension testing
def test_block(data, outcome, label):
    rows = []
    ans = data[data["response_flag"] == True]
    for d in DIMS + ["eng_index"]:
        a = ans.loc[ans[outcome] == 1, d].dropna()
        b = ans.loc[ans[outcome] == 0, d].dropna()
        if len(a) < 20:
            continue
        t, p = stats.ttest_ind(a, b, equal_var=False)
        sp = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
        rows.append(dict(pop=label, var=d, leavers=a.mean(), stayers=b.mean(),
                         gap=a.mean()-b.mean(), d=(a.mean()-b.mean())/sp, p=p,
                         n_ev=len(a), n=len(a)+len(b)))
    # non-response, using the full risk set
    ct = pd.crosstab(data["nonresponse"], data[outcome])
    if ct.shape == (2, 2):
        orr, p = stats.fisher_exact(ct.values)
        r = data.groupby("nonresponse")[outcome].mean()
        rows.append(dict(pop=label, var="NON-RESPONSE", leavers=r.get(1, np.nan),
                         stayers=r.get(0, np.nan), gap=r.get(1, np.nan)-r.get(0, np.nan),
                         d=orr, p=p, n_ev=int(ct[1].sum()), n=int(ct.values.sum())))
    return pd.DataFrame(rows)


blocks = [
    (rs, "exit_180", "ALL -> voluntary"),
    (rs[rs.hipo == 1], "exit_180", "HIPO -> voluntary"),
    (rs, "regret_180", "ALL -> regrettable"),
    (rs[rs.hipo == 1], "regret_180", "HIPO -> regrettable"),
]
res = pd.concat([test_block(d, o, l) for d, o, l in blocks], ignore_index=True)
res["q"] = multipletests(res["p"], method="fdr_bh")[1]
res["sig"] = np.where(res.q < .001, "***", np.where(res.q < .01, "**",
                      np.where(res.q < .05, "*", "")))
pd.set_option("display.width", 220)
for l in res["pop"].unique():
    print(f"\n{'='*104}\n{l}\n{'='*104}")
    print(res[res["pop"] == l]
          .sort_values("p")[["var", "leavers", "stayers", "gap", "d", "p", "q", "n_ev", "sig"]]
          .to_string(index=False, float_format=lambda x: f"{x:.4g}"))
res.to_csv(OUT / "wave_risk_tests.csv", index=False)

# ------------------------------------------------------- multivariate, HiPo risk set
print(f"\n{'='*104}\nMULTIVARIATE — HiPo risk set, voluntary exit within {HORIZON}d\n{'='*104}")
m = rs[(rs.hipo == 1) & (rs.response_flag == True)].copy()
X = pd.DataFrame({
    "career_development": m.career_development,
    "recognition": m.recognition,
    "manager_effectiveness": m.manager_effectiveness,
    "confidence_in_role_future": m.confidence_in_role_future,
    "psychological_safety": m.psychological_safety,
    "senior_leadership_trust": m.senior_leadership_trust,
    "wellbeing": m.wellbeing,
    "purpose_meaning": m.purpose_meaning,
    "compa_ratio": m.compa_ratio,
    "tenure_years": m.tenure_years,
    "role_level": m.role_level,
})
X = pd.concat([X, pd.get_dummies(m.department, prefix="dep", drop_first=True).astype(float),
               pd.get_dummies(m.wave_number, prefix="wave", drop_first=True).astype(float)], axis=1)
y = m["exit_180"]
ok = X.notna().all(axis=1)
X, y = X[ok], y[ok]
fit = sm.Logit(y, sm.add_constant(X)).fit(disp=0, cov_type="cluster",
                                          cov_kwds={"groups": m.loc[ok, "employee_id"]})
out = pd.DataFrame({"OR": np.exp(fit.params), "lo": np.exp(fit.conf_int()[0]),
                    "hi": np.exp(fit.conf_int()[1]), "p": fit.pvalues})
print(out[~out.index.str.startswith(("dep_", "wave_", "const"))]
      .sort_values("p").to_string(float_format=lambda x: f"{x:.4g}"))
print(f"\nn={len(y)} person-waves, {int(y.sum())} exits, pseudo-R2={fit.prsquared:.4f}, "
      f"SEs clustered on employee")
rs.to_csv(OUT / "wave_risk_set.csv", index=False)
print("wrote eddited_csv/wave_risk_set.csv + wave_risk_tests.csv")
