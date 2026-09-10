"""
wave_silence.py — survey wave-to-wave statistics and the anatomy of going quiet.

Outputs (to eddited_csv/):
  wave_summary.csv            per-wave headcount, response rate, dimension means
  wave_transitions.csv        wave k -> k+1 state transition matrix (counts + row %)
  silence_patterns.csv        response sequences for the balanced 5-wave panel
  silence_exit_hazard.csv     exit-within-180d by silence state (wave risk set)
  silence_precursor.csv       scores in the wave BEFORE a person goes quiet
  wave_panel.csv              person-wave panel with state + silence run length
"""
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "original_csv"
OUT = ROOT / "eddited_csv"
OUT.mkdir(exist_ok=True)

DIMS = ["manager_effectiveness", "psychological_safety", "recognition",
        "career_development", "senior_leadership_trust", "purpose_meaning",
        "wellbeing", "confidence_in_role_future"]

eng = pd.read_csv(RAW / "engagement.csv")
emp = pd.read_csv(RAW / "employees.csv")
att = pd.read_csv(RAW / "attrition_log.csv")

eng["survey_date"] = pd.to_datetime(eng.survey_date)
emp["hire_date"] = pd.to_datetime(emp.hire_date)
emp["exit_date"] = pd.to_datetime(emp.exit_date)
att["exit_date"] = pd.to_datetime(att.exit_date)

ANCHOR = eng.groupby("wave_number").survey_date.max()          # wave close date
WAVES = list(ANCHOR.index)

att_small = att[["employee_id", "exit_date", "exit_type", "regrettable_flag"]].rename(
    columns={"exit_date": "exit_dt"})
emp = emp.merge(att_small, on="employee_id", how="left")
emp["voluntary"] = (emp.exit_type == "voluntary").astype(int)

# ══════════════════════════════════════════════════ 1. per-wave summary
rows = []
for w in WAVES:
    d = ANCHOR[w]
    sub = eng[eng.wave_number == w]
    employed = ((emp.hire_date <= d) & (emp.exit_date.isna() | (emp.exit_date > d))).sum()
    r = sub.response_flag
    rec = dict(wave=w, close_date=d.date(), employed=int(employed),
               invited=len(sub), responded=int(r.sum()), silent=int((~r).sum()),
               response_rate=r.mean(), silence_rate=1 - r.mean())
    for c in DIMS:
        rec[c] = sub.loc[r, c].mean()
    rec["overall_score"] = sub.loc[r, DIMS].mean(axis=1).mean()
    rows.append(rec)
wave_summary = pd.DataFrame(rows)
wave_summary.to_csv(OUT / "wave_summary.csv", index=False)

# within-person score change, wave to wave (responders in both waves)
eng["overall"] = eng[DIMS].mean(axis=1)
piv = eng.pivot_table(index="employee_id", columns="wave_number",
                      values="overall", dropna=False)
paired = []
for w in WAVES[:-1]:
    a, b = piv[w], piv[w + 1]
    ok = a.notna() & b.notna()
    t, p = stats.ttest_rel(b[ok], a[ok])
    paired.append(dict(transition=f"W{w}->W{w+1}", n_paired=int(ok.sum()),
                       mean_before=a[ok].mean(), mean_after=b[ok].mean(),
                       delta=(b[ok] - a[ok]).mean(), t=t, p=p))
paired = pd.DataFrame(paired)

# ══════════════════════════════════════════════════ 2. person-wave panel + states
panel = []
for w in WAVES:
    d = ANCHOR[w]
    employed = emp[(emp.hire_date <= d) & (emp.exit_date.isna() | (emp.exit_date > d))]
    s = employed[["employee_id"]].copy()
    s["wave"] = w
    s["wave_date"] = d
    panel.append(s)
panel = pd.concat(panel, ignore_index=True)
panel = panel.merge(eng[["employee_id", "wave_number", "response_flag", "overall"] + DIMS]
                    .rename(columns={"wave_number": "wave"}), on=["employee_id", "wave"], how="left")
panel["state"] = np.where(panel.response_flag.eq(True), "responded",
                  np.where(panel.response_flag.eq(False), "silent", "not_surveyed"))
panel = panel.merge(emp[["employee_id", "hipo_flag", "department", "role_level", "compa_ratio",
                         "tenure_months", "exit_dt", "exit_type", "regrettable_flag",
                         "salary"]], on="employee_id", how="left")

panel = panel.sort_values(["employee_id", "wave"])
# consecutive silence run length ending at this wave
def runlen(g):
    out, n = [], 0
    for s in g:
        n = n + 1 if s == "silent" else 0
        out.append(n)
    return out
