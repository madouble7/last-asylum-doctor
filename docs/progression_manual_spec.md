# Doctor's Progression Manual — Architecture Specification

**Status:** Draft / specification-only

**Base:** `3ea55cddb388a8312dfc56e784a18b5460845a82`
**Scope:** A factual, calculation-driven manual for Matt's Server 283 account,
from mid-game foundations through the T9-to-T10 transition.
**Integration owner:** ATLAS Copilot

This document specifies the manual's structure and decision loops. It does not
add game facts, resolve missing gates, or prescribe a universal build order.

## 1. Architecture boundary

The manual follows the four application layers established by the repository:

| Layer | Contents | Allowed inputs | Hard boundary |
| --- | --- | --- | --- |
| **1. Fact** | Source-backed node identity, level costs, time, power, effects, explicit prerequisites, and building gates. | Hashed source captures and reviewed account observations. | No inferred edge, rounded value, or strategy statement becomes a fact. |
| **2. Calculation** | Marginal Efficiency Scores (MES), dependency closure, cost/time totals, event-point projections, and scenario comparisons. | Layer-1 facts plus explicit model parameters. | Outputs are reproducible calculations, not game facts. |
| **3. Strategy** | Priorities, trade-offs, event timing, reserve policies, and stop/continue rules. | Layer-2 results and attributed strategy claims. | Rules must state objective, assumptions, and uncertainty. |
| **4. S283 account state** | Matt's current levels, queues, inventories, goals, budget, and observed unlocks. | Timestamped user input or reviewed S283 captures. | Account state never mutates shared facts and is not generalized to other servers. |

Every recommendation displays its path through these layers. A missing link is
labelled `UNVERIFIED`; the manual must prefer “not enough evidence” to a
confidently invented prerequisite or benefit.

## 2. Evidence status and current boundary

Use the following tags on facts, gates, edges, and claims:

| Tag | Meaning in this specification |
| --- | --- |
| `KNOWN` | Explicitly documented in the repository or a reviewed source-backed record. |
| `REPORTED` | Player/calculator handoff retained in the repository but not independently verified. |
| `INFERRED` | Hypothesis from ordering, naming, layout, or extrapolation; never a factual input. |
| `UNKNOWN` | Not exposed, not captured, or not scoped sufficiently to use. |

The current normalized all-tree corpus is `data/research/all/` (348 nodes and
2,287 level-cost records across 18 branches). It supplies identity, costs,
base duration, and source power/might fields. Public science modules do not
provide research-to-research edges or Institute/Sanctuary gates; those fields
remain `UNKNOWN` unless a separate capture proves them.

The bounded Commando/T10 export and its 18 prerequisite rows are explicitly
marked `USER-SUPPLIED_CHAIN`, so those edges are `REPORTED`. The reported
Institute 25/26/27 high-tier gate and the reported Development-before-advanced-
military relationship remain unscoped `REPORTED` leads. They may guide a
capture request, but they cannot block a calculation as though verified.

## 3. S283 account-state contract

The manual accepts an account-state snapshot with:

| Field | Required distinction |
| --- | --- |
| `account_scope` | `Matt_S283`; never merge with another server/account. |
| `observed_at_utc` | Timestamp of the state observation. |
| `sanctuary_level` | Current visible level, separate from a target or gate. |
| `research_lab_level` / `training_grounds_level` | Current building levels; do not call them Institute levels without explicit evidence. |
| `research_levels` | Current level per node, with `USER_ENTERED_CURRENT` or reviewed-capture provenance. |
| `target_levels` | Desired endpoints tagged `CALCULATOR_TARGET`; never source facts. |
| `queues` | Active construction/research/training timers and remaining minutes. |
| `inventory` | Resources in Millions, Study Scrolls as integer items, speedups by subtype. |
| `event_context` | Event, day, league/bracket, and verified multiplier or `UNKNOWN`. |
| `objective` | For example `earliest_t9`, `t10_readiness`, `research_day_points`, or `resource_safety`. |

