# Hypothesis Register — NovaCorp $42M People Cost Investigation

Status: **planning artefact — no hypothesis below has been tested yet.** This register exists
to make the "explore broadly" phase disciplined and pre-committed, so that later testing is not
a search for a story but a check-off against a plan fixed in advance (this also mitigates
p-hacking / multiple-comparison cherry-picking — see `analysis_plan.md` Section 7).

Governed by `CLAUDE.md` throughout — in particular: never treat `regrettable_flag`,
`performance_band_at_exit`, `stated_exit_reason`, `pathway`, `salary_at_exit`,
`manager_id_at_exit`, or `notice_period_served` as predictive features (Section 18); never use
gender, cultural_background, or age_band as intervention-targeting variables (Section 11);
label every eventual result as observed fact / statistical evidence / inference / hypothesis /
recommendation (Section 21); default to associational, not causal, language (Section 19).

Each hypothesis carries an ID (`AREA-#`) and a **provisional Phase-2 priority tier**
(Wave 1 = test first, Wave 2 = test if Wave 1 findings warrant it, Wave 3 = lower expected
yield or highly exploratory) based on qualitative reasoning from facts already confirmed in
`CLAUDE.md` (e.g., confirmed row counts, confirmed rate gaps). This tiering sequences *testing
effort* — it is explicitly **not** a storyline selection, and tiers may move once evidence
comes in (per the prioritisation framework in `analysis_plan.md` Section 8, which scores
*tested findings*, not raw hypotheses).

Population codes (P1–P8) are defined in `analysis_plan.md` Section 4; each hypothesis cites the
one(s) it uses.

---

## 1. Regrettable Attrition (RA)

### RA-1 — Concentration of regrettable attrition
- **Business question:** Is regrettable voluntary attrition concentrated in specific
  departments, role levels, or tenure bands, or spread evenly across the workforce?
- **Why it matters:** Directly informs whether the $22–25M regrettable-attrition component
  needs a targeted or a company-wide response; concentration = higher tractability.
- **Datasets required:** `employees.csv`, `attrition_log.csv`.
- **Variables required:** `department`, `role_level`, `role_family`, `tenure_months`,
  `regrettable_flag`, `exit_type`.
- **Correct population/denominator:** P3 (voluntary exits, n=1,133) as numerator population;
  P1+P2 combined (all employees who were "at risk" during the window, i.e. active at some
  point) as the exposure denominator for rate calculations, segmented the same way.
- **Proposed analytical method:** Segment-level regrettable-voluntary-attrition rate table
  (department × role_level), ranked by rate and by absolute headcount/dollar exposure.
- **Statistical test/model:** Chi-square test of independence (regrettable exit vs.
  department) with Benjamini–Hochberg correction across all segment comparisons; report
  proportions with Wilson confidence intervals given some cells will be small.
- **Potential confounders:** Department headcount size (larger departments mechanically
  produce more regrettable exits in absolute terms even at a flat rate) — must present both
  rate and absolute count/dollar views side by side.
- **Leakage risks:** None directly (this is a descriptive/inferential exercise, not a
  forward-looking predictive model) — but avoid implying causality from segment concentration
  alone.
- **Ethical considerations:** Do not cross-tabulate with gender/cultural_background/age_band
  for targeting; may include as a fairness-audit side-check only (Section 11).
- **Possible financial impact method:** Apply Section 14 replacement-cost formula
  (1.5× salary × 85% backfill rate, + 12% super on-cost) to the concentrated segment(s)
  identified, compared to the same formula applied company-wide, to show $ concentration.
- **Evidence that would SUPPORT:** A small number of segments (e.g., 2–3 department×level
  cells) account for a disproportionate share (e.g., >40%) of regrettable exits relative to
  their share of headcount, with a statistically significant chi-square result surviving
  correction.
- **Evidence that would REJECT:** Regrettable attrition rate is statistically indistinguishable
  across segments once headcount is accounted for (roughly proportional spread).
- **Provisional priority:** Wave 1 (foundational — needed before any other RA/AI/DR hypothesis
  can be sequenced).

### RA-2 — Engagement decline precedes regrettable exit
- **Business question:** Do employees who become regrettable voluntary leavers show a
  measurable decline in engagement scores in the wave(s) before departure, versus stable
  employees?
- **Why it matters:** If true, engagement surveys are a genuine leading indicator NovaCorp
  could act on before losing the person — directly actionable and forward-looking, unlike
  `stated_exit_reason`.
- **Datasets required:** `engagement.csv`, `attrition_log.csv`, `employees.csv`.
- **Variables required:** `wave_number`, `survey_date`, the seven 1–5 engagement dimensions,
  `response_flag`, `exit_date`, `regrettable_flag`.
- **Correct population/denominator:** P5 (regrettable voluntary exits, n=153) as the case
  group; a matched or full comparison group of P1 (active, still-employed) employees with
  ≥2 waves of data, matched loosely on department/level/tenure.
- **Proposed analytical method:** Within-person engagement trajectory (wave-over-wave change)
  comparison between eventual regrettable leavers and stayers, using only waves completed
  strictly before each leaver's `exit_date` (no post-exit data used, and no using a leaver's
  later wave to describe a stayer comparison group).
- **Statistical test/model:** Difference-in-trend test (e.g., mixed-effects/growth-curve model
  with employee random intercept, or simpler paired pre/post wave comparison via Mann-Whitney
  U on the deltas) on each of the 7 dimensions; correct for multiple dimensions tested (7
  tests → BH correction).
- **Potential confounders:** Tenure and department composition of leavers vs. stayers;
  survey-timing proximity to exit (someone who left right after Wave 5 has a very different
  "before" window than someone who left between waves).
- **Leakage risks:** High — this is the classic timing-leakage case flagged in `CLAUDE.md`
  Section 18. Must strictly use only pre-exit waves per employee; must not use n=153's own
  final (possibly post-decision) wave as if it were an independent predictor when the
  narrative purpose is "early warning."
- **Ethical considerations:** If validated, any resulting "early warning" framing must be
  presented as a manager/HR support trigger, not a covert monitoring/surveillance tool — flag
  this explicitly in any recommendation downstream.
- **Possible financial impact method:** Not directly monetised itself; feeds into RA-1's
  targeting logic (identifies *which* future regrettable exits might be interceptable) and a
  potential future avoided-cost estimate if such an early-warning trigger were adopted
  (framed as a scenario, not a committed saving).
- **Evidence that would SUPPORT:** Statistically significant, meaningful-effect-size decline
  in ≥2 engagement dimensions (esp. `senior_leadership_trust`, `career_development`,
  `confidence_in_role_future`) in the 1–2 waves before exit, not present in stayers.
- **Evidence that would REJECT:** No detectable pre-exit decline distinguishable from normal
  wave-to-wave noise in stayers, or decline is present in stayers just as much as leavers.
- **Provisional priority:** Wave 1 (high strategic value if it holds; directly tests the
  "surveys as leading indicator" thesis that underlies the entire disengagement narrative).

### RA-3 — Regrettable attrition and performance overlap
- **Business question:** Are regrettable voluntary leavers disproportionately drawn from
  higher performance bands (i.e., is NovaCorp really losing its better people), or is HR's
  `regrettable_flag` uncorrelated with objective performance signals?
- **Why it matters:** Validates (or challenges) the core premise that regrettable attrition is
  NovaCorp's costliest, highest-value-loss component.
- **Datasets required:** `attrition_log.csv`, `performance.csv`, `employees.csv`.
- **Variables required:** `regrettable_flag`, `performance_band_at_exit`, `performance_rating`
  (from `performance.csv`, pre-exit reviews only), `goal_achievement_score`.
- **Correct population/denominator:** P3 (voluntary exits) split into regrettable (P5) vs.
  not-regrettable-voluntary.
- **Proposed analytical method:** Compare distribution of most-recent pre-exit
  `performance_rating` (from `performance.csv`, independent of HR's own
  `performance_band_at_exit` field) between regrettable and non-regrettable voluntary leavers.
- **Statistical test/model:** Ordinal logistic regression or Mann-Whitney U on ordinally-coded
  performance rating vs. regrettable_flag; cross-check agreement rate between
  `performance.csv` rating and `attrition_log.csv` `performance_band_at_exit` (inter-source
  consistency check).
- **Potential confounders:** Tenure (longer-tenured employees have more review history and
  more chances to be rated highly); department mix.
- **Leakage risks:** Must use only the performance review immediately preceding exit, not
  reviews that could postdate it; note the 2025-H2 cycle gap (Section 5/18) may
  systematically bias which leavers have a "recent" rating available.
- **Ethical considerations:** None beyond standard non-identification; this is a
  label-validity check on HR's own data, treat sensitively (not a performance-management
  audit of individuals).
- **Possible financial impact method:** If regrettable-flagged leavers are confirmed
  higher-performing, this supports using the full 1.5× replacement multiplier on that
  population as-is; if not, this is a candidate reason to build a team-defined alternative
  "regrettable" definition (Section 10) with a stated justification.
- **Evidence that would SUPPORT:** Regrettable-flagged leavers show significantly higher
  pre-exit performance ratings/goal scores than non-regrettable voluntary leavers.
- **Evidence that would REJECT:** No significant performance difference — suggesting
  `regrettable_flag` reflects something other than demonstrated performance (e.g., manager
  sentiment, role criticality, or inconsistent application).
- **Provisional priority:** Wave 1 (a load-bearing validity check on the primary cost label).

### RA-4 — Push vs. pull pathway and cost composition
- **Business question:** Does the "pull" (opportunity-driven) pathway account for a
  disproportionate share of regrettable, high-salary attrition compared to "push"?
- **Why it matters:** Pull exits imply external market competitiveness problems
  (compensation/career), while push exits imply internal management/fit problems — these
  point to different interventions.
- **Datasets required:** `attrition_log.csv`, `employees.csv`.
- **Variables required:** `pathway`, `regrettable_flag`, `salary_at_exit`, `role_level`,
  `department`.
- **Correct population/denominator:** P3 (voluntary exits, n=1,133) — note `pathway` is
  recorded for exits generally; confirm during Phase 0 whether it is populated for
  involuntary exits too, and restrict to voluntary if not cleanly defined otherwise.
- **Proposed analytical method:** Cross-tab `pathway` × `regrettable_flag`; compare
  `salary_at_exit` and `role_level` distributions between push and pull groups.
- **Statistical test/model:** Chi-square (pathway × regrettable_flag); Mann-Whitney U
  (salary_at_exit by pathway).
- **Potential confounders:** Department/role-level composition of push vs. pull groups.
- **Leakage risks:** `pathway` is a post-exit HR classification (Section 6) — usable as an
  outcome/descriptive variable only, never as a predictive feature.
- **Ethical considerations:** None beyond standard aggregation practice.
- **Possible financial impact method:** Split the $22–25M regrettable-attrition estimate into
  a pull-driven share and a push-driven share, each pointing to a different intervention
  budget line (market-pay adjustment vs. management/engagement investment).
- **Evidence that would SUPPORT:** Pull exits are significantly more likely to be flagged
  regrettable and carry higher salary/role-level than push exits.
- **Evidence that would REJECT:** No meaningful difference in regrettable-flag rate, salary,
  or level between push and pull pathways.
- **Provisional priority:** Wave 2.

### RA-5 — Internal consistency of the regrettable_flag label
- **Business question:** Is `regrettable_flag` applied consistently (e.g., predictable from
  objective factors like performance and tenure), or does it vary in ways better explained by
  which manager recorded it?
- **Why it matters:** If the flag is manager-idiosyncratic rather than employee-value-based,
  any cost estimate built directly on it inherits that noise, and the register should
  recommend a triangulated/alternative definition (Section 10).
- **Datasets required:** `attrition_log.csv`, `employees.csv`, `performance.csv`.
- **Variables required:** `regrettable_flag`, `manager_id_at_exit`, pre-exit
  `performance_rating`, `tenure_months`.
