# LastAsylumDatabase.com source reconnaissance

Investigation date: 2026-08-26

Scope: read-only reconnaissance of the science index and the **DEF Boost III** page. This document describes the site's current public build; asset hashes may change after any deployment.

## Executive conclusion

**Confidence: HIGH**

The site is a client-side React application built with Vite. The initial HTML for both `/science` and `/science/def-boost-iii` is only an application shell. It contains an empty `<div id="root"></div>` and loads the main JavaScript bundle:

```text
https://lastasylumdatabase.com/assets/index-Bx4NNJcK.js
```

The detailed DEF Boost III data is not server-rendered, embedded in the initial HTML, or fetched from a JSON/API endpoint. The main bundle contains a dynamic-import map that maps the logical build-time source path:

```text
../content/science/def-boost-iii.json
```

to this publicly retrievable, page-specific JavaScript module:

```text
https://lastasylumdatabase.com/assets/def-boost-iii-C6p9jdId.js
```

That module contains the metadata and all ten detailed level records as JavaScript values and exports them as an ES module. It is the earliest practical structured source currently exposed by the deployed site.

The logical `.json` path appears to identify the site's build-time source file, but it is not deployed as public JSON. Requesting `/content/science/def-boost-iii.json` returns the generic HTML application shell with HTTP 200 and `Content-Type: text/html`.

## 1. How the page is rendered

An ordinary HTTP GET of `/science/def-boost-iii` returned a small HTML document with:

- an empty root element;
- one module script, `/assets/index-Bx4NNJcK.js`;
- one stylesheet, `/assets/index-CnenB1oj.css`;
- no DEF Boost III text or level table;
- no embedded application JSON or page-specific structured state;
- Vite-style hashed assets and a client-side route for `science/:slug`.

The main bundle initializes React with `createRoot`, defines the `science` and `science/:slug` client routes, and loads individual research records through dynamic imports. The browser-generated DOM is therefore a downstream rendering of the module data, not its original public source.

The effective flow is:

```text
build-time science JSON
    -> Vite-generated page-specific ESM chunk
    -> React client route/component
    -> rendered DOM
```

## 2. Where DEF Boost III data originates

The deployed main bundle includes this mapping (minified in production):

```javascript
"../content/science/def-boost-iii.json": () =>
  import("./def-boost-iii-C6p9jdId.js")
```

The bundle's science-node loader constructs the logical key `../content/science/${slug}.json`, invokes the mapped dynamic import, and returns the imported module's default export.

This shows that the site's maintainers likely author or generate the node as `content/science/def-boost-iii.json` before building the app. Vite transforms that input into a JavaScript module for deployment. The original JSON is not a public endpoint, so the deployed ESM chunk is the earliest practical source available to an external ingestion process.

## 3. Exact public source and related assets

Initial page:

```text
https://lastasylumdatabase.com/science/def-boost-iii
```

Current main bundle, which contains the catalog and chunk mapping:

```text
https://lastasylumdatabase.com/assets/index-Bx4NNJcK.js
```

Current detailed-data chunk:

```text
https://lastasylumdatabase.com/assets/def-boost-iii-C6p9jdId.js
```

Science index:

```text
https://lastasylumdatabase.com/science
```

Public sitemap:

```text
https://lastasylumdatabase.com/sitemap.xml
```

These hashed asset names are a snapshot, not stable permanent identifiers. A production process must rediscover them from the current HTML and main bundle on each source-version change.

## 4. Evidence that the chunk is the factual source

The page-specific module exports a default object with:

- `id: "11022"`
- `slug: "def-boost-iii"`
- `name: "DEF Boost III"`
- `description: "Soldier DEF"`
- `tab: "Elite Troop"`
- `tab_slug: "elite-troop"`
- `tech_type: 11`
- `max_level: 10`
- `levels_count: 10`
- `image: "/images/science/def-boost-iii.png"`
- `pos: "1_13_2"`
- a `levels` array containing exactly ten records

The raw records validate the known displayed values. For example:

| Level | Raw time | Raw power | Raw farms/lumber | Raw herbs | Study Scroll |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `11d 3h 46m 40s` / `964000` sec | `15020` | `31736000` | `97332000` | `1440` |
| 2 | `13d 10h 13m 20s` / `1160000` sec | `34510` | `54640000` | `164407000` | `1600` |
| 10 | `28d 8h 33m 20s` / `2450000` sec | `252020` | `194697000` | `584440000` | `2400` |

Those raw values produce the site's rounded display values such as `15.0K`, `31.7M`, `97.3M`, `1.44K`, and `252K`. The chunk also includes `raw_id` values `11022001` through `11022010`, duplicate compatibility fields such as `cost_food`, `cost_wood`, and `cost_iron`, and a normalized per-level `costs` array.

This is stronger evidence than matching rendered text: the module supplies both exact values and display-ready time strings to the client-side component.

## 5. How science nodes are discovered

The `/science` index uses `science_catalog.json`, which is compiled directly into the main bundle. Its entries contain each node's:

- `slug`;
- name and description;
- tab and tab slug;
- technology type;
- level count and maximum level;
- image path.

The catalog includes the DEF Boost III entry and supplies the slugs used to create `/science/{slug}` client-side links. A separate `science_tabs.json` object is also embedded in the main bundle.

