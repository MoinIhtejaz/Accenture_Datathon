"""
charts_waves.py — survey wave-to-wave and "who goes quiet" figures.  -> charts_waves/

  s01  response rate across the five waves
  s02  alluvial: how everyone moves between responding, silent and gone
  s03  transition matrix — silence is sticky
  s04  dose response: exit rate by consecutive silent waves
  s05  raster: every person's five-wave response sequence
  s06  what they said in the wave BEFORE they went quiet
  s07  HiPos start as the most engaged responders and converge to everyone else
  s08  silent in their last survey: leavers vs stayers, and the lead time
"""
import warnings
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from pathlib import Path
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "charts_waves"
OUT.mkdir(exist_ok=True)
CSV = ROOT / "eddited_csv"

PURPLE, GREY, RED, TEAL, AMBER = "#A100FF", "#8C8C94", "#D9376E", "#00857D", "#E8A33D"
INK, LIGHT = "#2B2B33", "#F2F2F5"
mpl.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans", "font.size": 10.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#CCCCCC", "axes.labelcolor": "#333333",
    "xtick.color": "#555555", "ytick.color": "#555555",
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.titlepad": 34, "figure.facecolor": "white", "axes.facecolor": "white",
})
sub = lambda ax, t: ax.text(0, 1.012, t, transform=ax.transAxes, fontsize=9.5,
                            color="#666666", va="bottom")
note = lambda f, t: f.text(0.005, -0.04, t, fontsize=8.2, color="#777777",
                           ha="left", va="top", wrap=True)
def save(f, n):
    f.savefig(OUT / n); plt.close(f); print("  ", n)

ws = pd.read_csv(CSV / "wave_summary.csv")
panel = pd.read_csv(CSV / "wave_panel.csv", low_memory=False)
panel["wave_date"] = pd.to_datetime(panel.wave_date)
panel["exit_dt"] = pd.to_datetime(panel.exit_dt)
pats = pd.read_csv(CSV / "silence_patterns.csv")
dose = pd.read_csv(CSV / "silence_dose_response.csv")
prec = pd.read_csv(CSV / "silence_precursor.csv")
resp = panel[panel.state.isin(["responded", "silent"])]
WLAB = [f"W{r.wave}\n{pd.to_datetime(r.close_date):%b %Y}" for r in ws.itertuples()]

print("writing charts to charts_waves/")

# ═══════════════════════════════════════════════ s01 response rate by wave
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.0),
                              gridspec_kw={"width_ratios": [1.25, 1]})
x = ws.wave.values
ax.bar(x, ws.responded, color=PURPLE, alpha=.85, width=.6, label="Responded")
ax.bar(x, ws.silent, bottom=ws.responded, color=GREY, alpha=.45, width=.6, label="Silent")
for xi, r, s in zip(x, ws.responded, ws.silent):
    ax.text(xi, r / 2, f"{r:,}", ha="center", va="center", color="white",
            fontsize=9.5, fontweight="bold")
    ax.text(xi, r + s / 2, f"{s:,}", ha="center", va="center", color="#3A3A42", fontsize=9.5)
ax.set_xticks(x); ax.set_xticklabels(WLAB)
ax.set_ylabel("People surveyed")
ax.set_title("The silent block grows every wave")
sub(ax, "Survey invitations by wave, split by whether the person answered")
ax.legend(frameon=False, loc="upper right", ncols=2)
ax.set_ylim(0, 15600)

rr = ws.response_rate * 100
ax2.plot(x, rr, "-o", color=PURPLE, lw=2.6, ms=8)
for xi, v in zip(x, rr):
    ax2.annotate(f"{v:.1f}%", (xi, v), textcoords="offset points",
                 xytext=(0, 13) if xi in (1, 2, 4) else (0, -20),
                 ha="center", fontsize=10.5, fontweight="bold", color=PURPLE)
ax2.set_xticks(x); ax2.set_xticklabels([f"W{i}" for i in x])
ax2.set_ylim(79.4, 84.6); ax2.set_ylabel("Response rate (%)")
ax2.set_title("Down 3.4 points in 17 months")
sub(ax2, "Share of invited employees who answered")
ax2.annotate("", xy=(5.18, 80.3), xytext=(5.18, 83.6),
             arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=1.6, shrinkA=0, shrinkB=0))
