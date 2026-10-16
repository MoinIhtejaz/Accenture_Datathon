# Findings 06: the retention thesis

Scripts: `helper_code/thesis_chain.py`, `targeting_rules.py`, `charts_thesis.py`,
`verify_thesis.py`
Figures: `charts_thesis/t01` to `t08`

## The argument in one paragraph

NovaCorp already knows who its most valuable people are. It flags 1,210 of them as high
potential, and those 1,210 resign at half again the rate of everyone else, carrying roughly $25M
of replacement cost with them. NovaCorp also already collects the warning: people who stop
answering the engagement survey are about twice as likely to be gone before the next one. The
warning arrives a year early and is currently filed as missing data. The recommendation is to
connect the two. When a HiPo goes quiet, someone senior has a proper conversation with them
inside 30 days, and pay position decides who gets called first.

## The chain, stated so it can be attacked

See `t01_causal_chain.png`.

| Link | Claim | Test | Result | Verdict |
|---|---|---|---|---|
| L1 | HiPos resign more | Fisher exact, n = 13,403 | OR 1.63 [1.36 to 1.95], p = 5.5 x 10⁻⁷ | holds |
| L2 | Their exits carry the regrettable cost | Fisher exact | OR 10.5 [7.6 to 14.6], p = 4 x 10⁻³⁹ | holds |
| L3 | Pay position separates painful losses from routine ones | Welch t, within leavers | 0.868 vs 0.900, p = 0.003 | holds, but not as a cause |
| L4 | Silence flags them early | Discrete-time risk set, 55,939 person-waves | OR 1.85 [1.23 to 2.77], p = 0.005 | holds, with a caveat |

Three links carry the argument. L3 is drawn as a modifier hanging off the side rather than a step
in the chain, and the reason is in section 3. Get that distinction wrong in the room and the whole
thing unravels.

## L1: HiPos resign more

151 of 1,210 HiPos resigned over the two-year window, against 982 of 12,193 everyone else. That is
12.5% against 8.1%, a rate ratio of 1.55 and an odds ratio of 1.63.

The obvious objection is that HiPos are concentrated somewhere else that explains it: a young
cohort, a hot department, a pay band. They are not. Put tenure, compa-ratio, role level,
department, hire source and contract type into a logistic model and the HiPo coefficient barely
moves, adjusted OR 1.58 [1.30 to 1.93], p = 5.0 x 10⁻⁶.

Being flagged high potential is not a proxy for something else. It is its own risk factor.

## L2: those resignations are where the money is

See `t02_where_the_cost_sits.png`.

HiPos are 9.0% of headcount and 49.7% of everyone HR flagged as a regrettable loss. That is a 5.5
times enrichment, odds ratio 10.5, p = 4 x 10⁻³⁹. Half the regrettable-attrition problem sits
inside one twelfth of the workforce.

The money follows. The 151 HiPos who resigned were carrying $19.6M of base salary between them.
At the brief's finance benchmarks, 1.5 times base to replace and an 85% backfill rate, that is
$24.9M over two years, or about $12.5M a year. The CFO has booked $22 to $25M for regrettable
attrition. This one cohort accounts for essentially all of it.

That is what makes the targeting defensible. You are not proposing to boil the ocean. You are
proposing to watch 9% of the workforce because that 9% is where the entire line item lives.

## L3: pay tells you how much it hurts, not who is leaving

See `t03_pay_severity.png`. This is the section to read twice.

Among the 151 HiPos who resigned, the ones HR flagged as regrettable were paid meaningfully below
the ones it did not: compa-ratio 0.868 against 0.900, Welch t = -2.99, p = 0.003, Hedges g = -0.49.
It survives controls for role level, department and tenure (beta = -0.030, p = 0.008). Put a
practical line at compa 0.90 and the split is stark: HiPos below it who resign get flagged
regrettable 61% of the time, against 39% for those at or above.

Now the part that has to be said out loud, because a judge will find it in ninety seconds if you
do not.

**Compa-ratio does not predict whether a HiPo resigns.** Leavers average 0.884, stayers 0.879,
p = 0.38. There is no pay effect on the decision to leave. And when we added a pay filter to the
trigger rule, the rule got worse, not better: hit rate dropped from 3.80% to 2.12% and the
association stopped being significant (p = 0.39). See `t05_trigger_choice.png`.

