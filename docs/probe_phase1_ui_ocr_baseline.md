# PROBE Phase 1 — Read-Only UI Capture + OCR Baseline

Date: 2026-08-28
Scope: read-only observation of the live BlueStacks Pie64 emulator. No ADB
input, tap, swipe, gameplay action, purchase, upgrade, item use, runtime
change, or account-state change was performed. Matt remains the operator for
manual navigation.

## Executive verdict

The screenshot/OCR pipeline is operational and suitable for targeted UI
observation, but this first run is not yet production-grade for unattended
numeric ingestion. Four OpenCV preprocessing variants consistently recovered
most large labels and resource strings. Stylized digits, punctuation, and
countdown text still require crop-level pixel review and must remain
`REVIEW` unless independently validated.

No S27 Research Lab or Training Grounds requirement was visible in this
baseline frame. The captured frame was a research confirmation dialog for a
lower-level technology and is not evidence about S27 progression.

## 1. Reusable capture utility

[tools/probe_phase1_ui_ocr.py](/C:/Users/madou/Documents/last-asylum-doctor-probe/tools/probe_phase1_ui_ocr.py)
provides two bounded commands:

- `capture`: detects the ready device, reads package version metadata, runs
  only `exec-out screencap -p`, hashes the PNG, and writes a JSON sidecar.
- `ocr`: loads a local image, applies four OpenCV variants, runs RapidOCR,
  and writes per-detection provenance.

The capture command has no arbitrary ADB-command argument and contains no
input/event operation path.

The local capture directory is `data/raw/probe/screenshots/`, covered by the
existing `data/raw/*` ignore rule. PNGs and OCR JSON sidecars are not tracked.

## 2. Capture provenance

| Field | Observation |
|---|---|
| Device | `emulator-5554` |
| Package | `com.phs.global` |
| Client | 1.0.97 / code 97 |
| Server field | 283 |
| Capture timestamp | 2026-08-28T20:13:26.062109Z |
| Image size | 900 × 1600 |
| Screenshot SHA-256 | `808d4148a7b15eb923c8c9a93502659f4410c03d503647dfbe3f9f6cdf393440` |
| ADB operation | `exec-out screencap -p` |

The source PNG metadata is at the ignored sidecar corresponding to the
capture, and the OCR observations are in its `.ocr.json` sidecar.

## 3. OCR benchmark

The baseline used these deterministic variants on the full screenshot, with
2× cubic upscaling before enhancement or thresholding:

1. grayscale;
2. CLAHE-enhanced grayscale;
3. Otsu threshold;
4. adaptive Gaussian threshold.

The run produced 86 detections: 21, 21, 22, and 22 respectively. Confidence
values ranged from 0.522 to 0.923.

Every detection preserves:

- source screenshot SHA-256;
- crop coordinates (`[0, 0, 900, 1600]` for this run);
- raw OCR text;
- whitespace-normalized value, without silently changing digits or terms;
- OCR confidence;
- source-crop bounding box;
- validation status.

Without an operator-supplied expected value, the utility intentionally marks
all results `REVIEW`. With `--expected`, it marks only an exact normalized
match `PASS`; mismatches are `FAIL`. No OCR result was written to canonical
game-data tables.

## 4. Screen successfully observed

The current frame was a research confirmation dialog titled **Resource
Gathering I**. Visible source pixels showed:

- `Research Level 4 → 5`;
- current effect `+16% → +20%`;
- Might `5,710 → 7,930`;
- prerequisite `Research Lab Lv.14`;
- resource displays `3.6M/646K`, `4.1M/646K`, and `3.6M/1.9M`;
- original time `07:20:00`;
- visible countdown `02:36:29` at capture time.

These are observations of this screen only, not a claim about the account's
canonical research or resource state.

## 5. OCR accuracy observed against source pixels

The following repeatability counts compare normalized OCR text against the
visible source pixels across the four variants. They are benchmark evidence,
not automatic acceptance rules:

| Visible field | Exact variant matches | Assessment |
|---|---:|---|
| `Increases Squad 1 Gathering` | 4/4 | PASS for this label |
| `+16%` and `+20%` | 4/4 each | PASS for these values |
| `7,930` | 4/4 | PASS for this value |
| `3.6M/646K`, `4.1M/646K`, `3.6M/1.9M` | 4/4 each | PASS for these displays |
| `Research Lab Lv.14` | 3/4 | REVIEW; one case variant differed |
| `Research Level 4 → 5` | 3/4 recognized as `Research Level 4 5` | REVIEW; arrow was omitted |
| `Resource Gathering I` | 2/4 | REVIEW; one punctuation error and one split result |
| `5,710` | 1/4 | REVIEW; alternatives included `5,710 CO` and `5.710` |
| `Original Time: 07:20:00` | 2/4 | REVIEW; one leading-character error and spacing variation |
| `02:36:29` | 3/4 | REVIEW; one variant produced an incorrect digit string |

The main failure mode is not lack of text detection; it is ambiguous
interpretation of stylized numeric glyphs and punctuation. Numeric values
remain noncanonical until a targeted crop is visually checked.

## 6. S27 priority result

| Requested observation | Result |
|---|---|
| Research Lab 26 → 27 requirements | Not shown in baseline frame; no fact captured. |
| Training Grounds 26 → 27 requirements | Not shown in baseline frame; no fact captured. |
| Prerequisite lock messages | None for S27 in baseline frame. |
| Required resources | No S27 resources shown. |
| Construction time | No S27 construction time shown. |

Known static identity metadata remains supporting context only: 1001 is
Sanctuary, 1007 is Research Lab, and 1020 is Training Grounds. No new ID
linkage was inferred from OCR.

## 7. Production viability

**Provisional: viable for read-only targeted observation; not yet viable for
unattended numeric extraction.** The pipeline is deterministic and preserves
the evidence needed for review. Production use requires per-screen crop
profiles, expected-value/pixel validation for numeric fields, and rejection
of `REVIEW`/`FAIL` observations from canonical tables.

Dependencies are intentionally limited to OpenCV and RapidOCR. The exact
optional installation is recorded as the `probe` extra in `pyproject.toml`;
the benchmark used OpenCV 5.0.0 and `rapidocr_onnxruntime` 1.2.3.

## 8. Recommended next capture

Ask Matt to manually expose **one Research Lab building/details or upgrade
requirements screen**, without starting or confirming an upgrade. Capture
that frame first. If the game hides Research Lab 26 → 27 requirements while
Sanctuary 27 is upgrading, record that explicitly and then request one
Training Grounds details screen. Continue one screen at a time.

## Validation and repository note

The only device operation in this phase was the read-only screenshot capture
plus package metadata queries. No screenshots, OCR sidecars, APKs, account
secrets, or bulk assets are committed.
