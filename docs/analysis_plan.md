# Analysis Plan — NovaCorp $42M People Cost Investigation

Governing document: `CLAUDE.md` (read first, always). Companion document:
`hypothesis_register.md` (the full hypothesis tree this plan sequences and scores).

## 0. Philosophy

**Explore broadly → validate rigorously → present narrowly.**

- *Explore broadly:* the hypothesis register covers 11 areas and 47 pre-committed hypotheses,
  deliberately wider than what will ever appear in a 15-slide deck, so that narrowing later is
  a defensible editorial choice rather than an artefact of what we happened to look at first.
- *Validate rigorously:* every hypothesis carries a stated method, confounders, leakage risks,
  and pre-specified support/reject evidence *before* it is tested — this is the project's own
  pre-registration discipline, meant to prevent the search for a story from masquerading as a
  search for the truth.
- *Present narrowly:* the final deck carries only the 1–2 storylines that survive validation
  and score highest on the prioritisation framework in Section 8 below — everything else
  (including hypotheses that were tested and rejected) moves to appendix as evidence of
  breadth, per `CLAUDE.md` Section 10 and the brief's own instruction that limitations and
  explored-but-rejected paths are rewarded, not penalised.

**This document does not select a storyline.** No hypothesis has been tested yet. Storyline
selection happens only in Phase 4/5, after evidence exists to score.

## 1. What This Plan Covers

1. Six investigation phases (0–6), from data foundations to deck construction.
2. Reusable population definitions (P1–P8), used consistently across every hypothesis so that
   population choice is decided once, deliberately, and documented — not re-litigated
   ad hoc per analysis (directly addressing `CLAUDE.md` Section 6's explicit warning about
   `employees.csv` mixing active and departed employees).
3. Reusable derived variables to be built once in Phase 0 and reused across many hypotheses,
   for consistency and efficiency.
4. Statistical rigour safeguards (multiple-comparison control, minimum sample sizes,
   pre-specification discipline).
5. The prioritisation framework (7 criteria) requested for scoring **tested findings** — not
   raw hypotheses — in Phase 4.

## 2. Investigation Phases

### Phase 0 — Population & Variable Foundations (no hypothesis testing yet)
Build once, reuse everywhere:
- The eight reusable populations (P1–P8, Section 4).
- The reusable derived-variable tables (Section 5).
- A feasibility check on CP-series hypotheses specifically: confirm whether any form of
  level-change / promotion-event can actually be observed longitudinally in `employees.csv`
  (a single-snapshot `role_level` field cannot, by itself, reveal historical promotions) —
  if not, CP-1/CP-2/CP-4 must be re-scoped in the register to rely on
  `promotion_recommendation` persistence/repetition as an explicit proxy, with that
  limitation stated up front rather than discovered mid-analysis.
- A data-quality pass: missingness map per field per file, `data_source_system` consistency
  check (do compa_ratio/role_level definitions look comparable across legacy HRIS exports?),
  and a documented decision log entry for every cleaning choice (`CLAUDE.md` Section 16).
- Output: a single, versioned analysis dataset (or a small number of joined views) that every
  later phase reads from, so every number in the final deck traces back to one pipeline
  (`CLAUDE.md` Section 20).

### Phase 1 — Broad Descriptive Scan
Univariate and bivariate description across all four files: distributions, missingness,
obvious outliers, rate tables by department/level/entity/gender(fairness-only)/tenure. No
inferential claims yet — this phase exists to sanity-check Phase 0's foundations and to
surface anything the hypothesis register did not anticipate (if something material turns up,
it is added to the register as a new, labelled hypothesis before being tested — not tested
ad hoc).

### Phase 2 — Hypothesis-Driven Testing
Work through `hypothesis_register.md` in wave order (Wave 1 → 2 → 3), applying each
hypothesis's pre-specified method exactly as written. For each:
- Record the result using `CLAUDE.md` Section 21's fact/evidence/inference/hypothesis
  vocabulary — a tested hypothesis becomes either "statistical evidence" (with effect size +
  CI) or "not supported," never silently upgraded to "inference" or "recommendation" in the
  same breath.
- Apply the multiple-comparison and sample-size safeguards in Section 7 below as each test is
  run, not retrospectively.
- Log every test run — including null results — in the decision log (`CLAUDE.md` Section 16),
  so the eventual deck's "we explored broadly" claim is auditable, not asserted.

