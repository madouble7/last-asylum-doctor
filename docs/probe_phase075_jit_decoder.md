# PROBE Phase 0.75 — Targeted JIT Payload Decoder Experiment

Date: 2026-08-28
Scope: static, read-only inspection of three explicitly named payloads from
the preserved Last Asylum client 1.0.97 / version code 97. No ADB input,
gameplay, runtime modification, hooking, injection, protection bypass,
decryption, bulk extraction, or MINER creation was performed.

## Executive verdict

**Outcome B — PARTIALLY DECODABLE.** The normal Unity container boundary is
deterministically readable: the APK is a ZIP, the selected entry is a UnityFS
AssetBundle, and UnityPy identifies each target as a named TextAsset with a
stable internal path and exact byte length. The payload bytes themselves do
not expose a normal text, protobuf, Lua-bytecode, or standard compression
format in this bounded test. No numeric rows were recovered.

This is enough to establish where the BuildingLevel, BuildingUpgrade, and
CollegeTechLevel data lives, but not enough to claim local numeric gameplay
truth. MINER is not justified.

## A. Selected bundles and representative payloads

Source: ignored local copy of `split_abPack1.apk`, pinned to client version
1.0.97 / code 97. The smallest representative set is one TextAsset per
family, all in the same base-data JIT bundle:

| Family | Bundle | Internal TextAsset container | Raw payload bytes |
|---|---|---|---:|
| BuildingLevel | `assets/ABAsset/gamedata_basedb_f_basedata_jit.assetbundles` | `assets/resourcesdata/gamedata/basedb_f/basedata_jit/buildinglevel.bytes` | 161,487 |
| BuildingUpgrade | same | `assets/resourcesdata/gamedata/basedb_f/basedata_jit/buildingupgrade.bytes` | 265,317 |
| CollegeTechLevel | same | `assets/resourcesdata/gamedata/basedb_f/basedata_jit/collegetechlevel.bytes` | 611,965 |

The source UnityFS bundle is 4,988,185 bytes and contains 737 serialized
objects: one `AssetBundle` and 736 `TextAsset` objects. No other JIT table was
read for row extraction.

Inspection code: [tools/probe_phase075_jit_decoder.py](/C:/Users/madou/Documents/last-asylum-doctor-probe/tools/probe_phase075_jit_decoder.py).

## B. Serialization and container format

The observed container chain is:

```text
split_abPack1.apk (ZIP/APK)
  -> gamedata_basedb_f_basedata_jit.assetbundles (UnityFS)
    -> serialized TextAsset named BuildingLevel / BuildingUpgrade / CollegeTechLevel
      -> .bytes m_Script payload
```

All three payloads begin with the same 48-byte fingerprint prefix:

```text
7e 35 00 06 35 6d 7c 3f 61 7f 7b 55 7e 67 65 1a
3f 65 73 72 70 67 65 79 75 67 61 6d 4d 28 2c 74
3f 1f 39 55 42 06 08 11 12 5d 03 11 0b 1d 14 13
```

None matched the tested signatures for gzip, zlib, LZ4 frame, nested UnityFS,
or Lua bytecode (`\x1bLua`). Printable-byte ratios were high, but the visible
bytes were not readable schema/row text; printable ratio is not evidence that
the payload is plaintext. The exact encoding or transformation is
**UNCONFIRMED**. No decompression, deobfuscation, decryption, brute force, or
runtime-assisted interpretation was attempted.

## C. BuildingLevel result

Classification: **PARTIALLY DECODABLE**.

Confirmed:

- TextAsset name: `BuildingLevel`.
- Stable Unity container path and exact raw payload length above.
- The object is inside the expected UnityFS JIT/base-data bundle.

Not recovered:

- stable row keys for building IDs 1001, 1007, or 1020;
- level 26–30 rows;
- resource costs, construction time, prerequisites, or unlock conditions;
- a parseable field schema.

The target payload did not contain readable ASCII occurrences of the three
known building IDs. That negative byte-fingerprint observation does not prove
the IDs are absent; it only confirms that they were not exposed as plain ASCII
in this payload boundary.

## D. BuildingUpgrade result

Classification: **PARTIALLY DECODABLE**.

Confirmed:

- TextAsset name: `BuildingUpgrade`.
- Stable Unity container path and exact raw payload length above.
- The target is a separate payload from `BuildingLevel`, not a decoded row.

Not recovered:

- building ID to level rows;
- level 26–30 costs or timers;
- prerequisite building IDs/levels or unlock conditions;
- a parseable numeric schema.

The common prefix and lack of a standard format identify a repeatable payload
boundary, not a recoverable row format.

## E. CollegeTechLevel result

Classification: **PARTIALLY DECODABLE**.

Confirmed:

- TextAsset name: `CollegeTechLevel`.
- Stable Unity container path and exact raw payload length above.
- The target is separate from readable `collegetech.txt` identity/description
  data.

Not recovered:

- research/technology level rows;
- costs, research time, effects, or prerequisite references;
- a stable row-key representation inside this payload.

Therefore no CollegeTech numeric value is reported as client truth.

## F. Schema and field-name evidence elsewhere in the client

The selected protobuf TextAssets provide runtime message field names, but they
are not schemas for the opaque JIT tables and do not supply local costs.

Confirmed examples:

- `building.proto` → `BuildingDto`: `buildingId`, `originalId`, `level`,
  `status`, `startTime`, `endTime`, `canProduce`, and `resourceDetail`.
