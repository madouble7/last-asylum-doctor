# Building source reconnaissance

Investigation date: 2026-08-26

Scope: read-only, low-volume static inspection of the current public building data on LastAsylumDatabase.com, LastAsylumPlague.com, and SatoriMeta. Downloaded JavaScript was inspected as text and was never executed. No browser automation was used. No building data or inferred relationship was written to SQLite, and the existing research corpus was not changed.

## 1. Primary conclusion

No single inspected source is sufficient for every building fact.

- **LastAsylumDatabase.com is the best canonical source for building identities and per-level factual values.** It exposes 46 buildings and advertises 980 level records through a catalog plus one structured ESM module per building. It supplies exact resources, time, source IDs, maximum levels, power values, and level-specific prerequisite text.
- **SatoriMeta is the best retrieval source for normalized building-to-building prerequisites.** Its server-rendered calculator embeds 46 buildings, 974 levels, and structured `{building, level}` requirements. It also preserves a count of unresolved non-building conditions. It should be treated as a secondary structured source because its upstream provenance is not published, it omits six levels found in LastAsylumDatabase, and it has at least one material power disagreement.
- **LastAsylumPlague.com is a useful community-guide fallback for Sanctuary unlocks, Diamonds, and a second presentation of requirements.** Its one indexed building page supplies explicit unlock text unavailable from the other two sources. Its resource and `Build Time` values are not safe canonical base values because they diverge from the exact `Original Time`/structured-source values and appear adjusted or rounded despite contradictory explanatory text.

The future ingestion design should preserve separate source assertions. Agreement may increase confidence, but one source's value must never silently overwrite another's.

Confidence in the delivery-mechanism and field findings is **HIGH for the public builds retrieved on the investigation date**. Confidence that LastAsylumDatabase values are true in-game base facts is **MEDIUM-HIGH pending targeted manual game verification**. Confidence in unlock coverage is **LOW outside Sanctuary**.

## 2. Safety and method

All three `robots.txt` files were checked before content inspection:

| Site | Relevant result | Action |
| --- | --- | --- |
| `lastasylumdatabase.com` | `/` allowed; unrelated event/item/map paths disallowed | Building routes and static assets only |
| `lastasylumplague.com` | Empty `Disallow` plus sitemap index | Sitemap, one indexed page, its public REST representation, and one bounded 404 route check |
| `satorimeta.com` | `/` allowed | Calculator HTML and its two referenced first-party client bundles only |

Requests were sequential, cached, and bounded. There was no authentication, bypass, destructive interaction, or mass crawl. The existing respectful HTTP client retained response bodies and retrieval metadata under the Git-ignored raw cache. The current production research parser was not changed; for temporary inspection of building modules, its safe literal parser was used after narrowly translating minified JavaScript booleans `!0`/`!1` to `true`/`false`. This did not execute JavaScript.

## 3. Source inventory and counts

| Source | Building identities | Level records exposed | Scope note |
| --- | ---: | ---: | --- |
| LastAsylumDatabase | 46 | 980 advertised by catalog | 13 buildings max at Lv1, one at Lv2, 31 at Lv30, one at Lv35 |
| SatoriMeta | 46 | 974 embedded | Same slug set; Residence includes only Lv2 and Soldier's Rest ends at Lv30 |
| LastAsylumPlague | 1 indexed building page | 30 Sanctuary table rows | No equivalent indexed pages for the other 45 buildings |

The LastAsylumDatabase building catalog, its import map, and its 46 `/buildings/{slug}` sitemap routes have identical slug sets. SatoriMeta also has the same 46 slugs, but not the same level coverage:

- LastAsylumDatabase has Residence Lv1 and Lv2; SatoriMeta has only Residence Lv2.
- LastAsylumDatabase has Soldier's Rest Lv1-Lv35; SatoriMeta has Lv1-Lv30.

Those account for the six-record difference. A direct request for the bounded guess `https://lastasylumplague.com/buildings/walls/` returned 404, and its current post sitemap contains only the Sanctuary building page.

## 4. LastAsylumDatabase.com

### Delivery mechanism

Buildings use the same broad Vite architecture as science, but the building schema is different:

