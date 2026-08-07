# Findings Register — Broad Discovery (Phase 1)

Every number below was produced by `python src/eda_discovery.py`
(full evidence trail: `outputs/logs/eda_discovery.log`) and visualised, where a
clear business question warranted a chart, by `python src/discovery_charts.py`
(`outputs/charts/discovery/`). Governing context: `CLAUDE.md`,
`docs/analysis_plan.md`, `docs/hypothesis_register.md`,
`docs/feature_dictionary.md`.

**Status: candidate findings only.** Per `CLAUDE.md` Section 21 these are
**statistical evidence** at best (tested relationships with effect size and a
sample size) — none has been promoted to **inference** or **recommendation**.
Multiple-comparison correction (Benjamini-Hochberg) was applied within each
family of related tests (all 8 engagement dimensions tested together, etc.).
No hypothesis testing beyond this broad scan has been performed; no storyline
has been selected (see Section 3).

All manager-level findings (FR-07) are reported in aggregate only — no
individual manager, employee, or reviewer is identified anywhere in this
document or its charts, per `CLAUDE.md` Section 11.

Base population for all rate comparisons: the 13,403-employee master dataset
(`employee_analytics_master.csv`), i.e. P1+P2 from `docs/analysis_plan.md`
Section 4 (active-at-any-point during the window). "Voluntary exit rate" =
voluntary exits ÷ this base, consistently, unless stated otherwise.

---

## Section 1: Findings

### FR-01 — HiPo-flagged employees drive nearly all regrettable attrition
- **Observed pattern:** HiPo-flagged employees have a voluntary exit rate of
  12.5% vs. 8.1% for everyone else, and a **regrettable** voluntary exit rate
  of 6.3% vs. 0.6% — roughly a 10x relative difference.
- **Sample size:** n=1,210 HiPo-flagged, n=12,193 not flagged (13,403 total).
- **Effect magnitude:** Voluntary exit: χ²=27.3, p=1.8e-7, Cramér's V=0.045.
  Regrettable voluntary exit: χ²=306.3, p=1.4e-68, Cramér's V=0.151 (the
  largest effect size found anywhere in this scan).
- **Business significance:** The brief's $22–25M "regrettable attrition"
  component is framed as losing high-value people. This is the first direct,
  well-powered confirmation of *who* those high-value people actually are —
  and it is not who a naive read of "high performer" would suggest (see FR-20
  contrast below).
- **Potential explanation:** HiPo employees are, by construction, the most
  externally marketable segment of the workforce; if internal
  investment/recognition lags the external market's interest in them, they
  are also the segment best positioned to act on a better offer.
- **Alternative explanation:** Reverse composition effect — HiPo status may
  correlate with tenure/role/department in ways not yet controlled for (e.g.
  HiPo concentration in high-turnover departments or entities). Not yet
  tested with a multivariable model.
- **Further test required:** Logistic regression of regrettable exit on
  `hipo_flag` controlling for department, role_level, legacy_entity, and
  compa_ratio (HP-1 in the hypothesis register); triangulate with FR-19
  (promotion signal) and engagement scores specific to this segment (HP-3).
- **Potential financial exposure:** 76 regrettable voluntary exits among HiPo
  employees (of 153 company-wide) — HiPo employees account for **~50% of all
  regrettable attrition from 9% of the workforce**. At the brief's 1.5x salary
  replacement multiplier, even a rough average-salary estimate puts this
  segment's share of the $22–25M component in the high single-digit millions;
  precise costing deferred to Phase 3.
- **Chart:** `outputs/charts/discovery/01_hipo_regrettable_exit.png`

### FR-02 — Entity_B's attrition gap is not a department artefact
- **Observed pattern:** Entity_B's voluntary exit rate (11.9%) exceeds every
  other legacy entity, and it holds this rank in **5 of 6** departments where
  it has an adequately-sized presence (Wealth Management, Insurance,
  Corporate Operations, Technology, Risk & Compliance) — not concentrated in
  one business area.
- **Sample size:** n=1,884 Entity_B employees; per-department subgroups range
  n=199–463.
- **Effect magnitude:** Company-wide χ²=38.1, p=2.7e-8, Cramér's V=0.053.
  Department-level rates for Entity_B range 9.8%–13.6%, consistently above
  the NovaCorp-Origin rate in the same department (6.9%–9.3%).
- **Business significance:** Rules out "Entity_B just happens to sit in a
  high-turnover department" as the explanation — directly relevant to
  evaluating management's Q2 FY2026 stabilisation timeline (H-Mgmt-2).
- **Potential explanation:** An entity-level (not department-level) driver —
  consistent with a cultural/trust or acquisition-integration mechanism
  (see FR-04).
- **Alternative explanation:** An uncontrolled entity-level confound other
  than department (e.g. role_level mix, hire-cohort timing) could still be
  driving this; role_level was not controlled for in this pass.
- **Further test required:** AI-1/AI-4 multivariable model controlling for
  role_level and tenure simultaneously.
- **Potential financial exposure:** Entity_B's rate vs. the NovaCorp-Origin
  baseline (11.9% vs. 8.1%) implies roughly 70 "excess" voluntary exits/year
  in this cohort alone at current headcount — full costing in Phase 3.
- **Chart:** `outputs/charts/discovery/02_attrition_by_legacy_entity.png`

### FR-03 — Entity_C is promoted at roughly half the rate of every other cohort, at every level
- **Observed pattern:** Promotion-recommendation rate for Entity_C is
  dramatically lower than NovaCorp-Origin/Entity_A/Entity_B at **every**
  role level: L1 14.3% vs. 33–34%; L2 13.3% vs. 37–41%; L3 11.1% vs. 36–41%;
  L4 20.0% vs. 34–47%.
- **Sample size:** n=1,014 Entity_C employees with a performance record;
  level-specific cells range n=15–764 (all ≥15, per-level minimum applied).
- **Effect magnitude:** Roughly 2–3x lower promotion-recommendation
  probability than the best-performing comparison cohort, holding at every
  level — a large, consistent, role-level-controlled gap.
- **Business significance:** Management's Annual Report describes Entity_C as
  "within normal range for an early-stage integration," based only on its
  attrition rate (9.3%). This finding is **independent of and not mentioned
  in that narrative** — a structural progression gap for the most recently
  acquired cohort that attrition-rate monitoring alone would never surface.
  Directly relevant to `CLAUDE.md`'s standing instruction to test, not adopt,
  management's framing.
- **Potential explanation:** New-entity onboarding into the promotion process
  (calibration committees, manager unfamiliarity with new-entity staff,
  performance-review cadence lag) may under-recommend recently-acquired
  employees regardless of merit.
- **Alternative explanation:** Entity_C may look genuinely different on an
  unobserved productivity/tenure dimension — but performance RATING mix is
  nearly identical across all four entities (FR-12), which weighs against a
  merit-based explanation.
- **Further test required:** CP-2 in the hypothesis register — a
  tenure-controlled (not just role-level-controlled) regression, since
  Entity_C's tenure distribution is mechanically compressed (acquired late
  FY2024).
