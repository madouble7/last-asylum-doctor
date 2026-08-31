# Research Source Manifest

**Status:** Draft canonical standard

**Scope:** Every Last Asylum research tree and every future research export captured for Doctor's Companion.
**Authority:** Facts remain source observations until they pass normalization and review. A calculator result is never a replacement for a source fact.

This manifest makes a research record reproducible: another reviewer must be
able to identify the exact source bytes, the game/account context in which they
were observed, the normalization applied, and the assumptions used by any
derived recommendation.

## 1. ARCHITECT four-layer evidence architecture

The repository's four application layers remain separate. Capture, parsing,
normalization, and reconciliation are evidence controls inside (and attached
to) the factual layer; they do not constitute additional decision layers.

| Layer | Purpose | Required output | Prohibited shortcut |
| --- | --- | --- | --- |
| **1. Factual game data** | Preserve verified observations and their applicability. | Immutable captures plus normalized research nodes, levels, costs, effects, prerequisites, and building gates. | Reconstructing a source from a paraphrase, or filling a missing fact from a different source. |
| **2. Calculated efficiency** | Compute transparent totals and comparisons from facts. | Versioned cost/time roll-ups, marginal values, and calculator inputs/outputs linked to fact IDs. | Hiding assumptions or promoting a calculated value to a game fact. |
| **3. Strategic judgment** | State explicit priorities, trade-offs, and uncertainty. | Attributed strategy rules/claims with conditions and corroboration status. | Presenting a player's recommendation as an objective mechanic. |
| **4. Player-specific recommendations** | Apply facts, calculations, and strategy to one account. | Recommendation, current state, target, and rationale with freshness and scope. | Inventing missing data or changing shared facts to fit one player. |

Layers are linked by IDs. A Layer-4 recommendation must be traceable through
its Layer-2 calculations and Layer-3 rules to Layer-1 facts and at least one
hashed capture. If that chain is incomplete, the result is labelled
`UNVERIFIED` and is not presented as a game fact.

## 2. Research-tree registry

The registry currently covers these 18 tree identifiers. A new tree requires a
manifest entry before ingestion; an unknown tree must fail validation rather
than be folded into a nearby category.

| `tree_slug` | Display name |
| --- | --- |
| `alliance-duel` | Alliance Duel |
| `caravan-transport` | Caravan Transport |
| `defensive-tactics` | Defensive Tactics |
| `development` | Development |
| `economy` | Economy |
| `elite-troop` | Elite Troop |
| `full-development` | Full Development |
| `hero` | Hero |
| `offensive-tactics` | Offensive Tactics |
| `prosperous-economy` | Prosperous Economy |
| `ranger-mastery` | Ranger Mastery |
| `soldier` | Soldier |
| `squad-1` | Squad 1 |
| `squad-2` | Squad 2 |
| `squad-3` | Squad 3 |
| `squad-4` | Squad 4 |
| `warlock-mastery` | Warlock Mastery |
| `warrior-mastery` | Warrior Mastery |

The source spelling is retained in `tree`; `tree_slug` is the stable mechanical
identifier. Display names are not used as foreign keys.

## 3. Branch-capture provenance contract

A **branch capture** is one bounded export or observation for one research
branch (`tree_slug` plus source locator). A capture may contain many nodes, but
each node and level must retain its `capture_id`.

The following metadata is mandatory. When the source does not provide a value,
record `unknown` (or `null` where the field is nullable) and explain why; never
omit the field.

