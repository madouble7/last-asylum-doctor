# Doctor's Companion - Architect State

## Canonical checkpoint

- Branch: `main`.
- State recorded against commit `d597242` (Sprint #1 integration); verify
  `HEAD` before relying on this field after a later checkpoint.
- Canonical repository:
  `C:\Users\madou\Documents\last-asylum-doctor`.

## Product mission

Doctor's Companion should help a Doctor answer: what is known about the game,
what is true for this account, what can be done next, and which choice is worth
considering. Facts, calculations, strategy, and player-specific intent remain
separate so recommendations do not turn guesses into game data.

## Operating roles

- **ARCHITECT**: product and architecture authority; sets direction and resolves
  consequential tradeoffs.
- **ATLAS**: canonical production builder and explicit integrator.
- **SCOUT**: external intelligence, source validation, evidence lineage, and
  strategy research.
- **PROBE**: passive installed-client and live-account observation owner.
- **ENGINEER**: independent technical R&D, diagnostics, benchmarking, and
  feasibility/review specialist in the VS Code Agents window.

Role names describe responsibilities, not models or providers.

## Current production capabilities

- **Research corpus and database**: targeted and explicit full-corpus science
  ingestion can normalize source-backed research nodes, levels, times, power,
  costs, and provenance into JSON/SQLite. Validation rejects malformed or
  incomplete source shapes.
- **Building data**: the planner has confirmed Server 283 milestone inputs for
  Sanctuary/Training Grounds/Research Lab progression. A general canonical
  building database is not yet present.
- **Shop Doctor/economics**: the workbook reader and economic database preserve
  item identity, offers, packs, choices, assumptions, source snapshots, and
  validation status without rewriting source vocabulary.
- **Recovery Planner**: deterministic resource, speedup, milestone, and troop
  readiness calculations accept extensible account-state JSON. Unknown values
  remain limitations; troop costs, training times, and economic optimality are
  not invented.
- **PROBE capture/navigation infrastructure**: read-only frame capture, OCR
  anchors, state recognition, bounded safe-navigation fixtures, dry-run mode,
  transition verification, and session journals exist. Experimental ADB input
  is isolated from normal operation.
- **Shadow Observer v0.2**: passive ADB/display polling records novel frames in
  append-only JSONL, compares change against the last recorded frame, requires
  explicit foreground confirmation before OCR, retains bounded evidence only
  for confirmed game frames, preserves parser diagnostics, reports structured
  OCR/recognition/storage failures, and records per-stage timing totals. State
  recognition uses conservative multi-anchor rules so map labels do not claim
  building detail states.
- **Account observation contract**: v0.1 defines raw observations, normalized
  facts, and PASS-only account snapshots with provenance, review/fail handling,
  and historical supersession.
- **Evidence/provenance model**: factual records retain source scope, URLs or
  evidence identifiers, dates, server/version context, hashes, raw values, and
  uncertainty. Research and economic source observations remain auditable.
- **Control-room workflow**: one canonical shared-main repository has ATLAS,
  SCOUT, and PROBE workspace wrappers with local `Doctor PowerShell` profiles;
  the three-window launcher remains the supported fallback.

## Current evidence posture

- Research costs, times, power, levels, and source metadata are known only for
  validated ingested records and their stated source scope.
- Numeric research effects are incomplete. The Scout validation oracle currently
  separates 6 direct-primary claims, 4 derived level-series claims, and 6
  secondary/inferred claims.
- The authoritative research prerequisite graph is incomplete. Ordering,
  numeric IDs, guide layouts, and public descriptions do not prove dependency
  edges or building gates.
- Scout's prerequisite and high-tier gating claims remain `UNVERIFIED`; its
  ledger is a PROBE validation oracle, not a replacement for live verification.
- A public or historical client value is a `VERSION_SIGNAL` until it is tied to
  a locally observed client/version and appropriate server scope.
- Conflicts and missing observations stay visible; they are not averaged into a
  canonical fact.

## Current account/progression context

- Confirmed planner milestones cover Sanctuary 27 follow-on progression through
  Training Grounds 27 and Research Lab 27, with source-scoped resource and
  duration inputs.
- The planner can reason about current T8 troops, wounded/recoverable troops,
  and a desired combat-ready target when those values are supplied.
- Current live resource balances, speedup inventories, building levels, troop
  counts, research levels, and player targets are not established in this
  repository. Do not present sample planner input as live account state.

## Policy / safety constraints

- Passive observation and OCR are the preferred live-account reconnaissance
  mode; Matt plays normally while PROBE observes.
- Shadow Observer generates no game input. It has no tap, swipe, keyevent, or
  text-input path and has no cloud/VLM dependency.
- The ADB input adapter is an experimental, policy-reviewed fixture and is not
  normal Server 283 production mode. Account-changing automation remains
  prohibited.
- Raw screenshots and live observation streams remain local/ignored when
  appropriate. Secrets and unnormalized raw evidence do not belong in Git.

## Highest-value open loops

- Complete the first bounded Shadow Observer live acceptance and assess actual
  foreground detection, OCR quality, screen classification, evidence retention,
  timing quality, and safe failure behavior against the v0.2 schema.
- Build the eventual narrow adapter from validated raw observations to
  normalized facts and account snapshots; do not bypass the evidence boundary.
- Expand direct client verification of research effects, prerequisite edges,
  building gates, and account/progression fields before canonical integration.
- Connect accepted account snapshots to planner inputs while preserving fact
  provenance and explicit missing-input limitations.

**Immediate next acceptance target:** Shadow Observer live acceptance and
observation quality on the installed client, beginning with a bounded session.

## Re-grounding rule

Before major planning, ARCHITECT should read this briefing, the relevant
architecture decision records, and the actual current repository evidence. The
briefing is a compact orientation layer, not a substitute for source records,
tests, implementation, or current Git state.
