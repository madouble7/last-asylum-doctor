# Shop Doctor ingestion

The Shop Doctor workbook is a local, user-provided economic/acquisition source. It is not a game-authoritative source and must remain unmodified and Git-ignored under `data/imports/`.

## Source and provenance

Each import reads the real `.xlsx` with `openpyxl` in read-only mode and stores a source snapshot containing its filename, SHA-256, byte size, sheet names, maximum observed workbook date, and ingestion time. Every raw observation also retains its source sheet and row.

The v5.2 adapter expects the workbook's `LIVE OFFERS`, `CASH PACKS`, `PACK CONTENTS`, `ITEM CATALOG`, `CALC ENGINE`, and `ADVANCED SETTINGS` sheets. It fails safely if a required sheet, canonical item reference, pack reference, normalization check, or bonus-Diamond assumption is invalid.

## Commands

```powershell
last-asylum-doctor inspect-shop-doctor data\imports\shop_doctor_v5_2_2026-08-27.xlsx
last-asylum-doctor ingest-shop-doctor data\imports\shop_doctor_v5_2_2026-08-27.xlsx --store-db
last-asylum-doctor show-item gearstone
last-asylum-doctor show-item-prices speedup
```

`inspect-shop-doctor` performs no database writes. `ingest-shop-doctor` requires `--store-db` deliberately. Re-ingesting an identical workbook hash creates no duplicate snapshot, offer, pack, component, conversion, or model observation.

## Raw facts versus workbook model output

Raw facts include the offer/shop/currency/date, actual package fields, quantity, price, cash-pack header, pack component, and item-catalog relationship data. They are stored separately from formula-driven workbook outputs such as VE$, historical best/median price, and catalog scoring/Alliance Duel fields.

`economic_model_observations` retains useful workbook calculations with `status = WORKBOOK_MODEL`. Those values are not game facts and must not be used as facts in a future recommendation layer. In the current v5.2 snapshot, the 358 workbook-model observations remain separate from raw offer observations, canonical item definitions, cash-pack contents, choice/conversion relationships, and currency/source observations.

## Canonical item reconciliation

The current live Shop Doctor v5.2 catalog contains **37 populated canonical item rows**. This is the reconciled count; an earlier approximate reference to about 41 items was an overcount. Counts are validation outputs and are not hard-coded in production logic.

## Alliance Duel fields

Alliance Duel (AD) data is ancillary to Last Asylum Doctor. Shop Doctor AD fields may combine source/published values, account-adjusted values, manual overrides, and historical tracker assumptions. They must not automatically be treated as authoritative canonical game facts, and core economic or acquisition calculations must not depend on AD accuracy.

## Normalization rules preserved from v5.2

- **Speedup** is one canonical item with a `1 minute` base unit. Package denomination and speedup type remain metadata.
- `actual_item_count × base_units_per_item` must equal the normalized quantity when both fields are present.
- Cash-pack `Assumed Bonus Diamonds` is stored with `DERIVED_ASSUMPTION`, validated as `ROUND(price × 100)`, and never treated as observed contents.
- Pack statuses such as `PARTIAL / MINIMUM KNOWN`, `PRICE MISSING`, and `PRICE MISSING / NEED DATA` remain source statuses. Unknown components are not zero.
- `CHOOSE ONE` contents create mutually exclusive options. They are not added together.
- `CONVERTS TO` retains both the supply container and its context-specific output.

## Current v5.2 examples

At Sanctuary Lv26, the workbook defines antitoxin supply conversions separately from their container identity: SR → 0.678M Antitoxin, SSR → 5.4M, and UR → 16.3M. It defines SSR/UR Resource Supplies as choose-one resource options and defines Deluxe Choice Chest as one choice among Raven Essence, Gearstones, Raven Gear Chest Lv5, or UR Resource Supplies. The nested UR Resource Supply graph is retained rather than flattened.
