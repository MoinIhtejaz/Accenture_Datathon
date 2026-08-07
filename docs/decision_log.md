# Data Quality Decision Log

Companion to `outputs/reports/data_quality_report.md` and
`outputs/tables/data_quality_issues.csv`. Required by `CLAUDE.md` Section 16 (documentation
of every cleaning/exclusion/imputation decision) and Section 20 (reproducibility).

**Status convention:** every decision below is **PROPOSED** — a recommendation with stated
reasoning, not an action taken. Per the explicit instruction governing this audit, **no
cleaning has been performed**. This log is what a cleaning step would execute against, once
separately approved. Each entry will be updated to `IMPLEMENTED` (with the commit/script
reference) or `REJECTED` (with why) only when that later step actually happens.

Format per decision: the issue(s) it responds to, the question that needs an answer, the
options considered, the recommendation, and the reasoning — so a reviewer can disagree with
the recommendation without having to redo the investigation.

---

## DEC-001 — How to handle `tenure_months` (responds to DQ-001, DQ-002, DQ-009)

**Question:** Can the supplied `tenure_months` column be used as-is anywhere in the analysis?

**Options considered:**
1. Use `tenure_months` as supplied everywhere (status quo).
2. Recompute tenure from `hire_date` and (`exit_date` or a fixed window-end) as a new derived
   column, and use that instead everywhere tenure matters.
