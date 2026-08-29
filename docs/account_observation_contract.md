# Account Observation Contract v0.1

## Purpose and boundary

This is the smallest interchange contract between the future PROBE Shadow
Observer and the Companion planner. It is an evidence-first JSON/JSONL
contract, not a database schema.

The contract has three layers:

1. **RAW OBSERVATION** is one captured screen and what was directly extracted
   from it. It is immutable evidence, including ambiguous and failed extracts.
2. **NORMALIZED FACT** is one interpreted datum, with an explicit unit and
   entity identity. It points back to the raw observation and is the unit of
   validation.
3. **ACCOUNT SNAPSHOT** is a materialized latest-known view made only from
   accepted (`PASS`) facts. It is the input boundary for calculations.

No event bus, broker, framework, or schema migration is implied. A future
implementation may append JSONL records and build a snapshot in memory or in a
new persistence layer.

## Common conventions

- JSON names use `snake_case`.
- Timestamps are ISO 8601 UTC strings, for example
  `2026-08-29T14:03:22Z`.
- Counts, levels, seconds, and item amounts are non-negative integers. Do not
  encode a rounded display value as an exact amount.
- Unknown is represented by omission, not by zero. `null` is allowed when the
  screen explicitly shows an empty/unavailable value and that distinction is
  useful.
- `contract_version` is required on every record and starts at `0.1`.
- `record_type` is one of `raw_observation`, `normalized_fact`, or
  `account_snapshot`.
- Identifiers such as `grain`, `sanctuary`, `t8`, and a research `slug` are
  mechanical identities, not claims that source vocabulary has been proven.

## RAW OBSERVATION

Recommended JSONL record: one record per captured screen (or one atomic screen
state when a capture is split by the observer).

```json
{
  "contract_version": "0.1",
  "record_type": "raw_observation",
  "observation_id": "obs-20260829-00017",
  "account_id": "local-account-1",
  "observed_at": "2026-08-29T14:03:22Z",
  "source": {
    "type": "bluestacks_screen",
    "server": "283",
    "package": "com.example.game",
    "client_version": "1.0.97",
    "client_version_code": 97
  },
  "evidence": {
    "sha256": "<sha256-of-captured-screen>",
    "uri": "ignored-local-evidence/screenshot.png",
    "capture_method": "passive_frame_capture"
  },
  "screen": {
    "state": "resource_panel",
    "screen_fingerprint": "<optional-fingerprint>"
  },
  "claims": [
    {
      "claim_id": "obs-20260829-00017:grain",
      "field": "resource_balance",
      "entity": {"kind": "resource", "id": "grain"},
      "raw_value": "252.0M",
      "extraction_method": "ocr",
      "status": "PASS",
      "review_reason": null
    }
  ]
}
```

Required raw fields are `contract_version`, `record_type`, `observation_id`,
`observed_at`, `source.type`, `source.server`, `evidence.sha256`,
`evidence.capture_method`, and `claims`. `source.package`, client version
fields, evidence URI, screen state, fingerprint, and `account_id` are optional
when unavailable. A claim requires `claim_id`, `field`, `raw_value`,
`extraction_method`, and `status`; entity identity is required when the field
has an entity (resource, building, troop, or research node).

The raw value is exactly what was read or extracted, including display suffixes,
OCR text, and a `null` only when the screen explicitly represents null. The raw
record must not be rewritten after capture. A later correction is another
record linked through a fact or review reference.

## NORMALIZED FACT

Recommended JSONL record: one record per interpreted datum. It may be produced
only after validation of the corresponding claim.

```json
{
  "contract_version": "0.1",
  "record_type": "normalized_fact",
  "fact_id": "fact-20260829-00017-grain",
  "observation_id": "obs-20260829-00017",
  "claim_id": "obs-20260829-00017:grain",
  "observed_at": "2026-08-29T14:03:22Z",
  "field": "resource_balance",
  "entity": {"kind": "resource", "id": "grain"},
  "raw_value": "252.0M",
  "normalized_value": 252000000,
  "unit": "items",
  "extraction_method": "ocr",
  "status": "PASS",
  "provenance": {
    "source_type": "bluestacks_screen",
    "server": "283",
    "client_version": "1.0.97",
    "client_version_code": 97,
    "evidence_sha256": "<sha256-of-captured-screen>"
  },
  "supersedes_fact_id": null,
  "review_reason": null
}
```