So what is compa-ratio actually doing? Two readings, and the deck should offer both:

The generous reading is that underpaid HiPos are the best value in the building, so losing one
genuinely hurts more, and HR's flag is tracking something real about the cost of the loss.

The sceptical reading is that `regrettable_flag` is a retrospective HR judgement, and pay is one
of the things HR looks at when making it. findings_04 already showed the flag tracks performance
band almost tautologically. This is the second contaminant.

Either way the operational conclusion is identical, and it is the useful one: **compa-ratio is a
triage variable, not a trigger.** It sets the order of the queue and hints at what to put on the
table in the conversation. It never decides who gets the call.

## L4: silence, and the test that could have killed it

See `t04_silence_falsification.png`.

Design first, because the design is the argument. Every survey wave, take everyone still employed
on the survey date, record whether they answered, then ask whether they resigned before the next
survey actually happened. That last part matters: the boundary is the real next wave date, not a
made-up day count, so nobody is credited with foresight they could not have had. 55,939
person-waves, five waves, and every row carries the same exposure.

Across all staff, 1.34% of responders resigned before the next wave against 3.07% of
non-responders. Odds ratio 2.33 [2.03 to 2.68], p = 2.4 x 10⁻³⁰. In the HiPo subgroup it is 2.09%
against 3.80%, OR 1.85, p = 0.005.

It holds in every wave separately, at odds ratios between 1.71 and 2.73, all five clearing a
Bonferroni-corrected threshold of 0.01. It holds at every look-ahead from 30 days to 545. And it
holds when you throw out every survey taken within 90 days of an exit, so it is not just people on
notice ignoring HR: silence 90 to 365 days ahead of the exit still gives OR 2.07.

**Then the test that should have killed it.** If silence were really a resignation signal, it
should not predict getting fired. It does. Silence predicts involuntary exit at OR 2.18,
p = 1.4 x 10⁻⁷, statistically indistinguishable from its effect on resignations.

Silence is a disengagement marker, not a resignation marker. Say this on the slide rather than
waiting to be asked. It does not weaken the recommendation, it widens it: the same conversation
that retains someone who was drifting toward the door also catches someone drifting toward a
performance problem. Both cost NovaCorp money.

## The intervention

See `t06_funnel.png` and `t08_operating_model.png`.

The rule: when a HiPo does not respond to a survey wave, an HR business partner runs a structured
1:1 within 30 days. Priority order inside the queue is set by compa-ratio, furthest below 0.90
first.

The numbers behind it:

| | |
|---|---|
| HiPo person-waves in scope | 4,904 |
| Triggered (HiPo and silent) | 894, about 447 a year |
| Hit rate inside the triggered group | 3.80% against a 2.41% HiPo base |
| Lift | 1.58x over the HiPo base, 2.3x over the company base |
| Share of HiPo resignations reached | 28.8% |
| Conversations per resignation found | 26 |
| Caseload | roughly 14 a week across the HR team |

Nobody should pretend 3.8% is a good hit rate. It is not. Resignation is a rare event and no rule
will hand HR a list where most people are about to quit. The case does not rest on precision. It
rests on the asymmetry: a structured conversation costs a few hundred dollars and a HiPo
replacement costs $165,194.

### What the conversation is for

The four files contain nothing about workload, pay expectations, career intentions or personal
circumstances. That is not a gap in the analysis, it is the reason the intervention is a
conversation rather than another dashboard. The agenda writes itself from what the data cannot
see: is the workload survivable, is the pay position understood and defensible, is there a path
they can name, is something happening at home, do they have the tools and training for what
changed in their job this year. Pay comes up first for anyone sitting below 0.90 because those are
the people whose loss HR later regrets most.

### Why a tiered version is better than a flat one

Testing the alternatives changed the recommendation, which is the point of testing them. See
`t05_trigger_choice.png`.

Silence twice running is a much sharper signal than silence once: 5.2% hit rate against 3.1%
company-wide, and the lowest break-even of any rule at 5.8%. Silence once can be a holiday.
Silence twice is a pattern. So:

