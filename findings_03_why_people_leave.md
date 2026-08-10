# Findings 03 — Why people leave

Model: `helper_code/risk_set.py`. Outputs: `eddited_csv/risk_set_2024-10-25.csv`, `eddited_csv/risk_set_2025-01-31.csv`.

## Method

Everything in findings_01 was conditioned on having left, so it could describe leavers but could not explain them. This adds the control group.

Pick a reference date. Take every employee active on that date. Build features from information observable **on or before** that date only. Outcome = voluntary exit in the following 12 months. Involuntary exits inside the window are censored, not treated as controls. `regrettable_flag` and `performance_band_at_exit` are never used, as features or as outcome.

Two reference dates, so every effect can be checked for stability:

| Reference | Risk set | Voluntary exits in next 12m | Base rate |
|---|---|---|---|
| 25 Oct 2024 (wave 3) | 11,446 | 538 | 4.70% |
| 31 Jan 2025 (wave 4) | 11,330 | 429 | 3.79% |

---

## 1. The answer: almost nothing NovaCorp measures predicts who leaves

This is the finding, and it is uncomfortable enough that it should lead the deck rather than hide in the appendix.

Logistic regression, both reference dates, odds ratios:

| Feature | OR (Oct 24) | OR (Jan 25) | Verdict |
|---|---|---|---|
| **Missed surveys** (per survey not returned) | **2.50** *** | **2.39** *** | **Strong, stable** |
| HiPo flag | 1.50 ** | 1.64 ** | Real, modest |
| Small team (≤3 reports) | 1.31 ** | 1.41 ** | Real, modest — but see §4 |
| Promotion recommended | 1.22 | 0.92 | Null |
| Strong performance rating | 1.01 | 0.80 | Null |
| Tenure < 6 months | 0.98 | 1.27 | Null |
| Acquisition hire | 0.95 | 0.86 | Null |
| Role level | 0.97 | 0.94 | Null |
| **Compa-ratio below 0.90** | **0.93** | **0.93** | **Null** |
| Engagement index score | 0.77 ** | 0.85 | Unstable |

`***` p<0.001, `**` p<0.01. Pseudo-R² = 0.050 and 0.060.

**Pay position does not predict exit.** Univariately the gradient is not merely weak, it runs the wrong way — the lowest-paid band has the *lowest* exit rate:

| Compa-ratio | n | Exit rate | Rel. risk |
|---|---|---|---|
| <0.80 | 279 | 2.5% | 0.53 |
| 0.85–0.90 | 1,958 | 4.9% | 1.04 |
| 0.90–0.95 | 3,000 | 5.1% | 1.09 |
| 1.00+ | 2,273 | 4.5% | 0.95 |

This kills the intuitive story. findings_01 §1 showed leaving HiPos and staying HiPos are paid the same (0.868 vs 0.879); with a full control group that generalises to the whole workforce. **The HiPo pay gap is a fairness and market-exposure problem, not the reason anyone is walking out.** Recommending pay remediation as a retention lever is not supported — and findings_02 §5 already showed it loses money on those grounds.

Also null: performance rating, promotion recommendation, department, role level, contract type, `days_to_fill`, and — despite findings_01 §4 — every one of the eight engagement dimensions.

## 2. The one thing that works: people stop answering long before they leave

Not what they say. Whether they say anything.

Within employees eligible for all three surveys up to Oct 2024:

| Surveys returned (of 3) | n | Exit rate |
|---|---|---|
| 3 | 5,211 | 2.6% |
| 2 | 2,909 | 5.5% |
| 1 | 524 | **13.0%** |

A clean 5× dose-response. It holds in every stratum tested:

- **Not an exposure artefact.** Among those eligible for only 2 surveys: 0 returned → 18.0%, 1 → 7.3%, 2 → 2.9%.
- **Not tenure.** Within <6m: 11.6% vs 4.8%. Within 1–2y: 11.0% vs 2.2%. Within 2y+: 14.6% vs 2.8%.
- **Not acquisition status.** Acquisition hires RR 2.49; origin hires RR 3.38.
- **Not contract type.** Response-rate distribution is identical across full-time, part-time, fixed-term and casual (0.09 / 0.30 / 0.61 in every case), so it is not a mechanical access problem.

