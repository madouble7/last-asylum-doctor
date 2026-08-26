# Science schema diversity audit

Investigation date: 2026-08-26

## Verdict

**Full-corpus readiness: READY**

**Confidence: HIGH** for the current deployed source structure. The audit sampled 25 detailed modules across 18 research trees, found no parse or validation failures, and found no meaningful factual field that the current normalized model or SQLite schema drops. The ingestion layer now also rejects unrecognized source fields and conflicting compatibility aliases, so an unobserved future variation fails loudly rather than being silently discarded.

This is not a claim that every one of the remaining 323 detailed modules was inspected. Full ingestion should retain its existing per-node validation, provenance, cache, pacing, and fail-fast behavior.

## Scope and request discipline

The audit did not write sampled nodes to the permanent SQLite database. It used the existing raw HTTP cache where available, performed a fresh `robots.txt` check, and fetched exactly 25 detailed science modules sequentially. No browser automation, JavaScript execution, authentication bypass, or aggressive concurrency was used.

The current sitemap exposed 348 science slugs. The detailed-module audit therefore covered 25/348 nodes (about 7.2%).

## Sampling methodology

The current Vite bundle supplied both the science import map and its embedded science catalog. The sample was selected deterministically:

1. Always include the three validated nodes: `def-boost-iii`, `research-upgrade-iii`, and `training-points`.
2. For each catalog tree, select the median slug in that tree when it fits in the 25-node cap.
3. Fill the remaining positions with evenly spaced entries from the sorted sitemap/import-map intersection.

This avoids a first-alphabetical sample while remaining repeatable for the same source build.

## Exact sampled slugs

```text
def-boost-iii
research-upgrade-iii
training-points
kill-points
luck
defensive-stance-i-2
quick-bandage-iii
herb-gathering-iii
hp-boost-ii
quick-bandage-v
warlock-atk-ii
high-alert-i-2
herb-gathering-v
ranger-hp-ii-2
def-drill-vii
defensive-stance-i
defensive-stance-ii
defensive-stance-iii
defensive-stance-iv
warlock-hp-ii-2
warrior-hp-ii-2
attack-training-vi
blight-slayer-iv
bounty-hunter-ii
construction-master
```

## Research trees encountered

The 25 modules covered 18 trees:

```text
Alliance Duel
Caravan Transport
Defensive Tactics
Development
Economy
Elite Troop
Full Development
Hero
Offensive Tactics
Prosperous Economy
Ranger Mastery
Soldier
Squad 1
Squad 2
Squad 3
Squad 4
Warlock Mastery
Warrior Mastery
```

## Parse and validation outcome

| Check | Result |
| --- | ---: |
| Detailed modules sampled | 25 |
| Parser successes | 25 |
| Parser failures | 0 |
| Normalization/validation failures | 0 |
| Modules where level count equaled declared `max_level` | 25 |
| Modules with contiguous levels | 25 |
| Five-level modules | 16 |
| Ten-level modules | 9 |
| Unexpected source types | 0 |

All modules used the same observed data-only ESM grammar: variable declarations holding literals followed by one default object export. No dynamic expressions or new module structure was encountered.

## Source field inventory

Every sampled module had the following top-level factual keys:

```text
description
id
image
levels
levels_count
max_level
name
pos
slug
tab
tab_slug
tech_type
```

Every sampled level record used this key set:

```text
ability
cost_farms
cost_food
cost_herbs
cost_iron
cost_lumber
cost_special
cost_special_name
cost_wood
costs
level
power
raw_id
time
time_sec
```

Every sampled cost object used only:

```text
amount
amount_fmt
item_id
resource
```

## Resource and item inventory

The exact source vocabulary found in the sample was:

| Identifier | Source label | Source item ID | Occurrences |
| --- | --- | --- | ---: |
| `farms` | `Farms` | — | 145 |
| `lumber` | `Lumber` | — | 145 |
| `herbs` | `Herbs` | — | 145 |
| `study_scroll` | `Study Scroll` | `item_research_info` | 95 |

No semantic resource remapping was applied.

## Structural variations

Three generic cost shapes occurred:

| Shape | Nodes |
| --- | ---: |
| Farms, Lumber, Herbs | 15 |
| Farms, Lumber, Herbs, Study Scroll | 7 |
| Study Scroll only | 3 |

The source uses optional/compatibility fields as follows:

- Standard-resource-only nodes represent `cost_special` and `cost_special_name` as `null`.
- Nodes with Study Scroll use integer `cost_special` and text `cost_special_name` matching the generic cost entry.
- Study-Scroll-only nodes set the ordinary compatibility cost aliases to zero; the generic `costs` array correctly contains only Study Scroll.
- `item_id` is absent from ordinary resource cost objects and present for Study Scroll.
- No zero `time_sec`, generic cost amount, or power value was observed. The only zeroes were compatibility aliases in Study-Scroll-only nodes.

## Model and database compatibility

| Source field group | Classification | Current handling |
| --- | --- | --- |
| Node identity, name, tree, effect, max level, tech type, image, position, URLs | A — preserved | `ResearchNode` and `research_nodes` retain them. |
| Level number, raw ID, time text, seconds, power | A — preserved | `ResearchLevel` and `research_levels` retain them. |
| Generic cost label, amount, item ID, formatted amount | A — preserved | `ResearchCost` and `research_level_costs` retain them as generic rows. |
| `levels_count` | B — redundant | Validated against `max_level`; no separate storage needed. |
| `ability` | B — redundant | Equaled `power` in every sampled level. |
| Ordinary `cost_*` aliases | B — compatibility aliases | Matched the generic source costs or zero for absent ordinary resources. |
| `cost_special`, `cost_special_name` | B — compatibility aliases | Matched the generic Study Scroll cost or were both `null` when absent. |

There were no C (meaningful factual data currently dropped) or D (uncertain human-review) fields in the live sample.

## Hardening applied after the audit

The normalizer now permits only the observed source field sets and validates the compatibility aliases against the generic cost list. Consequently:

- an unknown node, level, or cost key causes a validation failure;
- a source `ability` value that differs from `power` causes a validation failure;
- an alias cost that conflicts with the generic cost list causes a validation failure.

This is intentionally conservative. It prevents a future site change from silently losing factual information, while leaving the generic resource-cost schema open to new resource labels that appear inside the already-supported `costs` array.

## Recommendation

No model or SQLite schema change is required before full-corpus ingestion. The existing generic cost rows are compatible with arbitrary additional resource/item labels, and all currently observed factual node/level fields are represented or verified as redundant.

Proceed with a future full-corpus ingestion only as a separately authorized run. Keep the bounded audit command available as a preflight check after source deployments:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe audit-science-schema
```

The generated detailed audit evidence is stored locally at:

```text
data/processed/science_schema_audit.json
```
