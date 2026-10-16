"""Regrettable-exit RATE by department: exits per 1,000 employees.
One bar per department, no comparison bar needed - the denominator is baked in.
"""
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
e = pd.read_csv(HERE/"original_csv"/"employees.csv")
reg = set(pd.read_csv(HERE/"eddited_csv"/"attrition_reg.csv").employee_id)
e["is_reg"] = e.employee_id.isin(reg)

t = e.groupby("department").agg(hc=("employee_id","size"), reg=("is_reg","sum"))
t["rate"] = t.reg / t.hc * 1000
t = t.sort_values("rate", ascending=True)
bank = t.reg.sum() / t.hc.sum() * 1000

fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#C0392B" if r > bank else "#95A5A6" for r in t.rate]
ax.barh(t.index, t.rate, color=colors, zorder=3)
for i, (r, n, hc) in enumerate(zip(t.rate, t.reg, t.hc)):
    ax.text(r + 0.15, i, f"{r:.1f}   ({n} of {hc:,})", va="center", fontsize=9.5)
ax.axvline(bank, color="#2C3E50", ls="--", lw=1.4, zorder=4)
ax.text(bank, len(t)-0.35, f" bank average {bank:.1f}", color="#2C3E50",
        fontsize=9, fontweight="bold")
ax.set_xlabel("Regrettable exits per 1,000 employees")
ax.set_title("Which departments actually lose their best people?",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlim(0, t.rate.max()*1.42)
ax.grid(axis="x", alpha=0.25, zorder=0)
for s in ("top","right","left"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(HERE/"reg_department_rate.png", dpi=200, bbox_inches="tight")
print(t.round(1).to_string()); print(f"bank average {bank:.1f}")
