# Findings 04 — Significance testing the "blocked high performers" hypothesis

**Hypothesis as stated:** employees performing at Outstanding/High Performer level who were not
promoted left the business.

**Verdict: partially supported, and not in the way the dashboard implies.** Promotion stagnation
is a real and significant driver of voluntary exit. It is *not* specific to high performers — it is
slightly *weaker* for them. Two of the three dashboard KPIs do not survive a base-rate comparison.

Script: `helper_code/sig_tests.py`, `helper_code/sig_tests_part2.py`

---

## 0. The design flaw that has to be fixed first

The dashboard uses `eddited_csv` (153 regrettable leavers). A chi-square needs a comparison group.
"50% of leavers were HiPo" is uninterpretable without "what % of stayers were HiPo".

**Cohort for all tests below:** all 13,294 employees with ≥1 performance review (stayers + leavers).
Outcome = `exit_type == 'voluntary'` (1,133 events). Predictor = `promotion_recommendation` ever
TRUE across the three observed review cycles.

---

## 1. Chi-square: performance rating × voluntary exit (5×2)

| Rating | Stayed | Left (voluntary) | Exit rate |
|---|---|---|---|
| Unsatisfactory | 347 | 29 | 7.71% |
| Below Expectations | 1,296 | 125 | 8.80% |
| Meets Expectations | 5,605 | 545 | 8.86% |
| High Performer | 3,491 | 318 | 8.35% |
| Outstanding | 1,422 | 116 | 7.54% |

χ²(4) = 3.40, **p = 0.49**, Cramér's V = 0.016, n = 13,294

**Top performers do not leave at a higher rate than anyone else.** Flat across all five bands.
The first half of the hypothesis fails outright.

---

## 2. Chi-square: blocked promotion × voluntary exit, *within* top performers

| Ever recommended for promotion | Stayed | Left | Exit rate |
|---|---|---|---|
| No | 2,415 | 266 | **9.92%** |
| Yes | 2,498 | 168 | **6.30%** |

χ²(1) = 23.49, **p = 1.3 × 10⁻⁶**, Cramér's V = 0.066, OR = 0.61 [0.50–0.75], Fisher p = 1.4 × 10⁻⁶

This is real and it is the finding worth keeping.

### 2b. Same test on non-top performers (the contrast group that kills the narrative)

| Ever recommended | Stayed | Left | Exit rate |
|---|---|---|---|
| No | 5,689 | 630 | **9.97%** |
| Yes | 1,559 | 69 | **4.24%** |

χ²(1) = 53.01, p = 3.3 × 10⁻¹³, OR = **0.40** [0.31–0.52]

The effect is **stronger** for non-top performers (OR 0.40) than for top performers (OR 0.61).
Promotion stagnation predicts exit for everybody. It is not a high-performer story.

### 2c. `promotion_eligible` (the HR field the dashboard uses) — null

χ²(1) = 0.82, **p = 0.36**, OR = 0.90 [0.71–1.13]. The static HR eligibility flag has no
relationship to exit. Only the *review-cycle* promotion recommendation does.

---

## 3. Logistic regression with interaction — the formal test

Controls: tenure, compa-ratio, role level, department, age band (fixed effects).

| Term | OR | 95% CI | p |
|---|---|---|---|
| Top performer | 1.49 | 1.12–1.99 | 0.007 |
| Ever recommended for promotion | **0.41** | 0.31–0.52 | <0.0001 |
| **Top × not-promoted (interaction)** | **0.66** | 0.48–0.92 | **0.012** |
| Tenure (years) | 0.97 | 0.95–0.98 | <0.0001 |
| Compa-ratio | 0.28 | 0.11–0.72 | 0.008 |

Likelihood-ratio test for the interaction: LR = 6.31, df = 1, **p = 0.012**. Pseudo-R² = 0.018.

The interaction is **significant and negative** — the opposite direction to the hypothesis.
Being blocked hurts high performers *less* than it hurts everyone else.

Observed exit rates by cell:

| | Not promoted | Promoted |
|---|---|---|
| **Top performer** | 9.92% | 6.30% |
| **Other** | 9.97% | 4.24% |

---

## 4. Cochran–Mantel–Haenszel — does it hold within departments?

Stratified by department (7 strata), top performers only:

- Pooled OR = **0.608** [0.497–0.743], CMH test p = 9.8 × 10⁻⁷
- Breslow–Day homogeneity: χ² = 4.61, p = 0.59 → the odds ratio is consistent across departments,
  so this is not a single department dragging the pooled result.

The promotion effect is not a departmental composition artefact.

---

## 5. Why the dashboard KPIs mislead

### 5a. `promotion_eligible` — no signal at all

| Group | % promotion-eligible |
|---|---|
| Regrettable leavers | 24.2% |
| All voluntary leavers | 26.0% |
| **Active staff** | **25.6%** |

"Only 24% were promotion-eligible at exit" reads as damning but is **identical to the base rate**.
This KPI should be removed from the deck.

### 5b. `regrettable_flag` is close to circular with performance

`performance_band_at_exit` × `regrettable_flag`, leavers only:

| Band at exit | Not regrettable | Regrettable | % flagged |
|---|---|---|---|
| Outstanding | 54 | 97 | **64.2%** |
| High Performer | 341 | 31 | 8.3% |
| Meets Expectations | 490 | 17 | 3.4% |
| Below Expectations | 255 | 4 | 1.5% |
| Unsatisfactory | 107 | 4 | 3.6% |

`hipo_flag` × `regrettable_flag`: 42.0% of HiPo leavers flagged regrettable vs 6.3% of non-HiPo.

HR appears to assign `regrettable_flag` largely *from* the performance band and HiPo status.
"128 of 153 regrettable exits were Outstanding or High Performer" is therefore close to a
definitional tautology, not a discovery. The brief already warns that `regrettable_flag` is a
retrospective HR judgement — this quantifies how far that goes.

### 5c. HiPo rate is the one KPI that does hold up

49.7% of regrettable leavers vs 8.6% of active staff. But given 5b, use it descriptively, not as
causal evidence.

---

## 6. What to put in the deck instead

**Claim that survives scrutiny:**
> Employees who go three review cycles without a promotion recommendation leave voluntarily at
> ~10% vs ~5% for those who receive one — a 2.1× relative risk that holds after controlling for
> department, role level, tenure and pay position (CMH pooled OR 0.61, p < 0.001, consistent
> across all seven departments).

**Claim to drop:**
> "High performers are leaving because they are blocked from promotion." The data does not support
> a performance-specific effect; the interaction runs the other way (p = 0.012).

**Framing benefit:** the surviving claim is *bigger*, not smaller — promotion stagnation affects
~9,000 employees, not 153. It also changes the intervention: a career-pathing fix aimed at the
whole population, not a HiPo retention programme.

---

## 7. Caveats to state in the appendix

1. **`promotion_recommendation` is not exogenous.** Managers may withhold recommendations from
   people already showing disengagement or known to be interviewing. Reverse causation is live.
   Mitigation: re-run using only recommendations from cycles ≥6 months before exit date.
2. 2025-H2 review cycle is deliberately missing, so "ever recommended" covers 2024-H1 to 2025-H1.
3. Pseudo-R² = 0.018 — promotion status explains a small share of exit variance. Real but not the
   whole story; frame as "one lever", not "the driver".
4. Multiple comparisons: ~12 tests run. Bonferroni threshold α = 0.0042. Tests 1, 2, 2b, 3, 4 and
   the LR interaction test all remain significant at that threshold; 2c and 5a were null anyway.
5. 109 employees have no performance review and were dropped (0.8%).
