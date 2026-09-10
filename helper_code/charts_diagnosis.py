"""
charts_diagnosis.py — one figure per surviving finding, plus two figures showing the
artefacts we had to discard. Written to charts_diagnosis/.
"""
import warnings
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "charts_diagnosis"
OUT.mkdir(exist_ok=True)

PURPLE, GREY, RED, TEAL, AMBER = "#A100FF", "#8C8C94", "#D9376E", "#00857D", "#E8A33D"
mpl.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans", "font.size": 10.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#CCCCCC", "axes.labelcolor": "#333333",
    "xtick.color": "#555555", "ytick.color": "#555555",
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.titlepad": 34, "figure.facecolor": "white", "axes.facecolor": "white",
})

e = pd.read_csv(ROOT / "eddited_csv" / "master_plus.csv", low_memory=False)
rs = pd.read_csv(ROOT / "eddited_csv" / "wave_risk_set.csv", low_memory=False)
pr = pd.read_csv(ROOT / "eddited_csv" / "review_risk_set.csv", low_memory=False)
e["promo_rate"] = e["n_promo_rec"] / e["n_reviews"].replace(0, np.nan)
DIMS = ["career_development", "recognition", "manager_effectiveness", "psychological_safety",
        "senior_leadership_trust", "purpose_meaning", "wellbeing", "confidence_in_role_future"]


def sub(ax, txt):
    ax.text(0, 1.012, txt, transform=ax.transAxes, fontsize=9.5, color="#666666", va="bottom")


def note(fig, txt):
    fig.text(0.005, -0.035, txt, fontsize=8.2, color="#777777", ha="left", va="top", wrap=True)


def save(fig, name):
    fig.savefig(OUT / name)
    plt.close(fig)
    print("  ", name)


print("writing charts to charts_diagnosis/")

# ═════════════════════════════════════════════ 01 the headline gap
fig, ax = plt.subplots(figsize=(7.2, 4.2))
rates = [e[e.hipo == 0].voluntary.mean(), e[e.hipo == 1].voluntary.mean()]
ns = [(e.hipo == 0).sum(), (e.hipo == 1).sum()]
ci = [1.96 * np.sqrt(r * (1 - r) / n) for r, n in zip(rates, ns)]
b = ax.bar(["Not flagged HiPo", "Flagged HiPo"], rates, color=[GREY, PURPLE], width=.5,
           yerr=ci, capsize=6, error_kw=dict(ecolor="#444", lw=1.2))
for bar, r, n in zip(b, rates, ns):
    ax.text(bar.get_x() + bar.get_width()/2, r + .012, f"{r:.1%}", ha="center",
            fontweight="bold", fontsize=13)
    ax.text(bar.get_x() + bar.get_width()/2, .004, f"n = {n:,}", ha="center",
            color="white", fontsize=9)
ax.set_ylim(0, .17); ax.set_ylabel("Voluntary exit rate, 2024–25")
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
ax.set_title("HiPos leave 1.55× more often than everyone else")
sub(ax, "Odds ratio 1.63 [1.35–1.98], Fisher exact p = 5.5 × 10⁻⁷ · 151 of 1,210 HiPos left voluntarily")
note(fig, "Source: employees.csv + attrition_log.csv, n = 13,403. Bars show 95% CI.")
save(fig, "d01_hipo_gap.png")

# ═════════════════════════════════════════════ 02 THE headline: silence beats scores
fig, ax = plt.subplots(figsize=(8.2, 4.6))
d = rs.copy()
q25 = d.loc[d.nonresponse == 0, "eng_index"].quantile(.25)
groups = {
    "Answered the survey,\nscored in the top 75%": d[(d.nonresponse == 0) & (d.eng_index >= q25)],
    "Answered the survey,\nscored in the bottom 25%": d[(d.nonresponse == 0) & (d.eng_index < q25)],
    "Did not answer\nthe survey at all": d[d.nonresponse == 1],
}
vals = [g.exit_180.mean() for g in groups.values()]
nn = [len(g) for g in groups.values()]
cis = [1.96 * np.sqrt(v * (1 - v) / n) for v, n in zip(vals, nn)]
cols = [GREY, AMBER, RED]
b = ax.bar(list(groups), vals, color=cols, width=.55, yerr=cis, capsize=6,
           error_kw=dict(ecolor="#444", lw=1.2))
