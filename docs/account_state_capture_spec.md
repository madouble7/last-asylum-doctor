# Account State Ingestion and OCR Capture Specification

Status: **DRAFT / PROBE READ-ONLY**
Canonical base: `3ea55cddb388a8312dfc56e784a18b5460845a82`
Account scope: `Matt_S283`
Server scope: `283`

## Purpose and boundaries

This document specifies how passive BlueStacks screenshots and OCR observations
can be normalized into a reviewable `research_user_state.json`. It does not
permit game input, research, building upgrades, spending, inventory use, or
any other account-changing action. A screenshot is evidence; it is not itself
verified account state.

The requested `src/last_asylum_doctor/client/shadow_observer.py` path is not
present in the inspected repository. The currently available implementation is
`src/last_asylum_doctor/probe/shadow_observer.py`. The committed
`data/research/research_user_state.json` is the earlier Commando-only contract
(23 states and 116 target deltas), so the 18-tree shape below is a proposed
extension, not a claim about the current canonical file.

## Evidence record

Every capture and derived observation must retain:

```json
{
  "observation_id": "session-000001",
  "captured_at_utc": "2026-08-31T12:00:00Z",
  "account_scope": "Matt_S283",
  "server": "283",
  "package": "com.phs.global",
  "client_version_name": "1.0.97",
  "client_version_code": 97,
  "foreground_status": "confirmed_game",
  "screenshot_hash": "sha256 hex",
  "screenshot_path": "data/raw/probe/shadow/screenshots/...png",
  "current_screen_state": "research_tree_index",
  "ocr_raw_output": [
    {
      "raw_ocr_text": "Current Level 8",
      "normalized_value": "Current Level 8",
      "confidence": 0.98,
      "bbox_source_crop_pixels": [[10, 20], [200, 20], [200, 50], [10, 50]],
      "crop_coordinates_xywh": [0, 0, 720, 1280],
      "preprocessing_variant": "clahe_up2"
    }
  ],
  "validation_status": "REVIEW",
  "transition_provenance": {
    "kind": "passive_local_observation",
    "method": "sha256+perceptual_hash+state_recognizer"
  }
}
```

The screenshot hash, capture timestamp, device/package metadata, screen state,
OCR text, confidence, bounding box, crop, and preprocessing variant are
required for traceability. `PASS` means the record passed all deterministic
checks and any required corroboration; `REVIEW` means it is a candidate only;
`FAIL` means it must not update canonical state.

## Canonical research state

The top-level shape preserves the existing `research_user_state.json` contract
and adds a complete 18-tree `research_states` collection. All 348 canonical
nodes must be represented exactly once. `target_level` is optional for a
capture-only state and must remain distinct from the observed `current_level`.

```json
{
  "schema_version": 2,
  "dataset": "research_all_trees",
  "account_scope": "Matt_S283",
  "server": "283",
  "state_labels": ["OCR-VERIFIED", "USER-ENTERED", "USER-TARGET"],
  "research_state_record_count": 348,
  "research_states": [
    {
      "node_id": "1001",
      "branch": "Development",
      "name": "Rapid Construction I",
      "current_level": 8,
      "max_level": 5,
      "state_label": "OCR-VERIFIED",
      "account_scope": "Matt_S283",
      "observed_at_utc": "2026-08-31T12:00:00Z",
      "evidence_observation_ids": ["session-000001"],
      "source_screenshot_hashes": ["sha256 hex"],
      "verification": {
        "status": "PASS",
        "rule": "exact node identity plus level read and corroborated frame",
        "confidence": 0.98
      }
    }
  ],
  "target_deltas": []
}
```

Rules:

1. Resolve a node only through the canonical `node_id`, branch, and name
   catalog. OCR text alone cannot create a new node.
2. `current_level` and `target_level` are strict non-negative integers. The
   observed level must be no greater than the catalog `max_level`.
3. A level is `OCR-VERIFIED` only when the screen identity, node identity, and
   level are all readable and pass deterministic range checks. Otherwise retain
   the candidate as `REVIEW` evidence and leave the prior state unchanged.
4. A changed value requires two consistent passive observations from separate
   captures, or one capture with an unambiguous level and exact node identity.
   Conflicting captures remain conflicts; they are never averaged.
5. `USER-ENTERED` and `USER-TARGET` remain user claims and are not silently
   relabeled as OCR facts. Every record carries its own provenance.