- Tier 1, silent once: automated manager check-in, logged, no HR time. 5,126 a year. This tier
  exists mainly so Tier 3 is detectable, since you cannot spot two consecutive silences without
  registering the first.
- Tier 2, HiPo and silent: structured 1:1 with an HR business partner inside 30 days. 447 a year.
- Tier 3, anyone silent two waves running: mandatory retention conversation with a named owner and
  a 30-day follow-up. 766 a year.

Adding "passed over for promotion at the last review" holds the hit rate steady at 4.06% while
cutting Tier 2's caseload by a third. Worth keeping as a tie-breaker.

## What it costs and what it has to achieve

See `t07_breakeven.png`.

Assume a structured 1:1 plus follow-up costs $500 of loaded HR time. Tier 2 is 447 conversations,
so $223,500 a year. Sitting inside that flagged group are about 17 resignations a year, each
costing $165,194 to replace.

**The programme breaks even if it prevents 8.0% of the resignations in the flagged group. That is
1.4 people a year out of 17.**

| Prevention rate | Cost avoided | Net | ROI |
|---|---|---|---|
| 5% | $0.14M | -$0.08M | negative |
| 10% | $0.28M | +$0.06M | 0.3x |
| 20% | $0.56M | +$0.34M | 1.5x |
| 30% | $0.84M | +$0.62M | 2.8x |

Sensitivity on the one assumption that is genuinely ours to make up:

| Cost per conversation | Break-even prevention rate |
|---|---|
| $250 | 4.0% |
| $500 | 8.0% |
| $1,000 | 15.9% |
| $2,000 | 31.8% |

Even at $2,000 a conversation the bar is under a third. Present this as a hurdle rate, not a
forecast. Nothing in the data establishes what the real prevention rate would be, and any team
that claims otherwise is making it up.

## The five things a judge will push on

1. **"Silence predicts being fired too, so this is not a retention signal."** Correct, and it is
   on our own slide. It is a disengagement signal. That makes the conversation more useful, not
   less, because the same intervention addresses both outcomes.

2. **"Non-response is not exogenous."** Also correct. Someone who has mentally checked out ignores
   the survey, so we cannot separate cause from symptom. The 90 to 365 day test rules out the
   notice-period version of the objection but not the general one. Our claim is that silence is a
   usable flag, never that fixing non-response fixes attrition.

3. **"You are building on `regrettable_flag`, which the brief says is unreliable."** We use it to
   size the prize in L2 and to describe severity in L3, never as an outcome to be modelled. The
   trigger, the targeting and the cost case all run on voluntary exit and HiPo status. That was
   deliberate, and section 3 documents exactly how the flag is contaminated.

4. **"A 3.8% hit rate is terrible."** It is, and we say so first. The economics work because of
   the cost asymmetry, not because of the model quality. Anyone claiming a high-precision
   attrition model on 13,000 employees and a 1.7% base rate is overfitting.

5. **"Why not just pay the underpaid HiPos more?"** Because the data says that would not stop them
   leaving. Compa-ratio has no relationship to whether a HiPo resigns (p = 0.38), and adding it to
   the trigger made the rule measurably worse. Pay is a retention lever once you are already in the
   conversation, not a targeting variable before it.

## Caveats for the appendix

1. The five wave-level silence tests all clear a Bonferroni threshold of 0.01. Across the full
   programme of work, roughly 250 tests, the headline results clear α = 0.0002.
2. The window is 1 Jan 2024 to 31 Dec 2025. Wave 5 has a truncated look-ahead against the censor
   date; every silence result was re-run without it and holds (OR 2.39).
3. `promotion_recommendation` covers 2024-H1 to 2025-H1 only. 2025-H2 is deliberately absent.
4. This is synthetic data with at least one known generator fingerprint, documented in
   findings_05. Any odds ratio above about 10 in this dataset should be stratified and
   timing-tested before it goes on a slide. L2's OR of 10.5 sits right at that line and was
   checked; it survives because the enrichment is smooth across departments rather than
   concentrated in one artefact.
5. The $500 cost per conversation is our assumption, not the brief's. Everything downstream of it
   is sensitivity-tested above.
6. `verify_thesis.py` recomputes every number in this memo directly from the four raw CSVs.