```text
HTML application shell
    -> current main Vite bundle
    -> embedded buildings_catalog.json and dynamic-import map
    -> ../content/buildings/{slug}.json logical key
    -> public page-specific hashed ESM module
    -> React building-detail table
```

The public building route is:

```text
https://lastasylumdatabase.com/buildings/{slug}
```

The inspected main bundle was:

```text
https://lastasylumdatabase.com/assets/index-Bx4NNJcK.js
SHA-256: 6bdcb91d052b392f94e27d46e2a81e5d6655b5a10a5d192a2942dcb70a640284
Last-Modified: Mon, 20 Jul 2026 06:31:22 GMT
```

The sitemap had 814 total URLs, including 46 building-detail routes:

```text
SHA-256: 2ffe9b74fd6beaa17a327724327ad486f310d2759a3a4823df7d628619c34af0
```

Eleven page-specific modules were inspected: the nine requested representative types plus Residence and Soldier's Rest to investigate a cross-source count discrepancy. This remained a bounded sample rather than a complete building crawl.

### Catalog fields

Each embedded catalog entry contains:

```text
slug, name, id, max_level, levels_count, image, description,
power_max, is_main
```

### Detailed module fields

The sampled building objects contain:

```text
id, slug, name, max_level, levels_count, levels, image, time_max,
description, power_max, is_main
```

The usual sampled level record contains:

```text
level, time_sec, time,
cost_farms, cost_lumber, cost_herbs, cost_stars,
reward_antitoxins, reward_stars,
cost_food, cost_wood, cost_iron, reward_exp,
prerequisites, prerequisites_readable, power
```

The pairs `cost_farms`/`cost_food`, `cost_lumber`/`cost_wood`, `cost_herbs`/`cost_iron`, and `reward_antitoxins`/`reward_exp` hold equal values in the sample. `cost_stars` and `reward_stars` also match. These appear to be compatibility aliases, but ingestion should retain the source names until the game meaning is verified instead of assuming every label is semantically interchangeable.

`time_sec` is the exact numeric duration and `time` is a formatted rendering. For ordinary sampled buildings, `power` behaves as total power at that building level: the calculator's power gain is the target-level value minus the current-level value, and the last value equals catalog `power_max`. Soldier's Rest is an explicit counterexample discussed below, so the future raw field should be named `source_power_value` until its semantics are validated per building.

### Prerequisites and Sanctuary gates

Prerequisites are explicit, target-level-specific strings. Multiple simultaneous requirements are supported and separated by a middle dot. `prerequisites` and `prerequisites_readable` matched in the sample. Examples include:

| Target | Explicit source requirement |
| --- | --- |
| Walls Lv1 | Sanctuary Lv4 |
| Research Lab Lv1 | Sanctuary Lv7 |
| Training Grounds Lv1 | Sanctuary Lv6 **and** Barracks Lv1 |
| Warrior Statue Lv1 | Sanctuary Lv7 |
| Warlock Statue Lv1 | Sanctuary Lv11 |
| Alliance Hall Lv1 | Sanctuary Lv6 **and** Falcon Tower Lv1 |
| Builder's Hut Lv1 | Sanctuary Lv3 |
| Farm Lv1 | Sanctuary Lv1 |
| Sanctuary Lv30 | Research Lab Lv29 **and** Training Grounds Lv29 **and** Antitoxin Workshop Lv15 |

The source therefore explicitly represents both “building X needs Sanctuary level Y” and “Sanctuary level X needs several other buildings.” It does not expose a typed non-building requirement collection. Sanctuary's `cost_stars` is nonzero on Lv3-Lv30, but that is a cost field and must not be transformed into a generic prerequisite without preserving its exact source meaning.

### Unlocks

No explicit unlock collection was found in the catalog, the sampled detailed objects, or the building-detail renderer. Reverse-computing unlocks from prerequisite edges may later be useful for navigation, but it would be a calculated inverse dependency, not a source-authored unlock fact. It must not be stored as though the source explicitly said “unlocks.”

## 5. LastAsylumPlague.com

### Delivery mechanism and scope

The Sanctuary page is conventional WordPress HTML with a server-rendered 30-row table:

```text
https://lastasylumplague.com/buildings/sanctuary/
SHA-256: a709d3fe7068b280c0da92659c215d7c6a598de9b92cfc16f145e3cddbba3faf
```