For this draft the supplied S283 milestones—Sanctuary 26/27, Research Lab 27,
Training Grounds 27, and T9 unlocked—are `KNOWN` account-state inputs, with the
reviewed T9 chain documented in
`docs/probe_phase12_s27_t9_capture_analysis.md`. They are not universal gate
facts. The manual must still show the capture or entry timestamp whenever it
uses them.

## 4. Phased progression roadmap

Phases are decision horizons, not automatic level gates. A Doctor may remain in
a phase when the next phase's prerequisites or evidence are unavailable.

### Phase A — Early Foundation (Sanctuary 1–25)

**Purpose:** establish compounding capacity and avoid stranded upgrades.

Decision rules:

1. Keep construction and research queues continuously utilized when the
   account objective values growth; record queue downtime as a calculation.
2. Prefer Development/Economy actions whose measured benefit improves future
   queue throughput or resource income, subject to the Doctor's stated budget.
3. Do not rank by aggregate Might alone. Use MES only when the underlying
   effect or power proxy is present and its limitation is visible.
4. Treat building-to-building requirements as facts only when explicitly
   captured. Do not turn screen order into a research prerequisite.
5. Begin a reserve for Study Scroll demand and T9/T10 research, but do not
   assign a future quantity until the target tree and cost evidence exist.

**Exit review:** Sanctuary-26 plan, current queues, resource reserve, and a
source-backed list of the next eligible research actions.

### Phase B — Economic Scaling (Full Development and Sanctuary 26–27)

**Purpose:** fund the long, resource-heavy bridge into advanced military
systems.

Decision rules:

1. Compare Full Development and other economy candidates by MES under the
   account's actual resource and time budgets.
2. Include prerequisite closure costs when the objective is an unlock; show
   direct and closure totals separately.
3. Keep Sanctuary/Research Lab/Training Grounds building upgrades in the
   building layer. A building requirement is not a research effect.
4. Reserve Study Scrolls for the stated objective and upcoming verified event
   multipliers; never spend them because a node merely appears nearby in the
   catalog.
5. At Sanctuary 26, record supply yields as level-26 observations. Do not
   extrapolate them to Sanctuary 27; a projected yield is `INFERRED`.

**Exit review:** S27/T9 chain captured or explicitly marked incomplete, with a
banked-resource and queue plan that lists assumptions.

### Phase C — Military Transition (T9 unlock and T9 operation)

**Purpose:** convert the economic base into the first advanced troop capability
without sacrificing the event or research objective.

The currently reviewed S283 chain is:

```text
Sanctuary 27 -> Training Grounds 27 -> Soldier Training Level 9 (T9)
```

This is a reviewed account-specific progression observation. The T9 lock names
Training Grounds 27; it does not, by itself, establish a Research Lab gate or a
named research prerequisite.

Decision rules:

1. For an earliest-T9 objective, compare speeding Sanctuary 27 and Training
   Grounds 27 against the account's time and event objective.
2. Treat T9 troop cost, batch size, training time, casualty behavior, and T10
   promotion economics as separate facts; leave absent values `UNKNOWN`.
3. Use the Commando/Elite Troop chain only as `REPORTED` until an independent
   S283 capture confirms each edge and required level.
4. Do not postpone an otherwise high-MES economic action solely because a
   reported Institute 25/26/27 threshold has no node mapping.

### Phase D — T10 readiness and end-game transition

**Purpose:** prepare a defensible T10 route after the current T9 state.

Required evidence before a T10 recommendation can be marked verified:

- named T10 research/building prerequisites and required levels;
- T10 training/promotion costs, time, batch size, and combat/stat outcomes;
- Study Scroll demand across all competing trees;
- current S283 event scoring and any research-day multiplier; and
- the account's resource, speedup, and queue opportunity costs.

Until these facts exist, the manual may produce a labelled scenario or evidence
request, not a definitive T10 order.

## 5. Marginal Efficiency Scoring (MES)

MES ranks an eligible *next action* or a bounded path for a stated objective.
It is not a permanent tier list and it does not optimize raw Might by default.