- **Correct population/denominator:** P3 (voluntary exits, n=1,133).
- **Proposed analytical method:** Mixed-effects logistic regression of `regrettable_flag` on
  performance/tenure with a manager random effect; examine how much residual variance is
  attributable to `manager_id_at_exit` after controlling for objective factors.
- **Statistical test/model:** Mixed-effects logistic regression; intra-class correlation (ICC)
  on the manager random effect.
- **Potential confounders:** Manager tenure/team composition; role criticality (not directly
  observed — a limitation to state explicitly).
- **Leakage risks:** None (this is a label-validity study, not a predictive model).
- **Ethical considerations:** Do not name or expose individual managers in any output; report
  only the aggregate ICC/variance-explained finding.
- **Possible financial impact method:** Not directly monetised; a methodological finding that
  changes how the $22–25M denominator should be defined (see RA-3).
- **Evidence that would SUPPORT:** Meaningful manager-level ICC (e.g., >0.10) in
  `regrettable_flag` after controlling for performance/tenure.
- **Evidence that would REJECT:** Regrettable_flag is well explained by performance/tenure
  alone with negligible manager-level residual variance.
- **Provisional priority:** Wave 2.

---

## 2. Disengagement / Productivity Loss (DP)

### DP-1 — Defining and sizing "persistently disengaged"
- **Business question:** What share of the active workforce shows sustained low engagement
  across multiple waves (vs. a transient single-wave dip), and how large is that population?
- **Why it matters:** Finance's $12–15M estimate needs a population definition; this
  hypothesis constructs and sizes one transparently.
- **Datasets required:** `engagement.csv`, `employees.csv`.
- **Variables required:** All 7 engagement dimensions, `wave_number`, `response_flag`.
- **Correct population/denominator:** P1 (active workforce, n=12,003) restricted to those with
  at least 2–3 valid (responded) waves, to distinguish "persistent" from "single observation."
- **Proposed analytical method:** Construct a composite engagement index per wave (mean or
  factor score across the 7 dimensions); classify employees as "persistently disengaged" if
  the composite is below a defined threshold (e.g., bottom quartile) in a majority of their
  valid waves. Report the resulting headcount and % of workforce.
- **Statistical test/model:** Threshold sensitivity analysis (vary the quartile/majority-of-
  waves rule and show how the sized population changes) rather than a single hard cut — per
  Section 14's sensitivity-testing requirement.
- **Potential confounders:** Employees with fewer valid waves (due to hire timing or
  non-response) are structurally more likely to be miscategorised — treat wave-count as a
  covariate, not noise.
- **Leakage risks:** None (this is descriptive population construction, not prediction).
- **Ethical considerations:** This constructed label must never be used to target individuals
  for adverse action; it exists to size a cost, not to flag people (Section 11).
- **Possible financial impact method:** Apply Section 14's 15%-of-base-salary productivity-loss
  formula to the sized population; report against Finance's $12–15M range as a check, with
  the threshold-sensitivity range carried through.
- **Evidence that would SUPPORT:** A stable, non-trivial population (e.g., materially >0% and
  <100% of workforce) emerges consistently across reasonable threshold choices.
- **Evidence that would REJECT:** The sized population is wildly threshold-dependent (e.g.,
  swings from 2% to 60% of the workforce with small threshold changes), indicating the
  construct is too unstable to support a specific dollar estimate with confidence.
- **Provisional priority:** Wave 1 (a prerequisite for any DP-series dollar estimate).

### DP-2 — Concentration of persistent disengagement
- **Business question:** Is persistent disengagement (as defined in DP-1) concentrated by
  department, legacy entity, or manager, or evenly spread?
- **Why it matters:** Concentration = tractable, targeted intervention; even spread = a
  company-wide culture issue requiring a different (and costlier) response.
- **Datasets required:** `engagement.csv`, `employees.csv`.
- **Variables required:** DP-1's derived flag, `department`, `legacy_entity_code`,
  `manager_id`.
- **Correct population/denominator:** P1, restricted as in DP-1.
- **Proposed analytical method:** Segment-level prevalence table with rate and absolute
  headcount, mirroring RA-1's approach.
- **Statistical test/model:** Chi-square / logistic regression with department, legacy entity,
  and (via random effects) manager as predictors of the DP-1 flag; BH-corrected.
- **Potential confounders:** Department and legacy-entity composition overlap (e.g., Entity_B
  employees may cluster in specific departments) — model jointly, not in isolation.
- **Leakage risks:** None.
- **Ethical considerations:** Manager-level results reported in aggregate only (Section 11);
  no naming.
- **Possible financial impact method:** Same as DP-1, split by top concentrated segment(s) vs.
  remainder, to show $ concentration.
- **Evidence that would SUPPORT:** Statistically and practically significant concentration in
  a small number of segments.
- **Evidence that would REJECT:** Roughly uniform prevalence across segments after accounting
  for headcount.
- **Provisional priority:** Wave 1.

### DP-3 — Engagement-to-productivity link
- **Business question:** Does low engagement (particular dimensions) actually associate with
  lower measured performance/goal achievement, validating Finance's assumption that
  disengagement causes productivity loss?
- **Why it matters:** This is the single most load-bearing assumption behind the $12–15M
  component — Finance's estimate assumes engagement→productivity, but this has not been
  checked against NovaCorp's own performance data.
- **Datasets required:** `engagement.csv`, `performance.csv`, `employees.csv`.
- **Variables required:** 7 engagement dimensions, `goal_achievement_score`,
  `performance_rating`, `review_date`, `survey_date`.
- **Correct population/denominator:** P1 (active employees) with a temporally-matched pair of
  an engagement wave and a subsequent (not prior) performance review, to give the engagement
  measure a chance to precede the outcome it's meant to explain.
- **Proposed analytical method:** Regression of `goal_achievement_score` on same-employee
  engagement composite (and individual dimensions), controlling for department, role_level,
  and tenure.
- **Statistical test/model:** OLS/mixed-effects regression with employee and manager random
  effects (to avoid manager-level confounding of both engagement ratings and goal scores);
  report effect size and CI, not just significance.
- **Potential confounders:** Manager-level rating leniency/strictness could inflate both
  engagement scores (via `manager_effectiveness`) and goal_achievement_score simultaneously —
  a serious confound requiring the manager random effect above.
- **Leakage risks:** Must ensure engagement wave used precedes the performance review used, to
  avoid reverse-sequencing.
- **Ethical considerations:** Standard; findings are about the workforce in aggregate, not
  individual performance judgement.
- **Possible financial impact method:** If a credible (associational, not causal — Section 19)
  link is found, use the estimated effect size to sanity-check (not replace) Finance's flat
  15%-of-salary assumption; if no link is found, this is a significant, reportable challenge
  to the $12–15M component's basis.
- **Evidence that would SUPPORT:** Statistically and practically meaningful positive
  association between engagement (esp. `purpose_meaning`, `wellbeing`,
  `confidence_in_role_future`) and subsequent goal achievement, robust to manager controls.
- **Evidence that would REJECT:** Null or negligible association once manager-level
  confounding is controlled for.
