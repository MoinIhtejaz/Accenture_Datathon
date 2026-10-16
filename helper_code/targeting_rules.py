"""
targeting_rules.py — "HiPo goes silent" is one candidate trigger. Test it against the obvious
alternatives so the deck can defend the choice rather than assert it.

Each rule is scored on the four things an HR director actually cares about:
  precision  what fraction of the people we call were genuinely about to resign
  recall     what fraction of the resignations we would have touched at all
  caseload   how many conversations per year this creates
  break-even what share of the flagged resignations we need to prevent to pay for it
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eddited_csv"
d = pd.read_csv(OUT / "master_plus.csv", low_memory=False)
d["exit_dt"] = pd.to_datetime(d["exit_dt"])
eng = pd.read_csv(ROOT / "original_csv" / "engagement.csv", parse_dates=["survey_date"])
perf = pd.read_csv(ROOT / "original_csv" / "performance.csv", parse_dates=["review_date"])

REPL, BACKFILL, COST_1TO1, YEARS = 1.5, 0.85, 500, 2.0

wave_date = eng.groupby("wave_number").survey_date.median()
nxt = {1: wave_date[2], 2: wave_date[3], 3: wave_date[4], 4: wave_date[5],
       5: pd.Timestamp("2025-12-31")}

rs = eng.merge(d[["employee_id", "exit_dt", "voluntary", "regrettable", "hipo",
                  "compa_ratio", "salary"]], on="employee_id", how="left")
rs = rs[rs.exit_dt.isna() | (rs.exit_dt > rs.survey_date)].copy()
rs["boundary"] = rs.wave_number.map(nxt)
rs["silent"] = (~rs.response_flag.astype(bool)).astype(int)
rs["quit"] = ((rs.voluntary == 1) & (rs.exit_dt <= rs.boundary)).astype(int)
rs["reg_quit"] = ((rs.regrettable == 1) & (rs.exit_dt <= rs.boundary)).astype(int)

# was the person silent in the PREVIOUS wave too?
rs = rs.sort_values(["employee_id", "wave_number"])
rs["silent_prev"] = rs.groupby("employee_id")["silent"].shift(1)
rs["silent_twice"] = ((rs.silent == 1) & (rs.silent_prev == 1)).astype(int)

# most recent promotion recommendation strictly before this wave
pm = perf.merge(rs[["employee_id", "survey_date"]].drop_duplicates(),
                on="employee_id", how="inner")
pm = pm[pm.review_date < pm.survey_date]
last_rec = (pm.sort_values("review_date")
              .groupby(["employee_id", "survey_date"])["promotion_recommendation"].last()
              .rename("last_rec").reset_index())
rs = rs.merge(last_rec, on=["employee_id", "survey_date"], how="left")
rs["passed_over"] = (rs.last_rec == False).astype(int)
rs["underpaid"] = (rs.compa_ratio < 0.90).astype(int)

avg_leaver_sal = d.loc[(d.hipo == 1) & (d.voluntary == 1), "salary"].mean()
cost_per_exit = avg_leaver_sal * REPL * BACKFILL
print(f"avg HiPo leaver salary ${avg_leaver_sal:,.0f} -> replacement ${cost_per_exit:,.0f}\n")

RULES = {
    "HiPo + silent": (rs.hipo == 1) & (rs.silent == 1),
    "HiPo + silent + underpaid": (rs.hipo == 1) & (rs.silent == 1) & (rs.underpaid == 1),
    "HiPo + silent two waves running": (rs.hipo == 1) & (rs.silent_twice == 1),
    "HiPo + silent + passed over": (rs.hipo == 1) & (rs.silent == 1) & (rs.passed_over == 1),
    "HiPo, all of them (no trigger)": (rs.hipo == 1),
    "Anyone silent (drop HiPo filter)": (rs.silent == 1),
    "Anyone silent two waves running": (rs.silent_twice == 1),
}

rows = []
tot_all = rs.quit.sum()
tot_hipo = rs.loc[rs.hipo == 1, "quit"].sum()
for name, mask in RULES.items():
    f = rs[mask]
    if len(f) == 0:
        continue
    denom = tot_hipo if name.startswith("HiPo") else tot_all
    prec = f.quit.mean()
    n_yr, exits_yr = len(f) / YEARS, f.quit.sum() / YEARS
    be = (n_yr * COST_1TO1) / (exits_yr * cost_per_exit) if exits_yr else np.nan
    ct = pd.crosstab(mask, rs.quit)
    o, p = stats.fisher_exact(ct.values) if ct.shape == (2, 2) else (np.nan, np.nan)
    rows.append(dict(rule=name, flagged=len(f), per_year=n_yr, precision=prec,
                     lift=prec / rs.quit.mean(), recall=f.quit.sum() / denom,
                     reg_caught=int(f.reg_quit.sum()), exits_yr=exits_yr,
                     cost_yr=n_yr * COST_1TO1, breakeven=be, OR=o, p=p,
                     nnc=1 / prec if prec else np.nan))

R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print("=" * 130)
print("CANDIDATE TRIGGER RULES   (recall measured against the matching population: "
      "HiPo rules vs HiPo resignations, open rules vs all)")
print("=" * 130)
print(R.assign(
    precision=lambda x: (x.precision * 100).round(2).astype(str) + "%",
    recall=lambda x: (x.recall * 100).round(1).astype(str) + "%",
    lift=lambda x: x.lift.round(2),
    breakeven=lambda x: (x.breakeven * 100).round(1).astype(str) + "%",
    per_year=lambda x: x.per_year.round(0).astype(int),
    exits_yr=lambda x: x.exits_yr.round(1),
    cost_yr=lambda x: "$" + (x.cost_yr / 1000).round(0).astype(int).astype(str) + "k",
    nnc=lambda x: x.nnc.round(0).astype(int),
    OR=lambda x: x.OR.round(2), p=lambda x: x.p.map(lambda v: f"{v:.2g}"),
)[["rule", "flagged", "per_year", "precision", "lift", "recall", "nnc",
   "exits_yr", "cost_yr", "breakeven", "OR", "p"]].to_string(index=False))

print("""
READ

  1. Repeated silence beats single silence, by a lot. Going quiet in two consecutive waves lifts
     the hit rate to 5.8% (3.5x base) against 3.8% for one wave. It also has the lowest
     break-even of any rule at 5.2%. Silence once can be a holiday. Silence twice is a pattern.

  2. Adding the pay filter makes the rule WORSE, not better. "HiPo + silent + underpaid" drops
     precision to 2.12% and the association stops being significant (p = 0.39). This is the
     clearest possible confirmation that compa-ratio belongs nowhere near the trigger. It tells
     you how much a loss will hurt, not who is about to go.

  3. Adding "passed over for promotion" holds precision roughly steady (4.06%) while cutting the
     caseload by a third. Cheap refinement, keep it as a tie-breaker.

  4. Coverage versus focus. The HiPo rules touch 29% of HiPo resignations. Dropping the HiPo
     filter reaches 34% of ALL resignations for about 5x the cost. That is the answer when the
     CHRO asks what a bigger budget buys.

  The honest ceiling: precision stays in single digits because resignation is rare. No rule hands
  HR a list where most people are about to quit. The case rests on a 90-minute conversation being
  cheap and a HiPo replacement costing $165k.
""")
R.to_csv(OUT / "targeting_rules.csv", index=False)
print("wrote eddited_csv/targeting_rules.csv")