### Phase 3 — Financial Quantification
Apply `CLAUDE.md` Section 14 methodology only to hypotheses that survived Phase 2 with
adequate evidence strength. Every dollar figure shows its formula, its Section-7 constants,
its population/denominator, and a sensitivity range. No financial estimate is built on an
untested or rejected hypothesis.

### Phase 4 — Prioritisation & Cross-Validation
Score each *tested finding* (not raw hypothesis) using the 7-criterion framework in Section 8.
Run robustness checks on the top-scoring candidates specifically (subgroup stability,
sensitivity to definitional choices, triangulation across ≥2 datasets per `CLAUDE.md`
Section 10). This phase produces a ranked shortlist, not a final decision.

### Phase 5 — Storyline Selection (explicitly out of scope for this document)
Narrow the Phase 4 shortlist to the 1–2 storylines the deck will carry, informed by the
prioritisation scores but also by narrative coherence and CHRO actionability as a final human
judgement call. **Not performed here.**

### Phase 6 — Deck Construction
Apply `CLAUDE.md` Sections 15–16: Problem → Evidence → Why it matters → Root cause →
Recommendation → Impact structure, ≤15 core slides, full methodology and rejected-hypothesis
summary in appendix.

## 3. Traceability to Management Hypotheses

For visibility, the register's acquisition-integration hypotheses map directly onto
`CLAUDE.md` Section 9's management hypotheses, so their resolution explicitly confirms or
contradicts the Annual Report's narrative rather than quietly sidestepping it:

| CLAUDE.md hypothesis | Tested by |
|---|---|
| H-Mgmt-1 (Entity_A integration success) | AI-2 |
| H-Mgmt-2 (Entity_B temporary stabilisation) | AI-1, AI-3, AI-4 |
| H-Mgmt-3 (Risk & Compliance / FAR talent competition) | AI-5, DR-3 |
| H-Mgmt-4 (regrettable vs. structural reshaping framing) | RA-3, RA-5 |
| H-Mgmt-5 (People Reinvention Programme) | Not independently testable with current data — remains a strategic-intent signal only; flag as a limitation if the final deck references it. |

## 4. Reusable Population Definitions

| Code | Definition | Source | n (confirmed) | Primary use |
|---|---|---|---|---|
| P1 | Active workforce as of window end | `employees.csv`, `status`=='active' | 12,003 | Current-state description, fairness composition, structural denominators |
| P2 | All exits during window (voluntary + involuntary) | `employees.csv` `status`=='departed'; = all of `attrition_log.csv` | 1,400 | Contrast population; involuntary-vs-voluntary framing |
| P3 | Voluntary exits only | `attrition_log.csv`, `exit_type`=='voluntary' | 1,133 | Primary population for "why do people choose to leave" |
| P4 | Involuntary exits only | `attrition_log.csv`, `exit_type`=='involuntary' | 267 | Control/contrast group; explicitly excluded from regrettable-attrition costing |
| P5 | HR-flagged regrettable voluntary exits | `attrition_log.csv`, `exit_type`=='voluntary' AND `regrettable_flag`==True | 153 | HR's own definition of the $22–25M cost population; benchmark for any team-alternative definition |
| P6 | Full historical roster | `employees.csv`, all rows | 13,403 | Survival/hazard analysis with explicit right-censoring for active records |
| P7 | Survey-eligible population per wave | `engagement.csv`, employees issued that wave (respondents + non-respondents) | ~10,000–12,000/wave (varies) | Response-rate and non-response analysis (Area 9) |
| P8 | HiPo / promotion-eligible subsets | `employees.csv`, `hipo_flag`==True and/or `promotion_eligible`==True | To be sized in Phase 0 | Areas 4 and 8 |
| P1+P2 | "At risk during the window" — active-at-any-point union | Union of P1 and P2 | 13,403 (== P6) | Rate denominators for any attrition-rate calculation (numerator from P2/P3/P4/P5, denominator from here, segmented identically) |

**Standing rule:** every hypothesis in the register states which of these it uses. If a
Phase 2 analysis needs a population not listed here, it must be added to this table with the
same rigor before use, not defined inline and forgotten.

## 5. Reusable Derived Variables (built once in Phase 0)

- **`engagement_wide`** — one row per employee: per-wave value and `response_flag` for each of
  the 7 dimensions; wave-over-wave deltas; a composite engagement index (documented
  construction method); last-observed-value-before-a-given-cutoff; response-pattern
  classification (always-responds / always-dark / went-dark / resumed, per SR-3);
  non-response count and rate.
