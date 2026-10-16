"""
Pie chart of regrettable exits (edited.csv) split into:
  High Achievers  = Outstanding, High Performer
  Underperformers = Meets Expectations and below
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HIGH = {"Outstanding", "High Performer"}
UNDER = ["Meets Expectations", "Below Expectations", "Unsatisfactory"]

df = pd.read_csv("eddited_csv/attrition_reg.csv")
band = df["performance_band_at_exit"].str.strip()

n_high = band.isin(HIGH).sum()
n_under = (~band.isin(HIGH)).sum()
total = n_high + n_under

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 6.5),
                              gridspec_kw={"width_ratios": [1.15, 1]})

colors = ["#1f4e79", "#d1495b"]
wedges, _, autotexts = ax.pie(
    [n_high, n_under],
    labels=[f"High Achievers\n(Outstanding + High Performer)",
            f"Underperformers\n(Meets Expectations or below)"],
    colors=colors, autopct=lambda p: f"{p:.1f}%\n({round(p*total/100)})",
    startangle=90, counterclock=False,
    explode=(0.03, 0.03), textprops={"fontsize": 11},
    wedgeprops={"edgecolor": "white", "linewidth": 2},
)
for t in autotexts:
    t.set_color("white"); t.set_fontweight("bold"); t.set_fontsize(12)
ax.set_title(f"Regrettable Exits by Performance Tier (n={total})",
             fontsize=14, fontweight="bold", pad=18)

# breakdown bar
counts = band.value_counts()
order = ["Outstanding", "High Performer"] + UNDER
vals = [counts.get(b, 0) for b in order]
bar_colors = ["#1f4e79", "#3d7ab8", "#d1495b", "#b03246", "#7d1f2e"]
bars = ax2.barh(order[::-1], vals[::-1], color=bar_colors[::-1])
for b, v in zip(bars, vals[::-1]):
    ax2.text(v + 1.5, b.get_y() + b.get_height()/2, str(v),
             va="center", fontsize=10, fontweight="bold")
ax2.set_xlim(0, max(vals) * 1.18)
ax2.set_xlabel("Regrettable exits")
ax2.set_title("Detail by band", fontsize=13, fontweight="bold", pad=18)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)

plt.tight_layout()
plt.savefig("fig4_perf_tier_pie.png", dpi=200, bbox_inches="tight")
print(f"High achievers: {n_high} ({n_high/total:.1%})")
print(f"Underperformers: {n_under} ({n_under/total:.1%})")