ax2.text(5.30, 81.95, "−3.4 pts\n≈ 400 extra\nsilent people\nat wave 5", color=RED, fontsize=10,
         fontweight="bold", ha="left", va="center")
ax2.set_xlim(.55, 6.5)
note(fig, "Source: engagement.csv (55,971 person-waves). Denominator is everyone employed at the wave close date — "
          "invitation coverage is 99–100% of headcount in every wave, so the fall is real disengagement, not sampling.")
fig.tight_layout(); save(fig, "s01_response_rate_by_wave.png")

# ═══════════════════════════════════════════════ s02 alluvial (W1 cohort)
wide = panel.pivot_table(index="employee_id", columns="wave", values="state", aggfunc="first")
wide = wide.reindex(columns=[1, 2, 3, 4, 5])
coh = wide[wide[1].notna()].copy()          # everyone employed at wave 1
for w in [2, 3, 4, 5]:
    coh[w] = coh[w].fillna("left")
ORDER = ["responded", "silent", "left"]
COL = {"responded": PURPLE, "silent": RED, "left": "#C9C9D2"}
NAME = {"responded": "Responded", "silent": "Silent (did not answer)", "left": "Left the company"}

fig, ax = plt.subplots(figsize=(13.6, 6.6))
gap, barw = 420, 0.115
pos, tot = {}, len(coh)
for wi, w in enumerate([1, 2, 3, 4, 5]):
    counts = coh[w].value_counts()
    y = 0
    for st in ORDER:
        n = int(counts.get(st, 0))
        pos[(w, st)] = [y, y + n]
        if n:
            ax.add_patch(Rectangle((wi - barw / 2, y), barw, n, facecolor=COL[st],
                                   edgecolor="white", lw=.8, zorder=3))
            if n > 700:
                ax.text(wi, y + n / 2, f"{n:,}", ha="center", va="center", color="white",
                        fontsize=9.4, fontweight="bold", zorder=4)
            elif n > 120:
                ax.text(wi + barw / 2 + .04, y + n / 2, f"{n:,}", ha="left", va="center",
                        color="#555555", fontsize=8.8, zorder=4)
        y += n + gap

def ribbon(x0, x1, y0a, y0b, y1a, y1b, col, alpha):
    v = [(x0, y0a), ((x0 + x1) / 2, y0a), ((x0 + x1) / 2, y1a), (x1, y1a),
         (x1, y1b), ((x0 + x1) / 2, y1b), ((x0 + x1) / 2, y0b), (x0, y0b), (x0, y0a)]
    c = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
         MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(v, c), facecolor=col, edgecolor="none", alpha=alpha, zorder=1))

cur = {k: v[0] for k, v in pos.items()}
for wi, w in enumerate([1, 2, 3, 4]):
    ct = pd.crosstab(coh[w], coh[w + 1])
    for a in ORDER:
        if a not in ct.index:
            continue
        for b in ORDER:
            n = int(ct.loc[a, b]) if b in ct.columns else 0
            if n < 15:
                continue
            y0, y1 = cur[(w, a)], cur[(w + 1, b)]
            col = COL["left"] if b == "left" else (RED if b == "silent" else PURPLE)
            al = .60 if (a == "silent" and b == "silent") else (.28 if b == "silent" else
                 (.22 if b == "left" else .12))
            ribbon(wi + barw / 2, wi + 1 - barw / 2, y0, y0 + n, y1, y1 + n, col, al)
            cur[(w, a)] += n; cur[(w + 1, b)] += n

top = max(pos[(w, "left")][1] for w in [1, 2, 3, 4, 5])
ax.set_xlim(-.62, 4.72); ax.set_ylim(-300, top + 300)
ax.set_xticks(range(5)); ax.set_xticklabels(WLAB)
ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
ax.set_title("Silence is not a fixed group of people — it churns, and it grows")
sub(ax, f"The {tot:,} people employed at wave 1, followed through all five waves. Band height = headcount.")
ax.legend(handles=[Patch(facecolor=COL[s_], label=NAME[s_]) for s_ in ORDER],
          frameon=False, ncols=3, loc="upper left", bbox_to_anchor=(0, 1.085))
