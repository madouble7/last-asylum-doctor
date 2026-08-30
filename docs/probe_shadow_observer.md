# PROBE Shadow Observer v0.3

Matt can play normally while the observer polls the BlueStacks framebuffer.
The observer is passive: its ADB calls are limited to device discovery,
installed package metadata, foreground activity inspection, and framebuffer
capture. It does not navigate, dismiss, or alter the game.

## Run

From the repository root, run:

```text
.\.venv\Scripts\python.exe tools\probe_shadow_observer.py
```

The default mode runs until `Ctrl+C`, polls every five seconds, appends JSONL
to `data/raw/probe/shadow/observations.jsonl`, and retains at most 100 PNGs in
`data/raw/probe/shadow/screenshots`. A bounded capture is useful for a test or
short reconnaissance session:

```text
.\.venv\Scripts\python.exe tools\probe_shadow_observer.py --duration 300 --interval 5 --verbose
```

Useful controls are `--adb`, `--serial`, `--server`, `--output`,
`--evidence-dir`, `--max-captures`, and `--change-threshold`.

## Async capture spool

The v0.3 path separates framebuffer capture from OCR and recognition. Capture
is passive and spool-only; it never invokes OCR or writes the observation
JSONL stream. Run a bounded capture batch with:

```text
.\.venv\Scripts\python.exe tools/probe_shadow_capture.py --count 12 --interval 5
```

Each accepted frame is written beneath `spool/tmp/<capture-id>/` as
`frame.png` and `capture.json`, flushed durably, and atomically renamed into
`spool/inbox/<capture-id>/`. The directory appearance in `inbox/` is the
commit point, so a worker never sees a partial capture. The spool also has
`processing/`, `processed/`, and `failed/` directories.

Process a bounded batch locally with one reusable OCR perceiver:

```text
.\.venv\Scripts\python.exe tools/probe_shadow_worker.py --limit 12
```

The worker recovers orphaned `processing/` directories on startup, atomically
claims complete inbox directories, validates the sidecar, PNG hash, byte
length, and dimensions, then performs OCR, recognition, extraction, and
JSONL persistence. Successful evidence moves to `processed/`. Malformed
metadata, integrity failures, OCR failures, and other worker failures retain
the original evidence and move the directory to `failed/` with an inspectable
`failure.json` diagnostic. If that diagnostic cannot be durably written, the
worker leaves the capture in `processing/` and reports the persistence failure
without a terminal move. Capture IDs are stable and indexed from the JSONL
stream, so recovery or restart does not append a duplicate observation.
Only one worker may own a spool at a time; a small process lock refuses a
second worker and releases automatically when its process exits.

The internal spool schema is v0.3 and is separate from the account
observation contract. Asynchronous observations preserve `captured_at_utc`
and `capture_timing_ms`; worker queue latency, OCR, recognition/extraction,
persistence, and total processing durations are recorded in
`processing_timing_ms`. The synchronous `run_once()` path and its v0.2
`timing_ms` field remain unchanged.

The persisted `capture_staging_duration_ms` covers durable `frame.png` staging
before the sidecar write, as does the pre-commit `spool_write_duration_ms`, and
both exclude the durable `capture.json` write and the final directory rename.
The capture runtime result's
`capture_total_duration_ms` measures the complete enqueue call, including the
sidecar write and directory commit, but is not written back into committed
sidecar evidence.

## Capture and change detection

Every poll is held in memory first. The source frame is SHA-256 hashed and a
pure-standard-library 64-bit average perceptual hash is calculated from an
8-by-8 grayscale sample. A frame is suppressed when its change score is below
the configured threshold (`0.08` by default). Therefore duplicate frames do
not produce OCR, PNGs, or JSONL records. The first frame is always recorded.

OCR is run only for a novel frame whose foreground package is explicitly
confirmed as the game package. Missing or malformed foreground metadata is
`unknown`, skips OCR, and does not retain a screenshot. The optional RapidOCR
adapter already used by PROBE returns no anchors when its optional dependencies
are unavailable; OCR, recognition, and storage exceptions become structured
`FAIL` observations with stage diagnostics.
For committed spool captures, `foreground_status` is required and authoritative:
`unknown` remains unknown even when a package string was captured, and confirmed
statuses require a non-empty package consistent with that status. Direct legacy
frames without `foreground_status` retain conservative foreground inference.
The recognizer uses multi-anchor rules for the captured inventory, item dialog,
Kingdom War, Black Ops, Loot, map, and building states. Weak labels such as
`Upgrade` or `Training Grounds` remain `unknown` for review. Animation is
rate-limited by polling and bounded by `--max-captures`; no popup is dismissed.

## Account-observation boundary

