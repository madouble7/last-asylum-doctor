# Doctor's Companion Project Guidelines

## Product and terminology

- The product is **Doctor's Companion**.
- Players of Last Asylum are Doctors. Do not call the software itself "the Doctor."
- Keep factual game data, calculations, strategy, and player-specific recommendations distinct.

## Evidence and factual integrity

- Never invent missing game facts, costs, times, dependencies, mechanics, or currentness.
- Preserve provenance and context for every factual observation: source, URL or evidence identifier, date, server, version, and account or era scope when known.
- Preserve conflicts as conflicts. Never average conflicting factual values or present an inferred value as a fact.
- Label material claims as `FACT`, `STRATEGY`, `FUTURE_WARNING`, or `VERSION_SIGNAL` where appropriate.
- Keep server-, version-, and account-specific observations scoped; do not generalize them to all players.
- Distinguish direct evidence from inference and state uncertainty explicitly.
- Keep secrets and raw evidence out of Git when appropriate; commit normalized, reviewable records and references instead.

## Engineering

- Inspect the existing implementation, architecture, and dependencies before proposing changes.
- Prefer small deterministic solutions that fit the current Python package and CLI.
- Prefer existing architecture and dependencies. Avoid speculative frameworks and unrelated redesigns.
- Preserve canonical data integrity and avoid unrelated refactors or cleanup.
- Add focused tests for changed behavior, run focused checks followed by the full suite when appropriate, and run `git diff --check` before committing.
- Commit only bounded completed work on the expected branch for the assigned role.

## Ownership and parallelism

- ATLAS owns implementation and integration in the canonical product repository.
- SCOUT owns public-source reconnaissance and returns evidence to ATLAS.
- PROBE owns installed-client and live-account reconnaissance and returns validated observations to ATLAS.
- Multiple agents may work simultaneously only when file and data ownership do not conflict. Agents must not modify another role's worktree.