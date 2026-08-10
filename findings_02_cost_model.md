# Findings 02 — Rebuilding the $42M

Model: `helper_code/cost_model.py`. Outputs: `eddited_csv/cost_model_scenarios.csv`, `eddited_csv/exits_bucketed.csv`.

All constants are the brief's own: replacement 1.5× base salary, backfill 85%, disengagement loss 15% of base salary/yr, super on-cost 12.0%, agency fee 18% of first-year base, direct hire benchmark $5,500. Window 1 Jan 2024 – 31 Dec 2025, annualised by dividing by 2.

**Headline:** the $42M total is roughly the right order of magnitude, but not one of its three components survives contact with the data. Regrettable attrition is overstated relative to the population HR actually flagged; disengagement is understated by 3–5×; hiring inefficiency is understated by 3–4×. The brief is directionally right and compositionally wrong, and the composition is what determines where the CHRO spends money.

---

## 1. The brief's $22–25M cannot be built from `regrettable_flag`

Costing HR's 153 flagged regrettable leavers with the brief's own constants:

153 exits × mean salary × 1.5 × 0.85 ÷ 2 years = **$12.7M/yr**.

That is roughly half the stated $22–25M. Reaching the stated figure from that population requires a multiplier of **2.20–2.50× base salary**, against the benchmark of 1.275× (1.5 × 0.85) the brief itself supplies.

| Definition | n | $M/yr @ 1.0× | @ 1.5× × 85% | @ 2.0× |
|---|---|---|---|---|
| HR `regrettable_flag` only | 153 | 10.0 | **12.7** | 20.0 |
| Voluntary + HiPo, tenure ≥180d | 118 | 7.7 | 9.8 | 15.3 |
| HR flag OR (voluntary + HiPo) | 228 | 14.8 | 18.9 | 29.6 |
| Voluntary + High/Outstanding, tenure ≥180d | 360 | 22.4 | 28.6 | 44.9 |
| Voluntary + (HiPo or High/Outstanding), tenure ≥180d | 403 | 25.2 | **32.1** | 50.3 |
| All voluntary exits | 1,133 | 70.8 | 90.2 | 141.6 |

So $22–25M is only reachable two ways: keep the brief's cost constants and roughly **double the population** (to ~300–400 exits), or keep HR's 153 and roughly **double the multiplier**. The brief does not say which it did.

This is the opening argument for the deck. It is not "the number is wrong" — it is **"the number is not reconcilable to HR's own definition, so it cannot be used to prioritise."**

## 2. A defensible regrettable population

Built from observables only. `regrettable_flag` and `performance_band_at_exit` are excluded on the evidence in findings_01 §3 (the latter agrees with the actual review record 15.7% of the time).

| Scenario | Rule | n | per yr | $M/yr @1.5××85% |
|---|---|---|---|---|
| **Low** | Voluntary, tenure ≥365d, HiPo | 109 | 54 | **9.0** |
| **Central** | Voluntary, tenure ≥180d, HiPo *or* last rating High/Outstanding | 403 | 202 | **32.1** |
| **High** | Voluntary, tenure ≥180d, not rated Below/Unsatisfactory | 783 | 392 | **63.0** |

Range across all nine population × multiplier combinations: **$6.0M – $84.0M/yr**. The width of that band is itself a finding — it is what happens when the underlying flag is unreliable, and it should be shown on the slide rather than hidden behind a point estimate.

Overlap with HR's view is poor. Of HR's 153 flagged: 82 land in our regrettable bucket, 44 are routine voluntary churn, 27 are early-tenure exits that belong in hiring. Of our 403: 321 were never flagged by HR at all.

## 3. Re-cut buckets, mutually exclusive

Assignment priority: early exit (≤90 days) → involuntary → regrettable (central rule) → routine voluntary. Each of the 1,400 exits lands in exactly one bucket; verified no double counting.