The page is WordPress post 14, published 2026-03-10 and modified 2026-07-19 according to its public metadata. The public `wp-json/wp/v2/posts/14` response is a JSON envelope, but `content.rendered` still contains the table as HTML rather than typed level objects. Static HTML parsing is sufficient.

Columns are:

```text
Level, Farms, Lumbers, Herbs, Stars, Required Buildings,
Diamonds, Build Time, Original Time, Unlocks
```

Requirements and unlocks are level-specific human-readable cells. They are parseable but not strongly typed. Multiple required buildings occupy the same cell. There is no Might/power column.

### Explicit unlock examples

The page explicitly supplies facts absent from the other inspected sources:

| Sanctuary level | Source-authored unlock text |
| --- | --- |
| Lv1 | New Lumberyard and Farms |
| Lv2 | New Herb Garden |
| Lv3 | Builder's Hut, Herb Storage, Lumber Depot, Granary |
| Lv10 | Private Stable, Alliance Stable, New Antitoxin Workshop, New Smelting Workshop |
| Lv11 | Warlock Statue, New Scout Squad |
| Lv20 | New Squad 3, Barracks, Smelting Workshop |

These should enter a future unlock table only as source-backed text assertions until each target can be resolved unambiguously. Words such as “New,” troop/feature labels, and repeated building names require a reviewed alias map; they should not be guessed into building IDs.

### Base-versus-adjusted ambiguity

The article describes the table as base time/resources and also warns that actual account values can be lower because of Builder's Hut, alliance effects, survivors, Noble Fortress, and other bonuses. The table itself contains both `Build Time` and `Original Time`.

The evidence shows:

- `Original Time` agrees exactly with LastAsylumDatabase and SatoriMeta at all compared Sanctuary levels.
- `Build Time` begins to fall below `Original Time` at Lv11 and is progressively much lower at later levels.
- resource values are rounded at some levels and become materially lower than the exact structured values at later levels.

Therefore `Original Time` is the safe base-duration candidate. `Build Time` is an adjusted/displayed value, even though the page does not publish the exact modifier context. The resource columns are not safe base values. The page's prose and table values are internally ambiguous, so future ingestion must store the two time columns separately and must not use its resources as canonical base costs without manual verification.

## 6. SatoriMeta

### Delivery mechanism

The calculator is server-rendered with Astro/Preact:

```text
https://satorimeta.com/en/last-asylum/calculator/
SHA-256: 1780d190f2243718e558988a36ddf6f062f373c6265bd634f2b4145d24d80ddc
```

The page's `<astro-island>` contains an HTML-escaped serialized `props` value. Static decoding yields top-level fields:

```text
buildings, resourceImages, locale, strings, routineBuildings
```

No API request, `fetch`, or XHR was found in the two referenced calculator/client bundles. The 46-building dataset is already present in the initial HTML and the client bundle only performs calculations and interaction. Exact per-level requirements can therefore be retrieved without executing remote JavaScript.

The ultimate upstream origin is **not disclosed by the inspected page or bundles**. Many values exactly match LastAsylumDatabase, but the six-level coverage difference and Soldier's Rest power disagreement prove that “Satori is merely a lossless copy of LastAsylumDatabase” would be an unsupported conclusion.

### Structured fields and calculation semantics

Each building contains:

```text
slug, name, sortOrder, levels, imagePath
```

Each level contains:

```text
level, grain, timber, herb, antitoxin, timeSeconds, power,
requirements (optional)
```

`antitoxin` is zero in all 974 embedded rows. Requirements contain:

```text
buildings: [{building: slug, level: integer}, ...]
unresolvedRequirementCount: integer
```

The payload has 920 levels with a `requirements` object, 919 with at least one resolved building requirement, and 31 levels with one unresolved non-building condition each. Sanctuary Lv3-Lv30 account for 28 of those unresolved conditions. Those levels also have nonzero LastAsylumDatabase `cost_stars`, but Satori does not name its unresolved condition; the correspondence must be documented, not promoted to an asserted Star requirement.

The calculator sums grain/timber/herb/time for each selected upgrade step, recursively raises prerequisite buildings from Lv0, and calculates power gain as target-level `power` minus current-level `power`. It does not add prerequisite construction time to the displayed grand total in the inspected client logic, although it does add prerequisite resource costs; that is calculator behavior, not a new factual field.

