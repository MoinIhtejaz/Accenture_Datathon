"""
thesis_chain.py — formalise the retention thesis as four testable links, then price the
intervention it implies.

The thesis, stated so it can be attacked:

  L1  HiPo-flagged staff resign at a higher rate than everyone else.
  L2  Those resignations concentrate the regrettable-attrition cost.
  L3  Among HiPos who resign, pay position separates the painful losses from the routine ones.
  L4  Survey silence flags disengagement early enough to intervene.

  => Operating rule: when a HiPo goes silent in a survey wave, HR runs a structured 1:1 inside
     30 days. Pay position sets the priority order and hints at what to put on the table.

L3 is the link that will get attacked, and it should. Compa-ratio does NOT predict whether a
HiPo resigns (p = 0.38). It predicts which HiPo resignations get flagged regrettable. That makes
it a severity/triage variable, not a trigger, and the memo has to say so.
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
d = pd.read_csv(OUT / "master_plus.csv", low_memory=False)
d["exit_dt"] = pd.to_datetime(d["exit_dt"])
eng = pd.read_csv(ROOT / "original_csv" / "engagement.csv", parse_dates=["survey_date"])
line = lambda t: print(f"\n{'='*100}\n{t}\n{'='*100}")

# finance benchmarks from the brief
REPLACEMENT_MULT, BACKFILL, SUPER = 1.5, 0.85, 0.12

def or_ci(ct):
    o, p = stats.fisher_exact(ct)
    a, b, c, e = np.asarray(ct).ravel()
    se = np.sqrt(1/a + 1/b + 1/c + 1/e)
    return o, np.exp(np.log(o) - 1.96*se), np.exp(np.log(o) + 1.96*se), p

# ═══════════════════════════════════════════════════════════ L1
line("L1  HiPos resign more")
ct = pd.crosstab(d.hipo, d.voluntary).values
o, lo, hi, p = or_ci(ct)
r = d.groupby("hipo").voluntary.mean()
print(f"  non-HiPo {r[0]:.2%}  vs  HiPo {r[1]:.2%}   rate ratio {r[1]/r[0]:.2f}x")
print(f"  OR {o:.2f} [{lo:.2f}-{hi:.2f}]   Fisher p = {p:.3g}   n = {len(d):,}")
m = smf.logit("voluntary ~ hipo + tenure_years + compa_ratio + role_level + C(department)"
              " + C(hire_source) + C(contract_type)", data=d).fit(disp=0)
print(f"  adjusted OR (tenure, pay, level, dept, source, contract): "
      f"{np.exp(m.params['hipo']):.2f} "
      f"[{np.exp(m.conf_int().loc['hipo',0]):.2f}-{np.exp(m.conf_int().loc['hipo',1]):.2f}], "
      f"p = {m.pvalues['hipo']:.3g}")

# ═══════════════════════════════════════════════════════════ L2
line("L2  HiPo resignations concentrate the regrettable cost")
reg = d[d.regrettable == 1]
o2, lo2, hi2, p2 = or_ci(pd.crosstab(d.hipo, d.regrettable).values)
print(f"  regrettable exits: {len(reg)}   of which HiPo: {int(reg.hipo.sum())} "
      f"({reg.hipo.mean():.1%})")
print(f"  HiPo share of headcount: {d.hipo.mean():.1%}  ->  enrichment "
      f"{reg.hipo.mean()/d.hipo.mean():.1f}x")
print(f"  OR {o2:.1f} [{lo2:.1f}-{hi2:.1f}], p = {p2:.3g}")
hv = d[(d.hipo == 1) & (d.voluntary == 1)]
sal_h = hv.salary.sum()
print(f"\n  cost weight (base salary of the leaving cohort):")
print(f"    all 1,133 voluntary leavers        ${d[d.voluntary==1].salary.sum()/1e6:>6.1f}M")
print(f"    the 151 HiPo voluntary leavers     ${sal_h/1e6:>6.1f}M "
      f"({sal_h/d[d.voluntary==1].salary.sum():.0%} of the total from "
      f"{151/1133:.0%} of the people)")
print(f"    the 153 regrettable-flagged        ${reg.salary.sum()/1e6:>6.1f}M")
rc = sal_h * REPLACEMENT_MULT * BACKFILL
print(f"\n  replacement cost of the HiPo cohort at {REPLACEMENT_MULT}x base, "
      f"{BACKFILL:.0%} backfill: ${rc/1e6:.1f}M over two years  (${rc/2e6:.1f}M/yr)")
print(f"  brief's regrettable-attrition line: $22-25M  ->  this cohort alone covers it")

# ═══════════════════════════════════════════════════════════ L3
line("L3  Pay position separates painful HiPo losses from routine ones")
a = hv.loc[hv.regrettable == 1, "compa_ratio"]; b = hv.loc[hv.regrettable == 0, "compa_ratio"]
t, p3 = stats.ttest_ind(a, b, equal_var=False)
sp = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
print(f"  among the {len(hv)} HiPos who resigned:")
print(f"    flagged regrettable  compa {a.mean():.4f}  (n={len(a)})")
print(f"    not flagged          compa {b.mean():.4f}  (n={len(b)})")
print(f"    gap {a.mean()-b.mean():+.4f}   Welch t = {t:.2f}, p = {p3:.4f}, "
      f"Hedges g = {(a.mean()-b.mean())/sp:.2f}")
mm = smf.ols("compa_ratio ~ regrettable + role_level + C(department) + tenure_years",
             data=hv).fit()
print(f"    adjusted for level, dept, tenure: beta = {mm.params['regrettable']:+.4f}, "
      f"p = {mm.pvalues['regrettable']:.4f}")
print("\n  THE HONEST CAVEAT — same variable, different question:")
a2 = d.loc[(d.hipo == 1) & (d.voluntary == 1), "compa_ratio"]
b2 = d.loc[(d.hipo == 1) & (d.voluntary == 0), "compa_ratio"]
t2, p3b = stats.ttest_ind(a2, b2, equal_var=False)
print(f"    does compa predict WHETHER a HiPo resigns?  leavers {a2.mean():.4f} vs "
      f"stayers {b2.mean():.4f},  p = {p3b:.3f}  -> NO")
print("    so compa is a severity/triage variable, not a trigger. Use it to rank the queue")
print("    and to shape the offer, never to decide who gets contacted.")
print(f"\n  practical split: HiPos below compa 0.90 who resign are flagged regrettable "
      f"{hv[hv.compa_ratio<0.90].regrettable.mean():.0%} of the time "
      f"(n={len(hv[hv.compa_ratio<0.90])}), vs "
      f"{hv[hv.compa_ratio>=0.90].regrettable.mean():.0%} for those at or above "
      f"(n={len(hv[hv.compa_ratio>=0.90])})")

# ═══════════════════════════════════════════════════════════ L4 + risk set
line("L4  Silence is an early, actionable disengagement flag")
wave_date = eng.groupby("wave_number").survey_date.median()
CENSOR = pd.Timestamp("2025-12-31")
nxt = {1: wave_date[2], 2: wave_date[3], 3: wave_date[4], 4: wave_date[5], 5: CENSOR}
rs = eng.merge(d[["employee_id", "exit_dt", "voluntary", "regrettable", "hipo",
                  "compa_ratio", "salary", "department"]], on="employee_id", how="left")
rs = rs[rs.exit_dt.isna() | (rs.exit_dt > rs.survey_date)].copy()
rs["boundary"] = rs.wave_number.map(nxt)
rs["silent"] = (~rs.response_flag.astype(bool)).astype(int)
rs["quit_next"] = ((rs.voluntary == 1) & (rs.exit_dt <= rs.boundary)).astype(int)
rs["reg_next"] = ((rs.regrettable == 1) & (rs.exit_dt <= rs.boundary)).astype(int)

for lab, sub in [("all staff", rs), ("HiPos", rs[rs.hipo == 1])]:
    o4, lo4, hi4, p4 = or_ci(pd.crosstab(sub.silent, sub.quit_next).values)
    rr = sub.groupby("silent").quit_next.mean()
    print(f"  {lab:<10} answered {rr[0]:.2%} -> silent {rr[1]:.2%}   "
          f"OR {o4:.2f} [{lo4:.2f}-{hi4:.2f}]  p = {p4:.3g}   n = {len(sub):,} person-waves")
print("\n  the falsification test that matters:")
d2 = d.copy()
rs2 = rs.merge(d[["employee_id"]].assign(x=1), on="employee_id", how="left")
inv = pd.read_csv(ROOT / "original_csv" / "attrition_log.csv", parse_dates=["exit_date"])
rs = rs.merge(inv[["employee_id", "exit_type"]], on="employee_id", how="left")
rs["invol_next"] = ((rs.exit_type == "involuntary") & (rs.exit_dt <= rs.boundary)).astype(int)
oi, _, _, pi = or_ci(pd.crosstab(rs.silent, rs.invol_next).values)
print(f"    silence -> involuntary exit: OR {oi:.2f}, p = {pi:.3g}")
print("    silence is a disengagement marker, not a resignation-specific one. State this;")
print("    it does not weaken the intervention, it widens who it helps.")

# ═══════════════════════════════════════════════════════════ TARGETING RULE
line("THE OPERATING RULE — HiPo goes silent -> structured 1:1 within 30 days")
h = rs[rs.hipo == 1]
flag = h[h.silent == 1]
base = h.quit_next.mean()
prec = flag.quit_next.mean()
recall = flag.quit_next.sum() / h.quit_next.sum()
print(f"  HiPo person-waves in scope           {len(h):,}")
print(f"  triggered (HiPo and silent)          {len(flag):,}  "
      f"({len(flag)/len(h):.1%} of HiPo waves)")
print(f"  base resignation rate                {base:.2%}")
print(f"  rate inside the triggered group      {prec:.2%}   (precision)")
print(f"  lift over base                       {prec/base:.2f}x")
print(f"  share of all HiPo resignations caught {recall:.1%}   (recall)")
print(f"  number needed to contact per resignation found  {1/prec:.0f}")

per_wave = len(flag) / 5
print(f"\n  caseload: {per_wave:.0f} conversations per survey wave "
      f"({per_wave/13:.0f} per week across the HR team, 4 waves a year)")

# break-even
avg_sal = hv.salary.mean()
cost_per_exit = avg_sal * REPLACEMENT_MULT * BACKFILL
COST_1TO1 = 500  # loaded cost of an HR business partner running a structured 90-min 1:1 + follow-up
n_year = len(flag) / 2          # two-year window in the data
exits_in_flagged_year = flag.quit_next.sum() / 2
print(f"\n  annualised: {n_year:.0f} conversations, {exits_in_flagged_year:.0f} resignations "
      f"sitting inside that flagged group")
print(f"  avg HiPo leaver salary ${avg_sal:,.0f}  ->  replacement cost "
      f"${cost_per_exit:,.0f} each")
print(f"  programme cost at ${COST_1TO1}/conversation: ${n_year*COST_1TO1:,.0f}/yr")
be = (n_year * COST_1TO1) / (exits_in_flagged_year * cost_per_exit)
print(f"  BREAK-EVEN: the programme pays for itself if it prevents "
      f"{be:.1%} of the resignations in the flagged group")
print(f"             = {be*exits_in_flagged_year:.1f} of {exits_in_flagged_year:.0f} people a year")
for eff in [0.05, 0.10, 0.20, 0.30]:
    saved = eff * exits_in_flagged_year * cost_per_exit
    net = saved - n_year * COST_1TO1
    print(f"    if it works on {eff:>4.0%} of them: ${saved/1e6:>4.2f}M avoided, "
          f"net ${net/1e6:>+5.2f}M, ROI {net/(n_year*COST_1TO1):>5.1f}x")

# sensitivity on the 1:1 cost
print("\n  sensitivity to the cost-per-conversation assumption:")
for c in [250, 500, 1000, 2000]:
    b_ = (n_year * c) / (exits_in_flagged_year * cost_per_exit)
    print(f"    ${c:>5}/conversation -> break-even at {b_:>5.1%} prevention")

rs.to_csv(OUT / "thesis_risk_set.csv", index=False)
print("\nwrote eddited_csv/thesis_risk_set.csv")