| Bucket | n | per yr | $M/yr |
|---|---|---|---|
| Routine voluntary churn | 542 | 271 | 43.5 |
| **Regrettable attrition** | 403 | 202 | **32.1** |
| Involuntary / managed exits | 236 | 118 | 19.5 |
| **Hiring inefficiency** (exits ≤90d) | 219 | 110 | **17.0** |

Plus an agency premium of **$2.3M/yr** — 274 agency hires since 2024 at 18% of first-year base versus the $5,500 direct-hire benchmark.

The hiring line is the one to lead with. The brief says $4–6M. The data says **$17.0M + $2.3M ≈ $19M/yr**, and 195 of those 219 early exits are acquisition hires. This cost is currently misfiled inside "attrition", which is why nobody has fixed it — retention interventions do not touch it.

## 4. Disengagement is understated, not overstated

The brief's $12–15M ÷ (mean salary $128,353 × 15%) implies **623–779 disengaged staff — 5–6% of the workforce**.

Measured at the latest survey wave (Aug 2025, 11,914 active staff surveyed, 80.5% response):

| Population | n | % surveyed | $M/yr @15% |
|---|---|---|---|
| Engagement index < 2.5 | 717 | 6.0% | 14.0 |
| Engagement index < 3.0 | 2,566 | 21.5% | 49.8 |
| Engagement index < 3.25 | 4,036 | 33.9% | 78.3 |
| Non-responders | 2,329 | 19.5% | 44.5 |

The brief's number reproduces almost exactly at an index threshold of **2.5** — the severely disengaged bottom 6%. At any conventional threshold the population is 3–5× larger.

**Two caveats that must go on the slide, not in the appendix.** First, findings_01 §4 showed engagement scores do not decline before exit, so the 15%-of-salary elasticity is assumed, not measured — this bucket is the least evidenced of the three. Second, non-responders are shown separately because `response_flag` is deliberate signal, but charging them the full 15% loss is the most aggressive assumption in the model and should not be added to the index-based figure without saying so.

## 5. The pay lever, and why blanket remediation fails

| Target compa-ratio | Active HiPos below | Annual cost incl. 12% super |
|---|---|---|
| 0.85 | 306 | $2.5M |
| 0.90 | 619 | $6.6M |
| 0.95 | 879 | $13.1M |
| 1.00 | 991 | $20.9M |

Set against HiPo voluntary attrition of **$9.8M/yr** (118 exits, tenure ≥180d):

- Lifting everyone to 0.95 costs **$13.1M** to address **$9.8M** of loss — negative return even at 100% effectiveness, which no retention intervention achieves.
- Lifting the worst-paid 306 to 0.85 costs **$2.5M**. It only needs to prevent ~26% of HiPo regrettable exits to break even.

The recommendation is therefore a **floor, not a market-match**. That distinction is the actionability argument.

---

## Verification performed

1. 1,400 exits, 1,400 unique IDs, one bucket each — confirmed.
2. No employee appears in two buckets (max distinct buckets per ID = 1).
3. Bucket salary totals reconcile to `attrition_log` total to <$1.
4. Hiring-inefficiency bucket max tenure = 90d; regrettable bucket min tenure = 184d; regrettable bucket 100% voluntary.
5. Observed exit window is 700 days, annualised as 730. Per-year costs are therefore **understated by ~4%** — conservative, and stated rather than corrected.

## Open issues

- The 15% disengagement elasticity is unvalidated against this data and cannot be validated with it. Either source it externally or present the bucket as a stated assumption.
- Acquisition-hire `hire_date` may be a migration date (findings_01 §2). Every tenure filter in this model inherits that risk. The ≥180d floor limits the damage but does not remove it.
- 2025-H2 reviews are missing by design, so `last_rating` for anyone exiting after 30 Jun 2025 is staler than for earlier leavers. This biases the Central and High scenarios in an unknown direction.
- No stayer control group. All costs here are gross; none are net of what NovaCorp would have spent anyway on planned turnover.
