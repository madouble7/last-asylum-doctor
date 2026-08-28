# Research Doctor capability audit

Audit date: 2026-08-28. This is a read-only audit of the existing local
corpus and SQLite database. It does not fetch new sources, change factual
records, or infer effects or prerequisites.

## Executive result

The corpus is sufficient for a factual research cost/time/power explorer, and
for transparent mathematical efficiency comparisons. It is not sufficient for
an account-aware “what should I research next?” doctor because gameplay effects,
research prerequisites, and live account state are not represented.

Current verified scope: **348 nodes, 2,287 levels, 18 trees**. The database also
contains 7,634 generic level-cost rows and 702 source observations across four
ingestion runs.

## 1. Actual schema

The schema is defined in `src/last_asylum_doctor/database/research.py` and was
checked with SQLite `PRAGMA table_info`.

| Table | Stored fields |
| --- | --- |
| `research_nodes` | `id`, `slug`, `source_research_id`, `name`, `tree`, `tree_slug`, `effect`, `max_level`, `tech_type`, `image`, `position`, `source_page_url`, `source_asset_url`, `first_seen_at`, `last_seen_at` |
| `research_levels` | `id`, `research_node_id`, `level`, `source_record_id`, `power`, `research_time_seconds`, `time_source` |
| `research_level_costs` | `id`, `research_level_id`, `resource_identifier`, `source_label`, `amount`, `item_id`, `source_amount` |
| `research_source_observations` | `id`, `ingestion_run_id`, `research_node_id`, `observed_at`, `source_page_url`, `source_asset_url`, `source_retrieved_at`, `content_sha256`, `etag`, `last_modified`, `content_type` |
| `ingestion_runs` | `id`, `started_at`, `completed_at`, `status`, `requested_slugs_json`, `requested_count`, `succeeded_count`, `failed_count`, `error_message` |

The normalized processed corpus additionally preserves each node's levels,
generic `costs`, source-cost metadata, and retrieval metadata. No research
relationship table exists. No `strategy_claims` or `claim_evidence` table is
implemented yet; those names occur only in reconnaissance/design discussion.

## 2. Coverage matrix

“Present structured” means a typed, queryable factual value exists for the
current corpus. “Text-only” is intentionally not treated as a numeric effect.

| Field | Coverage | Evidence/limitation |
| --- | --- | --- |
| Tree | PRESENT STRUCTURED | `tree`, `tree_slug`; 18 groups |
| Node name | PRESENT STRUCTURED | Non-empty `name` for all 348 |
| Node identifier | PRESENT STRUCTURED | `slug` and `source_research_id` |
| Level | PRESENT STRUCTURED | 2,287 numbered level rows |
| Max level | PRESENT STRUCTURED | `max_level`, validated against source level count |
| Power | PRESENT STRUCTURED | Integer `power` per level |
| Research time | PRESENT STRUCTURED | Integer seconds plus original `time_source` |
| Farms/Grain cost | PRESENT STRUCTURED (source label is Farms) | Generic cost rows; no separate Grain fact |
| Lumber/Timber cost | PRESENT STRUCTURED (source label is Lumber) | Generic cost rows; no separate Timber fact |
| Herbs cost | PRESENT STRUCTURED | Generic cost rows |
| Study Scroll cost | PRESENT STRUCTURED | Generic cost rows with `item_id=item_research_info` |
| Other resources/currencies | PARTIAL | Generic schema is extensible; current corpus observes only Farms, Lumber, Herbs, Study Scroll |
| Effect/stat name | PRESENT BUT TEXT-ONLY | Node `effect`/source `description` strings |
| Effect amount per level | ABSENT | `power` is a research-power value, not a parsed gameplay effect amount |
| Effect type/unit | ABSENT | No percentage/flat/unit field |
| Cumulative effect | ABSENT | No cumulative effect field |
| Multiple effects per level/node | UNSAFE TO INFER | One description string; no structured effect list |
| Prerequisite node | ABSENT | No source field or table |
| Prerequisite level | ABSENT | No source field or table |
| Research Lab requirement | ABSENT | Not exposed by the corpus |
| Sanctuary requirement | ABSENT | Tab `unlock_level` values are null and unused |
| Other building requirement | ABSENT | Not exposed by the corpus |
| Tree unlock/gate | ABSENT | No populated gate relationship |
| Position/order metadata | PRESENT STRUCTURED | `position` is retained; semantics are layout-like, not dependency proof |
| Source/provenance | PRESENT STRUCTURED | URLs, retrieval time, SHA-256, ETag/Last-Modified/content type |

All current node `image`, `tech_type`, and `position` values are populated.
Observed level shapes are 12 one-level nodes, 219 five-level nodes, 116
ten-level nodes, and one twenty-level node.

## 3. Effect evidence

The raw cached ESM modules contain a text description and numeric `power`, but
no numeric gameplay-effect field. Examples:

```text
DEF Boost III raw: r=`Soldier DEF`, ... power:15020, ... ability:15020
DB: effect="Soldier DEF"; level 1 power=15020

Additional Farmland raw: r=`Farm Limit`, ... power:610, ...
DB: effect="Farm Limit"; level 1 power=610
```

`ability` mirrors `power` in the audited source shape and is validated as such;
it does not establish the amount of Soldier DEF or Farm Limit gained. Text such
as `All Points↑ (Excluding Diamond Purchases)` (Arena Expert) and
`Ranger Hero gains additional DMG↓ in battle` names a qualitative effect only.
Percentages versus flat values cannot be distinguished safely. Multiple effects
cannot be represented as separate facts. Effect values must not be inferred
from names, descriptions, positions, or power.

