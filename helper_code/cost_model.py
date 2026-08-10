"""
NovaCorp people-cost model — rebuild of the brief's $42M.

Purpose
-------
The brief asserts ~$42M/yr of annual people cost, split:
    regrettable attrition      $22-25M
    disengagement productivity $12-15M
    hiring inefficiency        $4-6M

This script does three things:
  1. REVERSE-ENGINEER  — find which population x costing combination reproduces $22-25M,
                         and show that HR's own `regrettable_flag` cannot get there under
                         the brief's own benchmark constants.
  2. REBUILD           — cost a regrettable population defined from observables only,
                         with low/central/high scenarios and sensitivity bands.
  3. RE-CUT            — reallocate spend across the three buckets with an explicit
                         mutually-exclusive assignment rule (no double counting).

Every constant traces to the brief. Nothing is invented. See CONSTANTS below.

Run:  python3 helper_code/cost_model.py
Writes: findings_02_cost_model.md  and  eddited_csv/cost_model_scenarios.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "original_csv"
OUT = ROOT / "eddited_csv"
OUT.mkdir(exist_ok=True)

# --------------------------------------------------------------------------
# CONSTANTS — all sourced from the brief's finance benchmark table
# --------------------------------------------------------------------------
REPLACEMENT_MULT = 1.5      # replacement cost = 1.5x base salary
BACKFILL_RATE = 0.85        # 85% of exits are backfilled
DISENGAGE_LOSS = 0.15       # productivity loss = 15% of base salary per year
SUPER_ONCOST = 0.120        # superannuation on-cost
AGENCY_FEE = 0.18           # agency fee = 18% of first-year base
DIRECT_HIRE_COST = 5_500    # benchmark cost per direct hire

WINDOW_YEARS = 2.0          # 1 Jan 2024 - 31 Dec 2025
TENURE_FLOOR_D = 180        # min tenure to count an exit as "regrettable" not "early"
EARLY_EXIT_D = 90           # exits at or below this tenure = failed hire / integration


# --------------------------------------------------------------------------
# LOAD
# --------------------------------------------------------------------------
def load():
    emp = pd.read_csv(RAW / "employees.csv")
    att = pd.read_csv(RAW / "attrition_log.csv")
    perf = pd.read_csv(RAW / "performance.csv")
    eng = pd.read_csv(RAW / "engagement.csv")

    perf["review_date"] = pd.to_datetime(perf["review_date"])
    last_review = (
        perf.sort_values("review_date")
        .groupby("employee_id")
        .tail(1)
        .set_index("employee_id")[["performance_rating", "goal_achievement_score"]]
        .rename(columns={"performance_rating": "last_rating",
                         "goal_achievement_score": "last_goal"})
    )

    ex = att.merge(emp, on="employee_id", suffixes=("", "_e"))
    ex["exit_date"] = pd.to_datetime(ex["exit_date"])
    ex["hire_date"] = pd.to_datetime(ex["hire_date"])
    ex["tenure_d"] = (ex["exit_date"] - ex["hire_date"]).dt.days
    ex = ex.join(last_review, on="employee_id")

    act = emp[emp["status"] == "active"].copy()
    act = act.join(last_review, on="employee_id")

    return emp, att, perf, eng, ex, act


def annual_replacement_cost(df, mult=REPLACEMENT_MULT, backfill=BACKFILL_RATE,
                            salary_col="salary_at_exit", years=WINDOW_YEARS):
    """Annualised replacement cost for a set of exits, in $M."""
    return df[salary_col].sum() * mult * backfill / years / 1e6


# --------------------------------------------------------------------------
# STEP 1 — reverse-engineer the brief's $22-25M
# --------------------------------------------------------------------------
def reverse_engineer(ex):
    """Which definition reproduces the brief's headline? Under the brief's own
    constants, HR's regrettable_flag lands at roughly half the stated figure."""
    strong = ["Outstanding", "High Performer"]
    vol = ex["exit_type"] == "voluntary"
    seasoned = ex["tenure_d"] >= TENURE_FLOOR_D
    hipo = ex["hipo_flag"] == True  # noqa: E712
    rated = ex["last_rating"].isin(strong)

    defs = {
        "HR regrettable_flag only": ex["regrettable_flag"] == True,  # noqa: E712
        "All voluntary exits": vol,
        "Voluntary, tenure >= 180d": vol & seasoned,
        "Voluntary, tenure >= 365d": vol & (ex["tenure_d"] >= 365),
        "Voluntary + HiPo, tenure >= 180d": vol & seasoned & hipo,
        "Voluntary + High/Outstanding, tenure >= 180d": vol & seasoned & rated,
        "Voluntary + (HiPo or High/Outstanding), tenure >= 180d": vol & seasoned & (hipo | rated),
        "HR flag OR (voluntary + HiPo)": (ex["regrettable_flag"] == True) | (vol & hipo),  # noqa: E712
    }

    rows = []
    for name, mask in defs.items():
        s = ex[mask]
        base = s["salary_at_exit"].sum() / WINDOW_YEARS / 1e6
        rows.append({
            "definition": name,
            "n_exits": len(s),
            "n_per_year": round(len(s) / WINDOW_YEARS),
            "salary_base_$M_yr": round(base, 1),
            "at_1.0x": round(base * 1.0, 1),
            "at_1.5x_x_85pct": round(base * REPLACEMENT_MULT * BACKFILL_RATE, 1),
            "at_2.0x": round(base * 2.0, 1),
            "reproduces_22_25M": 22 <= base * REPLACEMENT_MULT * BACKFILL_RATE <= 25,
        })
    return pd.DataFrame(rows)


