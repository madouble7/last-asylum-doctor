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
- The canonical development repository is `C:\Users\madou\Documents\last-asylum-doctor` on `main`.
- During parallel specialist work, do not run `git add`, `git commit`, `git reset`, `git checkout`, `git switch`, `git stash`, `git merge`, or `git cherry-pick` unless the mission explicitly designates the agent as INTEGRATOR.
- Only an explicitly designated ATLAS INTEGRATOR inspects all changes, detects overlap, runs the appropriate checks, reconciles authorized shared changes, and commits a coherent checkpoint to `main`.

## Ownership and parallelism

- ATLAS owns implementation and integration in the canonical product repository.
- SCOUT owns public-source reconnaissance and returns evidence to ATLAS.
- PROBE owns installed-client and live-account reconnaissance and returns validated observations to ATLAS.
- Default ATLAS ownership is `src/`, `tests/`, database/schema, CLI, integration, optimization, and shared application code.
- Default SCOUT ownership is source reconnaissance, evidence reports, strategy claims, source lineage, and version research, preferably in Scout-specific documentation/evidence artifacts.
- Default PROBE ownership is `tools/probe*`, PROBE documentation, client inspection, and specifically assigned perception/navigation code; raw probe evidence remains ignored.
- Agents may read across the repository, but may modify another role's default domain only when the current mission explicitly grants ownership.
- If potential file or domain overlap is detected, stop editing that file and report the overlap instead of competing with another agent.
- Multiple agents may work simultaneously only when file and data ownership do not conflict. Agents must not modify another role's worktree.