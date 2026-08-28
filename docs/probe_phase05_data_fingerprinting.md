# Probe Phase 0.5 — Structured-Data Fingerprinting

Date: 2026-08-28  
Scope: bounded, static-only inspection of nine explicitly selected UnityFS bundles from the preserved version 1.0.97 abPack1 split. No ADB input, gameplay, runtime modification, decryption, hooking, patching, broad bundle scan, or binary asset extraction was performed.

## Executive verdict

The client contains a deterministic, parseable text-data layer. UnityPy identified UnityFS AssetBundle objects containing TextAssets whose internal paths end in .txt, .proto.txt, or .bytes.

The English base-data bundle is especially useful: its TextAssets are Lua-table text files such as item.txt, building.txt, buildingdetails.txt, gototarget.txt, and collegetech.txt. Rows directly expose stable keys or numeric IDs plus fields such as name, description, building classification, and display labels.

Antitoxin can be mapped to stable IDs for specific records, but the bare display concept is not a unique global ID. For example, item_heroExp_1k and item_heroExp_5k are distinct item IDs, while building ID 1027 is the Antitoxin Workshop and ItemIcon ID 5 is the direct Antitoxin icon/config row.

Building identity/progression references are visible, but numeric building-level, upgrade-cost, and research-level tables reside in JIT TextAssets that have a common binary/obfuscated prefix. They were not decoded. No S27 costs or progression values are published.

## A. Selected bundles inspected

All selected payloads were read from the ignored local copy of split_abPack1.apk. Total selected payload size was approximately 12.9 MB.

| Bundle | Bytes | UnityPy objects | Object types | Purpose |
|---|---:|---:|---|---|
| assets/ABAsset/gamedata_basedb_f_basedata_jit.assetbundles | 4,988,185 | 737 | 1 AssetBundle, 736 TextAsset | JIT/base tables |
| assets/ABAsset/gamedata_basedb_f_en.assetbundles | 585,424 | 250 | 1 AssetBundle, 249 TextAsset | English base-data text |
| assets/ABAsset/gamedata_language_f_en.assetbundles | 241,924 | 80 | 1 AssetBundle, 79 TextAsset | English language tables |
| assets/ABAsset/gamedata_pb_f.assetbundles | 187,368 | 120 | 1 AssetBundle, 119 TextAsset | Protobuf schema text |
| assets/ABAsset/gamedata_atlasconfig_f.assetbundles | 22,312 | 70 | 1 AssetBundle, 69 TextAsset | Atlas/config text |
| assets/ABAsset/luascript_logic.assetbundles | 6,791,545 | 2,100 | 1 AssetBundle, 2,099 TextAsset | xLua logic resources |
| assets/ABAsset/luascript_eyu_logic_datas_building.assetbundles | 7,921 | 2 | 1 AssetBundle, 1 TextAsset | Building Lua resource |
| assets/ABAsset/luascript_eyu_logic_ui_item_hero.assetbundles | 30,030 | 10 | 1 AssetBundle, 9 TextAsset | Hero UI Lua resources |
| assets/ABAsset/luascript_eyu_logic_ui_item_tech.assetbundles | 7,790 | 3 | 1 AssetBundle, 2 TextAsset | Technology UI Lua resources |

The reusable bounded inspector is tools/probe_phase05_fingerprint.py. It uses UnityPy 1.25.3 to read only explicitly selected bundles and reports object types, TextAsset names/containers, classifications, and tracer contexts. UnityPy was installed only because ordinary ZIP inspection cannot enumerate Unity serialized objects or TextAsset contents.

## B. Serialized object types found

### English base-data

The bundle contains 249 TextAssets plus its AssetBundle directory object. Representative internal containers include:

- assets/resourcesdata/gamedata/basedb_f/en/item.txt
- assets/resourcesdata/gamedata/basedb_f/en/building.txt
- assets/resourcesdata/gamedata/basedb_f/en/buildingdetails.txt
- assets/resourcesdata/gamedata/basedb_f/en/gototarget.txt
- assets/resourcesdata/gamedata/basedb_f/en/resourceinfo.txt
- assets/resourcesdata/gamedata/basedb_f/en/collegetech.txt
- assets/resourcesdata/gamedata/basedb_f/en/collegeTechType.txt
- assets/resourcesdata/gamedata/basedb_f/en/itemicon.txt
- assets/resourcesdata/gamedata/basedb_f/en/task.txt
- assets/resourcesdata/gamedata/basedb_f/en/functionunlock.txt
- assets/resourcesdata/gamedata/basedb_f/en/pointsource.txt

