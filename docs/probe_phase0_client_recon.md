# Probe Phase 0 — Last Asylum Installed Client Reconnaissance

Date: 2026-08-28  
Scope: read-only live ADB/package inspection and offline archive inspection. No ADB input, taps, swipes, gameplay, purchases, upgrades, item use, reward claims, runtime modification, protection bypass, or automated gameplay was performed.

## Executive verdict

The live BlueStacks Pie64 device contains com.phs.global version 1.0.97 (version code 97) as a four-file split installation. The prior abPack1 lead is confirmed: it is split_abPack1.apk, a 387,824,773-byte ZIP/APK containing 2,035 UnityFS-backed .assetbundles plus audio and support metadata.

The client is confirmed as Unity/IL2CPP. abPack1 contains named game-data, localization, Lua, hero, building, technology, item, and activity asset bundles. English bundles contain recognizable game strings, including Study Scroll(s), Gearstone(s), Antitoxin, and Sanctuary.

Useful static extraction appears feasible, but the useful data is serialized inside UnityFS bundles rather than exposed as standalone gameplay JSON/CSV or SQLite. A narrowly scoped Unity asset-bundle parser experiment is justified; MINER is not.

## A. BlueStacks / ADB result

The previous host reconnaissance established the BlueStacks installation and version. The resumed live checks found:

- device: emulator-5554, state device
- product/model metadata: b0qxxx / SM-S908E
- Android release: 9
- Android API level: 28
- live ABI list: x86_64,x86,arm64-v8a,armeabi-v7a,armeabi
- live 64-bit ABIs: x86_64,arm64-v8a
- live 32-bit ABIs: x86,armeabi-v7a,armeabi
- normal read-only ADB commands succeeded

No ADB input or game interaction commands were issued.

## B. Installed Last Asylum version

Live package-manager output:

    versionCode=97
    versionName=1.0.97
    minSdk=24
    targetSdk=35

HD-Aapt independently reported package com.phs.global, version code 97, version name 1.0.97, and launch activity com.games37.sdk.AtlasPluginDemoActivity labelled Last Asylum: Plague.

## C. Base/split APK inventory

pm path com.phs.global returned exactly these four installed files:

| Role | Installed source path | Local filename | Size (bytes) | SHA-256 |
|---|---|---|---:|---|
| Base | /data/app/com.phs.global-1Tx8mePgCof_-RPOrcjQeQ==/base.apk | base.apk | 24,452,058 | 14543B75953B46D6EE9EDF3113A7975D0698EA44E09287ACDF6A43D9C59324D7 |
| Named asset split | /data/app/com.phs.global-1Tx8mePgCof_-RPOrcjQeQ==/split_abPack1.apk | split_abPack1.apk | 387,824,773 | A85031E413FD26E662B7A8811474CE7A716D1BFA91CCA82A81502F5800FE647A |
| ABI split | /data/app/com.phs.global-1Tx8mePgCof_-RPOrcjQeQ==/split_config.arm64_v8a.apk | split_config.arm64_v8a.apk | 49,448,525 | 90B2C124048C267078E05EE142AAB447FB463B3A9B3499CA7C60EED7AE4F0821 |
| Language split | /data/app/com.phs.global-1Tx8mePgCof_-RPOrcjQeQ==/split_config.en.apk | split_config.en.apk | 45,465 | 45166BCE4DC70DC25AAFEAA2C91C64F562AE6A8EF2EC7A4B42C6EEC7235CA217 |

Copies are in the ignored path data/raw/probe/client/1.0.97/. Device sha256sum values matched local SHA-256 values. Originals were not modified, and binaries were not staged or committed.

## D. abPack1 verified status and actual type

Confirmed:

- installed split filename: split_abPack1.apk
- installed source path: /data/app/com.phs.global-1Tx8mePgCof_-RPOrcjQeQ==/split_abPack1.apk
- archive magic: 50 4B 03 04 (ZIP/APK)
- package: com.phs.global
- split name from manifest tooling: abPack1
- split version code: 97
- total ZIP entries: 2,100
- asset entries: 2,095
- asset roots: assets/ABAsset and assets/CustomDatas
- asset extensions: 2,035 .assetbundles, 49 .wem, 7 .bnk, and 3 .json
- all 2,095 asset entries had equal uncompressed and compressed lengths in the outer ZIP listing