6. Missing trees or nodes are explicit `REVIEW`/unknown records during a
   partial session; absence from a screenshot is not evidence of level zero.

## Building state

Building observations are separate from research nodes. The initial allowlist
is Sanctuary, Research Lab, and Training Grounds.

```json
{
  "buildings": [
    {
      "building_id": "research_lab",
      "display_name": "Research Lab",
      "current_level": 12,
      "observed_at_utc": "2026-08-31T12:02:00Z",
      "account_scope": "Matt_S283",
      "server": "283",
      "state_label": "OCR-VERIFIED",
      "evidence_observation_ids": ["session-000004"],
      "verification": {
        "status": "PASS",
        "confidence": 0.96,
        "rule": "building title plus current-level label in building detail"
      }
    }
  ]
}
```

Only `sanctuary`, `research_lab`, and `training_grounds` are accepted in this
first contract. Building detail must contain the building identity and an
explicit current-level value. `next level`, requirements, and construction
time are contextual evidence and must not be mistaken for the current level.

## Resource and speedup inventory

Inventory is recorded as observed quantities with explicit units and item
identity. Do not convert an OCR number into a resource balance unless its label,
unit, and ownership context are visible.

```json
{
  "inventory": {
    "observed_at_utc": "2026-08-31T12:04:00Z",
    "account_scope": "Matt_S283",
    "resources": [
      {
        "resource_id": "timber",
        "quantity": 1250000,
        "unit": "base_units",
        "display_value": "1.25M",
        "state_label": "OCR-VERIFIED",
        "evidence_observation_ids": ["session-000007"],
        "verification_status": "PASS"
      }
    ],
    "speedups": [
      {
        "item_id": "research_speedup",
        "duration_seconds": 3600,
        "quantity": 4,
        "unit": "items",
        "state_label": "OCR-VERIFIED",
        "evidence_observation_ids": ["session-000007"],
        "verification_status": "PASS"
      }
    ]
  }
}
```

Resource quantities and speedup durations are strict non-negative integers in
canonical units. Keep the displayed string for auditability. A bag category,
item name, quantity, and unit must agree; ambiguous commas, decimal suffixes,
or clipped labels produce `REVIEW`. An item count is not a usable duration, and
a research cost from the public corpus is not an observed inventory balance.

## Passive OCR mapping flow

1. Capture only with `exec-out screencap -p`; record the immutable PNG and
   SHA-256 hash. Device discovery, package metadata, and foreground inspection
   are read-only prerequisites.
2. Suppress unchanged frames using the observer's perceptual/change threshold,
   while retaining the capture metadata needed to explain suppression.
3. Run OCR on the full frame or declared crop using the recorded preprocessing
   variant. Preserve raw text, normalized text, confidence, and source-crop
   coordinates; never overwrite raw OCR with normalized text.
4. Recognize the screen from explicit anchors. Known informational screens
   include research tree/index, research node detail, Sanctuary, Research Lab,
   Training Grounds, and bag inventory. Unknown or non-game foreground is
   `REVIEW` and cannot update state.
5. Parse typed candidates only inside screen-specific regions. Research levels
   require a node title/identity anchor plus `Current Level`; building levels
   require the building title plus `Current Level`; inventory requires category,
   item label, quantity, and unit.
6. Join candidates to canonical IDs, enforce integer/range/unit checks, and
   attach observation IDs and screenshot hashes. Any failed check yields
   `REVIEW` or `FAIL`, never a guessed value.
7. Emit a proposed state delta for review. Only `PASS` records may replace the
   latest verified value; conflicts remain separately recorded with both pieces
   of evidence.

The resulting normalized file should be generated from evidence records and
remain reproducible. Raw probe evidence stays under ignored `data/raw/probe`
paths; canonical normalized records contain hashes and provenance references,
not unreviewed screenshots or secrets.

## Acceptance checklist

- [ ] All 18 branches and all 348 node IDs are present in the catalog.
- [ ] Every captured research level maps to exactly one canonical node.
- [ ] Building records are limited to the initial three-building allowlist.
- [ ] Resource and speedup quantities have explicit canonical units.
- [ ] Every verified value has timestamp, account/server scope, screenshot hash,
  OCR provenance, and validation status.
- [ ] No `REVIEW` or `FAIL` candidate mutates `research_user_state.json`.
- [ ] No capture path contains an input/event operation.