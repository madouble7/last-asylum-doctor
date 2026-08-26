# Full science-corpus ingestion

This workflow belongs only to Last Asylum Doctor's **factual game data** layer. It retrieves verified research records and provenance; it does not calculate efficiency, choose strategy, track a player, or generate recommendations.

## Explicit command

Full ingestion is deliberately opt-in and requires SQLite storage:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe ingest-science --all --store-db --output data\processed\research_corpus.json
```

The existing targeted command remains available and never turns into a crawl:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe ingest-science def-boost-iii --store-db
```

`--all` cannot be combined with explicit slugs. It also requires `--store-db`, so a broad retrieval is always retained as factual/provenance evidence rather than being an accidental transient action.

## Discovery and reconciliation

At the start of every full run, the command refreshes `robots.txt`, discovers the current Vite entry bundle, parses the current sitemap, and extracts the current science dynamic-import map. It reports:

- sitemap science-slug count;
- import-map science-slug count;
- usable intersection count;
- sitemap-only slugs; and
- import-map-only slugs.

Only the intersection is requested as detailed ESM modules. Mismatches are retained in `research_corpus.json` and printed by the CLI; they are never silently treated as complete coverage.

## Request discipline and cache

The existing HTTP client makes ordinary sequential requests with a descriptive User-Agent, explicit timeouts/retries, pacing, and a one-hour content-addressed cache. A fresh robots-policy check happens before each broad run. The tool stops before detailed retrieval if robots disallows an intended asset path.

It does not use browser automation, downloaded-JavaScript execution, authentication bypass, or anti-bot bypass.

Use `--refresh` only when a fresh source retrieval is necessary. A normal rerun within the cache window is useful for proving database idempotency without unnecessary detailed remote requests.

## Acceptance and partial failures

Every detailed module is parsed and normalized independently. Unknown factual source fields, parser changes, invalid identities, invalid level sequences, and invalid values remain hard failures for that node; facts are never guessed or silently dropped.

If one detailed node fails, its slug and exact error are written to the generated corpus JSON and printed by the CLI. Successfully validated nodes are still stored transactionally. The associated `ingestion_runs` row is marked `failed`, with accurate nonzero `failed_count` and `succeeded_count`; it is not falsely reported as a complete run. A database write failure rolls back that factual write transaction.

Rerunning is safe: node, level, and cost facts are upserted without duplicates. A new ingestion run and one provenance observation per accepted node are intentionally retained. The run summary compares source content hashes against the prior observation and reports new, changed, and unchanged assets.

## Database validation and profile

After a full run, the command validates the local database, including SQLite/foreign-key integrity, required identities and provenance, nonnegative factual values, level count/contiguity, duplicate logical records, and run state. It explicitly checks DEF Boost III level 1 against the verified exact values.

The generated descriptive profile is written to:

```text
data/processed/science_corpus_profile.json
```

It reports counts, research-tree inventory, source resource/item identifiers, maximum-level distribution, cost shapes, zero-cost and zero-time levels, optional values, and source/parser/schema anomalies. These are factual descriptions only—not assessments of research value.

## Safe reruns after a source deployment

After Last Asylum Database deploys new assets, first run the bounded compatibility audit:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe audit-science-schema --refresh
```

Then run the explicit full command with `--refresh`. If the source shape changes, let validation fail, inspect the generated evidence, add the smallest justified compatibility support and regression test, and rerun. Do not skip or invent data to force completion.
