# Last Asylum Doctor

Last Asylum Doctor is a future intelligent companion for *Last Asylum: Plague*. It will help players understand progression, manage resources, evaluate purchases, and choose practical next steps.

## Long-term goals

The project is intended to combine verified game data with upgrade dependencies, building requirements, shop and pack price history, strategy rules, player progression state, and a quest-style check-off workflow. These pieces will eventually support personalized recommendations that update as a player marks progress complete.

## Architecture principle

The project keeps four layers separate:

1. **Factual game data** — verified information about the game.
2. **Calculated efficiency** — transparent calculations derived from factual data.
3. **Strategic judgment** — explicit rules and trade-offs for choosing among options.
4. **Player-specific recommendations** — advice based on a player's recorded progression state.

The recommendation layer must never invent missing factual game data.

## Initial research-data milestone

The first planned data milestone is a verified research record for **DEF Boost III**, including the factual information needed to represent it accurately and connect it to later dependency work.

## Existing Google Sheets guide

Google Sheets currently contains the existing shop/value guide. It may become one data source in the future, but it is not intended to be the primary application interface.

## Development

Create or activate the local Python environment, then run:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The starter command is available after installing the project:

```powershell
last-asylum-doctor
```

Targeted science ingestion requires explicit slugs and never defaults to all nodes:

```powershell
last-asylum-doctor ingest-science def-boost-iii research-upgrade-iii training-points
```

See [the ingestion documentation](docs/ingestion.md) for the source pipeline,
caching behavior, validation rules, and failure modes.

Initialize the local factual-data database and persist an explicit ingestion:

```powershell
last-asylum-doctor init-db
last-asylum-doctor ingest-science def-boost-iii research-upgrade-iii training-points --store-db
last-asylum-doctor show-research def-boost-iii
```

See [the database documentation](docs/database.md) for the factual SQLite schema
and its provenance behavior.

Before any broad research ingestion, run the bounded compatibility audit:

```powershell
last-asylum-doctor audit-science-schema
```

See [the science schema audit](docs/science_schema_audit.md) for its sampling
method, source-field findings, and readiness decision.