The main bundle additionally contains a complete dynamic-import map from logical paths such as `../content/science/{slug}.json` to hashed page-specific chunks. This map connects a catalog slug to its detailed-data asset.

The public sitemap is a second, simpler discovery source. At investigation time it contained 814 URLs, including 348 `/science/{slug}` node URLs and the DEF Boost III URL. The sitemap is preferable for discovering public page URLs, while the embedded science catalog provides richer index metadata and the dynamic-import map provides the actual chunk lookup.

## 6. Network/API findings

No science JSON or application API endpoint was found.

Static inspection found only one `fetch(` occurrence in the main bundle, in Vite's module-preload compatibility code. The science loader itself uses a dynamic `import()` from the generated chunk map. There was no Axios reference and no `/api/` reference in the main bundle.

The relevant browser traffic is therefore expected to be ordinary static asset retrieval:

1. GET the route and receive the HTML shell.
2. GET the main JavaScript bundle.
3. Resolve the slug in the generated import map.
4. GET the page-specific ESM chunk.
5. Render the returned module data into the DOM.

No authentication, cookies, browser-only headers, or anti-bot bypass were needed for the reconnaissance requests. The HTML, bundle, chunk, robots file, and sitemap all responded to ordinary HTTP requests.

## 7. Is JavaScript execution required?

JavaScript execution is required for the website itself to render the table in a browser. It is **not required to retrieve the factual data**.

An ingestion tool can use ordinary HTTP GET requests to retrieve the HTML, main bundle, sitemap, and detailed chunk. It will still need a safe way to interpret the ESM module or transform its exported data into a language-neutral structure. That is parsing work, not browser automation.

## 8. Is Playwright/browser automation necessary?

No. Playwright is not necessary for the currently observed data path and should not be added for production ingestion solely for this source.

Browser/network inspection could be useful later as a diagnostic fallback if the site's build architecture changes, but it would add overhead and fragility without improving access to the present structured source.

## 9. Recommended production ingestion strategy

Use a conservative, version-aware ordinary-HTTP pipeline:

1. Fetch the current page or home HTML and extract the current `/assets/index-*.js` module URL.
2. Fetch the main bundle once per detected deployment version.
3. Use `/sitemap.xml` to enumerate public science page slugs, or extract the embedded `science_catalog.json` when its richer metadata is needed.
4. Extract the main bundle's logical-path-to-chunk mapping for `../content/science/*.json`.
5. Fetch only the required page-specific chunks, with caching, a clear user agent, low concurrency, and retry/backoff.
6. Parse the ESM data structurally and validate required fields, types, slug agreement, level count, unique levels, and raw IDs before accepting a record.
7. Save source URL, retrieval timestamp, asset hash/ETag, and validation result alongside ingested facts for provenance.
8. Treat a changed bundle layout or failed validation as a source-adapter failure; do not guess or fill missing factual fields.

For the first milestone, ingest only DEF Boost III and verify every exact raw value against a checked fixture before considering broader enumeration.

The parser should avoid broad regular expressions over the rendered page or arbitrary minified code. A small, isolated adapter for the observed ESM export shape is appropriate, with fixture tests and a deliberate failure mode when the structure changes. Before implementation, evaluate whether a lightweight JavaScript parser or an already-available local JavaScript runtime gives safer deterministic decoding without adding a browser dependency.

## 10. Risks and fragility

- **Hashed asset paths change:** both the main bundle and node chunk names may change on every deployment.
- **Build layout is not an API contract:** Vite may change minification, code splitting, import-map construction, or export shape.
- **Logical JSON is not public:** `/content/science/*.json` currently falls back to HTML, so it cannot be used as a stable endpoint.
- **Catalog and sitemap may diverge:** validate that discovered slugs exist in the import map before requesting chunks.
- **JavaScript is not JSON:** unsafe evaluation must be avoided; use a constrained parser/runtime and validate the resulting object.
- **Source values may change:** retain provenance and detect changes rather than silently overwriting verified facts.
- **HTTP 200 can be misleading:** SPA fallback paths can return HTML with status 200, so always verify `Content-Type` and expected structure.
- **Site ownership and usage terms:** before broad ingestion, review applicable terms and keep request volume respectful even though `robots.txt` currently allows the science paths.

## 11. Classification against the candidate mechanisms

| Candidate mechanism | Finding |
| --- | --- |
| Server-rendered HTML | No; the initial root is empty. |
| JSON/API/network endpoint | No public JSON/API endpoint found. |
| JSON embedded in initial HTML | No. |
| Statically bundled JavaScript data object | Yes for the science catalog and tabs in the main bundle. |
| Dynamically imported module/chunk | Yes; this is where the detailed DEF Boost III record lives. |
| Client-rendered DOM | Yes, but it is downstream of the dynamic module. |
| Other mechanism | The public sitemap also exposes the node URLs. |

## Request discipline used in this investigation

Only a small number of direct GET/HEAD requests were made for the two target routes, their referenced assets, the guessed logical JSON path, `robots.txt`, and `sitemap.xml`. No crawling, authentication bypass, site modification, or production scraper implementation was performed. No project dependency was installed.
