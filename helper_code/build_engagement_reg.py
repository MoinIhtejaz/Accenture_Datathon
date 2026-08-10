"""
Build engagement_reg.csv — the engagement.csv rows belonging to the regrettable
leavers listed in edited.csv — and chart every field that sits after
response_flag (the eight survey dimensions).

Each dimension gets a grouped bar chart: mean score per wave for the
regrettable leavers next to the mean for everyone else. Responded rows only
(non-responders carry no scores). n is printed on each leaver bar and the gap
in points sits above the pair.

Two extra charts:
  eng_reg_response_rate.png  — response rate by wave, leavers vs rest.
      response_flag=False is deliberate signal in this dataset, not noise.
  eng_reg_summary.png        — all eight dimensions side by side, pooled
      across waves.

Usage:  python build_engagement_reg.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
EDITED = HERE / "eddited_csv" / "attrition_reg.csv"
ENGAGEMENT = HERE / "original_csv" / "engagement.csv"
OUT_CSV = HERE / "eddited_csv" / "engagement_reg.csv"

LEAVER_C = "#C0392B"
REST_C = "#95A5A6"

# ---------------------------------------------------------------- build table
edited = pd.read_csv(EDITED)
eng = pd.read_csv(ENGAGEMENT)

reg_ids = edited["employee_id"].unique()
eng["is_regrettable"] = eng["employee_id"].isin(reg_ids)

eng_reg = eng[eng["is_regrettable"]].drop(columns="is_regrettable").copy()
eng_reg.to_csv(OUT_CSV, index=False)

matched = eng_reg["employee_id"].nunique()
print(f"engagement.csv:  {len(eng):,} rows")
print(f"edited.csv:      {len(reg_ids):,} regrettable leavers")
print(f"engagement_reg:  {len(eng_reg):,} rows / {matched:,} employees")
if matched < len(reg_ids):
    print(f"  note — {len(reg_ids) - matched} leavers never appear in the survey "
          f"(hired or exited outside the wave dates, or never sampled)")
print(f"Wrote {OUT_CSV.name}\n")

# fields after response_flag
DIMS = list(eng.columns[eng.columns.get_loc("response_flag") + 1:])
DIMS = [c for c in DIMS if c != "is_regrettable"]
WAVES = sorted(eng["wave_number"].unique())


def nice(col):
    return col.replace("_", " ").title()


def wave_chart(col):
    """Mean score per wave: regrettable leavers vs everyone else."""
    resp = eng[eng["response_flag"]]
    grp = resp.groupby(["wave_number", "is_regrettable"])[col]
    mean = grp.mean().unstack()
    n = grp.size().unstack()

    lm = mean.reindex(WAVES)[True].values
    rm = mean.reindex(WAVES)[False].values
    ln = n.reindex(WAVES)[True].fillna(0).values
    rn = n.reindex(WAVES)[False].fillna(0).values

    x = range(len(WAVES))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5.2))

    ax.bar([i - w / 2 for i in x], lm, w, color=LEAVER_C, zorder=3,
           label=f"Regrettable leavers (n={int(ln.sum()):,} responses)")
    ax.bar([i + w / 2 for i in x], rm, w, color=REST_C, zorder=3,
           label=f"Everyone else (n={int(rn.sum()):,} responses)")

    for i, (v, c) in enumerate(zip(lm, ln)):
        if pd.notna(v):
            ax.text(i - w / 2, v + 0.03, f"n={int(c)}", ha="center", va="bottom",
                    fontsize=8, color=LEAVER_C, fontweight="bold")
    for i, (a, b) in enumerate(zip(lm, rm)):
        if pd.notna(a) and pd.notna(b):
            d = a - b
            ax.text(i, max(a, b) + 0.16, f"{d:+.2f}", ha="center", va="bottom",
                    fontsize=9, color="#2C3E50",
                    fontweight="bold" if abs(d) >= 0.25 else "normal")

    ax.set_ylabel("Mean score (1–5)")
    ax.set_xlabel("Survey wave")
    ax.set_title(f"{nice(col)} — regrettable leavers vs rest of workforce",
                 fontsize=13, fontweight="bold", pad=14)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Wave {w_}" for w_ in WAVES])
    ax.set_ylim(0, 5.6)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    ax.grid(axis="y", alpha=0.25, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(0.0, -0.19, "Label above each pair = leaver mean minus rest. "
                        "Responded rows only.",
            transform=ax.transAxes, fontsize=8, color="#7F8C8D")

    fname = f"eng_reg_{col}.png"
    fig.tight_layout()
    fig.savefig(HERE / fname, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {fname}")


def response_rate_chart():
    """Share of sampled rows that were actually answered, by wave."""
    rate = (eng.groupby(["wave_number", "is_regrettable"])["response_flag"]
              .mean().unstack() * 100)
    n = eng.groupby(["wave_number", "is_regrettable"]).size().unstack()

    lr = rate.reindex(WAVES)[True].values
    rr = rate.reindex(WAVES)[False].values
    ln = n.reindex(WAVES)[True].fillna(0).values

    x = range(len(WAVES))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.bar([i - w / 2 for i in x], lr, w, color=LEAVER_C, zorder=3,
           label="Regrettable leavers")
    ax.bar([i + w / 2 for i in x], rr, w, color=REST_C, zorder=3,
           label="Everyone else")

    for i, (v, c) in enumerate(zip(lr, ln)):
        if pd.notna(v):
            ax.text(i - w / 2, v + 1.0, f"n={int(c)}", ha="center", va="bottom",
                    fontsize=8, color=LEAVER_C, fontweight="bold")
    for i, (a, b) in enumerate(zip(lr, rr)):
        if pd.notna(a) and pd.notna(b):
            ax.text(i, max(a, b) + 4.5, f"{a - b:+.1f}pp", ha="center", va="bottom",
                    fontsize=9, color="#2C3E50",
                    fontweight="bold" if abs(a - b) >= 5 else "normal")

    ax.set_ylabel("Response rate (%)")
    ax.set_xlabel("Survey wave")
    ax.set_title("Survey response rate — regrettable leavers vs rest",
                 fontsize=13, fontweight="bold", pad=14)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Wave {w_}" for w_ in WAVES])
    ax.set_ylim(0, 118)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    ax.grid(axis="y", alpha=0.25, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(0.0, -0.19, "Silence is signal: response_flag=False rows carry no "
                        "scores but still count in the denominator.",
            transform=ax.transAxes, fontsize=8, color="#7F8C8D")

    fig.tight_layout()
    fig.savefig(HERE / "eng_reg_response_rate.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  eng_reg_response_rate.png")


def summary_chart():
    """All eight dimensions, pooled across waves."""
    resp = eng[eng["response_flag"]]
    lm = [resp.loc[resp["is_regrettable"], c].mean() for c in DIMS]
    rm = [resp.loc[~resp["is_regrettable"], c].mean() for c in DIMS]

    order = sorted(range(len(DIMS)), key=lambda i: lm[i] - rm[i])
    cats = [nice(DIMS[i]) for i in order]
    lm = [lm[i] for i in order]
    rm = [rm[i] for i in order]

    x = range(len(cats))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.bar([i - w / 2 for i in x], lm, w, color=LEAVER_C, zorder=3,
           label="Regrettable leavers")
    ax.bar([i + w / 2 for i in x], rm, w, color=REST_C, zorder=3,
           label="Everyone else")

    for i, (a, b) in enumerate(zip(lm, rm)):
        d = a - b
        ax.text(i, max(a, b) + 0.10, f"{d:+.2f}", ha="center", va="bottom",
                fontsize=9, color="#2C3E50",
                fontweight="bold" if abs(d) >= 0.25 else "normal")

    ax.set_ylabel("Mean score (1–5), all waves pooled")
    ax.set_title("Engagement gap by dimension — regrettable leavers vs rest",
                 fontsize=13, fontweight="bold", pad=14)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats, rotation=20, ha="right")
    ax.set_ylim(0, 5.4)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    ax.grid(axis="y", alpha=0.25, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(0.0, -0.34, "Sorted worst gap first. Label = leaver mean minus rest.",
            transform=ax.transAxes, fontsize=8, color="#7F8C8D")

    fig.tight_layout()
    fig.savefig(HERE / "eng_reg_summary.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  eng_reg_summary.png")


print(f"Charting {len(DIMS)} dimensions after response_flag:")
for col in DIMS:
    wave_chart(col)
response_rate_chart()
summary_chart()

# ------------------------------------------------------------------- printout
resp = eng[eng["response_flag"]]
gap = pd.DataFrame({
    "leaver_mean": [resp.loc[resp["is_regrettable"], c].mean() for c in DIMS],
    "rest_mean": [resp.loc[~resp["is_regrettable"], c].mean() for c in DIMS],
}, index=DIMS)
gap["gap"] = gap["leaver_mean"] - gap["rest_mean"]
print("\nPooled gap (responded rows only):")
print(gap.sort_values("gap").round(3).to_string())