The JSONL emitted here is a PROBE-specific raw observation stream. It is
evidence for the v0.1 account-observation contract, not a normalized account
snapshot. An eventual adapter can map `observation_id`, `timestamp`,
`screenshot_hash`, client/server metadata, and `validation_status` to the
contract's raw-observation provenance, then validate OCR candidates into
normalized facts. This observer does not emit canonical facts or snapshots.
Candidate extraction is deliberately narrow and preserves original OCR source
text for review.

## Observation schema

Each JSONL line is one observation with these fields:

```json
{
  "observation_id": "session-000001",
  "timestamp": "2026-08-29T12:00:00+00:00",
  "session_id": "session",
  "package": "com.phs.global",
  "client_version_name": "1.0.97",
  "client_version_code": 97,
  "server": "283",
  "screenshot_hash": "sha256...",
  "screenshot_path": "data/raw/probe/shadow/screenshots/...png",
  "previous_screen_state": null,
  "current_screen_state": "research_lab",
  "ocr_anchors": [],
  "ocr_raw_output": [],
  "extracted_candidate_values": [],
  "validation_status": "PASS",
  "transition_provenance": {
    "kind": "passive_local_observation",
    "method": "sha256+perceptual_hash+state_recognizer",
    "previous_observation_id": null
  },
  "change_score": 1.0,
  "perceptual_fingerprint": "...",
  "raw_capture_retained": true,
  "foreground_status": "confirmed_game",
  "foreground_parser": {},
  "timing_ms": {
    "capture_duration_ms": 0.0,
    "ocr_duration_ms": 0.0,
    "recognition_extraction_duration_ms": 0.0,
    "persistence_duration_ms": 0.0,
    "total_duration_ms": 0.0
  }
}
```

OCR anchors preserve text, confidence, and pixel bounding boxes. Candidate
values are labeled as OCR-derived values, not factual game data. Records keep
the prior recognized state and prior observation ID, creating an append-only
observed transition trail. `PASS` means a known state was recognized;
`REVIEW` means unknown, overlay, or non-game foreground; `FAIL` means capture
availability failed.

## Failure, storage, and timing behavior

- No ready emulator, missing ADB, or a disconnected bridge creates one
  `unavailable` / `FAIL` record and stops the session without writing a PNG.
- A different foreground package creates a `not_game_foreground` / `REVIEW`
  record and does not retain that screen's raw PNG.
- Direct frames with missing or malformed foreground metadata create a
  `foreground_unknown` / `REVIEW` record, skip OCR, and do not retain that
  screen's raw PNG. Spool captures reject missing or invalid foreground status
  and inconsistent confirmed package context before OCR.
- Unknown screens and ambiguous OCR remain `unknown` / `REVIEW`; the observer
  never attempts to dismiss an overlay.
- OCR, local recognition/extraction, and persistence failures produce `FAIL`
  diagnostics with an `error_reason`, exception type, message, and stage. A
  persistence failure is returned to the caller without claiming that a JSONL
  record was written.
- Every recorded observation includes per-stage elapsed milliseconds. The run
  summary includes timing sample count and totals.
- Only retained novel frames count against `--max-captures`. After the bound,
  observations remain in JSONL with `raw_capture_retained: false` and a
  retention note.
- `data/raw/*` is ignored by Git, so raw screenshots and local observation
  streams stay out of normal commits.
- Async failed spool directories remain inspectable local evidence. The worker
  does not rewrite `frame.png`; terminal transitions move the capture
  directory as one unit.
- Canonical JSONL appends are flushed and fsynced. On startup, a malformed or
  invalid-UTF-8 final tail is copied to a `corrupt-tail` artifact and the
  canonical stream is truncated to the last known-good record. A malformed
  middle record fails startup rather than being guessed around.
- A validated capture-processing failure is classified as
  `validated_capture_processing_failure` and keeps its validated capture
  metadata in `failure.json`; malformed or integrity-failed spool evidence is
  `untrusted_spool_evidence` and does not manufacture a canonical observation.
- Capture-ID reuse is rejected when the persisted screenshot hash differs.
  Replays are idempotent only when the processed directory's immutable capture
  metadata and frame bytes match exactly; a same-ID payload mismatch is an
  explicit collision. Equal screens under different capture IDs remain
  separate observations.
- Directories under `tmp/` never reached the inbox commit point. They are
  ignored by the worker and a failed current-process enqueue leaves a durable
  failure marker for later inspection; no temporary-file garbage collector is
  implied.

## Learning boundary

v0.3 learning is append-only observational knowledge:

```text
screen fingerprint + OCR anchors + observed state transition + evidence hash
```

There is no reinforcement learning, embedding database, cloud vision call, or
new vision dependency in this milestone. RapidOCR remains optional and is
constructed lazily once per worker perceiver. The existing safe-navigation
engine remains a fixture and transition model, while this observer has no
action driver at all.