Representative UnityFS headers begin with UnityFS and editor version 2022.3.62f1. abPack1 is therefore an asset split containing Unity asset bundles and related custom data/audio files. Its name alone was not used for classification.

## E. Engine/framework evidence

Unity is CONFIRMED. The base APK contains:

- assets/bin/Data
- assets/bin/Data/globalgamemanagers
- globalgamemanagers.assets.split0 through split3
- assets/bin/Data/Resources/unity_builtin_extra
- assets/bin/Data/unity default resources
- assets/bin/Data/ScriptingAssemblies.json
- assets/bin/Data/RuntimeInitializeOnLoads.json
- Unity module names including UnityEngine.AssetBundleModule.dll, UnityEngine.LocalizationModule.dll, and UnityEngine.UnityWebRequestAssetBundleModule.dll

The ABI split contains lib/arm64-v8a/libunity.so. Representative abPack1 bundles carry the UnityFS header and Unity editor version 2022.3.62f1.

Other framework evidence:

- Wwise is CONFIRMED by libAkUnitySoundEngine.so, .bnk banks, and .wem media.
- xLua is CONFIRMED by libxlua.so and many luascript_*.assetbundles names.
- Firebase/Google/Android support libraries are present but are integration dependencies, not the game engine.

## F. IL2CPP / Mono evidence

IL2CPP is CONFIRMED:

- ABI split entry: lib/arm64-v8a/libil2cpp.so, 92,781,384 bytes
- base entry: assets/bin/Data/Managed/Metadata/global-metadata.dat, 14,328,172 bytes
- global-metadata.dat begins with AF 1B B1 FA

Classic Mono deployment was not observed. The archive listing did not show the expected deployed managed assembly DLL set. The native libil2cpp.so plus IL2CPP metadata establish IL2CPP as the primary scripting runtime. No metadata parser or decompiler was run.

## G. Structured-data candidates

No standalone gameplay JSON/CSV/TSV/SQLite table was found in archive listings. The strongest candidates are UnityFS bundles:

| Package/split | Internal path or family | Approx. size/count | Confidence and evidence |
|---|---|---:|---|
| split_abPack1.apk | assets/ABAsset/gamedata_basedb_f_basedata_jit.assetbundles | 4,988,185 bytes | High: core game-data name and raw Antitoxin |
| split_abPack1.apk | assets/ABAsset/gamedata_basedb_f_en.assetbundles | 585,424 bytes | High: English item/story/UI strings |
| split_abPack1.apk | assets/ABAsset/gamedata_language_f_en.assetbundles | 241,924 bytes | High: English UI/localization strings |
| split_abPack1.apk | assets/ABAsset/gamedata_pb_f.assetbundles | 187,368 bytes | Medium: protobuf-related name; not parsed |
| split_abPack1.apk | assets/ABAsset/gamedata_atlasconfig_f.assetbundles | 22,312 bytes | Medium: named atlas configuration |
| split_abPack1.apk | assets/ABAsset/gamedata_basedb_f_*.assetbundles | 20 / 16,062,409 bytes total | High: locale-specific base-data family |
| split_abPack1.apk | assets/ABAsset/gamedata_language_f_*.assetbundles | 19 / 4,632,043 bytes total | High: locale-specific language family |
| split_abPack1.apk | assets/ABAsset/luascript_logic.assetbundles | 6,791,545 bytes | High: Lua logic payload |
| split_abPack1.apk | assets/ABAsset/luascript_eyu_logic_datas_building.assetbundles | 7,921 bytes | Medium: building data logic name |
| split_abPack1.apk | assets/ABAsset/luascript_eyu_logic_ui_item_hero.assetbundles | 30,030 bytes | Medium: hero UI/data logic name |
| split_abPack1.apk | assets/ABAsset/luascript_eyu_logic_ui_item_tech.assetbundles | 7,790 bytes | Medium: technology UI/data logic name |
| split_abPack1.apk | assets/ABAsset/luascript_*.assetbundles | 392 / 22,275,175 bytes total | High: logic/UI/activity family |

Unity serialized markers such as AssetBundle, m_PreloadTable, m_MainAsset, Dependencies, and RuntimeCompatibility are visible in raw payloads. Their fields are not safely recoverable as tables by simple text inspection. A UnityFS/serialized-object parser is needed for field-level extraction.

