"""
Profile the regrettable-exit population against a comparison group.

The point of this script is NOT to describe the 153 regrettable leavers in
isolation -- describing cases selected on the outcome tells you nothing.
Every statistic here is computed against a stayer baseline so that
"X% of leavers were Y" can be read as "...versus Z% of people who stayed".

Outputs a console report. Run:  python profile_regrettable.py
"""

import numpy as np
import pandas as pd
from scipy import stats

pd.set_option("display.width", 220)

DIMS = [
    "manager_effectiveness", "psychological_safety", "recognition",
    "career_development", "senior_leadership_trust", "purpose_meaning",
    "wellbeing", "confidence_in_role_future",
]


def load():
    emp = pd.read_csv("original_csv/employees.csv")
    att = pd.read_csv("original_csv/attrition_log.csv")
    df = emp.merge(att.drop(columns=["exit_date"]), on="employee_id", how="left")
    df["regr"] = df["regrettable_flag"].fillna(False).infer_objects(copy=False).astype(bool)
    df["stayer"] = df["status"].eq("active")
    return df


def hdr(s):
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


def composition(df, col):
    """Category mix among regrettable leavers vs stayers, with lift."""
    r = df[df.regr][col].value_counts(normalize=True) * 100
    s = df[df.stayer][col].value_counts(normalize=True) * 100
    out = pd.DataFrame({"regr_%": r, "stayer_%": s}).fillna(0)
    out["lift"] = (out["regr_%"] / out["stayer_%"]).round(2)
    return out.sort_values("lift", ascending=False).round(1)


def welch(x, y):
    """Welch t-test plus Cohen's d -- effect size always reported alongside p."""
    x, y = x.dropna(), y.dropna()
    _, p = stats.ttest_ind(x, y, equal_var=False)
    d = (x.mean() - y.mean()) / np.sqrt((x.var() + y.var()) / 2)
    return x.mean(), y.mean(), d, p