note(fig, "Fixed cohort, so nothing enters after wave 1 — the grey block only grows. The dark red ribbon is people "
          "silent in back-to-back waves; the pale red is responders newly going quiet. Each wave 15.6–17.7% of "
          "responders go quiet, and someone already quiet stays quiet 15.8% → 21.0% of the time.")
fig.tight_layout(); save(fig, "s02_alluvial_five_waves.png")

# ═══════════════════════════════════════════════ s03 transition heatmap
fig, axes = plt.subplots(1, 4, figsize=(13.6, 3.9), sharey=True)
for i, (w, ax) in enumerate(zip([1, 2, 3, 4], axes)):
    d = panel[panel.wave.isin([w, w + 1])]
    a = wide[w]; b = wide[w + 1]
    ok = a.isin(["responded", "silent"])
    bb = b.reindex(a.index).fillna("left")
    ct = pd.crosstab(a[ok], bb[ok], normalize="index").reindex(
        index=["responded", "silent"], columns=["responded", "silent", "left"]).fillna(0)
    im = ax.imshow(ct.values, cmap="Purples", vmin=0, vmax=.9, aspect="auto")
    for r in range(2):
        for c in range(3):
            v = ct.values[r, c]
            ax.text(c, r, f"{v*100:.1f}%", ha="center", va="center", fontsize=10.5,
                    fontweight="bold" if c == 1 else "normal",
                    color="white" if v > .5 else (RED if c == 1 else INK))
    ax.set_xticks(range(3)); ax.set_xticklabels(["Responds", "Silent", "Gone"], fontsize=9.5)
    ax.set_title(f"W{w} → W{w+1}", fontsize=11.5, pad=8)
    ax.set_xticks(np.arange(-.5, 3), minor=True); ax.set_yticks(np.arange(-.5, 2), minor=True)
    ax.grid(which="minor", color="white", lw=2); ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
axes[0].set_yticks([0, 1]); axes[0].set_yticklabels(["Responded\nlast wave", "Silent\nlast wave"], fontsize=9.5)
fig.suptitle("Silence is sticky — and the stickiness is getting worse", x=0.005, ha="left",
             fontsize=13, fontweight="bold", y=1.20)
fig.text(0.005, 1.115, "Where people go next, given where they were. Rows sum to 100%.",
         fontsize=9.5, color="#666666", ha="left")
note(fig, "A responder goes quiet next wave 15.6% → 17.7% of the time. Someone already quiet stays quiet 15.8% → 21.0% "
          "and leaves the company 3.6% → 5.6% — roughly double a responder's exit rate at every step.")
fig.tight_layout(); save(fig, "s03_transition_matrix.png")

# ═══════════════════════════════════════════════ s04 dose response
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.0),
                              gridspec_kw={"width_ratios": [1.15, 1]})
lab = dose.label.tolist(); v = dose.exit_rate.values * 100
cols = [GREY, "#F0A9C0", "#E46E93", RED]
b = ax.bar(range(4), v, color=cols, width=.62)
for i, (bb, r, n) in enumerate(zip(b, v, dose.person_waves)):
    ax.text(bb.get_x() + bb.get_width() / 2, r + .28, f"{r:.2f}%", ha="center",
            fontsize=11.5, fontweight="bold", color=INK)
    ax.text(bb.get_x() + bb.get_width() / 2, .22, f"n={n:,}", ha="center", fontsize=9,
            color="white" if i else "white")
ax.set_xticks(range(4)); ax.set_xticklabels(lab, fontsize=10)
ax.set_ylabel("Voluntary exit within 180 days (%)"); ax.set_ylim(0, 14)
ax.set_title("Each extra silent wave roughly doubles the chance they resign")
sub(ax, "Wave risk set: everyone employed at each wave close, followed 180 days")
ax.annotate("6.8× the\nbaseline", xy=(3, 12.11), xytext=(2.15, 12.6), fontsize=10.5,
            fontweight="bold", color=RED,
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.5))