for bar, v, n in zip(b, vals, nn):
    ax.text(bar.get_x() + bar.get_width()/2, v + .0016, f"{v:.2%}", ha="center",
            fontweight="bold", fontsize=13)
    ax.text(bar.get_x() + bar.get_width()/2, .0008, f"n = {n:,}", ha="center",
            color="white", fontsize=9)
ax.axhline(vals[0], ls=":", color="#999", lw=1)
ax.annotate("", xy=(2.42, vals[2]), xytext=(2.42, vals[0]),
            arrowprops=dict(arrowstyle="<->", color=RED, lw=1.6))
ax.plot([2.28, 2.46], [vals[2]]*2, color=RED, lw=1, ls=":")
ax.text(2.50, (vals[0] + vals[2]) / 2, "2.3×", color=RED, fontweight="bold", fontsize=13,
        va="center")
ax.set_xlim(-0.6, 2.85)
ax.set_ylim(0, .049); ax.set_ylabel("Left voluntarily within 180 days")
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
ax.set_title("A blank survey predicts the exit. A bad score barely does.")
sub(ax, "Silence vs answered: OR 2.24 [1.98–2.54], p = 8.7 × 10⁻³⁷ · Low score vs good score: 2.04% vs 1.65%")
note(fig, "Discrete-time risk set: 55,939 person-waves across 5 survey waves. Everyone in a row was "
          "employed on the survey date and had the same 180-day look-ahead.")
save(fig, "d02_silence_beats_scores.png")

# ═════════════════════════════════════════════ 03 silence lead time
fig, ax = plt.subplots(figsize=(7.6, 4.4))
hor = [90, 180, 270, 365]
for lab, mask, col, mk in [("All staff", slice(None), PURPLE, "o"),
                           ("HiPos only", rs.hipo == 1, RED, "s")]:
    d = rs if isinstance(mask, slice) else rs[mask]
    ors, los, his = [], [], []
    for h in hor:
        d2 = d.copy()
        d2["ev"] = ((d2.voluntary == 1) & (d2.days_to_exit <= h)).astype(int)
        ct = pd.crosstab(d2.nonresponse, d2.ev).values
        o, _ = stats.fisher_exact(ct)
        a, bb, c, dd = ct.ravel()
        se = np.sqrt(1/a + 1/bb + 1/c + 1/dd)
        ors.append(o); los.append(np.exp(np.log(o) - 1.96*se)); his.append(np.exp(np.log(o) + 1.96*se))
    ax.errorbar(hor, ors, yerr=[np.array(ors)-np.array(los), np.array(his)-np.array(ors)],
                marker=mk, color=col, capsize=5, lw=2, ms=8, label=lab)
ax.axhline(1, color="#999", ls="--", lw=1)
ax.text(370, 1.02, "no effect", color="#999", fontsize=9)
ax.set_xticks(hor); ax.set_xlabel("Look-ahead window after the survey (days)")
ax.set_ylabel("Odds ratio for voluntary exit")
ax.set_title("Silence is an early warning, not a resignation echo")
sub(ax, "The signal is already there a full year out — it is not just people on notice skipping the survey")
ax.legend(frameon=False)
note(fig, "Waves inside a 90-day notice window were also tested separately: silence 90–365 days ahead of "
          "exit still gives OR 2.07 (p = 1.7 × 10⁻³²) for all staff and 1.50 (p = 0.022) for HiPos.")
save(fig, "d03_silence_lead_time.png")

# ═════════════════════════════════════════════ 04 engagement dimensions are flat for HiPo
fig, ax = plt.subplots(figsize=(8.4, 5.0))
rows = []
for pop, lab, col in [(rs[rs.hipo == 1], "HiPos", RED), (rs, "All staff", PURPLE)]:
    a_ = pop[pop.response_flag == True]
    for dm in DIMS:
        g1 = a_.loc[a_.exit_180 == 1, dm].dropna(); g0 = a_.loc[a_.exit_180 == 0, dm].dropna()
        sp = np.sqrt(((len(g1)-1)*g1.var(ddof=1) + (len(g0)-1)*g0.var(ddof=1)) / (len(g1)+len(g0)-2))
        dd_ = (g1.mean() - g0.mean()) / sp
        se = np.sqrt(1/len(g1) + 1/len(g0) + dd_**2/(2*(len(g1)+len(g0))))
        rows.append(dict(pop=lab, dim=dm, d=dd_, lo=dd_-1.96*se, hi=dd_+1.96*se, col=col))
F = pd.DataFrame(rows)
order = F[F.pop == "All staff"].sort_values("d")["dim"].tolist() if False else \
        F[F["pop"] == "All staff"].sort_values("d")["dim"].tolist()