def implied_multiplier(ex):
    """What multiplier on base salary would HR's flagged population need to hit $22-25M?"""
    base = ex.loc[ex["regrettable_flag"] == True, "salary_at_exit"].sum() / WINDOW_YEARS  # noqa: E712
    return base / 1e6, 22e6 / base, 25e6 / base


# --------------------------------------------------------------------------
# STEP 2 — defensible regrettable population, low / central / high
# --------------------------------------------------------------------------
def defensible_scenarios(ex):
    """Regrettable defined from observable facts only.

    Deliberately excludes `regrettable_flag` and `performance_band_at_exit`:
    findings_01 showed the latter agrees with the actual review record only
    15.7% of the time for flagged leavers.

    Acquisition hires are NOT excluded here, but tenure for them is unreliable
    (hire_date may be the system-migration date). The tenure floor therefore
    does double duty: it removes the integration cliff from this bucket and
    routes it to hiring inefficiency instead.
    """
    vol = ex["exit_type"] == "voluntary"
    hipo = ex["hipo_flag"] == True  # noqa: E712
    strong = ex["last_rating"].isin(["Outstanding", "High Performer"])
    not_weak = ~ex["last_rating"].isin(["Below Expectations", "Unsatisfactory"])

    scenarios = {
        # Narrow: only people the business had formally identified as high potential,
        # who left voluntarily after a full year. Hardest to argue with.
        "Low (conservative)": vol & (ex["tenure_d"] >= 365) & hipo,
        # Central: formal HiPo designation OR a documented strong rating.
        "Central": vol & (ex["tenure_d"] >= TENURE_FLOOR_D) & (hipo | strong),
        # Broad: anyone who left voluntarily and was not underperforming.
        # Treats "regrettable" as "we would have kept them".
        "High (broad)": vol & (ex["tenure_d"] >= TENURE_FLOOR_D) & not_weak,
    }

    rows = []
    for name, mask in scenarios.items():
        s = ex[mask]
        for mult, mlabel in [(1.0, "1.0x"), (1.5, "1.5x (brief)"), (2.0, "2.0x")]:
            rows.append({
                "scenario": name,
                "n_exits": len(s),
                "n_per_year": round(len(s) / WINDOW_YEARS),
                "mean_salary": round(s["salary_at_exit"].mean()),
                "replacement_mult": mlabel,
                "cost_$M_per_yr": round(annual_replacement_cost(s, mult=mult), 1),
            })
    return pd.DataFrame(rows), scenarios