grp = pats.groupby("n_silent", as_index=False).n.sum()
bal = panel.pivot_table(index="employee_id", columns="wave", values="state", aggfunc="first")
balc = bal.notna().all(axis=1)
ns = bal[balc].apply(lambda r: sum(v == "silent" for v in r), axis=1)
ex = panel.groupby("employee_id").exit_type.first().reindex(ns.index)
tab = pd.DataFrame({"n_silent": ns, "vol": (ex == "voluntary").astype(int)})
g = tab.groupby("n_silent").vol.agg(["mean", "size"])
ax2.plot(g.index, g["mean"] * 100, "-o", color=RED, lw=2.6, ms=8)
for i, (m, n) in zip(g.index, g.values):
    ax2.annotate(f"{m*100:.1f}%\n(n={int(n):,})", (i, m * 100), textcoords="offset points",
                 xytext=(0, 12), ha="center", fontsize=9.3, color=INK)
ax2.set_xlabel("Number of silent waves out of five"); ax2.set_ylabel("Voluntary exit rate (%)")
ax2.set_ylim(-2, 34); ax2.set_xticks(range(5))
ax2.set_title("Same picture at the person level")
sub(ax2, "Balanced panel: 9,248 people present at all five waves")
note(fig, "Left panel is the exposure-corrected view (person-waves, 180-day follow-up); linear-by-linear trend "
          "p = 1.1 × 10⁻⁵⁰. Right panel is a survivor cohort by construction — it only contains people still employed "
          "at wave 5, so its absolute rates are understated. Both point the same way.")
fig.tight_layout(); save(fig, "s04_dose_response.png")

# ═══════════════════════════════════════════════ s05 raster of sequences
seqs = bal[balc].apply(lambda r: "".join("S" if v == "silent" else "R" for v in r), axis=1)
def cls(p):
    if p == "RRRRR": return 0
    if p.count("S") == 1 and p.endswith("S"): return 3
    if p.count("S") == 1: return 1
    if p.endswith("S") and p.count("S") == len(p) - p.index("S"): return 3
    return 2
order = pd.DataFrame({"seq": seqs}); order["g"] = order.seq.map(cls)
order["nS"] = order.seq.str.count("S")
order = order.sort_values(["g", "nS", "seq"])
M = np.array([[1 if ch == "S" else 0 for ch in s] for s in order.seq])

fig, (ax, axb) = plt.subplots(1, 2, figsize=(13.2, 6.2),
                              gridspec_kw={"width_ratios": [1, 1.15]})
ax.imshow(M, aspect="auto", interpolation="nearest",
          cmap=mpl.colors.ListedColormap([LIGHT, RED]))
ax.set_xticks(range(5)); ax.set_xticklabels([f"W{i}" for i in range(1, 6)])
ax.set_ylabel("Employees (sorted by pattern)")
ax.set_yticks([0, len(M)]); ax.set_yticklabels(["0", f"{len(M):,}"])
ax.set_title("Every employee's five-wave silence pattern")
sub(ax, "One row per person; red = did not answer that wave")
edges = order.g.values
for gval, name in [(0, "Never silent  43.5%"), (1, "One-off skip  31.8%"),
                   (2, "In and out  15.0%"), (3, "Went quiet, stayed quiet  9.8%")]:
    idx = np.where(edges == gval)[0]
    if len(idx) == 0: continue
    ax.axhline(idx[-1] + .5, color="white", lw=1.6)
    ax.text(5.15, idx.mean(), name, fontsize=9.6, va="center", color=INK)

top = pats.head(10).iloc[::-1]
cmap = {"Never silent": GREY, "One-off skip": "#C9A0DC",
        "In and out": AMBER, "Went quiet and stayed quiet": RED}
axb.barh(range(len(top)), top.n, color=[cmap[g] for g in top.group], height=.72)
axb.set_yticks(range(len(top)))
axb.set_yticklabels([f"{p}" for p in top.pattern], fontfamily="DejaVu Sans Mono", fontsize=10.5)
for i, (n, pc) in enumerate(zip(top.n, top.pct)):
    axb.text(n + 60, i, f"{n:,}  ({pc*100:.1f}%)", va="center", fontsize=9.6, color=INK)
axb.set_xlim(0, 4900); axb.set_xlabel("People")
axb.set_title("The ten most common sequences")
sub(axb, "R = responded, S = silent, wave 1 on the left")
axb.legend(handles=[Patch(facecolor=c, label=k) for k, c in cmap.items()],
           frameon=False, fontsize=9, loc="lower right")
