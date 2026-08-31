# Agent Status Board

## Handoff snapshot

- **Snapshot date:** 2026-08-31
- **Source:** Matt's transition handoff
- **Evidence class:** REPORTED
- **Verification:** This board records the supplied roster and reported role
  state. It is not an independent verification of agent availability,
  execution, or completion.

## Reported operational roster

The following seven operational sessions are reported in Matt's transition
handoff. Their routing values are reproduced as reported; `context NOT
RECORDED` means no context value was supplied in the handoff.

| Operational session | Reported status | Reported routing |
| --- | --- | --- |
| **ATLAS Copilot** | REPORTED operational session | GPT-5.6 Luna / Medium / 200k |
| **SCOUT Copilot** | REPORTED operational session | GPT-5.6 Luna / Medium / 200k |
| **PROBE Copilot** | REPORTED operational session | GPT-5.6 Luna / Medium / 200k |
| **ENGINEER** | REPORTED operational session | Claude Sonnet 5 / High / 200k |
| **ATLAS Codex** | REPORTED operational session | GPT-5.6 sol / ultra / context NOT RECORDED |
| **SCOUT Codex** | REPORTED operational session | GPT-5.6 terra / high / context NOT RECORDED |
| **PROBE Codex** | REPORTED operational session | GPT-5.6 terra / high / context NOT RECORDED |

ARCHITECT remains the coordinating authority and a required reader of this
board; it is not one of the seven operational sessions listed above.

## Operating boundary

The roster is a coordination record, not a permission grant. Repository
ownership, evidence boundaries, safety constraints, and integration authority
remain governed by the project instructions, architecture decisions, and the
current repository state.

## Ruff baseline audit

Command: `.\.venv\Scripts\python.exe -m ruff check . --output-format json`

- **Ruff version:** 0.16.4
- **Current findings:** 20
- **Reported legacy baseline:** 19 findings across five pre-Shadow probe tool
  files
- **Delta:** one additional `I001` finding at
  `tests/test_probe_capture.py:1`; this test file is outside the five-file
  legacy-tool baseline.
- **Disposition:** findings are recorded only; no legacy Ruff violations were
  repaired in this docs-only checkpoint.

```json
{
  "ruff_version": "0.16.4",
  "total": 20,
  "findings": [
    {"rule": "I001", "file": "tests/test_probe_capture.py", "line": 1},
    {"rule": "I001", "file": "tools/probe_capture.py", "line": 8},
    {"rule": "I001", "file": "tools/probe_capture_core.py", "line": 8},
    {"rule": "I001", "file": "tools/probe_phase05_fingerprint.py", "line": 12},
    {"rule": "E501", "file": "tools/probe_phase05_fingerprint.py", "line": 35},
    {"rule": "E501", "file": "tools/probe_phase05_fingerprint.py", "line": 101},
    {"rule": "E501", "file": "tools/probe_phase05_fingerprint.py", "line": 149},
    {"rule": "I001", "file": "tools/probe_phase075_jit_decoder.py", "line": 12},
    {"rule": "E501", "file": "tools/probe_phase075_jit_decoder.py", "line": 56},
    {"rule": "E501", "file": "tools/probe_phase075_jit_decoder.py", "line": 95},
    {"rule": "I001", "file": "tools/probe_phase1_ui_ocr.py", "line": 13},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 51},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 52},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 64},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 67},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 80},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 94},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 119},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 123},
    {"rule": "E501", "file": "tools/probe_phase1_ui_ocr.py", "line": 141}
  ]
}
```
