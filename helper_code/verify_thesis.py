"""
verify_thesis.py — recompute every number in findings_06 from the four raw CSVs only.
Nothing here reads an intermediate file. If a check fails, the memo is wrong, not the script.
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
RAW = Path(__file__).resolve().parent.parent / "original_csv"
emp = pd.read_csv(RAW / "employees.csv", parse_dates=["hire_date", "exit_date"])
att = pd.read_csv(RAW / "attrition_log.csv", parse_dates=["exit_date"])
eng = pd.read_csv(RAW / "engagement.csv", parse_dates=["survey_date"])
perf = pd.read_csv(RAW / "performance.csv", parse_dates=["review_date"])

fails = []
def chk(label, got, want, tol=.02, fmt="{:.4f}"):
    ok = abs(got - want) <= tol * max(abs(want), 1e-9)
    print(f"  [{'OK ' if ok else 'BAD'}] {label:<58} got {fmt.format(got):>12}  "
          f"memo {fmt.format(want):>12}")
    if not ok:
        fails.append(label)

d = emp.merge(att[["employee_id", "exit_type", "regrettable_flag", "exit_date"]]
              .rename(columns={"exit_date": "xd"}), on="employee_id", how="left")
d["exit_dt"] = d["exit_date"].fillna(d["xd"])
d["vol"] = (d.exit_type == "voluntary").astype(int)
d["reg"] = (d.regrettable_flag == True).astype(int)
d["hp"] = d.hipo_flag.astype(int)
d["tenure_years"] = d.tenure_months / 12
REPL, BACKFILL, COST = 1.5, .85, 500

print("\nL1  HiPos resign more")
chk("HiPo resignation rate", d[d.hp == 1].vol.mean(), .125)
chk("non-HiPo resignation rate", d[d.hp == 0].vol.mean(), .081)
o, p = stats.fisher_exact(pd.crosstab(d.hp, d.vol).values)
chk("odds ratio", o, 1.63)
chk("rate ratio", d[d.hp == 1].vol.mean()/d[d.hp == 0].vol.mean(), 1.55)
chk("p (log10)", np.log10(p), np.log10(5.5e-7), tol=.05)
m = smf.logit("vol ~ hp + tenure_years + compa_ratio + role_level + C(department)"
              " + C(hire_source) + C(contract_type)", data=d).fit(disp=0)
chk("adjusted OR", np.exp(m.params["hp"]), 1.58)
chk("adjusted p (log10)", np.log10(m.pvalues["hp"]), np.log10(5.0e-6), tol=.08)

print("\nL2  the cost concentration")
reg = d[d.reg == 1]
chk("HiPo share of headcount", d.hp.mean(), .090)
chk("HiPo share of regrettable exits", reg.hp.mean(), .497)
chk("enrichment", reg.hp.mean()/d.hp.mean(), 5.5, tol=.03)
o2, p2 = stats.fisher_exact(pd.crosstab(d.hp, d.reg).values)
chk("odds ratio", o2, 10.5)
sal = d.loc[(d.hp == 1) & (d.vol == 1), "salary"].sum()
chk("HiPo leaver base salary ($M)", sal/1e6, 19.6, fmt="{:.2f}")
chk("replacement cost ($M)", sal*REPL*BACKFILL/1e6, 24.9, fmt="{:.2f}")
chk("annualised ($M)", sal*REPL*BACKFILL/2e6, 12.5, fmt="{:.2f}")

print("\nL3  pay as severity, not trigger")
hv = d[(d.hp == 1) & (d.vol == 1)]
a = hv.loc[hv.reg == 1, "compa_ratio"]; b = hv.loc[hv.reg == 0, "compa_ratio"]
chk("regrettable HiPo leaver compa", a.mean(), .868, tol=.004)
chk("routine HiPo leaver compa", b.mean(), .900, tol=.004)
t, p3 = stats.ttest_ind(a, b, equal_var=False)
chk("Welch t", t, -2.99, tol=.03)
chk("p", p3, .003, tol=.15)
sp = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1))/(len(a)+len(b)-2))
chk("Hedges g", (a.mean()-b.mean())/sp, -.49, tol=.05)
chk("flagged rate | compa < 0.90", hv[hv.compa_ratio < .90].reg.mean(), .61, tol=.03)
chk("flagged rate | compa >= 0.90", hv[hv.compa_ratio >= .90].reg.mean(), .39, tol=.05)
a2 = d.loc[(d.hp == 1) & (d.vol == 1), "compa_ratio"]
b2 = d.loc[(d.hp == 1) & (d.vol == 0), "compa_ratio"]
chk("NULL: compa vs resigning, p", stats.ttest_ind(a2, b2, equal_var=False)[1], .38, tol=.10)

print("\nL4  silence, wave-boundary risk set")
wd = eng.groupby("wave_number").survey_date.median()
nxt = {1: wd[2], 2: wd[3], 3: wd[4], 4: wd[5], 5: pd.Timestamp("2025-12-31")}
r = eng.merge(d[["employee_id", "exit_dt", "vol", "hp", "compa_ratio", "salary", "exit_type"]],
              on="employee_id", how="left")
r = r[r.exit_dt.isna() | (r.exit_dt > r.survey_date)].copy()
r["bnd"] = r.wave_number.map(nxt)
r["sil"] = (~r.response_flag.astype(bool)).astype(int)
r["ev"] = ((r.vol == 1) & (r.exit_dt <= r.bnd)).astype(int)
r["inv"] = ((r.exit_type == "involuntary") & (r.exit_dt <= r.bnd)).astype(int)
chk("person-waves", len(r), 55939, tol=0, fmt="{:.0f}")
chk("all staff: rate | answered", r[r.sil == 0].ev.mean(), .0134)
chk("all staff: rate | silent", r[r.sil == 1].ev.mean(), .0307)
chk("all staff OR", stats.fisher_exact(pd.crosstab(r.sil, r.ev).values)[0], 2.33)
h = r[r.hp == 1]
chk("HiPo: rate | answered", h[h.sil == 0].ev.mean(), .0209)
chk("HiPo: rate | silent", h[h.sil == 1].ev.mean(), .0380)
oh, ph = stats.fisher_exact(pd.crosstab(h.sil, h.ev).values)
chk("HiPo OR", oh, 1.85); chk("HiPo p", ph, .005, tol=.15)
oi, pi = stats.fisher_exact(pd.crosstab(r.sil, r.inv).values)
chk("FALSIFICATION: silence -> involuntary OR", oi, 2.18)
print("     per-wave ORs (memo says 1.71 to 2.73, all Bonferroni-significant at 0.01):")
for w in range(1, 6):
    s = r[r.wave_number == w]
    ow, pw = stats.fisher_exact(pd.crosstab(s.sil, s.ev).values)
    flag = "OK " if pw < .01 else "BAD"
    print(f"       [{flag}] wave {w}: OR {ow:.2f}, p = {pw:.2e}")
    if pw >= .01:
        fails.append(f"wave {w} Bonferroni")

print("\nTHE OPERATING RULE")
flag = h[h.sil == 1]
chk("triggered person-waves", len(flag), 894, tol=0, fmt="{:.0f}")
chk("conversations per year", len(flag)/2, 447, tol=.01, fmt="{:.0f}")
chk("hit rate", flag.ev.mean(), .038)
chk("HiPo base rate", h.ev.mean(), .0241)
chk("lift over HiPo base", flag.ev.mean()/h.ev.mean(), 1.58, tol=.03)
chk("lift over company base", flag.ev.mean()/r.ev.mean(), 2.29, tol=.03)
chk("recall of HiPo resignations", flag.ev.sum()/h.ev.sum(), .288, tol=.03)
chk("conversations per resignation found", 1/flag.ev.mean(), 26, tol=.05, fmt="{:.0f}")
avg = hv.salary.mean()
chk("avg HiPo leaver salary ($k)", avg/1e3, 129.6, tol=.01, fmt="{:.1f}")
cpe = avg*REPL*BACKFILL
chk("replacement cost each ($k)", cpe/1e3, 165.2, tol=.01, fmt="{:.1f}")
n_yr, ex_yr = len(flag)/2, flag.ev.sum()/2
chk("resignations inside flagged group, per yr", ex_yr, 17, tol=.05, fmt="{:.0f}")
chk("programme cost ($k/yr)", n_yr*COST/1e3, 223.5, tol=.01, fmt="{:.1f}")
be = (n_yr*COST)/(ex_yr*cpe)
chk("BREAK-EVEN prevention rate", be, .080, tol=.03)
chk("people to retain per year", be*ex_yr, 1.4, tol=.05, fmt="{:.2f}")
print("     scenarios:")
for e, want in [(.05, -.08), (.10, .06), (.20, .34), (.30, .62)]:
    net = (e*ex_yr*cpe - n_yr*COST)/1e6
    chk(f"       net at {e:.0%} prevention ($M)", net, want, tol=.12, fmt="{:+.2f}")
print("     cost sensitivity:")
for c, want in [(250, .040), (500, .080), (1000, .159), (2000, .318)]:
    chk(f"       break-even at ${c}/conversation", (n_yr*c)/(ex_yr*cpe), want, tol=.03)

print("\nTIER 3  silence two waves running")
r = r.sort_values(["employee_id", "wave_number"])
r["prev"] = r.groupby("employee_id")["sil"].shift(1)
r["twice"] = ((r.sil == 1) & (r.prev == 1)).astype(int)
t3 = r[r.twice == 1]
chk("Tier 3 conversations per year", len(t3)/2, 766, tol=.01, fmt="{:.0f}")
chk("Tier 3 hit rate", t3.ev.mean(), .052)
chk("Tier 3 break-even", (len(t3)/2*COST)/((t3.ev.sum()/2)*cpe), .058, tol=.03)
chk("Tier 1 conversations per year", len(r[r.sil == 1])/2, 5126, tol=.01, fmt="{:.0f}")
chk("Tier 1 hit rate", r[r.sil == 1].ev.mean(), .031)

print("\nTHE PAY-FILTER REGRESSION (why compa is excluded from the trigger)")
up = h[(h.sil == 1) & (h.compa_ratio < .90)]
chk("HiPo + silent + underpaid hit rate", up.ev.mean(), .0212)
ct = pd.crosstab((r.hp == 1) & (r.sil == 1) & (r.compa_ratio < .90), r.ev)
chk("its p-value (should be non-significant)",
    stats.fisher_exact(ct.values)[1], .39, tol=.15)

print("\n" + "=" * 92)
print("ALL CHECKS PASSED" if not fails else f"{len(fails)} MISMATCHES:\n  " + "\n  ".join(fails))
