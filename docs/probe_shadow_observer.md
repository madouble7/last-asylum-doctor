# PROBE Shadow Observer

## Direction

The next production reconnaissance mode is **PROBE SHADOW OBSERVER**. Matt
plays normally; PROBE generates no game input and does not navigate the game.

## Intended behavior

A future Shadow Observer will autonomously:

- detect BlueStacks/client availability
- capture frames locally
- detect meaningful UI changes
- classify screen states
- OCR useful fields
- hash screenshots and derived evidence
- record state transitions
- learn screen fingerprints and observed navigation paths
- update a structured account-observation stream

This design removes the need for Matt to manually trigger screenshots while
keeping observation separate from gameplay control. It is a design direction,
not an implementation in this integration milestone.

## Guardrails

- No tap, swipe, key event, resource use, speedup, training, healing, upgrade,
  purchase, attack, or other game input.
- Unknown or ambiguous screens become review records rather than actions.
- Each observation keeps package, installed version name, installed version
  code, server, timestamp, raw evidence reference, hash, normalized
  interpretation, and `PASS` / `REVIEW` / `FAIL` status.
- Historical client versions remain attached to historical observations;
  public APK metadata remains a `VERSION_SIGNAL` until observed locally.

The existing safe-navigation engine remains useful as a fixture and state/
transition model, but its live ADB input path is experimental and not enabled
for normal Server 283 operation.