- **Potential financial exposure:** Not a direct cost line, but a leading
  indicator for future regrettable attrition in this cohort as career
  frustration compounds — and an ethics/equity exposure regardless of
  downstream cost (`CLAUDE.md` Section 11).
- **Chart:** `outputs/charts/discovery/03_promotion_rate_by_entity_and_level.png`

### FR-04 — Entity_B's attrition tracks leadership trust, not pay
- **Observed pattern:** Entity_B has the **highest** median compa_ratio of
  any cohort (0.96, tied with Entity_A/C, all above NovaCorp-Origin's 0.94) —
  it is not underpaid. It has the **lowest** mean `senior_leadership_trust`
  latest score of any cohort (3.06 vs. 3.26–3.37 elsewhere), a clear outlier.
  Within Entity_B itself, leavers are not paid less than stayers at any role
  level tested (role_level 2 leavers were paid *more* than stayers, p=0.014).
- **Sample size:** n=1,884 Entity_B employees for the aggregate comparisons;
  within-entity role-level tests n=27–1,189.
- **Effect magnitude:** compa_ratio gap: +0.02 favouring Entity_B vs.
  NovaCorp-Origin. Trust gap: −0.27 to −0.31 vs. every other cohort.
- **Business significance:** This is a direct test of H-Mgmt-2 / hypothesis
  AI-1. It redirects the likely intervention: a compensation correction for
  Entity_B (the naive read of "post-acquisition pay misalignment") would be
  **spending against the wrong driver** on this evidence. A
  leadership/trust-focused intervention is better supported.
- **Potential explanation:** Post-acquisition leadership changes, unclear
  reporting lines, or unmet cultural-integration commitments erode trust in
  senior leadership specifically (not managers generally — `career_development`
  shows a much smaller gap: 3.32 vs. 3.36–3.38).
- **Alternative explanation:** `senior_leadership_trust` could itself be
  downstream of the same unobserved factor driving attrition (reverse
  causality / common cause) rather than a driver in its own right — this scan
  cannot establish direction.
- **Further test required:** AI-1's full nested-model comparison (entity-only
  vs. entity+compa_ratio vs. entity+compa_ratio+engagement), and an explicit
  reverse-causality discussion per `CLAUDE.md` Section 19 before any causal
  claim.
- **Potential financial exposure:** Reallocating a planned Entity_B
  compensation-correction budget toward a leadership/culture intervention
  could avoid misdirected spend of an unknown but potentially material size —
  quantify once a specific proposed intervention exists.
- **Chart:** `outputs/charts/discovery/04_entity_b_pay_vs_trust.png`

### FR-05 — Survey silence predicts departure better than any survey score
- **Observed pattern:** Employees who never responded to any eligible survey
  wave have a 24.5% voluntary exit rate, vs. 8.9% for those whose most recent
  eligible wave was a non-response, vs. 6.0% for recent responders — a clean,
  monotonic gradient. No individual engagement *score* dimension shows an
  effect anywhere near this size (largest score-based gap: −0.11 points on
  senior_leadership_trust, q=0.063, not significant after correction).
- **Sample size:** n=506 never-responded, n=2,224 recent non-response,
  n=10,366 recent responders (13,096 with ≥1 eligible wave).
- **Effect magnitude:** Never-responded vs. responded: χ²=232.3, p=1.9e-52,
  Cramér's V=0.133 — the second-largest effect size in this entire scan.
- **Business significance:** NovaCorp's current 81.7% survey response rate is
  reported as a participation metric. This finding says the **non-responding
  ~18%** is not noise to shrug off — it is a substantially higher-risk
  population than anything visible in the response data HR currently reviews.
- **Potential explanation:** Disengagement severe enough to predict departure
  may manifest as withdrawal from optional company processes (the survey)
  before it manifests as a low score on a survey the employee still bothers
  to complete.
- **Alternative explanation:** Reverse timing — some non-response could
  reflect employees already mentally checked out post-resignation-decision
  (though `CLAUDE.md`/audit confirms no raw survey postdates an actual exit,
  so this would have to be pre-exit disengagement, not post-decision apathy
  captured after the fact).
- **Further test required:** SR-1/SR-4 — rule out contract_type/tenure access
  effects as the driver of non-response itself before treating it as a pure
  engagement signal (the audit already found some legacy-entity variation in
  response rates — DQ-006 — that must be controlled for).
- **Potential financial exposure:** Not separately costed; this is
  fundamentally a **measurement/early-warning-system finding** — its value is
  in what it would let NovaCorp act on earlier, not a standalone dollar
  figure.
- **Chart:** `outputs/charts/discovery/05_nonresponse_leading_indicator.png`

### FR-06 — High performers stalled without a promotion signal leave nearly 2x as often
- **Observed pattern:** Among promotion-eligible, currently high-performing
  employees (High Performer/Outstanding rating), those who have **never**
  received a promotion recommendation leave voluntarily at 9.6%, vs. 5.3% for
  those who have.
- **Sample size:** n=686 "stalled," n=655 "advancing" (1,341 total).
- **Effect magnitude:** χ²=8.2, p=0.0042, Cramér's V=0.078.
- **Business significance:** A concrete, internally-controllable process
  lever (promotion review cadence/visibility) tied to a nearly 2x attrition
  gap in exactly the population the company can least afford to lose.
- **Potential explanation:** Perceived career stagnation despite demonstrated
  performance drives external job search.
- **Alternative explanation:** "Never recommended" may correlate with
  department/role_level ceiling effects (e.g., already near the top of a
  narrow role family) rather than a generic process failure — not yet
  controlled for.
- **Further test required:** CP-1/CP-4 — Cox proportional-hazards model
  controlling for department, role_level, and tenure; note the CP-series
  feasibility caveat that no true promotion *event* exists in the data, only
  the recommendation flag used here as a proxy (`docs/feature_dictionary.md`
  Section 7).
- **Potential financial exposure:** 686 employees at elevated risk; even a
  partial narrowing of the 9.6%→5.3% gap for this specific, identifiable,
  high-value segment is a targeted, high-ROI candidate — full costing in
  Phase 3.
- **Chart:** `outputs/charts/discovery/06_stalled_promotion_pipeline.png`

### FR-07 — Attrition varies sharply by manager, but "concentration" needs a caveat
- **Observed pattern:** Across 745 managers with ≥5 direct reports, team
  voluntary-exit rates range from 0% (the modal outcome — 391 of 745 managers,
  52%) to 60%. A between-manager variance-decomposition proxy attributes
  ~12.2% of total variance in voluntary exit to which manager an employee has
  (R²-like = 0.1215) — above the 0.05–0.10 threshold the hypothesis register
  called "practically meaningful" (MG-1).
- **Sample size:** n=745 managers (≥5 reports), 5,454 employees in the pool.
- **Effect magnitude:** R²-like = 0.122 (unadjusted for department/entity
  composition — see caveat below).
- **Business significance:** If even partly causal, manager quality/practice
  is a distinct, trainable lever independent of the department- and
  entity-level findings above.
- **Potential explanation:** Genuine variation in manager practice
  (recognition, workload management, advocacy for direct reports).
