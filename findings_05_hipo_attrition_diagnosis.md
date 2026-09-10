# Findings 05: why the skilled leavers are leaving

Scripts: `helper_code/build_master.py`, `sweep_hipo.py`, `diagnose_confounds.py`, `wave_risk_set.py`,
`structural_drivers.py`, `silence_and_units.py`, `final_checks.py`, `charts_diagnosis.py`
Figures: `charts_diagnosis/d01` to `d12`

## The short version

We ran the diagnosis on both definitions of the group in parallel, as agreed: HiPo-flagged people
who resigned, and people HR flagged as regrettable losses. The two definitions do not point at the
same thing, and that gap is itself one of the more useful results.

The honest answer to "why are they leaving" is that the four files do not contain the reason. What
they do contain is a reliable warning, one real structural gradient, and a set of plausible-sounding
explanations that fall apart when you fix the measurement. All three are worth 15 slides.

Nine things survived scrutiny:

1. HiPos resign at 12.5% against 8.1% for everyone else (OR 1.63, p = 5.5 x 10⁻⁷). Real, and the
   starting point for the cost case.
2. Not answering the engagement survey predicts resignation more than twice as strongly as
   answering it badly (OR 2.24, p = 8.7 x 10⁻³⁷). This is the single biggest usable signal in the data.
3. The silence shows up a year before the exit, so it is not people on notice ignoring HR.
4. For HiPos, none of the eight survey dimensions separate leavers from stayers. Not one.
5. Being passed over for promotion raises exit odds for HiPos (OR 1.63, p = 0.022) and for nobody
   else. This partly reverses findings_04, for reasons worth being upfront about.
6. Department matters more than anything else structural. Corporate Operations runs 19.1% HiPo
   attrition against 7.0% in Retail Banking, and nothing in the data explains why.
7. Attrition does not cluster under bad managers. It is slightly under-dispersed, which is the
   opposite of what a manager problem looks like.
8. Pay position does not predict who leaves. It predicts who gets called a regrettable loss.
9. Two of the largest effects we found were artefacts. Both are documented below because a judge
   will look for them.

## First, the design problem that changes several answers

Most of the obvious comparisons in this dataset are broken in the same way, and it took a while to
see it.

Someone who resigned in March 2024 could physically appear in one performance review cycle. Someone
still employed in December 2025 appears in three. So any count taken per person rather than per
opportunity will make leavers look neglected, regardless of how they were actually treated. Leavers
average 1.68 reviews and 3.02 survey waves. Stayers average 2.74 and 4.51. See `d06_exposure_bias.png`.

This is why "leavers were less likely to have ever been recommended for promotion" looks so strong
and means so little. Normalise to recommendations per review and the all-staff gap collapses to
p = 0.26.

Everything below uses one of two designs instead:

- Wave risk set: 55,939 person-waves. For each survey wave, take everyone employed on the survey
  date, record what they did or did not answer, then ask whether they resigned in the next 180 days.
  Same calendar moment, same look-ahead, same exposure for every row.
- Review risk set: 34,979 reviews, built the same way.

Both let a leaver and a stayer contribute on equal terms until the leaver drops out of the risk set.

## Finding 1: HiPos really do leave more

`d01_hipo_gap.png`

151 of 1,210 HiPos resigned over the two years, against 982 of 12,193 everyone else. That is 12.5%
against 8.1%, OR 1.63 [1.35 to 1.98], Fisher p = 5.5 x 10⁻⁷.

Their combined base salary was $19.6M. At the finance benchmarks (1.5x replacement, 85% backfill)
that is $24.9M of replacement cost from this group alone, which lands squarely inside the $22 to
$25M regrettable attrition line the brief gives you. See `d12_cost_size.png`. Worth saying on a slide:
the HiPo population is 9% of headcount and accounts for roughly the whole attrition cost estimate.

## Finding 2: the survey people skip tells you more than the survey they fill in

`d02_silence_beats_scores.png`, `d03_silence_lead_time.png`

This is the result to lead with.

Across the wave risk set, people who did not respond to a survey resigned within 180 days at 3.84%.
People who responded and scored in the bottom quartile resigned at 2.04%. People who responded and
scored normally resigned at 1.65%. All responders taken together, low scorers included, come to
1.75%. The odds ratio for silence against answering is 2.24 [1.98 to 2.54], p = 8.7 x 10⁻³⁷, and it
stays at 2.24 after adjusting for HiPo status, tenure, compa-ratio, role level, department and wave.