Required fields are `contract_version`, `record_type`, `fact_id`,
`observation_id`, `claim_id`, `observed_at`, `field`, `raw_value`,
`normalized_value`, `unit`, `status`, and `provenance` with at least
`source_type`, `server`, and `evidence_sha256`. `entity` is required for
entity-scoped fields. `extraction_method`, client metadata, review reason, and
`supersedes_fact_id` are optional.

A fact is `PASS` only when identity, unit, parsing, and plausibility checks
succeed. `REVIEW` means the interpretation is retained for human or later
validation but is not canonical. `FAIL` means extraction or normalization
failed; preserve the raw value and reason, but never use it in a snapshot.
Status is about this datum, not about the whole screen.

Values should use these field/entity shapes:

| Datum | `field` | Entity and normalized value |
| --- | --- | --- |
| Grain, Timber, Herbs, Antitoxin | `resource_balance` | `resource` / integer `items` |
| Study Scrolls | `item_balance` | `item` / integer `items` |
| Construction, training, research, universal speedups | `speedup_balance` | `speedup` id `construction`, `training`, `research`, or `universal`; integer `seconds` (retain original item unit in `raw_value`) |
| Sanctuary level | `building_level` | `building` id `sanctuary` / integer `level` |
| Current construction | `construction_state` | `building` / object with `target_level` and `remaining_seconds`; omit unknown members |
| Research Lab level | `building_level` | `building` id `research_lab` / integer `level` |
| Training Grounds level | `building_level` | `building` id `training_grounds` / integer `level` |
| Troops by tier and type | `troop_count` | `troop` with `tier` and stable `type` / integer `troops` |
| Wounded/recoverable troops | `troop_count` | `troop` id `wounded` or `recoverable` / integer `troops` |
| Current research node level | `research_level` | `research_node` with stable `slug` / integer `level` |
| Visible research effect | `research_effect` | `research_node` / source-preserving text or structured value |
| Visible research prerequisite | `research_prerequisite` | `research_node` / source-preserving prerequisite text or structured value |

For troop type and research identity, use a source identifier when one is
visible. Do not silently map an unknown label to a known type or research slug;
use `status: REVIEW` until the identity is validated.

## ACCOUNT SNAPSHOT

A snapshot is a replaceable materialized view, not a second source of truth.
It contains only the latest compatible `PASS` fact for each field/entity key.

```json
{
  "contract_version": "0.1",
  "record_type": "account_snapshot",
  "snapshot_id": "snap-20260829-00018",
  "account_id": "local-account-1",
  "as_of": "2026-08-29T14:03:22Z",
  "generated_at": "2026-08-29T14:04:01Z",
  "source_fact_ids": ["fact-20260829-00017-grain"],
  "resources": {
    "grain": {"value": 252000000, "unit": "items", "fact_id": "fact-20260829-00017-grain"}
  },
  "items": {
    "study_scroll": {"value": 120, "unit": "items", "fact_id": "<fact-id>"}
  },
  "speedups": {
    "construction": {"seconds": 10800, "fact_id": "<fact-id>"},
    "training": {"seconds": 3600, "fact_id": "<fact-id>"},
    "research": {"seconds": 0, "fact_id": "<fact-id>"},
    "universal": {"seconds": 1800, "fact_id": "<fact-id>"}
  },
  "buildings": {
    "sanctuary": {"level": 27, "fact_id": "<fact-id>"},
    "research_lab": {"level": 27, "fact_id": "<fact-id>"},
    "training_grounds": {"level": 27, "fact_id": "<fact-id>"}
  },
  "current_construction": {"target_level": 27, "remaining_seconds": 1200000, "fact_id": "<fact-id>"},
  "troops": {
    "counts": [{"tier": "t8", "type": "<validated-type>", "troops": 125000, "fact_id": "<fact-id>"}],
    "wounded": {"troops": 0, "fact_id": "<fact-id>"},
    "recoverable": {"troops": 0, "fact_id": "<fact-id>"}
  },
  "research": {
    "levels": [{"slug": "<validated-slug>", "level": 3, "fact_id": "<fact-id>"}],
    "effects": [{"slug": "<validated-slug>", "value": "<source-preserving-value>", "fact_id": "<fact-id>"}],
    "prerequisites": [{"slug": "<validated-slug>", "value": "<source-preserving-value>", "fact_id": "<fact-id>"}]
  }
}
```