These are human-readable Lua-table text assets. The common form is:

    local data = {
        ["stable-key"] = { ["id"] = ..., ["name"] = ..., ["description"] = ... },
    }
    return data

The selected base-data bundle also includes domain-specific tables named Building, BuildingDetails, BuildingArea, CollegeTech, Item, ResourceInfo, and related records.

### English language

The language bundle contains 79 TextAssets. The selected records include:

- language_f/en/item.txt
- language_f/en/building.txt
- language_f/en/tech.txt
- language_f/en/lang_abc.txt
- language_f/en/common.txt

These are human-readable key/value localization tables, including a header of KEY,Chinese. They provide localization keys and display strings, but not a complete join to every base-data record.

### Protobuf schemas

The protobuf bundle contains 119 human-readable .proto.txt TextAssets, including:

- building.proto
- item.proto
- resource.proto
- level.proto
- server.proto
- union_building.proto
- collegeTech.proto
- union_tech.proto

These are schema definitions for runtime/server messages, not local numeric configuration tables.

### JIT/base and Lua resources

The JIT bundle contains 736 TextAssets with .bytes containers, including:

- Building
- BuildingLevel
- BuildingUpgrade
- CollegeTech
- CollegeTechLevel
- Item
- ResourceInfo

Representative JIT sizes are BuildingLevel 161,080 bytes, BuildingUpgrade 264,559 bytes, CollegeTechLevel 606,098 bytes, Item 274,237 bytes, and ResourceInfo 14,175 bytes.

The xLua logic bundle contains 2,099 .bytes TextAssets. Representative names include UIItemSpeedUseCell, UIHeroListItem, UIHeroShowAttrTips, UIBuildingUpgrade, UITechResearchPanelMaxLevelPart, and QueueTechObject.

## C. Antitoxin localization-to-ID mapping result

### Confirmed links within individual config domains

The English base-data Item TextAsset contains direct rows such as:

- item_heroExp_1k_show → id item_heroExp_1k_show → name 1K Antitoxin
- item_heroExp_1k → id item_heroExp_1k → name 1K Antitoxin
- item_heroExp_5k → id item_heroExp_5k → name 5K Antitoxin
- item_castleBox_HeroEXP_1 through _4 → distinct IDs → Antitoxin Level Supply variants
- item_research_info → id item_research_info → name Study Scroll
- item_equipment_enhanceStone, _25, and _100 → distinct IDs → name Gearstone

The English Building TextAsset contains:

- building key 1027 → id 1027 → name Antitoxin Workshop
- build/create descriptions explicitly state Produces Antitoxin
- building key 1001 → id 1001 → name Sanctuary
- building key 1007 → id 1007 → name Research Lab
- building key 1020 → id 1020 → name Training Grounds

The English BuildingDetails TextAsset independently contains:

- key/id 1027 → Produces Antitoxin hourly.
- key/id 1001 → Sanctuary description
- key/id 5042 → Produces Gearstones.

The English ItemIcon TextAsset contains a direct row with id 5, name Antitoxin, and description Use to enhance hero strength. This is a confirmed ID in the ItemIcon/config domain, but it is not by itself proof that 5 is the canonical resource ID everywhere.

### Localization-key link

The English language Item TextAsset contains:

    shop_pack_heroExp,Antitoxin Potion

Therefore:

- Antitoxin Potion → shop_pack_heroExp is CONFIRMED within the language table.
- shop_pack_heroExp → a canonical item ID in the English Item table is UNCONFIRMED; no same-key row was established in this bounded test.
- 1K Antitoxin / 5K Antitoxin → their specific item IDs is CONFIRMED directly in basedb_f/en/item.txt.
- Antitoxin Workshop → building ID 1027 is CONFIRMED directly in basedb_f/en/building.txt.
- Bare display concept Antitoxin → one unique global ID is UNCONFIRMED because multiple item, icon, building, task, and text records use the term.

### Supporting navigation/task records

The English GoToTarget TextAsset contains:

- goto_104 → id goto_104 → Upgrade Sanctuary
- citadel → id citadel → Sanctuary
- 123_0 → id 123_0 → Obtain Antitoxin
- commander_1613 → id commander_1613 → Use Antitoxin Potion