note(fig, "Balanced panel of 9,248 people surveyed in all five waves. Only 43.5% answered every time. The 9.8% who went "
          "quiet and never came back are the group worth a conversation — but note this cohort excludes anyone who had "
          "already left by wave 5, so it understates the terminal-silence group.")
fig.tight_layout(); save(fig, "s05_sequence_raster.png")

# ═══════════════════════════════════════════════ s06 precursor
fig, ax = plt.subplots(figsize=(12.4, 5.6))
p6 = prec[prec.dimension != "overall"].sort_values("diff")
y = np.arange(len(p6))
for i, r in enumerate(p6.itertuples()):
    ax.plot([r.mean_stayed, r.mean_went_quiet], [i, i], color="#CCCCCC", lw=2.4, zorder=1)
ax.scatter(p6.mean_stayed, y, s=90, color=PURPLE, zorder=3, label="Kept responding")
ax.scatter(p6.mean_went_quiet, y, s=90, color=RED, zorder=3, label="Went quiet next wave")
ax.set_yticks(y); ax.set_yticklabels([d.replace("_", " ").title() for d in p6.dimension])
ax.set_xlabel("Mean score in the wave before (1–5)")
ax.set_title("What people said in the last survey they answered")
sub(ax, "Scores at wave k, split by whether the same person answered wave k+1  ·  n = 6,063 vs 29,208")
ax.legend(frameon=False, loc="upper left", ncols=2, bbox_to_anchor=(0, 1.115))
for i, r in enumerate(p6.itertuples()):
    star = "***" if r.p < .001 else ("**" if r.p < .01 else ("*" if r.p < .05 else "n.s."))
    ax.text(3.412, i, f"Δ {r.diff:+.3f}  {star}", fontsize=9.3,
            color=RED if r.p < .05 else "#999999", va="center")
ax.set_xlim(3.295, 3.452)
note(fig, "Only two dimensions separate the people about to go quiet: senior leadership trust (Δ −0.059, p = 1×10⁻⁵) and "
          "purpose & meaning (Δ −0.042, p = 0.002). Both effect sizes are tiny (Cohen's d ≈ 0.06) — the scores are "
          "close to useless as an individual early warning. The act of not answering carries far more signal than "
          "anything written on the form. *** p<0.001, ** p<0.01, * p<0.05.")
fig.tight_layout(); save(fig, "s06_precursor_scores.png")

# ═══════════════════════════════════════════════ s07 HiPo convergence
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.0))
sr = resp.groupby(["wave", "hipo_flag"]).state.apply(lambda s: (s == "silent").mean()).unstack()
ax.plot(sr.index, sr[False] * 100, "-o", color=GREY, lw=2.5, ms=7.5, label="Everyone else")
ax.plot(sr.index, sr[True] * 100, "-o", color=PURPLE, lw=2.8, ms=8.5, label="HiPo")
for w in sr.index:
    off = (0, -18) if w in (1, 2) else (0, 12)
    ax.annotate(f"{sr.loc[w, True]*100:.1f}%", (w, sr.loc[w, True] * 100),
                textcoords="offset points", xytext=off, ha="center",
                fontsize=9.6, color=PURPLE, fontweight="bold")
ax.set_xticks(sr.index); ax.set_xticklabels([f"W{i}" for i in sr.index])
ax.set_ylabel("Silence rate (%)"); ax.set_ylim(9, 23)
ax.legend(frameon=False, ncols=2, loc="lower right")
ax.set_title("HiPos were the most engaged group — then they weren't")
sub(ax, "Share not answering, by wave")
ax.annotate("", xy=(4.92, 19.1), xytext=(1.08, 12.4),
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6, connectionstyle="arc3,rad=-.18"))
ax.text(2.35, 14.6, "+7.3 pts\np = 1.5 × 10⁻⁵", color=RED, fontsize=10.5, fontweight="bold",
        ha="center")

hz = pd.read_csv(CSV / "silence_exit_hazard.csv")
h = hz[hz.outcome == "exit_180"]
yy = np.arange(len(h))
ax2.errorbar(h.odds_ratio, yy, xerr=[h.odds_ratio - h.ci_lo, h.ci_hi - h.odds_ratio],
             fmt="o", color=RED, ms=9, lw=2, capsize=5)
