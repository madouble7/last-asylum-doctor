# Research Structured Access Validation

**Status:** Completed
**Date:** 2026-08-29
**Scope:** Normal unauthenticated public access to structured research data.

## Findings

- **FACT:** Last Asylum Unofficial's `getResearchData` function returned an
  authentication-required HTTP 500 response for unauthenticated requests. No
  research entity schema or research records were retrieved.
- **FACT:** The public client bundle still provides schema evidence for `types`,
  `techs`, `levels`, numeric `ability` values, and `precondition` data. Schema
  presence must not be reported as data access.
- **FACT:** No credentials were used or extracted, and access controls were not
  bypassed.
- **FACT:** Last Asylum Database remains accessible for the 348-node structured
  baseline of costs, base times, power, names, and metadata. Numeric effects,
  effect units, prerequisite technology IDs/levels, and building gates remain
  absent there.

## Source and version context

- Last Asylum Unofficial: `https://last-asylum-unofficial.com`; schema and
  endpoint behavior observed 2026-08-29.
- Last Asylum Database: `https://lastasylumdatabase.com`; public ESM baseline.
- Live account validation: Server 283, historical client `com.phs.global`
  `1.0.97` / code `97`.
- Public APK metadata for `1.0.99` / code `99` is only a `VERSION_SIGNAL` until
  detected locally.

## Decision

Unauthenticated automated research ingestion from Last Asylum Unofficial is not
available under the project's non-circumvention rules. Keep the Database source
as the cost/time/power baseline and use reviewed, read-only live observations for
missing effects and prerequisite edges.
