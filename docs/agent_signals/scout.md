<!-- Agent signal file: SCOUT. Single writer: SCOUT only. -->

## EVIDENCE

### Local offline research-branch audit

- **Audit date:** 2026-08-31.
- **Local sources inspected:** `data/processed/research_corpus.json`,
	`docs/science_schema_audit.md`, `docs/science_prerequisite_reconnaissance.md`,
	`docs/research_doctor_capability_audit.md`, `docs/ingestion.md`, and local
	tests. No matching research-branch records were found under
	`tests/fixtures/`.
- **Corpus provenance:** `data/processed/research_corpus.json` records
	`generated_at=2026-08-26T17:09:15.714326+00:00`, source site
	`https://lastasylumdatabase.com/`, 348 requested/successful node records,
	and the source bundle URL. This is a local preserved external-source
	snapshot, not direct game-client extraction.

#### Branch inventory

| Branch | Status | Local node metadata | Resource fields observed locally | Building/Sanctuary gate |
| --- | --- | --- | --- | --- |
| Development | **KNOWN** | 18 nodes; `research_id` span `1001-1034` (span is non-contiguous); max level 5 | `farms`, `lumber`, `herbs` | **UNKNOWN** |
| Full Development | **KNOWN** (nearest local match to a broader Development branch) | 16 nodes; `research_id` span `1015-1032` (span is non-contiguous); max level 5 | `farms`, `lumber`, `herbs` | **UNKNOWN** |
| Guardian | **UNKNOWN** | No local node or branch record found | UNKNOWN | UNKNOWN |
| Specialist | **UNKNOWN** | No local node or branch record found | UNKNOWN | UNKNOWN |
| Production | **UNKNOWN** | No exact local branch record found; `Production` mentions refer to application/building context, not a research tree | UNKNOWN | UNKNOWN |

#### Additional known local structure

- **KNOWN:** The preserved corpus contains 18 named trees in total, including
	Development, Full Development, Economy, and Prosperous Economy. The local
	schema audit reports 348 nodes and 2,287 level rows; observed node shapes
	include 16 five-level nodes and 9 ten-level nodes, plus one twenty-level
	node and 12 one-level nodes.
- **KNOWN:** The normalized level-cost structure supports `farms`, `lumber`,
	`herbs`, and Study Scroll rows (`item_id=item_research_info`) in the corpus
	schema. The Development and Full Development rows inspected above expose
	only `farms`, `lumber`, and `herbs`; no badges or other branch-specific
	currency was locally confirmed for them.
- **KNOWN:** `research_id`, `tech_type`, `tree`, and `tree_slug` are preserved
	metadata fields. The local evidence explicitly warns that numeric ID
	prefixes, positions, and tab/category values do not prove prerequisite
	relationships or even universally identify a tree.
- **KNOWN:** The local public-source audit found no research prerequisite graph,
	edge list, required research level, Research Lab requirement, Sanctuary
	requirement, or other-building gate in the preserved science data.
- **UNKNOWN:** Guardian and Specialist node ID ranges, counts, max levels,
	resources, effects, and gates.
- **UNKNOWN:** Whether the requested `Production` label is an alternate name
	for an existing local tree, a future branch, or a separate game system.