- **`performance_summary`** — most recent pre-cutoff `performance_rating` and
  `goal_achievement_score`; rating trajectory (ordinally coded, improving/flat/declining);
  `promotion_recommendation` history/count; explicit flag for employees whose most recent
  available review predates the missing 2025-H2 cycle by more than one cycle (right-truncation
  flag, per `CLAUDE.md` Section 18).
- **`manager_rollup`** — per `manager_id`: span of control (direct-report count); team-average
  engagement per dimension; team voluntary-attrition rate; team-average performance; share of
  team under an acting/interim manager; the manager's *own* engagement/performance as rated by
  their manager (a manager-quality proxy, used only in aggregate per `CLAUDE.md` Section 11).
- **`compensation_benchmark`** — `compa_ratio` distribution by department × role_level ×
  legacy_entity_code; below-band flag (threshold to be set and sensitivity-tested, not fixed
  arbitrarily); a tenure–compa_ratio slope per department × role_level cell (compression/
  inversion indicator, per CM-2).
- **`cohort_time_variables`** — tenure_months bucket; hire-year; an approximate
  quarters-since-acquisition value for Entity_A/B/C cohorts, built from the Annual Report's
  stated acquisition periods (Entity_A≈FY2022, Entity_B≈FY2023, Entity_C≈late FY2024) —
  **explicitly documented as a cohort-level approximation, not a per-employee acquisition
  date**, since no such field exists in the data.
- **`exit_funnel_variables`** — for P2/P3 employees only: last engagement wave completed before
  `exit_date`; engagement trend in the waves preceding exit; whether the employee was a
  non-respondent in their final available wave before exit. Built once, reused by RA-2, SR-1,
  and IX-3.

All five outputs are code-generated, versioned, and documented per `CLAUDE.md` Section 20 —
no manual editing of any derived table.

## 6. Hypothesis Tree Overview

Full detail lives in `hypothesis_register.md`. Summary by area and provisional Wave-1 count:

| Area | Code | Hypotheses | Wave 1 |
|---|---|---|---|
| Regrettable attrition | RA | 5 | RA-1, RA-2, RA-3 |
| Disengagement / productivity loss | DP | 4 | DP-1, DP-2, DP-3 |
| Hiring inefficiency | HI | 4 | HI-1 |
| Career progression / promotion friction | CP | 4 | — (all Wave 2/3, gated on Phase 0 feasibility check) |
| Manager effects | MG | 4 | MG-1 |
| Acquisition integration | AI | 5 | AI-1, AI-2 |
| Compensation positioning | CM | 4 | CM-1, CM-3 (ethics-mandated), CM-4 |
| High performer / HiPo retention | HP | 4 | HP-1 |
| Survey non-response behaviour | SR | 4 | SR-1 |
| Department/role-specific problems | DR | 4 | DR-4 |
| Interactions | IX | 5 (4 substantive + 1 cross-ref) | — (all gated on other Waves) |

15 Wave-1 hypotheses total. Wave 1 is chosen to front-load: (a) hypotheses that validate the
core cost-model assumptions themselves (DP-3, HP-1, RA-3), (b) the single most consequential
management-narrative test (AI-1), (c) the ethics-mandated fairness audit (CM-3), and (d) cheap,
high-information foundational cuts (RA-1, DR-4, MG-1) that many later hypotheses depend on.

## 7. Statistical Rigour Safeguards

- **Pre-specification:** the register fixes each hypothesis's method and support/reject
  criteria before testing (done). Deviating from a pre-specified method during Phase 2
  requires a documented reason in the decision log, not a silent change.
- **Multiple-comparison control:** within any family of related tests run in the same pass
  (e.g., 7 engagement dimensions in DP-3/AI-4/HP-3, or a department × level grid in RA-1/DR-1),
  apply Benjamini–Hochberg FDR correction and report corrected q-values alongside raw p-values.
- **Minimum sample size:** no segment-level rate or effect is reported as a standalone
  headline finding below n=30 per compared group; smaller cells are reported only in
  aggregate or explicitly labelled "indicative, underpowered" (`CLAUDE.md` Section 12).
- **Effect size over significance:** every reported test pairs a p/q-value with an effect
  size and confidence interval; a significant-but-trivial effect does not advance past
  Phase 2 into Phase 3 costing.
- **Leakage discipline:** every hypothesis's stated leakage risk (register field) is checked
  off explicitly in Phase 2, not assumed handled by using the "right" dataset alone.
