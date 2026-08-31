# Research Tree Topology Manifest

**Status:** Draft / research-only

**Base:** `81dd56a9ef87781c957590592b13d45500ea1e68`

**Owner:** SCOUT Codex; ATLAS Copilot integrates canonical changes
**Scope:** Building gates, research-to-research prerequisites, and provisional
Sanctuary supply-yield context for all 18 research trees.

This document is a topology evidence register, not a claim that every gate or
edge is known. Unknowns are first-class records. No level is invented from a
tree position, an ID pattern, a calculator layout, or a player's progression.

## 1. Evidence architecture and evidence tags

The manifest follows the four application layers in
`docs/research_source_manifest.md`:

1. **Factual game data** — source captures, normalized nodes/levels/costs,
   explicit edges, and explicit building gates.
2. **Calculated efficiency** — dependency closure, cost/time roll-ups, and
   supply-yield comparisons derived from Layer 1.
3. **Strategic judgment** — attributed priorities and trade-offs, with their
   conditions and uncertainty.
4. **Player-specific recommendations** — account state, target, and advice.

This file records Layers 1 and 3 evidence boundaries. A graph edge derived by a
calculator belongs to Layer 2 and must not be written as a factual edge.

Every requirement row uses exactly one of these classifications:

| Tag | Meaning | Permitted use |
| --- | --- | --- |
| `KNOWN` | Explicitly documented in the repository or a retained source-backed record. | May enter the factual layer with its provenance link. |
| `REPORTED` | Player, calculator, or handoff assertion preserved in the repository but not independently source-verified. | Lead or provisional comparison only; never silently promoted. |
| `INFERRED` | Hypothesis derived from layout, naming, level sequence, or another indirect signal. | Investigation queue only; never a prerequisite or gate fact. |
| `UNKNOWN` | No usable evidence, or evidence is incomplete/unscoped. | Keep the field explicit and do not substitute a value. |

`OBSERVED`, `DERIVED`, and `CONFLICT` may appear as supporting refinements in
linked evidence records, but the topology requirement itself still receives one
of the four tags above.

## 2. Current source boundary

The public LastAsylumDatabase science corpus is documented as 348 nodes across
18 trees and 2,287 levels. It supplies node identity, descriptions, layout
metadata, costs, base time, and research power. Its current public modules do
not supply research prerequisites, required research levels, Sanctuary gates,
Institute gates, or a connected edge graph (`docs/science_prerequisite_reconnaissance.md`).

The canonical research export currently contains a bounded 23-node Commando
dataset (`data/research/research_nodes.json`) and 18 prerequisite rows
(`data/research/research_prerequisites.json`). Its metadata explicitly says
`evidence_status: USER-SUPPLIED_CHAIN`; those edges are therefore `REPORTED`,
not source-verified facts. The node file's `source_branch: Elite Troop` and
`branch: Commando` are identity/provenance fields, not proof of a cross-tree
dependency.

No source inspected in the building reconnaissance establishes a
building-to-research-tree gate. SatoriMeta and LastAsylumDatabase do expose
building-to-building requirements, which are recorded separately below.

## 3. Eighteen-tree gate matrix

The matrix is intentionally complete even where every gate is unknown. A cell
tag applies to the entire statement in that cell. `Institute` is not silently
equated with the `Research Lab` building used in building-only records.

