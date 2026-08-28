# Economic database

The economic/acquisition layer shares the local SQLite database with research but uses independent tables. Research tables and source vocabulary remain unchanged.

```text
source_snapshots ──< offer_observations >── items
       │                    │                 │
       ├──< cash_packs ──< cash_pack_components
       ├──< choice_groups ──< choice_options >─┘
       ├──< currency_valuation_assumptions >── currencies
       └──< economic_model_observations

items ──< item_aliases
items ──< item_domain_keys
```

`source_snapshots` is immutable by SHA-256. `offer_observations`, `cash_packs`, and `cash_pack_components` are unique by snapshot, sheet, and source row, which preserves history and makes identical imports idempotent.

`items` is the canonical Doctor registry. `item_aliases` preserves workbook terminology and aliases; `item_domain_keys` bridges other factual domains without rewriting their source records.

`choice_groups`/`choice_options` describe both `CHOOSE ONE` and `CONVERTS TO` relationships. A choice option may itself be a container with its own group, so nested choices remain graph-shaped.

`currencies` may represent a literal currency, an event token, or an internal choice-container route. `currency_valuation_assumptions` stores the workbook's stated classification: direct/observed cash anchor, derived valuation assumption, or unanchored.

`cash_packs.bonus_diamonds_status` records that bonus Diamonds are derived assumptions. Pack valuation status is kept verbatim; a partial pack is a minimum-known value, never a complete zero-filled valuation.

Use `PRAGMA integrity_check` and `PRAGMA foreign_key_check` after imports. The CLI ingestion validates both plus the workbook's reference and normalization invariants.