- **Provisional priority:** Wave 1 (highest strategic value in this area — directly tests
  whether Finance's $12–15M assumption is empirically grounded).

### DP-4 — Company-wide engagement trend
- **Business question:** Is engagement improving, flat, or declining across the five waves,
  overall and within key segments (e.g., Entity_B, Risk & Compliance)?
- **Why it matters:** Determines whether disengagement is a growing, stable, or shrinking cost
  exposure — materially changes urgency framing for the CHRO.
- **Datasets required:** `engagement.csv`, `employees.csv`.
- **Variables required:** 7 dimensions, `wave_number`, `survey_date`, `department`,
  `legacy_entity_code`.
- **Correct population/denominator:** P1, respondents only (`response_flag`==True) for the
  trend itself; response *rate* trend tracked separately (see SR series) since a rising
  non-response rate would bias a naive respondent-only trend upward or downward.
- **Proposed analytical method:** Wave-over-wave mean (with CI) for each dimension, overall
  and by key segment; a respondent-composition check (are the same people responding each
  wave, or is the panel churning?) alongside the headline trend.
- **Statistical test/model:** Linear trend test (wave number as continuous predictor) with
  cluster-robust SEs by employee; segment × wave interaction to test whether trends differ by
  group.
- **Potential confounders:** Panel composition change (attrition removes low-engagement people
  from later waves, mechanically flattering the trend) — must be explicitly addressed, ideally
  via a matched-panel (same-employee-across-waves) sensitivity check.
- **Leakage risks:** None.
- **Ethical considerations:** None beyond standard aggregation.
- **Possible financial impact method:** Feeds a directional (not point-estimate) statement
  about whether the $12–15M exposure is likely to grow or shrink under current trajectory.
- **Evidence that would SUPPORT (worsening story):** Statistically significant downward trend
  that survives the matched-panel/survivorship check.
- **Evidence that would REJECT:** Flat or improving trend, or an apparent decline that
  disappears once panel composition (attrition-driven survivorship) is controlled for.
- **Provisional priority:** Wave 2.

---

## 3. Hiring Inefficiency (HI)

### HI-1 — Hire source and early attrition ("poor match")
- **Business question:** Do agency-sourced hires show higher early (short-tenure) attrition
  than direct, referral, or graduate hires?
- **Why it matters:** Directly tests the brief's "poor-match early attrition" framing within
  the $4–6M hiring-inefficiency component; if true, the true cost of agency hiring exceeds the
  18% fee premium alone.
- **Datasets required:** `employees.csv`, `attrition_log.csv`.
- **Variables required:** `hire_source`, `hire_date`, `exit_date`, `tenure_months`,
  `exit_type`.
- **Correct population/denominator:** P6 (full roster) restricted to employees hired during
  the observation window with enough follow-up time to observe an "early" exit (define
  "early" explicitly, e.g., ≤12 months tenure, then sensitivity-test the cutoff).
- **Proposed analytical method:** Early-exit rate by `hire_source`, with survival curves
  (Kaplan–Meier) by hire source over the first 12–18 months.
- **Statistical test/model:** Log-rank test across hire-source survival curves; Cox
  proportional-hazards model controlling for department/role_level/level.
- **Potential confounders:** Hire source is not random — agency hiring may be used
  disproportionately for hard-to-fill or high-turnover role types (e.g., specialist Risk &
  Compliance roles), which would confound a naive comparison. Must control for role_family/
  department/level.
- **Leakage risks:** For active employees with short tenure, right-censoring must be handled
  properly (they haven't had a chance to "fail" yet) — this is exactly the survival-analysis
  case flagged in Section 12.
- **Ethical considerations:** None beyond standard.
- **Possible financial impact method:** Compare realised cost per successful (retained-past-
  X-months) hire by source: agency (18% of first-year salary) vs. direct ($5,500 flat),
  adjusted for the source-specific early-attrition rate (a failed hire effectively doubles
  acquisition cost via re-hiring).
- **Evidence that would SUPPORT:** Agency hires show significantly higher early-exit hazard
  than direct/referral/graduate hires after controlling for role/department/level.
- **Evidence that would REJECT:** No significant difference in early-attrition hazard by hire
  source once role composition is controlled for.
- **Provisional priority:** Wave 1.

### HI-2 — Structural recruiting bottlenecks (days_to_fill)
- **Business question:** Is `days_to_fill` structurally elevated in specific departments/role
  families, pushing NovaCorp toward costlier agency channels there?
- **Why it matters:** If certain roles are structurally hard to fill, the fix is a talent-
  pipeline/market-positioning intervention, not a generic "use fewer agencies" directive.
- **Datasets required:** `employees.csv`.
- **Variables required:** `days_to_fill`, `department`, `role_family`, `role_level`,
  `hire_source`.
- **Correct population/denominator:** P6, all hires with a non-missing `days_to_fill` value.
- **Proposed analytical method:** Distribution of `days_to_fill` by department/role_family/
  level; correlation with subsequent reliance on `hire_source`=='agency'.
- **Statistical test/model:** ANOVA/Kruskal-Wallis across departments/role families on
  `days_to_fill`; correlation test between department-level mean `days_to_fill` and
  department-level % agency-sourced.
- **Potential confounders:** Role seniority (senior roles inherently take longer to fill,
  regardless of department) — control for `role_level`.
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Identify the highest-`days_to_fill` segments and
  estimate the agency-fee premium attributable to them specifically vs. the company average.
- **Evidence that would SUPPORT:** Specific departments/role families (e.g., Risk &
  Compliance, senior Technology roles) show significantly longer fill times, correlated with
  higher agency usage.
- **Evidence that would REJECT:** `days_to_fill` is roughly uniform across segments once
  role_level is controlled for.
- **Provisional priority:** Wave 2.

### HI-3 — Hire-source mix shift over time / by cohort
- **Business question:** Has NovaCorp's reliance on agency hiring increased over the
  observation window or in post-acquisition periods, increasing average cost per hire?
- **Why it matters:** Distinguishes a worsening trend (urgent) from a stable baseline
  (context) in the hiring-inefficiency component.
- **Datasets required:** `employees.csv`.
- **Variables required:** `hire_source`, `hire_date`, `legacy_entity_code`.
- **Correct population/denominator:** P6, hires occurring within the 2024–2025 window (to
  align with the observation period; pre-2024 hires included only for historical trend
  context, clearly labelled as outside the official window).
- **Proposed analytical method:** % agency-sourced hires by hire-quarter; compare NovaCorp-
  Origin vs. post-acquisition-period hiring mix.
- **Statistical test/model:** Trend test (proportion agency-sourced regressed on hire-quarter);
  chi-square for hire-source mix by legacy-entity-code period.
- **Potential confounders:** Overall hiring volume changes (e.g., a hiring freeze then a
  surge) can mechanically shift mix independent of any deliberate sourcing-strategy change.
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Trend-adjusted cost-per-hire estimate, run-rated
  forward if the trend is real and continuing.
- **Evidence that would SUPPORT:** A statistically significant upward trend in agency-hire
  share, particularly coincident with acquisition integration periods.
- **Evidence that would REJECT:** Flat or declining agency-hire share over time.
- **Provisional priority:** Wave 3.

### HI-4 — Early attrition concentration by hire source × onboarding
- **Business question:** Beyond HI-1's overall comparison, is early attrition specifically
  concentrated among agency hires in their first 3–6 months (suggesting an onboarding/
  screening-quality problem) rather than spread evenly across the first year?
- **Why it matters:** A first-90-days problem points to onboarding fixes; a slower-burning
  first-year problem points to a role-fit/market-expectation problem — different, cheaper
  fixes.
- **Datasets required:** `employees.csv`, `attrition_log.csv`.
- **Variables required:** `hire_source`, `hire_date`, `exit_date`, `tenure_months`,
  `pathway`.
- **Correct population/denominator:** Same as HI-1, restricted further to exits with
  `tenure_months` ≤ 12.
- **Proposed analytical method:** Histogram of tenure-at-exit (months) for early leavers, by
  hire source; identify whether agency-hire early exits cluster in months 0–3 vs. spread to
  6–12.
- **Statistical test/model:** Kolmogorov–Smirnov test comparing the tenure-at-exit distribution
  (within the ≤12-month early-leaver population) between agency and non-agency hires.
- **Potential confounders:** Role type/department mix within the early-leaver population.
- **Leakage risks:** None (retrospective description of already-departed early leavers).
- **Ethical considerations:** None.
- **Possible financial impact method:** Refines HI-1's cost estimate by pinpointing which
  window of the first year drives the loss, to scope a specific onboarding-investment ROI case.
- **Evidence that would SUPPORT:** Agency-hire early exits cluster significantly earlier
  (e.g., median tenure-at-exit well under 6 months) than non-agency early exits.
- **Evidence that would REJECT:** No distributional difference in timing of early exit by
  hire source.
- **Provisional priority:** Wave 3 (depends on HI-1 confirming a base effect first).

---

## 4. Career Progression / Promotion Friction (CP)

### CP-1 — Frozen pipeline effect
- **Business question:** Do promotion-eligible employees who are not promoted within a
  defined window show elevated subsequent voluntary attrition?
- **Why it matters:** If a "frozen pipeline" effect exists, it is a highly tractable,
  internally-controllable lever (promotion process/cadence) distinct from external market
  competition.
- **Datasets required:** `employees.csv`, `performance.csv`, `attrition_log.csv`.
- **Variables required:** `promotion_eligible`, `hipo_flag`, `tenure_months`,
  `promotion_recommendation` (from `performance.csv`, as a proxy signal since actual level-
  change events are not directly flagged in the data — this is a modelling choice to document
  explicitly), `role_level`, `exit_type`, `exit_date`.
- **Correct population/denominator:** P1 (active + departed as applicable) restricted to
  employees ever flagged `promotion_eligible`==True, split into "eligible and recommended but
  apparently not advanced within N months" vs. "eligible and advanced" — noting the dataset
  has no direct level-change-event field, so "advancement" must be operationalised carefully
  (e.g., via `role_level` observed at two points in time, if longitudinal snapshots allow; if
  not directly observable, this must be stated as a data limitation and the hypothesis
  re-scoped to use `promotion_recommendation` persistence/repetition as a proxy).
- **Proposed analytical method:** Time-to-exit comparison (Kaplan–Meier / Cox) between
  "stalled" and "advanced" promotion-eligible sub-groups.
- **Statistical test/model:** Cox proportional-hazards regression, controlling for
  department, role_level, tenure.
- **Potential confounders:** Performance itself (someone not promoted may genuinely be a lower
  performer, which independently predicts attrition) — must control for
  `goal_achievement_score`/`performance_rating`.
- **Leakage risks:** Must define the "stalled" window using only information available up to
  that point in time, not using the fact that they eventually left to retroactively define
  "stalled."
- **Ethical considerations:** None beyond standard; this concerns process/systemic fairness,
  not individual promotion decisions.
- **Possible financial impact method:** If confirmed, estimate replacement cost (Section 14
  formula) attributable to the "stalled-eligible" segment specifically, as a targeted
  retention-lever business case (promotion-cycle acceleration vs. attrition cost avoided).
- **Evidence that would SUPPORT:** Significantly higher attrition hazard for stalled-eligible
  employees vs. advanced-eligible employees, controlling for performance.
- **Evidence that would REJECT:** No hazard difference once performance is controlled for
  (i.e., it's a performance story, not a pipeline story).
- **Provisional priority:** Wave 2 (high potential value, but contingent on confirming the
  data actually supports an "advancement" proxy — a Phase 0 feasibility check is required
  first).

### CP-2 — Progression consistency across legacy entities
- **Business question:** Does promotion likelihood (via `promotion_recommendation` rate and/or
  any observable level progression) differ by `legacy_entity_code`, suggesting inconsistent
  opportunity post-acquisition?
- **Why it matters:** Directly relevant to the acquisition-integration narrative — an
  "opportunity gap" would be a concrete, fixable driver of Entity_B/C dissatisfaction distinct
  from vague "cultural" explanations.
- **Datasets required:** `employees.csv`, `performance.csv`.
- **Variables required:** `legacy_entity_code`, `promotion_recommendation`, `role_level`,
  `tenure_months`, `hipo_flag`.
- **Correct population/denominator:** P1 (active workforce), controlling for tenure (newer
  cohorts like Entity_C mechanically have less time to be promoted).
- **Proposed analytical method:** Promotion-recommendation rate by legacy entity, controlling
  for tenure and department via regression rather than raw comparison.
- **Statistical test/model:** Logistic regression of `promotion_recommendation` on
  `legacy_entity_code`, controlling for tenure, department, role_level, performance.
- **Potential confounders:** Tenure-since-hire (not tenure-since-acquisition, which is not
  directly available) is a strong confounder here and must be modelled explicitly.
- **Leakage risks:** None.
- **Ethical considerations:** None beyond standard fairness framing (this is a structural-
  equity question about acquired employees, consistent with Section 11's intent even though
  legacy_entity_code is not itself a protected characteristic).
- **Possible financial impact method:** Not directly monetised; feeds a qualitative/structural
  recommendation about integration process design.
- **Evidence that would SUPPORT:** Significantly lower promotion-recommendation rates for
  Entity_B/C employees than NovaCorp-Origin after controlling for tenure and performance.
- **Evidence that would REJECT:** No significant difference once tenure/performance are
  controlled for.
- **Provisional priority:** Wave 2.

### CP-3 — Career development perception vs. actual mobility
- **Business question:** Are `career_development` engagement scores systematically lower in
  segments where employees stay longer at the same level, indicating a perceived (and
  possibly real) progression-friction problem?
- **Why it matters:** Connects the "soft" engagement signal to a "hard" structural metric,
  strengthening the case for a career-pathing intervention if both align.
- **Datasets required:** `engagement.csv`, `employees.csv`.
- **Variables required:** `career_development` dimension, `tenure_months`, `role_level`,
  `department`.
- **Correct population/denominator:** P1, respondents only.
- **Proposed analytical method:** Correlate mean `career_development` score by segment against
  segment-level average tenure-at-current-level (a constructed proxy, since level-change
  events are not directly observable — documented as a limitation).
- **Statistical test/model:** Segment-level correlation; regression of individual
  `career_development` scores on tenure controlling for department/level.
- **Potential confounders:** Role family (some role families have inherently flatter
  structures/fewer levels to climb) — control for role_family.
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Not directly monetised; supports CP-1/CP-2's
  recommendation with a corroborating engagement-side signal (triangulation, per Section 10).
- **Evidence that would SUPPORT:** Negative correlation between career_development score and
  proxy time-at-level, holding department/role_family constant.
- **Evidence that would REJECT:** No meaningful correlation.
- **Provisional priority:** Wave 3.

### CP-4 — HiPo stagnation compounding risk
- **Business question:** Do HiPo-flagged, promotion-eligible employees who show no
  advancement signal over an extended period exhibit higher attrition than HiPo employees who
  do advance?
- **Why it matters:** This is the highest-value-per-person cell if it exists — losing a
  flagged high-potential employee due to internal stagnation is a clearly preventable, high-
  cost event.
- **Datasets required:** `employees.csv`, `performance.csv`, `attrition_log.csv`.
- **Variables required:** `hipo_flag`, `promotion_eligible`, `promotion_recommendation`,
  `tenure_months`, `exit_type`, `regrettable_flag`.
- **Correct population/denominator:** P8 (HiPo subset) crossed with the CP-1 stalled/advanced
  split.
- **Proposed analytical method:** Compare attrition rate (and regrettable-flag rate among
  leavers) between "stalled HiPo" and "advancing HiPo" sub-groups.
- **Statistical test/model:** Chi-square / Fisher's exact test (small expected cell sizes
  likely, given HiPo is a minority flag) — report with exact CIs given likely small n.
- **Potential confounders:** Department/role composition of the HiPo population.
- **Leakage risks:** Same as CP-1 — define "stalled" using only information available before
  the observation window's relevant point, not retroactively.
- **Ethical considerations:** Do not report cells small enough to be individually
  identifiable, given HiPo is likely a small population per segment (Section 11).
- **Possible financial impact method:** If confirmed and material in headcount, this is a
  strong, narrow, high-ROI recommendation case: cost of a modest HiPo-specific career-pathing
  investment vs. Section 14 replacement cost of losing flagged high-potential staff.
- **Evidence that would SUPPORT:** Stalled HiPo employees show a meaningfully and
  significantly higher (or at minimum, not lower) attrition/regrettable rate than advancing
  HiPo employees, with adequate sample size to trust the estimate.
- **Evidence that would REJECT:** No detectable difference, or sample size too small (per
  Section 12) to support any claim — in which case this must be reported as inconclusive, not
  as a negative finding.
- **Provisional priority:** Wave 2 (high potential value; gated on CP-1's feasibility check
  and on HiPo population size being large enough to analyse).

---

## 5. Manager Effects (MG)

### MG-1 — Manager-level clustering of outcomes
- **Business question:** How much of the variation in attrition and engagement is
  attributable to the manager (`manager_id`), independent of department and role?
- **Why it matters:** If manager effects are large, "manager quality" is a distinct,
  actionable lever the CHRO can invest in (training, span-of-control redesign) separate from
  department-level narratives.
- **Datasets required:** `employees.csv`, `engagement.csv`, `attrition_log.csv`.
- **Variables required:** `manager_id`, engagement dimensions, exit outcomes, `department`,
  `role_level` (as controls).
- **Correct population/denominator:** P1 for engagement variance decomposition; P1+P2 combined
  for attrition variance decomposition, restricted to managers with a minimum team size
  (e.g., ≥5 direct reports) to get a stable per-manager estimate.
- **Proposed analytical method:** Variance-components / random-effects model: outcome ~
  department + role_level + (1 | manager_id); report the manager-level intra-class
  correlation (ICC).
- **Statistical test/model:** Mixed-effects linear model (engagement outcomes) and mixed-
  effects logistic model (attrition outcome), both with manager random intercepts.
- **Potential confounders:** Managers are not randomly assigned to teams — a manager with a
  structurally harder team (e.g., a legacy Entity_B integration team) could look like a "bad
  manager" when the effect is actually team composition. Control for department/legacy_entity
  composition of the team before attributing residual variance to the manager per se.
- **Leakage risks:** None (this is variance decomposition, not individual prediction).
- **Ethical considerations:** Aggregate reporting only — the finding is "manager effects
  explain X% of variance," never a ranked list of named managers (Section 11).
- **Possible financial impact method:** If a material ICC is found, estimate the attrition-
  cost gap between top-quartile and bottom-quartile manager teams (in aggregate, anonymised)
  to frame the size of the opportunity from manager-quality investment.
- **Evidence that would SUPPORT:** Manager-level ICC meaningfully greater than zero (e.g.,
  >0.05–0.10 is often considered practically meaningful in organisational research) after
  controlling for department/role/legacy-entity composition.
- **Evidence that would REJECT:** Negligible manager-level ICC — outcomes are well explained
  by department/role/entity alone.
- **Provisional priority:** Wave 1.

### MG-2 — Outlier manager concentration
- **Business question:** Does a small subset of managers account for a disproportionate share
  of regrettable attrition and low engagement within their teams?
- **Why it matters:** Distinguishes "manager quality matters somewhat everywhere" (MG-1, a
  general capability-building case) from "a specific, addressable subset of managers/teams
  drives most of the problem" (a targeted, faster-payback intervention).
- **Datasets required:** Same as MG-1.
- **Variables required:** Same as MG-1, aggregated to manager level.
- **Correct population/denominator:** Managers with ≥5 direct reports (to avoid unstable
  small-team rates).
- **Proposed analytical method:** Pareto/concentration analysis of team-level regrettable-
  attrition counts and low-engagement prevalence across managers (e.g., what % of the total
  is accounted for by the top decile of managers).
- **Statistical test/model:** Empirical Bayes shrinkage estimate of manager-level rates (to
  avoid mistaking small-sample noise for true outlier status) before ranking managers.
- **Potential confounders:** Same as MG-1 — team composition must be adjusted for before
  labelling a manager an "outlier."
- **Leakage risks:** None.
- **Ethical considerations:** This is the most sensitive hypothesis in the register — any
  output must remain fully anonymised in all external-facing material (deck, appendix); any
  internal-only manager-level output must be flagged as diagnostic, not disciplinary, and
  paired with a support/enablement framing, consistent with Section 11's "structural before
  individual-blame" principle.
- **Possible financial impact method:** Aggregate dollar exposure attributable to the
  concentrated outlier group (anonymised), to justify a manager-capability investment
  business case.
- **Evidence that would SUPPORT:** A clearly disproportionate concentration (e.g., top 10% of
  managers by shrinkage-adjusted rate account for a share of regrettable attrition well above
  10%) that survives the composition-adjustment check.
- **Evidence that would REJECT:** Concentration is no greater than expected under a roughly
  uniform rate with sampling noise (i.e., the "outliers" are a statistical artefact of small
  team sizes).
- **Provisional priority:** Wave 2 (ethically sensitive — sequence after MG-1 establishes
  whether manager effects are material at all).

### MG-3 — Acting/interim management and team engagement
- **Business question:** Are teams led by an acting/interim manager (`acting_appointment`==
  True, applicable at L2–L4) associated with lower `manager_effectiveness` scores than teams
  led by a substantively-appointed manager?
- **Why it matters:** If true, this is a very concrete, structural, easily-fixed finding
  (reduce time-in-acting-role, or provide acting-manager support) — a strong candidate for
  "tractable" scoring.
- **Datasets required:** `employees.csv`, `engagement.csv`.
- **Variables required:** `acting_appointment` (on the manager's own record), `manager_id`,
  `manager_effectiveness` (aggregated to the manager's team).
- **Correct population/denominator:** Managers at L2–L4 (where `acting_appointment` is
  applicable) with ≥5 direct reports.
- **Proposed analytical method:** Compare team-average `manager_effectiveness` between acting
  and substantive managers, controlling for department and manager tenure-in-role.
- **Statistical test/model:** Linear regression / mixed-effects model of team-average
  manager_effectiveness on acting_appointment status, controlling for department, level.
- **Potential confounders:** Acting appointments may be more common in recently-disrupted
  teams (e.g., post-acquisition or post-departure of the substantive manager) — the
  disruption itself, not the acting status, could be the true driver. Flag this explicitly as
  a hard-to-fully-rule-out confound.
- **Leakage risks:** None.
- **Ethical considerations:** Aggregate only; do not identify specific acting managers.
- **Possible financial impact method:** If confirmed, estimate the engagement/attrition gap
  attributable to acting-management periods and frame against the cost of faster permanent-
  appointment processes or interim-manager support programs.
- **Evidence that would SUPPORT:** Significantly lower manager_effectiveness (and,
  secondarily, higher team attrition) under acting managers, robust to the disruption
  confound as far as the data allows.
- **Evidence that would REJECT:** No significant difference.
- **Provisional priority:** Wave 2.

### MG-4 — Span of control and manager overload
- **Business question:** Is a larger manager span of control (team size) associated with lower
  `manager_effectiveness` ratings and/or higher team attrition?
- **Why it matters:** A span-of-control finding translates directly into an organisational-
  design recommendation (headcount/structure), which is unusually concrete for a CHRO to act
  on.
- **Datasets required:** `employees.csv`, `engagement.csv`, `attrition_log.csv`.
- **Variables required:** `manager_id` (count of direct reports), `manager_effectiveness`,
  attrition outcomes, `department`.
- **Correct population/denominator:** All managers (any level with direct reports), P1 for
  team composition.
- **Proposed analytical method:** Regression of team-average manager_effectiveness and team
  attrition rate on span of control, controlling for department and role_level.
- **Statistical test/model:** OLS/logistic regression with department fixed effects;
  non-linearity check (span effects are often threshold-based, not linear — test with a
  spline or quantile bins).
- **Potential confounders:** Department norms for span of control differ structurally (e.g.,
  Operations-Processing roles may have naturally larger teams than Executive) — department
  fixed effects are essential here.
- **Leakage risks:** None.
- **Ethical considerations:** Aggregate only.
- **Possible financial impact method:** If a threshold effect is found (e.g., effectiveness
  drops sharply above N direct reports), estimate headcount/dollar cost of restructuring
  spans above that threshold vs. attrition cost avoided.
- **Evidence that would SUPPORT:** Significant negative relationship (or a clear threshold
  effect) between span of control and manager_effectiveness/team retention, net of
  department norms.
- **Evidence that would REJECT:** No relationship, or the relationship is fully explained by
  department norms alone.
- **Provisional priority:** Wave 3.

---

## 6. Acquisition Integration (AI)

### AI-1 — Compensation vs. culture as the Entity_B driver (tests H-Mgmt-2)
- **Business question:** Is Entity_B's elevated attrition better explained by inherited
  compensation positioning (`compa_ratio`) than by engagement/cultural-integration measures?
- **Why it matters:** Directly tests management's narrative that Entity_B attrition is a
  temporary "stabilisation" issue — if compensation is the real driver, it will not resolve
  on its own by Q2 FY2026 as management projects, and needs a specific pay intervention.
- **Datasets required:** `employees.csv`, `engagement.csv`, `attrition_log.csv`.
- **Variables required:** `legacy_entity_code`, `compa_ratio`, engagement dimensions,
  `exit_type`, `department`, `role_level`.
- **Correct population/denominator:** P1+P2 (all employees at risk during the window),
  restricted for the core comparison to Entity_B vs. NovaCorp-Origin, matched/controlled on
  department and role_level.
- **Proposed analytical method:** Multivariable logistic regression of voluntary exit on
  `legacy_entity_code`, `compa_ratio`, and engagement composite jointly, to see which retains
  explanatory power once the others are included (a horse-race, not a single-variable test).
- **Statistical test/model:** Logistic regression with department/role_level controls;
  compare nested models (entity-only vs. entity+compa_ratio vs. entity+compa_ratio+
  engagement) via likelihood-ratio tests to see how much of the entity effect each factor
  absorbs.
- **Potential confounders:** Entity_B employees may cluster in specific departments/levels
  where compa_ratio norms differ for reasons unrelated to the acquisition — control for
  department/level throughout.
- **Leakage risks:** Use only pre-exit engagement waves and current (not `salary_at_exit`,
  which is post-outcome) compa_ratio from `employees.csv`.
- **Ethical considerations:** None beyond standard; this is a structural/organisational
  question, not about individuals.
- **Possible financial impact method:** If compensation is confirmed as a material, distinct
  driver, estimate the cost of a compa_ratio correction for the Entity_B cohort against the
  Section 14 replacement-cost savings from reduced attrition in that cohort.
- **Evidence that would SUPPORT:** `compa_ratio` remains a significant predictor of Entity_B
  attrition after controlling for department/level, and materially reduces the residual
  "Entity_B effect" in the nested-model comparison.
- **Evidence that would REJECT:** The Entity_B effect persists essentially unchanged after
  controlling for compa_ratio, while engagement measures absorb most of it instead
  (supporting management's cultural-integration narrative), or neither absorbs it
  (unexplained by either candidate factor).
- **Provisional priority:** Wave 1 (this is the single most consequential test in the entire
  register given Entity_B's confirmed 15.0% vs. 10.4% group-average gap and its explicit
  place in the Annual Report's forward strategy).

### AI-2 — Survivorship check on the Entity_A "success" narrative (tests H-Mgmt-1)
- **Business question:** Does Entity_A's lower-than-average attrition rate (7.5% vs. 10.4%)
  hold up once compared to NovaCorp-Origin employees at the same time-since-hire, rather than
  being an artefact of already having lost its highest-flight-risk people in earlier years
  (outside the observation window)?
- **Why it matters:** Distinguishes "integration genuinely worked" from "the people most
  likely to leave already left before this data started" — materially changes whether
  Entity_A is a template to replicate for Entity_B/C or a survivorship illusion.
- **Datasets required:** `employees.csv`.
- **Variables required:** `legacy_entity_code`, `hire_date`, `tenure_months`, `department`,
  `role_level`.
- **Correct population/denominator:** P6 (full roster, to allow tenure/survival framing),
  Entity_A vs. NovaCorp-Origin, matched on department/level and (as best approximable)
  tenure-since-hire band.
- **Proposed analytical method:** Compare current attrition rate for Entity_A vs. NovaCorp-
  Origin employees within matched tenure bands, rather than a raw unmatched comparison.
- **Statistical test/model:** Stratified comparison (by tenure band) with a Mantel-Haenszel
  test, or a Cox model with legacy_entity_code and tenure interaction.
- **Potential confounders:** Department/role-level mix differences between Entity_A and
  NovaCorp-Origin.
- **Leakage risks:** None; explicitly a bias-check exercise.
- **Ethical considerations:** None.
- **Possible financial impact method:** Not directly monetised; a credibility check that
  determines whether an "Entity_A playbook" recommendation is well-founded.
- **Evidence that would SUPPORT (i.e., supports management's claim as genuine):** Entity_A's
  attrition advantage persists within matched tenure/department/level strata.
- **Evidence that would REJECT (i.e., survivorship artefact):** The advantage shrinks
  substantially or disappears once matched on tenure/department/level.
- **Provisional priority:** Wave 1.

### AI-3 — Dose-response of time-since-acquisition on attrition
- **Business question:** Does attrition risk within each acquired cohort decline
  monotonically the longer the cohort has been part of NovaCorp, consistent with a genuine
  "integration takes time" effect?
- **Why it matters:** A clean dose-response pattern would meaningfully support the
  "stabilisation" narrative in general (beyond the specific Entity_B compensation-vs-culture
  question in AI-1); its absence would undermine the "just wait it out" framing entirely.
- **Datasets required:** `employees.csv`.
- **Variables required:** `legacy_entity_code`, `hire_date` (as a proxy — true acquisition
  date is only known at the cohort level from the Annual Report: Entity_A≈FY2022,
  Entity_B≈FY2023, Entity_C≈late FY2024 — document this as an approximation, not a precise
  per-employee acquisition date), `tenure_months`, `exit_date`.
- **Correct population/denominator:** P6, all three acquired cohorts.
- **Proposed analytical method:** Approximate each cohort's "quarters since acquisition" using
  the Annual-Report-stated acquisition period, and plot quarterly attrition rate against
  quarters-since-acquisition for each cohort on a common axis.
- **Statistical test/model:** Trend test (attrition rate regressed on quarters-since-
  acquisition, cohort as a fixed effect); explicitly caveated given the cohort-level (not
  individual-level) precision of the "since-acquisition" timing.
- **Potential confounders:** Macro/company-wide attrition trends (e.g., the RBA rate cycle,
  general FY2025 conditions) could coincide with and be mistaken for a cohort-specific
  stabilisation trend — include a NovaCorp-Origin trend line as a baseline comparison.
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Informs the credibility of management's FY2026
  guidance that Entity_B will normalise "within 12 months of programme completion" — not
  itself a cost estimate.
- **Evidence that would SUPPORT:** A visible downward trend with increasing time-since-
  acquisition, consistent across cohorts and distinct from the NovaCorp-Origin baseline trend.
- **Evidence that would REJECT:** No consistent trend, or a trend indistinguishable from the
  company-wide baseline.
- **Provisional priority:** Wave 2.

### AI-4 — Engagement trajectory differences by legacy entity, controlling for role mix
- **Business question:** Do engagement trajectories differ by `legacy_entity_code` even after
  controlling for department/role/level, indicating a genuine cultural-integration effect
  distinct from what kind of work people happen to do?
- **Why it matters:** Isolates "integration/culture" from "role composition" as an
  explanation, directly relevant to whether the "People Reinvention Programme" should target
  culture specifically.
- **Datasets required:** `engagement.csv`, `employees.csv`.
- **Variables required:** 7 engagement dimensions, `wave_number`, `legacy_entity_code`,
  `department`, `role_level`.
- **Correct population/denominator:** P1, respondents, across all four `legacy_entity_code`
  groups.
- **Proposed analytical method:** Mixed-effects model of each engagement dimension on
  `legacy_entity_code` × `wave_number`, controlling for department and role_level, with
  employee random intercepts.
- **Statistical test/model:** Mixed-effects regression; BH-corrected across the 7 dimensions
  tested.
- **Potential confounders:** Department/role_level composition (explicitly controlled for in
  the model itself, not just noted).
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Not directly monetised; supports/refutes the case for
  entity-specific (vs. department-specific) intervention design.
- **Evidence that would SUPPORT:** Significant `legacy_entity_code` main effect or
  entity×wave interaction remaining after department/role_level controls.
- **Evidence that would REJECT:** Legacy-entity differences disappear once department/role
  composition is controlled for (i.e., it was a role-mix story all along).
- **Provisional priority:** Wave 2.

### AI-5 — Does Risk & Compliance attrition = acquisition effect wearing a department label? (tests H-Mgmt-3, overlaps IX-4)
- **Business question:** Is elevated Risk & Compliance attrition driven specifically by
  acquired (Entity_A/B/C) employees within that department, or is it elevated among
  NovaCorp-Origin Risk & Compliance staff too (i.e., a genuine FAR/regulatory-market effect
  independent of acquisition history)?
- **Why it matters:** Management's narrative (H-Mgmt-3) attributes Risk & Compliance
  attrition to external FAR-driven competition for talent; if the effect is actually
  concentrated in acquired sub-populations, the intervention should be integration-focused,
  not market-pay-focused, or some blend of both with a different emphasis.
- **Datasets required:** `employees.csv`, `attrition_log.csv`.
- **Variables required:** `department`, `legacy_entity_code`, `role_level`, `exit_type`.
- **Correct population/denominator:** P1+P2, restricted to `department`=='Risk & Compliance',
  split by `legacy_entity_code`.
- **Proposed analytical method:** Within-department attrition rate by legacy entity,
  specifically at Director/L4 level (the level the Annual Report names).
- **Statistical test/model:** Chi-square / logistic regression of voluntary exit on
  legacy_entity_code, restricted to Risk & Compliance, controlling for role_level.
- **Potential confounders:** Small cell sizes at the department × entity × level intersection
  — flag explicitly if underpowered (Section 12).
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Refines the targeting (and therefore cost/benefit
  framing) of any Risk & Compliance retention intervention.
- **Evidence that would SUPPORT (acquisition-driven):** Attrition within Risk & Compliance is
  significantly higher among Entity_A/B/C staff than NovaCorp-Origin staff at the same level.
- **Evidence that would REJECT (i.e., supports a broad market-driven story):** Attrition is
  elevated fairly uniformly across legacy-entity groups within Risk & Compliance, including
  NovaCorp-Origin.
- **Provisional priority:** Wave 2 (cell-size risk noted — may end up inconclusive).

---

## 7. Compensation Positioning (CM)

### CM-1 — Below-band pay and voluntary attrition
- **Business question:** Do employees with a low `compa_ratio` (below their role-level band
  midpoint) show higher voluntary attrition than those at/above midpoint, independent of
  performance?
- **Why it matters:** A clean compensation-attrition link is one of the most directly
  actionable levers available (a pay-band correction), if it survives confound checks.
- **Datasets required:** `employees.csv`, `attrition_log.csv`, `performance.csv`.
- **Variables required:** `compa_ratio`, `exit_type`, `department`, `role_level`, `tenure_months`,
  `performance_rating`/`goal_achievement_score`.
- **Correct population/denominator:** P1+P2, all employees at risk during the window.
- **Proposed analytical method:** Logistic regression of voluntary exit on `compa_ratio`,
  controlling for department, role_level, tenure, and performance.
- **Statistical test/model:** Logistic regression with the above controls; report odds ratio
  with CI per 0.1 unit of compa_ratio, not just a binary below/above-midpoint split, to avoid
  arbitrary threshold effects.
- **Potential confounders:** Performance (lower performers may also be paid less and leave
  more, for reasons unrelated to pay itself) — controlled for directly in the model.
- **Leakage risks:** Use `compa_ratio` from `employees.csv` (current/at-employment value), not
  `salary_at_exit` from `attrition_log.csv` (post-outcome, though numerically identical per
  Section 5 — still conceptually the pre-exit variable to reason from).
- **Ethical considerations:** None beyond standard; this is a compensation-structure question,
  not individual-level.
- **Possible financial impact method:** If confirmed, estimate the cost of correcting
  compa_ratio for the below-midpoint, elevated-flight-risk segment vs. Section 14 replacement
  cost avoided — a direct pay-equity-investment ROI case.
- **Evidence that would SUPPORT:** Significant negative association between compa_ratio and
  voluntary exit odds, robust to performance controls.
- **Evidence that would REJECT:** No significant association once performance/tenure are
  controlled for.
- **Provisional priority:** Wave 1.

### CM-2 — Pay compression/inversion in high-attrition segments
- **Business question:** Is compa_ratio dispersion (compression or inversion — e.g., long-
  tenured employees paid at or below the rate of recent hires at the same level) greater in
  high-attrition segments (Entity_B, Risk & Compliance L4) than low-attrition segments?
- **Why it matters:** Compression specifically (as distinct from simply "low pay") is a
  well-documented driver of dissatisfaction among tenured staff and points to a different fix
  (internal equity adjustment) than a flat market-pay increase.
- **Datasets required:** `employees.csv`.
- **Variables required:** `compa_ratio`, `tenure_months`, `hire_date`, `department`,
  `role_level`, `legacy_entity_code`.
- **Correct population/denominator:** P1, within department × role_level cells with enough
  headcount to compute a meaningful dispersion statistic.
- **Proposed analytical method:** Within-cell compa_ratio-vs-tenure correlation; a positive
  correlation is healthy (tenure rewarded), a flat/negative correlation indicates compression/
  inversion. Compare this correlation across segments.
- **Statistical test/model:** Correlation/regression of compa_ratio on tenure_months within
  cells; compare coefficients across high- vs. low-attrition segments.
- **Potential confounders:** Role-level definitions may differ subtly in scope across legacy
  systems (`data_source_system`) — a data-quality check to run before trusting cross-entity
  compa_ratio comparability.
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Scope of a targeted internal-equity pay correction for
  the affected tenure band(s) within the identified segment(s).
- **Evidence that would SUPPORT:** Flatter or negative tenure–compa_ratio relationship in
  high-attrition segments compared to low-attrition segments.
- **Evidence that would REJECT:** No meaningful difference in the tenure–pay relationship
  across segments.
- **Provisional priority:** Wave 3.

### CM-3 — Pay-equity fairness audit (fairness-auditing use only — see Section 11)
- **Business question:** Do gender or cultural-background pay gaps in `compa_ratio` exist
  after controlling for level, department, and tenure?
- **Why it matters:** A required responsible-AI/fairness check given Section 11 and the
  Annual Report's own stated female-representation target; this is audit, not targeting.
- **Datasets required:** `employees.csv`.
- **Variables required:** `compa_ratio`, `gender`, `cultural_background`, `role_level`,
  `department`, `tenure_months`.
- **Correct population/denominator:** P1 (active workforce, consistent with how the Annual
  Report frames its own representation metrics).
- **Proposed analytical method:** Standard pay-gap decomposition (e.g., an Oaxaca-Blinder-
  style or simple regression-adjusted gap) controlling for level/department/tenure.
- **Statistical test/model:** OLS regression of compa_ratio (or log-salary) on gender/cultural
  background with level/department/tenure controls; report adjusted gap with CI.
- **Potential confounders:** Role_family/level composition differences by gender/cultural
  background are themselves part of the structural story (a "pipeline" gap, not just a "pay
  for the same job" gap) — report both the raw and adjusted gap to show both effects.
- **Leakage risks:** None.
- **Ethical considerations:** **This hypothesis exists solely for fairness auditing and
  structural-disparity understanding, per Section 11. Its output must never be used to guide
  who receives a retention offer, comp adjustment, or other individual intervention on the
  basis of gender/cultural background.** Any recommendation arising from this must be
  structural/policy-level (e.g., band-design review), not individually targeted.
- **Possible financial impact method:** Cost of closing any confirmed adjusted gap, presented
  as a fairness/compliance investment case, separate from the core $42M attrition-cost
  narrative.
- **Evidence that would SUPPORT (a gap exists):** Statistically significant adjusted gap
  after controlling for level/department/tenure.
- **Evidence that would REJECT:** No significant adjusted gap (raw gap, if any, fully
  explained by role/level composition).
- **Provisional priority:** Wave 1 (ethics-mandated, not optional — must be run regardless of
  whether it feeds the final storyline, per the 20%-weighted Ethics criterion).

### CM-4 — The "underpaid star" flight-risk segment
- **Business question:** Do high performers with below-midpoint compa_ratio show
  disproportionately higher attrition than high performers at/above midpoint?
- **Why it matters:** If it exists and is sized adequately, this is potentially the single
  highest-ROI, most narrowly-targetable segment in the entire register — a small, well-
  defined, high-value population.
- **Datasets required:** `employees.csv`, `performance.csv`, `attrition_log.csv`.
- **Variables required:** `compa_ratio`, `performance_rating`/`goal_achievement_score`,
  `exit_type`, `regrettable_flag`.
- **Correct population/denominator:** P1+P2 restricted to employees with a "High Performer"
  or "Outstanding" rating in their most recent pre-exit (or, for stayers, most recent)
  review.
- **Proposed analytical method:** Interaction model — voluntary exit ~ compa_ratio ×
  high_performer_flag, controlling for department/role_level.
- **Statistical test/model:** Logistic regression with interaction term; test whether the
  compa_ratio effect on attrition is significantly steeper among high performers than others.
- **Potential confounders:** High performers may be systematically younger/more senior/
  differently distributed across departments — control for role_level/department/tenure.
- **Leakage risks:** Use pre-exit performance rating only.
- **Ethical considerations:** None beyond standard (this is a performance × pay interaction,
  not a protected-characteristic one).
- **Possible financial impact method:** Size this specific segment (headcount, current
  compa_ratio gap to midpoint) and cost a targeted correction against Section 14's
  replacement-cost savings — likely the register's clearest small-scope, high-confidence
  business case if confirmed.
- **Evidence that would SUPPORT:** Significant compa_ratio × performance interaction, with
  the pay-attrition relationship notably steeper among high performers.
- **Evidence that would REJECT:** No significant interaction (pay affects attrition similarly
  regardless of performance level).
- **Provisional priority:** Wave 1 (high expected business/financial materiality if
  confirmed — sequence early).

---

## 8. High Performer / High Potential Retention (HP)

### HP-1 — Is NovaCorp actually losing its best people disproportionately?
- **Business question:** Do HiPo-flagged and/or high-performance-rated employees have
  voluntary attrition rates that are higher, lower, or statistically indistinguishable from
  the general workforce?
- **Why it matters:** This is the single most important test for whether the "$22–25M
  regrettable attrition = losing high-value people" framing is empirically justified at all.
- **Datasets required:** `employees.csv`, `performance.csv`, `attrition_log.csv`.
- **Variables required:** `hipo_flag`, pre-exit `performance_rating`, `exit_type`,
  `regrettable_flag`.
- **Correct population/denominator:** P1+P2, split by `hipo_flag` and by most-recent pre-exit
  performance band.
- **Proposed analytical method:** Voluntary-attrition-rate comparison by HiPo status and by
  performance band, with Wilson CIs given HiPo is likely a minority population.
- **Statistical test/model:** Chi-square / logistic regression of voluntary exit on
  hipo_flag and performance band jointly, controlling for department/role_level.
- **Potential confounders:** Department/role_level composition of the HiPo population.
- **Leakage risks:** Pre-exit performance only.
- **Ethical considerations:** None beyond standard aggregation; watch for small-cell
  suppression given HiPo is likely a minority flag (Section 11/12).
- **Possible financial impact method:** If HiPo/high-performer attrition rate is confirmed
  elevated, this directly validates (and helps re-size) the regrettable-attrition dollar
  estimate at a higher average replacement-cost multiplier (since higher salary/seniority
  people cost more to replace per Section 14's 1.5× formula).
- **Evidence that would SUPPORT:** HiPo/high-performer voluntary attrition rate is
  statistically significantly higher than the general population rate.
- **Evidence that would REJECT:** HiPo/high-performer attrition rate is equal to or lower than
  the general population — meaning NovaCorp's regrettable-attrition problem is not
  specifically a "losing our best" problem, and the $22–25M framing needs re-examination or
  re-labelling.
- **Provisional priority:** Wave 1 (foundational for the entire regrettable-attrition
  narrative — must be tested early).

### HP-2 — HiPo exits skew toward "pull" pathway
- **Business question:** Do HiPo employees who leave skew more toward the "pull"
  (opportunity-driven) pathway than non-HiPo leavers?
- **Why it matters:** Would corroborate an external-market-demand explanation specifically for
  top talent, pointing toward a market-competitiveness (pay/brand) response rather than an
  internal-culture one for this specific segment.
- **Datasets required:** `attrition_log.csv`, `employees.csv`.
- **Variables required:** `hipo_flag`, `pathway`, `exit_type`.
- **Correct population/denominator:** P3 (voluntary exits) split by `hipo_flag`.
- **Proposed analytical method:** Cross-tab pathway × hipo_flag among voluntary leavers.
- **Statistical test/model:** Chi-square / Fisher's exact test (likely small HiPo-leaver n —
  use exact test).
- **Potential confounders:** Department/role_level composition.
- **Leakage risks:** None (post-hoc descriptive, `pathway` used as outcome only).
- **Ethical considerations:** Small-cell suppression if HiPo-leaver n is very small.
- **Possible financial impact method:** Not directly monetised; informs whether a market-pay
  or an internal-engagement lever is the better-targeted response for this segment.
- **Evidence that would SUPPORT:** Significantly higher pull-pathway share among HiPo leavers
  vs. non-HiPo leavers.
- **Evidence that would REJECT:** No significant difference, or sample too small to
  distinguish (report as inconclusive if so).
- **Provisional priority:** Wave 3 (gated on HP-1 confirming a base effect and adequate n).

### HP-3 — HiPo recognition/investment gap
- **Business question:** Do HiPo employees show lower `senior_leadership_trust` or
  `career_development` scores than their performance level would predict, suggesting a
  recognition/investment gap despite formal HiPo status?
- **Why it matters:** If NovaCorp's HiPo employees don't feel invested in despite the formal
  label, the flag is not translating into a retention-protective experience — a "label
  without substance" finding with a clear program-design fix.
- **Datasets required:** `engagement.csv`, `employees.csv`, `performance.csv`.
- **Variables required:** `hipo_flag`, `senior_leadership_trust`, `career_development`,
  `goal_achievement_score`/`performance_rating`.
- **Correct population/denominator:** P1, respondents, comparing HiPo vs. non-HiPo employees
  matched on performance band.
- **Proposed analytical method:** Regression of the two engagement dimensions on hipo_flag,
  controlling for performance band, department, role_level.
- **Statistical test/model:** Linear regression with the above controls; BH-corrected across
  the 2 dimensions tested.
- **Potential confounders:** Performance band itself (controlled for directly).
- **Leakage risks:** None.
- **Ethical considerations:** None beyond standard.
- **Possible financial impact method:** Not directly monetised; supports a low-cost program-
  design recommendation (e.g., structured HiPo career conversations) rather than a large
  compensation-based one.
- **Evidence that would SUPPORT:** HiPo employees score significantly lower on these
  dimensions than performance-matched non-HiPo peers.
- **Evidence that would REJECT:** No significant difference, or HiPo employees score higher
  (i.e., the program is working as intended).
- **Provisional priority:** Wave 3.

### HP-4 — HiPo promotion-pipeline speed
- **Business question:** Is the promotion pipeline for HiPo employees meaningfully faster
  (higher promotion_recommendation rate, less time at level) than for non-HiPo employees of
  similar performance?
- **Why it matters:** Tests whether the HiPo program has real "teeth"; overlaps with CP-series
  hypotheses but specifically isolates the HiPo-labelling effect.
- **Datasets required:** `employees.csv`, `performance.csv`.
- **Variables required:** `hipo_flag`, `promotion_recommendation`, `promotion_eligible`,
  `tenure_months`, `role_level`.
- **Correct population/denominator:** P1, promotion-eligible employees, split by hipo_flag.
- **Proposed analytical method:** Logistic regression of promotion_recommendation on
  hipo_flag, controlling for performance band, department, role_level, tenure.
- **Statistical test/model:** Logistic regression with the above controls.
- **Potential confounders:** Performance band (controlled for directly); tenure.
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Not directly monetised; a program-effectiveness
  finding supporting (or challenging) continued investment in the HiPo identification
  process itself.
- **Evidence that would SUPPORT:** HiPo status significantly increases promotion-
  recommendation likelihood net of performance/tenure.
- **Evidence that would REJECT:** No significant effect — the HiPo flag does not translate
  into faster progression once performance is accounted for.
- **Provisional priority:** Wave 3.

---

## 9. Survey Non-Response Behaviour (SR)

### SR-1 — Non-response as a leading indicator
- **Business question:** Is non-response to an engagement survey wave (`response_flag`==
  False) itself associated with elevated subsequent voluntary attrition, similar to or
  distinct from low-score disengagement?
- **Why it matters:** If "going silent" is as predictive as scoring low, HR's current
  engagement dashboard (which typically reports only among respondents) is systematically
  blind to a meaningful risk signal.
- **Datasets required:** `engagement.csv`, `attrition_log.csv`, `employees.csv`.
- **Variables required:** `response_flag` (per wave), `wave_number`, `exit_date`, `exit_type`.
- **Correct population/denominator:** P7 (survey-eligible population per wave); for the
  outcome side, subsequent voluntary exit within a defined follow-up window after each wave.
- **Proposed analytical method:** Compare subsequent-voluntary-exit rate between non-
  respondents and respondents at a given wave, and between non-respondents and *low-scoring*
  respondents specifically (a three-way comparison: high-scorers vs. low-scorers vs. non-
  responders).
- **Statistical test/model:** Logistic regression / Cox model of subsequent voluntary exit on
  a 3-level wave-status variable (responded-high, responded-low, non-responded), controlling
  for department/role_level/tenure.
- **Potential confounders:** Tenure and contract type may drive both non-response (e.g., less
  survey access/engagement with HR process for casual/part-time staff — see SR-4) and
  attrition independently — control for contract_type.
- **Leakage risks:** Must use only the wave's response status and prior information to predict
  *subsequent* exit, not concurrent or past exit.
- **Ethical considerations:** If confirmed, this finding must be framed as a case for
  improving survey reach/relevance and manager check-ins, not as grounds for treating non-
  response itself as a punitive or monitoring trigger against individuals.
- **Possible financial impact method:** Not directly monetised; a methodological finding that
  could materially change how "disengagement" is measured/sized going forward (feeds back
  into DP-1's population definition as a robustness check).
- **Evidence that would SUPPORT:** Non-respondents show subsequent voluntary-exit rates
  statistically indistinguishable from (or higher than) low-scoring respondents, and clearly
  higher than high-scoring respondents.
- **Evidence that would REJECT:** Non-respondents' subsequent exit rate resembles the overall
  average or the high-scoring group, suggesting non-response is unrelated to attrition risk
  (e.g., just administrative/random).
- **Provisional priority:** Wave 1 (directly actionable for how the CHRO should read her own
  existing survey dashboard, regardless of the rest of the narrative).

### SR-2 — Structural (non-random) patterns in non-response
- **Business question:** Do non-response rates differ systematically by department, legacy
  entity, or manager, indicating structural disengagement with the survey process itself
  rather than random non-completion?
- **Why it matters:** A structural non-response pattern (e.g., concentrated in Entity_B or
  specific managers' teams) is itself a diagnostic signal, and also a data-quality caveat for
  every other engagement-based finding in segments where non-response is high.
- **Datasets required:** `engagement.csv`, `employees.csv`.
- **Variables required:** `response_flag`, `department`, `legacy_entity_code`, `manager_id`,
  `wave_number`.
- **Correct population/denominator:** P7.
- **Proposed analytical method:** Non-response rate table by department/legacy entity/wave;
  mixed-effects logistic model of response_flag with a manager random effect.
- **Statistical test/model:** Chi-square (department/entity); ICC on the manager random
  effect, as in MG-1.
- **Potential confounders:** Department/entity composition overlap (same caution as MG-1/DP-2).
- **Leakage risks:** None.
- **Ethical considerations:** Manager-level results aggregate/anonymised only (Section 11).
- **Possible financial impact method:** Not directly monetised; a data-quality/measurement
  finding.
- **Evidence that would SUPPORT:** Significant, non-trivial variation in non-response rate by
  segment and/or a meaningful manager-level ICC in non-response.
- **Evidence that would REJECT:** Non-response is roughly uniform across segments (consistent
  with administrative/random causes).
- **Provisional priority:** Wave 2.

### SR-3 — "Going dark" transitions
- **Business question:** Do employees who transition from responding to non-responding
  between consecutive waves show a distinct risk profile from chronic non-responders or
  chronic responders?
- **Why it matters:** A "going dark" transition (as opposed to a stable pattern) may be a
  sharper, more time-specific warning signal than static respondent/non-respondent status.
- **Datasets required:** `engagement.csv`, `attrition_log.csv`.
- **Variables required:** `response_flag` sequence per employee across waves, `exit_date`.
- **Correct population/denominator:** P7, employees with at least 2 consecutive wave
  opportunities.
- **Proposed analytical method:** Classify each employee's wave-response sequence into
  patterns (always-responds, always-dark, went-dark, resumed) and compare subsequent
  voluntary-exit rates across patterns.
- **Statistical test/model:** Chi-square across pattern categories; report with CIs, watch
  for small cells in less common patterns.
- **Potential confounders:** Timing — a "went dark then exited two waves later" employee had
  more time to be observed exiting than someone who went dark in the final wave; account for
  exposure time in the comparison.
- **Leakage risks:** Only use pattern information available before the relevant exit
  point.
- **Ethical considerations:** Same as SR-1 — support-oriented framing, not surveillance.
- **Possible financial impact method:** Not directly monetised; refines SR-1's early-warning
  framing if it holds.
- **Evidence that would SUPPORT:** "Went-dark" employees show elevated subsequent exit risk
  relative to always-responds and comparable to or exceeding always-dark.
- **Evidence that would REJECT:** No meaningful difference between transition patterns.
- **Provisional priority:** Wave 3.

### SR-4 — Access/fatigue vs. disengagement explanation for non-response
- **Business question:** Is non-response better explained by structural survey-access
  patterns (e.g., contract_type, tenure, role level) than by disengagement per se?
- **Why it matters:** If non-response is largely a Casual/Part-time access issue rather than a
  disengagement signal, SR-1's "early warning" framing needs an important caveat, and the fix
  is a survey-process fix, not an engagement intervention.
- **Datasets required:** `engagement.csv`, `employees.csv`.
- **Variables required:** `response_flag`, `contract_type`, `tenure_months`, `role_level`.
- **Correct population/denominator:** P7.
- **Proposed analytical method:** Logistic regression of response_flag on contract_type,
  tenure, role_level jointly.
- **Statistical test/model:** Logistic regression; report which factors retain explanatory
  power.
- **Potential confounders:** Contract_type may itself correlate with department/role_family —
  include as controls.
- **Leakage risks:** None.
- **Ethical considerations:** None beyond standard (contract_type is not a protected
  characteristic, though it may correlate with age/caring responsibilities — treat with the
  same fairness-audit caution as Section 11 recommends for proxies).
- **Possible financial impact method:** Not directly monetised; a measurement-validity
  finding.
- **Evidence that would SUPPORT:** Contract_type/tenure/role_level substantially explain
  non-response, independent of any engagement-score-based explanation.
- **Evidence that would REJECT:** These structural factors have little explanatory power,
  supporting a more direct disengagement interpretation of non-response (strengthening SR-1).
- **Provisional priority:** Wave 2 (needed to correctly interpret SR-1's result).

---

## 10. Department / Role-Specific Problems (DR)

### DR-1 — Do attrition drivers differ by department?
- **Business question:** Is the *dominant driver* of voluntary attrition (compensation vs.
  engagement vs. manager vs. career-progression) different across departments, such that a
  single company-wide lever would under-serve some departments?
- **Why it matters:** Directly tests whether a segmented recommendation set outperforms a
  single uniform one — central to the "actionability" judging criterion (15%).
- **Datasets required:** All four.
- **Variables required:** All variables used in CM-1, DP-3, MG-1, and CP-1's models, run
  separately (or with department interactions) per department.
- **Correct population/denominator:** P1+P2, split by department.
- **Proposed analytical method:** Run the CM-1/DP-3/MG-1/CP-1 model specifications with a
  department interaction term (or separately per department if cell sizes allow), and compare
  which predictor(s) carry significant weight in which department.
- **Statistical test/model:** Interaction terms in the pooled models above; likelihood-ratio
  test for whether allowing department-specific coefficients improves fit over a pooled model.
- **Potential confounders:** Smaller departments (Executive Leadership, n=230 total) will be
  underpowered for department-specific modelling — flag explicitly per Section 12 rather than
  force a per-department estimate everywhere.
- **Leakage risks:** Same as the underlying hypotheses being decomposed.
- **Ethical considerations:** Same as the underlying hypotheses.
- **Possible financial impact method:** A department-by-department cost-driver map, enabling
  a differentiated (not one-size-fits-all) resource-allocation recommendation.
- **Evidence that would SUPPORT:** Significant department interaction terms — i.e., the
  predictor that matters most genuinely differs by department.
- **Evidence that would REJECT:** A single pooled model (no department interaction) fits
  about as well — i.e., one company-wide story is adequate.
- **Provisional priority:** Wave 2 (synthesis hypothesis — best run after Wave 1 single-factor
  hypotheses are tested).

### DR-2 — Seniority-level interaction with driver type
- **Business question:** Does the dominant attrition driver differ by seniority (e.g., junior
  levels driven by hiring/onboarding factors, senior levels by compensation/market factors)?
- **Why it matters:** Similar rationale to DR-1 but along the seniority axis rather than
  department — informs whether recommendations should be level-differentiated.
- **Datasets required:** Same as DR-1.
- **Variables required:** Same as DR-1, with `role_level` as the interacting dimension.
- **Correct population/denominator:** P1+P2, split by role_level band (e.g., L1–2 vs. L3–4 vs.
  L5+).
- **Proposed analytical method:** Same interaction-model approach as DR-1, using role_level
  band instead of department.
- **Statistical test/model:** Same as DR-1.
- **Potential confounders:** Level bands have very different headcounts (L1 far larger than
  L7–8) — weight interpretation accordingly and flag small-n bands.
- **Leakage risks:** Same as underlying hypotheses.
- **Ethical considerations:** Same as underlying hypotheses.
- **Possible financial impact method:** A level-differentiated resource-allocation
  recommendation, complementing DR-1.
- **Evidence that would SUPPORT:** Significant role-level-band interaction terms in the
  driver models.
- **Evidence that would REJECT:** No meaningful interaction — driver importance is consistent
  across levels.
- **Provisional priority:** Wave 2.

### DR-3 — Risk & Compliance Director (L4) specific profile
- **Business question:** Is the Risk & Compliance L4 (Director) attrition profile
  (compensation, engagement, workload proxies) distinct enough from the rest of the
  department to warrant the specific intervention the Annual Report names?
- **Why it matters:** Operationalises a named management priority (Section 8/9) with
  independent evidence rather than accepting the narrative at face value.
- **Datasets required:** All four, restricted to Risk & Compliance.
- **Variables required:** `role_level`, `compa_ratio`, engagement dimensions,
  `goal_achievement_score`, `exit_type`.
- **Correct population/denominator:** P1+P2, `department`=='Risk & Compliance',
  `role_level`==4, compared against (a) the rest of Risk & Compliance and (b) L4 employees
  company-wide.
- **Proposed analytical method:** Descriptive profile comparison (attrition rate, compa_ratio,
  engagement means) across these three reference groups; flag small-n risk explicitly given
  this is a narrow department × level cell.
- **Statistical test/model:** Two-sample tests (t-test/Mann-Whitney, chi-square as
  appropriate) for each comparison, BH-corrected across the variables tested; explicit power/
  sample-size caveat given expected small n.
- **Potential confounders:** Tenure and legacy-entity mix within this narrow cell.
- **Leakage risks:** Pre-exit variables only.
- **Ethical considerations:** Small-cell suppression risk is high here — if the cell is too
  small to report safely/reliably, say so rather than force a headline number (Section 11/12).
- **Possible financial impact method:** If a distinct, adequately-sized profile is confirmed,
  cost a targeted L4 Risk & Compliance retention package against Section 14 replacement costs
  for this specific, high-salary, hard-to-backfill population.
- **Evidence that would SUPPORT:** A distinct and adequately-powered profile — e.g.,
  meaningfully lower compa_ratio and/or engagement than comparison groups, alongside elevated
  attrition.
- **Evidence that would REJECT:** No distinguishable profile, or the cell is too small to draw
  any reliable conclusion (report as inconclusive rather than force a finding).
- **Provisional priority:** Wave 2.

### DR-4 — Technology's absolute dollar exposure despite "in line" rate
- **Business question:** Even though the Annual Report classifies Technology's attrition as
  "in line" with the firm average, does its large headcount (22.6% of workforce) make it a
  top-3 department by absolute attrition dollar cost regardless?
- **Why it matters:** A rate-only view (as management's own reporting uses) can obscure a
  large absolute-dollar opportunity; the CHRO needs both views to prioritise correctly.
- **Datasets required:** `employees.csv`, `attrition_log.csv`.
- **Variables required:** `department`, `salary`/`salary_at_exit`, `exit_type`,
  `regrettable_flag`.
- **Correct population/denominator:** P3 (voluntary exits) by department.
- **Proposed analytical method:** Rank departments by absolute Section-14 replacement-cost
  dollars (not just rate), and compare the ranking to a rate-only ranking to show where they
  diverge.
- **Statistical test/model:** Descriptive only (this is a materiality/framing exercise, not a
  hypothesis test in the inferential sense) — report point estimates with the same
  sensitivity ranges as other Section 14 costings.
- **Potential confounders:** N/A (descriptive).
- **Leakage risks:** None.
- **Ethical considerations:** None.
- **Possible financial impact method:** Direct — this *is* the financial-impact exercise
  (Section 14), applied per department.
- **Evidence that would SUPPORT:** Technology (or any large-headcount, "in-line" department)
  ranks materially higher on absolute dollar cost than its rate-based rank would suggest.
- **Evidence that would REJECT:** Department dollar-cost ranking closely tracks its rate-based
  ranking (i.e., headcount-weighting doesn't change the priority order much).
- **Provisional priority:** Wave 1 (cheap to compute, directly reframes prioritisation, and is
  a natural companion output to RA-1).

---

## 11. Interactions Between Areas (IX)

### IX-1 — Acquisition cohort × manager effects
- **Business question:** Is Entity_B's elevated attrition disproportionately concentrated
  under a subset of managers, suggesting integration failure is locally managed rather than
  uniformly structural across the cohort?
- **Why it matters:** If true, a manager-capability intervention targeted at Entity_B team
  leads could be far cheaper and faster than a cohort-wide compensation or culture program.
- **Datasets required:** `employees.csv`, `attrition_log.csv`, `engagement.csv`.
- **Variables required:** `legacy_entity_code`, `manager_id`, exit outcomes, engagement
  dimensions.
- **Correct population/denominator:** Entity_B employees (P1+P2 subset), grouped by manager
  (≥5 Entity_B reports per manager for a stable estimate).
- **Proposed analytical method:** Within Entity_B only, repeat MG-1/MG-2's manager-variance
  decomposition and concentration analysis.
- **Statistical test/model:** Mixed-effects model / ICC, as in MG-1, restricted to the
  Entity_B sub-population.
- **Potential confounders:** Manager team composition (department mix within Entity_B).
- **Leakage risks:** None.
- **Ethical considerations:** Same anonymisation requirements as MG-2.
- **Possible financial impact method:** If concentrated, cost a targeted manager-support
  intervention for the identified (anonymised) subset of Entity_B teams vs. a cohort-wide
  program.
- **Evidence that would SUPPORT:** Meaningful manager-level ICC/concentration within
  Entity_B, larger than the company-wide baseline from MG-1.
- **Evidence that would REJECT:** Entity_B attrition is roughly uniform across its managers —
  a structural, not locally-managed, effect.
- **Provisional priority:** Wave 2 (contingent on both AI-1 and MG-1 being run first).

### IX-2 — Sizing the "underpaid high performer" segment (CM-4 × HP-1)
- **Business question:** Is the underpaid-high-performer segment (CM-4) large enough in
  headcount and salary to represent a financially material share of the $22–25M regrettable-
  attrition component on its own?
- **Why it matters:** Determines whether this narrow, high-confidence segment (if CM-4 and
  HP-1 both confirm) is a "nice footnote" or a genuine primary recommendation candidate.
- **Datasets required:** Same as CM-4 and HP-1.
- **Variables required:** Combined variable set from CM-4 and HP-1.
- **Correct population/denominator:** Intersection of the CM-4 and HP-1 populations.
- **Proposed analytical method:** Headcount and Section-14 dollar sizing of the intersection
  segment, expressed as a % of the total regrettable-attrition cost estimate.
- **Statistical test/model:** Descriptive sizing with a sensitivity range (per Section 14),
  not a fresh hypothesis test (this reuses CM-4/HP-1's statistical results).
- **Potential confounders:** N/A (sizing exercise).
- **Leakage risks:** None beyond what CM-4/HP-1 already carry.
- **Ethical considerations:** Same as CM-4/HP-1.
- **Possible financial impact method:** Direct — expresses the CM-4 finding as a % of the
  $22–25M component, the clearest possible "how much money" answer for this storyline
  candidate.
- **Evidence that would SUPPORT:** The segment represents a non-trivial share (e.g., double-
  digit %) of the regrettable-attrition dollar estimate.
- **Evidence that would REJECT:** The segment is real (per CM-4/HP-1) but too small in dollar
  terms to be a primary recommendation, better placed as a supporting data point.
- **Provisional priority:** Wave 2 (depends entirely on CM-4 and HP-1 results).

### IX-3 — The engagement → non-response → exit funnel
- **Business question:** Does a detectable share of leavers pass through a sequential pattern
  of declining engagement scores followed by non-response before exiting, forming a coherent
  "disengagement funnel" rather than three unrelated signals?
- **Why it matters:** If a funnel pattern is detectable for a meaningful share of leavers, it
  materially strengthens the case that engagement data (not exit interviews) should be
  NovaCorp's primary early-warning system — a significant, higher-confidence upgrade to the
  RA-2/SR-1 findings if they hold individually.
- **Datasets required:** `engagement.csv`, `attrition_log.csv`, `employees.csv`.
- **Variables required:** Full per-employee wave sequence (scores + response_flag), `exit_date`.
- **Correct population/denominator:** P3 (voluntary leavers with ≥3 wave opportunities before
  exit) vs. a matched stayer comparison group.
- **Proposed analytical method:** Sequence/pattern classification (e.g., declining-then-dark
  vs. stable vs. other patterns) and comparison of pattern prevalence between leavers and
  stayers.
- **Statistical test/model:** Chi-square on pattern-category prevalence between leavers and
  stayers; treat as exploratory/descriptive given the compound, multi-step definition (higher
  risk of overfitting a narrative to noise — flag this explicitly and require the pattern to
  be simple/pre-specified, not tuned after looking at the data).
- **Potential confounders:** Same timing/censoring cautions as RA-2 and SR-3, compounded.
- **Leakage risks:** High — this hypothesis combines RA-2 and SR-3's leakage risks; strict
  pre-exit-only sequencing is essential, and the pattern definition must be fixed before
  testing (not adjusted post hoc to fit the leaver data better than the stayer data).
- **Ethical considerations:** Same support-not-surveillance framing as RA-2/SR-1/SR-3.
- **Possible financial impact method:** Not directly monetised; a measurement/early-warning-
  system finding, valuable primarily for its actionability narrative rather than a dollar
  figure.
- **Evidence that would SUPPORT:** A pre-specified "declining then dark" pattern is
  significantly more prevalent among leavers than stayers.
- **Evidence that would REJECT:** No meaningful prevalence difference, or the pattern is too
  rare in both groups to distinguish reliably (report as inconclusive rather than a negative
  finding if underpowered).
- **Provisional priority:** Wave 3 (highest combined leakage/overfitting risk in the register
  — only worth running once RA-2 and SR-1 have independently confirmed their component
  effects).

### IX-4 — Department label vs. acquisition-history explanation (duplicate cross-reference)
- See **AI-5**, which already operationalises this interaction (Risk & Compliance × legacy
  entity). Retained here only as an index entry so the "interactions" area is complete;
  not a separate test to avoid duplicating AI-5's design.

### IX-5 — Compounding risk: HiPo × promotion-stall × underpayment
- **Business question:** Do HiPo employees who are both promotion-stalled (CP-4) AND
  below-midpoint on compa_ratio (CM-1/CM-4) show a disproportionately higher attrition rate
  than either factor predicts alone?
- **Why it matters:** If risk factors compound multiplicatively rather than merely add up,
  this identifies the single narrowest, highest-urgency segment in the entire register — very
  likely small in headcount and therefore cheap to address directly.
- **Datasets required:** `employees.csv`, `performance.csv`, `attrition_log.csv`.
- **Variables required:** `hipo_flag`, promotion-stall proxy (from CP-1/CP-4),
  `compa_ratio`, exit outcomes.
- **Correct population/denominator:** P8 (HiPo subset) crossed with the CP-4 stall
  classification and a below-midpoint compa_ratio flag; likely a very small n — treat any
  result here as strictly exploratory and confirm sample size before drawing any conclusion.
- **Proposed analytical method:** Three-way interaction test if sample size allows; if not
  (likely, given the register's own small-cell warnings on HiPo elsewhere), a simple
  descriptive comparison with explicit "insufficient power" labelling rather than a forced
  statistical test.
- **Statistical test/model:** Logistic regression with interaction terms if n permits;
  otherwise, descriptive only, per Section 12's sample-size documentation requirement.
- **Potential confounders:** Department/role composition of this narrow intersection.
- **Leakage risks:** Same as CP-1/CM-1 (define stall and pay status using only pre-outcome
  information).
- **Ethical considerations:** High small-cell/re-identification risk (Section 11) — this
  hypothesis is the most likely in the register to be reportable only as an aggregate
  directional statement, not a precise estimate, if it turns out headcount is very small.
- **Possible financial impact method:** If a material and adequately-sized segment exists,
  this is a natural closing "quick win" recommendation candidate: a small, named, high-
  confidence group with a clear, low-cost fix (accelerate promotion review + targeted pay
  correction).
- **Evidence that would SUPPORT:** A compounding (super-additive) effect on attrition risk,
  with adequate sample size to trust the estimate.
- **Evidence that would REJECT:** Effects are merely additive (no compounding), or the
  intersection is too small to draw any reliable conclusion.
- **Provisional priority:** Wave 3 (fully contingent on CP-1, CP-4, and CM-1 results, and on
  the intersection being large enough to analyse at all).

---

## Register Summary

47 hypotheses across 11 areas (RA ×5, DP ×4, HI ×4, CP ×4, MG ×4, AI ×5, CM ×4, HP ×4, SR ×4,
DR ×4, IX ×4 substantive + 1 cross-reference). Provisional Wave 1 count: 15 hypotheses — these
are tested first in Phase 2 (see `analysis_plan.md`). No hypothesis here has been tested; no
finding, number, or conclusion in this file should be cited as evidence until it has gone
through Phase 2 testing and been re-scored via the prioritisation framework.

---

## Phase 1 Broad Discovery — Cross-Reference (see `docs/findings_register.md`)

`src/eda_discovery.py` ran a broad descriptive scan across the master dataset
(`outputs/logs/eda_discovery.log`). This is **not** Phase 2 formal hypothesis
testing — no confound model has been fitted for any hypothesis below, and
sample sizes/multiple-comparison corrections vary in rigour by hypothesis.
Treat every status below as a **prior for Phase 2 sequencing**, not a
resolved result. Full detail, effect sizes, and caveats are in
`docs/findings_register.md` (FR-IDs referenced below).

| Hypothesis | Phase 1 status | Evidence | Notes |
|---|---|---|---|
| HP-1 | **Strongly supported** (for HiPo specifically) | FR-01 | Regrettable exit rate 10x higher for HiPo-flagged employees (V=0.151, largest effect in the scan). |
| RA-3 | **Refined, not simply supported** | FR-01 vs. RA-3 context | Performance *rating* alone shows no significant link to voluntary/regrettable exit — the HP-1 signal is specifically about the `hipo_flag`, not current performance rating. Do not conflate the two going into Phase 2. |
| SR-1 | **Strongly supported** | FR-05 | Never-responded population has a 24.5% voluntary exit rate vs. 6.0% for recent responders (V=0.133, second-largest effect in the scan). |
| SR-3 | **Not supported** | FR-15 | The specific responder→non-responder transition adds no signal beyond recent non-response alone. |
| AI-1 | **Resolved toward the culture explanation, not compensation** | FR-04 | Entity_B has the *highest* compa_ratio of any cohort but the *lowest* leadership-trust score; within-Entity_B leaver/stayer pay comparisons show no pay disadvantage for leavers. Full nested-model test still required before this is causal. |
| AI-2 | **Suggestive support** | FR-02 (Entity_A context) | Entity_A shows the lowest attrition of all four cohorts, below even the NovaCorp-Origin baseline — consistent with genuine integration success, but the matched-tenure survivorship check (AI-2's actual design) has not yet been run. |
| CP-1 / CP-4 | **Supported** | FR-06, FR-18 | Stalled high performers (eligible, high-performing, never recommended) leave at 9.6% vs. 5.3% for those recommended (p=0.004). Eligibility alone (FR-18) shows no effect — it's the recommendation that matters. |
| CP-2 | **Strongly supported (Entity_C), supported (Entity_B)** | FR-03 | Entity_C promoted at roughly half the rate of every other cohort at every role level 1-4; performance rating mix is statistically indistinguishable across entities (FR-12), weighing against a merit-based explanation. |
| CM-1 | **Not supported at the univariate, company-wide level** | FR-10 | compa_ratio quartile-within-level shows a flat, non-monotonic relationship with voluntary exit. Full multivariable CM-1 test still warranted before ruling this out entirely. |
| CM-4 | **Untested** | — | Requires the performance × compensation interaction model specified in the hypothesis register; not run in this pass. |
| HI-1 | **Reframed** | FR-09, FR-11 | Agency hires show the *lowest* (not highest) exit rate of any channel — contradicts the hypothesis's original framing. The real early-attrition signal is concentrated in `hire_source == 'acquisition'`, entangled with legacy_entity and post-acquisition timing (FR-09), not agency-vs-direct sourcing. |
| MG-1 | **Supported, magnitude uncertain** | FR-07 | Unadjusted manager-level variance-decomposition proxy ≈ 12% — above the register's own "practically meaningful" threshold, but not yet controlled for department/entity composition as MG-1 specifies. |
| MG-2 | **Likely not supported as stated — probable sparse-count artefact** | FR-07 | The "top decile of managers hold 100% of regrettable exits" figure is very likely explained by a rare outcome spread across many small teams (52% of managers have exactly zero exits), not genuine outlier management. Requires the empirical-Bayes shrinkage approach MG-2 already specifies before any claim is made. |
| MG-3 | **Inconclusive — underpowered** | FR-17 | Directionally consistent (acting managers' teams show lower engagement, acting appointees show higher personal attrition) but n=82/166, neither significant. |
| MG-4 | **Not supported** | FR-16 | No correlation between span of control and either voluntary exit rate or manager effectiveness (Spearman r ≈ −0.01 for both). |
| DP-3 | **Untested** | — | Not run in this pass; requires the engagement→goal_achievement regression DP-3 specifies. |

All other hypotheses (RA-1/2/4/5, DP-1/2/4, HI-2/3/4, CP-3, AI-3/4/5, CM-2/3,
HP-2/3/4, SR-2/4, DR-1/2/3/4, IX-1/2/3/5) were not directly touched by this
broad scan and remain fully open for Phase 2, though several are informed by
the additional context findings in `docs/findings_register.md` Section 2
(e.g. DR-1's "do drivers differ by department" is partially previewed by
FR-02's department-by-department Entity_B breakdown).
