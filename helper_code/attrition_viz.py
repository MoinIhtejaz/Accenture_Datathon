"""
Attrition analysis — 2024 vs 2025.

Produces three charts from attrition_log.csv:
  1. fig1_regrettable_by_year.png  — regrettable vs non-regrettable exits
  2. fig2_exit_type_by_year.png    — voluntary vs involuntary exits
  3. fig3_regrettable_perf_band.png— performance band at exit, regrettable exits only

Usage:  python attrition_viz.py [path/to/attrition_log.csv]
"""

import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------------- config
CSV = Path(sys.argv[1] if len(sys.argv) > 1 else "attrition_log.csv")
OUT = CSV.parent
YEARS = [2024, 2025]

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "axes.titleweight": "bold",
})

PERF_ORDER = [
    "Outstanding",
    "High Performer",
    "Meets Expectations",
    "Below Expectations",
    "Unsatisfactory",
]

# ---------------------------------------------------------------- load
df = pd.read_csv(CSV, parse_dates=["exit_date"])
df["exit_year"] = df["exit_date"].dt.year

# keep only the two years of interest
df = df[df["exit_year"].isin(YEARS)].copy()

# tidy label columns
df["regrettable"] = df["regrettable_flag"].map({True: "Regrettable",
                                                False: "Non-regrettable"})
df["exit_type_label"] = df["exit_type"].str.capitalize()
df["performance_band_at_exit"] = pd.Categorical(
    df["performance_band_at_exit"], categories=PERF_ORDER, ordered=True
)

print(f"Loaded {len(df):,} exits  |  "
      + "  ".join(f"{y}: {n:,}" for y, n in df["exit_year"].value_counts().sort_index().items()))


# ---------------------------------------------------------------- helper
def annotate(ax, denom_by_x=None, fmt_pct=True):
    """Write count (and share of its year) on top of every bar."""
    for container in ax.containers:
        labels = []
        for bar in container:
            h = bar.get_height()
            if not h:
                labels.append("")
                continue
            if fmt_pct and denom_by_x is not None:
                # x-centre of the bar maps back to a tick -> a year
                idx = int(round(bar.get_x() + bar.get_width() / 2))
                idx = min(max(idx, 0), len(denom_by_x) - 1)
                labels.append(f"{int(h)}\n{h / denom_by_x[idx]:.0%}")
            else:
                labels.append(f"{int(h)}")
        ax.bar_label(container, labels=labels, padding=3, fontsize=11)
    ax.margins(y=0.18)


year_totals = [df[df["exit_year"] == y].shape[0] for y in YEARS]


# ---------------------------------------------------------------- FIG 1
# Regrettable vs non-regrettable, by exit year
tab1 = (df.groupby(["exit_year", "regrettable"]).size()
          .rename("exits").reset_index())

fig, ax = plt.subplots(figsize=(9, 6))
sns.barplot(data=tab1, x="exit_year", y="exits", hue="regrettable",
            hue_order=["Non-regrettable", "Regrettable"],
            palette=["#9BB1C7", "#C1443F"], ax=ax)
annotate(ax, year_totals)
ax.set(xlabel="Exit year", ylabel="Number of exits",
       title="Regrettable vs non-regrettable exits, 2024 vs 2025")
ax.legend(title=None, bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False)
fig.savefig(OUT / "fig1_regrettable_by_year.png")
plt.close(fig)

print("\nRegrettable split")
print(pd.crosstab(df["exit_year"], df["regrettable"], margins=True))


# ---------------------------------------------------------------- FIG 2
# Voluntary vs involuntary, by exit year
tab2 = (df.groupby(["exit_year", "exit_type_label"]).size()
          .rename("exits").reset_index())

fig, ax = plt.subplots(figsize=(9, 6))
sns.barplot(data=tab2, x="exit_year", y="exits", hue="exit_type_label",
            hue_order=["Voluntary", "Involuntary"],
            palette=["#2E7D6F", "#D98A3C"], ax=ax)
annotate(ax, year_totals)
ax.set(xlabel="Exit year", ylabel="Number of exits",
       title="Voluntary vs involuntary exits, 2024 vs 2025")
ax.legend(title=None, bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False)
fig.savefig(OUT / "fig2_exit_type_by_year.png")
plt.close(fig)

print("\nExit-type split")
print(pd.crosstab(df["exit_year"], df["exit_type_label"], margins=True))


# ---------------------------------------------------------------- FIG 3
# Performance band at exit — REGRETTABLE exits only
reg = df[df["regrettable_flag"]].copy()
tab3 = (reg.groupby(["exit_year", "performance_band_at_exit"], observed=False)
           .size().rename("exits").reset_index())

reg_totals = [reg[reg["exit_year"] == y].shape[0] for y in YEARS]

fig, ax = plt.subplots(figsize=(13, 6.5))
sns.barplot(data=tab3, x="exit_year", y="exits",
            hue="performance_band_at_exit", hue_order=PERF_ORDER,
            palette=sns.color_palette("RdYlGn_r", len(PERF_ORDER)), ax=ax)
annotate(ax, reg_totals)
ax.set(xlabel="Exit year", ylabel="Number of regrettable exits",
       title="Performance band at exit — regrettable exits only")
ax.legend(title="Performance band at exit", bbox_to_anchor=(1.01, 1),
          loc="upper left", frameon=False)
fig.savefig(OUT / "fig3_regrettable_perf_band.png")
plt.close(fig)

print("\nPerformance band at exit (regrettable only)")
print(pd.crosstab(reg["exit_year"], reg["performance_band_at_exit"], margins=True))

print(f"\nSaved 3 charts to {OUT.resolve()}")