| Field | Definition and rule |
| --- | --- |
| `capture_id` | Stable unique ID for this capture; never reused. |
| `source_id` | Stable ID for the originating site, export, video, screenshot set, or player observation. |
| `branch_slug` | Registry identifier for the captured research branch. |
| `source_url` | Original public URL, file URI, or declared in-game evidence locator. Preserve query parameters. |
| `final_url` | URL after redirects, when HTTP retrieval is used. |
| `source_asset_url` | Exact JSON/ESM/API asset when a page points to a separate data asset; otherwise `null`. |
| `retrieved_at_utc` | UTC ISO-8601 timestamp of byte retrieval or observation. Local time alone is invalid. |
| `raw_sha256` | Lowercase SHA-256 of the exact response bytes or canonical image/PDF bytes. Hash the bytes before parsing. |
| `content_type` / `http_status` | Response metadata when applicable; preserve redirects and failures. |
| `etag` / `last_modified` | Response validators when supplied; otherwise `null`. |
| `retrieval_method` | For example `anonymous_http`, `authorized_export`, `manual_screenshot`, or `manual_ui_observation`. |
| `auth_state` | One of `anonymous`, `authenticated_authorized`, `user_provided_export`, or `unknown`. Store no cookies, tokens, or credentials. |
| `server_scope` | Server/kingdom number or an explicit `unknown`/`not_applicable`; do not infer it from a URL or channel. |
| `account_scope` | Account identifier or safe description such as `reviewer-owned-S283`; avoid personal secrets. |
| `region` / `language` | Region and locale visible in the source or export, or `unknown`. |
| `sanctuary_level_observed` | Player's visible current Sanctuary level at capture time, not a requirement. |
| `institute_level_observed` | Player's visible current Institute level at capture time, not a requirement. |
| `season_or_era` | Season, Era, event phase, or `not_stated`. |
| `client_build` | Visible game version/build when available. |
| `source_published_at` / `source_updated_at` | Publisher timestamps, kept separate from retrieval time. |
| `parser_version` | Parser/OCR/extraction version and configuration. Manual captures use the capture protocol version. |
| `row_count` / `node_count` / `level_count` | Counts observed before normalization; useful for completeness checks. |
| `completeness` | `complete_branch`, `partial_branch`, or `single_node`; include the expected range when partial. |
| `evidence_locator` | JSON path, source record ID, page anchor, screenshot filename/region, or video timestamp. |
| `reviewer` / `reviewed_at_utc` | Human reviewer and review timestamp for promoted facts. |
| `notes` | Explicit caveats, access limitations, OCR uncertainty, or unresolved identity questions. |

`source_url`, `retrieved_at_utc`, `server_scope`, `account_scope`, `auth_state`,
and `raw_sha256` are the minimum provenance gate. A record failing that gate
may remain a research lead, but cannot be promoted to a canonical fact.

## 4. Export and capture requirements

1. Capture the complete response bytes before parsing. Preserve the final URL,
   request parameters, status, content type, and relevant response validators.
2. Store the raw object outside tracked canonical datasets (content-addressed
   by `raw_sha256`) with a sidecar manifest containing the fields above. Never
   overwrite an earlier hash; a recapture is a new snapshot.
3. For screenshots, PDFs, or OCR, hash the original artifact, retain the
   screenshot/page/region locator, and record the OCR engine and version. OCR
   text is an extraction aid, not independent evidence.
4. Preserve source IDs, labels, amount text, and visible formatting alongside
   normalized values. Do not discard unknown fields until a schema review has
   classified them.
5. Record branch completeness explicitly. A page showing only levels 1–10 is
   not evidence that level 10 is the branch maximum.
6. Use sequential, authorized retrieval that respects robots, rate limits,
   access controls, and source terms. `auth_state` describes access; it never
   authorizes bypassing a control.
7. Re-run schema and invariant validation after every export. Unknown fields,
   duplicate levels, non-contiguous levels, invalid units, or unresolved IDs
   fail the capture rather than being silently dropped.

## 5. Canonical data dictionary

### `research_node` (one node in a tree)

| Field | Type | Meaning |
| --- | --- | --- |
| `research_id` | string | Source node ID, preserved exactly. |
| `slug` | string | Stable source/canonical slug used for joins. |
| `name` | string | Visible node name. |
| `tree` / `tree_slug` | string | Source tree label and registry identifier. |
| `effect_raw` | string | Source description, unedited. |
| `effect_structured` | nullable object | Structured effect only when directly supported; otherwise `null`. |
| `max_level` | integer | Declared maximum; must agree with captured levels when completeness is `complete_branch`. |
| `tech_type` / `image` / `position` | nullable | Source presentation metadata, not decision facts. |
| `capture_id` | ID | Layer-1 provenance link. |

### `research_level` (one level of one node)

| Field | Type | Meaning |
| --- | --- | --- |
| `research_id` / `slug` | string | Must match the parent node. |
| `level` | integer | One-based level; complete branches must be contiguous `1..max_level`. |
| `source_record_id` | string/integer | Original row ID when supplied. |
| `power` | integer | Exact source power value; do not replace with rounded display text. |
| `time_source` | string | Original time text or label. |
| `time_seconds` | integer | Lossless source duration when supplied. |
| `time_minutes` | integer | Decision-facing duration in whole minutes; see unit rules below. |
| `time_rounding` | enum | `exact`, `ceil_for_completion`, or `unknown`; required when seconds are not minute-aligned. |
| `capture_id` | ID | Provenance link for this level. |

