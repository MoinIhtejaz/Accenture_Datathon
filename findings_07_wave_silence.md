# Findings 07 — Wave-to-wave survey statistics and the anatomy of going quiet

*Scripts: `helper_code/wave_silence.py` (stats), `helper_code/charts_waves.py` (figures).
Outputs: `eddited_csv/wave_*.csv`, `eddited_csv/silence_*.csv`, `charts_waves/s01–s08`.*

---

## 0. What the survey panel actually is

Five waves between March 2024 and August 2025, 55,971 person-wave rows, 13,096 distinct
employees. Every wave was sent to essentially the whole company — invitations cover
99–100% of everyone employed at the wave close date — so a non-response is a choice, not a
sampling gap. `response_flag = False` rows carry no scores at all (100% null on every
dimension), which is why silence has to be analysed as a behaviour rather than imputed away.

| Wave | Close date | Employed | Invited | Responded | Silent | Response rate |
|---|---|---|---|---|---|---|
| 1 | 8 Mar 2024 | 10,042 | 10,043 | 8,396 | 1,647 | **83.6%** |
| 2 | 8 Jul 2024 | 10,816 | 10,719 | 8,850 | 1,869 | **82.6%** |
| 3 | 31 Oct 2024 | 11,572 | 11,627 | 9,419 | 2,208 | **81.0%** |
| 4 | 8 Feb 2025 | 11,442 | 11,446 | 9,301 | 2,145 | **81.3%** |
| 5 | 8 Aug 2025 | 12,122 | 12,136 | 9,741 | 2,395 | **80.3%** |

Response rate falls 3.4 points across the window — about 400 extra silent people at wave 5
than wave 1's rate would produce. Headcount grew 21% over the same period, so the silent
block grew twice as fast as the company.

**→ `charts_waves/s01_response_rate_by_wave.png`**

## 1. The scores barely move. The silence does.

Mean scores by wave, responders only (1–5 scale):

| Dimension | W1 | W2 | W3 | W4 | W5 | W1→W5 |
|---|---|---|---|---|---|---|
| Manager effectiveness | 3.364 | 3.345 | 3.365 | 3.355 | 3.366 | +0.002 |
| Psychological safety | 3.385 | 3.382 | 3.362 | 3.364 | 3.363 | −0.022 |
| Recognition | 3.392 | 3.381 | 3.364 | 3.366 | 3.375 | −0.017 |
| Career development | 3.385 | 3.366 | 3.374 | 3.362 | 3.369 | −0.016 |
| Senior leadership trust | 3.392 | 3.363 | 3.341 | 3.342 | 3.338 | **−0.054** |
| Purpose & meaning | 3.391 | 3.370 | 3.345 | 3.330 | 3.316 | **−0.075** |
| Wellbeing | 3.402 | 3.378 | 3.364 | 3.371 | 3.364 | −0.038 |
| Confidence in role future | 3.402 | 3.398 | 3.386 | 3.366 | 3.355 | **−0.047** |

Within-person paired t-tests on the composite score:

| Transition | n paired | Before | After | Δ | p |
|---|---|---|---|---|---|
| W1→W2 | 6,941 | 3.390 | 3.380 | −0.010 | 0.0003 |
| W2→W3 | 7,265 | 3.374 | 3.364 | −0.010 | 0.0001 |
| W3→W4 | 7,609 | 3.365 | 3.361 | −0.004 | 0.112 |
| W4→W5 | 7,445 | 3.366 | 3.358 | −0.008 | 0.002 |

Three of four transitions are statistically significant and every one of them is
**practically meaningless** — a tenth of a decimal point on a five-point scale. Anyone
reading only the score dashboard would conclude nothing is happening. The signal is in
who stopped filling the form in.

## 2. Where people go, wave to wave

Row = state at wave *k*, columns = state at wave *k+1*, rows sum to 100%:

| Transition | Prior state | → Responds | → **Silent** | → Gone |
|---|---|---|---|---|
| W1→W2 | Responded | 82.7% | **15.6%** | 1.7% |
| | Silent | 80.6% | **15.8%** | 3.6% |
| W2→W3 | Responded | 81.8% | **16.5%** | 1.6% |
| | Silent | 78.0% | **18.2%** | 3.8% |
| W3→W4 | Responded | 81.1% | **17.7%** | 1.2% |
| | Silent | 74.9% | **22.0%** | 3.2% |
| W4→W5 | Responded | 80.0% | **17.6%** | 2.4% |
| | Silent | 73.4% | **21.0%** | 5.6% |

Three things fall out of this table:

1. **Silence is sticky, and getting stickier.** Someone already quiet stays quiet 15.8% →
   21.0% of the time. A responder goes quiet 15.6% → 17.7%. The gap opens over the window.
2. **Silence roughly doubles the exit rate at every single step** — 3.6% vs 1.7%, 3.8% vs
   1.6%, 3.2% vs 1.2%, 5.6% vs 2.4%.
3. **Silence churns.** Three-quarters of the silent come back next wave. It is not a fixed
   group of disengaged people; it is a revolving door that a minority never exit.

**→ `charts_waves/s03_transition_matrix.png`, `charts_waves/s02_alluvial_five_waves.png`**

## 3. Individual patterns across all five waves

For the 9,248 people surveyed at all five waves:

| Pattern group | People | Share |
|---|---|---|
| Never silent (`RRRRR`) | 4,018 | 43.5% |
| One-off skip (one S, e.g. `SRRRR`) | 2,943 | 31.8% |
| In and out (scattered) | 1,383 | 15.0% |
| **Went quiet and stayed quiet** (trailing run of S) | **904** | **9.8%** |