- **Alternative explanation — important, and visible in the chart itself:**
  the histogram's large spike at exactly 0% is consistent with **small teams
  and a low base rate mechanically producing zero exits for most managers by
  chance**, not necessarily uniformly excellent management. A separate
  concentration check (top decile of managers by regrettable-exit rate
  "holding" 100% of all regrettable exits) is very likely this same sparse-count
  artifact — with a rare outcome spread across many small teams, *any* manager
  with even one regrettable exit is mechanically pushed into the "top" group.
  This number is reported here specifically to flag it as **probably not a
  genuine finding** without correction, not to feature it as one.
- **Further test required:** MG-1/MG-2's full specification — a mixed-effects
  model with department and legacy_entity as fixed effects and manager as a
  random effect, plus empirical-Bayes shrinkage before any "outlier manager"
  claim is made. The unadjusted 12.2% figure is an upper bound, not a clean
  manager effect.
- **Potential financial exposure:** Not costed — this is a methodology-gated
  finding; a shrinkage-corrected re-estimate is required before sizing it.
- **Chart:** `outputs/charts/discovery/07_manager_level_dispersion.png`

### FR-08 — An apparent early-tenure attrition cliff, with a significant interpretation caveat
- **Observed pattern:** Employees with recomputed tenure of 0–6 months show a
  60.2% voluntary exit rate, dramatically higher than every other tenure band
  (7–12mo: 8.4%; 13–24mo: 6.9%; 25–60mo: 3.5%; 60mo+: 8.0%).
- **Sample size:** n=377 in the 0–6mo band (n=1,117–7,380 in other bands).
- **Effect magnitude:** Roughly 7–17x the rate of any other band.
- **Business significance:** If taken at face value, this would be the
  single largest attrition signal in the dataset — but it should not be taken
  at face value (see below).
- **Potential explanation:** Genuine early-tenure flight risk (poor
  onboarding, unmet expectations) — plausible and consistent with HI-4's
  design in the hypothesis register.
- **Alternative explanation — the dominant concern:** This is a
  **right-censoring artefact.** The 0–6mo band pools two very different
  populations: (a) employees who left within 6 months at *any point* across
  the full 2-year window, and (b) employees hired very recently who are still
  active. Population (b) can only be drawn from the last ~6 months of the
  window (a small pool), while population (a) draws from the entire 2-year
  window — mechanically inflating the apparent rate. `CLAUDE.md` Section 12
  flags exactly this risk for tenure-banded comparisons.
- **Further test required:** Proper Kaplan–Meier survival curves with
  right-censoring handled correctly (as HI-1/HI-4 already specify), not a
  naive cross-sectional tenure-band rate.
- **Potential financial exposure:** Not costed at this stage — the naive rate
  above should not be used for any dollar estimate.
- **Chart:** `outputs/charts/discovery/08_tenure_band_exit_rate.png` (chart
  title carries the same caveat)

### FR-09 — A wave of very early exits clusters right after each entity's own acquisition period
- **Observed pattern:** Among employees with `hire_source == 'acquisition'`,
  voluntary exits with <12 months' (recomputed) tenure occur at 9.1%
  (Entity_B) and 8.4% (Entity_C) — vs. 0.8% for Entity_A and <0.6% for every
  non-acquisition hire source company-wide. Investigating further: these
  employees' `hire_date` values cluster tightly in the 1–2 quarters
  immediately following each entity's own acquisition period (Entity_A hires
  ~2023 Q2–Q4, Entity_B ~2024 Q2–Q3, Entity_C ~2025 Q2), and their exit dates
  are spread out (not batch-clustered), consistent with genuine individual
  departures rather than a single data artefact.
- **Sample size:** n=171 (Entity_B), n=85 (Entity_C), n=16 (Entity_A) early
  acquisition-sourced voluntary exits, out of 5,344 total acquisition-sourced
  employees.
- **Effect magnitude:** χ²=328.8, p=6.8e-70, Cramér's V=0.157 (largest effect
  size found in the entire discovery scan) for early-voluntary-exit rate by
  hire_source overall, driven almost entirely by this pattern.
- **Business significance:** Read generously, this is a large, previously
  unquantified population-level signal of employees leaving very shortly
  after joining via acquisition — a direct integration-cost and cultural-fit
  signal the Annual Report does not surface at this resolution.
- **Potential explanation:** Genuine rapid post-acquisition attrition —
  employees who did not want to work for the acquiring organisation leave as
  soon as practicable after the transition completes.
- **Alternative explanation — must be resolved before this is trusted:** the
  semantics of `hire_date` for `hire_source == 'acquisition'` employees are
  not fully documented in the brief. If `hire_date` reflects a
  system-migration/onboarding-into-NovaCorp-systems date rather than each
  individual's true original hire date at the acquired company, "tenure"
  for this subgroup would be mechanically compressed for reasons unrelated
  to any employee's actual decision to leave quickly.
- **Further test required:** Confirm the exact operational definition of
  `hire_date` for acquisition-sourced records (data dictionary follow-up);
  cross-reference against `days_to_fill` and any available legacy
  `data_source_system` migration-date metadata before treating this as a
  clean "quit fast after acquisition" behavioural finding rather than a
  labelling artefact.
- **Potential financial exposure:** If genuine, 272 early exits concentrated
  in acquisition-sourced staff represent a meaningful, front-loaded slice of
  both the hiring-inefficiency and regrettable-attrition cost components —
  sizing deferred until the hire_date ambiguity above is resolved.
- **Chart:** `outputs/charts/discovery/09_post_acquisition_rapid_exits.png`

### FR-10 — Pay relative to peers shows no clean gradient with attrition
- **Observed pattern:** Splitting employees into compa_ratio quartiles
  *within their own role_level* (a loose control for seniority), voluntary
  exit rates are 8.5% (Q1, lowest pay), 9.0% (Q2), 8.2% (Q3), 8.0% (Q4,
  highest pay) — flat, and not even monotonic in the expected direction.
- **Sample size:** ~3,150–3,750 employees per quartile.
- **Effect magnitude:** Negligible — the full range across quartiles is
  1 percentage point, well within noise given the CIs.
- **Business significance:** A meaningful **null finding**: at the
  whole-company, univariate level, being relatively underpaid vs. peers at
  the same level does not show the clean "pay drives attrition" relationship
  hypothesis CM-1 anticipated. This tempers expectations for a broad,
  company-wide compensation-correction recommendation.
- **Potential explanation:** Compensation may matter only in specific,
  narrower segments (e.g. combined with high performance — hypothesis CM-4)
  rather than as a general company-wide driver.
- **Alternative explanation:** A purely within-role_level quartile split is a
  coarse control; a true multivariable model (controlling for department,
  tenure, and performance simultaneously) could still reveal a real but
  currently-masked relationship.
- **Further test required:** CM-1's full logistic regression specification
  before concluding compensation is not a driver anywhere in the business —
  this finding rules out only the crude, company-wide univariate version of
  that claim.
- **Potential financial exposure:** Tempers (does not eliminate) the case for
  a broad compensation-correction line item; a narrower, targeted case (e.g.
  FR-01's HiPo segment, or CM-4's "underpaid star" segment) remains untested
  and could still be material.