### `research_cost` (one resource requirement at one level)

| Field | Type | Meaning |
| --- | --- | --- |
| `resource_key` | string | Mechanical identifier derived from the source label; do not imply game semantics. |
| `source_label` | string | Original resource name. |
| `item_id` | nullable string | Source item ID when supplied. |
| `amount_raw` | integer/decimal | Exact source amount, lossless. |
| `amount_millions` | decimal | `amount_raw / 1,000,000` for resources; derived, never a replacement for `amount_raw`. |
| `unit_class` | enum | `resource`, `item`, `scroll`, `currency`, or `unknown`. |
| `source_amount` | nullable string | Original formatted amount such as `15.0K`. |
| `capture_id` | ID | Provenance link. |

### `research_prerequisite` (explicit dependency edge)

| Field | Type | Meaning |
| --- | --- | --- |
| `research_id` | string | Node being unlocked. |
| `prerequisite_research_id` | string | Required predecessor node. |
| `required_level` | integer | Required predecessor level, when stated. |
| `edge_type` | enum | `requires`, `alternative`, `same_branch`, or `unknown`. |
| `alternative_group` | nullable string | Groups OR alternatives without inventing an AND edge. |
| `condition_text` | string | Exact source wording when available. |
| `evidence_locator` / `capture_id` | ID/locator | Proof for this edge. |

Ordering on a screen, proximity in a table, or a shared tree label is not a
prerequisite. Unresolved endpoints are retained as flagged edges, not guessed.

### Layer-3 and Layer-4 linkage records

These records keep interpretation and personalization out of the factual
tables while preserving a complete audit trail.

| Record | Required fields | Rule |
| --- | --- | --- |
| `research_claim` | `claim_id`, `claim_type`, `statement`, `applicability`, `status`, `evidence_ids` | `claim_type` is `FACT`, `STRATEGY`, `FUTURE_WARNING`, or `VERSION_SIGNAL`; strategy is attributed, not rewritten as a mechanic. |
| `research_conflict` | `conflict_id`, `fact_ids`, `scope`, `resolution_status`, `review_notes` | Keep incompatible observations linked and scoped; never average them into a new fact. |
| `calculation_run` | `run_id`, `model_version`, `input_fact_ids`, `assumptions`, `generated_at_utc`, `output_unit` | Reproducible Layer-2 output; assumptions and freshness are mandatory. |
| `recommendation` | `recommendation_id`, `account_scope`, `current_value_roles`, `target_value_roles`, `calculation_run_id`, `strategy_claim_ids`, `status` | Layer-4 advice must identify the player state and target separately and must not mutate shared research facts. |

### `research_building_gate` (availability constraint)

| Field | Type | Meaning |
| --- | --- | --- |
| `research_id` | string | Node or branch gated by the building. |
| `building_key` | enum | `sanctuary`, `institute`, or a separately identified building. |
| `required_level` | nullable integer | Explicit required building level. |
| `gate_type` | enum | `availability`, `queue`, `cost_modifier`, or `unknown`. |
| `scope` | string | Server/build/season scope for the gate. |
| `condition_text` | string | Exact wording or a concise transcription. |
| `capture_id` / `evidence_locator` | ID/locator | Proof and location. |

## 6. Unit and normalization rules

- **Resources:** keep `amount_raw` in the source's smallest stated unit and
  expose `amount_millions` for canonical comparisons and reports. Do not round
  before storage; display at sufficient precision to reproduce the raw value.
  “Millions” applies to Farms, Lumber, Herbs, and other bulk resources, not to
  Study Scrolls, badges, shards, or tickets.
- **Time:** retain source text and exact seconds. The planning field is integer
  `time_minutes`; use exact division when possible and `ceil_for_completion`
  when a partial minute must still be waited. Never silently truncate.
- **Power and levels:** integers. Percent effects are percentage points (for
  example, `5.0%`), not an unlabelled decimal fraction.
- **Identity:** IDs are strings, case-preserved in the raw layer. Canonical
  aliases are separate rows; a similar name never proves identity.