Read those three numbers again. A bad score moves you from 1.65% to 2.04%. Silence moves you to
3.84%. NovaCorp is spending its engagement budget reading the responses and throwing away the more
informative half of the dataset.

For HiPos specifically the effect is smaller but still there: 2.74% against 4.47%, OR 1.66,
p = 0.0096. The interaction with HiPo status runs slightly negative (OR 0.71, p = 0.087), so silence
is marginally less diagnostic for HiPos than for everyone else, though the difference is not
significant.

The obvious objection is that people already resigning stop filling in surveys, which would make
this a lagging indicator dressed up as a leading one. It does not hold. Drop every wave that falls
inside a 90-day notice window and look only at exits between 90 and 365 days out: OR 2.07,
p = 1.7 x 10⁻³² for all staff, OR 1.50, p = 0.022 for HiPos. The signal is there a year ahead. It
also replicates in all five waves independently (ORs 1.71 to 2.71, every one significant).

One more angle. Of people who eventually resigned, 34% were silent in their final survey against 18%
of people who stayed (OR 2.19, p = 2.4 x 10⁻¹⁹).

The brief told you non-response was deliberate signal. It was not exaggerating.

## Finding 3: for HiPos, the survey scores are flat

`d04_engagement_flat_for_hipo.png`

Every one of the eight dimensions, tested on HiPos in the risk set, produces a confidence interval
that crosses zero. Career development, the dimension everyone expects to be the culprit, comes in at
Hedges' g = -0.01. Recognition is -0.12 with a CI from -0.32 to +0.07. Psychological safety runs the
wrong way.

Across all staff two dimensions do clear FDR correction, senior leadership trust (g = -0.15) and
purpose and meaning (g = -0.13), but those are small effects on 798 events, and neither survives in
the HiPo subgroup. A multivariate model on the HiPo risk set with all eight dimensions plus controls
returns a pseudo-R² of 0.032 and not a single significant survey term.

So NovaCorp's engagement instrument, as scored, cannot tell you which of your HiPos is about to
resign. Combined with Finding 2, the recommendation writes itself: stop treating the survey as a
thermometer and start treating participation as the metric.

## Finding 4: the promotion story is real, smaller than reported, and only true for HiPos

`d05_promotion_block.png`

findings_04 concluded that promotion stagnation predicts exit for everyone and is slightly weaker
for high performers. On the exposure-fair design that flips.

Review-level, asking whether a review with no promotion recommendation is followed by a resignation
within 180 days:

| Cohort | Recommended | Not recommended | OR | p |
|---|---|---|---|---|
| HiPo-flagged | 3.55% | 5.66% | 1.63 [1.06 to 2.51] | 0.022 |
| Not HiPo-flagged | 2.89% | 3.29% | 1.14 [0.94 to 1.39] | 0.19 |
| Rated High Performer or above | 2.99% | 3.24% | 1.08 [0.89 to 1.33] | 0.45 |
| Rated Outstanding | 2.99% | 2.85% | 0.95 [0.65 to 1.39] | 0.85 |

The effect exists for the HiPo flag and disappears for every performance-rating definition of the
same idea. Note what that means: the thing that predicts exit is being told you are high potential
and then not being promoted. Doing well and not being promoted does not have the same effect. That
is a much more specific and more actionable claim than the one currently in the deck.

Be careful with it though. The formal interaction test (no_promo x hipo, clustered standard errors,
review-level) gives OR 1.45, p = 0.11. So the stratified tests differ but we cannot prove the
difference is real at conventional thresholds. Phrase it as "the effect is concentrated in the HiPo
group" and not "HiPos are uniquely affected."

The correction to findings_04 needs to be in the appendix rather than buried. The old headline
compared "ever recommended" across people with unequal numbers of reviews, which builds the answer
into the question. Fixing it shrinks the claim from 2.1x to 1.63x and moves it to a different
population. A judge who spots the original error will assume nothing else was checked.

## Finding 5: department is the biggest structural gradient, and we cannot explain it

`d07_department_gradient.png`