### 5.1 Candidate definition

A candidate (i) is a transition from a known current level to one next level,
or a finite target path whose prerequisite closure is explicit. For each
candidate retain:

- `delta_effect` or `delta_power` and its evidence status;
- resource costs (c_{i,r}) in Millions;
- Study Scroll cost (s_i) as an integer count;
- duration (t_i) in integer minutes;
- direct costs versus prerequisite-closure costs;
- eligibility and unresolved gates; and
- the source fact IDs and model version.

An ineligible candidate is not rescued by a high score. It is returned as
`BLOCKED_BY_UNKNOWN_GATE` or `BLOCKED_BY_REQUIREMENT`.

### 5.2 Benefit term

Let (G_{i,k}) be the verified change in stat/effect (k), expressed as
percentage points or a game-unit delta. Let (w_k) be an explicit objective
weight. The normalized benefit is:

\[
B_i = \sum_k w_k \frac{G_{i,k}}{G_{ref,k}}
      + w_P \frac{\Delta P_i}{P_{ref}}
\]

where (P) is source power only when no better combat/effect measure exists.

- Use either the structured effect term or the power-proxy term when they
  represent the same outcome; do not double-count them.
- (G_{ref,k}) and (P_{ref}) are documented positive reference scales (for
  example, the current account total or a scenario baseline).
- If the effect unit is absent, set that term to `UNKNOWN`; do not convert a
  prose description into a made-up percentage.
- If the source reports a percentage, retain percentage points (`5.0%`), not an
  unlabelled fraction (`0.05`).

### 5.3 Cost burden

For resource budgets (R_r), Study Scroll budget (S), and time horizon (T):

\[
C_i = w_R \sum_r \alpha_r \frac{c_{i,r}}{R_r}
    + w_S \frac{s_i}{S}
    + w_T \frac{t_i}{T}
\]

`α_r` is a declared scarcity multiplier. Resource amounts are displayed in
Millions; Study Scrolls remain integer items. If a budget is zero or unknown,
the corresponding candidate is either blocked or the term is marked
`UNCOMPARABLE`, never silently treated as free.

### 5.4 Score and event modifier

With a small positive ε to avoid division by zero:

\[
\boxed{MES_i = \frac{B_i}{\epsilon + C_i}}
\]

For an active event (e), let (E_i) be verified event points or event value
generated by the action and λE the Doctor's explicit event weight:

\[
MES_{i,e} = \frac{B_i + \lambda_E E_i}{\epsilon + C_i}
\]

An event multiplier changes (E_i), not the factual research effect. If the
multiplier, league, or point table is not verified for S283, set (E_i) to
`UNKNOWN` and render a non-event score rather than guessing.

### 5.5 Path scoring and decision constraints

For a path (q), sum resource, scroll, and time costs across transitions, but
calculate benefit from the final state minus the initial state when effects are
non-additive. Include prerequisite closure in a separate line item:

```text
path_total = direct_action_total + required_closure_total
path_benefit = final_verified_effect - initial_verified_effect
```

MES is a ranking aid. The strategy layer may override it only with a named
hard constraint (for example, “earliest T9”) or an explicit reserve rule, and
the override must be shown in the recommendation.

## 6. Doctor Action Playbook

### 6.1 Daily decision template

```text
Date / observed_at_utc:
Account scope: Matt_S283
Sanctuary / Institute-or-Research-Lab / Training Grounds:
Active event and day:
Verified event multiplier / points:
Objective for today:
Current queues and remaining minutes:
Available resources (Millions), Study Scrolls, speedups:

Eligible candidates:
1. <action> — MES <score>; benefit <...>; direct cost <...>; closure <...>
2. <action> — MES <score>; benefit <...>; direct cost <...>; closure <...>

Chosen action:
Why this action wins under the stated objective:
Required prerequisites and evidence tags:
Reserve consumed / reserve remaining:
Unknowns or stop conditions:
Fact IDs / calculation run / strategy rule:
```

