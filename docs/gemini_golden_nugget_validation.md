# Gemini Golden Nugget Validation

Snapshot: 2026-08-28 (America/Chicago)

Scope: targeted validation only; no broad Last Asylum reconnaissance

Decision labels: **CONFIRMED**, **LIKELY**, **UNCONFIRMED**, **INCORRECT**

## A. Executive verdict

Gemini found one genuinely valuable source and one technically real package lead, but it appears to have promoted several leads into conclusions before inspecting the evidence.

- **Last Asylum Unofficial is useful.** It is a separate Base44 application with ordinary public, read-only structured resources. It exposes building, hero-progression, item, pack, event, and server-milestone records. It should be treated as a corroborating community dataset, not yet as an independent authority.
- **Its coverage is uneven.** The building data is unusually strong and exactly matches Doctor's existing Sanctuary 26–30 reference values. The hero tables have material gaps and a duplicate conflict. The site itself labels basic Hero Gear progression as outdated.
- **The Android package claims stop at packaging metadata.** `com.phs.global`, current version/build `1.0.99 (99)`, split delivery, and the current split/module name `abPack1` are confirmed. Public metadata examined here does **not** establish Unity, Unity AssetBundles, IL2CPP, Mono, readable progression tables, or that `abPack1` contains any particular data.
- **Static-data extraction is a reasonable experiment, not a confirmed source.** Android/Unity games commonly ship some local assets and configuration, but Last Asylum-specific item, hero, research, building, cost, prerequisite, and future-system tables have not been demonstrated in the package.
- **Several source-quality claims are overstated.** A Discord invite proves only that an invite exists. `yt-dlp` being open source does not make a YouTube-download workflow automatically compliant. Qwen and RapidOCR are credible OCR candidates, but their general benchmarks do not validate them on Last Asylum UI. The unofficial Server Age tool is a manually indexed community milestone timeline; it does not derive an exact age from a server number.

The Gemini review and its original citation list were not present in this worktree or the supplied attachment. Consequently, the audit below tests the named claims against the strongest discoverable sources; it cannot verify whether Gemini quoted a different, unavailable citation accurately.

### Claim matrix

| Statement | Verdict | What the evidence establishes |
|---|---|---|
| Last Asylum Unofficial is a separate technical implementation | **CONFIRMED** | Separate domain, Base44 app ID, public entity schema, and no references to LastAsylumDatabase, SatoriMeta, or lastasylumwiki in the inspected client bundle. |
| Its factual data was independently derived from those sites | **UNCONFIRMED** | No methodology, source credits, or lineage statement was found; exact overlapping building values are identical. |
| The site is currently maintained | **LIKELY** | Its JavaScript asset was redeployed on 2026-08-28 and Pack rows extend to 2026-07-19, but most core tables were last edited in March–May. |
| The site has complete Antitoxin, Skill Badge, and star/shard tables | **INCORRECT** | Antitoxin: 127/150 populated; Skill Badges: 21/30 populated; stars: 50 rows but 49 unique keys, with missing and conflicting coordinates. |
| The site has useful building calculators/data | **CONFIRMED** | 50 buildings, 754 upgrade rows, costs, times, might, dependencies, and calculator UI. |
| The site provides exact server age from server number | **INCORRECT** | The user enters an age taken from the in-game Monument; the page then filters 41 community milestones covering days 1–120. |
| The package name is `com.phs.global` | **CONFIRMED** | Official Play URL and current signed-bundle metadata agree. |
| Current Android version/build is `1.0.99 (99)` | **CONFIRMED** | APKMirror and APKPure both show the 2026-08-27 release; Google Play confirms the package but does not display versionName/versionCode publicly. |
| The app is delivered as split APKs / an XAPK-style mirror bundle | **CONFIRMED** | APKMirror lists a base APK plus 26 splits; APKPure packages the install set as XAPK. “XAPK” is a repository container term, not Google's publishing format. |
| A split/module named `abPack1` exists | **CONFIRMED** | Current 1.0.99 APKMirror metadata lists a 370.71 MB dynamic feature named `abPack1`; APKPure lists it in older variants too. |
| `abPack1` is proven to be a Unity AssetBundle pack | **UNCONFIRMED** | A Play asset/dynamic-feature name is arbitrary. Android documents that asset packs can be used by native, Java, or Unity apps, and Unity's own PAD integration says packs need not contain AssetBundles. |
| Last Asylum is proven to use Unity | **UNCONFIRMED** | No engine signature from the actual archives was available in the public metadata examined. |
| Last Asylum is proven to use IL2CPP or Mono | **UNCONFIRMED** | No observed `libil2cpp.so`, `global-metadata.dat`, or managed-assembly inventory. |
| The client/package contains readable progression tables | **UNCONFIRMED** | Neither split names nor size prove content. Archive inspection is still required. |

