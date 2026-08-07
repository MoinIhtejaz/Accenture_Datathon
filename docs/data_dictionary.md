# Data Dictionary — NovaCorp People Analytics Challenge

Authoritative, field-level reference for `employees.csv`, `attrition_log.csv`,
`engagement.csv`, and `performance.csv`. Every value/range/count below was verified by
running `src/data_audit.py` against the actual files in this project (not assumed from the
brief) — see `outputs/reports/data_quality_report.md` and `outputs/tables/data_quality_issues.csv`
for the full evidence trail, and `docs/decision_log.md` for how each caveat below should be
handled. This document supersedes `CLAUDE.md` Section 5 for field-level detail; `CLAUDE.md`
remains authoritative for business context and standing rules.

Regenerate this file's numbers by re-running `python src/data_audit.py` if the source CSVs
change.

---

## employees.csv — 13,403 rows, 24 columns

Full historical roster (both active and departed employees who were on payroll at any point
1 Jan 2024 – 31 Dec 2025).

| Field | Type (as loaded) | Observed values / range | Missingness | Known caveats |
|---|---|---|---|---|
| `employee_id` | string | `E00001`–`E14500`, all match `E\d{5}` | 0 | **IDs are not contiguous** — max ID (14,500) exceeds row count (13,403). Never infer population size from ID range. Unique, no duplicates, primary key. |
| `name` | string | free text | 0 | Identifier-adjacent; never display in outward-facing analysis (`CLAUDE.md` Section 11). |
| `hire_date` | date | 1988-01-11 to 2025-12-17 | 0 | 10,050 rows (75%) predate the 2024-01-01 observation window — expected, since tenure carries over; not an error. |
| `exit_date` | date | 2024-01-31 to 2025-12-31 (where populated) | 12,003 (89.6%) | **EXPECTED MISSINGNESS** — null count matches active headcount exactly; null means "still active" per the brief's own definition. Never treat as a data gap. |
| `status` | string | `active` (12,003), `departed` (1,400) | 0 | Fully consistent with `exit_date` null pattern and with `attrition_log.csv` membership (0 mismatches found). |
| `department` | string | 7 values: Retail Banking, Technology, Risk & Compliance, Insurance, Wealth Management, Corporate Operations, Executive Leadership | 0 | Matches expected vocabulary exactly; no typos/case variants found. |
| `role_family` | string | 7 values: Operations-Processing, Technology, Client-Advisory, Risk-Compliance, Corporate-Support, Executive, **Management** | 0 | The brief's table cell lists "Management" after a semicolon as a 7th category (applies at L5 and below) — confirmed present in the data as a legitimate distinct category, not a formatting error. |
| `role_level` | int64 | 1–8 | 0 | Median salary is monotonically increasing by level (verified) — level coding is internally consistent. |
| `job_title` | string | free text, paired with role_family/role_level | 0 | Not separately audited for consistency against role_family/role_level; treat as descriptive only. |
| `salary` | float64 | $55,000–$1,206,500 (median $122,700) | 0 | No zero/negative values; no >3×IQR outliers within department×role_level cells. Matches `attrition_log.salary_at_exit` exactly for all departed employees (0 mismatches). |
| `compa_ratio` | float64 | 0.660–1.190 (mean 0.945) | 0 | All values fall within a plausible 0.3–2.5 band (heuristic, no official band table supplied — see limitation below). |
| `gender` | string | Female, Male, Non-binary, Prefer not to say | 0 | **Fairness-audit use only — never an intervention-targeting variable (`CLAUDE.md` Section 11).** |
| `age_band` | string | 18-24 through 60+ in 5-year bands | 0 | Same fairness-only restriction as `gender`. |
| `cultural_background` | string | 11 values (ABS classification: African, Anglo-Australian, East Asian, European (non-Anglo), Latin American, Maori/Aboriginal & Torres Strait Islander, Middle Eastern, Pacific Islander, Prefer not to say, South Asian, Southeast Asian) | 0 | Same fairness-only restriction as `gender`. |
| `contract_type` | string | Full-time (10,435), Part-time (1,599), Fixed-term (689), Casual (680) | 0 | — |
| `hipo_flag` | bool | True/False | 0 | Minority flag — watch small-cell sizes in any segment cross-tab (`CLAUDE.md` Section 12). |
| `promotion_eligible` | bool | True/False | 0 | — |
| `manager_id` | string | references `employee_id` | 1 | **EXPECTED MISSINGNESS** — the single null belongs to the sole `role_level == 8` (CEO) record, i.e. the top of the hierarchy. Zero orphaned references (every non-null `manager_id` resolves to a real employee); zero self-managed rows. |
| `hire_source` | string | agency, direct, referral, graduate, acquisition | 0 | — |
| `legacy_entity_code` | string | Entity_A (1,950), Entity_B (1,884), Entity_C (1,014), NovaCorp-Origin (8,555) | 0 | Maps 1:1 onto `data_source_system` (see cross-file note below) — confirms each acquired entity's records still carry their pre-acquisition system tag. |
| `data_source_system` | string | WorkdayHR (8,555), SAP-HR (1,950), BambooHR-EntityB (1,884), PeopleSoft-Legacy (1,014) | 0 | 1:1 with `legacy_entity_code`: WorkdayHR=NovaCorp-Origin, SAP-HR=Entity_A, BambooHR-EntityB=Entity_B, PeopleSoft-Legacy=Entity_C. **WorkdayHR/NovaCorp-Origin records show a 62.0% tenure-reconciliation mismatch rate vs. 2–4% for the other three systems** (DQ-009) — a system-specific artefact, not evenly spread. |
| `days_to_fill` | float64 | 14–90 days | 0 | No negative values; no values above a 180-day plausibility ceiling. |
| `tenure_months` | int64 | 0–462 | 0 | **ERROR (DQ-001, DQ-009) — do not use at face value.** Does not reconcile with `hire_date` and the documented "to exit_date or window end" definition for 40.6% of records. For active employees, the implied as-of date (back-solved from `hire_date` + `tenure_months`) ranges from Nov 2025 to Jun 2026 rather than clustering at the stated window end of 2025-12-31. Overwhelmingly concentrated in `WorkdayHR`/`NovaCorp-Origin` records. **Recompute tenure directly from `hire_date` and `exit_date`/window-end instead of trusting this column.** 66 rows show `tenure_months == 0` (plausible same-month hire-and-exit; verify per record, don't assume error). |
| `acting_appointment` | bool | True/False, applies at L2–L4 | 0 | Not independently verified against role_level bounds in this audit — treat the "L2-L4 only" scoping as documented, not re-confirmed. |

---

## attrition_log.csv — 1,400 rows, 10 columns

One row per departure during the observation window. Row count exactly matches the number of
`status == 'departed'` records in `employees.csv` (0 employee_id mismatches either direction).

| Field | Type | Observed values / range | Missingness | Known caveats |
|---|---|---|---|---|
| `employee_id` | string | references `employees.csv` | 0 | Zero orphans; zero duplicates (each departed employee appears exactly once). |
| `exit_date` | date | 2024-01-31 to 2025-12-31 | 0 | Identical to `employees.csv.exit_date` for every matched employee (0 mismatches). |
| `exit_type` | string | voluntary (1,133), involuntary (267) | 0 | — |
| `stated_exit_reason` | string | 11 values (Better opportunity, Career advancement, Compensation, Involuntary - conduct, Involuntary - performance, Involuntary - restructure, Personal reasons, Relocation, Role uncertainty / unclear future, Study/career change, Work-life balance) | 0 | **Per the brief, 40–60% of these do not reflect the true primary driver on triangulation — treat as one weak signal, never ground truth (`CLAUDE.md` Section 6).** |
| `notice_period_served` | bool | True/False | 0 | — |
| `regrettable_flag` | bool | True (153), False (1,247) | 0 | **Retrospective HR judgement recorded after the exit — carries hindsight-bias risk (`CLAUDE.md` Section 6). Internal consistency of this label is untested by this audit** (see Hypothesis RA-5 in `hypothesis_register.md`, not yet run). |
| `performance_band_at_exit` | string | Outstanding, High Performer, Meets Expectations, Below Expectations, Unsatisfactory | 0 | Retrospective judgement, same caution as `regrettable_flag`. |
| `salary_at_exit` | float64 | matches `employees.csv.salary` exactly | 0 | 0 mismatches across all 1,400 departed employees — confirmed identical, as the brief states (no intra-window salary adjustments modelled). |
| `manager_id_at_exit` | string | references `employees.csv` | 0 | Zero orphans. |
| `pathway` | string | push (955), pull (445) | 0 | Post-exit HR classification — outcome/descriptive variable only, never a predictive feature (`CLAUDE.md` Section 18). |

---

## engagement.csv — 55,971 rows, 12 columns

Five survey waves. Not every employee has 5 rows — 307 employees (2.3%) have zero rows.

| Field | Type | Observed values / range | Missingness | Known caveats |
|---|---|---|---|---|
| `employee_id` | string | references `employees.csv` | 0 | Zero orphans. 13,096 distinct employees appear at least once (out of 13,403). |
| `wave_number` | int64 | 1–5 | 0 | Per-employee `survey_date` is always non-decreasing in `wave_number` (0 order violations) — safe to sort by either, but see the note on wave 3's rollout window below. |
| `survey_date` | date | 2024-02-23 to 2025-08-08 | 0 | Wave date windows: W1 2024-02-23→03-08 (14d), W2 2024-06-24→07-08 (14d), **W3 2024-09-01→10-31 (60d — 4× wider than the other waves)**, W4 2025-01-25→02-08 (14d), W5 2025-07-25→08-08 (14d). Treat wave 3 as spanning two months, not a single point in time. |
| `response_flag` | bool | True (45,707), False (10,264) | 0 | Non-response rate ~18.3% overall; varies by `legacy_entity_code` (Entity_A/NovaCorp-Origin ~84%, **Entity_B 63.4%, Entity_C 68.6%** — a 20.7-point gap, DQ-006) and only marginally by department/contract_type. 506 employees never respond to any wave they were issued. |
| `manager_effectiveness` | float64 | 1.0–5.0 | 10,264 (18.3%) | **EXPECTED MISSINGNESS** — null count exactly matches `response_flag == False` count; never null when a response was given, never populated when it wasn't (0 violations either direction). Same pattern for all 7 dimensions below. |
| `psychological_safety` | float64 | 1.0–5.0 | 10,264 (18.3%) | As above. |
| `recognition` | float64 | 1.0–5.0 | 10,264 (18.3%) | As above. |
| `career_development` | float64 | 1.0–5.0 | 10,264 (18.3%) | As above. |
| `senior_leadership_trust` | float64 | 1.0–5.0 | 10,264 (18.3%) | As above. |
| `purpose_meaning` | float64 | 1.0–5.0 | 10,264 (18.3%) | As above. |
| `wellbeing` | float64 | 1.0–5.0 | 10,264 (18.3%) | As above. |
| `confidence_in_role_future` | float64 | 1.0–5.0 | 10,264 (18.3%) | As above. |

**Coverage note:** of the 307 employees with zero engagement rows, 139 are fully explained by
being hired after wave 5 closed or exiting at/before wave 1 closed (EXPECTED, per the brief).
The remaining 168 are not explained by hire/exit timing alone — plausibly staggered
within-window survey issuance not recorded at individual level — and are logged as
**UNKNOWN / REQUIRES ASSUMPTION** (DQ-005). Every employee employed across the full wave
1–5 span (n=9,244) has all 5 rows — no unexplained coverage gaps in the fully-eligible
population.

---

## performance.csv — 34,979 rows, 7 columns

Performance reviews. 109 employees (0.8%) have zero review records.

| Field | Type | Observed values / range | Missingness | Known caveats |
|---|---|---|---|---|
| `employee_id` | string | references `employees.csv` | 0 | Zero orphans. 13,294 distinct employees appear at least once. |
| `review_date` | date | 2024-01-30 to 2025-11-09 | 0 | Never after the employee's own `exit_date`, never before `hire_date` (0 violations either direction) — no raw-timestamp temporal leakage found anywhere in this file. |
| `performance_rating` | string | Outstanding (4,207), High Performer (10,069), Meets Expectations (16,072), Below Expectations (3,622), Unsatisfactory (1,009) | 0 | — |
| `review_cycle` | string | 2024-H1 (11,061), 2024-H2 (11,591), 2025-H1 (12,327) | 0 | **2025-H2 is entirely absent — EXPECTED MISSINGNESS, exactly as the brief states** (DQ-008); the most recent review for most employees is 2025-H1 or 2024-H2. **Separately: 32 rows labelled `2024-H1` have a `review_date` falling well outside that half-year (up to ~18 months later), overwhelmingly for employees reviewed within 3 days of `hire_date` who then departed within ~1 month (DQ-007, ERROR). Never use `review_cycle` as a time-ordering proxy — always sequence by `review_date`.** |
| `promotion_recommendation` | bool | True/False | 0 | No independent longitudinal promotion-event field exists in the data; this flag (and its persistence across cycles) is the only available proxy for progression (see the CP-series feasibility caveat in `docs/analysis_plan.md` Phase 0). |
| `goal_achievement_score` | float64 | 0.0–100.0 | 0 | Fully within documented bounds. |
| `reviewer_id` | string | references `employees.csv` | 0 | Zero orphans. |

---

## Cross-File Consistency (verified, all clean unless noted)

| Check | Result |
|---|---|
| `employees.status == 'departed'` ⇔ present in `attrition_log.csv` | 0 mismatches either direction |
| `employees.exit_date` vs `attrition_log.exit_date` (same employee) | 0 mismatches |
| `employees.salary` vs `attrition_log.salary_at_exit` (same employee) | 0 mismatches |
| Any `employee_id` in `attrition_log`/`engagement`/`performance` missing from `employees.csv` | 0 orphans in any file |
| Any `manager_id` / `reviewer_id` / `manager_id_at_exit` missing from `employees.csv` | 0 orphans |
| `data_source_system` ↔ `legacy_entity_code` mapping | Clean 1:1 (each source system belongs to exactly one legacy entity) |
| Voluntary attrition rate reconciliation vs. Annual Report's reported 10.4% | Voluntary exits ÷ active headcount = 9.44%; ÷ (active+departed) = 8.45%. Neither denominator is stated in the brief — treat as directional confirmation only, not a resolved methodology (see `docs/decision_log.md`). |

## Known Limitations of This Dictionary

- `compa_ratio` and salary plausibility bands (0.3–2.5, 3×IQR) are heuristic choices made for
  this audit, not sourced from an official NovaCorp pay-band table (none was supplied).
- The 168 "unexplained" zero-engagement-wave employees (DQ-005) could not be fully resolved
  without per-employee survey-issuance dates, which are not present in the data.
- `job_title` was not cross-validated against `role_family`/`role_level` for internal
  consistency.
- `acting_appointment`'s documented "applies at L2–L4 only" scoping was not independently
  re-verified in this audit.

All figures above are reproducible by running `python src/data_audit.py` from the project
root.
