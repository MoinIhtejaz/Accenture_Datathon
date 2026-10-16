"""
verify_findings05.py — recompute every number quoted in findings_05 straight from the raw CSVs,
without touching any of the intermediate files. If a number disagrees, the memo is wrong.
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

warnings.filterwarnings("ignore")
RAW = Path(__file__).resolve().parent.parent / "original_csv"
emp = pd.read_csv(RAW / "employees.csv", parse_dates=["hire_date", "exit_date"])
att = pd.read_csv(RAW / "attrition_log.csv", parse_dates=["exit_date"])
eng = pd.read_csv(RAW / "engagement.csv", parse_dates=["survey_date"])
perf = pd.read_csv(RAW / "performance.csv", parse_dates=["review_date"])

fails = []
def chk(label, got, want, tol=0.02, fmt="{:.4f}"):
    ok = abs(got - want) <= tol * max(abs(want), 1e-9) if want else abs(got - want) <= tol
    print(f"  [{'OK ' if ok else 'BAD'}] {label:<62} got {fmt.format(got):>12}  memo {fmt.format(want):>12}")
    if not ok:
        fails.append(label)

d = emp.merge(att[["employee_id", "exit_type", "regrettable_flag", "exit_date"]]
              .rename(columns={"exit_date": "xd"}), on="employee_id", how="left")
d["exit_dt"] = d["exit_date"].fillna(d["xd"])
d["vol"] = (d["exit_type"] == "voluntary").astype(int)
d["reg"] = (d["regrettable_flag"] == True).astype(int)
d["hp"] = d["hipo_flag"].astype(int)

print("\nFINDING 1 — the HiPo gap")
chk("HiPo voluntary exit rate", d[d.hp == 1].vol.mean(), .1248)
chk("non-HiPo voluntary exit rate", d[d.hp == 0].vol.mean(), .0805)
o, p = stats.fisher_exact(pd.crosstab(d.hp, d.vol).values)
chk("odds ratio", o, 1.63); chk("p-value (log10)", np.log10(p), np.log10(5.5e-7), tol=.05)
chk("HiPo voluntary leavers, n", ((d.hp == 1) & (d.vol == 1)).sum(), 151, tol=0, fmt="{:.0f}")
sal = d.loc[(d.hp == 1) & (d.vol == 1), "salary"].sum()
chk("combined base salary ($M)", sal/1e6, 19.6, fmt="{:.2f}")
chk("replacement cost 1.5x x 85% ($M)", sal*1.5*.85/1e6, 24.9, fmt="{:.2f}")

print("\nFINDING 2 — silence (rebuilt risk set from scratch)")
CEN = pd.Timestamp("2025-12-31")
r = eng.merge(d[["employee_id", "exit_dt", "vol", "hp"]], on="employee_id", how="left")
r = r[r.exit_dt.isna() | (r.exit_dt > r.survey_date)]
r = r.assign(dte=(r.exit_dt - r.survey_date).dt.days)
r["ev"] = ((r.vol == 1) & (r.dte <= 180)).astype(int)
r["sil"] = (~r.response_flag.astype(bool)).astype(int)
chk("risk-set person-waves", len(r), 55939, tol=0, fmt="{:.0f}")
chk("exit rate | answered (all responders)", r[r.sil == 0].ev.mean(), .0175)
chk("exit rate | silent", r[r.sil == 1].ev.mean(), .0384)
o, p = stats.fisher_exact(pd.crosstab(r.sil, r.ev).values)
chk("silence OR", o, 2.24); chk("silence p (log10)", np.log10(p), np.log10(8.8e-35), tol=.05)
DIMS = ["manager_effectiveness", "psychological_safety", "recognition", "career_development",
        "senior_leadership_trust", "purpose_meaning", "wellbeing", "confidence_in_role_future"]
r["idx"] = r[DIMS].mean(axis=1)
q = r.loc[r.sil == 0, "idx"].quantile(.25)
chk("exit rate | answered, bottom quartile", r[(r.sil == 0) & (r.idx < q)].ev.mean(), .0204)
chk("exit rate | answered, top 75%", r[(r.sil == 0) & (r.idx >= q)].ev.mean(), .0165)
h = r[r.hp == 1]
chk("HiPo exit rate | answered", h[h.sil == 0].ev.mean(), .0274)
chk("HiPo exit rate | silent", h[h.sil == 1].ev.mean(), .0447)
chk("HiPo silence OR", stats.fisher_exact(pd.crosstab(h.sil, h.ev).values)[0], 1.66)

print("\n  robustness")
s = r[(r.dte.isna()) | (r.dte > 90)].copy()
s["e2"] = ((s.vol == 1) & (s.dte <= 365)).astype(int)
chk("OR, silence 90-365d before exit (all)",
    stats.fisher_exact(pd.crosstab(s.sil, s.e2).values)[0], 2.07)
sh = s[s.hp == 1]
chk("OR, silence 90-365d before exit (HiPo)",
    stats.fisher_exact(pd.crosstab(sh.sil, sh.e2).values)[0], 1.50, tol=.04)
w = r[r.wave_number < 5]
chk("OR excluding wave 5", stats.fisher_exact(pd.crosstab(w.sil, w.ev).values)[0], 2.39)
lastw = r.sort_values("survey_date").groupby("employee_id").agg(
    ls=("sil", "last"), vol=("vol", "first"), n=("wave_number", "size"))
lw = lastw[lastw.n >= 2]
chk("silent in final survey | eventual leaver", lw[lw.vol == 1].ls.mean(), .34, tol=.04)
chk("silent in final survey | stayer", lw[lw.vol == 0].ls.mean(), .186, tol=.04)

print("\nFINDING 4 — promotion, review-level")
pv = perf.merge(d[["employee_id", "exit_dt", "vol", "hp"]], on="employee_id", how="left")
pv = pv[pv.exit_dt.isna() | (pv.exit_dt > pv.review_date)]
pv = pv.assign(dte=(pv.exit_dt - pv.review_date).dt.days)
pv["ev"] = ((pv.vol == 1) & (pv.dte <= 180)).astype(int)
pv["np_"] = (~pv.promotion_recommendation.astype(bool)).astype(int)
chk("review-level rows", len(pv), 34979, tol=0, fmt="{:.0f}")
for lab, m, want_lo, want_hi, want_or in [
        ("HiPo", pv.hp == 1, .0355, .0566, 1.63),
        ("non-HiPo", pv.hp == 0, .0289, .0329, 1.14)]:
    x = pv[m]
    rr = x.groupby("np_").ev.mean()
    chk(f"{lab}: exit rate | recommended", rr[0], want_lo)
    chk(f"{lab}: exit rate | not recommended", rr[1], want_hi)
    chk(f"{lab}: OR", stats.fisher_exact(pd.crosstab(x.np_, x.ev).values)[0], want_or)
RO = {"Unsatisfactory": 1, "Below Expectations": 2, "Meets Expectations": 3,
      "High Performer": 4, "Outstanding": 5}
pv["rn"] = pv.performance_rating.map(RO)
tp = pv[pv.rn >= 4]
chk("top-rated: OR (should be null)",
    stats.fisher_exact(pd.crosstab(tp.np_, tp.ev).values)[0], 1.08)

print("\nFINDING 5 — department")
hh = d[d.hp == 1]
dep = hh.groupby("department").vol.agg(["mean", "sum", "size"])
for k, v in [("Corporate Operations", .1908), ("Risk & Compliance", .1818),
             ("Retail Banking", .0701)]:
    chk(f"HiPo exit rate, {k}", dep.loc[k, "mean"], v)
chk("chi2 p (department x exit, HiPos)",
    stats.chi2_contingency(pd.crosstab(hh.department, hh.vol))[1], .0014, tol=.10)
med = d.groupby("department").salary.median()
chk("min departmental median salary ($k)", med.min()/1e3, 121.5, tol=.01, fmt="{:.1f}")
chk("max departmental median salary ($k)", med.max()/1e3, 125.8, tol=.01, fmt="{:.1f}")

print("\nFINDING 6 — manager dispersion")
mg = d.groupby("manager_id").agg(span=("employee_id", "size"), v=("vol", "sum"))
big = mg[mg.span >= 5]
pb = d.vol.mean()
chk("teams with span>=5", len(big), 745, tol=0, fmt="{:.0f}")
chk("dispersion ratio", big.v.var() / (big.span*pb*(1-pb)).mean(), .79, tol=.03)

print("\nFINDING 7 — pay")
chk("HiPo leavers compa", d.loc[(d.hp == 1) & (d.vol == 1), "compa_ratio"].mean(), .884, tol=.005)
chk("HiPo stayers compa", d.loc[(d.hp == 1) & (d.vol == 0), "compa_ratio"].mean(), .879, tol=.005)
lv = d[d.vol == 1]
chk("regrettable leavers compa", lv.loc[lv.reg == 1, "compa_ratio"].mean(), .917, tol=.005)
chk("other leavers compa", lv.loc[lv.reg == 0, "compa_ratio"].mean(), .947, tol=.005)

print("\nDISCARDS")
mgr_left = d.set_index("employee_id").vol.rename("x")
dep_mgr = d.merge(d.set_index("employee_id")["exit_type"].notna().rename("md"),
                  left_on="manager_id", right_index=True, how="left")
dep_mgr["md"] = dep_mgr["md"].fillna(False).astype(int)
cas = dep_mgr[dep_mgr.md == 1]
chk("employees with a departed manager", len(cas), 112, tol=0, fmt="{:.0f}")
chk("their voluntary exit rate", cas.vol.mean(), .75, tol=.02)
spans = d.groupby("manager_id").size()
dm = spans.reindex(d.loc[d.exit_type.notna() & d.employee_id.isin(d.manager_id), "employee_id"]).dropna()
chk("departed managers", len(dm), 95, tol=0, fmt="{:.0f}")
chk("max span among departed managers", dm.max(), 3, tol=0, fmt="{:.0f}")
chk("leavers mean n_reviews", perf.merge(d[["employee_id","exit_type"]],on="employee_id")
    .query("exit_type.notna()").groupby("employee_id").size().reindex(
    d.loc[d.exit_type.notna(),"employee_id"]).fillna(0).mean(), 1.68, tol=.03)

print("\nMULTIPLE COMPARISONS")
chk("Bonferroni alpha for ~252 tests", .05/252, .0002, tol=.02, fmt="{:.5f}")

print("\n" + "="*90)
print("ALL CHECKS PASSED" if not fails else f"{len(fails)} MISMATCHES: {fails}")