Only 43.5% of employees answered every wave. The 9.8% with a terminal silence run are the
operationally interesting group — and this cohort *understates* them, because by
construction it only contains people still employed at wave 5.

**→ `charts_waves/s05_sequence_raster.png`**

## 4. The dose-response — the number that matters

Wave risk set (55,839 person-waves; everyone employed at each wave close, followed 180 days):

| State at the wave | Person-waves | Voluntary exits ≤180d | Exit rate |
|---|---|---|---|
| Responded | 45,620 | 807 | **1.77%** |
| Silent, 1 wave | 8,691 | 290 | **3.34%** |
| Silent, 2 in a row | 1,305 | 67 | **5.13%** |
| Silent, 3+ in a row | 223 | 27 | **12.11%** |

Monotone, near-doubling at each step, 6.8× baseline at the top. Linear-by-linear trend
test p = 1.1 × 10⁻⁵⁰.

Odds ratios, silent vs responded:

| Population | Outcome | Rate silent | Rate responded | OR [95% CI] | p |
|---|---|---|---|---|---|
| All | Voluntary exit ≤180d | 3.76% | 1.77% | **2.17 [1.92–2.45]** | 4.5 × 10⁻³⁶ |
| All | Regrettable exit ≤180d | 0.39% | 0.26% | 1.49 [1.04–2.13] | 0.036 |
| All | **Involuntary** exit ≤180d | 0.97% | 0.43% | **2.29 [1.80–2.92]** | 6 × 10⁻¹² |
| HiPo | Voluntary exit ≤180d | 4.37% | 2.75% | **1.62 [1.11–2.35]** | 0.015 |
| Non-HiPo | Voluntary exit ≤180d | 3.70% | 1.67% | 2.26 [1.98–2.57] | 1.5 × 10⁻³⁵ |

**Falsification stated up front:** silence predicts *involuntary* exit at OR 2.29 — as
strongly as it predicts resignation. It is a disengagement marker, not a resignation
marker. That is consistent with the position already taken in findings_06 and should stay
on the slide rather than be discovered by a judge.

**→ `charts_waves/s04_dose_response.png`, `charts_waves/s07_hipo_convergence.png`**

## 5. What people said in the last survey they answered

Comparing scores at wave *k* for people who answered wave *k+1* (n = 29,208) against those
who went quiet at *k+1* (n = 6,063):

| Dimension | Went quiet | Kept responding | Δ | Cohen's d | p |
|---|---|---|---|---|---|
| Senior leadership trust | 3.311 | 3.370 | −0.059 | −0.062 | 1.0 × 10⁻⁵ |
| Purpose & meaning | 3.324 | 3.366 | −0.042 | −0.044 | 0.002 |
| Composite | 3.357 | 3.374 | −0.016 | −0.029 | 0.044 |
| Manager effectiveness | 3.343 | 3.361 | −0.019 | −0.019 | 0.17 |
| Confidence in role future | 3.376 | 3.391 | −0.015 | −0.016 | 0.24 |
| Psychological safety | 3.367 | 3.375 | −0.008 | −0.008 | 0.56 |
| Career development | 3.371 | 3.373 | −0.002 | −0.002 | 0.88 |
| Recognition | 3.379 | 3.375 | +0.004 | +0.004 | 0.77 |
| Wellbeing | 3.386 | 3.377 | +0.009 | +0.010 | 0.50 |

Two dimensions are significant — senior leadership trust and purpose & meaning — and both
effect sizes are around d = 0.06, which is nothing. **The survey answers do not tell you
who is about to go quiet. The act of going quiet is the signal.** This is the honest
version of the finding and it strengthens the recommendation rather than weakening it: the
trigger runs off a response flag, not off a score threshold, so it needs no model, no
scoring, and no interpretation of what someone wrote.

**→ `charts_waves/s06_precursor_scores.png`**

## 6. The operational case

- **33.1%** of voluntary leavers were silent at the last survey they were present for,
  against **19.5%** of people still employed (p = 2.3 × 10⁻²², n = 916 vs 11,914).
- For the 303 leavers whose final survey was a non-response, the first wave of that silent
  run came a **median 84 days** (IQR 40–146) before the resignation date.
- HiPos entered wave 1 as the *most* engaged group in the company (12.1% silent vs 16.8%)
  and finished level with everyone else (19.4% vs 19.8%) — a 7.3-point deterioration,
  p = 1.5 × 10⁻⁵. Whatever happened over 2024–25, it landed hardest on the people NovaCorp
  had flagged as its future.
- No department is distinguishable on silence rate (17.99% to 19.87% across the seven
  units; Executive Leadership is highest but n = 936). Consistent with the department ANOVA
  null in findings_05 — this is a company-level pattern, not a pocket.

**→ `charts_waves/s08_final_survey_and_leadtime.png`**

## 7. Caveats to keep on the appendix slide

1. The balanced 5-wave panel (§3) is a **survivor cohort** — it excludes anyone who left
   before August 2025, so its absolute exit rates are understated. Every headline number in
   §4 uses the exposure-corrected wave risk set instead, per the rule set in findings_05.
2. Non-response has innocent causes — leave, secondment, parental leave, a full inbox.
   The claim is not that silence *means* disaffection; it is that the silent population
   contains enough at-risk people to be worth a conversation at a 3.8% hit rate.
3. Wave 5 (Aug 2025) has only ~5 months of follow-up inside the 31 Dec 2025 data window,
   so 180-day outcomes for that wave are partially right-censored. Excluding wave 5 does
   not change the direction or significance of the dose-response.
4. Silence predicts involuntary exit as strongly as voluntary (§4). Do not sell it as a
   resignation predictor.
