# Findings 01 — Profile of the 153 flagged regrettable leavers

Scope: `attrition_log.regrettable_flag == True`, n = 153 of 1,400 exits. All 153 are voluntary.
Window 1 Jan 2024 – 31 Dec 2025. Joined to employees.csv, engagement.csv, performance.csv on employee_id (0 unmatched).

---

## 1. The single strongest pattern: HiPo underpayment

| Group | n | mean compa-ratio |
|---|---|---|
| Regrettable leavers, HiPo | 76 | 0.868 |
| Regrettable leavers, non-HiPo | 77 | 0.965 |
| **Active staff, HiPo** | **1,029** | **0.879** |
| Active staff, non-HiPo | 10,974 | 0.952 |

HiPos are 9% of the workforce but **50% of regrettable leavers** (index 5.5×).

Of the 76 HiPo regrettable leavers, 72 were paid below 0.95 compa and 30 below 0.85. Only 4 were at or above market.

**The critical nuance — do not skip this on the slide.** Leaving HiPos (0.868) are paid almost identically to staying HiPos (0.879). So underpayment does **not** by itself separate leavers from stayers. What the data actually shows is structural: NovaCorp pays HiPos ~7pp below market and everyone else at market, and the gap is uniform across all seven departments (0.875–0.888 vs 0.951–0.954). That uniformity means it is a pay-architecture artefact, not local manager discretion.

Read it as an **exposure** finding rather than a trigger: 879 active HiPos sit below 0.95 compa, 306 below 0.85. That is the standing at-risk population, and it is a lever the CHRO can actually pull.

## 2. A 30-day integration cliff in the acquired entities

174 of 1,400 exits occurred at **≤45 days tenure, median exactly 30 days**. Of those, 155 were `hire_source = acquisition` (89 Entity_B, 66 Entity_C). 24 were flagged regrettable.

Onboarding waves are visible in hire_date: Entity_B May–Sep 2024 (1,884 people), Entity_C Apr–Jun 2025 (1,014 people).

| Cohort | Onboarded | Exited | Rate |
|---|---|---|---|
| Entity_B (2024 wave) | 1,884 | 283 | 15.0% |
| Entity_C (2025 wave) | 1,014 | 94 | 9.3% |

A median of exactly 30 days is too clean to be organic. Two readings, and the deck should state which one is being used:

- **Behavioural:** a retention-payment or notice cliff at one month post-integration.
- **Data integrity:** `hire_date` for acquired staff is the system-migration date, not true hire date, so their real tenure is unknown and every tenure-based statistic on acquisition hires is wrong.

Either way this contaminates any tenure variable. Flag it, treat acquisition hires separately.

## 3. `performance_band_at_exit` is not evidence

Cross-tabulating HR's `performance_band_at_exit` against each person's actual last performance review before exit:

- **Exact agreement: 15.7%** for regrettable leavers (27.7% across all 1,400 exits) — no better than chance.
- HR labelled 128 of 153 as Outstanding or High Performer. The review record supports **67**.
- Of the 97 labelled "Outstanding", only 8 actually held an Outstanding rating. 47 were "Meets Expectations" and 7 were "Below Expectations".
- Every one of the 153 had at least one review on file, so this is not a missing-data problem.

Mean goal-achievement at last review was 68.7 vs an all-staff mean of 66.9 — a real but small edge, nowhere near the "we lost our best people" story the flag implies.

**Consequence:** `regrettable_flag` and `performance_band_at_exit` are HR narrative. Any $ figure built on them inherits the error. This is the basis for challenging the brief's $22–25M rather than accepting it.

## 4. Engagement surveys did not see these people coming