**Lead-time test — the important one.** If non-response were mechanical (people on notice or long leave don't fill in surveys) the effect would concentrate just before exit. It does not:

| Exit occurs after ref date | RR at 2+ missed surveys |
|---|---|
| 0–3 months | 3.11 |
| 3–6 months | 3.60 |
| 6–9 months | 3.36 |
| 9–12 months | 3.11 |
| 12–18 months | 4.69 |

Flat, and if anything strongest at the longest horizon. This is a genuine leading indicator with **12–18 months of warning**, which is far more operational runway than any exit interview provides.

## 3. Why the survey scores are useless — and it is not what you would guess

The obvious hypothesis is that people disengage, score badly, then go quiet, then leave. It is wrong.

Take everyone who responded to waves 1 and 2, then split by whether they responded to wave 3. Compare the scores they gave **while both groups were still answering**:

| Dimension | Future drop-outs | Continued responders | Gap |
|---|---|---|---|
| Senior leadership trust | 3.36 | 3.39 | −0.04 |
| Confidence in role future | 3.38 | 3.41 | −0.03 |
| Manager effectiveness | 3.35 | 3.35 | −0.00 |
| Career development | 3.39 | 3.38 | +0.01 |
| Recognition | 3.41 | 3.38 | +0.03 |
| **Overall index** | **3.38** | **3.38** | **−0.00** |

n = 1,079 drop-outs vs 5,794 continuers. Identical to two decimal places.

So the people who are about to withdraw are, while they are still answering, indistinguishable from everyone else. **The instrument has no content validity for retention risk.** Only the act of participating carries information; the answers carry none.

The instrument is not pure noise — it discriminates between departments (spread 0.55) and role levels (0.63). But it does not discriminate HiPo from non-HiPo (spread 0.009), and it does not discriminate future leavers from stayers at all. Inter-dimension correlation averages 0.27, low for an engagement battery, which suggests the eight dimensions are not measuring one coherent construct.

There is a second-order consequence for the reported number. Response rates fall 84% → 80% across the five waves while the reported index stays flat at 3.39 → 3.36. The people leaving the sample are disproportionately the ones who then leave the company, so **the headline engagement score is propped up by survivorship.** It is stable because it is losing its most at-risk respondents, not because sentiment is stable.

## 4. Data-quality finding: `manager_id` leaks the outcome and must not be modelled

An initial pass showed that employees whose manager had recently exited left at a 100% rate (RR 21.3). That is not a finding, it is leakage. Checking the whole table:

| | Manager active | Manager departed |
|---|---|---|
| **Employee active** | 12,002 | **0** |
| **Employee departed** | 1,288 | 112 |

Not one active employee reports to a departed manager. P(departed | manager departed) = 100.0%; P(departed | manager active) = 9.7%.

That is organisationally impossible — when a manager resigns their team does not resign with them — so `manager_id` encodes exit status by construction rather than describing the org chart. Consequences:

1. No manager-quality or team-contagion analysis is possible. findings_01 §5 concluded "no manager concentration"; the stronger and correct statement is that **the field cannot support the question**.
2. The `small_team` effect in §1 (OR 1.31 / 1.41) should be treated as suggestive only. Span is computed over active staff at the reference date, so a small team may simply be one that has already shrunk through attrition — reverse causation is not ruled out.
3. `attrition_log.manager_id_at_exit` agrees with `employees.manager_id` 100% of the time, so it is the same field and offers no independent check.

## 5. The signal fails on exactly the population that costs the most

| Missed surveys | HiPos (n) | Exit rate | RR |
|---|---|---|---|
| 0 | 609 | 6.1% | 0.95 |
| 1 | 336 | 6.8% | 1.06 |
| 2+ | 54 | 7.4% | 1.16 |

Against RR 2.5–3.4 in the general population, the non-response signal is **flat for HiPos**. HiPos leave at an elevated base rate (OR ~1.5, and they are 50% of HR's flagged regrettable exits) and they leave without any warning the current data can detect.

This must be stated rather than glossed. It means an early-warning system built on survey participation will work for the bulk of the workforce and will not work for the most expensive segment. n = 54 at the top band, so the null is imprecise — but a monitoring system cannot be recommended for HiPos on this evidence.

---

## What this means for the recommendation

The honest answer to "why are so many people leaving" is that **NovaCorp cannot currently answer that question**, and the three instruments it would use to try are each independently broken:

- **Exit interviews** — 93% cite a pull reason, 1 of 153 cites pay, while sitting at 0.88 median compa (findings_01 §6). The brief's own 40–60% error warning is visible in the data.
- **Engagement survey** — no content validity for retention risk (§3); reported score propped up by survivorship.
- **`regrettable_flag` / `performance_band_at_exit`** — agrees with the review record 15.7% of the time (findings_01 §3).
- **`manager_id`** — leaks the outcome, cannot support manager analysis (§4).

Two things are nevertheless actionable, and they are the two the deck should carry:

1. **Survey participation is a free, existing, 12–18-month leading indicator that NovaCorp is currently discarding as missing data.** No new collection required. Works for the general population; explicitly does not work for HiPos.
2. **The integration cliff is the one exit driver with an identified mechanism and a real price tag** — 219 exits at ≤90 days, 195 of them acquisition hires, ~$19M/yr (findings_02 §3). It is structural, not attitudinal, which is why none of the attitudinal instruments detect it.

Pay remediation should be argued on fairness and market exposure, and should not be sold to the CFO as a retention intervention. The data does not support that claim.

---

## Verification performed

1. Effects reproduced at two independent reference dates; `missed_surveys` OR 2.50 vs 2.39 with non-overlapping-with-null CIs at both.
2. Non-response effect stratified by surveys-offered, tenure band, hire source and contract type — survives all four.
3. Lead-time test rules out the mechanical explanation (effect flat from 0–3m out to 12–18m).
4. Target leakage audit on `manager_id` — leakage found and the variable excluded (§4).
5. Involuntary exits censored rather than counted as controls, so the outcome is voluntary exit only.

## Limitations

- Pseudo-R² 0.05–0.06. Even the best available model explains very little variance. Most of who leaves is unpredictable from what NovaCorp records — that is a statement about the data, not a modelling failure, and it should be said plainly.
- Observational throughout. Nothing here establishes causation; `missed_surveys` is a leading indicator, and there is no evidence that making someone respond would change their behaviour.
- HiPo null in §5 rests on n=54 in the top band.
- Acquisition-hire `hire_date` may be a migration date (findings_01 §2), so tenure features for that group remain unreliable.
- The 2025-H2 review cycle is missing by design, limiting performance features at the later reference date.