Representative normalized requirements include:

```text
Sanctuary Lv10 -> infirmary Lv7 + walls Lv9 + 1 unresolved condition
Sanctuary Lv20 -> alliance-hall Lv18 + farm Lv10 + research-lab Lv19
                  + 1 unresolved condition
Sanctuary Lv30 -> antitoxin-workshop Lv15 + research-lab Lv29
                  + training-grounds Lv29 + 1 unresolved condition
Training Grounds Lv1 -> barracks Lv1 + sanctuary Lv6
Alliance Hall Lv1 -> falcon-tower Lv1 + sanctuary Lv6
```

This is the strongest inspected format for building graph construction because the building slugs and levels are already typed. The unresolved count must remain unresolved; no placeholder fact should name a Star, research, territory, or other condition without another explicit source.

## 7. Representative Sanctuary comparison

LastAsylumDatabase and SatoriMeta agree exactly on all listed Sanctuary costs, seconds, cumulative level power, and normalized/text building requirements. LastAsylumPlague's `Original Time` also agrees exactly, and its required-building text expresses the same conjunctions.

| Level | LastAsylumDatabase / Satori base values | LastAsylumPlague presentation | Result |
| --- | --- | --- | --- |
| Lv1 | grain 29, timber 29, 2 sec, power 900 | resources blank; `Already Built` | Level-one semantics conflict |
| Lv3 | grain 983, timber 983, Stars 17, 3 sec, power 2,500 | 983/983, Stars 17, 3 sec; explicit unlocks | Agreement on shown numeric facts |
| Lv10 | 748,700/748,700/232,900, Stars 112, 20,123 sec; Walls 9 + Infirmary 7; power 9,700 | 749K/749K/233K, 5:35:23 for both times; same requirements | Rounded resources; time and requirements agree |
| Lv11 | 1,853,000/1,853,000/601,800, Stars 142, 26,043 sec; Research Lab 7 + Training Grounds 10; power 12,000 | 1.9M/1.9M/602K; Build 6:53:23; Original 7:14:03 | Resources rounded; Original agrees; Build is 1,240 sec lower |
| Lv20 | 60.03M/60.03M/18.41M, Stars 247, 430,820 sec; Research Lab 19 + Alliance Hall 18 + Farm 10; power 67,300 | 57.0M/57.0M/17.5M; Build 3d11h41m13s; Original 4d23h40m20s | Requirements and Original agree; displayed resources about 5% lower and Build about 30% lower |
| Lv26 | 386.8M/386.8M/123.5M, Stars 304, 2,676,737 sec; Research Lab 25 + Warrior Statue 25 + Antitoxin Workshop 13 | 362M/362M/115M; Build 19d22h9m35s; Original 30d23h32m17s | Requirements and Original agree; resources about 6-7% lower and Build about 36% lower |
| Lv29 | 1.047B/1.047B/316.4M, Stars 326, 6,820,324 sec; Research Lab 28 + Alliance Hall 28 + Herb Garden 13 | 995M/995M/301M; Build 37d12h00m59s; Original 78d22h32m04s | Requirements and Original agree; resources about 5% lower and Build about 52% lower |
| Lv30 | 1.356B/1.356B/441.3M, Stars 326, 8,866,423 sec; Research Lab 29 + Training Grounds 29 + Antitoxin Workshop 15; power 384,300 | 1.3B/1.3B/415M; Build 47d22h53m09s; Original 102d14h53m43s | Requirements and Original agree; resources lower/rounded and Build about 53% lower |

LastAsylumPlague does not expose Sanctuary power, while LastAsylumDatabase and Satori agree on it for every sampled Sanctuary row.

## 8. Other exact disagreements

The strongest non-Sanctuary conflict is Soldier's Rest:

- LastAsylumDatabase declares max Lv35 and supplies 35 rows; Satori stops at Lv30.
- LastAsylumDatabase gives source `power` values 100, 200, ... 3,000 through Lv30 and no power on Lv31-Lv35; its catalog `power_max` is 3,000.
- Satori gives Soldier's Rest power 500 at Lv1, 1,000 at Lv2, and 260,000 at Lv30.
- Costs and times at Soldier's Rest Lv30 agree exactly: grain 717,840,000, timber 717,840,000, herb 119,640,000, and 6,649,817 seconds.
- LastAsylumDatabase provides Lv31-Lv35 costs and times but leaves prerequisites and power absent; those five rows require special validation before canonical promotion.

