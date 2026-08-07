"""
NovaCorp People Analytics Challenge — Discovery Charts
=========================================================

Produces ONLY the charts that answer a specific business question surfaced by
src/eda_discovery.py (see outputs/logs/eda_discovery.log for every underlying
number). No chart here exists "because the data was available" — each one is
named after the finding it supports and cross-references a finding_register.md
ID in its title. All manager-level views are aggregated; no individual
manager, employee, or reviewer is ever named or plotted.

Palette: fixed categorical order (blue, orange, aqua, yellow) from the
dataviz skill's validated reference palette — colorblind-safe, never cycled,
never assigned by rank.

Run: `python src/discovery_charts.py` from anywhere.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from load_data import BASE_DIR, OUTPUT_TABLES_DIR

CHART_DIR = BASE_DIR / "outputs" / "charts" / "discovery"
MASTER_PATH = OUTPUT_TABLES_DIR / "employee_analytics_master.csv"

BLUE, ORANGE, AQUA, YELLOW, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e34948"
TEXT_PRIMARY, TEXT_SECONDARY, GRID = "#0b0b0b", "#52514e", "#e5e3de"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "text.color": TEXT_PRIMARY, "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT_SECONDARY, "xtick.color": TEXT_SECONDARY,
    "ytick.color": TEXT_SECONDARY, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k / n
    denom = 1 + z**2 / n
    centre = p + z**2 / (2 * n)
    adj = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)
    return ((centre - adj) / denom, (centre + adj) / denom)


def pct_axis(ax):
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))


def save(fig, name):
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / name
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path}")


def bar_with_ci(ax, labels, rates, cis_lo, cis_hi, ns, color, annotate_n=True):
    x = np.arange(len(labels))
    bars = ax.bar(x, rates, color=color, width=0.6, zorder=3)
    err_lo = [max(0, r - lo) for r, lo in zip(rates, cis_lo)]
    err_hi = [max(0, hi - r) for r, hi in zip(rates, cis_hi)]
    ax.errorbar(x, rates, yerr=[err_lo, err_hi], fmt="none", ecolor=TEXT_PRIMARY,
                elinewidth=1.2, capsize=3, zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    for i, (r, n) in enumerate(zip(rates, ns)):
        label = f"{r:.1%}" + (f"\n(n={n:,})" if annotate_n else "")
        ax.text(i, r + err_hi[i] + 0.003, label, ha="center", va="bottom",
                 fontsize=9.5, color=TEXT_PRIMARY)
    return bars


# ---------------------------------------------------------------------------
# 1. HiPo flag: voluntary + regrettable exit rate
# ---------------------------------------------------------------------------

def chart_hipo_regrettable(m):
    groups = [False, True]
    labels = ["Not HiPo", "HiPo-flagged"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))
    for ax, outcome, title in zip(
        axes, ["voluntary_exit", "regrettable_voluntary_exit"],
        ["Voluntary exit rate", "Regrettable voluntary exit rate"]
    ):
        rates, los, his, ns = [], [], [], []
        for g in groups:
            sub = m[m["hipo_flag"] == g]
            n, k = len(sub), int(sub[outcome].sum())
            lo, hi = wilson_ci(k, n)
            rates.append(k / n); los.append(lo); his.append(hi); ns.append(n)
        bar_with_ci(ax, labels, rates, los, his, ns, [BLUE, ORANGE])
        for bar, c in zip(ax.patches, [BLUE, ORANGE]):
            bar.set_color(c)
        pct_axis(ax)
        ax.set_title(title, fontsize=11.5, color=TEXT_PRIMARY)
        ax.set_ylim(0, max(rates) * 1.6)
    fig.suptitle("FR-01: HiPo-flagged employees leave — and leave regrettably — far more than everyone else",
                 fontsize=12.5, y=1.04)
    save(fig, "01_hipo_regrettable_exit.png")


# ---------------------------------------------------------------------------
# 2. Legacy entity: voluntary exit rate
# ---------------------------------------------------------------------------

def chart_entity_attrition(m):
    t = m.groupby("legacy_entity", observed=True)["voluntary_exit"].agg(["sum", "count"])
    t["rate"] = t["sum"] / t["count"]
    t = t.sort_values("rate", ascending=False)
    los, his = zip(*[wilson_ci(k, n) for k, n in zip(t["sum"], t["count"])])
    fig, ax = plt.subplots(figsize=(7, 4.2))
    colors = [ORANGE if idx == "Entity_B" else BLUE for idx in t.index]
    bar_with_ci(ax, list(t.index), list(t["rate"]), los, his, list(t["count"]), colors)
    for bar, c in zip(ax.patches, colors):
        bar.set_color(c)
    pct_axis(ax)
    ax.set_ylim(0, t["rate"].max() * 1.5)
    ax.set_title("FR-02: Entity_B's attrition gap persists across every department (chi2 p=2.7e-08)",
                 fontsize=12)
    save(fig, "02_attrition_by_legacy_entity.png")


# ---------------------------------------------------------------------------
# 3. Promotion recommendation rate by legacy entity, within role level (FR-03)
# ---------------------------------------------------------------------------

def chart_entity_promotion_gap(m):
    m8 = m[m["performance_promotion_recommendation_ever"].notna()].copy()
    m8["promo"] = m8["performance_promotion_recommendation_ever"].astype(bool)
    levels = [1, 2, 3, 4]
    entities = ["NovaCorp-Origin", "Entity_A", "Entity_B", "Entity_C"]
    colors = {"NovaCorp-Origin": BLUE, "Entity_A": AQUA, "Entity_B": ORANGE, "Entity_C": RED}
    fig, ax = plt.subplots(figsize=(9, 4.8))
    width = 0.2
    x = np.arange(len(levels))
    for i, ent in enumerate(entities):
        rates = []
        for lvl in levels:
            sub = m8[(m8["role_level"] == lvl) & (m8["legacy_entity"] == ent)]
            rates.append(sub["promo"].mean() if len(sub) >= 15 else np.nan)
        ax.bar(x + (i - 1.5) * width, rates, width=width, color=colors[ent], label=ent, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Level {l}" for l in levels])
    pct_axis(ax)
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.set_title("FR-03: Entity_C is promoted at roughly half the rate of every other cohort, at every level",
                 fontsize=12)
    save(fig, "03_promotion_rate_by_entity_and_level.png")


# ---------------------------------------------------------------------------
# 4. Entity_B: compensation is not the driver — trust is (FR-04)
# ---------------------------------------------------------------------------

def chart_entity_b_pay_vs_trust(m):
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    entities = ["NovaCorp-Origin", "Entity_A", "Entity_B", "Entity_C"]
    colors = [BLUE, AQUA, ORANGE, RED]

    ax = axes[0]
    medians = [m.loc[m["legacy_entity"] == e, "compa_ratio"].median() for e in entities]
    bars = ax.bar(entities, medians, color=colors, zorder=3)
    ax.set_ylim(0.85, 1.0)
    ax.set_title("Median compa_ratio\n(Entity_B is NOT underpaid)", fontsize=11)
    for i, v in enumerate(medians):
        ax.text(i, v + 0.003, f"{v:.2f}", ha="center", fontsize=9.5)
    ax.set_xticks(range(len(entities)))
    ax.set_xticklabels(entities, rotation=15, ha="right")

    ax = axes[1]
    means = [m.loc[m["legacy_entity"] == e, "senior_leadership_trust_latest_score"].mean() for e in entities]
    bars = ax.bar(entities, means, color=colors, zorder=3)
    ax.set_ylim(2.8, 3.5)
    ax.set_title("Mean senior_leadership_trust (latest)\n(Entity_B is the clear outlier)", fontsize=11)
    for i, v in enumerate(means):
        ax.text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=9.5)
    ax.set_xticks(range(len(entities)))
    ax.set_xticklabels(entities, rotation=15, ha="right")

    fig.suptitle("FR-04: Entity_B's elevated attrition tracks leadership trust, not pay", fontsize=12.5, y=1.05)
    save(fig, "04_entity_b_pay_vs_trust.png")


# ---------------------------------------------------------------------------
# 5. Survey non-response as a leading indicator (FR-05)
# ---------------------------------------------------------------------------

def chart_nonresponse_leading_indicator(m):
    m6 = m[m["engagement_n_waves_available"] > 0].copy()
    recent_non_resp = m6["engagement_recent_non_response_flag"] == True  # noqa: E712 — NaN -> False cleanly
    m6["group"] = np.select(
        [m6["engagement_n_responses_available"] == 0, recent_non_resp],
        ["Never responded", "Recent non-response"],
        default="Responded recently",
    )
    order = ["Responded recently", "Recent non-response", "Never responded"]
    colors = [BLUE, ORANGE, RED]
    rates, los, his, ns = [], [], [], []
    for g in order:
        sub = m6[m6["group"] == g]
        n, k = len(sub), int(sub["voluntary_exit"].sum())
        lo, hi = wilson_ci(k, n)
        rates.append(k / n); los.append(lo); his.append(hi); ns.append(n)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bar_with_ci(ax, order, rates, los, his, ns, colors)
    for bar, c in zip(ax.patches, colors):
        bar.set_color(c)
    pct_axis(ax)
    ax.set_ylim(0, max(rates) * 1.4)
    ax.set_title("FR-05: Silence predicts departure better than any survey score\n(voluntary exit rate by response behaviour)",
                 fontsize=12)
    save(fig, "05_nonresponse_leading_indicator.png")


# ---------------------------------------------------------------------------
# 6. Promotion pipeline: stalled high performers (FR-06)
# ---------------------------------------------------------------------------

def chart_stalled_pipeline(m):
    m9 = m[m["performance_promotion_recommendation_ever"].notna()].copy()
    m9["promo_rec_ever"] = m9["performance_promotion_recommendation_ever"].astype(bool)
    m9["high_perf"] = m9["performance_latest_rating"].isin(["High Performer", "Outstanding"])
    stalled = m9[(m9["promotion_eligible"]) & (m9["high_perf"]) & (~m9["promo_rec_ever"])]
    advancing = m9[(m9["promotion_eligible"]) & (m9["high_perf"]) & (m9["promo_rec_ever"])]
    labels = ["Stalled\n(eligible, high-performing,\nnever recommended)",
              "Advancing\n(eligible, high-performing,\nrecommended)"]
    groups = [stalled, advancing]
    rates = [g["voluntary_exit"].mean() for g in groups]
    ns = [len(g) for g in groups]
    los, his = zip(*[wilson_ci(int(g["voluntary_exit"].sum()), len(g)) for g in groups])
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    bar_with_ci(ax, labels, rates, los, his, ns, [RED, AQUA])
    for bar, c in zip(ax.patches, [RED, AQUA]):
        bar.set_color(c)
    pct_axis(ax)
    ax.set_ylim(0, max(rates) * 1.5)
    ax.set_title("FR-06: High performers stuck without a promotion signal leave\nnearly 2x as often (p=0.004)", fontsize=12)
    save(fig, "06_stalled_promotion_pipeline.png")


# ---------------------------------------------------------------------------
# 7. Manager-level dispersion in voluntary exit rate (privacy-safe, aggregated)
# ---------------------------------------------------------------------------

def chart_manager_dispersion(m):
    mgr = m.groupby("manager_id", observed=True).agg(
        team_size=("employee_id", "count"),
        voluntary_exit_rate=("voluntary_exit", "mean"),
    ).reset_index()
    mgr = mgr[mgr["team_size"] >= 5]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(mgr["voluntary_exit_rate"], bins=20, color=BLUE, zorder=3)
    ax.axvline(m["voluntary_exit"].mean(), color=RED, linestyle="--", linewidth=1.5,
               label=f"Company average ({m['voluntary_exit'].mean():.1%})")
    ax.set_xlabel("Team voluntary exit rate")
    ax.set_ylabel("Number of managers")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.legend(frameon=False)
    ax.set_title(f"FR-07: Attrition varies sharply by manager (n={len(mgr)} managers, ≥5 reports)\n"
                 "No individual manager identified — aggregate distribution only", fontsize=11.5)
    save(fig, "07_manager_level_dispersion.png")


# ---------------------------------------------------------------------------
# 8. Tenure-band voluntary exit rate (early-tenure risk, with censoring caveat)
# ---------------------------------------------------------------------------

def chart_tenure_band(m):
    m3 = m.copy()
    m3["tenure_band"] = pd.cut(m3["tenure_months"], bins=[-1, 6, 12, 24, 60, 10000],
                                labels=["0-6mo", "7-12mo", "13-24mo", "25-60mo", "60mo+"])
    t = m3.groupby("tenure_band", observed=True)["voluntary_exit"].agg(["sum", "count"])
    t["rate"] = t["sum"] / t["count"]
    los, his = zip(*[wilson_ci(k, n) for k, n in zip(t["sum"], t["count"])])
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bar_with_ci(ax, list(t.index), list(t["rate"]), los, his, list(t["count"]), BLUE)
    pct_axis(ax)
    ax.set_ylim(0, 0.75)
    ax.set_title("FR-08: Apparent early-tenure attrition spike — see caveat\n(right-censoring likely inflates the 0-6mo bar; not a clean rate)",
                 fontsize=11.5)
    save(fig, "08_tenure_band_exit_rate.png")


# ---------------------------------------------------------------------------
# 9. Post-acquisition rapid exits (FR-09)
# ---------------------------------------------------------------------------

def chart_acquisition_rapid_exit(m):
    acq = m[m["hire_source"] == "acquisition"].copy()
    early = acq[(acq["voluntary_exit"]) & (acq["tenure_months"] < 12)]
    by_entity = early["legacy_entity"].value_counts().reindex(["Entity_A", "Entity_B", "Entity_C"]).fillna(0)
    totals = acq["legacy_entity"].value_counts().reindex(["Entity_A", "Entity_B", "Entity_C"]).fillna(0)
    rate = by_entity / totals
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = [AQUA, ORANGE, RED]
    bars = ax.bar(rate.index, rate.values, color=colors, zorder=3)
    for i, (r, n) in enumerate(zip(rate.values, by_entity.values)):
        ax.text(i, r + 0.006, f"{r:.1%}\n(n={int(n)})", ha="center", fontsize=9.5)
    pct_axis(ax)
    ax.set_ylim(0, rate.max() * 1.35)
    ax.set_title("FR-09: A wave of very early exits clusters right after each\nentity's own acquisition period (<12mo tenure, voluntary)",
                 fontsize=11.5, pad=14)
    save(fig, "09_post_acquisition_rapid_exits.png")


# ---------------------------------------------------------------------------
# 10. Compensation is NOT a clean company-wide attrition driver (null finding)
# ---------------------------------------------------------------------------

def chart_compa_quartile_flat(m):
    m4 = m.copy()

    def _safe_qcut(s):
        try:
            return pd.qcut(s, 4, labels=False, duplicates="drop")
        except ValueError:
            return pd.Series(np.nan, index=s.index)

    label_map = {0: "Q1 (low)", 1: "Q2", 2: "Q3", 3: "Q4 (high)"}
    m4["q"] = m4.groupby("role_level")["compa_ratio"].transform(_safe_qcut).map(label_map)
    t = m4.dropna(subset=["q"]).groupby("q", observed=True)["voluntary_exit"].agg(["sum", "count"])
    t = t.reindex(["Q1 (low)", "Q2", "Q3", "Q4 (high)"])
    t["rate"] = t["sum"] / t["count"]
    los, his = zip(*[wilson_ci(k, n) for k, n in zip(t["sum"], t["count"])])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bar_with_ci(ax, list(t.index), list(t["rate"]), los, his, list(t["count"]), BLUE)
    pct_axis(ax)
    ax.set_ylim(0, 0.13)
    ax.set_title("FR-10: Pay relative to peers shows no clean gradient with attrition\n(compa_ratio quartile within role_level)",
                 fontsize=11.5)
    save(fig, "10_compa_ratio_quartile_flat.png")


def main():
    m = pd.read_csv(MASTER_PATH, parse_dates=["hire_date", "exit_date", "cutoff_date"], low_memory=False)
    for c in ["voluntary_exit", "regrettable_voluntary_exit", "hipo_flag", "departed"]:
        m[c] = m[c].astype(bool)

    chart_hipo_regrettable(m)
    chart_entity_attrition(m)
    chart_entity_promotion_gap(m)
    chart_entity_b_pay_vs_trust(m)
    chart_nonresponse_leading_indicator(m)
    chart_stalled_pipeline(m)
    chart_manager_dispersion(m)
    chart_tenure_band(m)
    chart_acquisition_rapid_exit(m)
    chart_compa_quartile_flat(m)
    print(f"\n10 charts written to {CHART_DIR}")


if __name__ == "__main__":
    main()
