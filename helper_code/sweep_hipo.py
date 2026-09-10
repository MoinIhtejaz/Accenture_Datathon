"""
sweep_hipo.py — univariate significance sweep, run in parallel on two definitions of the
population we care about.

  POP A  "HiPo churn"      : cohort = hipo_flag == True (n=1210). Outcome = voluntary exit.
                             Clean, avoids the regrettable_flag circularity from findings_04.
  POP B  "Regrettable"     : cohort = active staff + regrettable leavers. Outcome = regrettable.
                             Business-resonant but partly definitional; read alongside POP A.
  POP C  "Which exits hurt": cohort = voluntary leavers only. Outcome = regrettable.
                             Asks what separates a painful exit from a routine one.

Every categorical gets chi-square (Fisher when 2x2 and sparse); every continuous gets Welch's t
plus Mann-Whitney as a distribution-free check. Effect sizes reported throughout because with
n=13k, p-values alone will light up on noise. Benjamini-Hochberg FDR across the whole sweep.
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "eddited_csv" / "master_features.csv", low_memory=False)

CATS = ["department", "role_family", "role_level", "gender", "age_band",
        "cultural_background", "contract_type", "hire_source", "legacy_entity_code",
        "promotion_eligible", "acting_appointment", "ever_promo_rec", "last_promo_rec",
        "top_performer", "ever_nonresponder", "went_silent", "mgr_departed",
        "underpaid", "notice_period_served", "pathway"]

CONTS = ["salary", "compa_ratio", "compa_vs_peer", "salary_vs_peer", "tenure_years",
         "days_to_fill", "mgr_span", "mgr_team_vol_rate", "mgr_team_hipo_share",
         "mgr_rated_effectiveness", "nonresponse_rate", "n_promo_rec", "n_reviews",
         "n_reviewers", "mean_goal", "last_goal", "goal_delta", "mean_rating_num",
         "last_rating_num", "rating_delta", "last_engagement_index", "mean_engagement_index",
         "slope_engagement_index"]
ENG_DIMS = ["manager_effectiveness", "psychological_safety", "recognition",
            "career_development", "senior_leadership_trust", "purpose_meaning",
            "wellbeing", "confidence_in_role_future"]
CONTS += [f"last_{d}" for d in ENG_DIMS] + [f"slope_{d}" for d in ENG_DIMS]


def cramers_v(ct):
    chi2 = stats.chi2_contingency(ct)[0]
    n = ct.values.sum()
    return float(np.sqrt(chi2 / (n * (min(ct.shape) - 1))))


def hedges_g(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    d = (a.mean() - b.mean()) / sp if sp > 0 else np.nan
    J = 1 - 3 / (4 * (na + nb) - 9)
    return float(d * J)


def sweep(data, outcome, label):
    rows = []
    y = data[outcome]
    for c in CATS:
        if c not in data:
            continue
        sub = data[[c, outcome]].dropna()
        if sub[c].nunique() < 2 or sub[outcome].nunique() < 2:
            continue
        ct = pd.crosstab(sub[c], sub[outcome])
        if ct.shape[0] < 2 or ct.values.min() < 0 or ct.values.sum() < 30:
            continue
        chi2, p, dofv, _ = stats.chi2_contingency(ct)
        eff, extra = cramers_v(ct), ""
        if ct.shape == (2, 2):
            orr, fp = stats.fisher_exact(ct.values)
            a, b, cc, d = ct.values.ravel()
            if min(a, b, cc, d) > 0:
                se = np.sqrt(1 / a + 1 / b + 1 / cc + 1 / d)
                lo, hi = np.exp(np.log(orr) - 1.96 * se), np.exp(np.log(orr) + 1.96 * se)
                extra = f"OR={orr:.2f} [{lo:.2f}-{hi:.2f}]"
            p = fp
        rate = sub.groupby(c)[outcome].mean()
        rows.append(dict(pop=label, var=c, kind="cat", n=int(ct.values.sum()),
                         stat=chi2, p=p, effect=eff, effect_name="CramersV",
                         detail=extra, spread=f"{rate.min():.1%}-{rate.max():.1%}",
                         hi_group=str(rate.idxmax()), hi_rate=float(rate.max()),
                         lo_group=str(rate.idxmin()), lo_rate=float(rate.min())))

    for c in CONTS:
        if c not in data:
            continue
        sub = data[[c, outcome]].dropna()
        g1 = sub.loc[sub[outcome] == 1, c].to_numpy(float)
        g0 = sub.loc[sub[outcome] == 0, c].to_numpy(float)
        if len(g1) < 15 or len(g0) < 15 or np.ptp(np.r_[g0, g1]) == 0:
            continue
        t, p = stats.ttest_ind(g1, g0, equal_var=False)
        u, pu = stats.mannwhitneyu(g1, g0)
        rows.append(dict(pop=label, var=c, kind="num", n=len(sub), stat=t, p=p,
                         effect=hedges_g(g1, g0), effect_name="Hedges_g",
                         detail=f"MWU p={pu:.2e}", spread=f"{g1.mean():.3f} vs {g0.mean():.3f}",
                         hi_group="event", hi_rate=float(g1.mean()),
                         lo_group="non-event", lo_rate=float(g0.mean())))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------- cohorts
popA = df[df["hipo"] == 1].copy()
popB = df[(df["regrettable"] == 1) | (df["status"] == "active")].copy()
popC = df[df["exit_type"] == "voluntary"].copy()

res = pd.concat([
    sweep(popA, "voluntary", "A_hipo_voluntary"),
    sweep(popB, "regrettable", "B_regrettable_vs_active"),
    sweep(popC, "regrettable", "C_which_exits_hurt"),
], ignore_index=True)

res["q"] = multipletests(res["p"], method="fdr_bh")[1]
res["sig"] = np.where(res["q"] < 0.01, "***", np.where(res["q"] < 0.05, "**",
                      np.where(res["q"] < 0.10, "*", "")))
res = res.sort_values(["pop", "q"])
res.to_csv(ROOT / "eddited_csv" / "sweep_results.csv", index=False)

pd.set_option("display.width", 250, "display.max_colwidth", 46)
for pop in ["A_hipo_voluntary", "B_regrettable_vs_active", "C_which_exits_hurt"]:
    sub = res[res["pop"] == pop]
    n_ev = {"A_hipo_voluntary": (popA["voluntary"] == 1).sum(),
            "B_regrettable_vs_active": (popB["regrettable"] == 1).sum(),
            "C_which_exits_hurt": (popC["regrettable"] == 1).sum()}[pop]
    print(f"\n{'='*120}\n{pop}   cohort n={sub['n'].max()}  events={n_ev}\n{'='*120}")
    print(sub[sub["q"] < 0.10][["var", "kind", "n", "p", "q", "effect", "effect_name",
                                "spread", "hi_group", "hi_rate", "lo_group", "lo_rate",
                                "detail", "sig"]].to_string(index=False))
    print(f"  ... {(sub['q'] >= 0.10).sum()} of {len(sub)} tests not significant at FDR 10%")