- **Reverse-causality and confound check:** for every hypothesis with a plausible reverse-
  causal story (flagged throughout the register, e.g., RA-2, DP-3), the write-up must state
  why the observed direction is still the more likely one, or concede it cannot be
  established (`CLAUDE.md` Section 19) — associational language only unless this is done.

## 8. Prioritisation Framework

This framework scores **tested findings** in Phase 4 — it is not applied to untested
hypotheses, since two of its seven criteria (Evidence Strength, Novelty) cannot be honestly
scored before a result exists. No hypothesis in the register has been scored yet; the wave
tiers in Section 6 and in `hypothesis_register.md` are a separate, qualitative *sequencing*
judgement, not a priority score.

### 8.1 Criteria, Weights, and Anchors

Weights are set to mirror the competition's own judging rubric (`CLAUDE.md` Section 3), so
that a high-scoring finding under this framework is, by construction, a finding the judges are
likely to reward.

| # | Criterion | Weight | 1 (low) | 3 (medium) | 5 (high) |
|---|---|---|---|---|---|
| 1 | Evidence Strength | 25% | Single-source, uncontrolled, small n | One robustness check passed, moderate n, some confounds addressed | Triangulated across ≥2 datasets, confound-controlled, adequate n, survives sensitivity checks |
| 2 | Ethical Defensibility | 20% | Relies on protected-characteristic targeting, individual-identifiable, or ungated manager-blame framing | Passes core Section 11 rules but needs careful framing | Clean, structural, transparent about fairness implications, no targeting risk |
| 3 | Business Value | 15% | Tangential to any named NovaCorp metric | Plausibly relevant to a cost component | Directly moves a named KPI (voluntary attrition rate, a $42M component, a named strategic target) |
| 4 | Financial Materiality | 15% | Negligible (<$0.5M or <2% of a cost component, per Section 14 costing) | Moderate ($0.5–2M, or a clearly-scoped subset) | Large (>$2M or >10% of a component), computed with a stated formula and sensitivity range |
| 5 | Tractability | 15% | Not actionable within NovaCorp's control (e.g., macro rate cycle) | Actionable but slow/expensive (large structural change) | Directly actionable HR lever, deployable within 6–12 months, plausible budget |
| 6 | Strategic Relevance | 5% | Unconnected to any named FY2026/FY2027 priority | Loosely related | Directly addresses a named strategic pillar or management concern (Section 8/9) |
| 7 | Novelty | 5% | Restates management's existing narrative with no new evidence | Adds a modest refinement to a known narrative | Surfaces a materially new insight, or a data-backed contradiction of management's narrative |

**Hard gate:** any finding scoring 1 on Ethical Defensibility is excluded from the deck
regardless of composite score — this is a gate, not merely a 20%-weighted input, consistent
with `CLAUDE.md` Section 11 being a standing rule rather than a trade-off variable. Novelty is
deliberately the lowest-weighted criterion, reflecting the brief's own statement that the goal
is not technical cleverness (`CLAUDE.md` Section 1) — here, "novel" means "new decision-
relevant information," not "sophisticated method."

### 8.2 Composite Score

```
Composite = 0.25×Evidence + 0.20×Ethics + 0.15×BusinessValue + 0.15×FinancialMateriality
          + 0.15×Tractability + 0.05×StrategicRelevance + 0.05×Novelty
```
Scale: 1–5 per criterion → composite range 1.0–5.0. Findings with Ethics = 1 are excluded
before ranking, irrespective of composite.

### 8.3 Scoring Template (to be populated in Phase 4 — currently empty by design)

| Finding ID | One-line result | Evidence (25%) | Ethics (20%) | Business Value (15%) | Financial Materiality (15%) | Tractability (15%) | Strategic Relevance (5%) | Novelty (5%) | Composite | Gate passed? |
|---|---|---|---|---|---|---|---|---|---|---|
| *(populated in Phase 4, one row per tested finding)* | | | | | | | | | | |

## 9. Explicit Stop Condition

This plan, and the accompanying hypothesis register, define **what will be tested and how** —
they do not contain results, scores, or a storyline. Per `CLAUDE.md`'s standing rule against
inventing results, no placeholder numbers, illustrative statistics, or example scores have
been included anywhere in this plan or the register. Phase 0 begins only on separate
instruction.

## 10. Immediate Next Step (not started)

Phase 0: build the P1–P8 population views and the five reusable derived-variable tables listed
in Section 5, run the CP-series feasibility check, and produce the Phase 0 data-quality/
decision-log entries — before any hypothesis in Section 6's Wave 1 is tested.
