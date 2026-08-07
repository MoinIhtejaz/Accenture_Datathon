# CLAUDE.md — NovaCorp People Analytics Challenge (Accenture × SUBAA, 2026)

This file is the permanent operating context for this project. It must be read before any
analysis, modelling, or slide-writing work begins. It encodes facts from the official brief and
annual report, explicit warnings from the brief, and standing rules of practice. It does not
contain analysis results — no findings from `employees.csv`, `attrition_log.csv`,
`engagement.csv`, or `performance.csv` have been examined for substance yet. Only schemas
and row counts have been inspected, to write this file.

**File location note:** The brief referred to `reference/...` and `data/...` subfolders. In this
project, all source files currently sit flat in the project root:
- `Accenture Case Comp Brief.pdf` (case brief)
- `NovaCorp_Annual_Report_FY2025.pdf` (annual report)
- `employees.csv`, `attrition_log.csv`, `engagement.csv`, `performance.csv`
- `notes.docx` — team meeting notes found in the directory but not part of the official
  brief/report set. Contains the team's own brainstormed attrition-driver ideas and a
  paraphrased (and slightly different) recollection of judging criteria from the induction
  session. **Treat the official brief (Section 8 below) as authoritative for judging weights.**
  The brainstormed ideas in notes.docx are informal team hypotheses, not management or
  Accenture statements — they are not reproduced here as project facts. Flag to the user if
  it should be formally incorporated.

See Section 17 for the recommended folder structure for outputs going forward.

---

## 1. Competition Objective

Produce the most rigorous, commercially useful, ethical, and persuasive submission to the
Accenture × SUBAA NovaCorp People Analytics Challenge — not the most technically complex
analysis. The deliverable is a decision-support package for a CHRO, not a data science
showcase. Judges explicitly reward reasoning quality and credibility over matching any
predetermined "correct" answer — different teams are expected to reach different conclusions.

## 2. Exact Business Problem

NovaCorp's CHRO has engaged the team to understand and address an **annual people cost
of approximately $42 million**, decomposed by Finance into three components:

| Component | Estimated Range | Description |
|---|---|---|
| Regrettable attrition | ~$22–25M | Replacement cost of high-value voluntary departures |
| Disengagement-driven productivity loss | ~$12–15M | Productivity reduction for persistently disengaged employees |
| Hiring inefficiency | ~$4–6M | Cost premium of agency hiring and poor-match early attrition |

**The task is explicitly NOT to validate the $42M figure.** The task is to:
1. Identify what is driving these costs,
2. Determine which components are most tractable to intervention, and
3. Advise the CHRO and CFO on where to prioritise.

The $42M and its component ranges are Finance's working estimate — a starting point, not a
conclusion, and not to be treated as ground truth to be reverse-fitted.

## 3. Judging Criteria and Weights (authoritative — from official brief, Section 8)

| Dimension | Weight |
|---|---|
| Analytical Rigour & Evidence Quality | 25% |
| Ethics & Responsible Practice | 20% |
| Business Problem Framing | 15% |
| Financial Impact Quantification | 15% |
| Recommendation Actionability | 15% |
| Communication & Narrative Coherence | 10% |

Note: Ethics is 20% of the grade — comparable in weight to rigour. It is not a checkbox.

## 4. Primary Audience

The **CHRO**, who will be physically in the room at the 21 August finals presentation, is the
primary audience — not a data scientist. Every slide, figure, and recommendation must be
calibrated to what a CHRO can act on, not to what is technically interesting to produce. The
CHRO will ask hard, skeptical questions; the CFO is a secondary audience whose main concern
is financial credibility of any quantified claim. Submission format: PDF slide deck, ≤15 core
slides (unlimited appendix), written for a non-technical HR leader.

## 5. Dataset Descriptions

All four files join on `employee_id`. Observation window: **1 January 2024 – 31 December
2025** (two years). Verified against the actual files in this project (not just the brief) —
row counts and category distributions below are confirmed, not assumed.

### employees.csv (13,403 rows — confirmed)
Full historical roster: **both active (12,003) and departed (1,400) employees** who were on
payroll at any point in the window. Active count matches the FY2025 Annual Report's "12,003
active employees" figure exactly; departed count matches `attrition_log.csv` row count exactly
— the files are internally consistent.

