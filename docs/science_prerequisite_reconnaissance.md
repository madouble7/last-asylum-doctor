# Science prerequisite reconnaissance

Investigation date: 2026-08-26

Scope: read-only static inspection of the current public science page, its Vite entry bundle, the science catalog/tabs, representative detailed modules, and all 348 detailed modules already retained in the local raw-response cache. Downloaded JavaScript was inspected as text and was never executed. No prerequisite data was written to SQLite.

## 1. Primary conclusion

**NO EXPLICIT PREREQUISITE SOURCE FOUND**

The current public build does not expose a research prerequisite graph, edge list, parent/child references, required research levels, or building/Sanctuary requirements for research nodes. The science page does not render a connected technology tree: it renders a searchable, filterable card grid. Individual node pages render metadata and a level/cost table.

The public data does contain position-like values, numeric identities, tree categories, and display ordering. None is used by the current application to calculate or draw prerequisite edges. Turning visual or numeric proximity into dependencies would therefore be inference and must not enter the factual database.

Confidence in this negative finding is **HIGH for the current deployed public build**. It is not proof that the game itself has no prerequisites or that a private/upstream dataset lacks them.

## 2. Current public source and relationship origin

The current `/science` HTML shell references:

```text
https://lastasylumdatabase.com/assets/index-Bx4NNJcK.js
```

Static response SHA-256 at inspection time:

```text
6bdcb91d052b392f94e27d46e2a81e5d6655b5a10a5d192a2942dcb70a640284
```

The bundle contains three relevant source groups:

1. `../content/science_catalog.json` — 348 card/catalog entries containing `slug`, `name`, `description`, `tab`, `tab_slug`, `tech_type`, `levels_count`, `max_level`, and `image`.
2. `../content/science_tabs.json` — 18 tree/tab entries containing `slug`, `name`, `order`, and `unlock_level`.
3. `../content/science/{slug}.json` dynamic-import mappings — one detailed ESM asset per node. All current detailed modules use the known node, level, and cost fields documented by the schema audit.

No additional logical path named like a science tree, graph, edge list, connection list, dependency set, or prerequisite manifest was found. Static bundle inspection found one `fetch(` call, which belongs to Vite module-preload support; science data is loaded from compiled static objects and dynamic imports, not an API.

The current stylesheet is:

```text
https://lastasylumdatabase.com/assets/index-CnenB1oj.css
```

It contains no science-tree, connector, edge, or connection-specific selector. More importantly, the React science component contains no connector-rendering structure for the stylesheet to style.

## 3. How the research UI is rendered

The science index component loads `science()` and `scienceTabs()` together. It:

- obtains filter labels by mapping the tab records' `name` values;
- filters cards using `entry.tab === selected` or `entry.tab_slug === selected`;
- searches `name`, `description`, and `tab` text;
- renders the filtered catalog in a responsive CSS grid;
- maps each entry directly to `/science/{slug}`;
- shows `image`, `tab`, `name`, `description`, `levels_count`, and `max_level`.

It does not sort by or access `id`, `pos`, `tech_type`, parents, prerequisites, or edges. Catalog order is retained after filtering.

The node-detail component loads one detailed module and renders `image`, `tab`, `name`, `description`, `max_level`, and a level table containing time, power, and costs. It does not access `id`, `raw_id`, `pos`, `tech_type`, or any requirement relationship.

There are therefore no research connecting lines in the current public UI. The only SVG inside the science index component is the search icon.

## 4. Keyword and structure search

The main bundle was searched statically for prerequisite, require/required, unlock, parent/child, edge, connection, dependency, previous/next, tech-tree, and science-tree terminology.

The two `prerequisites` occurrences belong to an unrelated event-level table. Generic framework and other feature text accounts for most parent/child, required, unlock, and next occurrences.

All 348 raw detailed science modules were searched separately. Only three contain any searched relationship-like word, and in each case `Unlocks` is the node's effect description:

| Slug | Effect text | Meaning established by source |
| --- | --- | --- |
| `lv-10-soldier` | `Unlocks Lv.10 Soldier Training` | Effect produced by this one-level research node. |
| `super-rewards` | `Unlocks  Tier 4–6 rewards` | Effect produced by this one-level Alliance Duel node. |
| `top-rewards` | `Unlocks Tier 7–9 rewards` | Effect produced by this one-level Alliance Duel node. |