| Research tree | Institute milestone(s) | Sanctuary milestone(s) | Cross-tree research prerequisite | Evidence / scope |
| --- | --- | --- | --- | --- |
| Alliance Duel | `UNKNOWN` — no explicit research gate captured | `UNKNOWN` — no explicit research gate captured | `UNKNOWN` | `UNKNOWN`; public science modules expose no edges or gates. |
| Caravan Transport | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Defensive Tactics | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Development | `UNKNOWN` | `UNKNOWN` | `REPORTED` — Development completion is said to precede advanced military research, but no node IDs/levels are supplied. | `REPORTED` handoff only; not independently verified. |
| Economy | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Elite Troop | `REPORTED` — an unscoped high-tier claim cites Institute 25/26/27; branch and threshold are not mapped. | `UNKNOWN` | `REPORTED` — reported Development/advanced-military relationship; exact edges absent. | `REPORTED`; do not assign 25, 26, or 27 to a node. |
| Full Development | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Hero | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Offensive Tactics | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Prosperous Economy | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Ranger Mastery | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; layout coordinates are not edges. |
| Soldier | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Squad 1 | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Squad 2 | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Squad 3 | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Squad 4 | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Warlock Mastery | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |
| Warrior Mastery | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN`; no tree-specific gate source. |

### Interpretation of the reported Institute milestone

The only current handoff is “Institute 25/26/27 gates high-tier research
branches.” It does not identify whether these are three separate gates, a
range, a server-dependent rollout, or which nodes are affected. It therefore
remains one `REPORTED` unscoped lead rather than 25/26/27 rows copied onto
Elite Troop, Commando, T10, or any other tree.

## 4. Known building topology (not research-tree gates)

These are useful prerequisites for a future progression graph, but they must
not be relabelled as research requirements. They are `KNOWN` because they are
explicitly recorded in `docs/building_source_reconnaissance.md`.

| Target building/level | Explicit building requirement | Tag | Evidence boundary |
| --- | --- | --- | --- |
| Walls Lv1 | Sanctuary Lv4 | `KNOWN` | LastAsylumDatabase building record. |
| Research Lab Lv1 | Sanctuary Lv7 | `KNOWN` | LastAsylumDatabase building record; this does not establish an Institute gate. |
| Training Grounds Lv1 | Sanctuary Lv6 **and** Barracks Lv1 | `KNOWN` | LastAsylumDatabase/SatoriMeta building records. |
| Warrior Statue Lv1 | Sanctuary Lv7 | `KNOWN` | LastAsylumDatabase building record. |
| Warlock Statue Lv1 | Sanctuary Lv11 | `KNOWN` | LastAsylumDatabase building record. |
| Alliance Hall Lv1 | Sanctuary Lv6 **and** Falcon Tower Lv1 | `KNOWN` | LastAsylumDatabase/SatoriMeta building records. |
| Builder's Hut Lv1 | Sanctuary Lv3 | `KNOWN` | LastAsylumDatabase building record. |
| Farm Lv1 | Sanctuary Lv1 | `KNOWN` | LastAsylumDatabase building record. |
| Sanctuary Lv26 | Research Lab Lv25, Warrior Statue Lv25, Antitoxin Workshop Lv13 | `KNOWN` | Compared building records; not a research-tree gate. |
| Sanctuary Lv30 | Research Lab Lv29, Training Grounds Lv29, Antitoxin Workshop Lv15 | `KNOWN` | Compared building records; not a research-tree gate. |

The building sources contain unresolved non-building conditions in some Satori
rows. Those conditions remain unnamed and are not converted into research,
Institute, Star, or Sanctuary requirements.

## 5. Cross-tree and Commando prerequisite ledger

### 5.1 User-supplied Commando chain

The following chain is present in
`data/research/research_prerequisites.json`. Each row is `REPORTED` because the
file itself preserves `USER-SUPPLIED_CHAIN` provenance. IDs and levels are
retained exactly; no stronger claim is made.

| Target node / level | Required node / level(s) | Tag | Evidence |
| --- | --- | --- | --- |
| 11013 Morale Lv3 | 11010 HP Boost II Lv3; 11011 ATK Boost II Lv3; 11012 DEF Boost II Lv3 | `REPORTED` | `research_prerequisites.json`, rules 01–03. |
| 11014 DEF Drill VIII Lv3 | 11013 Morale Lv3 | `REPORTED` | Rule 04. |
| 11015 Attack Training VIII Lv3 | 11013 Morale Lv3 | `REPORTED` | Rule 05. |
| 11016 Survival Training VIII Lv3 | 11013 Morale Lv3 | `REPORTED` | Rule 06. |
| 11017 Quick Bandage I Lv1 | 11014, 11015, and 11016 Lv3 | `REPORTED` | Rules 07–09. |
| 11018 Infirmary Expansion I Lv1 | 11014, 11015, and 11016 Lv3 | `REPORTED` | Rules 10–12. |
| 11019 Survival Skills Lv10 | 11017 Quick Bandage I Lv1; 11018 Infirmary Expansion I Lv1 | `REPORTED` | Rules 13–14. |
| 11020 HP Boost III Lv10 | 11019 Survival Skills Lv10 | `REPORTED` | Rule 15. |
| 11021 ATK Boost III Lv10 | 11020 HP Boost III Lv10 | `REPORTED` | Rule 16. |
| 11022 DEF Boost III Lv10 | 11021 ATK Boost III Lv10 | `REPORTED` | Rule 17. |
| 11023 Lv.10 Soldier Lv1 | 11022 DEF Boost III Lv10 | `REPORTED` | Rule 18. |

This ledger is an evidence-preserving handoff, not confirmation that the live
game enforces every edge. A future source-backed capture may corroborate,
replace, or conflict with individual rows; rows must not be bulk-promoted.

### 5.2 Development-to-military lead

| Proposed relationship | Tag | What is actually known |
| --- | --- | --- |
| Development node(s) must precede Elite Troop/Commando or T10 | `REPORTED` | Player/calculator handoff names the relationship but supplies no target node IDs, required levels, source URL, or capture hash. |
| `source_branch: Elite Troop` → `branch: Commando` in the bounded export | `KNOWN` | This is how the local node export labels its source and branch; it does not prove a prerequisite edge. |
| Any other cross-tree edge among the 18 trees | `UNKNOWN` | No explicit edge list or source-backed relationship is currently retained. |

Do not infer cross-tree edges from `pos`, `tech_type`, numeric ID prefixes,
catalog order, node names, or apparent military progression.

## 6. Sanctuary supply-yield policy

Sanctuary supply yields are level- and context-dependent observations. They are
not interchangeable with building costs or research gates.

| Observation | Required treatment | Tag |
| --- | --- | --- |
| Sanctuary 26 yield visible in a dated account capture | Store the exact yield, item/supply identity, Sanctuary level 26, server/account/build context, capture hash, and evidence locator. Keep it labelled as level-26 observed data. | `REPORTED` until the Layer-1 capture is independently reviewed; then retain the observation provenance. |
| Sanctuary 27 yield absent from the capture | Leave the value and any gate relationship explicit as unknown. | `UNKNOWN` |
| Value calculated by scaling, interpolating, or extrapolating Sanctuary 26 to 27 | Keep only as a clearly labelled model experiment; never write it into factual supply data. | `INFERRED` |
| Explicit Sanctuary 27 UI/export capture | Create a new capture and compare it to the level-26 observation; do not overwrite the earlier snapshot. | `KNOWN` after provenance and review gates pass |

Rules:

- `sanctuary_level_observed` is the account/building level at capture time;
  `yield_level` is the level to which the quantity applies. They must not be
  collapsed into one field.
- A level-26 observation cannot establish a level-27 yield, Institute gate,
  research prerequisite, or universal server rule.
- If the same item has multiple yields, retain each source-scoped observation;
  do not average values across servers, seasons, or account states.
- Calculator outputs based on yields belong to Layer 2 and must cite the exact
  observed inputs and assumptions.

## 7. Topology data dictionary

### `topology_capture`

| Field | Definition |
| --- | --- |
| `capture_id` | Unique, never-reused capture identifier. |
| `source_url` / `source_asset_url` | Original page and exact data asset, if distinct. |
| `retrieved_at_utc` | UTC timestamp of retrieval or UI observation. |
| `raw_sha256` | SHA-256 of exact response, export, screenshot, or PDF bytes. |
| `server_scope` / `account_scope` | Explicit server/kingdom and safe account scope; `unknown` is valid. |
| `auth_state` | `anonymous`, `authenticated_authorized`, `user_provided_export`, or `unknown`; never store credentials. |
| `sanctuary_level_observed` / `institute_level_observed` | Current visible account levels, separate from requirements. |
| `season_or_era` / `client_build` | Applicability context, or explicit unknown. |
| `completeness` | `complete_branch`, `partial_branch`, `single_node`, or `unscoped_handoff`. |
| `evidence_locator` | Source record ID, JSON path, screenshot region, or timestamp. |

These fields follow the required provenance contract in
`docs/research_source_manifest.md`.

### `research_tree_gate`

| Field | Definition |
| --- | --- |
| `tree_slug` / `research_id` | Tree-wide or node-specific target; do not use display names as keys. |
| `building_key` | `sanctuary`, `institute`, or an explicitly identified building. |
| `required_level` | Required building level, nullable only when the source omits it. |
| `evidence_tag` | One of `KNOWN`, `REPORTED`, `INFERRED`, `UNKNOWN`. |
| `scope` | Server, account, season, and client-build applicability. |
| `condition_text` | Exact source wording or a concise transcription. |
| `capture_id` / `evidence_locator` | Provenance link and precise location. |

### `research_prerequisite_edge`

| Field | Definition |
| --- | --- |
| `target_research_id` / `target_level` | Node and level being unlocked. |
| `required_research_id` / `required_level` | Explicit predecessor and threshold. |
| `edge_type` | `requires`, `alternative`, or `unknown`; never infer AND/OR from layout. |
| `evidence_tag` | One of the four required topology tags. |
| `capture_id` / `source_record_id` | Source and record identity. |
| `review_status` | `lead`, `corroborated`, `contradicted`, or `superseded`. |

### `sanctuary_supply_yield_observation`

| Field | Definition |
| --- | --- |
| `sanctuary_level` / `yield_level` | Level context, kept separate from account current level. |
| `supply_item_id` / `source_label` | Source identity and visible label. |
| `amount_raw` / `unit` | Exact quantity and unit; do not infer a scale curve. |
| `evidence_tag` | `KNOWN`, `REPORTED`, `INFERRED`, or `UNKNOWN`. |
| `server_scope` / `account_scope` / `client_build` | Applicability context. |
| `capture_id` | Hash-linked provenance. |

## 8. Validation and conflict handling

Before a topology row is promoted or used by a progression calculation:

- every requirement has an explicit evidence tag and a provenance link or an
  explanation for `UNKNOWN`;
- target and prerequisite IDs resolve, or unresolved external IDs are retained
  as flagged leads;
- levels are positive integers and source-required levels are not replaced by
  user-entered or calculator-target levels;
- Sanctuary and Institute requirements remain separate fields;
- `REPORTED` and `INFERRED` edges cannot satisfy a factual prerequisite check
  without an independent corroborating capture;
- partial branches, unresolved Satori conditions, and missing S27 yields remain
  visible; and
- source disagreements are retained as scoped observations and linked through a
  conflict record rather than averaged.

### Conflict review result for this draft

No conflicting **explicit** building prerequisite requirements were identified
across the inspected local documents. LastAsylumDatabase and SatoriMeta agree
on the representative building requirements documented above. Their unresolved
non-building conditions and the absence of research-tree gates are coverage
limitations, not contradictory level requirements. The reported Institute
25/26/27 and Development-to-military statements remain unscoped leads.

## 9. Highest-value evidence gaps

1. A hashed, server-scoped UI/export capture mapping Institute levels to named
   research nodes or branches.
2. A corresponding Sanctuary gate capture, kept distinct from Institute.
3. Independent validation of the 18-row Commando chain, including the reported
   Development-to-Commando connection.
4. A level-27 Sanctuary supply-yield capture to test whether level-26 values
   scale, change tier, or remain account-scoped.
5. A source-backed edge list for the remaining 17 trees, with explicit required
   levels and alternatives.

Until those captures exist, the progression engine may use the `REPORTED`
Commando chain only as an explicitly provisional scenario and must not claim
that any of the 18 trees has a verified Institute or Sanctuary gate.