Fields: `employee_id`, `name`, `hire_date`, `exit_date` (null if active), `status`
(active/departed), `department` (7 divisions), `role_family` (Operations-Processing,
Technology, Client-Advisory, Risk-Compliance, Corporate-Support, Executive), `role_level`
(1–8, 1=Entry/Frontline IC, 8=CEO), `job_title`, `acting_appointment` (applies L2–L4),
`salary` (base only, excludes super/bonus/equity), `compa_ratio` (salary ÷ role-level band
midpoint), `gender` (Female/Male/Non-binary/Prefer not to say), `age_band` (5-year brackets),
`cultural_background` (ABS classification), `contract_type` (Full-time/Part-time/Fixed-
term/Casual), `hipo_flag`, `promotion_eligible`, `manager_id`, `hire_source`
(agency/direct/referral/graduate/acquisition), `legacy_entity_code`
(NovaCorp-Origin/Entity_A/Entity_B/Entity_C), `data_source_system`, `days_to_fill`,
`tenure_months` (to window end or exit, calendar-month basis).

**Confirmed distributions:** legacy_entity_code — NovaCorp-Origin 8,555, Entity_A 1,950,
Entity_B 1,884, Entity_C 1,014. Department headcounts in this file are cumulative across the
2-year window (both active+departed) and will NOT match the Annual Report's "as at 30 June
2025" active-only snapshot table directly — active-only subsets must be filtered before
comparing to Annual Report figures.

**Explicit brief warning:** because the file mixes active and departed populations, the
correct population depends on the question being asked, and that choice must be reasoned
through and documented before analysis (see Section 18 on leakage/population choice).

### attrition_log.csv (1,400 rows — confirmed)
All departures during the window. Fields: `employee_id`, `exit_date`, `exit_type`
(voluntary 1,133 / involuntary 267 — confirmed), `stated_exit_reason`, `notice_period_served`,
`regrettable_flag` (True 153 / False 1,247 — confirmed), `performance_band_at_exit`,
`salary_at_exit` (identical to `employees.csv.salary` — no intra-window salary adjustments are
modelled), `manager_id_at_exit`, `pathway` (push 955 / pull 445 — confirmed; push = involuntary
or managed exit, pull = employee-initiated/opportunity-driven).

**Explicit brief warnings:**
- `stated_exit_reason` is an exit-interview field HR records at the time of exit. The brief
  states research consistently shows **40–60% of exit-interview reasons do not reflect the
  true primary driver** when triangulated against longitudinal engagement data. Treat as one
  weak signal, never as ground truth.
- `regrettable_flag`, `performance_band_at_exit`, and `stated_exit_reason` are all
  **retrospective judgements recorded by HR after the departure event** — they carry hindsight
  bias and possible motivated reasoning (e.g., a manager may retrospectively down-rate an
  employee they wanted to exit). Use with explicit caution, and never as an unqualified
  predictive-model label without acknowledging this (see Section 18).

### engagement.csv (55,971 rows — confirmed)
Five survey waves per employee (where applicable). Fields: `employee_id`, `wave_number` (1–5),
`survey_date`, `response_flag` (True 45,707 / False 10,264 — confirmed non-response),
`manager_effectiveness`, `psychological_safety`, `recognition`, `career_development`,
`senior_leadership_trust`, `purpose_meaning`, `wellbeing`, `confidence_in_role_future` (all
1–5 scale, null when `response_flag` is False).

**Explicit brief warning:** rows where `response_flag` is False are **intentional inclusions**
representing employees issued the survey who did not respond. Non-response itself may be
signal (e.g., correlated with disengagement or attrition risk) — do not silently drop these
rows without first considering what non-response patterns might indicate.

### performance.csv (34,979 rows — confirmed)
Fields: `employee_id`, `review_date`, `performance_rating` (Outstanding 4,207 / High Performer
10,069 / Meets Expectations 16,072 / Below Expectations 3,622 / Unsatisfactory 1,009 —
confirmed), `review_cycle` (2024-H1, 2024-H2, 2025-H1 — confirmed; **2025-H2 is absent from
the data**), `promotion_recommendation`, `goal_achievement_score` (0–100), `reviewer_id`.

