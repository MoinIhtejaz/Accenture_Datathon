"""
Leaver-vs-stayer risk set — the control group findings_01 lacks.

Design
------
Pick a reference date. Take every employee ACTIVE on that date. Build features
using ONLY information observable on or before that date. Outcome = voluntary
exit in the following 12 months.

This removes the two defects in the descriptive work so far:
  - no control group (everything was conditioned on having left)
  - look-ahead bias (using a leaver's final review to explain their exit)

Two reference dates are used so effects can be checked for stability:
  REF_A 2024-10-25  (engagement wave 3)
  REF_B 2025-01-31  (engagement wave 4)

Importantly, `regrettable_flag` and `performance_band_at_exit` are never used
as features or outcomes — findings_01 §3 showed both are retrospective HR
narrative. The outcome here is the observable fact of a voluntary exit.
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "original_csv"
OUT = ROOT / "eddited_csv"
OUT.mkdir(exist_ok=True)

DIMS = ["manager_effectiveness", "psychological_safety", "recognition",
        "career_development", "senior_leadership_trust", "purpose_meaning",
        "wellbeing", "confidence_in_role_future"]

HORIZON_D = 365


def build_risk_set(ref_date: str) -> pd.DataFrame:
    ref = pd.Timestamp(ref_date)

    emp = pd.read_csv(RAW / "employees.csv")
    att = pd.read_csv(RAW / "attrition_log.csv")
    perf = pd.read_csv(RAW / "performance.csv")
    eng = pd.read_csv(RAW / "engagement.csv")

    emp["hire_date"] = pd.to_datetime(emp["hire_date"])
    emp["exit_date"] = pd.to_datetime(emp["exit_date"])
    perf["review_date"] = pd.to_datetime(perf["review_date"])
    eng["survey_date"] = pd.to_datetime(eng["survey_date"])
    att["exit_date"] = pd.to_datetime(att["exit_date"])

    # --- risk set: hired on/before ref, not yet exited on ref -------------
    rs = emp[(emp["hire_date"] <= ref) &
             (emp["exit_date"].isna() | (emp["exit_date"] > ref))].copy()

    # --- outcome: voluntary exit within horizon --------------------------
    vol = att[att["exit_type"] == "voluntary"].set_index("employee_id")["exit_date"]
    rs["vol_exit_date"] = rs["employee_id"].map(vol)
    rs["left"] = ((rs["vol_exit_date"] > ref) &
                  (rs["vol_exit_date"] <= ref + pd.Timedelta(days=HORIZON_D))).fillna(False).astype(int)
    # anyone who exited involuntarily inside the window is censored, not a control
    invol = att[att["exit_type"] == "involuntary"].set_index("employee_id")["exit_date"]
    iv = rs["employee_id"].map(invol)
    censored = ((iv > ref) & (iv <= ref + pd.Timedelta(days=HORIZON_D))).fillna(False)
    rs = rs[~censored].copy()

    rs["tenure_m_at_ref"] = (ref - rs["hire_date"]).dt.days / 30.44

    # --- performance as of ref -------------------------------------------
    ph = perf[perf["review_date"] <= ref].sort_values("review_date")
    last = ph.groupby("employee_id").tail(1).set_index("employee_id")
    rs["last_rating"] = rs["employee_id"].map(last["performance_rating"])
    rs["last_goal"] = rs["employee_id"].map(last["goal_achievement_score"])
    rs["last_promo_rec"] = rs["employee_id"].map(last["promotion_recommendation"])
    rs["n_reviews"] = rs["employee_id"].map(ph.groupby("employee_id").size())

    # career blockage: recommended for promotion more than once and still here.
    # We cannot observe promotions directly (no role_level history), so a
    # REPEAT recommendation is the observable proxy for an unactioned one.
    rec_counts = ph[ph["promotion_recommendation"] == True].groupby("employee_id").size()  # noqa: E712
    rs["n_promo_recs"] = rs["employee_id"].map(rec_counts).fillna(0)
    rs["repeat_promo_rec"] = (rs["n_promo_recs"] >= 2).astype(int)
    rs["ever_promo_rec"] = (rs["n_promo_recs"] >= 1).astype(int)
    # eligible for promotion but never once recommended = the other blockage shape
    rs["eligible_never_rec"] = ((rs["promotion_eligible"] == True) &  # noqa: E712
                               (rs["n_promo_recs"] == 0)).astype(int)

    # performance trajectory (first vs last observed goal score)
    first = ph.groupby("employee_id").head(1).set_index("employee_id")
    rs["goal_delta"] = (rs["employee_id"].map(last["goal_achievement_score"]) -
                        rs["employee_id"].map(first["goal_achievement_score"]))

    # --- engagement as of ref --------------------------------------------
    eh = eng[eng["survey_date"] <= ref].sort_values("survey_date")
    last_wave = eh["wave_number"].max()
    lw = eh[eh["wave_number"] == last_wave].set_index("employee_id")
    rs["surveyed"] = rs["employee_id"].isin(lw.index)
    rs["responded"] = rs["employee_id"].map(lw["response_flag"])
    rs["non_responder"] = (rs["surveyed"] & (rs["responded"] != True)).astype(int)

    for d in DIMS:
        rs[d] = rs["employee_id"].map(lw[d])
    rs["eng_index"] = rs[DIMS].mean(axis=1)

    # within-person change in engagement across all waves up to ref
    resp = eh[eh["response_flag"] == True]  # noqa: E712
    f = resp.groupby("employee_id").head(1).set_index("employee_id")
    l = resp.groupby("employee_id").tail(1).set_index("employee_id")
    for d in ["manager_effectiveness", "career_development", "recognition"]:
        rs[f"d_{d}"] = rs["employee_id"].map(l[d]) - rs["employee_id"].map(f[d])

    # historic response rate — non-response as behaviour, not a single event
    rr = eh.groupby("employee_id")["response_flag"].mean()
    rs["hist_response_rate"] = rs["employee_id"].map(rr)

    # --- manager context --------------------------------------------------
    span = rs.groupby("manager_id").size()
    rs["mgr_span"] = rs["manager_id"].map(span)

    rs["ref_date"] = ref
    return rs


def rr_table(rs, feature, label=None, bins=None, labels=None):
    """Relative risk of voluntary exit by feature level, vs the base rate."""
    base = rs["left"].mean()
    x = rs[feature]
    if bins is not None:
        x = pd.cut(x, bins, labels=labels)
    g = rs.groupby(x, dropna=False)["left"].agg(["size", "sum", "mean"])
    g.columns = ["n", "exits", "exit_rate"]
    g["rel_risk"] = (g["exit_rate"] / base).round(2)
    g["exit_rate"] = (g["exit_rate"] * 100).round(1)
    g.index.name = label or feature
    return g[g["n"] >= 30]


if __name__ == "__main__":
    for ref in ["2024-10-25", "2025-01-31"]:
        rs = build_risk_set(ref)
        rs.to_csv(OUT / f"risk_set_{ref}.csv", index=False)
        print(f"{ref}: risk set n={len(rs):,}  voluntary exits in next 12m="
              f"{rs['left'].sum():,}  base rate={rs['left'].mean():.2%}")
