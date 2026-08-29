# Research Effects and Prerequisite Source Hunt

**Status:** Completed
**Investigation date:** 2026-08-29
**Scope:** Server 283 player horizon; source reconnaissance for numeric research
 effects, effect units, prerequisite edges, and building or tree gates.

## Calibrated findings

- **FACT:** Last Asylum Database exposes the current structured research baseline:
  348 nodes across 18 trees, 2,287 levels, names, descriptions, layout metadata,
  costs, base times, and research power. It does not expose numeric gameplay
  effects, effect units, prerequisite relationships, or building gates.
- **FACT:** Last Asylum Unofficial's client schema contains promising structures:
  `ability` payloads for numeric values and `precondition` tuples where condition
  `20201` maps a required technology ID and level. This is schema evidence, not
  retrieved gameplay data.
- **FACT:** No actual research records were retrieved anonymously from the
  Unofficial endpoint. The endpoint returned an authentication-required error;
  no authentication or access-control bypass was attempted.
- **FACT:** Reviewed live UI/OCR from PROBE remains the direct validator for exact
  visible effects and prerequisite text on the active Server 283 account.
- **VERSION_SIGNAL:** Public APK metadata reported `com.phs.global` version
  `1.0.99` / code `99` on 2026-08-27. This is not an installed-client
  observation. Historical live observations retain client `1.0.97` / code `97`.

## Source lineage and scope

- Last Asylum Database: public static ESM assets; canonical baseline for costs,
  times, power, and metadata only.
- Last Asylum Unofficial: public client bundle/schema analysis; candidate schema,
  but research payload access is authentication-gated.
- Live game UI / PROBE: direct Server 283 observations, requiring visual review;
  OCR confidence is not factual proof.
- Community guides, wiki material, and strategy sites: partial, dated or
  derivative context; useful for hypotheses, not a granular canonical matrix.

## Integration rule

Do not add inferred effect values or prerequisite edges to canonical factual
records. Future captures should record the node identity, level, visible effect
change and unit, building gate, parent-node gate, cost/time parity, source
metadata, screenshot hash, and human validation status.