## B. Confirmed useful discoveries

1. **Public structured community data exists.** Ordinary unauthenticated `GET` requests to the site's own `/api/apps/.../entities/...` resources return JSON. A five-row [HeroLevel example](https://last-asylum-unofficial.com/api/apps/698a36b276613255c34c822b/entities/HeroLevel?sort=level&limit=5) returns level and Antitoxin fields. The app's [public setting](https://last-asylum-unofficial.com/api/apps/public/prod/public-settings/by-id/698a36b276613255c34c822b) is `public_without_login`.

2. **Building coverage is immediately useful for corroboration.** The site has 50 building definitions and 754 upgrade records with costs, time, might, and dependencies. Five high-value overlap checks matched Doctor's existing SatoriMeta/LastAsylumDatabase reference values exactly:

| Upgrade to | Grain | Timber | Herbs | Base time | Result |
|---:|---:|---:|---:|---:|---|
| Sanctuary 26 | 386,800,000 | 386,800,000 | 123,500,000 | 30d 23h 32m 17s | Exact match |
| Sanctuary 27 | 548,000,000 | 548,000,000 | 168,600,000 | 43d 8h 57m 12s | Exact match |
| Sanctuary 28 | 731,100,000 | 731,100,000 | 236,500,000 | 60d 17h 20m 4s | Exact match |
| Sanctuary 29 | 1,047,000,000 | 1,047,000,000 | 316,400,000 | 78d 22h 32m 4s | Exact match |
| Sanctuary 30 | 1,356,000,000 | 1,356,000,000 | 441,300,000 | 102d 14h 53m 43s | Exact match |

These values are independently visible in the [SatoriMeta Sanctuary table](https://satorimeta.com/en/last-asylum/buildings/sanctuary/) and [Last Asylum Database Sanctuary table](https://lastasylumdatabase.com/buildings/sanctuary). Agreement confirms the values, not source independence.

3. **Hero values match the Doctor reconnaissance source where both are populated.** The unofficial rows for Antitoxin levels 2, 10, 20, 30, 45, 50, 65, 70, and 100 are respectively `100`, `1,500`, `8,700`, `19,900`, `137,900`, `587,900`, `2,500,000`, `5,500,000`, and `34,600,000`. Skill levels 2, 10, 15, and 20 are `50`, `1,200`, `3,100`, and `6,900` badges. Those exact values occur in the [lastasylumwiki hero table](https://lastasylumwiki.com/docs/hero-upgrade-costs/). The unofficial site becomes incomplete after Antitoxin level 126 (apart from an isolated level 131 value) and after Skill level 21; the wiki continues with values such as Antitoxin level 150 = `176,000,000` and Skill level 30 = `18,400`.

4. **Pack data is structured, not just screenshots.** There are 87 Pack rows: 46 `Pack Shop`, 20 `Value Event`, 13 `Pop Up`, and 8 `Shop`. All 87 have item lists, 83 have numeric raw prices, and two use choice-item structures. This is a pack catalog and analysis input, not proof of complete current live-shop coverage.

5. **The package lead is real and current.** [APKMirror's 1.0.99 metadata](https://www.apkmirror.com/apk/37games-global/last-asylum-plague/last-asylum-plague-1-0-99-release/last-asylum-plague-1-0-99-android-apk-download/) records `com.phs.global`, version `1.0.99 (99)`, minimum API 24, target API 35, arm64-v8a, base APK plus 26 splits, and a 370.71 MB `abPack1` dynamic feature. [APKPure](https://apkpure.net/last-asylum-plague/com.phs.global/download) independently reports 1.0.99 (99), XAPK, arm64-v8a, and the 2026-08-27 date. The [official Google Play listing](https://play.google.com/store/apps/details?id=com.phs.global) confirms the application ID/developer relationship.

## C. Useful but unverified leads

- **Research calculator payload.** The public client calls a read operation named `getResearchData` and contains consumers for `types`, `techs`, `levels`, numeric tech IDs, cost arrays, `specialCost`, `upgradeTime`, `ability`, and prerequisite entries. It specifically interprets prerequisite ID `20201` using `param1` as a tech ID and `param2` as a level, and recognizes `item_research_info` as Study Scrolls. This strongly suggests a structured research payload behind the calculator. A direct anonymous call returned `500 Authentication required to view users`, so the payload itself was not obtained and should not be represented as publicly harvestable yet.
- **Client localization.** The current APK set has 24 language configuration splits. That is actual Last Asylum evidence for localized Android resources, but not yet evidence of a complete in-game localization table or stable keys.
- **`abPack1` as an asset-bearing module.** Its 370.71 MB size makes asset content likely. It remains unknown whether that content is textures/audio/video, Unity archives, another engine's resources, or any configuration data.
- **Qwen and RapidOCR.** Qwen2.5-VL has strong vendor-reported OCR/document benchmarks and RapidOCR provides lightweight offline OCR across several inference engines. Both deserve a controlled screenshot benchmark. Neither has been validated on small, stylized, compressed Last Asylum UI text.
- **Community Discord.** The Building Calculator links `https://discord.gg/3qJhXhYyJF`. This establishes a public invite string only. Membership, searchable history, advanced-server quality, permission to collect content, and Gemini's unspecified Discord assertions remain unconfirmed.

## D. Incorrect or overstated Gemini claims

Because Gemini's original sources are unavailable, “support” below means what the likely/strongest discoverable source actually supports.

| Gemini claim area | Source support audit | Verdict |
|---|---|---|
| APK/AssetBundle | APKMirror supports a split/module called `abPack1`; Android documentation says asset packs are generic and Unity documentation says Unity PAD packs need not contain Unity AssetBundles. Inferring Unity AssetBundles or tables from the name is extrapolation. | **UNCONFIRMED** |
| Exact package composition | The current APKMirror page supports base + 26 splits and itemizes base, one ABI, 24 languages, and `abPack1`. APKPure's “XAPK” and byte size describe its own mirror container. Treating one mirror's total bytes as Google's universal delivered size is overstated. | **CONFIRMED** for components; **UNCONFIRMED** for a universal byte-exact package |
| Unofficial datasets | The homepage supports the existence of tools/tables. Only the public JSON resources support row counts and fields. Calling hero coverage complete is false; calling data current from the homepage alone is unsupported. | **CONFIRMED** existence; **INCORRECT** completeness |
| Independence | A separate implementation is demonstrated. No public provenance establishes independent factual collection. Exact five-for-five Sanctuary agreement is consistent with a shared upstream snapshot or independent transcription of the same game values. | **UNCONFIRMED** factual independence |
| Discord | An invite link supports the existence of an invitation, not claims about content, expertise, server age, access permission, or ingestibility. | **UNCONFIRMED** beyond the link |
| YouTube/`yt-dlp` compliance | The [`yt-dlp` repository](https://github.com/yt-dlp/yt-dlp) documents a downloader and its software license. It does not grant rights to third-party video content. [YouTube's Terms](https://www.youtube.com/static?template=terms) restrict downloads and automated access except when authorized by the service or rights holders. YouTube permits users to [view public transcripts](https://support.google.com/youtube/answer/15930243), while the official [`captions.download` API](https://developers.google.com/youtube/v3/docs/captions/download) requires authorization and edit permission. “Using yt-dlp is compliant” is therefore an overbroad assertion. | **INCORRECT** as a blanket claim |
| Qwen recommendation | The [Qwen2.5-VL-7B model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) reports OCRBench, TextVQA, DocVQA, and screen-control evaluations. That supports candidacy, not Last Asylum accuracy or superiority at the intended hardware/cost. | **LIKELY** useful; exact recommendation **UNCONFIRMED** |
| RapidOCR recommendation | [RapidOCR documentation](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/usage/) supports an offline OCR pipeline with ONNX Runtime and PP-OCR models. It provides no Last Asylum benchmark. | **LIKELY** useful; exact accuracy **UNCONFIRMED** |
| Exact server age | The unofficial page instructs users to read age from the in-game Monument and manually enter it. It does not map server 283—or any server number—to a date or age. Its milestones are community records, not an official release calendar. | **INCORRECT** if presented as automatically exact |

## E. Last Asylum Unofficial source assessment

### Independence and access model

The [homepage](https://last-asylum-unofficial.com/) identifies itself as “Community tools and calculators for Last Asylum players.” The inspected application is a standalone Base44 app (`698a36b276613255c34c822b`) with its own entity names and public-read configuration. Neither the page HTML nor the inspected 2026-08-28 client bundle references LastAsylumDatabase, SatoriMeta, or lastasylumwiki.

That proves **technical separation**, not independent authorship of facts. No source/methodology page, evidence ledger, game-build annotation, or attribution for the numeric tables was found. Use it as a separate transport/source record but not as an independent corroborating witness until lineage is clarified.

The site's [robots file](https://last-asylum-unofficial.com/robots.txt) allows `/`, and its [sitemap](https://last-asylum-unofficial.com/sitemap.xml) publishes the main routes. Structured records can be obtained through normal, anonymous, public site resources without evading controls. This validation used low-volume read-only requests, did not sign in, did not access player/user entities, and did not invoke mutations. Public entity responses include unnecessary provenance fields; any future adapter should whitelist content fields and avoid retaining personal identifiers.

### Freshness

- The active client asset, [`index-DZyzHJPm.js`](https://last-asylum-unofficial.com/assets/index-DZyzHJPm.js), returned `Last-Modified: Fri, 28 Aug 2026 15:08:29 GMT` during validation. The site was actively redeployed on the snapshot date.
- A fresh deployment does not mean fresh data. Latest row-edit dates are: hero progression 2026-03-09, basic gear 2026-03-20, advanced gear 2026-03-22, events/items 2026-03-26, buildings/upgrades through 2026-05-25, and packs through 2026-07-19.
- No records carry a game version, server, season, source URL, or evidence image. Drift cannot be resolved from row metadata alone.

### Exact structured coverage

| Entity | Rows | Latest row edit | Content fields / assessment |
|---|---:|---:|---|
| `HeroLevel` | 150 | 2026-03-09 | `level`, `antitoxin`; levels 1–150 exist, only 127 costs populated. Levels 127–130 and 132–150 are blank; level 131 alone is 100,000,000. |
| `SkillLevel` | 30 | 2026-03-09 | `level`, `skill_badges`; levels 1–21 populated, 22–30 blank. |
| `HeroStar` | 50 | 2026-03-09 | `star`, `sub_star`, `shards`, `icon`; only 49 unique coordinate pairs. `(8,4)` conflicts at 35 versus 40 shards; `(4,0)` and `(7,4)` are absent from the apparent sequence. |
| `HeroGear` | 40 | 2026-03-20 | `level`, `material_cost`; the UI explicitly says “Curently outdated, game changed how it works.” |
| `AdvancedHeroGear` | 5 | 2026-03-22 | Gearstones, herbs, tempered steel, UR/MR blueprints by star/sub-star; five rows is visibly partial coverage. |
| `Building` | 50 | 2026-03-05 | IDs, names, icons, ordering. |
| `BuildingUpgrade` | 754 | 2026-05-25 | From-level, grain/wood/herb, seconds, might, multiple-instance flag, dependencies. Strongest dataset found. |
| `Item` | 108 | 2026-03-20 | Item IDs/names, icon, conversions, analysis amount/value/note. |
| `ComplexItem` | 19 | 2026-03-26 | IDs/names, components, analysis value. |
| `Pack` | 87 | 2026-07-19 | Name, raw numeric price, location, item/choice arrays, format, notes/image. Useful catalog, not live-store completeness. |
| `Milestone` | 41 | 2026-03-10 | Day, title, description, banner/link; days 1–120. |
| `EventGroup` | 7 | 2026-02-22 | Group ID/name/description/banner. |
| `Event` | 149 | 2026-03-26 | Group, item ID, amount, points, sort order. |

The site also exposes public page routes for Building Calculator, Pack Analysis, Server Age, Research Calculator, hero levels, hero gear, and events. Authenticated “My”/manager pages are not evidence of public datasets and were not probed.

### Calculator and server-age behavior

The Building Calculator consumes the 50/754 building records, accepts current/target levels and discounts, and expands dependencies. This is substantive calculator coverage.

The Server Age page tells the player to find the current age in the in-game Monument, enter that day manually, and then divides the 41 milestones into past/upcoming. Examples include hero unlocks, Cheese Trap levels, City Siege tiers, Kingdom Conquest, and Royal City Scramble. The final row is day 120. These are useful chronology hypotheses but have no per-server/build provenance and should not drive exact Doctor forecasts without current in-game confirmation.

### Overall source verdict

**Tier:** useful secondary structured source.

**Best use:** building-cost corroboration, candidate item/pack/event IDs, and data-gap discovery.

**Do not use as:** sole authority, proof of current hero/gear costs, exact server calendar, or independent corroboration until lineage is known.

## F. APK/client evidence assessment

### What is actually evidenced

[APKMirror's current bundle inventory](https://www.apkmirror.com/apk/37games-global/last-asylum-plague/last-asylum-plague-1-0-99-release/last-asylum-plague-1-0-99-android-apk-download/) itemizes:

- Base APK: 23.33 MB
- ABI split: arm64-v8a, 47.20 MB
- 24 language splits
- Dynamic feature: `abPack1`, 370.71 MB
- Total mirror bundle: 469.16 MB; base plus 26 splits
- Version/package: `1.0.99 (99)`, `com.phs.global`
- Minimum/target: Android 7.0/API 24 and Android 15/API 35

APKPure's current XAPK is 526.3 MB. The differing container sizes are not a contradiction: repositories can package/compress variants differently. Older [APKPure 1.0.82 metadata](https://apkpure.net/last-asylum-plague/com.phs.global/download/1.0.82) also lists `abPack1` alongside ABI splits, showing the name is not a one-release anomaly.

### What the evidence does not establish

Android's [App Bundle format documentation](https://developer.android.com/guide/app-bundle/app-bundle-format) explains that base, feature, configuration, and asset modules can all become separate APKs. [Play Asset Delivery](https://developer.android.com/guide/playcore/asset-delivery) is intended for large game assets but is engine-neutral. Most decisively, Google's [Unity PAD integration](https://developer.android.com/guide/playcore/asset-delivery/integrate-unity) says an asset pack configured through Unity does **not** need to contain a Unity AssetBundle.

Therefore `abPack1` is evidence of a named, large delivered module—not of Unity, AssetBundles, or progression tables.

### Static-data potential: common pattern versus Last Asylum evidence

| Candidate | Technically common in Unity/large Android games | Actually evidenced in Last Asylum package | Verdict |
|---|---|---|---|
| Localization tables | Common as Android resources, engine localization assets, JSON/CSV/binary tables, or remote catalogs | 24 Android language splits are listed; their contents were not inventoried | **LIKELY** some local localization, exact tables **UNCONFIRMED** |
| Item IDs | Common in configs or serialized assets, but may be hashed/server-delivered | No package file or string observed | **UNCONFIRMED** |
| Hero IDs | Common for local references; live definitions may be remote | No package file or string observed | **UNCONFIRMED** |
| Research IDs | Common where UI needs stable references | No package file or string observed | **UNCONFIRMED** |
| Building IDs | Common where UI/assets reference buildings | No package file or string observed | **UNCONFIRMED** |
| Cost/config tables | Common for client prediction/display, but authoritative values can be server-side | No table observed | **UNCONFIRMED** |
| Prerequisite definitions | Common for local UI gating; server can remain authoritative | No definition observed | **UNCONFIRMED** |
| Future-system definitions | Sometimes shipped before activation; often remotely delivered or encrypted/obfuscated | No definition observed; inferring future systems from latent names would still require version/context validation | **UNCONFIRMED** |

If Unity is later confirmed, Unity's [AssetBundle documentation](https://docs.unity3d.com/es/current/Manual/AssetBundlesIntro.html) establishes only that AssetBundles can contain serialized non-code assets, including ScriptableObject data. It does not imply that every bundle contains readable tables. IL2CPP would require direct signatures such as `libil2cpp.so` (Unity's [Android symbols documentation](https://docs.unity3d.com/cn/2022.3/Manual/android-symbols.html) identifies that library); Mono would require a managed assembly layout. Neither was publicly observed here.

## G. Recommended PROBE Phase 0 experiment

Run a small, reproducible **inventory-only** experiment before designing an extractor.

1. **Acquire the authoritative install set.** Prefer a player's own current Google Play installation of `com.phs.global` 1.0.99. Record `adb shell dumpsys package com.phs.global` and enumerate paths with `adb shell pm path com.phs.global`; pull only those installed packages. A signature-verified mirror bundle can be a secondary reproducibility sample, not the authority.
2. **Hash and verify.** Record SHA-256 for every APK, versionName/versionCode, signer fingerprint, split name, delivery/module metadata, and file size. Confirm whether `abPack1` is a feature split or an install-time asset pack from its manifest rather than from a mirror label.
3. **Create only an archive inventory.** Use `apkanalyzer`, `aapt2`, `bundletool`, or `zipinfo` to list paths, manifests, native libraries, `assets/`, and resource tables. Do not decompile gameplay code in Phase 0.
4. **Test engine signatures.** Unity requires a cluster such as `libunity.so`, `libmain.so`, `assets/bin/Data`, `globalgamemanagers`, or `boot.config`. IL2CPP requires `libil2cpp.so` plus its metadata layout; Mono requires managed assemblies such as `Assembly-CSharp.dll`. Classify only from observed files.
5. **Test AssetBundle signatures separately.** Search file headers/names for actual Unity archives/serialized files; do not use `abPack1` as the test. Record counts and hashes, not extracted art/audio.
6. **Triage candidate static data.** List JSON, CSV, XML, protobuf/flatbuffer-like blobs, SQLite, Lua, ScriptableObject/serialized assets, addressable catalogs, and localization resources. Record paths, encodings, schema hints, and a few non-copyrightable identifier/value anchors only.
7. **Compare ten anchors without importing.** Suggested anchors: Sanctuary 26 and 30 resources/times/dependencies; Antitoxin levels 100 and 150; Skill Badge levels 20 and 30; two item IDs; two research IDs/prerequisites. A miss is meaningful: it distinguishes absent/remote/encoded data from confirmed local tables.
8. **Stop and report.** Commit only a manifest/hash/evidence report. Do not commit APKs, extracted assets, full localization, binaries, or database changes. Do not bypass encryption, authentication, anti-tamper, or runtime access controls.

Success criteria for Phase 0 are intentionally narrow: engine/backend classification, exact split inventory, and a yes/no answer for recognizable static-data candidates. It should not attempt full extraction or claim server authority.

## H. Sources and evidence

### Primary/official technical sources

- [Google Play: Last Asylum: Plague](https://play.google.com/store/apps/details?id=com.phs.global) — official product/package URL and publisher.
- [Android App Bundle format](https://developer.android.com/guide/app-bundle/app-bundle-format) — meaning of base, feature, configuration, and asset modules.
- [Play Asset Delivery](https://developer.android.com/guide/playcore/asset-delivery) — asset-pack purpose and delivery behavior.
- [Integrate asset delivery with Unity](https://developer.android.com/guide/playcore/asset-delivery/integrate-unity) — Unity support and explicit note that asset packs need not contain AssetBundles.
- [Unity AssetBundles](https://docs.unity3d.com/es/current/Manual/AssetBundlesIntro.html) — what an actual AssetBundle can contain.
- [Unity Android symbols](https://docs.unity3d.com/cn/2022.3/Manual/android-symbols.html) — `libil2cpp` meaning.
- [YouTube Terms of Service](https://www.youtube.com/static?template=terms), [view transcripts help](https://support.google.com/youtube/answer/15930243), and [`captions.download`](https://developers.google.com/youtube/v3/docs/captions/download) — access/download/compliance boundary.
- [Qwen2.5-VL-7B model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) and [RapidOCR usage](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/usage/) — general OCR capability only.

### Package metadata

- [APKMirror: Last Asylum 1.0.99](https://www.apkmirror.com/apk/37games-global/last-asylum-plague/last-asylum-plague-1-0-99-release/last-asylum-plague-1-0-99-android-apk-download/) — current version/build, signer hashes, base + 26 splits, language/ABI inventory, `abPack1`.
- [APKPure: current 1.0.99](https://apkpure.net/last-asylum-plague/com.phs.global/download) and [older 1.0.82 split inventory](https://apkpure.net/last-asylum-plague/com.phs.global/download/1.0.82) — independent version/XAPK metadata and persistence of `abPack1`.

### Community data sources

- [Last Asylum Unofficial home](https://last-asylum-unofficial.com/), [robots.txt](https://last-asylum-unofficial.com/robots.txt), [sitemap](https://last-asylum-unofficial.com/sitemap.xml), [client asset](https://last-asylum-unofficial.com/assets/index-DZyzHJPm.js), and [HeroLevel public JSON example](https://last-asylum-unofficial.com/api/apps/698a36b276613255c34c822b/entities/HeroLevel?sort=level&limit=5).
- [SatoriMeta Sanctuary](https://satorimeta.com/en/last-asylum/buildings/sanctuary/) and [Last Asylum Database Sanctuary](https://lastasylumdatabase.com/buildings/sanctuary) — exact building overlap checks.
- [lastasylumwiki Hero Upgrade Costs](https://lastasylumwiki.com/docs/hero-upgrade-costs/) — exact hero/skill overlap and completion contrast.

## I. Exact next actions

1. Run PROBE Phase 0 against a Play-installed 1.0.99 split set and produce a hash/manifest-only report.
2. Ask the Last Asylum Unofficial maintainer for data provenance, intended public-API use, rate limits, licensing/reuse permission, game version/server context, and correction process.
3. Send the maintainer four concrete quality findings: Antitoxin gaps, Skill Badge gaps, missing `(4,0)` and `(7,4)` star coordinates, and conflicting `(8,4)` values.
4. Recheck ten building rows outside Sanctuary against SatoriMeta/LastAsylumDatabase to determine whether the exact agreement is systematic.
5. Treat the 87 packs as a dated candidate snapshot. Verify currency/price semantics and five live in-game packs before any economic use.
6. Validate five server milestones on two differently aged servers; store observed server/day/build evidence rather than assuming a universal calendar.
7. Benchmark Qwen2.5-VL and RapidOCR on the same 50 cropped screenshots with exact-character accuracy, numeric-field accuracy, latency, VRAM/RAM, and failure categories. Choose by results, not generic OCRBench scores.
8. For YouTube, prefer public transcript viewing, metadata, timestamps, short necessary excerpts, and paraphrased claims. Do not adopt a blanket `yt-dlp` workflow without authorization and a source-specific rights/Terms review.
9. Do not add any unofficial/API/package-derived values to the Doctor database until provenance, version, field semantics, and a second evidence source are recorded.

No Doctor database, schema, or implementation files were changed for this mission.