ypos = {dm: i for i, dm in enumerate(order)}
for _, r in F.iterrows():
    off = .18 if r["pop"] == "HiPos" else -.18
    ax.errorbar(r["d"], ypos[r["dim"]] + off, xerr=[[r["d"]-r["lo"]], [r["hi"]-r["d"]]],
                fmt="o", color=r["col"], capsize=3, ms=6, lw=1.6)
ax.axvline(0, color="#666", lw=1.2)
ax.set_yticks(range(len(order)))
ax.set_yticklabels([o.replace("_", " ").title() for o in order])
ax.set_xlabel("Standardised gap between leavers and stayers (Hedges' g)")
ax.set_title("For HiPos, not one survey dimension separates leavers from stayers")
sub(ax, "Every red interval crosses zero. Career development — the intuitive culprit — is g = −0.01.")
ax.legend(handles=[Patch(color=RED, label="HiPos (110 exits)"),
                   Patch(color=PURPLE, label="All staff (798 exits)")],
          frameon=False, loc="lower right", fontsize=9)
ax.set_xlim(-0.40, 0.30)
ax.text(-0.385, len(order) - 0.35, "← leavers scored lower", fontsize=8.5, color="#999")
ax.text(0.06, len(order) - 0.35, "leavers scored higher →", fontsize=8.5, color="#999")
ax.set_ylim(-0.9, len(order) - 0.1)
note(fig, "Same risk set as fig d02, responders only. For all staff, senior leadership trust "
          "(g = −0.15) and purpose (g = −0.13) clear FDR correction; the effects are small and none "
          "of them survive in the HiPo subgroup.")
save(fig, "d04_engagement_flat_for_hipo.png")

# ═════════════════════════════════════════════ 05 promotion block, exposure-fair
fig, ax = plt.subplots(figsize=(8.0, 4.4))
pr["rating_num"] = pr["performance_rating"].map(
    {"Unsatisfactory": 1, "Below Expectations": 2, "Meets Expectations": 3,
     "High Performer": 4, "Outstanding": 5})
defs = [("HiPo-flagged", pr.hipo == 1), ("Not HiPo-flagged", pr.hipo == 0),
        ("Rated High Performer +", pr.rating_num >= 4), ("Rated Outstanding", pr.rating_num == 5)]
labs, ors, los, his, ps = [], [], [], [], []
for name, mask in defs:
    s = pr[mask]
    ct = pd.crosstab(s.no_promo, s.exit_180).values
    o, p = stats.fisher_exact(ct)
    a, bb, c, dd_ = ct.ravel(); se = np.sqrt(1/a + 1/bb + 1/c + 1/dd_)
    labs.append(name); ors.append(o); ps.append(p)
    los.append(np.exp(np.log(o)-1.96*se)); his.append(np.exp(np.log(o)+1.96*se))
y = np.arange(len(labs))[::-1]
cols = [RED if p < .05 else GREY for p in ps]
for yy, o, lo_, hi_, cc in zip(y, ors, los, his, cols):
    ax.errorbar([o], [yy], xerr=[[o-lo_], [hi_-o]], fmt="none", ecolor=cc, capsize=5, lw=2)
ax.scatter(ors, y, color=cols, s=80, zorder=3)
for yy, o, p in zip(y, ors, ps):
    ax.text(2.72, yy, f"OR {o:.2f}   p = {p:.3f}", va="center", fontsize=9.5,
            color="#333" if p < .05 else "#999")
ax.axvline(1, color="#666", ls="--", lw=1.2)
ax.set_yticks(y); ax.set_yticklabels(labs); ax.set_xlim(.55, 3.9)
ax.set_xlabel("Odds of leaving within 180 days of a review with no promotion recommendation")
ax.set_title("Being passed over only moves the needle for HiPos")
sub(ax, "Review-level risk set, 34,979 reviews — every review carries the same 180-day look-ahead")
note(fig, "This replaces the 'ever recommended' comparison in findings_04, which was exposure-biased: "
          "a 2024 leaver had one chance at a recommendation, a stayer had three. Fixing that shrinks "
          "the effect from 2.1× to 1.63× and confines it to the HiPo group.")
save(fig, "d05_promotion_block.png")

# ═════════════════════════════════════════════ 06 the exposure bias itself
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.2))
g = e.assign(grp=np.where(e.status == "active", "Still here",
                          np.where(pd.to_datetime(e.exit_dt).dt.year == 2024,
                                   "Left in 2024", "Left in 2025")))