ax2.axvline(1, color=GREY, ls="--", lw=1.3)
ax2.set_yticks(yy); ax2.set_yticklabels(h.population)
ax2.set_xlabel("Odds ratio: silent vs responded")
ax2.set_title("Silence predicts resignation in every group")
sub(ax2, "Voluntary exit within 180 days  ·  95% CI")
for i, r in enumerate(h.itertuples()):
    ex = int(np.floor(np.log10(r.p_value)))
    mant = r.p_value / 10 ** ex
    sup = str(abs(ex)).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
    ax2.text(r.ci_hi + .06, i, f"OR {r.odds_ratio:.2f}   p = {mant:.1f} × 10⁻{sup}",
             va="center", fontsize=9.4, color=INK)
ax2.set_xlim(.8, 3.7)
note(fig, "The HiPo effect is weaker than the population effect (OR 1.62 vs 2.17) but is measured on far fewer "
          "person-waves (4,893). Silence also predicts involuntary exit at OR 2.29 — it is a disengagement marker, "
          "not a resignation marker. Stated openly rather than left to be found.")
fig.tight_layout(); save(fig, "s07_hipo_convergence.png")

# ═══════════════════════════════════════════════ s08 last survey before exit + lead time
lv = panel[(panel.exit_type == "voluntary") & panel.state.isin(["responded", "silent"])]
lv = lv[lv.wave_date < lv.exit_dt]
last = lv.sort_values("wave").groupby("employee_id").tail(1)
stay = panel[panel.exit_dt.isna() & panel.state.isin(["responded", "silent"])] \
    .sort_values("wave").groupby("employee_id").tail(1)

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.0))
vals = [(stay.state == "silent").mean() * 100, (last.state == "silent").mean() * 100]
b = ax.bar([0, 1], vals, color=[GREY, RED], width=.5)
for bb, v, n in zip(b, vals, [len(stay), len(last)]):
    ax.text(bb.get_x() + bb.get_width() / 2, v + .7, f"{v:.1f}%", ha="center",
            fontsize=14, fontweight="bold", color=INK)
    ax.text(bb.get_x() + bb.get_width() / 2, 1.2, f"n = {n:,}", ha="center",
            fontsize=9.5, color="white")
ax.set_xticks([0, 1]); ax.set_xticklabels(["Still employed", "Resigned"])
ax.set_ylabel("Silent in their final survey (%)"); ax.set_ylim(0, 42)
ax.set_title("A third of resignations were already silent")
sub(ax, "State at the last survey each person was present for")
ct = np.array([[(last.state == "silent").sum(), (last.state == "responded").sum()],
               [(stay.state == "silent").sum(), (stay.state == "responded").sum()]])
pv = stats.chi2_contingency(ct)[1]
ax.text(.5, 38.5, f"33.1% vs 19.5%   p = {pv:.1e}".replace("e-", " × 10⁻"), ha="center",
        fontsize=10.5, color=RED, fontweight="bold")

lv2 = lv.sort_values(["employee_id", "wave"])
def lead(g):
    g = g.sort_values("wave")
    if g.iloc[-1].state != "silent":
        return np.nan
    run = 0
    for s in g.state.values[::-1]:
        if s == "silent":
            run += 1
        else:
            break
    f = g.iloc[len(g) - run]
    return (f.exit_dt - f.wave_date).days
ld = lv2.groupby("employee_id").apply(lead).dropna()
ax2.hist(ld, bins=np.arange(0, 380, 20), color=RED, alpha=.75, edgecolor="white")
ax2.axvline(ld.median(), color=INK, lw=2, ls="--")
ax2.text(ld.median() + 8, ax2.get_ylim()[1] * .92, f"median {ld.median():.0f} days",
         fontsize=10.5, fontweight="bold", color=INK)
ax2.set_xlabel("Days from first wave of the final silent run to resignation")
ax2.set_ylabel("Leavers")
ax2.set_title("The warning arrives about three months out")
sub(ax2, f"n = {len(ld)} voluntary leavers whose last survey was a non-response")
note(fig, "This is the operational case for the trigger: for a third of resignations there is a dated, machine-readable "
          "signal a median 84 days (IQR 40–146) before the resignation letter. It is not a prediction of who will "
          "leave — it is a list of who to talk to, arriving early enough to act on.")
fig.tight_layout(); save(fig, "s08_final_survey_and_leadtime.png")

print("done")