Required snapshot fields are `contract_version`, `record_type`, `snapshot_id`,
`as_of`, `generated_at`, and `source_fact_ids`. All domain sections are
optional, and individual members are present only when a current `PASS` fact
exists. Every materialized value carries its `fact_id`; this makes the
snapshot auditable without embedding the full evidence repeatedly.

## Update and supersession rules

1. Append every raw observation and every resulting normalized fact. Never
   delete or rewrite historical evidence.
2. Build a candidate snapshot by field/entity key, for example
   `resource_balance/resource:grain` or
   `troop_count/troop:t8:<type>`.
3. Consider only `PASS` facts with compatible identity, unit, server scope, and
   client context. `REVIEW` and `FAIL` remain searchable evidence but cannot
   create or replace a snapshot value.
4. For a key, a newer valid observation replaces the prior snapshot value and
   may set `supersedes_fact_id` to the prior fact. “Newer” is determined by
   `observed_at`, with ingestion order used only as a deterministic tie-breaker.
5. If a newer observation is `REVIEW`, `FAIL`, or ambiguous, retain the prior
   `PASS` value and record the newer result as evidence. Do not erase a known
   value merely because a later screen could not read it.
6. If a PASS fact explicitly proves that a value is zero, it replaces the prior
   value with zero. Absence from a screen does not prove zero.
7. A snapshot’s `as_of` is the newest observation time represented in it, not
   necessarily the time it was generated. Snapshot regeneration must be
   deterministic from retained facts.

A superseded fact is historical, not invalid. `supersedes_fact_id` expresses
lineage; it does not remove the older record. A future implementation may also
add `superseded_by_fact_id` when convenient, but v0.1 does not require a reverse
index.

## Provenance and review policy

Every factual datum must be traceable through `fact_id` -> `claim_id` ->
`observation_id` -> evidence hash. At minimum retain observation time, source
type, server, evidence SHA-256, extraction method, raw value, normalized value,
and status. Record package and client version/code whenever detected. Keep
source scope attached to the fact; do not promote a Server 283 observation to
all servers or versions.

Typical `REVIEW` reasons include low OCR confidence, a clipped number, an
unrecognized troop or research identity, conflicting visible values, or a
client/server mismatch. Typical `FAIL` reasons include an invalid number,
missing required identity, impossible unit conversion, or corrupted evidence.
The raw observation and normalized attempted fact remain available for audit,
reprocessing, and human review. Only `PASS` facts enter the canonical snapshot;
planner output should surface missing inputs rather than silently use REVIEW or
FAIL data.

## Recovery Planner compatibility

The current Recovery Planner accepts a flat JSON mapping and ignores unknown
additional keys. A future adapter should therefore read this snapshot and
produce the existing planner shape without changing planner calculations:

- `resources.{grain,timber,herbs,antitoxin}.value` -> the four required resource
  integers;
- `current_construction.remaining_seconds` for the active Sanctuary
  construction -> `sanctuary_27_remaining_seconds` when the target is the
  planner’s known Sanctuary milestone;
- `speedups.construction/training/universal.seconds` -> integer minutes using
  an explicit conversion policy, with any remainder rejected or retained for a
  later planner API rather than silently rounded;
- sum or select troop facts only when the requested tier/type is explicit, then
  map to `current_t8_troops` and `recoverable_or_wounded_troops`;
- keep `desired_combat_ready_troops` player intent, not an observed fact.

Missing or REVIEW/FAIL values must remain missing and be reported as a planner
input limitation. Research speedups, building levels, research facts, and
Study Scrolls can be carried in the snapshot before the Recovery Planner uses
them. The adapter should preserve `fact_id`/provenance alongside its input or
report so calculated results remain distinguishable from account facts.

This contract does not change the planner’s existing confirmed milestone
provenance, resource vocabulary, or strategy limitations. It also does not
claim troop costs, training times, research dependencies, or economic
optimality that have not been validated.

## Compatibility and evolution

Readers must ignore unknown fields and preserve records they do not understand.
Writers must continue emitting the required fields and must not reuse a field
name with a different unit or identity meaning. Additive fields should be
preferred in v0.x. A breaking change, such as changing seconds to minutes or
changing the identity of a resource, requires a new `contract_version` and an
explicit adapter. JSONL append order is not semantic; consumers use IDs,
timestamps, status, and supersession metadata.
