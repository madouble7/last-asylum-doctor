# ADR-012 - Asynchronous agent signals

Status: Accepted

## Decision

Use one durable Markdown signal file per operational agent session under
`docs/agent_signals/`. Signals are asynchronous handoffs and status records;
they do not grant repository permissions or replace the project ownership and
integration rules.

## Rules

- Each signal file has exactly one writer: the agent named by the file.
- Other agents may read signal files but must not edit them.
- Valid signal types are `DRIFT`, `BLOCKER`, `EVIDENCE`, and
  `CONTEXT_HEALTH`.
- Signals must preserve the distinction between reported information,
  observed evidence, inference, and unresolved uncertainty.

## Escalation

Escalate to Matt when a signal reports `DRIFT` or `CONTEXT_HEALTH`. The
escalation must identify the affected work, the evidence or symptom, and the
decision or intervention needed from Matt.

## Rationale

Per-agent files provide a low-overhead asynchronous handoff surface while the
single-writer rule prevents competing edits and preserves accountability.

## Tradeoffs

Signals remain intentionally lightweight and require Matt to resolve drift or
context-health concerns. They are not a substitute for canonical project state,
architecture decisions, tests, or explicit integration checkpoints.