**Explicit brief warning:** the 2025-H2 cycle (normally run Nov–Dec) is not in the dataset —
the most recent review for most employees is 2025-H1 or 2024-H2. Any analysis relating
"most recent performance" to attrition in late 2025 must account for this right-truncation.

## 6. Important Warnings Stated Directly in the Brief (do not lose these)

- The $42M figure is a starting point, not something to validate or reverse-engineer support for.
- Exit-interview reasons are unreliable 40–60% of the time — triangulate, don't trust at face value.
- `regrettable_flag`, `performance_band_at_exit`, `stated_exit_reason` are post-hoc HR judgements — handle with care, especially in modelling.
- `employees.csv` mixes active and departed populations — population choice must be justified per question.
- Non-response in `engagement.csv` is intentional and may itself be informative.
- The 2025-H2 performance cycle is missing entirely.
- Data reflects genuine enterprise HRIS messiness (multiple legacy platforms from 3 acquisitions): incomplete fields, migration artefacts, format inconsistencies. Data-cleaning decisions are a graded analytical step, not invisible preprocessing — document every inclusion/exclusion/imputation decision and why.
- Datasets are generated with fixed parameters. **Do not attempt to reverse-engineer the generation process** to extract information not obtainable through standard analysis.
- Cross-referencing across all four files is expected; single-file findings are weaker evidence.
- There is no single correct answer — different teams reaching different conclusions is expected and not penalised. Judged on reasoning quality and evidentiary rigour.
- Explicitly stating limitations is rewarded, not penalised — decks that omit limitations will face harder Q&A scrutiny, not less.
- No mentor support during the challenge window; this is by design and part of what's assessed.

## 7. Finance Assumptions Supplied by NovaCorp (use exactly as given; do not silently alter)

| Assumption | Value |
|---|---|
| Replacement cost multiplier | 1.5× annual base salary |
| Backfill rate | 85% of vacated positions filled |
| Disengagement productivity loss | 15% of base salary per year |
| Superannuation on-cost | 12.0% of base salary (legislated rate effective 1 July 2025) |
| Agency fee rate | 18% of first-year base salary |
| Direct hire benchmark | $5,500 per hire (fully loaded) |

Additional financial context from the Annual Report (FY2025 actuals, for framing/materiality
only — not attrition-cost assumptions):
- Total revenue $4,420M; NPAT $689M; Operating profit $1,375M; personnel expenses $1,750M
  (39.6% of revenue).
- Personnel expense note: $128K average base salary is **active-employee-only**; the $1,750M
  personnel line includes on-costs and partial-year costs for the 1,400 departed employees —
  these two figures are not directly comparable without adjustment.
- Voluntary attrition (company-reported) 10.4% FY2025, down from 10.9% FY2024, both above the
  9.5% internal benchmark/target.
- Acquisition integration costs: $67M FY2025 (down from $92M FY2024).
- FY2026 guidance: voluntary attrition target below 9.5%; NPAT $760–820M; cost-to-income below 67%.

Any dollar figure the team produces must show its arithmetic against these constants
transparently (see Section 14).

## 8. Relevant Strategic Priorities from the Annual Report

Four strategic pillars (FY2027 horizon):
1. **Organic Revenue Growth** — 6–8% CAGR target.
2. **Integration & Operational Scale** — complete 3-cohort acquisition integration by Q2
   FY2026; $85M run-rate cost synergies by FY2027; single core banking platform.
3. **Digital & Technology Transformation** — 75% of retail transactions digital by FY2026;
   $320M multi-year infrastructure investment.
4. **Workforce Capability & Culture** — build a high-performance, engaged workforce as
   competitive advantage; **resolve voluntary attrition below 9.5% by FY2026**; 40% female
   representation at Level 5+ by FY2027 (currently 34.1%, up from 31.8%).

Other named priorities: Risk & Compliance talent stabilisation (FAR-driven, Director/L4
focus); Entity_B integration completion by Q2 FY2026 (systems migration + cultural alignment,
core banking platform consolidation targeted December 2025); an unspecified, thrice-repeated
"People Reinvention Programme" with budget set aside but no defined scope, metrics, or
timeline disclosed anywhere in the report.