None names a prerequisite research node or required level. No raw module contains a prerequisite/parent/edge/dependency field. This is also independently enforced by the current strict schema validation: every one of the 348 modules passed the known-field validation during full ingestion.

## 5. Evidence-backed field semantics

### `id`

`id` is the stable source research-node identity in each detailed module. All 348 current values are unique. The public UI does not display or use it for ordering, navigation, or relationships.

Many IDs visually contain a tree-family prefix, but this is not a universal mapping to `tech_type`. In particular, the 16 Full Development nodes use IDs `1015`–`1032` while having `tech_type: 14`, and the 16 Prosperous Economy nodes use IDs `2015`–`2030` while having `tech_type: 15`. An ID prefix must not be treated as a prerequisite or even as an infallible tree identifier.

### `raw_id`

`raw_id` is a level-record identity. All 2,287 current level values are unique, and every value satisfies:

```text
raw_id = integer(node id) * 1000 + level
```

This establishes hierarchical identity construction, not dependency semantics. The public renderer does not use `raw_id`.

### `pos`

`pos` is present only in detailed modules, not in the science catalog used to render the index. Across all 348 nodes:

- every value has three integer components separated by underscores;
- the first component is always `1`;
- the second component ranges from `1` through `15`;
- the third component is `1`, `2`, or `3`;
- positions are unique within a tree;
- the same position values are reused across different trees.

This shape is compatible with a page/row/column-style layout coordinate, but the labels and exact semantics are not published. The current application never reads `pos`, never derives an edge from it, and never draws a line from it. A coordinate-like pattern alone is not source evidence of a prerequisite.

### `tab` and `tab_slug`

`tab` is the human-readable tree/category name. `tab_slug` is its machine-friendly identifier. The science UI uses both as filter values, with `tab` matching the visible tab buttons and `tab_slug` accepted as a fallback. They classify nodes; they do not encode edges.

### `tech_type`

`tech_type` is an integer category code. Each current tree has exactly one value, and the values correspond to the 18 current tab-order positions (`Development = 1` through `Warlock Mastery = 18`). The public science UI does not access it. The evidence supports treating it as an opaque source category code, not as progression or dependency data.

### `image`

`image` is a public image path. The index and detail components resolve it into the node icon shown in an `<img>` element. It has no observed relationship semantics.

### Tab `order` and `unlock_level`

`science_tabs.json` contains `order: 1` through `18`. That ordering supplies the current category/filter sequence. All 18 records contain `unlock_level: null`, and the science component does not read `unlock_level`. The field name suggests the upstream format can represent some tab-level unlock concept, but the current data supplies no value or requirement type, so no Sanctuary/building meaning can be assigned.

## 6. Three tree traces

The following traces describe source arrangement only. Arrows are deliberately omitted because the source provides no edges.

### Development

- 18 nodes; `tech_type: 1`; observed rows `1`–`11` and columns `1`–`3`.
- Examples: `rapid-construction-i` at `1_1_2`, `research-upgrade-i` at `1_2_2`, a three-node row at row 3, `construction-master` at `1_5_2`, and `extra-training-grounds` at `1_11_2`.
- Representative source assets:
  - `https://lastasylumdatabase.com/assets/rapid-construction-i-De4E7Q7z.js`
  - `https://lastasylumdatabase.com/assets/construction-master-DbVzQRwk.js`
  - `https://lastasylumdatabase.com/assets/extra-training-grounds-C5L0CV2N.js`
- The source does not state that a row-1 node unlocks a row-2 node, or that the three row-3 nodes share a parent.

### Elite Troop

- 23 nodes; `tech_type: 11`; observed rows `1`–`14` and columns `1`–`3`.
- Examples: `hp-boost-i` at `1_1_2`; `atk-boost-i` and `def-boost-i` at row 2 columns 1 and 3; three nodes at row 4; `def-boost-iii` at `1_13_2`; and `lv-10-soldier` at `1_14_2`.
- Representative source assets:
  - `https://lastasylumdatabase.com/assets/hp-boost-i-DZZTUz5Q.js`
  - `https://lastasylumdatabase.com/assets/def-boost-iii-C6p9jdId.js`
  - `https://lastasylumdatabase.com/assets/lv-10-soldier-2SUjkQf2.js`
- `lv-10-soldier` explicitly describes its own unlock effect, but no source field states which research nodes or levels are required to start it.

### Ranger Mastery