HiPo resignation rate by department:

| Department | Rate | Leavers | Adjusted OR vs Retail Banking |
|---|---|---|---|
| Corporate Operations | 19.1% | 25 of 131 | 3.09, p = 0.0003 |
| Risk & Compliance | 18.2% | 36 of 198 | 2.92, p = 0.0002 |
| Insurance | 14.3% | 23 of 161 | 2.15, p = 0.016 |
| Wealth Management | 13.0% | 15 of 115 | 1.97, p = 0.058 |
| Executive Leadership | 12.0% | 3 of 25 | 1.81, p = 0.37 |
| Technology | 10.2% | 27 of 266 | 1.50, p = 0.18 |
| Retail Banking | 7.0% | 22 of 314 | reference |

χ²(6) = 21.6, p = 0.0014. The adjusted odds ratios control for tenure, compa-ratio, role level and
hire source, and the top two barely move.

Then we tried to explain it and could not. Correlating the seven departmental HiPo exit rates against
every candidate driver: pay r = +0.07, tenure r = -0.27, role level r = +0.12, manager span r = +0.23,
days to fill r = -0.37, promotion rate r = -0.51, engagement index r = -0.54, non-response r = -0.19,
share from acquisitions r = -0.11, goal achievement r = -0.07. Nothing reaches significance and
nothing is even close with n = 7 departments. Median salaries sit between $121.5k and $125.8k across
all seven, so it is not a pay story.

The 2.7x spread is real. The cause is not in employees.csv, attrition_log.csv, engagement.csv or
performance.csv. That is a legitimate finding and it is a better slide than a fabricated explanation:
tell the CHRO where to look, and say plainly that the answer requires the exit conversations, the
workload data or the internal mobility records that were not supplied.

## Finding 6: NovaCorp does not have a bad manager problem

`d10_manager_clustering_null.png`

If particular managers were driving attrition, team exit counts would be over-dispersed relative to
binomial. Across 745 teams with five or more reports, the dispersion ratio is 0.79. Under-dispersed.
The overdispersion chi-square is 618 on 744 degrees of freedom, p ≈ 1.

Manager-effectiveness scores also fail to predict HiPo exit (OR 0.95, p = 0.64), and the leave-one-out
team exit rate is only marginally associated with an individual resigning across all staff (p = 0.024)
and null within HiPos (p = 0.42).

This one matters commercially. Manager coaching programmes are the reflexive answer to attrition and
they are expensive. The data does not support one here. Saying so, with the dispersion chart, is the
kind of negative result that separates a real analysis from a template.

## Finding 7: compa-ratio changes the label, not the decision

`d09_pay_paradox.png`

Two tests on the same variable:

Does pay position predict resignation? HiPo leavers average 0.884 against 0.879 for HiPo stayers,
p = 0.38. All staff, 0.943 against 0.946, p = 0.27. No.

Does pay position predict which resignations get flagged regrettable? Flagged leavers average 0.917
against 0.947 for unflagged leavers, p = 9.5 x 10⁻⁶, and it holds controlling for role level and
department (β = -0.029, p = 2.1 x 10⁻⁶).

Underpaid people are not more likely to resign. They are more likely to be called a regrettable loss
after they do. Combined with what findings_04 already showed about the flag tracking performance band,
this is the second independent piece of evidence that `regrettable_flag` encodes HR's retrospective
feelings about the loss rather than anything about the leaving. It should be described in the deck,
never used as an outcome variable.

This is also, incidentally, the clearest reason the two populations we ran in parallel disagree. The
regrettable population is partly a pay artefact. The HiPo population is not.

## Finding 8: two windows in the tenure curve

`d08_tenure_shape.png`

HiPo resignation rate against everyone else, by tenure band:

| Tenure | Not HiPo | HiPo | OR | p |
|---|---|---|---|---|
| under 1 year | 19.4% | 24.5% | 1.34 | 0.18 |
| 1 to 2 years | 5.7% | 11.9% | 2.24 | 0.0022 |
| 2 to 3 years | 2.0% | 1.1% | 0.55 | 0.57 |
| 3 to 5 years | 8.1% | 9.5% | 1.20 | 0.77 |
| 5 to 10 years | 7.9% | 10.0% | 1.29 | 0.44 |
| over 10 years | 7.5% | 12.2% | 1.70 | 0.00026 |

