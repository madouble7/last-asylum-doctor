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

### Institute / Sanctuary gate inventory

- **Terminology note:** Local reconnaissance uses **Research Lab** for building
	key `1007`. No local source inspected here establishes that “Institute” is
	the same building. Institute-specific requirements therefore remain
	**UNKNOWN** rather than being renamed or mapped by assumption.
- **Evidence scope:** Building prerequisites below come from the dated public
	source reconnaissance and Server 283 UI captures already preserved in local
	documentation. They are building gates or visible account observations,
	not automatically research-node gates.

| Milestone / tree | Tree or node ID | Required Institute level | Required Sanctuary level | Evidence classification | Evidence and limitation |
| --- | --- | ---: | ---: | --- | --- |
| Research Lab Lv1 building | `1007` building key | **UNKNOWN** | 7 | **KNOWN** | Public building source explicitly lists Research Lab Lv1 -> Sanctuary Lv7; no Institute term is used. |
| Development root research | Node ID **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | Existing effect ledger says a Research Lab Lv1 requirement was observed for an individual Development root, but it does not preserve the node ID or a direct dated gate record here. |
| Research Lab Lv27 building | `1007` building key | **UNKNOWN** | 27 | **OBSERVED** | Server 283 capture shows the visible lock `Sanctuary Lv.27`; this is a building-upgrade gate, not proof of a research-tree requirement. |
| Training Grounds Lv27 building | `1020` building key | **UNKNOWN** | 27 | **OBSERVED** | Server 283 capture shows the visible lock `Sanctuary Lv.27`; this is a building-upgrade gate. |
| Soldier Training Level 9 / T9 | Research node ID **UNKNOWN**; troop milestone, not identified as a science node | **UNKNOWN** | **UNKNOWN direct** | **KNOWN** for direct visible condition | T9 lock visibly says `Requires Lv.27 Training Grounds`; the same screen shows no Research Lab, Sanctuary, named-research, or other condition. Sanctuary 27 is only an upstream building-chain fact. |
| `lv-10-soldier` / Lv.10 Soldier | `11023` in local node extract | **UNKNOWN** (Research Lab Lv30 is only secondary consensus) | **UNKNOWN** (Sanctuary Lv30 is only secondary consensus) | **UNVERIFIED / UNKNOWN for canonical use** | Effect ledger records a secondary claim of Research Lab Lv30 + Sanctuary Lv30 + max Elite Troop, explicitly downgraded because no direct Server 283 observation exists. The uncommitted node extract is not canonical evidence. |
| Sanctuary Lv30 building | `1001` building key | **UNKNOWN as Institute** | N/A (target is Sanctuary) | **KNOWN** | Public building source explicitly lists Sanctuary Lv30 -> Research Lab Lv29 + Training Grounds Lv29 + Antitoxin Workshop Lv15. This does not prove the Lv10 Soldier research gate. |
| Advanced trees generally | Tree/node IDs **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | The 348-node science corpus exposes no research building-gate fields; no branch-wide Institute/Sanctuary formula is published. |

- **Worktree-local candidate data:** `data/research/research_nodes.json` and
	`data/research/research_prerequisites.json` are currently modified and not
	part of the verified HEAD at audit time. The prerequisite file labels its
	rules `USER-SUPPLIED_CHAIN`; it must not be promoted to `KNOWN` canonical
	evidence by this signal.
- **Recommended integration action:** Preserve the rows above as separate
	building-gate observations. Keep Institute and Sanctuary columns distinct,
	attach source/capture scope when normalized, and require direct UI evidence
	before promoting the T10 or any branch-wide gate from `UNVERIFIED`/`UNKNOWN`.

### The LAP Hub public structural reconnaissance

- **Audit date:** 2026-08-31.
- **Status:** **COMPLETE** for anonymous structural reconnaissance. Both
	`https://thelaphub.com/` and `https://thelaphub.com/tools/research` loaded
	publicly without authentication. The page header identifies the session as
	`Guest`; the presence of social sign-in controls does not establish that the
	research index is auth-gated.
- **Homepage OBSERVED:** The public homepage links to a featured `Research
	Planner` and describes it as covering every node's cost, prerequisites,
	duration, and effect. This is a tool description, not independent proof of
	every underlying value.