panel["silence_run"] = panel.groupby("employee_id").state.transform(lambda g: runlen(list(g)))
panel["prev_state"] = panel.groupby("employee_id").state.shift(1)
panel["prev_overall"] = panel.groupby("employee_id").overall.shift(1)
panel["newly_silent"] = ((panel.state == "silent") & (panel.prev_state == "responded")).astype(int)

# outcome: voluntary exit within 180 days of the wave close
panel["days_to_exit"] = (panel.exit_dt - panel.wave_date).dt.days
panel["exit_180"] = ((panel.exit_type == "voluntary") &
                     panel.days_to_exit.between(0, 180)).astype(int)
panel["regret_180"] = (panel.exit_180.eq(1) & panel.regrettable_flag.eq(True)).astype(int)
panel["invol_180"] = ((panel.exit_type == "involuntary") &
                      panel.days_to_exit.between(0, 180)).astype(int)
panel.to_csv(OUT / "wave_panel.csv", index=False)

# ══════════════════════════════════════════════════ 3. transition matrix
trans = []
wide = panel.pivot_table(index="employee_id", columns="wave", values="state",
                         aggfunc="first")
for w in WAVES[:-1]:
    a = wide[w].fillna("not_employed")
    b = wide[w + 1].fillna("left/not_employed")
    ct = pd.crosstab(a, b)
    ct = ct.reset_index().melt(id_vars=ct.index.name or "row", var_name="to", value_name="n")
    ct.columns = ["from", "to", "n"]
    ct["transition"] = f"W{w}->W{w+1}"
    trans.append(ct)
trans = pd.concat(trans, ignore_index=True)
trans["pct_of_from"] = trans.n / trans.groupby(["transition", "from"]).n.transform("sum")
trans.to_csv(OUT / "wave_transitions.csv", index=False)

# ══════════════════════════════════════════════════ 4. sequence patterns (balanced panel)
seq = wide.copy()
present_all = seq.notna().all(axis=1)
code = {"responded": "R", "silent": "S", "not_surveyed": "-"}
pat = seq[present_all].apply(lambda r: "".join(code[v] for v in r), axis=1)
pat_df = pat.value_counts().rename_axis("pattern").reset_index(name="n")
pat_df["pct"] = pat_df.n / pat_df.n.sum()

def classify(p):
    if p == "RRRRR":
        return "Never silent"
    if p == "SSSSS":
        return "Never responded"
    if "R" in p and p.endswith("S") and p.count("S") == len(p) - p.index("S"):
        return "Went quiet and stayed quiet"
    if p.count("S") == 1:
        return "One-off skip"
    return "In and out"
pat_df["group"] = pat_df.pattern.map(classify)
pat_df["n_silent"] = pat_df.pattern.str.count("S")
pat_df.to_csv(OUT / "silence_patterns.csv", index=False)

# attach pattern back to people for outcome analysis
pat_map = pat.rename("pattern").to_frame()
pat_map["group"] = pat_map.pattern.map(classify)
pat_map["n_silent"] = pat_map.pattern.str.count("S")
bal = emp.set_index("employee_id").join(pat_map, how="inner")
bal["vol_exit"] = ((bal.exit_type == "voluntary")).astype(int)

grp = bal.groupby("group").agg(people=("vol_exit", "size"),
                               vol_exits=("vol_exit", "sum"),
                               vol_rate=("vol_exit", "mean"),
                               hipo_share=("hipo_flag", "mean"),
                               compa=("compa_ratio", "mean")).reset_index()
nsil = bal.groupby("n_silent").agg(people=("vol_exit", "size"),
                                   vol_exits=("vol_exit", "sum"),
                                   vol_rate=("vol_exit", "mean"),
                                   hipo_share=("hipo_flag", "mean")).reset_index()

# ══════════════════════════════════════════════════ 5. silence -> exit hazard (risk set)
def or_ci(a, b, c, d):
    """a=exposed events, b=exposed non-events, c=unexp events, d=unexp non"""
    orr = (a * d) / (b * c)
    se = np.sqrt(1/a + 1/b + 1/c + 1/d)
    return orr, orr * np.exp(-1.96 * se), orr * np.exp(1.96 * se)

