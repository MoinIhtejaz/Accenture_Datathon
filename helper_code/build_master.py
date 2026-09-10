"""
build_master.py — one employee-level feature table for the HiPo / regrettable attrition diagnosis.

Design rules baked in:
  * Engagement and performance features use only observations dated strictly BEFORE exit_date
    for leavers. Without this you get leakage: a survey taken during someone's notice period
    predicts their exit trivially.
  * response_flag == False rows are kept and counted. The brief says non-response is signal.
  * 2025-H2 is deliberately absent from performance.csv. "Ever recommended" therefore spans
    2024-H1 to 2025-H1 only, and that caveat travels with every promotion feature.

Outputs: eddited_csv/master_features.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "original_csv"
OUT = ROOT / "eddited_csv"
OUT.mkdir(exist_ok=True)

ENG_DIMS = [
    "manager_effectiveness", "psychological_safety", "recognition",
    "career_development", "senior_leadership_trust", "purpose_meaning",
    "wellbeing", "confidence_in_role_future",
]

# ----------------------------------------------------------------------------- load
emp = pd.read_csv(RAW / "employees.csv", parse_dates=["hire_date", "exit_date"])
att = pd.read_csv(RAW / "attrition_log.csv", parse_dates=["exit_date"])
eng = pd.read_csv(RAW / "engagement.csv", parse_dates=["survey_date"])
perf = pd.read_csv(RAW / "performance.csv", parse_dates=["review_date"])

att = att.rename(columns={"exit_date": "exit_date_log"})
df = emp.merge(
    att[["employee_id", "exit_date_log", "exit_type", "stated_exit_reason",
         "notice_period_served", "regrettable_flag", "performance_band_at_exit",
         "salary_at_exit", "manager_id_at_exit", "pathway"]],
    on="employee_id", how="left",
)

df["exit_dt"] = df["exit_date"].fillna(df["exit_date_log"])
df["is_leaver"] = df["exit_type"].notna()
df["voluntary"] = (df["exit_type"] == "voluntary").astype(int)
df["regrettable"] = (df["regrettable_flag"] == True).astype(int)

CENSOR = pd.Timestamp("2025-12-31")
df["cutoff"] = df["exit_dt"].fillna(CENSOR)

# ------------------------------------------------------------------- engagement feats
eng = eng.merge(df[["employee_id", "cutoff"]], on="employee_id", how="left")
eng_pre = eng[eng["survey_date"] < eng["cutoff"]].copy()

resp = eng_pre[eng_pre["response_flag"] == True]

# last observed response per dimension
last = (resp.sort_values("survey_date")
            .groupby("employee_id")[ENG_DIMS].last()
            .add_prefix("last_"))
mean_ = resp.groupby("employee_id")[ENG_DIMS].mean().add_prefix("mean_")

# slope per dimension: OLS on wave_number, needs >=2 responses
def slopes(g):
    x = g["wave_number"].to_numpy(float)
    if len(x) < 2 or np.ptp(x) == 0:
        return pd.Series({f"slope_{d}": np.nan for d in ENG_DIMS})
    xc = x - x.mean()
    denom = (xc ** 2).sum()
    out = {}
    for d in ENG_DIMS:
        y = g[d].to_numpy(float)
        out[f"slope_{d}"] = np.nan if np.isnan(y).any() else float((xc * y).sum() / denom)
    return pd.Series(out)

slope = resp.groupby("employee_id").apply(slopes, include_groups=False)

# non-response behaviour
nr = eng_pre.groupby("employee_id").agg(
    waves_offered=("wave_number", "size"),
    waves_answered=("response_flag", "sum"),
)
nr["nonresponse_rate"] = 1 - nr["waves_answered"] / nr["waves_offered"]
nr["ever_nonresponder"] = (nr["waves_answered"] < nr["waves_offered"]).astype(int)

# did they go silent at the end? (last offered wave unanswered)
last_offer = (eng_pre.sort_values("wave_number")
                     .groupby("employee_id")["response_flag"].last()
                     .rename("answered_final_wave"))

eng_feat = last.join(mean_).join(slope).join(nr).join(last_offer)
eng_feat["went_silent"] = (~eng_feat["answered_final_wave"].fillna(True).astype(bool)).astype(int)

# composite index across the eight dimensions
eng_feat["last_engagement_index"] = eng_feat[[f"last_{d}" for d in ENG_DIMS]].mean(axis=1)
eng_feat["mean_engagement_index"] = eng_feat[[f"mean_{d}" for d in ENG_DIMS]].mean(axis=1)
eng_feat["slope_engagement_index"] = eng_feat[[f"slope_{d}" for d in ENG_DIMS]].mean(axis=1)

# ------------------------------------------------------------------ performance feats
perf = perf.merge(df[["employee_id", "cutoff"]], on="employee_id", how="left")
perf_pre = perf[perf["review_date"] < perf["cutoff"]].copy()

RATING_ORD = {"Unsatisfactory": 1, "Below Expectations": 2, "Meets Expectations": 3,
              "High Performer": 4, "Outstanding": 5}
perf_pre["rating_num"] = perf_pre["performance_rating"].map(RATING_ORD)

pf = perf_pre.sort_values("review_date").groupby("employee_id").agg(
    n_reviews=("performance_rating", "size"),
    last_rating_num=("rating_num", "last"),
    mean_rating_num=("rating_num", "mean"),
    first_rating_num=("rating_num", "first"),
    last_goal=("goal_achievement_score", "last"),
    mean_goal=("goal_achievement_score", "mean"),
    first_goal=("goal_achievement_score", "first"),
    n_promo_rec=("promotion_recommendation", "sum"),
    ever_promo_rec=("promotion_recommendation", "max"),
    last_promo_rec=("promotion_recommendation", "last"),
    n_reviewers=("reviewer_id", "nunique"),
)
pf["rating_delta"] = pf["last_rating_num"] - pf["first_rating_num"]
pf["goal_delta"] = pf["last_goal"] - pf["first_goal"]
pf["top_performer"] = (pf["last_rating_num"] >= 4).astype(int)

df = df.merge(eng_feat, on="employee_id", how="left").merge(pf, on="employee_id", how="left")

# ------------------------------------------------------------------- manager features
mgr_size = emp.groupby("manager_id").size().rename("mgr_span")
mgr_vol = (df.groupby("manager_id")["voluntary"].mean().rename("mgr_team_vol_rate"))
mgr_hipo = (df.groupby("manager_id")["hipo_flag"].mean().rename("mgr_team_hipo_share"))
df = (df.merge(mgr_size, left_on="manager_id", right_index=True, how="left")
        .merge(mgr_vol, left_on="manager_id", right_index=True, how="left")
        .merge(mgr_hipo, left_on="manager_id", right_index=True, how="left"))

# manager's own engagement-rated effectiveness, averaged over their reports
mgr_eff = (df.groupby("manager_id")["mean_manager_effectiveness"].mean()
             .rename("mgr_rated_effectiveness"))
df = df.merge(mgr_eff, left_on="manager_id", right_index=True, how="left")

# did the employee's own manager leave during the window?
mgr_left = df.set_index("employee_id")["is_leaver"].rename("mgr_departed")
df = df.merge(mgr_left, left_on="manager_id", right_index=True, how="left")
df["mgr_departed"] = df["mgr_departed"].fillna(False).astype(int)

# --------------------------------------------------------------------- pay position
df["peer_median_salary"] = df.groupby(["department", "role_level"])["salary"].transform("median")
df["salary_vs_peer"] = df["salary"] / df["peer_median_salary"]
df["peer_median_compa"] = df.groupby(["department", "role_level"])["compa_ratio"].transform("median")
df["compa_vs_peer"] = df["compa_ratio"] - df["peer_median_compa"]
df["underpaid"] = (df["compa_ratio"] < 0.90).astype(int)

df["tenure_years"] = df["tenure_months"] / 12.0
df["hipo"] = df["hipo_flag"].astype(int)

df.to_csv(OUT / "master_features.csv", index=False)
print(f"master_features.csv  rows={len(df)}  cols={df.shape[1]}")
print("hipo:", int(df.hipo.sum()), "| voluntary:", int(df.voluntary.sum()),
      "| regrettable:", int(df.regrettable.sum()))
print("hipo & voluntary:", int(((df.hipo == 1) & (df.voluntary == 1)).sum()))
