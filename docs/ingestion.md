# Science ingestion

Last Asylum Doctor's first production ingestion path retrieves factual research data from the static assets published by LastAsylumDatabase.com. It does not render pages, execute downloaded JavaScript, or use Playwright.

## Pipeline

The targeted pipeline performs these steps sequentially:

1. Fetch and enforce `robots.txt` for every intended source path.
2. Fetch the `/science` HTML shell.
3. Discover the current same-origin Vite `index-*.js` module from the HTML.
4. Fetch `sitemap.xml` and enumerate public `/science/{slug}` URLs.
5. Parse the main bundle's generated mapping from logical `content/science/{slug}.json` names to current hashed ESM chunks.
6. Fetch only the chunks for explicitly requested slugs.
7. Parse each data-only ESM module with a restricted literal parser.
8. Normalize and validate each research record.
9. Write human-readable JSON under `data/processed/`.

Asset hashes are always rediscovered. No current `index-*` or node-chunk hash is hard-coded.

## Module responsibilities

- `scraping/client.py` provides timeouts, a descriptive user agent, sequential pacing, transient retry handling, and content-addressed raw caching.
- `scraping/discovery.py` parses HTML, sitemap XML, robots rules, and the Vite science import map.
- `scraping/esm.py` safely parses the observed variable/literal/export module shape without `eval`, `exec`, or JavaScript execution.
- `scraping/science.py` coordinates targeted retrieval, normalization, validation, and JSON output.
- `models/research.py` defines the typed factual domain model and its invariants.
- `cli.py` requires explicit slugs and exposes no crawl-all behavior.

## Raw caching and provenance

Exact response bytes are stored beneath `data/raw/http/objects/`, named by SHA-256 checksum. Each object has metadata recording its source URL, retrieval timestamp, checksum, ETag, Last-Modified value, and content type when supplied. A URL-keyed index permits reuse of responses newer than one hour.

The raw and processed directories are intentionally Git-ignored. Downloaded third-party assets must not be committed.

Normalized nodes retain the detailed module's source page URL, source asset URL, and retrieval metadata. This allows a processed fact to be traced back to the cached evidence that supplied it.

## Normalization philosophy

Numeric values already present in the source module are authoritative. Presentation text such as `15.0K` is not reparsed when the module supplies exact `power` data.

Research costs are resource-agnostic. Each level contains:

- a convenient `costs` mapping, using a mechanical identifier derived from the source label;
- `source_costs`, preserving the original label, amount text, and item ID.

For example, `Study Scroll` becomes the mechanical identifier `study_scroll`, but no attempt is made to rename Farms to Grain or impose future canonical game-resource semantics.

## Three-node production validation

The initial live validation confirmed three distinct source cost shapes:

| Research node | Tree | Levels | Cost identifiers |
| --- | --- | ---: | --- |
| `def-boost-iii` | Elite Troop | 10 | `farms`, `lumber`, `herbs`, `study_scroll` |
| `research-upgrade-iii` | Full Development | 5 | `farms`, `lumber`, `herbs` |
| `training-points` | Alliance Duel | 10 | `study_scroll` |

DEF Boost III level 1 contains exact source power `15020`. The website formats that value as `15.0K`; `15000` is therefore a rounded interpretation, not the underlying source fact. The normalized output preserves `15020` in accordance with the numeric-source-first policy.

## Validation and failure behavior

Ingestion fails rather than guessing when:

- a requested slug is malformed, duplicated, missing from the sitemap, or missing from the bundle map;
- robots rules disallow an intended request;
- the HTML, sitemap, bundle map, or ESM structure changes unexpectedly;
- required identity fields are blank;
- `max_level` is not positive;
- source `levels_count`, actual record count, and `max_level` disagree;
- levels are not contiguous from 1 through the maximum;
- time, power, or a cost is negative;
- a resource appears twice in one level;
- a source value has an unexpected type.

The CLI also limits a targeted run to 25 explicit slugs. Broad ingestion is intentionally not implemented.

## Run targeted ingestion

Install the project and development tools into the existing environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run the three-node validation sample:

```powershell
.\.venv\Scripts\last-asylum-doctor.exe ingest-science def-boost-iii research-upgrade-iii training-points
```

The default normalized output is:

```text
data/processed/research_sample.json
```

Use `--refresh` only when a current network retrieval is required instead of a recent cached response. Requests remain sequential and paced.

## Why a browser is unnecessary

The initial page requires JavaScript to render, but its structured factual data is already available in ordinary static ESM assets. Direct HTTP retrieval is smaller, more auditable, and easier to validate than browser-generated DOM extraction. Browser automation should remain a diagnostic fallback only if the site's source architecture changes.