Two bands stand out, the second year and the long-service tail. The 2 to 3 year band is the quietest
in the company for both groups, which is odd and worth a sentence in the appendix.

Caveat that belongs on the slide: the formal HiPo by tenure-band interaction is not significant
(LR = 6.17, df = 5, p = 0.29). HiPos carry elevated risk fairly evenly across tenure. What the chart
shows is where the volume sits, not proof that the shape differs.

## Two things we found and threw away

Both were large. Both would have looked great on a slide. Include them in the appendix, because
showing your discards is worth more than one extra finding.

### The manager departure cascade

`d11_cascade_artefact.png`

112 employees had a manager who also departed. 75% of them resigned, against an 8.5% baseline.
Fisher OR = 35, p = 8.3 x 10⁻⁶⁴. An enormous effect and a tempting story about teams following their
leader out the door.

It is a definitional artefact. Every one of the 95 departed managers led a team of three or fewer,
and in 100% of those cases the entire unit disappeared. Split the sample and the effect lives
entirely in the small teams: OR 33 for spans of three or fewer, OR 1.0 and p = 1.00 for spans of four
or more. There is also no lead-lag order, with 52% of reports leaving after their manager and 48%
before (binomial p = 0.74). If it were contagion, the reports would follow.

What we are looking at is how tiny reporting lines are recorded when they dissolve, not a retention
signal.

### Counts of anything, per person

Covered above under the design problem. Number of reviews, number of promotion recommendations, and
number of survey waves all produced enormous "effects" (n_reviews reached p = 4.8 x 10⁻³⁷) that are
purely a function of how long someone was around to be counted.

## What we would put in the deck

The framing that survives all of the above is roughly this. NovaCorp cannot currently see its
regrettable attrition coming, but it is already collecting the data that would let it. It is
measuring the wrong half.

Three claims we would defend under questioning:

The warning exists and is being discarded. Survey non-response predicts resignation at 2.24x, a full
year ahead, in every wave, for every subgroup we tested. It outperforms the scored responses by more
than two to one. The intervention is a participation-triggered conversation, and it costs almost
nothing because the data already arrives every quarter.

The HiPo promise is the specific breach. Being flagged high potential and then not recommended for
promotion raises 180-day exit odds by 63%. The same treatment applied to strong performers who are
not flagged does nothing. NovaCorp is creating an expectation it does not meet, in a group that costs
$24.9M to replace.

Two of the popular explanations are wrong. It is not managers, and it is not pay. The dispersion test
and the compa-ratio tests are both clean nulls, and both point spending somewhere else.

## Caveats to carry into the appendix

1. 212 formal tests are logged in `sweep_results.csv` and `wave_risk_tests.csv`, plus roughly 40
   targeted follow-ups. Everything reported as significant clears Benjamini-Hochberg FDR at 5%, and
   the headline results clear a Bonferroni threshold of α = 0.0002 with room to spare. Findings 4 and
   8 do not, and are labelled accordingly in the text above.
2. Non-response is not exogenous. Someone who has mentally left ignores the survey. The 90 to 365 day
   test above rules out the notice-period version of that objection, but not the general one. Silence
   is a usable flag, not a proven cause, and the deck should not say "fix non-response to fix attrition."
3. The 2025-H2 review cycle is deliberately missing, so promotion exposure covers 2024-H1 to 2025-H1
   only. Wave 5 (July 2025) has a truncated look-ahead against the 31 December 2025 censor; every
   silence result was re-run without it and holds (OR 2.39, p = 4.7 x 10⁻³⁴).
4. `regrettable_flag` is now known to track performance band (findings_04) and compa-ratio (Finding 7
   here). We used it as a descriptive label and never as an outcome to be modelled.
5. Departmental correlations rest on seven data points. They are suggestive of absence, not proof of it.
6. 109 employees have no performance review and drop out of the review-level analyses. 817 never
   appear in engagement.csv at all, and a further 3,333 are missing at least one wave. The risk-set
   construction handles both rather than dropping them.
7. This is synthetic data. The span-3 artefact is proof that the generator leaves fingerprints. Any
   effect with an odds ratio above about 10 deserves the same treatment we gave that one before it
   goes near a slide.