Residence also differs semantically:

- LastAsylumDatabase includes Lv1 with zero resources, 2,000 seconds, and power 100, then Lv2 with 480/360 resources, 2 seconds, and no per-level power field.
- Satori omits Lv1 and gives Lv2 the same 480/360 resources and 2 seconds, with power 100.

These are reasons to retain raw source assertions and validate schema exceptions rather than forcing every building through an assumed uniform level model.

## 9. Source comparison and trust assessment

| Criterion | LastAsylumDatabase | SatoriMeta | LastAsylumPlague |
| --- | --- | --- | --- |
| Structured-data quality | High: compiled objects | High: typed embedded props | Medium: HTML table cells |
| Completeness | Highest: 46 / 980 advertised levels | High: 46 / 974 levels | Low: Sanctuary only |
| Prerequisite coverage | Broad explicit text | Best normalized building edges; unresolved counts | Sanctuary text only |
| Unlock coverage | None found | None found | Explicit Sanctuary unlock text |
| Provenance/auditability | High retrieval auditability; upstream game provenance unpublished | Page/hash auditable; ultimate dataset origin unpublished | Page/post metadata auditable; account context unclear |
| Respectful retrieval | Easy static HTTP; hashed module map | Easy single-page static HTTP | Easy static HTML |
| Apparent freshness | Bundle Last-Modified 2026-07-20 | No visible dataset update date found | Post modified 2026-07-19 |
| Fragility | Medium: asset hashes change per deploy | Medium-high: Astro serialization may change | Medium: table wording/layout may change |
| Canonical suitability | Best available for identity and base level facts | Secondary for normalized prerequisites and corroboration | Fallback for explicit unlocks/diamonds only |

Recommended source-confidence tiers:

1. `PRIMARY_STRUCTURED_SOURCE` — LastAsylumDatabase assertions that pass strict validation.
2. `SECONDARY_STRUCTURED_SOURCE` — SatoriMeta assertions, especially normalized prerequisite edges.
3. `COMMUNITY_GUIDE` — LastAsylumPlague text/table assertions.
4. `MANUAL_GAME_VERIFICATION` — versioned evidence captured directly from the game, with account modifiers and game version recorded. This can supersede a public-source assertion only by creating a new assertion/status, never by deleting the earlier evidence.

These are factual-source tiers, not strategic-confidence scores.

## 10. Recommended future factual model

The model should keep factual game data separate from calculations, strategic judgment, and player-specific recommendations.

### BuildingNode

```text
id                         local database identity
canonical_slug             stable local slug
name                       canonical display name
description                nullable
max_level                  source-backed assertion, not silently merged
image_path                 nullable
is_main                    nullable source property
created_at / updated_at
```

Source-specific IDs, slugs, names, and aliases should live in a mapping/assertion table rather than assuming that one public site's numeric ID is universal.

### BuildingLevel

```text
id
building_node_id
level
source_power_value         nullable; preserve before assigning semantics
base_time_seconds          nullable
source_formatted_time      nullable
created_at / updated_at
unique(building_node_id, level) for a resolved canonical claim
```

Resource amounts should use normalized child rows, for example `BuildingLevelResource(level_id, resource_kind, amount, semantic_role)`, because the sources expose grain/farms, timber/lumber, herb, Stars, Diamonds, and reward aliases with uncertain semantics. `semantic_role` should distinguish `upgrade_cost`, `displayed_adjusted_cost`, `reward`, and `unknown_source_role`. The original source field name must remain in provenance.

Do not store cumulative calculator totals as level facts. They belong to the calculated-efficiency layer and should be recomputed from atomic levels.

### BuildingRequirement

Requirements should be grouped by target-level/source observation so simultaneous all-of conditions are preserved:

```text
BuildingRequirementSet
  id
  target_building_level_id
  source_observation_id
  logic                      ALL when explicitly supported
  source_text                nullable
  unresolved_condition_count default 0

BuildingRequirement
  id
  requirement_set_id
  requirement_type           BUILDING_LEVEL or EXTERNAL_CONDITION
  required_building_node_id  nullable
  required_level             nullable
  external_identifier        nullable
  external_name              nullable
  source_order               nullable
  resolution_status
```