haz = []
for label, mask in [("All employees", panel.state.notna()),
                    ("HiPo only", panel.hipo_flag.eq(True)),
                    ("Non-HiPo", panel.hipo_flag.eq(False))]:
    p = panel[mask & panel.state.isin(["responded", "silent"])]
    for outcome in ["exit_180", "regret_180", "invol_180"]:
        t = pd.crosstab(p.state, p[outcome])
        if t.shape != (2, 2):
            continue
        a, b = t.loc["silent", 1], t.loc["silent", 0]
        c, d = t.loc["responded", 1], t.loc["responded", 0]
        orr, lo, hi = or_ci(a, b, c, d)
        chi2, pv = stats.chi2_contingency(t.values)[:2]
        haz.append(dict(population=label, outcome=outcome,
                        n_person_waves=len(p),
                        rate_silent=a / (a + b), rate_responded=c / (c + d),
                        odds_ratio=orr, ci_lo=lo, ci_hi=hi, p_value=pv))
haz = pd.DataFrame(haz)

# dose response: exit rate by consecutive silence run
dose = panel[panel.state.isin(["responded", "silent"])].copy()
dose["run_cap"] = dose.silence_run.clip(upper=3)
dose_tab = dose.groupby("run_cap").agg(person_waves=("exit_180", "size"),
                                        exits=("exit_180", "sum"),
                                        exit_rate=("exit_180", "mean"),
                                        regret_rate=("regret_180", "mean")).reset_index()
dose_tab["label"] = dose_tab.run_cap.map({0: "Responded", 1: "Silent 1 wave",
                                          2: "Silent 2 in a row", 3: "Silent 3+ in a row"})
haz.to_csv(OUT / "silence_exit_hazard.csv", index=False)
dose_tab.to_csv(OUT / "silence_dose_response.csv", index=False)

# ══════════════════════════════════════════════════ 6. what did they say BEFORE going quiet
pre = panel[(panel.prev_state == "responded")].copy()
pre["became_silent"] = (panel.loc[pre.index, "state"] == "silent").astype(int)
prev_scores = (panel.sort_values(["employee_id", "wave"])
                    .groupby("employee_id")[DIMS].shift(1))
pre = pre.join(prev_scores.add_prefix("prev_"), how="left")
prec = []
for c in DIMS + ["overall"]:
    col = f"prev_{c}" if c != "overall" else "prev_overall"
    g1 = pre.loc[pre.became_silent == 1, col].dropna()
    g0 = pre.loc[pre.became_silent == 0, col].dropna()
    t, p = stats.ttest_ind(g1, g0, equal_var=False)
    pooled = np.sqrt((g1.var() + g0.var()) / 2)
    prec.append(dict(dimension=c, n_went_quiet=len(g1), n_stayed=len(g0),
                     mean_went_quiet=g1.mean(), mean_stayed=g0.mean(),
                     diff=g1.mean() - g0.mean(), cohens_d=(g1.mean() - g0.mean()) / pooled,
                     t=t, p=p))
prec = pd.DataFrame(prec).sort_values("cohens_d")
prec.to_csv(OUT / "silence_precursor.csv", index=False)

# ══════════════════════════════════════════════════ print
pd.set_option("display.width", 200, "display.max_columns", 40)
print("\n=== 1. WAVE SUMMARY ===")
print(wave_summary[["wave", "close_date", "employed", "invited", "responded", "silent",
                    "response_rate", "overall_score"]].to_string(index=False))
print("\n--- dimension means (responders only) ---")
print(wave_summary[["wave"] + DIMS].round(3).to_string(index=False))
print("\n--- within-person change, paired t-test ---")
print(paired.round(4).to_string(index=False))
print("\n=== 2. TRANSITIONS (responded/silent only) ===")
tt = trans[trans["from"].isin(["responded", "silent"])]
print(tt.pivot_table(index=["transition", "from"], columns="to", values="pct_of_from")
        .round(3).to_string())
print("\n=== 3. SEQUENCE PATTERNS (balanced 5-wave panel, n=%d) ===" % present_all.sum())
print(pat_df.head(15).to_string(index=False))
print("\n--- grouped ---")
print(pat_df.groupby("group").agg(patterns=("pattern", "size"), people=("n", "sum"),
                                  pct=("pct", "sum")).sort_values("people", ascending=False).round(4).to_string())
print("\n--- outcome by group ---")
print(grp.round(4).to_string(index=False))
print("\n--- outcome by number of silent waves ---")
print(nsil.round(4).to_string(index=False))
print("\n=== 4. SILENCE -> EXIT HAZARD ===")
print(haz.round(4).to_string(index=False))
print("\n--- dose response ---")
print(dose_tab.round(4).to_string(index=False))
print("\n=== 5. SCORES IN THE WAVE BEFORE GOING QUIET ===")
print(prec.round(4).to_string(index=False))
print("\nwrote csvs to", OUT)