- 23 nodes; `tech_type: 17`; observed rows `1`–`13` and columns `1`–`3`.
- Rows 1, 2, 5, 8, and 11 each contain three separately positioned nodes; rows 3, 4, 6, 7, 9, 10, 12, and 13 contain a centered column-2 node.
- Examples: `ranger-hp-i-2` at `1_1_1`, `ranger-synergy-dmg-i` at `1_3_2`, `ranger-ultimate-guard-i` at `1_7_2`, and `ranger-ultimate-guard-ii` at `1_13_2`.
- Representative source assets:
  - `https://lastasylumdatabase.com/assets/ranger-hp-i-2-CUsceYJQ.js`
  - `https://lastasylumdatabase.com/assets/ranger-ultimate-guard-i-DkrQPX4F.js`
  - `https://lastasylumdatabase.com/assets/ranger-ultimate-guard-ii-DSyPrMyT.js`
- The alternating coordinate pattern may resemble a visual progression tree, but no public source assigns parent/child links or required completion levels.

## 7. Verified relationship examples

There are **no verified research-to-research prerequisite examples** in the inspected source.

The following would be unjustified and must not be stored:

```text
rapid-construction-i -> research-upgrade-i
def-boost-iii -> lv-10-soldier
ranger-ultimate-guard-i -> ranger-synergy-hp-ii
```

Those pairs can be placed near one another by `pos`, name, or apparent row sequence, but proximity is not an explicit relationship.

## 8. Level-specific and non-research requirements

No source field states a required research level, target level, prerequisite node, building level, Sanctuary level, or other external condition for any research node.

Level modules provide costs, time, power, compatibility aliases, and record identity only. They do not contain requirements. The all-null tab `unlock_level` values provide no usable requirement fact.

Accordingly:

- research-to-research prerequisites: not exposed;
- level-specific prerequisite thresholds: not exposed;
- building prerequisites: not exposed for science;
- Sanctuary prerequisites: not exposed for science;
- tab unlock requirements: structurally possible but all current values are null and unused.

## 9. Other public structured-source checks

- Initial HTML: application shell only; no science or graph data.
- Sitemap: science page URLs only; no relationship metadata.
- Main bundle catalog: card metadata only.
- Science tabs: category order plus all-null `unlock_level`.
- Detailed modules: node/level/cost facts only.
- API/fetch: no science API; static compiled data and dynamic imports are used.
- Build manifest/import map: maps slugs to detailed assets only; no graph asset was found.
- Rendered application code: card grid and detail table; no tree-line renderer.

Ordinary HTTP and static parsing are sufficient to retrieve everything the current public build exposes. They are not sufficient to obtain prerequisite facts that are absent from that build.

## 10. Database implications

Do **not** add or populate a prerequisite table from the current source. The smallest correct factual representation today is no schema change.

If a future authoritative source exposes requirements, a normalized design should represent requirements as their own source-backed facts rather than overloading `pos`, `id`, or `tech_type`. A possible future shape is:

```text
research_requirements
  id
  target_research_node_id
  target_level (nullable only if the source is node-level)
  requirement_type
  prerequisite_research_node_id (nullable)
  prerequisite_level (nullable)
  prerequisite_external_identifier (nullable)
  prerequisite_external_name (nullable)
  source_observation_id / source URL and content hash
```

That is a future compatibility sketch, not a schema recommendation justified for implementation now. Exact nullability, uniqueness, and requirement-type constraints must follow the first explicit source rather than assumptions.

## 11. Unknowns and possible future evidence

- Whether the game client contains a separate authoritative technology graph.
- Whether `pos` is generated from game coordinates, editorial layout, or another upstream field.
- What the first `pos` component means; it is constant in the public corpus.
- Whether the current tab `unlock_level` field was intended for Sanctuary level, another progression gate, or simply a generic unused catalog property.
- Whether prerequisite levels are always a predecessor's maximum level or vary per edge.
- Whether nodes can have multiple research prerequisites or non-research gates.

A future reconstruction from screenshots, visual proximity, name sequences, or game experience could be useful as a hypothesis set, but it must remain explicitly inferred and separate from factual tables until independently verified.

## 12. Confidence

**HIGH** that the current public LastAsylumDatabase.com build exposes no explicit science prerequisite graph and that its current React UI does not generate research edges.

**LOW** confidence in any prerequisite reconstructed from `pos`, IDs, names, or apparent row order without a new authoritative source. Such reconstruction was not performed in this task.
