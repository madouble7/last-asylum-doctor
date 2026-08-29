# Client Automation and Emulator Policy Reconnaissance

**Status:** Completed
**Date:** 2026-08-29
**Game:** *Last Asylum: Plague*, package `com.phs.global`
**Official source:** [37GAMES Terms of Use](https://gpassport.37games.com/center/servicePrivicy/service?language=en)

## Evidence summary

- **FACT:** The official 37GAMES terms restrict unauthorized bots, scripts,
  scrapers, automated access, service interference, security circumvention, and
  reverse engineering. The terms also reserve account enforcement actions for
  suspected violations. This report is operational risk documentation, not a
  legal conclusion.
- **FACT:** Emulator use is not identified here as a standalone prohibition, but
  unmodified-client use does not make restricted automation acceptable.
- **FACT:** Public APK metadata is not proof of the installed live-client
  version. Future sessions must detect package, installed version name, and
  installed version code locally.

## Project policy decision

- **PASSIVE OBSERVATION / OCR:** Preferred live-account reconnaissance mode.
  Capture frames locally, classify them, OCR useful fields, hash evidence, and
  require review of factual interpretations.
- **AUTOMATED ADB INPUT:** Technically feasible in the experimental navigation
  engine, but deployment on Matt's real account is **NOT APPROVED** under the
  current project policy review. The engine remains dry-run by default and its
  allowlist rejects account-changing actions.
- **ACCOUNT-CHANGING GAMEPLAY AUTOMATION:** Prohibited by project guardrails and
  not part of Doctor's Companion.
- **ANTI-DETECTION / EVASION:** Not implemented and not recommended. The project
  does not use coordinate jitter, randomized timing to conceal automation,
  humanized input, or other detection-avoidance behavior.

## Operational boundary

The current safe-navigation code is retained for deterministic state
recognition, semantic allowlists, before/after verification, graph persistence,
journal creation, and fixture testing. Normal Server 283 operation is passive
observation only. Any future change to that boundary requires an explicit policy
review; model instructions alone are not a security enforcement mechanism.