o = ["Left in 2024", "Left in 2025", "Still here"]
m1 = g.groupby("grp")["n_reviews"].mean().reindex(o)
m2 = g.groupby("grp")["waves_offered"].mean().reindex(o)
for ax, m, t, ylab in [(ax1, m1, "Performance reviews on file", "mean reviews"),
                       (ax2, m2, "Survey waves they were present for", "mean waves")]:
    b = ax.bar(o, m.values, color=[RED, AMBER, GREY], width=.55)
    for bar, v in zip(b, m.values):
        ax.text(bar.get_x()+bar.get_width()/2, v+.05, f"{v:.2f}", ha="center", fontweight="bold")
    ax.set_title(t, fontsize=11.5, pad=10); ax.set_ylabel(ylab)
    ax.tick_params(axis="x", labelsize=9.5)
fig.suptitle("Why 'leavers had fewer promotion recommendations' is not a finding",
             x=.005, ha="left", fontsize=13, fontweight="bold", y=1.10)
note(fig, "Someone who left in March 2024 could physically only appear in one review cycle. Any metric "
          "counted per person rather than per opportunity will make leavers look neglected. "
          "Normalising to recommendations per review, the all-staff gap drops to p = 0.26.")
save(fig, "d06_exposure_bias.png")

# ═════════════════════════════════════════════ 07 department gradient
fig, ax = plt.subplots(figsize=(8.6, 4.6))
h = e[e.hipo == 1]
dep = h.groupby("department").agg(rate=("voluntary", "mean"), n=("employee_id", "size"),
                                  ex=("voluntary", "sum")).sort_values("rate")
ci = 1.96*np.sqrt(dep["rate"]*(1-dep["rate"])/dep["n"])
cols = [RED if r > .14 else (AMBER if r > .10 else GREY) for r in dep["rate"]]
ax.barh(dep.index, dep["rate"], color=cols, height=.6, xerr=ci, capsize=4,
        error_kw=dict(ecolor="#555", lw=1))
for i, (idx, r) in enumerate(dep.iterrows()):
    ax.text(r["rate"]+ci.iloc[i]+.005, i, f"{r['rate']:.1%}   ({int(r['ex'])} of {int(r['n'])})",
            va="center", fontsize=9.5)
ax.axvline(h.voluntary.mean(), color=PURPLE, ls="--", lw=1.4)
ax.text(h.voluntary.mean()+.004, 6.35, f"HiPo average {h.voluntary.mean():.1%}",
        color=PURPLE, fontsize=9, va="center")
ax.set_ylim(-0.6, 6.9)
ax.set_xlim(0, .30); ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
ax.set_xlabel("HiPo voluntary exit rate, 2024–25")
ax.set_title("A HiPo in Corporate Operations is 3× more likely to leave than one in Retail Banking")
sub(ax, "χ²(6) = 21.6, p = 0.0014 · adjusted OR vs Retail Banking: Corp Ops 3.09 (p = 0.0003), Risk & Compliance 2.92 (p = 0.0002)")
note(fig, "Adjusted for tenure, compa-ratio, role level and hire source. None of pay, tenure, span, "
          "days-to-fill, promotion rate, engagement or acquisition history correlates with this "
          "gradient (all |r| < 0.55, p > 0.20) — the cause is not in the four files.")
save(fig, "d07_department_gradient.png")

# ═════════════════════════════════════════════ 08 tenure shape
fig, ax = plt.subplots(figsize=(8.2, 4.4))
e["tb"] = pd.cut(e.tenure_years, [0, 1, 2, 3, 5, 10, 100],
                 labels=["<1y", "1–2y", "2–3y", "3–5y", "5–10y", "10y+"])
t = e.pivot_table(index="tb", columns="hipo", values="voluntary", aggfunc="mean", observed=True)
n = e.pivot_table(index="tb", columns="hipo", values="voluntary", aggfunc="size", observed=True)
x = np.arange(len(t))
ax.bar(x-.19, t[0], .36, label="Not HiPo", color=GREY)
ax.bar(x+.19, t[1], .36, label="HiPo", color=PURPLE)
for i in range(len(t)):
    ax.text(x[i]+.19, t[1].iloc[i]+.006, f"{t[1].iloc[i]:.1%}", ha="center", fontsize=9,
            fontweight="bold", color=PURPLE)
    ax.text(x[i]-.19, t[0].iloc[i]+.006, f"{t[0].iloc[i]:.1%}", ha="center", fontsize=9, color="#666")