## 4. What can be calculated now

For any known node and inclusive level range, the existing rows support sums of
each stored resource, base research seconds, and source `power`. This works for
standard, mixed, and scroll-only shapes:

| Example | Result for level 1 through max |
| --- | --- |
| `Additional Farmland` (1 level) | 48,600 Farms; 48,600 Lumber; 147,000 Herbs; 2,100 s; 610 power |
| `ATK Boost I` (10 levels, mixed) | 20,923,000 Farms; 20,923,000 Lumber; 63,417,000 Herbs; 3,240 Study Scrolls; 610,700 s; 174,450 power |
| `Arena Expert` (20 levels, scroll-only) | 3,800 Study Scrolls; 1,518,400 s; 421,680 power |
| `DEF Boost III` (10 levels) | 956,413,000 Farms; 956,413,000 Lumber; 2,889,990,000 Herbs; 19,040 Study Scrolls; 15,994,000 s; 1,211,440 power |

These are additive source facts, not a valid prerequisite path. Missing cost
rows mean “not supplied by the source,” not zero; the model only sums rows that
exist.

## 5. Prerequisites and gates

The reconnaissance document `docs/science_prerequisite_reconnaissance.md`
concludes that the public corpus exposes no research-to-research edges, level
thresholds, building requirements, or populated tree gates. `position` is a
layout coordinate and `tech_type` is an opaque category code. Names, IDs, row
order, and visual proximity must not be converted into edges.

Therefore:

- known-node cost/time calculations do not require a prerequisite graph;
- “what should I research next?”, milestone, and tree-completion claims do
  require prerequisites/gates (or an explicitly supplied available-node set);
- no prerequisite graph should be added from the current source.

## 6. Research Doctor capability levels

| Level | Status today | Missing information |
| --- | --- | --- |
| 1. Cost of node X, levels 1→N | POSSIBLE NOW | None for current factual rows |
| 2. Power per scroll/time/resource | POSSIBLE WITH LIMITATIONS | Effect amount and account production/speed are absent; “power” is only the source metric |
| 3. Best account benefit | IMPOSSIBLE SAFELY | Per-level normalized effects, account state, unlock availability |
| 4. Exact prerequisite path to milestone | IMPOSSIBLE | Authoritative prerequisite/gate graph and target milestone definition |
| 5. Full account-aware recommendation engine | IMPOSSIBLE | Levels 3–4 data plus live account state and strategy evidence |

## 7. Strategy layer

Later qualitative guides should be stored as claims separate from factual rows.
The minimum useful evidence shape is:

- a claim with text, scope (tree/node/milestone), recommendation direction, and
  source URL/publication date;
- claim evidence with quoted/paraphrased support, locator, retrieval time, and
  confidence;
- explicit links from a claim to affected node slugs, without overwriting node
  costs, times, power, or effects.

Claims such as “prioritize Alliance Duel” or “Development compounds early” may
rank options, but may not change factual costs/effects. Conflicting claims must
remain visible rather than being silently merged.

## 8. Minimum account state

**Required for a next-step recommendation:** completed level per node,
currently available/unlocked nodes (until a verified graph exists), Study Scroll
balance, relevant resource balances, and active research/slot availability.

**High-value optional:** Research Lab and Sanctuary levels, research-speed
bonuses, troop/hero focus, and upcoming Alliance Duel timing. These become
required when gates, scheduling, or event timing are supported.

**Not needed yet:** purchasing history, shop prices, or a full optimizer for the
cost explorer MVP; those belong to the economic and later strategy layers.

## 9. Highest-value gaps

1. **Structured per-level effects and units.** Without them, the doctor cannot
   compare actual account benefit; descriptions and power are insufficient.
2. **Authoritative prerequisite and gate facts.** These block legal-path,
   milestone, and completion recommendations. They are the next priority after
   effect semantics for a recommendation product.
3. **Live account state.** Even perfect facts cannot answer “next” without what
   Matt has completed, can afford, and can currently start.
4. **Strategy claim evidence.** This improves prioritization after factual
   effects and availability are safe.
5. **Production/speed context.** Needed for calendar/resource forecasting, not
   for the basic cost explorer.

Obtaining a prerequisite graph is not automatically more valuable than effect
normalization: the graph enables legal paths, while effects enable benefit
ranking. For a first useful product, current structured costs already win; for
the recommendation engine, both are blocking, with effect semantics first for
benefit quality and prerequisites immediately after for legality.

## 10. First Research Doctor MVP

Build a **Research Cost & Marginal Efficiency Explorer**:

- Inputs: node(s), inclusive level range, and optional displayed resource/time
  units; later, optional speed multiplier.
- Calculations: additive Farms/Lumber/Herbs/Study Scroll costs, base seconds,
  source power, marginal cost per level, and ratios such as power per scroll or
  power per research-day.
- Outputs: auditable level table, totals, and side-by-side comparisons with
  source URLs and a clear “no prerequisite validation” warning.
- Limitations: no gameplay-effect ranking, legal path, account affordability,
  building gate, or strategy claim is asserted.
- Schema changes: none required. Existing tables and generic cost rows are
  sufficient.

## 11. Reproducibility

The read-only audit helper is:

```powershell
.venv\Scripts\python.exe tools\research_doctor_audit.py --output data/processed/research_doctor_audit.json
```

It reads only the local database and processed corpus. Tests and Ruff should be
run before committing this report and helper.
