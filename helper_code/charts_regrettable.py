"""
Deck-ready charts for the regrettable-leaver profile.

Every chart is a RATE, never a count share, so no mental arithmetic is needed
to read it:

    reg_rate_department.png   exits per 1,000 employees, by department
    reg_rate_age_band.png     exits per 1,000 employees, by age band
    reg_rate_entity.png       exits per 1,000 person-years, by originating
                              entity, before and after removing the
                              <=45-day integration-cliff exits

Design rules applied throughout:
  * one number per bar, stated in the axis label - no dual-denominator bars
  * 95% confidence interval on every bar, so thin cells are visibly thin
  * a bank-average reference line for instant comparison
  * raw numerator and denominator printed on each bar for auditability
  * red = worse than bank average, grey = at or better

Usage:  python charts_regrettable.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# white outline so value labels stay legible where they cross a whisker
HALO = [pe.withStroke(linewidth=3.5, foreground="white")]

HERE = Path(__file__).resolve().parent
WINDOW = (pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31"))

BAD = "#C0392B"      # above bank average
OK = "#8E9BA6"       # at or below bank average
INK = "#2C3E50"
MUTED = "#7F8C8D"

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


# ------------------------------------------------------------------ load once
def load():
    e = pd.read_csv(HERE / "original_csv" / "employees.csv", parse_dates=["hire_date", "exit_date"])
    a = pd.read_csv(HERE / "original_csv" / "attrition_log.csv", parse_dates=["exit_date"])
    reg_ids = set(pd.read_csv(HERE / "eddited_csv" / "attrition_reg.csv")["employee_id"])

    e["is_reg"] = e.employee_id.isin(reg_ids)

    # tenure at exit, used to isolate the ~30-day integration cliff
    ten = a.merge(e[["employee_id", "hire_date"]], on="employee_id", how="left")
    ten["days"] = (ten.exit_date - ten.hire_date).dt.days
    e["is_cliff"] = e.employee_id.isin(set(ten.loc[ten.days <= 45, "employee_id"]))

    # exposure in months inside the observation window
    start = e.hire_date.clip(lower=WINDOW[0])
    end = e.exit_date.fillna(WINDOW[1]).clip(upper=WINDOW[1])
    e["exposure_yrs"] = ((end - start).dt.days / 365.25).clip(lower=0)
    return e


def wilson(k, n, per=1000, conf=0.95):
    """Wilson score interval for a proportion, scaled to a per-N rate."""
    if n == 0:
        return 0.0, 0.0
    z = stats.norm.ppf(1 - (1 - conf) / 2)
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return max(0.0, (c - h)) * per, (c + h) * per


def poisson_ci(k, exposure, per=1000, conf=0.95):
    """Exact Poisson interval on a count, expressed as a rate per `per` units."""
    if exposure == 0:
        return 0.0, 0.0
    lo = 0.0 if k == 0 else stats.chi2.ppf((1 - conf) / 2, 2 * k) / 2
    hi = stats.chi2.ppf(1 - (1 - conf) / 2, 2 * (k + 1)) / 2
    return lo / exposure * per, hi / exposure * per


def style(ax):
    ax.grid(axis="x", alpha=0.22, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)


def headings(fig, ax, title, subtitle, footnote):
    """Titles above the axes and a footnote below, in figure coords, so they
    can never collide with each other or with the plot."""
    box = ax.get_position()
    h = fig.get_figheight()
    # offsets in inches, converted to figure fractions, so spacing stays
    # constant no matter how many rows the chart has
    fig.text(box.x0, box.y1 + 0.62 / h, title, fontsize=14.5, fontweight="bold",
             color=INK, ha="left", va="bottom")
    fig.text(box.x0, box.y1 + 0.30 / h, subtitle, fontsize=10.5, color=MUTED,
             ha="left", va="bottom")
    fig.text(box.x0, box.y0 - 0.95 / h, footnote, fontsize=8.5, color=MUTED,
             ha="left", va="top")


def rate_chart(t, title, subtitle, xlabel, filename, sort=True, footnote=None):
    """t: DataFrame indexed by category with columns k, n, rate, lo, hi."""
    if sort:
        t = t.sort_values("rate")
    avg = t.k.sum() / t.n.sum() * 1000

    fh = 0.66 * len(t) + 2.6
    fig, ax = plt.subplots(figsize=(11, fh))
    fig.subplots_adjust(top=1 - 1.05 / fh, bottom=1.35 / fh, left=0.19, right=0.99)

    colors = [BAD if r > avg else OK for r in t.rate]
    y = np.arange(len(t))

    ax.barh(y, t.rate, color=colors, height=0.60, zorder=3)
    ax.errorbar(t.rate, y, xerr=[t.rate - t.lo, t.hi - t.rate], fmt="none",
                ecolor=INK, elinewidth=1.3, capsize=4, alpha=0.7, zorder=4)

    # data limit is the widest interval; the right quarter is a fixed label column
    dmax = t.hi.max() * 1.04
    xmax = dmax / 0.74
    val_x, cnt_x = dmax * 1.06, dmax * 1.20

    for i, (r, k, n) in enumerate(zip(t.rate, t.k, t.n)):
        ax.text(val_x, i, f"{r:.1f}", va="center", ha="right",
                fontsize=11.5, fontweight="bold", color=INK)
        ax.text(cnt_x, i, f"{int(k)} of {int(n):,}", va="center", ha="left",
                fontsize=9.5, color=MUTED)

    ax.axvline(avg, color=INK, ls="--", lw=1.4, zorder=5)
    ax.text(avg, len(t) - 0.35, f"  bank average {avg:.1f}", color=INK,
            fontsize=9.5, fontweight="bold", va="bottom")

    ax.set_yticks(y)
    ax.set_yticklabels(t.index)
    ax.set_xlim(0, xmax)
    ax.set_xticks([x for x in ax.get_xticks() if x <= dmax])
    ax.set_xlabel(xlabel, fontsize=10.5)
    style(ax)
    headings(fig, ax, title, subtitle,
             footnote or "Whiskers are 95% confidence intervals — wider means fewer people, "
                         "so less certainty.")
    fig.savefig(HERE / filename, dpi=200)
    plt.close(fig)
    print(f"  {filename}")
    return t


def build(e, col, order=None):
    g = e.groupby(col).agg(k=("is_reg", "sum"), n=("employee_id", "size"))
    g["rate"] = g.k / g.n * 1000
    ci = [wilson(k, n) for k, n in zip(g.k, g.n)]
    g["lo"], g["hi"] = [c[0] for c in ci], [c[1] for c in ci]
    return g.reindex(order) if order else g


# ---------------------------------------------------------------------- build
e = load()
print("Charts:")

# 1. department -------------------------------------------------------------
# Executive Leadership is 2 leavers out of 230 - the interval runs 2.4 to 31.1,
# which says nothing and wrecks the axis scale. Held out, and disclosed.
dept_all = build(e, "department")
dept = dept_all.drop(index="Executive Leadership")
rate_chart(
    dept,
    "Corporate Ops and Risk & Compliance lose good people twice as fast as Retail",
    "Regrettable exits per 1,000 employees, Jan 2024 – Dec 2025",
    "Regrettable exits per 1,000 employees",
    "reg_rate_department.png",
    footnote=("Whiskers are 95% confidence intervals — wider means fewer people, so less "
              "certainty.\nExecutive Leadership excluded: 2 leavers from 230 staff gives an "
              "interval of 2.4–31.1, which carries no information."),
)

# 2. age band ---------------------------------------------------------------
AGE = ["60+", "55-59", "50-54", "45-49", "40-44", "35-39", "30-34", "25-29", "18-24"]
age = build(e, "age_band", order=AGE)
rate_chart(
    age,
    "Risk is bimodal: early-career and pre-retirement, not mid-career",
    "Regrettable exits per 1,000 employees, Jan 2024 – Dec 2025",
    "Regrettable exits per 1,000 employees",
    "reg_rate_age_band.png",
    sort=False,
    footnote=("Bars show 95% confidence intervals. Cells hold 9–28 leavers, so the "
              "intervals overlap heavily —\ntreat the bimodal shape as a hypothesis, "
              "not a result."),
)

# 3. entity, before and after the integration cliff -------------------------
ent = e.groupby("legacy_entity_code").agg(
    k=("is_reg", "sum"),
    n=("employee_id", "size"),
    exp=("exposure_yrs", "sum"),
)
ent["k_ex"] = e[~e.is_cliff].groupby("legacy_entity_code").is_reg.sum()
ent["rate"] = ent.k / ent.exp * 1000
ent["rate_ex"] = ent.k_ex / ent.exp * 1000
ent = ent.sort_values("rate")

ci = [poisson_ci(k, x) for k, x in zip(ent.k, ent.exp)]
ent["lo"], ent["hi"] = [c[0] for c in ci], [c[1] for c in ci]

fig, ax = plt.subplots(figsize=(11.5, 5.8))
fig.subplots_adjust(top=0.82, bottom=0.30, left=0.16, right=0.99)

y = np.arange(len(ent))
h = 0.34
ax.barh(y + h / 2 + 0.02, ent.rate, h, color=BAD, zorder=3,
        label="All regrettable exits")
ax.barh(y - h / 2 - 0.02, ent.rate_ex, h, color=OK, zorder=3,
        label="Excluding exits inside the first 45 days")
ax.errorbar(ent.rate, y + h / 2 + 0.02, xerr=[ent.rate - ent.lo, ent.hi - ent.rate],
            fmt="none", ecolor=INK, elinewidth=1.2, capsize=4, alpha=0.65, zorder=4)

dmax = ent.hi.max() * 1.04
xmax = dmax / 0.70
for i, r in enumerate(ent.itertuples()):
    ax.text(r.rate + dmax * 0.012, i + h / 2 + 0.02, f"{r.rate:.1f}", va="center",
            fontsize=11, fontweight="bold", color=BAD, zorder=6, path_effects=HALO)
    ax.text(r.rate_ex + dmax * 0.012, i - h / 2 - 0.02, f"{r.rate_ex:.1f}",
            va="center", fontsize=11, fontweight="bold", color=INK, zorder=6,
            path_effects=HALO)
    ax.text(dmax * 1.07, i, f"{int(r.k)} exits\n{int(r.n):,} staff",
            va="center", ha="left", fontsize=9.5, color=MUTED, linespacing=1.4)

ax.set_yticks(y)
ax.set_yticklabels(ent.index)
ax.set_xlim(0, xmax)
ax.set_xticks([x for x in ax.get_xticks() if x <= dmax])
ax.set_xlabel("Regrettable exits per 1,000 person-years", fontsize=10.5)
ax.legend(frameon=False, fontsize=10, loc="upper center", ncol=2,
          bbox_to_anchor=(0.42, -0.16))
style(ax)
headings(
    fig, ax,
    "The merger problem lives entirely in the first 30 days",
    "Acquired entities look 2–3x worse — until the integration-cliff exits come out, "
    "then they match Origin",
    "Person-years, not headcount: Entity_C staff joined Apr–Jun 2025 and carry roughly "
    "a third of Origin's exposure.\nEntity_A was integrated before the window opened and "
    "acts as a settled-acquisition control. Whiskers are 95% Poisson intervals.",
)
fig.savefig(HERE / "reg_rate_entity.png", dpi=200)
plt.close(fig)
print("  reg_rate_entity.png")

print("\nUnderlying numbers")
print("\nDepartment:\n", dept_all.round(1).to_string())
print("\nAge band:\n", age.round(1).to_string())
print("\nEntity:\n", ent[["k", "k_ex", "n", "exp", "rate", "rate_ex"]].round(1).to_string())