These confirm stable navigation/task keys for the displayed concepts, but they are not item-resource definitions.

## D. Secondary tracer results

### Study Scroll

CONFIRMED stable item mapping:

- English base-data Item row key/id item_research_info
- name Study Scroll
- description says it is used for advanced research projects

Additional base-data evidence:

- AllianceCompetitionStage contains a Study Scroll display field.
- PointSource contains a stable point-source row for consuming one Study Scroll.

The localization string is present in the base-data text layer; a separate language-key join was not required for this record.

### Gearstone

CONFIRMED as multiple stable item IDs, not one unique ID:

- item_equipment_enhanceStone
- item_equipment_enhanceStone_25
- item_equipment_enhanceStone_100
- item_equipment_enhanceStone_pieces

Building ID 5042 is the Smelting Workshop, with direct Gearstone production text. The base-data GetSource table also contains a Gearstone row with numeric ID 1000001, but its relationship to the Item rows was not proven in this bounded test.

### Sanctuary

CONFIRMED:

- building ID 1001 → Sanctuary
- GoToTarget key citadel → Sanctuary
- GoToTarget key goto_104 → Upgrade Sanctuary
- language strings include Sanctuary Lv.{0}, building-name formatting, and upgrade messaging
- FunctionUnlock contains a separate requirement mentioning Sanctuary Lv.27 for Super Dispatch

The Sanctuary Lv.27 mention is a feature-unlock text record, not a claim about Research Lab or Training Grounds costs.

### Research Lab

CONFIRMED:

- building ID 1007 → Research Lab
- Building fields include Research Speed and Free Speedup Time labels
- BuildingArea records describe constructing and using a Research Lab
- language strings include Research Lab and Research Lab upgrade/research messaging
- protobuf building schema carries runtime building identity and level fields

No numeric Research Lab level/cost row was decoded.

### Training Grounds

CONFIRMED:

- building ID 1020 → Training Grounds
- Building fields include Training Capacity and Soldier Training Level labels
- CollegeTech contains stable technology IDs 1003, 1010, 1014, 1017, 1024, 11009, and 12006 whose names/descriptions reference Training Grounds expansion or limit
- language strings include Training Grounds and soldier-training messages
- task/navigation records reference constructing or upgrading Training Grounds

These are identity, label, and technology-reference findings. They do not establish S27 costs or timers.

## E. xLua/config findings

xLua is CONFIRMED by Phase 0 native library evidence and the selected bundle names. In this Phase 0.5 parse:

- luascript_logic contains 2,099 TextAssets, all in .bytes-style internal containers.
- All sampled/selected xLua TextAssets share a common binary prefix beginning with byte values 126, 53, 0, 6, 53, 109, 124.
- No Lua bytecode magic 1B 4C 75 61 was found in the selected logic bundle.
- No plaintext function, local, require(, or return markers were found in those xLua payloads.
- No plaintext Lua script was therefore confirmed.
- The exact binary format is UNCONFIRMED. It may be compiled, transformed, or protected Lua/resource data; no decoding was attempted.

Game configuration nevertheless clearly uses Lua-table text in the English base-data bundle. The xLua resources appear to provide client logic/UI/protocol behavior, while the English base-data TextAssets provide readable configuration and display records.

No filename/index manifest beyond UnityPy container paths was needed for the selected bundles.

## F. Numeric/config structures discovered

### Confirmed local text structure

The strongest deterministic structure is:

    TextAsset container path
      → Lua-table file name
        → stable row key
          → id field
          → name/description/display fields

Confirmed examples include:

- item.txt: stable item key/id → name → description
- building.txt: numeric building ID → name → classification → stat-label fields
- buildingdetails.txt: numeric building ID → build description
- gototarget.txt: navigation key/id → name/description
- collegetech.txt: technology ID → name → effect description
- itemicon.txt: icon/config ID → name/description
- pointsource.txt: point-source ID → consumption display text

### Confirmed runtime schemas

The selected protobuf text provides these field patterns:

- BuildingDto: uuid, buildingId, originalId, level, status, startTime, endTime, canProduce, resourceDetail, and other building-state details.
- ItemDto: uuid, itemId, count, and endTime.
- ResourceInfo: type, value, and itemId.
- LevelDto: chapterId, levelId, challenge counts, new-player level IDs, and reward level IDs.
- UnionBuildingDto and related messages expose separate alliance-building runtime state.

These prove that runtime messages carry IDs, levels, quantities, and timestamps. They do not prove that the corresponding numeric configuration is locally readable or authoritative.

### Not confirmed

The following patterns were not established as decoded local rows:

- building_id → level → construction costs
- building_id → level → construction timer
- research_id → level → research costs/effects
- resource_id → quantity as a canonical local table
- localization key → universal ID across all config domains

The JIT objects named BuildingLevel, BuildingUpgrade, and CollegeTechLevel are the likely high-value sources, but their payloads are opaque in this inspection.

## G. Sanctuary/building-specific leads

The readable English layer establishes a useful identity graph:

- 1001 → Sanctuary
- 1007 → Research Lab
- 1020 → Training Grounds
- 1027 → Antitoxin Workshop
- 5042 → Smelting Workshop
- CollegeTech rows reference Training Grounds expansion/limit technologies.
- BuildingDetails and Building fields provide production/stat labels.
- BuildingArea, Task, FunctionUnlock, LoadingTips, PointSource, and language tables provide construction, upgrade, research, and unlock wording.

The JIT bundle exposes likely numeric/config table names:

- BuildingLevel, 161,080 bytes
- BuildingUpgrade, 264,559 bytes
- CollegeTechLevel, 606,098 bytes
- Building, 22,459 bytes
- CollegeTech, 33,790 bytes
- BuildingDetails, 5,109 bytes
- ConstructionLevelReward, 2,493 bytes

The JIT table names are strong leads, not decoded data. No explicit S27 Research Lab or Training Grounds cost/timer relationship was visible in readable form, and no inferred S27 costs are reported.

## H. What remains opaque

- JIT/base-data .bytes payload format and field encoding
- numeric BuildingLevel, BuildingUpgrade, and CollegeTechLevel rows
- actual construction/research costs and timers
- stable cross-domain join between language keys, item IDs, resource IDs, and server IDs
- xLua logic/resource format
- protobuf runtime payload values
- server overrides, live offers, account progression, inventory, and season state
- whether any client-side values are authoritative after server validation

The common JIT/xLua binary prefix was recorded as an observation only. It was not treated as proof of encryption and was not attacked or decoded.

## I. Whether deterministic extraction is now justified

Partially yes.

Deterministic extraction is justified for an allowlisted text layer: UnityPy can reliably enumerate the selected AssetBundle/TextAsset objects and recover readable Lua-table/protobuf/localization text with stable row keys, IDs, names, and descriptions.

Deterministic numeric gameplay extraction is not yet justified. The likely numeric sources are present by name but opaque. A parser that attempts to decode those payloads would need an additional format/protection determination and must stop if that crosses the stated boundary.

## J. Exact recommended MINER scope, if justified

MINER should still NOT be created.

If later justified by a successful bounded numeric parse, its initial scope should be explicitly limited to:

- one pinned APK version and hash set
- an allowlist of three or four bundles: basedb_f_en, basedb_f_basedata_jit, language_f_en, and optionally pb_f
- TextAsset object inventory and stable source/container paths
- Lua-table text parsing for item, building, buildingdetails, collegetech, resource, and navigation records
- provenance for bundle hash, internal path, object name, and parser version
- explicit separation of localization, identifiers, configuration, numeric values, and server/runtime fields
- no gameplay state, server calls, runtime hooks, decryption, broad bundle sweep, or automatic extraction of all assets

Until numeric rows can be decoded and cross-validated on a small sample, the reusable inspector is sufficient.

## K. Highest-value next experiment

Perform one offline, read-only numeric-format feasibility test on exactly:

1. basedata_jit/BuildingLevel
2. basedata_jit/BuildingUpgrade
3. basedata_jit/CollegeTechLevel

First determine whether the TextAsset payload has a documented/plain binary container, known compression signature, or parseable schema without bypassing protection. If not, stop and preserve the result as opaque.

If ordinary parsing succeeds, decode only a handful of records around building IDs 1001, 1007, and 1020 and one CollegeTech ID such as 1003. Validate that level, cost, timer, and prerequisite fields are explicitly part of each record before considering any broader extractor.

Do not infer S27 values from names, neighboring bytes, task text, or UI labels.

## Boundary and repository note

No ADB commands were used in this phase. No game process was started or controlled. No APK or extracted binary asset is tracked. The only intended tracked changes are this report and the small bounded inspector at tools/probe_phase05_fingerprint.py.