for i, lab, dx in [(1, "OR 2.24\np = 0.002", .80), (5, "OR 1.70\np = 0.0003", -.62)]:
    ax.annotate(lab, xy=(x[i]+.19+np.sign(dx)*.18, t[1].iloc[i]+.004),
                xytext=(x[i]+dx, t[1].iloc[i]+.062),
                fontsize=8.5, color=RED, ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.2,
                                connectionstyle="arc3,rad=0.2"))
ax.set_xticks(x); ax.set_xticklabels(t.index); ax.set_ylim(0, .31)
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
ax.set_ylabel("Voluntary exit rate"); ax.set_xlabel("Tenure")
ax.set_title("Two windows where HiPos go: the second year, and the long-service tail")
sub(ax, "The 2–3 year band is the quietest in the company for both groups — the risk is not linear in tenure")
ax.legend(frameon=False)
note(fig, "The formal hipo × tenure-band interaction is not significant (LR = 6.17, df = 5, p = 0.29), "
          "so read this as where the volume sits, not as proof that the shape differs by HiPo status.")
save(fig, "d08_tenure_shape.png")

# ═════════════════════════════════════════════ 09 the pay paradox
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.3))
a = e.loc[(e.hipo == 1) & (e.voluntary == 1), "compa_ratio"].dropna()
b = e.loc[(e.hipo == 1) & (e.voluntary == 0), "compa_ratio"].dropna()
ax1.hist([b, a], bins=28, density=True, color=[GREY, PURPLE], alpha=.75,
         label=[f"HiPo stayers ({len(b)})", f"HiPo leavers ({len(a)})"])
ax1.axvline(b.mean(), color=GREY, ls="--"); ax1.axvline(a.mean(), color=PURPLE, ls="--")
ax1.set_title("Pay position does NOT predict leaving", fontsize=11.5, color="#444", pad=10)
ax1.set_xlabel("Compa-ratio"); ax1.set_ylabel("density"); ax1.legend(frameon=False, fontsize=8.5)
ax1.text(.02, .78, f"0.884 vs 0.879\np = 0.38", transform=ax1.transAxes, fontsize=10,
         color=GREY, fontweight="bold")
lv = e[e.voluntary == 1]
a2 = lv.loc[lv.regrettable == 1, "compa_ratio"].dropna()
b2 = lv.loc[lv.regrettable == 0, "compa_ratio"].dropna()
ax2.hist([b2, a2], bins=28, density=True, color=[GREY, RED], alpha=.75,
         label=[f"Not flagged ({len(b2)})", f"Flagged regrettable ({len(a2)})"])
ax2.axvline(b2.mean(), color=GREY, ls="--"); ax2.axvline(a2.mean(), color=RED, ls="--")
ax2.set_title("...but it does predict how HR labels the exit", fontsize=11.5, color="#444", pad=10)
ax2.set_xlabel("Compa-ratio"); ax2.legend(frameon=False, fontsize=8.5)
ax2.text(.02, .78, "0.917 vs 0.947\np = 2 × 10⁻⁶", transform=ax2.transAxes, fontsize=10,
         color=RED, fontweight="bold")
fig.suptitle("The pay paradox: compa-ratio moves the label, not the decision",
             x=.005, ha="left", fontsize=13, fontweight="bold", y=1.08)
note(fig, "Right-hand gap holds controlling for role level and department (β = −0.029, p = 2.1 × 10⁻⁶). "
          "Underpaid people are not more likely to resign; they are more likely to be *called* a "
          "regrettable loss once they do. One more reason not to build the deck on regrettable_flag.")
save(fig, "d09_pay_paradox.png")

# ═════════════════════════════════════════════ 10 manager clustering is null
fig, ax = plt.subplots(figsize=(7.6, 4.4))
mg = e.groupby("manager_id").agg(span=("employee_id", "size"), vol=("voluntary", "sum"))
big = mg[mg["span"] >= 5]
p_bar = e.voluntary.mean()
obs = big["vol"].value_counts(normalize=True).sort_index()
ks = np.arange(0, int(big["vol"].max()) + 1)
exp = np.array([np.mean(stats.binom.pmf(k, big["span"], p_bar)) for k in ks])
w = .38
ax.bar(ks - w/2, [obs.get(k, 0) for k in ks], w, label="Observed", color=PURPLE)
ax.bar(ks + w/2, exp, w, label="If exits were random (binomial)", color=GREY)
ax.set_xlabel("Voluntary exits in the team, 2024–25"); ax.set_ylabel("Share of teams")
ax.set_xticks(ks)
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
ax.set_title("Attrition does not cluster under particular managers")
sub(ax, "745 teams with 5+ reports · dispersion ratio 0.79 (under-, not over-dispersed) · overdispersion χ² = 618 on 744 df, p ≈ 1")
ax.legend(frameon=False)
note(fig, "If NovaCorp had a 'bad manager' problem, the purple bars would have fatter tails than the "
          "grey ones. They do not. Manager-effectiveness survey scores also fail to predict HiPo exit "
          "(OR 0.95, p = 0.64). Manager coaching is not where the money is.")