3. Use `tenure_months` as supplied only for NovaCorp-Origin/WorkdayHR-independent purposes
   (e.g. coarse tenure banding where a few months of error doesn't matter) and recompute only
   where precision matters.

**Recommendation:** Option 2 — recompute tenure directly from `hire_date` and
(`exit_date`, or 2025-12-31 capped, for active employees) as a new derived field
(`tenure_months_recomputed`), and use that consistently everywhere in Phase 0 onward. Do not
delete or overwrite the original `tenure_months` column — retain it alongside, so the
discrepancy remains auditable rather than silently disappearing.

**Reasoning:** The stored value fails to reconcile with its own documented definition for
40.6% of records (DQ-001), and the failure is heavily concentrated in one source system
(WorkdayHR/NovaCorp-Origin, 62.0% mismatch vs. 2–4% elsewhere — DQ-009), consistent with a
system-specific export/computation issue rather than random noise. Using it at face value
would systematically distort any tenure-banded comparison, survival analysis, or
early-attrition cutoff specifically for the NovaCorp-Origin cohort (8,555 of 13,403
employees) — the opposite of a random error, which would at least average out. Recomputing
from the two underlying date fields (which passed every integrity check in this audit) is
lower-risk than trying to "correct" the stored value with an unknown formula.

**Caveat carried forward:** the 66 records with `tenure_months == 0` are plausible genuine
same-month hire-and-exit cases (DQ-002, BUSINESS SIGNAL) — recomputation should preserve
these as legitimately near-zero, not treat them as errors to exclude.

**Owner / next step:** Whoever builds the Phase 0 `cohort_time_variables` table
(`docs/analysis_plan.md` Section 5) implements the recomputation and documents the exact
formula used.

---

## DEC-002 — How to handle the 32 mislabelled `review_cycle` records (responds to DQ-007)

**Question:** Can `review_cycle` be trusted as a time-ordering / period label anywhere?

**Options considered:**
1. Trust `review_cycle` as given everywhere (status quo).
2. Never use `review_cycle` for time-ordering; always sort/filter by `review_date` instead,
   using `review_cycle` only as a coarse, non-authoritative label.
3. Re-derive a corrected `review_cycle` label from `review_date` for all 34,979 rows and
   replace the stored value.

**Recommendation:** Option 2. Do not relabel the column (Option 3) — that would be a cleaning
action taken without being asked, and the 32 affected rows are a small enough share (0.09%)
that avoiding the string entirely is simpler and safer than trying to re-derive it correctly
for every row.

**Reasoning:** The affected rows are concentrated among employees reviewed within 3 days of
`hire_date` who then departed within about a month — consistent with a day-1
onboarding/baseline review that a source system defaulted to the first cycle label rather
than computing the true period. Because `review_date` itself is clean (0 rows violate
hire/exit bounds — see DEC-004), there is no need to trust the label at all: any hypothesis
in `hypothesis_register.md` that needs "most recent review before date X" should filter on
`review_date <= X` directly, never on `review_cycle`. This is the audit's single most
important finding for the standing "never use information recorded after exit" rule, because
trusting the label (rather than the date) could silently pull a much-later review into an
analysis window that believed it was looking only at early-2024 information.

**Owner / next step:** Anyone writing a Phase 2 hypothesis test involving `performance.csv`
must filter by `review_date`, never `review_cycle`, and this rule should be called out in
code review / peer check.

---

## DEC-003 — Denominator for "regrettable attrition" costing (responds to brief's own warning, cross-referenced by RA-3/RA-5)

**Question:** Should the $22–25M "regrettable attrition" cost component be built on HR's own
`regrettable_flag` (n=153 voluntary exits), or an alternative team-defined population?

**Options considered:**
1. Use `regrettable_flag == True` as given.
2. Build an alternative definition (e.g. voluntary exits above a performance/seniority
   threshold) and use it instead of HR's flag.
3. Report both, with HR's flag as the primary/anchor number and any alternative as a
   sensitivity check.

**Recommendation:** Option 3 — defer the final choice to Phase 2 (hypotheses RA-3 and RA-5
in `hypothesis_register.md` test whether `regrettable_flag` correlates with objective
performance signals and whether it is manager-idiosyncratic). This audit does not resolve
the question; it only confirms `regrettable_flag` is internally well-formed (no missing
values, only two clean boolean states, 153/1,133 = 13.5% of voluntary exits flagged).

**Reasoning:** `CLAUDE.md` Section 6 explicitly flags `regrettable_flag` as a retrospective
HR judgement with hindsight-bias risk. A data-quality audit can confirm the field is
*well-formed*; it cannot and should not adjudicate whether it is *well-founded* — that is a
Phase 2 analytical question, not a Phase 0 cleaning question. Recording that distinction here
prevents this audit from silently pre-deciding a hypothesis-register question.

**Owner / next step:** Phase 2, hypotheses RA-3/RA-5.

---

## DEC-004 — No action needed: raw temporal-leakage checks (responds to Section 13.2 of the report)

**Question:** Is any cleaning or exclusion needed to prevent post-exit information leaking
into pre-exit analysis?

**Finding:** Zero violations found — no `engagement.survey_date` or `performance.review_date`
in the data exceeds its own employee's `exit_date`, and none precedes `hire_date`. Zero
per-employee wave-order violations (a later `wave_number` never has an earlier `survey_date`
than an earlier wave for the same person).

**Decision:** No cleaning action required for raw timestamps. The only temporal-correctness
risk in this data is the categorical one addressed in DEC-002 (review_cycle labels), which is
a *usage* rule (always sort by date, not label), not a row to exclude or a value to fix.

**Reasoning documented for completeness:** Given `CLAUDE.md`'s standing rule against using
post-exit information, this was checked directly and exhaustively rather than assumed clean
from the file design description. Recording the zero result here (not just in the report)
ensures a future contributor doesn't feel obliged to re-derive it before trusting the
dataset's temporal ordering.

---

## DEC-005 — Response-rate gap by legacy entity: analytical caveat, not a data error (responds to DQ-006)

**Question:** Does the ~21-point engagement survey response-rate gap between Entity_B/C
(63–69%) and Entity_A/NovaCorp-Origin (~84%) require any correction before use?

**Options considered:**
1. Ignore the gap and compare raw respondent-mean engagement scores across cohorts.
2. Explicitly weight or adjust for differential response propensity when comparing cohorts.
3. Report response rates alongside any cross-cohort engagement comparison, and flag
   comparisons as descriptive-only where the gap is large.

**Recommendation:** Option 3 for Phase 1/2 generally, with Option 2 (an explicit
non-response-adjustment or a dedicated test, per hypothesis SR-2/SR-4 in the hypothesis
register) required before any headline claim compares Entity_B/C engagement to
NovaCorp-Origin engagement.

**Reasoning:** This is not a data error — every row is well-formed (0 response_flag/score
inconsistencies) — but a large, non-random response-rate differential is a classic source of
non-response bias: if the type of person who stays silent differs systematically between
cohorts (plausible during an unsettled post-acquisition period), naive respondent-only
averages are not comparable across cohorts. Classified BUSINESS SIGNAL, not ERROR, because
the pattern itself may be analytically meaningful (Area SR in the hypothesis register) rather
than something to fix.

**Owner / next step:** Phase 2, hypotheses SR-1/SR-2/SR-4, and any AI-series (acquisition
integration) hypothesis that compares engagement across `legacy_entity_code`.

---

## DEC-006 — Residual unexplained zero-engagement-wave employees (responds to DQ-005)

**Question:** Can the 168 employees with zero engagement rows (not explained by hire-after-
wave-5 or exit-before-wave-1 timing) be safely treated as missing-at-random?

**Options considered:**
1. Assume missing-at-random and exclude silently from engagement-based analysis.
2. Flag explicitly wherever engagement-history-conditioned analysis is performed, without
   assuming a mechanism.
3. Investigate further (e.g. request per-employee survey-issuance dates from a hypothetical
   real HR system) — not possible here, as this is a fixed synthetic dataset.

**Recommendation:** Option 2. Carry this as a documented, explicit limitation in any Phase 2
analysis that conditions on engagement history (e.g. RA-2, SR-1, SR-3, IX-3 in the hypothesis
register), rather than silently excluding these 168 employees as if their absence were
guaranteed random.

**Reasoning:** All 168 are departed employees whose exit falls close to a wave's rollout
window (which spans up to 14–60 days, not a single day), consistent with staggered
per-employee survey administration that simply never reached them before they left — a
plausible benign mechanism, but not one this audit can *confirm* without individual
issuance-date data that does not exist in the files provided. `CLAUDE.md` Section 12 requires
documenting, not guessing, the missingness mechanism when it matters for a conclusion.

**Owner / next step:** Whoever runs RA-2/SR-1/SR-3/IX-3 in Phase 2 must state this as an
explicit limitation when interpreting results for early-window departures.

---

## DEC-007 — Salary/compa_ratio outlier plausibility bands are heuristic (responds to Section 5/9.1 of the report)

**Question:** Should the 0.3–2.5 `compa_ratio` band and 3×IQR salary-outlier rule used in
this audit be adopted as the project's standing definition of "implausible pay"?

**Recommendation:** No — treat both as **audit-stage screening thresholds only**, chosen to
be wide enough to avoid false alarms without an official NovaCorp pay-band table (none was
supplied in the brief). They found zero violations in this dataset, which is itself useful
(salary/compa_ratio data is clean by these generous standards) but should not be read as "no
outliers exist by any reasonable definition." If Phase 2/3 work (e.g. CM-series hypotheses)
needs a tighter, more defensible pay-equity threshold, it should set one explicitly for that
purpose and document it separately from this audit.

**Reasoning:** Per `CLAUDE.md` Section 12, any threshold choice must be stated and justified,
not silently assumed. Recording that this one is a screening convenience, not a business
definition, prevents it from being cited later as if NovaCorp had supplied it.

---

## Open Questions Not Resolved by This Audit

These require a human decision before Phase 0 proceeds, and are listed here rather than
silently defaulted:

1. **Voluntary attrition rate denominator** (Section 15 of the report): neither
   voluntary-exits÷active-headcount (9.44%) nor voluntary-exits÷(active+departed) (8.45%)
   exactly reproduces the Annual Report's stated 10.4%. The brief does not disclose Finance's
   exact denominator. Recommend documenting both reconciliation attempts transparently in any
   external-facing material rather than picking one and presenting it as "the" NovaCorp
   methodology.
2. **CP-series (career progression) feasibility**: confirmed in this audit that no
   longitudinal level-change event field exists — `role_level` is a single current-state
   snapshot. `docs/analysis_plan.md` Phase 0 already flags this; this log confirms the
   underlying data fact the flag depends on.
3. **`job_title` internal consistency**: not cross-validated against `role_family`/
   `role_level` in this audit; flag for a future pass if `job_title` is ever used as an
   analytical variable rather than a display field.