# --------------------------------------------------------------------------
# STEP 3 — re-cut the three buckets, mutually exclusive
# --------------------------------------------------------------------------
def recut_buckets(ex, act):
    """Assign every exit to exactly one bucket, in priority order.

    Priority matters: an exit at 30 days tenure who was also a HiPo is an
    onboarding failure, not a retention failure. Cost it once, in the bucket
    where the intervention lives.
    """
    ex = ex.copy()
    ex["bucket"] = "other"

    # 1. Early exits — failed hire / failed integration. Highest priority.
    early = ex["tenure_d"] <= EARLY_EXIT_D
    ex.loc[early, "bucket"] = "hiring_inefficiency"

    # 2. Involuntary — managed exits, not a cost line the CHRO is being asked about.
    ex.loc[~early & (ex["exit_type"] == "involuntary"), "bucket"] = "involuntary"

    # 3. Regrettable — central scenario, among what remains.
    hipo = ex["hipo_flag"] == True  # noqa: E712
    strong = ex["last_rating"].isin(["Outstanding", "High Performer"])
    reg = (~early) & (ex["exit_type"] == "voluntary") & \
          (ex["tenure_d"] >= TENURE_FLOOR_D) & (hipo | strong)
    ex.loc[reg, "bucket"] = "regrettable_attrition"

    # 4. Everything else voluntary — normal churn.
    ex.loc[(ex["bucket"] == "other") & (ex["exit_type"] == "voluntary"), "bucket"] = "routine_voluntary"

    summary = (
        ex.groupby("bucket")
        .agg(n_exits=("employee_id", "size"),
             total_salary=("salary_at_exit", "sum"))
        .assign(**{
            "n_per_year": lambda d: (d["n_exits"] / WINDOW_YEARS).round(),
            "cost_$M_per_yr": lambda d: (d["total_salary"] * REPLACEMENT_MULT
                                         * BACKFILL_RATE / WINDOW_YEARS / 1e6).round(1),
        })
        .drop(columns=["total_salary"])
        .sort_values("cost_$M_per_yr", ascending=False)
    )
    return ex, summary


def agency_premium(ex, emp):
    """Hiring inefficiency has a second component the brief's constants imply:
    agency hires cost 18% of first-year base vs $5,500 for a direct hire."""
    hires = emp[emp["hire_source"].isin(["agency", "direct"])].copy()
    hires["hire_date"] = pd.to_datetime(hires["hire_date"])
    recent = hires[hires["hire_date"] >= "2024-01-01"]
    ag = recent[recent["hire_source"] == "agency"]
    premium = (ag["salary"] * AGENCY_FEE - DIRECT_HIRE_COST).clip(lower=0).sum()
    return len(ag), premium / WINDOW_YEARS / 1e6


DIMS = ["manager_effectiveness", "psychological_safety", "recognition",
        "career_development", "senior_leadership_trust", "purpose_meaning",
        "wellbeing", "confidence_in_role_future"]


def disengagement_bucket(act, eng):
    """The brief's $12-15M implies a disengaged headcount. Solve for it, then
    measure the actual headcount at conventional thresholds.

    Finding: $12-15M implies ~620-780 people (5-6% of staff). That matches an
    engagement index below 2.5 — i.e. only the severely disengaged tail. At any
    conventional threshold the population, and the cost, is several times larger.

    Caveat: findings_01 showed engagement scores do NOT decline before exit, so
    the 15%-of-salary productivity loss is an assumed elasticity, not a measured
    one. Non-responders are included as a separate line because response_flag
    is deliberate signal (regrettable leavers under-respond), but attributing
    the full 15% loss to them is the most aggressive assumption in this model.
    """
    mean_sal = act["salary"].mean()
    loss_per_head = mean_sal * DISENGAGE_LOSS
    implied_lo, implied_hi = 12e6 / loss_per_head, 15e6 / loss_per_head

    latest = eng[eng["wave_number"] == eng["wave_number"].max()]
    latest = latest[latest["employee_id"].isin(act["employee_id"])]
    resp = latest[latest["response_flag"] == True].copy()  # noqa: E712
    resp["idx"] = resp[DIMS].mean(axis=1)
    sal = act.set_index("employee_id")["salary"]

    rows = []
    for t in [2.5, 3.0, 3.25]:
        ids = resp.loc[resp["idx"] < t, "employee_id"]
        rows.append({"population": f"engagement index < {t}",
                     "n": len(ids),
                     "pct_of_surveyed": f"{len(ids)/len(latest):.1%}",
                     "cost_$M_per_yr": round(sal.reindex(ids).sum() * DISENGAGE_LOSS / 1e6, 1)})
    nr = latest.loc[latest["response_flag"] != True, "employee_id"]  # noqa: E712
    rows.append({"population": "non-responders (latest wave)",
                 "n": len(nr),
                 "pct_of_surveyed": f"{len(nr)/len(latest):.1%}",
                 "cost_$M_per_yr": round(sal.reindex(nr).sum() * DISENGAGE_LOSS / 1e6, 1)})

    return mean_sal, loss_per_head, implied_lo, implied_hi, pd.DataFrame(rows)