- **Null versus zero:** `null` means not supplied/unknown; `0` means the source
  explicitly supplied zero.
- **Costs and effects:** retain the original label and amount beside every
  normalized value. A missing cost is not a free cost.
- **Conflicts:** preserve each observation and link them through a conflict or
  supersession record. Do not average incompatible snapshots.

## 7. Sanctuary and Institute level gates

1. Store Sanctuary and Institute requirements as separate
   `research_building_gate` rows. A Sanctuary requirement must never be copied
   into `institute_level_required`, or vice versa.
2. A gate is factual only when the source explicitly states it or shows a
   lock/requirement in a dated UI capture. Do not infer a gate from node order,
   the user's current level, or a calculator's target.
3. Keep `required_level` (what the game requires) separate from
   `sanctuary_level_observed`/`institute_level_observed` (what the account had
   at capture time). Both may be present and they answer different questions.
4. Attach server, season/era, client build, and capture provenance to every
   gate. If sources disagree, retain both scoped observations and mark the
   conflict; do not choose the higher or lower level without evidence.
5. A gate controls availability or eligibility. It is not a research cost and
   must not be included in resource totals unless a source explicitly says so.
6. A gate applying to an entire branch may be represented at branch scope only
   when the source says it applies to the branch; otherwise attach it to the
   individual node(s) shown.

## 8. User-entered levels and calculator targets

Every level used by a UI, import, or model carries a `value_role`:

| `value_role` | Meaning |
| --- | --- |
| `SOURCE_OBSERVED_LEVEL` | Level visible in a source export or UI capture. |
| `SOURCE_REQUIRED_LEVEL` | Level stated as a prerequisite or building gate. |
| `USER_ENTERED_CURRENT` | Player-provided current level; record entry timestamp and account scope. |
| `CALCULATOR_TARGET` | Desired endpoint selected by the user or scenario. |
| `CALCULATOR_RESULT` | A derived level/total produced by a model, never a source fact. |

Rules:

- Never store a bare “current level” or “target level” without `value_role`.
- User-entered values do not alter source observations, prerequisite edges, or
  maximum levels. A screenshot can corroborate a user value, but does not make
  a target factual.
- Calculator targets require a reason or scenario label (for example,
  `unlock_t10` or `next_alliance_duel`) and the source fact IDs used to compute
  them. Assumptions such as income, buffs, or completion date are explicit.
- A target may exceed the currently captured branch only as a labelled forecast;
  it must not create synthetic levels or costs.
- Recommendations display current input, target, scope, and freshness together
  so a user can distinguish “you have level 3” from “the model targets level 7.”

## 9. Promotion and validation checklist

A branch is promotable to the canonical research corpus only when:

- all mandatory provenance fields are present or explicitly marked unknown;
- the raw hash and evidence locator resolve to the retained capture;
- node IDs, tree identifiers, and level ranges validate;
- levels are contiguous and costs are non-negative with valid unit classes;
- every prerequisite and building gate is explicitly evidenced or flagged
  unresolved;
- source amounts, exact times, and original labels are retained beside derived
  Millions/minute fields;
- server/account/build/season applicability is visible to the reviewer; and
- conflicts, partial coverage, and user/calculator values are not presented as
  settled facts.

The manifest is a provenance contract, not a requirement to ingest every source
immediately. A partial or future-system capture is valuable when its limits are
recorded precisely.

## 10. Example sidecar (illustrative metadata only)

```yaml
capture_id: rc-2026-08-31-0001
source_id: last-asylum-database
branch_slug: elite-troop
source_url: https://example.invalid/science/def-boost-iii
source_asset_url: https://example.invalid/assets/def-boost-iii.json
retrieved_at_utc: 2026-08-31T15:00:00Z
raw_sha256: <sha256-of-exact-bytes>
retrieval_method: anonymous_http
auth_state: anonymous
server_scope: unknown
account_scope: not_applicable
sanctuary_level_observed: null
institute_level_observed: null
season_or_era: not_stated
client_build: unknown
completeness: single_node
node_count: 1
level_count: 10
parser_version: science-esm-v1
reviewer: scout
```

The example intentionally leaves uncertain context explicit. Real captures
must replace placeholders and add response metadata, evidence locators, and
the normalized node/level/cost records linked by `capture_id`.