- **Chart:** `outputs/charts/discovery/10_compa_ratio_quartile_flat.png`

---

## Section 2: Additional Findings (not individually charted — each answers a narrower or context-setting question)

### FR-11 — Graduate hires, not agency hires, show the highest overall exit rate
- **Observed pattern:** Voluntary exit rate by hire source: graduate 10.7%,
  acquisition 9.1%, referral 7.9%, direct 7.9%, **agency 7.6% (lowest)**.
- **Sample size:** n=683 (graduate) to 5,344 (acquisition).
- **Effect magnitude:** χ²=12.4, p=0.015, Cramér's V=0.030 (modest but the
  ranking itself is the notable part).
- **Business significance:** Directly contradicts the common assumption
  (and the hypothesis register's own HI-1 framing) that agency-sourced hires
  are the "poor fit" channel. On this data, agency hires are the *most*
  stable of the five channels; graduates are the least.
- **Potential explanation:** Graduates may face a steeper early-career
  expectation-mismatch; agencies may pre-screen for role fit effectively.
- **Alternative explanation:** Graduate hires skew toward lower tenure/younger
  age bands generally, which independently correlates with higher mobility —
  not yet controlled for.
- **Further test required:** HI-1 with department/role_level/tenure controls
  before revising the hiring-channel narrative.
- **Potential financial exposure:** Reframes where any hiring-efficiency
  budget should focus — likely graduate-programme onboarding/retention, not
  agency-vetting quality, contrary to the initial hypothesis framing.

### FR-12 — Performance rating mix is nearly identical across hire_source and legacy_entity
- **Observed pattern:** The distribution of `performance_latest_rating`
  (Below Expectations/Meets/High Performer/Outstanding/Unsatisfactory) varies
  by at most 1–2 percentage points across all 5 hire sources and all 4
  legacy entities.
- **Sample size:** Full population, 13,294 with a performance record.
- **Effect magnitude:** Negligible — this is reported as a **contextual null
  finding**, not a standalone effect.
- **Business significance:** Strengthens FR-03 and FR-11: wherever a group
  (Entity_C, graduates, etc.) shows a different outcome (promotion rate,
  attrition rate), it is *not* because that group is objectively rated as
  lower-performing. This weighs against merit-based explanations for the
  disparities found elsewhere.
- **Potential explanation / alternative explanation:** N/A — this is a
  supporting/ruling-out finding, not a primary one.
- **Further test required:** None on its own; cited as supporting evidence
  for FR-03.
- **Potential financial exposure:** None directly.

### FR-13 — Employees with a "consecutive deterioration" flag actually leave *less*, likely a tenure/survivorship confound
- **Observed pattern:** Across all 8 engagement dimensions, employees flagged
  with 2+ consecutive wave-over-wave score declines have a **lower**
  voluntary exit rate (2.1%–2.7%) than those without the flag (5.9%–6.2%) —
  the opposite direction of the naive "declining engagement predicts exit"
  expectation.
- **Sample size:** n=11,157 with ≥3 eligible waves (required to compute the
  flag at all).
- **Effect magnitude:** Strong and consistent: Cramér's V 0.070–0.089 across
  all 8 dimensions, all p<1e-13 after correction.
- **Business significance:** A genuinely counter-intuitive result that must
  not be reported as "declining engagement is protective" without the caveat
  below — doing so would be a serious overclaim.
- **Potential explanation:** None directly — see alternative explanation,
  which is assessed as the dominant one.
- **Alternative explanation (assessed as primary):** Computing this flag
  requires ≥3 eligible waves, which by construction requires longer tenure.
  Longer-tenured employees have a structurally lower baseline attrition rate
  (FR-08's 60mo+ band: 8.0% vs. shorter bands) than the always-short-tenured
  population that can never even be evaluated for this flag. The comparison
  group ("not flagged") still includes many short-tenure, high-base-rate
  employees, mechanically producing this reversal.
- **Further test required:** Repeat the comparison within fixed tenure bands
  before drawing any conclusion about the direction of this relationship.
- **Potential financial exposure:** None until re-tested — do not use this
  finding as-is for any recommendation.

### FR-14 — Engagement score volatility is lower among leavers, likely the same confound as FR-13
- **Observed pattern:** Median wave-to-wave volatility (standard deviation)
  is lower for voluntary leavers (0.39–0.41) than stayers (0.44) across all 8
  dimensions, all statistically significant.
- **Sample size:** n=539 leavers with ≥2 responses, n=10,488 stayers.
- **Effect magnitude:** Small-to-moderate, consistent direction across all 8
  dimensions.
- **Business significance / caveat:** Same mechanism as FR-13 — volatility
  requires ≥2 data points, and leavers with only 1–2 available waves
  (shorter tenure) are systematically excluded from this comparison, likely
  explaining the direction. Reported for completeness, not as an
  independent, trustworthy signal.
- **Further test required:** Tenure-controlled re-test, as FR-13.
- **Potential financial exposure:** None until re-tested.

### FR-15 — The specific "responder→non-responder transition" pattern adds nothing beyond recent non-response
- **Observed pattern:** Having ever transitioned from responding to
  non-responding shows no significant relationship with voluntary exit
  (5.9% vs. 6.2%, χ²=0.48, p=0.49) once considered on its own.
- **Sample size:** n=11,792 employees with ≥2 eligible waves.
- **Business significance:** A useful **negative finding** for hypothesis
  SR-3 — the specific "going dark" transition event does not add predictive
  value beyond simply knowing whether the *most recent* wave was a
  non-response (FR-05 already captures the useful signal).
- **Further test required:** None additional — this narrows, rather than
  expands, where the team should focus engagement-based early-warning work.
- **Potential financial exposure:** None — informs scope, not cost.

### FR-16 — Span of control shows no relationship with attrition or manager effectiveness
- **Observed pattern:** Manager team size correlates with neither team
  voluntary-exit rate (Spearman r=−0.014, p=0.71) nor average manager
  effectiveness score (r=−0.010, p=0.80).
- **Sample size:** n=745 managers (≥5 reports).
- **Business significance:** A clean rejection of hypothesis MG-4 in this
  data — span-of-control-driven overload is not a supported explanation for
  manager-level variation (FR-07's ~12% manager-level variance must come from
  something other than team size).
- **Further test required:** None on span of control specifically; MG-1's
  mixed-effects model remains the right next step to find what *does* explain
  the manager-level variance.
- **Potential financial exposure:** None — de-prioritises a possible
  intervention (span redesign) rather than costing one.

### FR-17 — Acting appointments show a directionally worse profile, but are underpowered
- **Observed pattern:** Employees under an acting/interim manager show lower
  team `manager_effectiveness` (median 3.29 vs. 3.39, p=0.39) and the acting
  managers themselves show higher personal voluntary-exit rate (12.2% vs.
  8.4%, p=0.31) — both directionally consistent with the hypothesis, neither
  statistically significant.
- **Sample size:** n=82 acting-appointment employees, n=166 employees under
  an acting manager — both well below the n≥30-per-group comfort threshold
  for a company-wide claim, though not below the hard minimum.
- **Business significance:** Suggestive, not conclusive. Reported per
  `CLAUDE.md` Section 12's instruction to state sample-size-driven
  inconclusiveness explicitly rather than silently drop a plausible pattern.
- **Further test required:** MG-3 as specified — a larger, better-powered
  test or a longer observation window would be needed to resolve this either
  way.
- **Potential financial exposure:** Not costed — insufficient evidence to
  size.

### FR-18 — Being formally promotion-eligible, on its own, shows no attrition relationship
- **Observed pattern:** `promotion_eligible == True` employees have a
  voluntary exit rate of 8.6% vs. 8.4% for ineligible employees — no
  meaningful difference (χ²=0.13, p=0.72).
- **Sample size:** n=3,425 eligible, n=9,978 ineligible.
- **Business significance:** The eligibility *flag* alone carries no signal —
  it is receiving an actual promotion *recommendation* (FR-06) that matters,
  not nominal eligibility. This sharpens where any promotion-process fix
  should focus (converting eligibility into real recommendations/movement,
  not expanding who is nominally eligible).
- **Further test required:** None additional — this and FR-06 together are
  sufficiently clear on their own.
- **Potential financial exposure:** None directly — a scoping finding for
  FR-06's recommendation.

### FR-19 — The HiPo programme has some teeth, but not enough
- **Observed pattern:** HiPo-flagged employees receive a promotion
  recommendation at nearly double the rate of everyone else (49.7% vs.
  30.6%, at least once), yet still show dramatically higher regrettable
  attrition (FR-01).
- **Sample size:** n=1,195 HiPo with a performance record, n=12,099 not
  flagged.
- **Business significance:** Rules out "the company simply ignores its HiPo
  population" as the explanation for FR-01 — the programme does allocate more
  promotion signal to this group. The regrettable-attrition problem persists
  anyway, which points toward either (a) the promotion signal arriving too
  slowly relative to external offers, or (b) non-promotion factors
  (compensation timing, engagement, direct competitor recruiting pressure on
  a visibly-flagged population) dominating.
- **Further test required:** HP-3/HP-4 as specified in the hypothesis
  register — compare time-to-recommendation and engagement trajectories
  specifically within the HiPo population.
- **Potential financial exposure:** Same population as FR-01; this finding
  affects *what kind* of intervention is likely to work (faster/bigger, not
  simply "more"), not the size of the exposure itself.

### FR-20 — Company-wide, salary and compa_ratio barely differ between leavers and stayers; tenure does, modestly
- **Observed pattern:** Median salary: leavers $122,400 vs. stayers $122,700
  (p=0.42, not significant). Median compa_ratio: 0.940 vs. 0.950 (p=0.28, not
  significant). Median tenure: leavers 78 months vs. stayers 97 months
  (p=3.3e-18, significant but modest in practical terms given the wide IQRs
  on both sides: leavers [11, 271], stayers [27, 280]).
- **Sample size:** n=1,133 voluntary leavers, n=12,003 active stayers.
- **Business significance:** Sets the baseline against which FR-01 (HiPo),
  FR-04 (Entity_B trust), and FR-06 (stalled promotion) all stand out as the
  real, specific signals — pay and raw tenure alone are weak, non-specific
  differentiators company-wide, consistent with FR-10's null finding.
- **Further test required:** None additional — a context-setting finding.
- **Potential financial exposure:** None directly.

---

## Section 3: Top 10 Candidate Storylines (ranked — NOT a final selection)

Ranked qualitatively on the `docs/analysis_plan.md` Section 8 criteria
(evidence strength, financial materiality, tractability, business value,
strategic relevance, novelty, ethical defensibility) as they currently stand
— pre-Phase-2 validation. Order may change once each is formally tested;
**no storyline has been chosen.**

**⚠ These rankings were assigned BEFORE the adversarial review in Section 4.
Six of the ten did not survive it as originally framed. The "Post-adversarial
verdict" column is authoritative; this table's original "why it ranks here"
column is left unedited as a historical record of the pre-review reasoning.
See Section 4 for the full destruction analysis and Section 5 for what
actually survives.**

| Rank | Finding(s) | Why it ranks here (pre-review) | Post-adversarial verdict |
|---|---|---|---|
| 1 | **FR-01** — HiPo → regrettable attrition | Largest effect size in the entire scan (Cramér's V 0.151), directly answers the brief's central "are we losing our best people" question, highly actionable, contradicts the more obvious "high performer rating" framing (RA-3-adjacent null result) — high novelty. | **ROBUST** |
| 2 | **FR-09** — Post-acquisition rapid exits | Largest chi-square effect size found (V=0.157), ties directly to the Annual Report's own acquisition-integration priority, entirely absent from management's narrative — but carries a real open question (hire_date semantics) that must be resolved first. | **REJECT** |
| 3 | **FR-03** — Entity_C promotion gap | Strong, consistent, role-level-controlled effect; directly contradicts management's "Entity_C is fine" framing; ethically significant regardless of downstream cost. | **REJECT** |
| 4 | **FR-04** — Entity_B: trust not pay | Directly resolves a named management hypothesis (H-Mgmt-2) with a clean, well-evidenced answer that redirects likely spend toward a cheaper, more targeted fix. | **ROBUST** |
| 5 | **FR-06 / FR-18** — Stalled promotion pipeline | Clean, actionable, internally-controllable lever with a clear at-risk population size (n=686). | **WEAK** |
| 6 | **FR-05** — Non-response as leading indicator | Second-largest effect size found; genuinely novel (nobody currently monitors non-response as a signal); directly actionable as a process change. | **ROBUST** |
| 7 | **FR-02** — Entity_B's department-robust gap | Reinforces #4; rules out the most obvious confound (department mix) for the Entity_B story. | **ROBUST** |
| 8 | **FR-07** — Manager-level variance (~12%) | Large potential lever, but explicitly gated on a shrinkage-corrected re-estimate before it can be trusted or sized — ranks below fully-tested findings for now. | **PROMISING BUT UNPROVEN** |
| 9 | **FR-11** — Hiring-channel reframe (graduates, not agency) | Overturns an assumption embedded in the hypothesis register itself; redirects hiring-efficiency investment; moderate effect size. | **ROBUST** (core 4-channel claim only — see caveat in Section 4) |
| 10 | **FR-08 / FR-13 / FR-14** — Tenure/trajectory confound family | Not a storyline to *act* on, but a methodologically important cluster: these findings show where naive analysis would mislead (censoring, survivorship), and must inform how any final storyline's evidence is presented so it survives scrutiny. | **REJECT** (as actionable findings; confirmed and reinforced as methodological warnings) |

**Findings not in the top 10 but worth carrying into Phase 2 regardless:**
FR-10 (compensation null result — tempers a likely-tempting but unsupported
company-wide pay narrative), FR-16/FR-17 (rule out span-of-control and
underpower acting-appointment claims, respectively), FR-19 (nuances #1),
FR-12/FR-15/FR-20 (context/negative findings that strengthen the case for
the findings above by ruling out simpler explanations).

**No final storyline has been selected.** Per `docs/analysis_plan.md`
Section 2, Phase 2 (formal hypothesis testing against the pre-registered
`docs/hypothesis_register.md` methods, with confound controls and multiple-
comparison discipline) is required before any of the above is presented as
more than a well-evidenced candidate.

---

## Section 4: Adversarial Review — Hostile Statistician Pass

**Posture for this section: assume every finding above is wrong until it
proves otherwise.** Each of the 10 findings ranked in Section 3 was
re-attacked using the checks below, computed fresh
(`src/adversarial_review.py`, a one-off stress-test script — not part of the
reusable pipeline, output not otherwise persisted beyond this section).
Threats tested, per finding, drawn from: denominator errors, small samples,
confounding, Simpson's paradox, survivorship bias, selection bias,
retrospective leakage, temporal ambiguity, missing-data bias, multiple
comparisons, spurious correlation, manager/department composition, role-level
composition, salary/tenure effects, acquisition-cohort effects, survey
response bias.

**Headline result of this pass: a previously undocumented, high-severity data
issue was found that invalidates two of the ten findings outright and
weakens a third.** See the boxed finding immediately below before reading the
individual verdicts — it applies to more than one of them.

### ⚠ Cross-cutting discovery: `hire_date` is not a reliable tenure origin for acquired-entity employees

Re-examining `hire_date` for the full (not just the early-exit subset of)
Entity_A/B/C populations:

| Entity | `hire_date` distribution |
|---|---|
| Entity_A (n=1,950) | **100%** dated 2023 |
| Entity_B (n=1,884) | **100%** dated 2024-Q2 or 2024-Q3 |
| Entity_C (n=1,014) | **100%** dated 2025-Q2 |

Every single employee in each acquired cohort carries a `hire_date` clustered
in a one-to-two-quarter window matching that entity's approximate acquisition
period — not a distribution of real historical hire dates. Two readings are
possible, and the data alone cannot distinguish them:

1. **A data-generation artefact** — `hire_date` should represent true
   original employment start and does not, for ~36% of the workforce
   (4,848 of 13,403 employees).
2. **A deliberate, legitimate convention** — `hire_date` represents "date
   became a NovaCorp-administered employee," resetting at acquisition even
   though the person may have a longer career at the legacy entity. This is
   a real convention some organisations use.

**Either way, the practical consequence is the same: `tenure_months` (and
therefore `tenure_months_recomputed`, and any early-tenure/"days since hire"
framing) for Entity_A/B/C employees measures time since an acquisition-linked
administrative event, not necessarily the individual's real employment
history.** This was not caught by the original data-quality audit (which
tested internal consistency between `hire_date` and `tenure_months`, not
whether `hire_date` itself was a meaningful, individually-varying date) — it
surfaces only when the full distribution of `hire_date` within an entity is
examined, which this adversarial pass did and the original discovery pass did
not. **This is logged as a new, standalone data-quality issue and should be
added to `outputs/tables/data_quality_issues.csv` and
`docs/decision_log.md` in a future audit-maintenance pass** (not done in this
document, which is scoped to the findings register).

This single issue is the primary reason FR-09 is rejected and FR-03 is
rejected outright below, and it reinforces (independently of the reasoning
already in the original write-up) why FR-08/13/14 were right to be
self-flagged as unreliable.

---

### FR-01 — HiPo → regrettable attrition: **ROBUST**

- **Confounding / composition (department, entity, role_level):** HiPo
  prevalence is nearly flat across department (7.4%–10.9%) and legacy_entity
  (8.7%–9.3%) — HiPo is not a proxy for "works in a high-turnover department"
  or "belongs to a particular acquisition cohort."
- **Simpson's paradox check:** the regrettable-exit gap (HiPo vs. not) holds
  in the **same direction at every role_level tested** (L1: 6.4% vs. 0.6%;
  L2: 3.8% vs. 0.6%; L3: 12.8% vs. 0.8%; L4: 9.5% vs. 1.2%) and in **every
  one of the 7 departments** (range 2.9%–12.2% for HiPo, 0.5%–0.9% for
  non-HiPo) — no stratum reverses or nullifies the pooled result.
- **Small sample / denominator:** even the smallest stratified cell
  (L4 HiPo, n=21) is directionally consistent with the larger cells; the
  headline comparison itself (n=1,210 vs. 12,193) is well powered.
- **Salary/tenure effects:** median tenure is similar between groups (86.5 vs.
  97 months) — not a large enough gap to plausibly explain a 10x rate
  difference.
- **Retrospective leakage:** `hipo_flag` is a pre-exit, employees.csv-level
  field, not sourced from `attrition_log.csv` — clean on this axis by
  construction (`docs/feature_dictionary.md` Section 5).
- **What still isn't tested:** true multivariable joint control (all
  covariates simultaneously) and reverse causality (does being flagged HiPo
  *change* an employee's own behaviour/expectations, confounding any later
  causal claim). This is why the verdict is ROBUST **as an association**, not
  a certified causal driver — that step is Phase 2's job.
- **Verdict: ROBUST.** This is the finding in the entire set that survived
  the most stratification cuts without moving.

### FR-09 — Post-acquisition rapid exits: **REJECT**

- **Temporal ambiguity / acquisition-cohort effects (fatal):** see the boxed
  discovery above. The entire "early exit" framing rests on
  `tenure_months < 12`, and for the Entity_B/C employees driving this finding,
  `tenure_months` is measured from a `hire_date` that is identical (to the
  quarter) for their whole cohort — not from each individual's actual
  employment start. The finding cannot distinguish "people who quit within a
  year of being hired" from "people who quit within a year of an
  administrative re-dating event applied to everyone."
- **Selection / apples-to-oranges comparison:** the original write-up ranked
  `hire_source == 'acquisition'` (9.1%/8.4% early-exit rate) directly against
  agency/direct/graduate/referral (<0.6% each) as if all five channels
  measured tenure the same way. They do not — non-acquisition channels have
  genuine, spread-out hire dates (median tenure 222–237 months); acquisition
  hires do not (median tenure 19 months, artificially compressed for the
  reason above).
- **Multiple comparisons / researcher degrees of freedom:** this finding was
  reached by scanning for the largest chi-square across hire_source, then
  subsetting further by legacy_entity, then further by hire-date quarter —
  three successive post-hoc cuts with no pre-registered stopping rule or
  correction. Even setting the `hire_date` issue aside, this path is exactly
  the kind of "hunt until something is significant" pattern `CLAUDE.md`
  Section 12 warns about.
- **Magnitude check:** the underlying "90.4% of all company-wide early exits
  are acquisition-sourced" statistic is dramatic largely *because* of how
  tenure is computed for that group, not necessarily because of a distinctly
  higher underlying quit propensity — it cannot be interpreted at face value
  given the above.
- **What would rescue this finding:** an authoritative definition of what
  `hire_date` means for acquisition-sourced records (does NovaCorp have a
  separate "original employment date" field not exposed in this dataset?);
  failing that, dropping any tenure-based framing entirely and re-testing
  using only `exit_date` timing relative to the entity's known
  acquisition-completion date (a per-entity, not per-employee, clock).
- **Verdict: REJECT** as currently framed. Not "weak" — the mechanism the
  finding claims to show cannot be distinguished from a measurement artefact
  with the data as understood today.

### FR-03 — Entity_C promotion gap: **REJECT**

- **Denominator error (fatal, and now fully explained):** `n_reviews_available`
  for Entity_C is **exactly 1 for 100% of the cohort** (mean = median = 1.0),
  vs. 2.8–2.9 for NovaCorp-Origin/Entity_A and 2.3 for Entity_B. "Ever
  recommended" is mechanically a fraction with a much smaller denominator of
  *opportunities* for Entity_C — not a smaller per-opportunity probability.
- **Confound resolved directly:** recomputing **promotion rate per review**
  (recommendations ÷ reviews available, removing the opportunity-count
  confound) gives Entity_A 14.2%, Entity_B 13.2%, Entity_C 13.9%,
  NovaCorp-Origin 14.2% — **statistically indistinguishable**. The entire
  "half the rate" gap evaporates.
- **Confirmation via equal-exposure subsample:** restricting to employees
  with *exactly* 3 reviews available (removing Entity_C entirely, since none
  qualify, but testing whether Entity_B's gap survives equal exposure to
  Entity_A/NovaCorp-Origin): Entity_B 34.3%, Entity_A 36.5%,
  NovaCorp-Origin 36.4% — Entity_B's gap also shrinks sharply under equal
  exposure and is no longer the dramatic effect originally reported.
- **Role-level composition:** the original finding controlled for role_level,
  which correctly ruled out *that* confound — but missed the more basic
  exposure-time confound, which is the one that actually explains the result.
- **Verdict: REJECT.** This is the cleanest, most complete kill in this
  review: the mechanism is fully identified (exposure time, itself caused by
  the `hire_date` cross-cutting issue above), and the effect disappears
  entirely once corrected for. The original finding's ethical framing
  ("structural disadvantage for Entity_C") does not survive — the promotion
  *process*, on this evidence, treats a per-review chance roughly equally
  across cohorts; Entity_C simply hasn't had the reviews yet.

### FR-04 — Entity_B: trust not pay: **ROBUST**

- **Simpson's paradox check (the critical test for this finding):**
  re-computed compa_ratio and `senior_leadership_trust` for Entity_B vs.
  NovaCorp-Origin **within every one of the 7 departments** (all n≥36,
  6 of 7 with n≥199). In **every single department**, Entity_B's compa_ratio
  is equal to or higher than NovaCorp-Origin's, and Entity_B's trust score is
  lower (Insurance: 2.84 vs. 3.22; Corporate Operations: 2.71 vs. 3.12;
  Retail Banking: 2.95 vs. 3.29; Risk & Compliance: 2.90 vs. 3.22; Technology:
  3.41 vs. 3.63; Wealth Management: 3.35 vs. 3.63; Executive Leadership: 3.53
  vs. 3.55, the one near-tie, smallest cell n=36). This is about as clean a
  Simpson's-paradox clearance as this dataset produces — the pattern is not
  an artefact of Entity_B happening to sit in low-trust departments.
- **Small sample:** every department cell except Executive Leadership has
  n≥199 on the Entity_B side; the finding is not resting on a fragile cell.
- **What is NOT resolved:** reverse causality (Section 19 of `CLAUDE.md`) —
  low trust could be a symptom of the same unobserved integration friction
  that also drives attrition, rather than an independent driver of it. The
  ROBUST verdict certifies the *association* survives every composition
  attack thrown at it; it does not certify a causal mechanism.
- **Verdict: ROBUST** (association only — causal direction remains Phase 2's
  job, per AI-1's original nested-model design).

### FR-06 / FR-18 — Stalled promotion pipeline: **WEAK** (downgraded from the original ranking)

- **Exposure-time / tenure confound (the decisive attack):** the "stalled"
  group has a materially shorter median tenure (76.5 months) than the
  "advancing" group (105 months) — almost 2.5 years' difference, unadjusted
  for in the original comparison.
- **Direct re-test:** restricting both groups to employees with *exactly* 3
  performance reviews available (a rough equal-exposure/equal-tenure-band
  control), the voluntary exit rate gap collapses from the original 9.6% vs.
  5.3% to **2.2% vs. 1.7%**, and loses significance entirely (χ²=0.12,
  p=0.73, n=499/525).
- **Interpretation:** the original, unrestricted comparison likely mixed
  shorter-tenured (higher base-rate) employees disproportionately into the
  "stalled" bucket. Department and role_level mix between the two groups were
  checked and are not the driver (both fairly similar, e.g. 55.1% vs. 52.7%
  at role_level 1) — tenure specifically is the confound.
- **What would rescue this finding:** the Cox proportional-hazards model
  CP-1 already specifies, controlling for tenure continuously rather than via
  a crude equal-review-count subsample (which discards most of the data and
  is likely underpowered in a different way — n=499/525 vs. the original
  686/655).
- **Verdict: WEAK.** Not rejected outright — the equal-exposure subsample is
  itself an imperfect control and a properly specified survival model could
  still find a real, smaller effect — but the dramatic 2x gap as originally
  reported does not survive the most obvious confound check and should not be
  carried forward at that magnitude.

### FR-05 — Non-response as leading indicator: **ROBUST**

- **The critical attack — is this just an Entity_B/C composition effect?**
  (Entity_B/C have both lower response rates *and* higher attrition, so the
  pooled non-response→exit link could be spurious.) Re-tested **within each
  legacy_entity separately**:
  - NovaCorp-Origin alone: never-responded 68.2% vs. responded 7.0%
    (n=88 never-responded, χ² p=3.9e-101)
  - Entity_B alone: never-responded 48.3% vs. responded 6.5%
    (n=116, p=2.0e-50)
  - Entity_C alone: 0.3% vs. 1.7% — not significant, n=293, but only 1 total
    exit event in the never-responded group, consistent with Entity_C's
    compressed observation window (see the cross-cutting `hire_date` issue)
    leaving too little follow-up time for the pattern to manifest, not a
    contradiction of it.
- **Result: this finding gets *stronger*, not weaker, under the composition
  attack** — the effect is if anything more extreme within NovaCorp-Origin
  alone than in the pooled estimate. This is the single most convincing
  survival of an adversarial test in this entire review.
- **Selection bias:** already documented in the original entry (differential
  response rates by entity per DQ-006) — now shown not to explain the
  relationship away.
- **Retrospective leakage:** none — non-response is observed strictly before
  each employee's cutoff date by construction (`docs/feature_dictionary.md`).
- **Verdict: ROBUST.**

### FR-02 — Entity_B's department-robust gap: **ROBUST**

- **Small-sample / cell-size audit:** re-examined every department×entity
  cell underlying the original "5 of 6 departments" claim. All cells have
  adequate n (119–2,052) and non-trivial event counts (9–157 exits) except
  Executive Leadership, which was already the one department excluded from
  the original claim. No cell is fragile enough to be driving the pattern by
  chance.
- **Consistency:** Entity_B ranks highest or second-highest in every
  department examined; the pattern is not being carried by one or two large
  departments.
- **What remains untested:** role_level composition within each
  department×entity cell specifically (as distinct from department alone) —
  a real but second-order gap, not one that plausibly reverses a pattern this
  consistent across 6 independent departments.
- **Verdict: ROBUST.** Effectively the same underlying evidence as FR-04;
  the two together (why + that-it's-not-a-department-artefact) form one
  well-supported story.

### FR-07 — Manager-level variance (~12%): **PROMISING BUT UNPROVEN** (unchanged tier, but for a more specific reason now)

- **Department/entity composition attack:** residualising `voluntary_exit`
  by department×legacy_entity cell mean **before** re-running the
  variance-decomposition barely changes the estimate (raw R²-like = 0.1215 →
  adjusted = 0.1203). This is a genuine surprise — the manager-level signal
  is **not** explained away by the two most obvious composition confounds.
  That strengthens confidence the *underlying* signal is real.
- **Why this still isn't ROBUST:** the R²-like statistic itself (a naive
  between-group/total-group sum-of-squares ratio) is known to **overstate**
  true random-effect variance when group sizes are small and unequal (most
  managers here have 5–8 reports) — it has no shrinkage correction, so noisy
  small-team estimates inflate the "between" term mechanically. This is a
  distinct problem from composition confounding and the department/entity
  adjustment does nothing to fix it.
- **Small-sample / concentration re-check:** the separate "top decile of
  managers hold 100% of regrettable exits" statistic from the original
  finding is reconfirmed as almost certainly a sparse-count artefact — 52%
  of the 745 managers (391) have exactly zero voluntary exits on their team,
  visible directly in the histogram (`07_manager_level_dispersion.png`).
  With a rare outcome spread across many small teams, *any* manager with a
  single such exit is mechanically pushed into the "top" group. This specific
  sub-claim should be dropped, not merely caveated.
- **Verdict: PROMISING BUT UNPROVEN.** Survives the composition attack;
  does not yet survive the statistical-methodology bar (a real mixed-effects
  model with empirical-Bayes shrinkage, exactly as MG-1/MG-2 already specify)
  needed before the ~12% figure or any manager-level claim is sized or acted
  on.

### FR-11 — Hiring-channel reframe: **ROBUST for the core claim, with a correction required**

- **Composition attack (role_level):** acquisition-sourced hires skew heavily
  toward role_level 1 (71.6% vs. 48–53% for the other four channels) — but
  restricting the comparison to role_level 1 only, the **core ranking
  (graduate highest, agency lowest) holds**: graduate 10.6%, referral 8.2%,
  direct 8.0%, agency 7.6%.
- **Tenure/salary composition attack:** median tenure for the four
  *non-acquisition* channels is nearly identical (agency 224mo, direct
  237mo, graduate 237mo, referral 222mo) — ruling out "graduates just have
  systematically different tenure exposure than agency hires" as an
  explanation for the gap between those two specifically.
- **Department composition:** hire_source mix across departments is fairly
  flat (10–12% range per department per source) — not a department-driven
  artefact.
- **The correction this review requires:** `hire_source == 'acquisition'`
  (median tenure 19 months) is contaminated by the same cross-cutting
  `hire_date` issue documented above and **must be excluded from this
  ranked comparison, not placed mid-table as the original write-up did.**
  Re-run restricted to the four organic channels only (tenure>24 months
  filter): graduate 10.2%, referral 8.0%, direct 7.8%, agency 7.4% — the
  ranking is unchanged and clean once the contaminated channel is removed.
- **Verdict: ROBUST for "graduate attrition exceeds agency attrition among
  organically-sourced hires."** The original framing that included
  `hire_source == 'acquisition'` in the same ranked list is corrected here —
  that channel's numbers are not comparable on this axis and should be
  reported separately if at all, pending resolution of the `hire_date`
  question above.

### FR-08 / FR-13 / FR-14 — Tenure/trajectory confound family: **REJECT** (as actionable findings — confirmed, not merely maintained)

- These three were already self-flagged as likely survivorship/censoring
  artefacts in the original write-up, before this adversarial pass began.
- **New evidence from this review reinforces the rejection independently:**
  the discovery that `hire_date` is administratively compressed for 36% of
  the workforce (Entity_A/B/C) means any tenure-band or tenure-dependent
  metric (exactly what FR-08/13/14 rely on) carries an additional, previously
  unquantified source of distortion beyond the right-censoring/survivorship
  mechanism already identified.
- **Verdict: REJECT** as usable, standalone business findings. Their value is
  and remains purely as a methodological warning — correctly self-identified
  the first time, now independently corroborated by a second, unrelated
  mechanism found in this review.

---

## Section 5: Top 5 Strongest Surviving Business Hypotheses

Nominated from the findings that reached **ROBUST** or **PROMISING BUT
UNPROVEN** above. These are candidates for Phase 2 formal testing and
eventual storyline selection — **not recommendations, and no final storyline
has been chosen.** Ranked by combined evidence strength (post-review) and
business materiality.

1. **HiPo employees are NovaCorp's dominant regrettable-attrition risk
   population** (FR-01, ROBUST). Survived every stratification cut
   (department, role_level) without moving. The single best-evidenced,
   highest-effect-size finding in the dataset.

2. **Entity_B's elevated attrition is a trust/leadership problem, not a
   compensation problem, and this holds in every department** (FR-04 + FR-02,
   both ROBUST). The two findings are one story: the entity effect is real
   and not a department artefact (FR-02), and the mechanism most consistent
   with the evidence is leadership trust, not pay (FR-04) — cleared through
   a full 7-department Simpson's-paradox check.

3. **Non-response to engagement surveys is a stronger, independent early-warning
   signal than any survey score, and gets stronger — not weaker — when
   tested within single entities** (FR-05, ROBUST). The rare finding in this
   review that survived its most dangerous attack by strengthening.

4. **The agency-hiring-channel-is-the-problem assumption is backwards: among
   organically-sourced hires, graduates show the highest attrition, agency
   the lowest** (FR-11, ROBUST for the corrected core claim). Survives
   role-level, tenure, and department composition checks; requires dropping
   the acquisition-sourced comparison from the same table.

5. **Manager identity is associated with a real, composition-independent
   share of attrition variance, but its size cannot yet be trusted** (FR-07,
   PROMISING BUT UNPROVEN). The only surviving finding not yet ROBUST that
   still merits a top-5 slot: it held up against the two confounds most
   likely to kill it (department, entity), which is more than most findings
   in this review achieved, and the potential lever (manager quality/practice)
   is large and currently unexploited by any other surviving hypothesis.
   Promotion to ROBUST requires the shrinkage-corrected mixed-effects
   re-estimate already specified in MG-1/MG-2.

**Not nominated, with reason:** FR-09, FR-03, and FR-08/13/14 were rejected
above and are excluded regardless of their original effect sizes. FR-06/FR-18
was downgraded to WEAK and excluded from this top 5, pending the proper
survival-model re-test — it may return in Phase 2 if that model finds a real,
smaller effect, but the 2x figure originally reported should not be carried
forward.

**No recommendations follow from this document.** Per the task governing
this review, recommendations are explicitly out of scope here.