Only explicit source facts should produce requirement rows. Satori's unnamed condition count belongs on the set until another source explicitly names each condition. `cost_stars` remains a cost assertion; it must not automatically generate `EXTERNAL_CONDITION: STAR`.

This structure supports multiple simultaneous building requirements, later research/tree/territory/feature requirement types, and auditable unresolved text without inventing a target.

### BuildingUnlock

An unlock table is justified because LastAsylumPlague explicitly supplies Sanctuary unlock cells:

```text
id
source_building_level_id
unlock_type                 BUILDING, RESEARCH_TREE, TROOP_TIER, FEATURE, OTHER
target_building_node_id     nullable
external_identifier        nullable
source_name                 exact source text
normalized_name             nullable until reviewed
source_observation_id
resolution_status
```

Do not create unlock rows by reversing prerequisite edges in the factual layer. A reverse edge such as “upgrading X unblocks Y” is a calculated graph result and should be labeled as such. No research-tree gate discovered here should be inserted into the current research facts.

## 11. Provenance and conflict strategy

Use immutable retrieval observations plus per-field assertions:

```text
Source
  id, name, tier, homepage

SourceObservation
  id, source_id, requested_url, final_url, retrieved_at,
  content_sha256, content_type, etag, last_modified

FactAssertion
  id, entity_type, entity_key, field_name,
  typed_value, source_field_name, source_observation_id,
  extraction_method, verification_status, notes
```

For relationship facts, the requirement/unlock row itself should point to the observation and retain the original text. A derived consensus view can classify assertions as:

```text
single_source
agreed_by_multiple_sources
conflicting
manually_verified
superseded_for_current_game_version
```

Conflict resolution must be explicit and field-specific. For example, Sanctuary Lv20 `Original Time` can agree with LastAsylumDatabase/Satori while the same community row's `Build Time` remains a separate adjusted assertion. Soldier's Rest Lv30 power must remain conflicting. Retrieval date, content hash, source tier, and manual evidence should inform a selected canonical view without deleting alternatives.

## 12. Static extraction and browser requirement

Ordinary HTTP plus static parsing is sufficient for all data found in this reconnaissance:

- LastAsylumDatabase: parse the main bundle's catalog/import map and the selected ESM module text.
- LastAsylumPlague: parse the server-rendered HTML table or the HTML inside the REST response.
- SatoriMeta: HTML-decode and statically decode the Astro props; inspect the calculator bundle as text for calculation semantics.

Browser automation and Playwright are **not necessary** for a production building ingestor based on the current deployments. A browser could be useful later for human visual validation, but it would add no source facts discovered here.

## 13. Important unknowns

- The sites do not publish authoritative game-version provenance for individual values.
- SatoriMeta's ultimate upstream dataset and update schedule are unknown.
- LastAsylumDatabase's compatibility aliases need semantic confirmation, especially Stars and antitoxin/EXP.
- Soldier's Rest power, Lv31-Lv35 completeness, and Residence Lv1 semantics conflict or vary by source.
- Satori's 31 unresolved conditions are counted but unnamed. Their exact types cannot be inferred.
- LastAsylumPlague's resource modifiers and the account/build used for `Build Time` are not disclosed.
- Unlock coverage outside Sanctuary is unknown; no complete public structured unlock corpus was found.
- LastAsylumDatabase prerequisite strings are explicit but require a reviewed parser and alias resolution; punctuation and names may vary outside the bounded sample.
- Some buildings may have special rules that violate ordinary cumulative-power or upgrade-level assumptions.
- No source inspected here establishes building-to-research-tree gates. Such facts need a separate explicit source or manual verification.

## 14. Recommended next implementation boundary

The next safe milestone is a production **building schema and ingestion design review**, followed by a strict LastAsylumDatabase building parser that stores raw observations and rejects unknown shapes. Satori prerequisite ingestion should be a separate adapter and comparison stage. LastAsylumPlague unlocks should remain a small manually reviewed fallback import. None should mutate the existing research facts or generate recommendations during that milestone.