- **Research index OBSERVED:** The anonymous index exposes 18 branch routes:
	Development, Economy, Hero, Soldier, Full Development, Prosperous Economy,
	Squad 1, Squad 2, Squad 4, Alliance Duel, Caravan Transport, Elite Troop,
	Squad 3, Offensive Tactics, Defensive Tactics, Warrior Mastery, Ranger
	Mastery, and Warlock Mastery. No Guardian or Specialist label was visible.
- **Branch-level data OBSERVED:** The index rendered public completion totals
	for Development (0/86 levels), Economy (0/107), Hero (0/140), Soldier
	(0/100), Squad 1 (0/100), Alliance Duel (0/132), Caravan Transport
	(0/43), and Squad 4 (0/100). Other branches were locked in the guest view.
	These are tool-state displays, not canonical game-account facts.

| LAP Hub branch or milestone | Public lock / dependency text | Evidence classification | Scope and limitation |
| --- | --- | --- | --- |
| Full Development | `Extra Training Grounds Lv.1` | **OBSERVED** | Anonymous index lock text; no Sanctuary or Research Lab level shown. |
| Prosperous Economy | `Herb Protection I Lv.1` | **OBSERVED** | Anonymous index lock text; this is a named research dependency, not a building gate. |
| Squad 2 | `Squad 1 25% complete` | **OBSERVED** | Anonymous index lock text; no building requirement shown. |
| Squad 3 | `Squad 2 25% complete` | **OBSERVED** | Anonymous index lock text; no building requirement shown. |
| Elite Troop | `Top Rewards Lv.1` | **OBSERVED** | Anonymous index lock text; no Research Lab/Sanctuary requirement shown. |
| Offensive Tactics | `Elite Troop 40% complete` | **OBSERVED** | Anonymous index lock text; percentage is tool logic/display, not independently verified game gating. |
| Defensive Tactics | `Elite Troop 40% complete` | **OBSERVED** | Same limitation as Offensive Tactics. |
| Warrior/Ranger/Warlock Mastery | `Elite Troop 80% complete` | **OBSERVED** | Anonymous index lock text; no building level shown. |
| Guardian / Specialist | No route or label observed | **UNKNOWN** | Not present among the 18 anonymous index branches; absence does not prove the game lacks these trees. |
| Research Lab / Sanctuary / Institute gates for research nodes | No building gate rendered on the index | **UNKNOWN** | The index only exposes branch lock text. Detailed node/building values were not directly observed in this bounded visit. |
| T9/T10 troop unlock requirements | No T9/T10 lock shown on the anonymous index | **UNKNOWN** | No troop tier panel was opened; do not infer from branch order or lock percentages. |

- **Public asset inspection OBSERVED:** The research route loaded a main
	bundle plus research-specific chunks including `researchNodes-DP2Wec-s.js`,
	`research-CqeowVD7.js`, and `tools.research.index-BStO2rhG.js`. The node
	chunk visibly contains a large numeric node-name dictionary including
	`Lv.10 Soldier` and output/stat labels. The planner chunk contains UI logic
	for tree requirements and a `researchLab` requirement kind. These are public
	schema/UI clues, not retrieved canonical prerequisite records.
- **Network boundary OBSERVED:** The route loaded 63 browser resources. No
	research-data API, GraphQL request, or separate JSON research payload was
	observed; the only non-asset requests were Cloudflare RUM traffic. Static
	bundle inspection found no research `fetch(` call. This supports a bundled
	public-data delivery path for the inspected route, but does not prove that
	all detail data is present in the inspected chunks.
- **Account boundary KNOWN from public bundle text:** Research-plan export is
	described as requiring an account. This is an export restriction, distinct
	from the anonymous ability to view the branch index.
- **UNKNOWN:** Exact per-node costs, durations, effect values, prerequisite
	edges, Research Lab/Institute levels, Sanctuary levels, server/version
	applicability, and any hidden or account-specific branches. No login,
	credential attempt, gated route bypass, or automated selection was used.
- **Recommended integration action:** Treat LAP Hub as a public secondary
	structural source for branch names and visible lock predicates. Preserve
	each lock with retrieval date and URL, but do not import its displayed
	percentages or named dependencies into canonical facts until a detail-page
	capture or export provides source-scoped records and provenance.