Aligning surveys to event time (months before each person's exit), responders only:

| Months to exit | n | manager_eff | psych_safety | recognition | career_dev | wellbeing |
|---|---|---|---|---|---|---|
| 12–18m | 48 | 3.24 | 3.04 | 3.04 | 3.03 | 3.04 |
| 6–9m | 54 | 3.37 | 3.47 | 3.33 | 3.49 | 3.49 |
| 3–6m | 61 | 3.09 | 3.36 | 3.27 | 3.22 | 3.25 |
| **0–3m** | **66** | **3.35** | **3.44** | **3.42** | **3.42** | **3.49** |

Scores in the final quarter before exit are at or above the company average. There is no engagement collapse.

Within-person change (last survey vs that person's first, n=78 with ≥2 responses), only one dimension moves:

| Dimension | mean delta | % declining |
|---|---|---|
| manager_effectiveness | **−0.201** | 59% |
| recognition | −0.048 | 53% |
| senior_leadership_trust | −0.043 | 53% |
| career_development | +0.072 | 49% |

**Non-response is the better signal.** Regrettable leavers respond at 71–77% per wave vs 80–84% for everyone else, and their response rate falls to 62.5% at 18–24 months out. The people who left stopped answering rather than answering badly — which is exactly why `response_flag = False` rows cannot be dropped.

## 5. No manager or team concentration

All 153 regrettable exits had **153 distinct managers**. Across all 1,400 exits the maximum any single manager lost was 3, and only 19 managers lost 3 or more (1,196 distinct managers).

There is no toxic-pocket story here. A manager-quality intervention cannot be justified from this slice, despite manager_effectiveness being the only declining survey dimension. Those two facts sit in tension and should be presented as such.

## 6. Stated reasons vs behaviour

| Stated reason | n |
|---|---|
| Career advancement | 82 |
| Better opportunity | 61 |
| Everything else (relocation, WLB, personal, role uncertainty) | 9 |
| **Compensation** | **1** |

Pathway: 118 pull / 35 push. So 93% state a pull reason and exactly one person in 153 cites pay — while sitting at a median compa-ratio of 0.88.

This is the brief's "40–60% of exit reasons are wrong" warning showing up in the data. It also means: **the intervention the exit interviews imply (more career pathways) is not the intervention the pay data implies.** Worth a slide on its own.

Supporting: only 20% of regrettable leavers had ever received a promotion recommendation, vs 32% of all staff. For HiPo leavers it was 26%. So the career-advancement complaint is corroborated — these people genuinely were not being put forward.

## 7. Secondary firmographics

Over-represented vs workforce share (index = leaver share ÷ workforce share):

- Role level 3 — index 1.73 (senior managers); role level 4 — 1.57
- Risk & Compliance — 1.44; Corporate Operations — 1.44
- Tenure <1yr — 2.88 (but see §2, contaminated by the acquisition cliff)
- Management role family — 1.37

Under-represented: Retail Banking (0.61), tenure 2–3yr (0.20).

Flat / no signal: gender, contract type, hire source, days_to_fill, salary level in absolute terms. Cultural-background indices range 0.32–1.53 on cell sizes of 1–21 — **too thin to interpret, and an ethics landmine. Do not put it on a slide** without a much larger denominator.

---

## Caveats

1. n = 153 is thin. Any cut past two dimensions produces cells under 10.
2. Everything here is conditioned on `regrettable_flag`, which §3 shows is unreliable. These are patterns in *what HR called regrettable*, not in *regrettable attrition*.
3. No stayer comparison in §§6–7, so "over-represented" is descriptive only — it is not evidence of causation.
4. 2025-H2 review cycle is absent by design; 33 regrettable leavers exited after 30 Jun 2025 and have no review covering their final months.

## What this points to next

- Rebuild the regrettable population from observable facts (voluntary + HiPo or rated High/Outstanding + tenure), and re-cost it. Expect a number materially different from $22–25M.
- Treat the 30-day acquisition cliff as its own cost line — it likely sits in *hiring inefficiency*, not regrettable attrition, and 174 exits is a bigger volume than the entire regrettable population.
- Size the HiPo pay-gap remediation: 879 active HiPos below 0.95 compa, cost to close vs replacement cost avoided.
