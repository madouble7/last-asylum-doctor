# PROBE Phase 2: Safe Navigation Foundation

## Scope

This phase adds a bounded reconnaissance foundation for Last Asylum: Plague.
It recognizes supported UI states and can propose one account-state-preserving
transition. The default CLI path is dry-run and sends no ADB input. It does not
start research, spend resources, claim rewards, enter combat, or perform any
other account change.

The implementation is in `src/last_asylum_doctor/probe/navigation.py` and the
CLI entry point is `last-asylum-doctor probe`. Existing read-only capture and OCR
tools remain separate.

## Architecture

- `Frame` carries a screenshot, SHA-256, dimensions, OCR anchors, and metadata.
- `StateRecognizer` claims only states supported by required OCR anchors;
  insufficient evidence becomes `unknown`.
- `ScreenState` stores state identity, screenshot hash, fingerprint, anchors,
  confidence, detected client version, and timestamps.
- `SafeAction` describes semantic input with normalized geometry and an
  account-state-preserving marker.
- `NavigationPolicy` is a deterministic allowlist that rejects unknown actions,
  missing geometry, invalid coordinates, and account-changing actions.
- `NavigationAgent` enforces dry-run behavior, step limits, before/after state
  verification, loop detection, and stop-on-uncertainty behavior.
- `NavigationGraph` persists observed transitions separately from factual game
  tables; `SessionJournal` writes JSON and Markdown review records.
- `AdbFrameSource` detects package version name and version code at capture time;
  it does not treat `1.0.97` as a permanent current version.

## Current policy boundary

**PASSIVE OBSERVATION / OCR is the preferred live-account reconnaissance mode.**
Matt should play normally while PROBE captures and reviews evidence.

The ADB input adapter is retained as **EXPERIMENTAL / NOT ENABLED FOR NORMAL
Server 283 OPERATION** pending an explicit future policy decision. The
`--execute-safe-navigation` CLI flag is an engineering fixture/experimental
switch, not approval for deployment on Matt's real account.

Account-changing gameplay automation is prohibited by project guardrails. No
coordinate jitter, randomized concealment timing, humanized input, stealth,
anti-detection, or evasion behavior is present or recommended.

## Dry-run workflow

```powershell
last-asylum-doctor probe inspect-current-screen --dry-run
last-asylum-doctor probe navigate-to-research-lab --dry-run
```

The navigation graph defaults to
`data/processed/probe/navigation_graph.json`; screenshots and session artifacts
are written to ignored data paths. A live device is not required for fixture
tests.

## Version and hardware handling

Every future live session must detect and record:

- package name
- installed version name
- installed version code
- server label and capture timestamp

Historical observations keep their historical client metadata. Public APK
metadata such as `1.0.99` / code `99` is a `VERSION_SIGNAL` only until observed
locally. The prior Windows adapter observation of an RTX 3080 reported roughly
4 GiB through one query, while `nvidia-smi`/CUDA was unavailable; the exact VRAM
quantity is **UNVERIFIED** and must not drive design decisions.

## Readiness

Fixture tests cover allowlist acceptance and rejection, dry-run input
suppression, transition success/failure, graph persistence, journal creation,
loop detection, step limits, and unknown-state handling. This is fixture-ready
and not a claim of live emulator availability or approval.