The three abPack1 JSON files are audio build metadata, not confirmed game configuration:

- CustomDatas/Audio/GeneratedSoundBanks/Android/PlatformInfo.json, 1,073 bytes; keys include PlatformInfo, Platform, Generator, and SoundBanksRoot.
- PluginInfo.json, 2,024 bytes; keys include PluginInfo, PluginLibs, LibName, LibId, DLL, and FileHash.
- SoundbanksInfo.json, 1,331,986 bytes; keys include SoundBanksInfo, SchemaVersion, SoundBanks, Id, Language, Path, and Media.

Base ScriptingAssemblies.json and RuntimeInitializeOnLoads.json are Unity runtime metadata, not gameplay tables. No generalized extractor was written and no heavyweight toolchain was installed.

## H. Localization / ID evidence

A bounded raw UTF-8/UTF-16 fingerprint scan covered every entry in all four APKs:

| Term | Result | Evidence |
|---|---|---|
| Study Scroll | Found as Study Scrolls | split_abPack1.apk / assets/ABAsset/gamedata_basedb_f_en.assetbundles |
| Gearstone | Found, including Gearstones | English and several locale gamedata_basedb_f_*.assetbundles |
| Raven Essence | Not observed | No raw match in any APK entry |
| Raven Fruit | Not observed | No raw match in any APK entry |
| Antitoxin | Found | Core, English/Portuguese base-data, English/Portuguese language bundles; one audio metadata occurrence |
| Skill Badge | Not observed | No raw match in any APK entry |
| Sanctuary | Found | English gamedata_basedb_f_en and gamedata_language_f_en |

The English base-data bundle contains nearby readable narrative/config text and identifier-like material. Near one Antitoxin occurrence, raw context included numeric-looking token 10000101032; this suggests IDs may be colocated with strings, not that this token's semantic mapping is known.

These are embedded UnityFS strings, not parsed localization records or numeric gameplay truth.

## I. Whether useful static extraction appears feasible

YES, provisionally. The client embeds named UnityFS game-data and language bundles, and raw English strings are accessible without bypassing protection. The likely path is a small offline parser experiment on only the English base-data and language bundles, with global-metadata.dat kept separate from gameplay-data parsing.

Field-level confidence remains low until Unity serialized objects are decoded and internal IDs, strings, costs, levels, and prerequisites are mapped. No bulk extraction was performed.

## J. What static data appears unavailable/server-driven

This run did not establish which values are authoritative on the server. The following remain unverified as gameplay truth:

- item/resource definitions and numeric costs
- hero, building, research/technology, gear, Raven, and Curio records
- level tables and prerequisite/unlock relationships
- shop/event configuration and prices
- server/season state, account inventory, progression state, and live offers

## K. Highest-value next experiment

Run one narrow offline parser feasibility test against the preserved files:

1. Read the UnityFS header and bundle directory for gamedata_basedb_f_en.assetbundles and gamedata_basedb_f_basedata_jit.assetbundles.
2. Enumerate serialized object types/names only; do not extract all assets.
3. Check whether English string records expose stable internal IDs and whether Antitoxin maps to an object.
4. Repeat the bounded check for gamedata_language_f_en.assetbundles.

Stop if the parser requires protection bypass, runtime hooks, decryption, or bulk extraction. If objects are ordinary Unity serialized data, document the minimum parser dependency and schema observations before larger work.

## L. Whether MINER should be created now

NO. The client justifies a bounded parser experiment, not a generalized MINER. Create MINER only after a small sample proves stable, useful field-level records can be decoded and validated.

## M. Security/protection boundary encountered

No anti-cheat, certificate, encryption, or access-control bypass was needed. APKs and UnityFS headers were inspected as ordinary local archives. The opaque serialized/compressed bundle payload is a tooling boundary, not evidence of encryption, and was not brute-forced or modified.

The only device-side operations were read-only ADB queries (getprop, pm, dumpsys, sha256sum, and pull). No game process was started or controlled by the probe.

## Commit / working-tree note

This report is the only intended repository change. Pulled APKs remain under ignored data/raw/probe/client/1.0.97/ and are not committed.
