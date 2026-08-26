# Factual research database

The local SQLite database stores only verified factual research data. Its default location is:

```text
data/last_asylum.db
```

It is generated locally and Git-ignored. The implementation uses Python's standard-library `sqlite3` module and enables foreign-key enforcement for every connection.

## Scope

This database belongs exclusively to the project's **factual game data** layer. It stores source-backed research facts and their provenance.

It intentionally does **not** store strategy scores, calculated efficiency, subjective priorities, player progress, player-specific recommendations, quests, or account state. Those belong to later layers and must not contaminate factual tables.

## Schema and relationships

| Table | Purpose |
| --- | --- |
| `research_nodes` | One current factual record for each logical research slug. |
| `research_levels` | One row per research node and level. Unique on `(research_node_id, level)`. |
| `research_level_costs` | Generic source-preserving cost rows for each research level. Unique on `(research_level_id, resource_identifier)`. |
| `ingestion_runs` | One record for each requested database-storage run and its outcome. |
| `research_source_observations` | The source metadata observed for each node in each ingestion run. |

```text
research_nodes 1 ──< research_levels 1 ──< research_level_costs
      │
      └──< research_source_observations >── 1 ingestion_runs
```

`research_nodes` holds current source-backed metadata such as name, tree, effect, maximum level, source page URL, source asset URL, and first/last seen timestamps.

`research_levels` holds the exact numeric power, normalized time in seconds, original source time text, and source level record ID when supplied.

## Generic resource costs

Costs use rows instead of fixed `farm_cost`, `herb_cost`, or `scroll_cost` columns. Research nodes have different source shapes, and later sources may introduce additional items.

Each cost row preserves:

- a mechanical identifier derived from the source label, such as `study_scroll`;
- the original source label, such as `Study Scroll`;
- the exact integer amount;
- source item ID and source-formatted amount when supplied.

No semantic remapping is performed. In particular, source `Farms` remains `farms`; it is not silently renamed to Grain.

## Provenance and raw evidence

Each persisted node receives a `research_source_observations` row for its ingestion run. It records the source page and ESM asset URLs, source retrieval timestamp, content SHA-256, ETag, Last-Modified value, and content type when supplied.

The raw response cache under `data/raw/http/` retains the retrieved source bytes. Database observations point to their identifying metadata, so a stored factual value can be audited back to a particular source asset and raw cache checksum.

## Idempotency and updates

Persisting the same normalized nodes again:

- does not duplicate `research_nodes`;
- does not duplicate levels or cost rows;
- creates a new `ingestion_runs` record and source observation for audit history.

When source facts change, the current node, level, and cost rows are updated in one transaction. Old cost rows are replaced by the current source's complete cost set, and obsolete levels are removed if the verified source level range changes. The prior source observation remains available through its earlier ingestion run and the raw cache.

Database writes validate foreign keys before commit. A failed storage transaction is rolled back and its run is recorded as failed instead of partially updating factual tables.

## CLI usage

Initialize a database:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe init-db
```

Retrieve only explicit source nodes and store them after normalization:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe ingest-science def-boost-iii research-upgrade-iii training-points --store-db
```

Use a different database path when needed:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe init-db --database data\validation.db
.\.venv\Scripts\last-asylum-doctor.exe ingest-science def-boost-iii --store-db --database data\validation.db
```

Inspect only stored factual data:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe show-research def-boost-iii
```

The ingestion command still requires explicit slugs. It never defaults to all discovered research nodes.