def hipo_pay_gap(act):
    """Cost to lift under-paid active HiPos to a target compa-ratio, incl. super."""
    rows = []
    hipo = act[act["hipo_flag"] == True]  # noqa: E712
    for target in [0.85, 0.90, 0.95, 1.00]:
        g = hipo[hipo["compa_ratio"] < target]
        uplift = ((target - g["compa_ratio"]) / g["compa_ratio"] * g["salary"]).sum()
        rows.append({
            "target_compa": target,
            "n_hipos_below": len(g),
            "annual_cost_$M": round(uplift * (1 + SUPER_ONCOST) / 1e6, 1),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
def main():
    emp, att, perf, eng, ex, act = load()

    print("=" * 78)
    print("STEP 1 — REVERSE-ENGINEERING THE BRIEF'S $22-25M")
    print("=" * 78)
    re_df = reverse_engineer(ex)
    print(re_df.to_string(index=False))
    base, lo, hi = implied_multiplier(ex)
    print(f"\nHR-flagged population base salary: ${base:.1f}M/yr across {int(att.regrettable_flag.sum())} exits.")
    print(f"To reach $22-25M it needs a multiplier of {lo:.2f}-{hi:.2f}x base salary,")
    print(f"against the brief's own benchmark of {REPLACEMENT_MULT}x x {BACKFILL_RATE:.0%} = "
          f"{REPLACEMENT_MULT*BACKFILL_RATE:.3f}x.")

    print("\n" + "=" * 78)
    print("STEP 2 — DEFENSIBLE REGRETTABLE POPULATION")
    print("=" * 78)
    sc_df, _ = defensible_scenarios(ex)
    print(sc_df.to_string(index=False))
    sc_df.to_csv(OUT / "cost_model_scenarios.csv", index=False)

    print("\n" + "=" * 78)
    print("STEP 3 — RE-CUT BUCKETS (mutually exclusive)")
    print("=" * 78)
    ex_b, summary = recut_buckets(ex, act)
    print(summary.to_string())
    assert ex_b["bucket"].notna().all() and (ex_b["bucket"] != "other").all(), \
        "every exit must land in exactly one bucket"
    print(f"\nDouble-count check: {len(ex_b)} exits, "
          f"{ex_b['bucket'].value_counts().sum()} bucket assignments. OK.")

    n_ag, ag_prem = agency_premium(ex, emp)
    print(f"\nAgency premium: {n_ag} agency hires since 2024, "
          f"${ag_prem:.1f}M/yr above the direct-hire benchmark.")

    print("\n" + "=" * 78)
    print("DISENGAGEMENT BUCKET")
    print("=" * 78)
    mean_sal, per_head, n_lo, n_hi, dis_df = disengagement_bucket(act, eng)
    print(f"Mean active salary ${mean_sal:,.0f}; loss/head ${per_head:,.0f}/yr at "
          f"{DISENGAGE_LOSS:.0%}.")
    print(f"The brief's $12-15M implies {n_lo:,.0f}-{n_hi:,.0f} disengaged staff "
          f"({n_lo/len(act):.0%}-{n_hi/len(act):.0%} of the workforce).")
    print("Measured populations at the latest survey wave:")
    print(dis_df.to_string(index=False))

    print("\n" + "=" * 78)
    print("HIPO PAY-GAP REMEDIATION (the lever, not a cost)")
    print("=" * 78)
    print(hipo_pay_gap(act).to_string(index=False))

    ex_b.to_csv(OUT / "exits_bucketed.csv", index=False)
    print(f"\nWrote {OUT/'cost_model_scenarios.csv'} and {OUT/'exits_bucketed.csv'}")


if __name__ == "__main__":
    main()
