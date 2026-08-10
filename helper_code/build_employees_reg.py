"""
Build employees_reg.csv — the employees.csv rows for the regrettable leavers
listed in edited.csv — and draw bar charts of department, age band and
originating legacy entity.

Each chart shows the regrettable leavers' share side by side with the
workforce share, because raw counts alone just track how big each group is.
Counts are printed on the leaver bars; the over/under-representation index
(leaver share / workforce share) sits above each pair.

Usage:  python build_employees_reg.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
EDITED = HERE / "eddited_csv" / "attrition_reg.csv"
EMPLOYEES = HERE / "original_csv" / "employees.csv"
OUT_CSV = HERE / "eddited_csv" / "employees_reg.csv"

LEAVER_C = "#C0392B"
STAFF_C = "#95A5A6"

# ---------------------------------------------------------------- build table
edited = pd.read_csv(EDITED)
employees = pd.read_csv(EMPLOYEES)

reg_ids = edited["employee_id"].unique()
employees_reg = employees[employees["employee_id"].isin(reg_ids)].copy()

missing = set(reg_ids) - set(employees_reg["employee_id"])
print(f"edited.csv:      {len(edited):,} rows ({len(reg_ids):,} unique employees)")
print(f"employees_reg:   {len(employees_reg):,} rows")
if missing:
    print(f"  WARNING — {len(missing)} ids in edited.csv not found in employees.csv: "
          f"{sorted(missing)[:10]}")
else:
    print("  all ids matched")

# carry the exit detail across so the file is self-contained
employees_reg = employees_reg.merge(
    edited.drop(columns=[c for c in edited.columns
                         if c in employees_reg.columns and c != "employee_id"]),
    on="employee_id",
    how="left",
)
employees_reg.to_csv(OUT_CSV, index=False)
print(f"Wrote {OUT_CSV.name}  ({employees_reg.shape[0]} rows x {employees_reg.shape[1]} cols)\n")

# ------------------------------------------------------------------- charting
workforce = employees  # everyone on the books in the window


def bar_chart(column, title, filename, order=None, rotate=20):
    """Grouped bar: regrettable-leaver share vs workforce share for `column`."""
    leaver_n = employees_reg[column].value_counts()
    leaver_pct = leaver_n / leaver_n.sum() * 100
    staff_pct = workforce[column].value_counts(normalize=True) * 100

    cats = order if order else leaver_n.sort_values(ascending=False).index.tolist()
    cats = [c for c in cats if c in leaver_pct.index]

    lp = leaver_pct.reindex(cats).values
    sp = staff_pct.reindex(cats).values
    ln = leaver_n.reindex(cats).values
    idx = lp / sp

    x = range(len(cats))
    w = 0.38
    fig, ax = plt.subplots(figsize=(max(7, len(cats) * 1.25), 5.2))

    ax.bar([i - w / 2 for i in x], lp, w, label=f"Regrettable leavers (n={int(ln.sum())})",
           color=LEAVER_C, zorder=3)
    ax.bar([i + w / 2 for i in x], sp, w, label=f"All employees (n={len(workforce):,})",
           color=STAFF_C, zorder=3)

    for i, (v, n) in enumerate(zip(lp, ln)):
        ax.text(i - w / 2, v + 0.4, f"{int(n)}", ha="center", va="bottom",
                fontsize=9, color=LEAVER_C, fontweight="bold")
    for i, (v, r) in enumerate(zip(lp, idx)):
        top = max(v, sp[i])
        ax.text(i, top + 2.6, f"{r:.2f}x", ha="center", va="bottom", fontsize=9,
                color="#2C3E50",
                fontweight="bold" if (r >= 1.25 or r <= 0.8) else "normal")

    ax.set_ylabel("Share of group (%)")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats, rotation=rotate, ha="right" if rotate else "center")
    ax.set_ylim(0, max(max(lp), max(sp)) * 1.28)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(0.0, -0.30, "Label above each pair = over/under-representation index "
                        "(leaver share ÷ workforce share).",
            transform=ax.transAxes, fontsize=8, color="#7F8C8D")

    fig.tight_layout()
    fig.savefig(HERE / filename, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {filename}")


AGE_ORDER = ["18-24", "25-29", "30-34", "35-39", "40-44",
             "45-49", "50-54", "55-59", "60+"]

print("Charts:")
bar_chart("department", "Regrettable leavers by department", "reg_department.png")
bar_chart("age_band", "Regrettable leavers by age band", "reg_age_band.png",
          order=AGE_ORDER, rotate=0)
bar_chart("legacy_entity_code", "Regrettable leavers by originating entity",
          "reg_legacy_entity.png", rotate=0)