save(fig, "d10_manager_clustering_null.png")

# ═════════════════════════════════════════════ 11 the artefact we threw away
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
sm_ = e[e.mgr_span <= 3]; lg = e[e.mgr_span > 3]
r_sm = sm_.groupby("mgr_departed")["voluntary"].mean()
r_lg = lg.groupby("mgr_departed")["voluntary"].mean()
for ax, r, t, ns in [(ax1, r_sm, "Teams of 3 or fewer", sm_.groupby("mgr_departed").size()),
                     (ax2, r_lg, "Teams of 4 or more", lg.groupby("mgr_departed").size())]:
    vals = [r.get(0, 0), r.get(1, 0)]
    b = ax.bar(["Manager stayed", "Manager also left"], vals, color=[GREY, RED], width=.5)
    for bar, v, k in zip(b, vals, [0, 1]):
        ax.text(bar.get_x()+bar.get_width()/2, v+.02, f"{v:.0%}", ha="center", fontweight="bold",
                fontsize=13)
        ax.text(bar.get_x()+bar.get_width()/2, .01 if v > .05 else v + .075,
                f"n = {ns.get(k,0):,}", ha="center",
                color="white" if v > .05 else "#777", fontsize=9)
    ax.set_ylim(0, .95); ax.set_title(t, fontsize=11.5, color="#444", pad=10)
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
ax1.set_ylabel("Voluntary exit rate")
ax1.text(.5, .62, "OR = 33\np = 9 × 10⁻⁶⁴", transform=ax1.transAxes, fontsize=11,
         color=RED, fontweight="bold", ha="center")
ax2.text(.5, .62, "OR = 1.0\np = 1.00", transform=ax2.transAxes, fontsize=11,
         color=GREY, fontweight="bold", ha="center")
fig.suptitle("Discarded: the 'manager departure cascade' is a definitional artefact",
             x=.005, ha="left", fontsize=13, fontweight="bold", y=1.08)
note(fig, "Every one of the 95 departed managers led a team of three or fewer, and in 100% of those "
          "cases the whole unit vanished. There is no lead-lag order either — 52% of reports left after "
          "their manager, 48% before (binomial p = 0.74). This is how the records were built, not a "
          "retention signal. Left in as a worked example of an effect size too good to be true.")
save(fig, "d11_cascade_artefact.png")

# ═════════════════════════════════════════════ 12 what it costs
fig, ax = plt.subplots(figsize=(8.4, 4.4))
hl = e[(e.hipo == 1) & (e.voluntary == 1)]
base = hl.salary.sum()
comps = {"Base salary of the 151\nHiPos who resigned": base,
         "Replacement cost\n(1.5× base, 85% backfilled)": base*1.5*.85,
         "Same, if silence-flagged\nexits were halved": base*1.5*.85*.5}
b = ax.barh(list(comps)[::-1], [v/1e6 for v in list(comps.values())[::-1]],
            color=[TEAL, PURPLE, GREY][::-1], height=.55)
for bar, v in zip(b, list(comps.values())[::-1]):
    ax.text(v/1e6 + .4, bar.get_y()+bar.get_height()/2, f"${v/1e6:.1f}M", va="center",
            fontweight="bold", fontsize=12)
ax.set_xlim(0, 31); ax.set_xlabel("A$ millions, 2024–25 combined")
ax.set_title(r"HiPo resignations alone account for ~\$25M of the \$22–25M attrition line")
sub(ax, "Finance benchmark: replacement cost 1.5× base salary, backfill rate 85%")
note(fig, "The bottom bar is illustrative only — it assumes a silence-triggered intervention retains half "
          "of the flagged group, which no evidence here establishes. Shown to size the prize, not to "
          "forecast it.")
save(fig, "d12_cost_size.png")

print("done —", len(list(OUT.glob('*.png'))), "figures")