def bh_correct(pvals, alpha=0.05):
    """Benjamini-Hochberg FDR. Returns adjusted p-values in original order."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    adj = np.empty(n)
    prev = 1.0
    for rank, idx in enumerate(reversed(order), start=1):
        val = min(prev, p[idx] * n / (n - rank + 1))
        adj[idx] = prev = val
    return adj


# --------------------------------------------------------------- 1. who
def who(df):
    hdr("1. WHO THEY ARE  (composition vs stayers; lift > 1 = over-represented)")
    for col in ["department", "legacy_entity_code", "role_level", "hire_source"]:
        print(f"\n--- {col} ---")
        print(composition(df, col).to_string())

    print("\n--- binary traits ---")
    for col in ["hipo_flag", "promotion_eligible"]:
        print(f"  {col:20s} regr={df[df.regr][col].mean()*100:5.1f}%   "
              f"stayer={df[df.stayer][col].mean()*100:5.1f}%")


# ------------------------------------------------- 2. the compa_ratio trap
def compa_trap(df):
    hdr("2. COMPA-RATIO: aggregate result vs stratified result (Simpson's paradox)")
    mr, ms, d, p = welch(df[df.regr].compa_ratio, df[df.stayer].compa_ratio)
    print(f"  AGGREGATE   regr={mr:.4f}  stayer={ms:.4f}  d={d:+.3f}  p={p:.3g}")
    print("  -> reads as 'regrettable leavers were underpaid'. Now stratify by HiPo:\n")

    print(f"  HiPo stayers avg compa    = {df[df.stayer & df.hipo_flag].compa_ratio.mean():.4f}")
    print(f"  non-HiPo stayers avg compa= {df[df.stayer & ~df.hipo_flag].compa_ratio.mean():.4f}")
    print("  (HiPos sit lower in band regardless of whether they leave)\n")

    for grp, lab in [(True, "HiPo"), (False, "non-HiPo")]:
        mr, ms, d, p = welch(df[df.regr & (df.hipo_flag == grp)].compa_ratio,
                             df[df.stayer & (df.hipo_flag == grp)].compa_ratio)
        print(f"  within {lab:9s} regr={mr:.4f}  stayer={ms:.4f}  d={d:+.3f}  p={p:.3g}")
    print("\n  -> the aggregate gap is confounding, not a pay-driven attrition finding.")


# ------------------------------------------------- 3. manager clustering
def managers(df, min_span=5):
    hdr("3. DO REGRETTABLE EXITS CLUSTER UNDER PARTICULAR MANAGERS?")
    mgr = (df.groupby("manager_id")
             .agg(span=("employee_id", "count"), regr=("regr", "sum")))
    mgr = mgr[mgr.span >= min_span]
    lam = mgr.regr.mean()
    disp = mgr.regr.var() / mgr.regr.mean()

    obs = mgr.regr.value_counts().sort_index()
    exp = pd.Series(stats.poisson.pmf(obs.index, lam) * len(mgr), index=obs.index)
    print(f"  managers with span >= {min_span}: {len(mgr)}   regrettable exits in scope: {int(mgr.regr.sum())}")
    print(f"  lambda (mean per manager) = {lam:.4f}")
    print(pd.DataFrame({"observed": obs, "poisson_expected": exp.round(1)}).to_string())
    print(f"\n  variance/mean = {disp:.3f}   (1.0 == random Poisson scatter, >1 == clustering)")
    print(f"  managers losing >=2: {int((mgr.regr >= 2).sum())}")
    print("\n  -> if dispersion ~= 1 and no manager loses 2+, the 'bad manager' hypothesis fails.")


# ------------------------------------------------- 4. the recognition gap
def recognition_gap(df):
    hdr("4. RECOGNITION GAP: rated highly, never put forward")
    perf = pd.read_csv("original_csv/performance.csv")
    pr = perf.groupby("employee_id").agg(
        promo_rec=("promotion_recommendation", "max"),
        goal=("goal_achievement_score", "mean"))
    m = df.merge(pr, left_on="employee_id", right_index=True, how="left")

    print(f"  Ever recommended for promotion: regr={m[m.regr].promo_rec.mean()*100:.1f}%  "
          f"stayers={m[m.stayer].promo_rec.mean()*100:.1f}%")
    print(f"  Mean goal achievement:          regr={m[m.regr].goal.mean():.1f}     "
          f"stayers={m[m.stayer].goal.mean():.1f}")
    print(f"\n  Performance band at exit (regrettable only):")
    print("   ", df[df.regr].performance_band_at_exit.value_counts().to_dict())

    elig = m[m.promotion_eligible == True]  # noqa: E712
    never = elig[elig.promo_rec != True]    # noqa: E712
    rec = elig[elig.promo_rec == True]      # noqa: E712
    ct = pd.crosstab(elig.promo_rec == True, elig.regr)  # noqa: E712
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    print(f"\n  Among promotion-ELIGIBLE employees:")
    print(f"    never recommended -> regrettable rate {never.regr.mean()*100:.2f}%  (n={len(never)})")
    print(f"    recommended       -> regrettable rate {rec.regr.mean()*100:.2f}%  (n={len(rec)})")
    print(f"    chi2={chi2:.1f}  dof={dof}  p={p:.4g}")


# ------------------------------------------------- 5. engagement signal
def engagement(df):
    hdr("5. LAST OBSERVED ENGAGEMENT BEFORE EXIT (BH-corrected)")
    g = pd.read_csv("original_csv/engagement.csv")
    last = (g[g.response_flag].sort_values("wave_number")
              .groupby("employee_id").tail(1).set_index("employee_id")[DIMS])
    m = df.merge(last, left_on="employee_id", right_index=True, how="left")

    rows, pvals = [], []
    for d in DIMS:
        mr, ms, dd, p = welch(m[m.regr][d], m[m.stayer][d])
        rows.append([d, round(mr, 3), round(ms, 3), round(dd, 3)])
        pvals.append(p)
    adj = bh_correct(pvals)
    out = pd.DataFrame(rows, columns=["dimension", "regr", "stayer", "cohen_d"])
    out["p_raw"] = [f"{x:.4g}" for x in pvals]
    out["p_BH"] = [f"{x:.4g}" for x in adj]
    out["sig_BH"] = adj < 0.05
    print(out.sort_values("cohen_d").to_string(index=False))


if __name__ == "__main__":
    d = load()
    print(f"Loaded {len(d):,} employees | regrettable={int(d.regr.sum())} | stayers={int(d.stayer.sum())}")
    who(d)
    compa_trap(d)
    managers(d)
    recognition_gap(d)
    engagement(d)
