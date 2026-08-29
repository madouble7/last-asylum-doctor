# Doctor's Companion - Architecture Decisions

This is a lightweight log of consequential decisions. It is not a record of
every implementation detail.

## ADR-001 - Doctor's Companion frames the player as the Doctor

Status: Accepted

Decision: The product is Doctor's Companion, and a player is a Doctor. The
software itself is not called "the Doctor."

Rationale: This keeps product terminology clear and leaves room for
player-specific recommendations without confusing the tool with its user.

Tradeoffs: Documentation must preserve the distinction consistently.

Revisit if: The product identity or audience changes.

## ADR-002 - Evidence comes before facts and recommendations

Status: Accepted

Decision: Preserve raw evidence and provenance, then normalize validated facts,
then calculate and recommend. Never invent missing game facts or silently
resolve conflicts.

Rationale: The Companion must remain auditable across servers, versions, and
account eras.

Tradeoffs: Incomplete outputs are sometimes preferable to convenient answers;
review work is required before uncertain data becomes canonical.

Revisit if: A replacement evidence model provides equal or better auditability.

## ADR-003 - Research dependencies are not inferred from ordering or IDs

Status: Accepted

Decision: Research tree order, numeric IDs, proximity, and guide layout do not
prove prerequisite edges or building gates. Store them as unverified leads until
validated by direct source or client evidence.

Rationale: Static data can expose node identity without exposing engine
conditions, and false dependencies would corrupt planning.

Tradeoffs: The dependency graph grows more slowly and may contain gaps.

Revisit if: A source exposes explicit, scoped prerequisite conditions with
adequate provenance.

## ADR-004 - Optimize marginal value, not Might by default

Status: Accepted

Decision: Economic and progression analysis should compare transparent marginal
value and the Doctor's stated objective, rather than optimize aggregate Might
as an assumed universal objective.

Rationale: Different Doctors value readiness, recovery, research, events, and
spending constraints differently; Might alone can reward the wrong action.

Tradeoffs: Recommendations require explicit assumptions and may not yield one
single global ranking.

Revisit if: The Doctor explicitly chooses a different objective for a bounded
analysis.

## ADR-005 - One canonical repository with shared-main specialist workflow

Status: Accepted

Decision: ATLAS, SCOUT, and PROBE operate against the canonical repository on
`main` in separate role windows. Work is coordinated in the shared worktree;
changes are not synchronized through routine branches or cherry-picks.

Rationale: The solo development workflow needs visible continuity across
specialist conversations and a single source of project state.

Tradeoffs: Shared-main work requires ownership discipline and explicit
integration checkpoints.

Revisit if: Concurrent scale or isolation requirements justify separate
worktrees and a different integration model.

## ADR-006 - ATLAS is the explicit integrator

Status: Accepted

Decision: ATLAS owns canonical production implementation and integration. A
checkpoint explicitly designates ATLAS as INTEGRATOR before staging or
committing the coherent sprint.

Rationale: One role must inspect cross-agent changes, run authoritative checks,
and reconcile the resulting checkpoint.

Tradeoffs: Integration is a deliberate step rather than an automatic side
effect of specialist work.

Revisit if: Repository ownership is reorganized.

## ADR-007 - Role names are independent of models and providers

Status: Accepted

Decision: ARCHITECT, ATLAS, SCOUT, PROBE, and ENGINEER name durable
responsibilities, not a particular AI model, vendor, or provider.

Rationale: Project continuity should survive tool and model changes.

Tradeoffs: Agent configuration must keep role contracts explicit.

Revisit if: The operating organization changes materially.

## ADR-008 - Live automated input is paused outside normal production mode

Status: Accepted

Decision: PROBE's ADB input adapter remains an experimental, policy-reviewed
fixture. Account-changing automation is prohibited, and automated input is not
normal Server 283 production operation.

Rationale: Passive observation preserves account state and reduces operational
risk while evidence quality is established.

Tradeoffs: Some navigation evidence must be collected manually or through
carefully bounded read-only routes.

Revisit if: An explicit safety review authorizes a narrowly defined change.

## ADR-009 - Passive Shadow Observer is the live reconnaissance direction

Status: Accepted

Decision: Use Shadow Observer v0.1 as the first live reconnaissance direction:
passive ADB/display capture, local classification/OCR, duplicate suppression,
bounded evidence, and append-only observations.

Rationale: It lets a Doctor play normally while the system collects auditable
observations without game input.

Tradeoffs: It does not yet normalize account facts or guarantee OCR quality;
live acceptance is still required.

Revisit if: Passive capture cannot produce sufficient evidence or the client
observation boundary changes.

## ADR-010 - Durable project state belongs in the repository

Status: Accepted

Decision: Material project state, architecture decisions, evidence posture, and
role contracts belong in repository files, not in one AI conversation.

Rationale: Conversations are transient and cannot reliably serve as the
canonical briefing for future decisions.

Tradeoffs: State files need concise maintenance and can become stale if not
updated at material checkpoints.

Revisit if: A durable, versioned project-state system supersedes repository
records without reducing auditability.

## ADR-011 - VS Code Agents window is for specialist experiments

Status: Accepted

Decision: ENGINEER uses the VS Code Agents window for specialist and
experimental engineering work. It does not replace the standing ARCHITECT,
ATLAS, SCOUT, or PROBE departments at this stage.

Rationale: Experiments benefit from an independent role while product direction,
production integration, external evidence, and client observation retain clear
owners.

Tradeoffs: ENGINEER findings require handoff and clean ATLAS integration rather
than silently entering production.

Revisit if: The role topology or integration workflow is intentionally changed.