## 9. Important Hypotheses Suggested by Management — LABELLED AS HYPOTHESES, NOT FACTS

These are claims and framings from NovaCorp's CEO letter and Workforce section. They are
management's *narrative*, not verified findings, and **must be independently tested against
the raw data**, not assumed true:

- **H-Mgmt-1:** "Entity_A has reached full operational integration and its attrition profile
  has normalised to below the Group average" (7.5% vs 10.4% group avg) — framed by
  management as evidence of *successful integration*. Alternative explanations (survivorship
  bias among long-tenured Entity_A stayers, role/seniority mix, time-since-acquisition
  confound) have not been ruled out and should be tested.
- **H-Mgmt-2:** Entity_B's elevated attrition (15.0%, ~47% above NovaCorp-Origin) is framed by
  management as a temporary *integration stabilisation* effect, expected to "normalise to
  Group-average levels within 12 months of programme completion" (Q2 FY2026). This is a
  forward-looking management assertion, not a demonstrated causal mechanism.
  Cultural/systems friction is one plausible driver among several (compensation gaps,
  role redundancy, management-quality differences) that the data should be used to
  discriminate between.
- **H-Mgmt-3:** Elevated Risk & Compliance attrition (11.8% vs 10.4% avg) is attributed by
  management primarily to FAR-driven external competition for senior regulatory talent,
  concentrated at Director (L4) level. This is management's causal attribution and should be
  tested against compensation, workload, engagement, and tenure signals in the data rather
  than accepted as the explanation.
- **H-Mgmt-4:** Management distinguishes "regrettable" attrition from attrition that
  "reflects the structural reshaping of our workforce post-acquisition," implying the latter
  is less concerning. This framing should not be adopted uncritically — `regrettable_flag` is
  itself an HR post-hoc judgement (Section 6) and management has an incentive to characterise
  attrition favourably.
- **H-Mgmt-5:** The "People Reinvention Programme" is asserted three times as a funded
  initiative but is never scoped. Its existence should be treated as a *strategic intent
  signal* only — it cannot be used as evidence that any specific intervention is already
  planned or funded at a specific level.

**Standing rule:** Never force the analysis to match NovaCorp management's existing
narrative. The Annual Report contains management observations that must be independently
tested against the raw data. If the data contradicts a management hypothesis above, report
the contradiction — that is a more valuable finding for the CHRO than confirmation.

## 10. Analytical Principles

- Explore broadly across all four datasets before committing to a narrative; then narrow to
  the 1–2 strongest, best-evidenced, most decision-relevant storylines. Breadth of exploration
  should be evident in appendix/methodology, not in the core 15 slides.
- Every claim in the final deck must survive: **So what? How large? How certain? How much
  money? Is it actionable? Is it ethical? What decision should the CHRO make?** (see repeated
  standing instruction at the end of this file).
- Prefer triangulated findings (evidenced across ≥2 of the 4 files) over single-file findings.
- Prefer explaining variance in outcomes NovaCorp already cares about (voluntary attrition,
  regrettable attrition, disengagement, hiring cost) over exploring for its own sake.
- A "preventable" or "regrettable" attrition definition is not given and must be constructed
  by the team — but any custom definition must be explicit, justified against the data, and
  distinguished from HR's own `regrettable_flag`.
- External market/industry context may be used to strengthen interpretation, but internal
  NovaCorp data must remain the primary evidentiary basis for all quantified claims.

## 11. Ethics Rules