Daily algorithm:

1. Snapshot account state and event context; reject stale or cross-server state.
2. Enumerate only next-level actions whose factual costs and current gates are
   known. Keep blocked actions visible with their blocker.
3. Add explicit prerequisite closure for an unlock objective.
4. Calculate ordinary MES and, only when verified, event-adjusted MES.
5. Apply hard constraints: queue availability, reserve floor, target deadline,
   and the Doctor's objective.
6. Choose the highest surviving candidate, record the rationale, and re-check
   the UI after completion or a source update.

### 6.2 Alliance Duel Research Day playbook

When Research Day is active:

1. Confirm the day, league/bracket, and multiplier from a current S283 source.
2. Generate research candidates that are already eligible and compare
   `MES_{i,e}` with ordinary MES.
3. Prefer actions that both advance the declared progression objective and have
   positive verified event value; do not buy event points with an unbounded
   Study Scroll opportunity cost.
4. Preserve a Study Scroll reserve for the next known research bottleneck. The
   reserve amount is a strategy parameter, not a game fact.
5. If event scoring is unavailable or stale, fall back to ordinary MES and mark
   the event branch `UNVERIFIED`.

### 6.3 Weekly review template

- refresh the account snapshot and source freshness;
- reconcile completed levels, costs, and remaining queues;
- review the next seven-day event calendar and verified bonuses;
- recompute resource/scroll reserves and scarcity multipliers;
- compare the current phase exit criteria with the next phase's evidence needs;
- open evidence requests for blocked T9/T10 gates rather than filling them in;
- record any strategy override and its expiry date.

## 7. Data contracts for the manual

### Fact record

`fact_id`, `research_id`, `tree`, `level`, `effect_raw`, `effect_structured`,
`power`, `costs_millions`, `study_scrolls`, `time_minutes`, `evidence_tag`,
`source_url`, `retrieved_at_utc`, `raw_sha256`, `server_scope`, `client_build`.

### Calculation record

`calculation_id`, `model_version`, `objective`, `candidate_or_path`,
`input_fact_ids`, `account_snapshot_id`, `weights`, `scarcity_multipliers`,
`event_parameters`, `direct_cost`, `closure_cost`, `benefit`, `MES`,
`unknowns`, `generated_at_utc`.

### Strategy record

`strategy_id`, `rule_text`, `objective`, `hard_constraints`, `reserve_policy`,
`applicability`, `source_claim_ids`, `status`, `reviewed_at_utc`.

### Account-state record

`account_snapshot_id`, `account_scope`, `observed_at_utc`, current levels,
queues, inventory, active event, user targets, and input provenance. User
targets carry `CALCULATOR_TARGET`; they never overwrite fact records.

## 8. Validation and stop conditions

The manual must stop or downgrade a recommendation when:

- a required cost, effect unit, prerequisite, or building gate is `UNKNOWN`;
- a candidate crosses a server/build/season scope without an explicit rule;
- an event multiplier or point table is stale or unverified;
- a target is being mistaken for a current level;
- a path contains an `INFERRED` edge presented as factual; or
- a resource/scroll budget is missing, zero, or incomparable.

Validation checks must confirm contiguous source levels, non-negative costs,
integer minutes, Million resource units, stable node IDs, and preserved source
provenance. A failed check produces a visible blocker, not a guessed value.

## 9. Current gaps and next evidence requests

The highest-value missing inputs for a verified S283 T10 manual are:

1. Named Institute and Sanctuary gates for each advanced research branch.
2. Independent confirmation of the reported Development-to-Commando/Elite
   Troop edges and the bounded Commando chain.
3. T10 research and troop-training costs, times, stats, and promotion rules.
4. Study Scroll costs/effects across every competing tree and current S283
   Alliance Duel scoring.
5. Sanctuary 27 supply yields and their server/build scope.

Until these are captured with provenance, the manual can still guide queue
discipline, ordinary cost comparisons, and evidence collection, but it must not
claim a complete or universally optimal T10 route.