- `collegeTech.proto` → `PushTechInfoS2C`: `techId`, `level`.
- `collegeTech.proto` → `TechInfoDto`: `techId`, `level`, `exp`,
  `researching`, `expMultiply`, and `supplyExp`.
- `collegeTech.proto` → `ResearchFinishNotifyS2C`: `researchLevel` and
  `researchTimes`.
- `resource.proto` → `ResourceInfo`: `type`, `value`, and `itemId`.
- `item.proto` → `ItemDto`: `itemId`, `count`, and `endTime`.

These schemas confirm that runtime/server messages can represent IDs, levels,
quantities, and timestamps. They do not connect those fields to the three JIT
byte streams, and no `BuildingLevel`, `BuildingUpgrade`, or
`CollegeTechLevel` protobuf message was established.

The readable English base-data layer separately confirms stable display/config
identity records:

- `building.txt`: `1001` → Sanctuary, `1007` → Research Lab, `1020` →
  Training Grounds.
- `collegetech.txt`: stable technology IDs and descriptions, including rows
  referring to Training Grounds expansion/limit.
- `buildingdetails.txt`, `gototarget.txt`, and language tables: descriptions,
  navigation keys, and localization templates.

Those are localization and identity/configuration facts, not numeric level
tables.

## G. Numeric/config structures actually evidenced

The strongest deterministic structure remains the readable text layer:

```text
UnityFS container path
  -> Lua-table TextAsset name
    -> stable row key
      -> id
        -> name / description / display fields
```

The following candidate structures were **not** evidenced as decoded local
rows in this experiment:

- building ID → level → construction costs;
- building ID → level → construction timer;
- building ID → level → prerequisite building ID/level;
- research ID → level → costs/time/effects/prerequisites;
- resource ID → quantity as a canonical local table.

The protobuf fields listed above describe runtime state/message shapes only.
Nearby numbers, shared prefixes, object order, or payload sizes were not used
to infer relationships.

## H. Sanctuary/building-specific leads and S27 facts

The known building identities are confirmed in the English text layer:

- 1001 → Sanctuary;
- 1007 → Research Lab;
- 1020 → Training Grounds.

No explicit numeric fact was recovered for Sanctuary 27, Research Lab 27, or
Training Grounds 27. No direct prerequisite relationship, construction cost,
construction timer, or research cost was recovered for those levels.

| Requested S27 fact | Result |
|---|---|
| Sanctuary 27 | One explicit feature-unlock text condition exists (Super Dispatch); no upgrade value, cost, or timer. |
| Research Lab 27 | No explicit level-27 value, cost, timer, or prerequisite. |
| Training Grounds 27 | No explicit level-27 value, cost, timer, or prerequisite. |
| Direct prerequisite relationship | None established. |

One explicit S27-related text fact is present in
`basedb_f/en/functionunlock.txt`, object `FunctionUnlock`, row ID `188`:

```text
Unlock VIP12 privileges or reach Sanctuary Lv.27 to use Super Dispatch
```

This is a confirmed feature-unlock condition tied to that text row. It is not
evidence of a Sanctuary upgrade cost, a Research Lab prerequisite, or a
Training Grounds progression value.

Language strings such as `Unlocks at Research Lab Lv.{0}` and `Training
Grounds unlock at Lv.{0}` are templates. They contain no concrete S27 value.

## I. xLua/config boundary

Phase 0.5 established xLua native/library and bundle evidence. The selected
logic bundle contained `.bytes` TextAssets with the same style of opaque
binary prefix, no Lua bytecode magic, and no plaintext Lua markers in the
bounded sample. This experiment did not attempt to decode those resources.

Readable Lua-table text is present in the English base-data bundle, while the
JIT numeric candidates remain opaque. This supports normal static parsing of
the text identity/localization layer only.

## J. What remains opaque

- the JIT payload encoding and field boundaries;
- BuildingLevel, BuildingUpgrade, and CollegeTechLevel numeric rows;
- costs, timers, effects, and prerequisites;
- canonical cross-domain joins among localization keys, item IDs, resource
  IDs, and server IDs;
- server-overridden/runtime progression and authoritative values.

The current evidence does not distinguish custom serialization from a
protected/transformed representation. Determining that through reverse
engineering would exceed this experiment's safety boundary.

## K. Outcome gate and MINER decision

**Gate: B — PARTIALLY DECODABLE.** Deterministic object/container discovery
works; important numeric payloads do not.

MINER should **not** be created. A future extractor would only be justified if
a documented or otherwise plainly parseable format becomes available and a
small sample exposes explicit row fields. If that happens, the initial scope
should remain an allowlist of the three JIT TextAssets plus the already
readable English identity layer, with source bundle hash, internal path, row
key, parser version, and an explicit separation of localization, IDs,
configuration, numeric values, and runtime/server data.

## L. Highest-value next experiment

Use a read-only PROBE UI/OCR observation of the already visible building and
research detail screens to record S27 costs, timers, and prerequisite text if
they are displayed. Do not tap, swipe, start, upgrade, spend, or modify
anything. This is the smallest experiment that can answer Matt's immediate
S27 need after the static numeric boundary remained unresolved.

If static work is revisited first, require a documented/plain format for one
of these exact payloads and validate one explicit row before expanding scope.

## Validation and repository note

Every payload fact above is tied to the local version 1.0.97 / code 97
`split_abPack1.apk`, the source bundle path, the Unity TextAsset container,
and the bounded parser method in
`tools/probe_phase075_jit_decoder.py`. No APK or extracted binary asset is
tracked or committed.