- **Never use protected characteristics — gender, cultural background, age (age_band) — as
  intervention targeting variables.** They may be used only for fairness auditing and
  understanding structural disparities (e.g., "are women underrepresented in promotion
  pipelines," "does attrition risk differ by cultural background after controlling for
  role/tenure"), never to decide who receives a retention offer, coaching, or other
  intervention.
- Never present individual-level or small-cell results in a way that could identify a named
  employee or a small, identifiable group. Aggregate and suppress small cells.
- Treat `name`, `manager_id`, `reviewer_id` as identifiers to be used for joins/network
  structure only, never displayed in outward-facing analysis or slides.
- Be alert to the manager-as-confound problem: a manager relationship exists in the data
  (`manager_id`, `reviewer_id`) — poor manager quality can drive both low engagement scores
  and high attrition. Do not let this collapse into a "blame the employee" framing.
  Recommendations should default to structural/systemic levers before individual-blame framing.
  Ethics is 20% of the score — weight this proportionally in review time.
- Flag any variable that is a statistical proxy for a protected characteristic (e.g., certain
  role families, hire sources, or tenure bands may correlate with age or cultural background)
  before using it as a segmentation or intervention-targeting variable.
- Empathy check: every recommendation involving people (not just costs) should be evaluated
  for downside employee impact, not only NovaCorp's financial benefit.

## 12. Statistical Standards

- Report effect sizes and confidence intervals/uncertainty ranges, not just point estimates
  or p-values. A statistically significant but tiny effect is not automatically a business
  priority.
- Correct for multiple comparisons when scanning many variables/segments for "significant"
  differences (the temptation to mine 7 departments × 8 role levels × multiple engagement
  dimensions for something significant is high — guard against it explicitly).
- Distinguish population-level description (e.g., "Entity_B attrition is 15.0%") from
  inferential claims about drivers (e.g., "X explains Entity_B's elevated attrition") — the
  former is descriptive statistics, the latter requires a modelling/inferential argument.
  See Section 21.
- For survival/tenure-type questions, remember `tenure_months` for active employees is
  right-censored (they haven't left yet) — treat this correctly (e.g., survival analysis or
  explicit censoring-aware framing), don't treat censored tenure as if it were a completed
  spell.
- Document sample sizes for every segment-level claim; be explicit when a subgroup (e.g.,
  Executive Leadership, n=230 employees total) is too small for a reliable estimate.
- Missing data (non-response in engagement, incomplete performance cycles, HRIS migration
  gaps) must be handled with a stated, defensible method — document whether data are
  plausibly missing-at-random or not, and what that implies for any conclusion drawn.

## 13. ML Standards (if predictive modelling is used)

- Any predictive model (e.g., attrition risk) must have a clearly stated **prediction
  target, prediction cutoff time, and feature set restricted to information available before
  that cutoff.** See Section 18 for leakage-specific rules.
- Favour interpretable models (logistic regression, simple trees/GBMs with SHAP) over
  black-box models the team cannot explain to a CHRO in plain language — communicability to a
  non-technical audience is a submission requirement, not optional polish.
- Report model performance with a train/validation split that respects time ordering
  (do not randomly shuffle across the two-year window if the model is meant to predict future
  attrition from past signals).
- Report fairness diagnostics (e.g., false-negative/false-positive rates by gender, cultural
  background, age band) for any model whose output could plausibly influence a people
  decision — even though these variables must never be model *inputs* used for targeting
  (Section 11).
- A model is a decision-support tool for the CHRO, not the deliverable itself — every model
  output must be translated into a business recommendation with a dollar and headcount
  estimate.

## 14. Financial Modelling Standards

- Every cost estimate must show its formula and the exact Finance-supplied constants used
  (Section 7) — no unexplained dollar figures.
- Distinguish **replacement cost** (1.5× salary, applied to the 85% backfill-rate share of
  regrettable voluntary departures), **disengagement productivity loss** (15% of base salary/
  year, applied to a defined "persistently disengaged" population — definition must be stated
  and justified), and **hiring inefficiency** (agency fee 18% of first-year salary vs $5,500
  direct-hire benchmark, applied to the relevant hire population) as separate, non-overlapping
  calculations, matching Finance's three-component decomposition.
- State clearly which employees are included in each calculation's denominator/population and
  why (e.g., is "regrettable attrition" all `regrettable_flag=True` records, or a team-defined
  alternative — and if alternative, why it's superior, per Section 10).
- Sensitivity-test key assumptions (e.g., what changes if backfill rate or the "persistently
  disengaged" threshold is varied) rather than presenting a single point estimate as certain.
- Recommendations should include an estimated financial impact of *acting* on them (the brief
  states judges will directly ask "what happens if NovaCorp acts on your recommendation?") —
  quantify in $, %, or headcount wherever the evidence supports it, and say explicitly when it
  cannot be quantified rather than fabricating a number.

## 15. Storytelling Standards

- Structure: **Problem → Evidence → Why it matters → Root cause → Recommendation → Impact.**
- ≤15 core slides, appendix unlimited — core slides carry the argument, appendix carries the
  proof/robustness checks a skeptical CHRO or judge might ask for.
- Every slide should pass the "so what" test — if a slide doesn't change what the CHRO should
  do, cut it or move it to appendix.
- Lead with the business decision, not the analytical method. Methods belong in appendix or a
  brief methodology note, not centre-stage.
- Use plain-language framing throughout — the audience is an HR leader, not a data scientist.
- Explicitly narrate limitations in the main narrative (not buried in fine print) — this is
  rewarded, not penalised, per the brief.

## 16. Required Documentation

For every analytical decision, maintain a running, versioned record (see Section 17 for
location) covering:
- Which employee population was used for a given analysis and why (active only / departed
  only / both) — mandatory given the brief's explicit warning (Section 6).
- Every data-cleaning, exclusion, or imputation decision, with rationale.
- Any custom definition created by the team (e.g., "preventable attrition," "persistently
  disengaged") — definition, justification, and how it differs from any HR-provided flag.
- All formulas used for financial estimates, with the exact constants from Section 7.
- All statistical tests run, including ones that did not yield a usable finding (to
  demonstrate breadth of exploration and guard against implicit p-hacking/cherry-picking).
- Model specification, feature set, cutoff time, and validation approach for any predictive
  model.
- A limitations log: what the analysis cannot conclude, and why.

## 17. Folder / Output Conventions

Recommended structure for all work going forward (source files currently remain flat in the
project root — see the file location note at the top of this document):

```
/data/                # raw source CSVs (as provided, untouched)
/reference/           # case brief PDF, annual report PDF
/notebooks_or_scripts/ # analysis code, one file/notebook per major analytical question
/outputs/
    /figures/         # exported charts used in the deck
    /tables/          # exported summary tables
/docs/
    decisions_log.md  # the running documentation required in Section 16
    limitations.md
/deck/                # slide deck source + exported PDF for submission
```

Raw source files should never be edited in place; all cleaning happens in code with the
transformation documented, so the pipeline from raw CSV to final slide number is reproducible
end to end (Section 20).

## 18. Rules Preventing Data Leakage

- **Population leakage:** `employees.csv` contains both active and departed employees. Any
  model or comparison that implicitly conditions on future knowledge of who departed (e.g.,
  using `tenure_months` computed relative to exit date as a feature to predict exit) is
  leaking the outcome into the feature set. Be explicit about the prediction cutoff and only
  use information known as of that cutoff.
- **Post-outcome fields as predictors:** `attrition_log.csv` fields — `regrettable_flag`,
  `performance_band_at_exit`, `stated_exit_reason`, `pathway`, `notice_period_served`,
  `salary_at_exit`, `manager_id_at_exit` — are all recorded at or after the exit event. **None
  of these may be used as predictors of whether/when someone will leave.** They may be used as
  outcome variables or for post-hoc descriptive segmentation of people who already left, never
  as inputs to a forward-looking risk model.
- **Engagement timing leakage:** when relating engagement survey waves to attrition, use only
  waves completed *before* the relevant exit date (or before the prediction cutoff) for that
  employee — do not use a wave 5 (later) survey response to "explain" an exit that occurred
  before wave 5 was fielded.
- **Performance timing leakage:** the 2025-H2 cycle is absent (Section 5); do not construct
  any feature that implicitly assumes visibility into performance data beyond 2025-H1 for
  events in late 2025.
- **Survivorship bias:** analyses of "what successful integration looks like" using only
  currently-active Entity_A employees exclude everyone from that cohort who already left —
  document this bias explicitly whenever population choice could induce it.

## 19. Rules Preventing Causal Overclaiming

- This is observational HR data, not an experiment. No randomisation, no natural experiment
  has been established. Default posture: **findings are associations until an explicit,
  justified causal design (e.g., a credible natural experiment, a validated instrument, a
  documented policy change with clean pre/post comparison and controls for confounds) is
  presented.**
- Never use causal language ("X causes Y," "X drives Y," "reducing X will reduce Y by Z%")
  for a bivariate or lightly-controlled association. Use "associated with," "consistent
  with," "correlated with," or "co-occurs with" instead, and reserve causal language only
  when the analysis explicitly earns it (e.g., addresses confounding, considers reverse
  causality, and states the identification assumption).
- Explicitly consider reverse causality wherever plausible — e.g., declining engagement
  scores could be a *symptom* of an employee who has already decided to leave (anticipatory
  disengagement), not solely a cause of the eventual departure.
- Explicitly consider omitted-variable confounds before attributing a driver — e.g., manager
  quality, role family, compensation, and legacy-entity cohort may all move together and
  confound a naive bivariate relationship.
- Any recommendation predicated on a causal claim must state the causal assumption being made
  and its risk of being wrong, so the CHRO can weigh that risk explicitly.

## 20. Rules for Reproducibility

- All analysis must be code-driven (not manual spreadsheet edits) so it can be re-run
  end-to-end from the raw CSVs to the final numbers/charts in the deck.
- Every number that appears in the final deck must be traceable to a specific script/notebook
  cell and a specific, documented data-population and formula choice.
- Random seeds must be fixed and recorded for any stochastic step (e.g., train/test splits,
  bootstrapped confidence intervals).
- Package/library versions used should be noted if they materially affect results (e.g.,
  specific statistical test implementations).
- Do not hand-adjust any output figure after generation; if a figure looks wrong, fix the
  code/data-handling step that produced it and regenerate.

## 21. Distinguishing Observed Fact / Statistical Evidence / Inference / Hypothesis / Recommendation

Every important claim in analysis notes and in the final deck must be labelled (explicitly or
by clearly separated section) as one of the following, and must not be upgraded to a stronger
category than the evidence supports:

- **Observed fact** — a direct tabulation from the data with no modelling or interpretation
  (e.g., "Entity_B voluntary attrition in the dataset is 15.0% over the observation window").
- **Statistical evidence** — a tested relationship with a stated method, effect size, and
  uncertainty measure (e.g., "employees in the bottom quartile of psychological_safety at
  their most recent survey wave have X percentage-points higher subsequent voluntary
  attrition, 95% CI [a,b], n=...").
- **Inference** — a reasoned interpretation that goes beyond the raw statistical result but is
  still tightly evidence-bound (e.g., "this pattern is consistent with unresolved cultural
  friction in the Entity_B cohort, though role-mix differences have not been fully ruled
  out").
- **Hypothesis** — an untested or only partially tested explanatory idea, including anything
  sourced from management's narrative (Section 9) or the team's own brainstorming, clearly
  flagged as unproven (e.g., "H: the Entity_B effect may be driven by compensation-band
  mismatches inherited at acquisition — not yet tested against compa_ratio data").
- **Recommendation** — an action proposed for the CHRO, explicitly built on top of the above,
  with its own stated confidence level and financial estimate (Section 14), never presented as
  though it were itself an observed fact.

Any slide or written analysis that blurs these categories (e.g., stating a hypothesis in the
same sentence structure as an observed fact) should be rewritten before it goes further.

---

## Standing Permanent Instructions (apply to all future work in this project)

- **Never force the analysis to match NovaCorp management's existing narrative.** The Annual
  Report contains management observations (Section 9) that must be independently tested
  against the raw data.
- **Never invent results. Never make up numbers.** If a number cannot be computed from the
  provided data with a documented method, say so explicitly rather than estimating silently.
- **Never present an association as causal without suitable evidence** (Section 19).
- **Never use protected characteristics — gender, cultural background, or age — as
  intervention-targeting variables.** They may be used for fairness auditing and understanding
  structural disparities only (Section 11).

**For every important finding, always ask:**
1. SO WHAT?
2. HOW LARGE?
3. HOW CERTAIN?
4. HOW MUCH MONEY?
5. IS IT ACTIONABLE?
6. IS IT ETHICAL?
7. WHAT DECISION SHOULD THE CHRO MAKE?

A finding that cannot answer most of these should not make it into the core 15-slide deck.
