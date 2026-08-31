<!-- Agent signal file: PROBE. Single writer: PROBE only. -->

## 2026-08-31 — Research dataset audit

- Status: **BLOCKED** — waiting for ATLAS to commit `data/research/*.json`.
- Repository checked: `main` at `71d196eba21ad48032c16513fb79c05b0ceca6af`, matching `origin/main`.
- Evidence: `git ls-tree -r --name-only origin/main -- data/research` returned no entries; local `data/research/` is absent.
- Mathematical totals: not audited because the normalized dataset is unavailable.
- Prerequisite graph: not audited because the normalized dataset is unavailable.
- Required follow-up: rerun the row-level cost/duration reconciliation and prerequisite existence/cycle traversal after ATLAS commits the dataset.

## EVIDENCE — 2026-08-31 Research dataset audit

- Status: **COMPLETE**. Audited `origin/main` at `7a64af4857920cfded6a09b180160c678cb5bab6` (`main` matched; no JSON or application code modified).
- Dataset counts: `research_nodes.json` 23/23; `research_upgrade_costs.json` 221/221; `research_prerequisites.json` 18/18; `research_user_state.json` 23 states/23 and 116 target deltas/116.
- Transition reconciliation for account scope `Matt_S283` (116 deltas; all mapped to cost rows): Timber `4,687.215M` vs `4,687.215M` (variance `0.000M`); Grain `4,687.215M` vs `4,687.215M` (variance `0.000M`); Herbs `14,058.618M` vs `14,058.618M` (variance `0.000M`); Study Scrolls `138,120` vs `138,120` (variance `0`); normalized duration `1,555,117` vs `1,555,117` minutes (variance `0`).
- Prerequisite graph: all 18 rules reference existing node IDs; zero broken/orphan references and zero cycles. Required terminal edge `11023` level 1 -> `11022` level 10 is present. Node `11019` has the required dependencies on `11017` and `11018` (level 1 rules present; its level-10 dependency rules are also represented).
- Verdict: **CLEAN / DAG VERIFIED**. No mathematical discrepancies or JSON parse failures observed.

## EVIDENCE — 2026-08-31 Full research database QA

- Status: **BLOCKED** — the requested full 18-tree dataset is not committed on `origin/main`.
- Canonical commit checked: `81dd56a9ef87781c957590592b13d45500ea1e68` on `main`, matching `origin/main`.
- Committed blob counts: `research_nodes.json` declares/contains 23 nodes; `research_upgrade_costs.json` declares/contains 221 level-cost rows; `research_user_state.json` contains 23 states and 116 target deltas. These are the earlier Commando slice, not 18 trees / 348 nodes / 2,287 rows.
- Worktree note: local `data/research/research_nodes.json`, `research_upgrade_costs.json`, and `docs/architect_state.md` are modified and uncommitted. They were not treated as canonical and were not audited or reverted.
- Full-dataset schema, unit, zero-resource-tree, and 18-tree numeric validation was not performed. Waiting for ATLAS Copilot to commit the full normalization to `origin/main`, then rerun this audit against committed blobs.

## EVIDENCE — 2026-08-31 Full 18-tree research QA

- Status: **COMPLETE**. Audited canonical `origin/main` at `3ea55cddb388a8312dfc56e784a18b5460845a82` (HEAD matched `origin/main`). Both canonical files parsed successfully.
- Dataset totals: `research_nodes.json` declares/contains 348 nodes; `research_upgrade_costs.json` declares/contains 2,287 level-cost rows; 18 unique source branches are represented.
- Branch coverage table (`nodes / cost rows`): Alliance Duel `14 / 132`; Caravan Transport `9 / 43`; Commando `23 / 221`; Defensive Tactics `16 / 151`; Development `18 / 86`; Economy `23 / 107`; Full Development `16 / 80`; Hero `28 / 140`; Offensive Tactics `16 / 151`; Prosperous Economy `16 / 76`; Ranger Mastery `23 / 200`; Soldier `20 / 100`; Squad 1 `20 / 100`; Squad 2 `20 / 100`; Squad 3 `20 / 100`; Squad 4 `20 / 100`; Warlock Mastery `23 / 200`; Warrior Mastery `23 / 200`.
- Structural integrity: zero duplicate node IDs; zero duplicate cost IDs; zero orphan cost rows; all 2,287 cost rows reference one of the 348 nodes.
- Resource fields: `timber_m`, `grain_m`, and `herbs_m` are runtime `Double` values for every row; zero negative values in each field.
- Integer fields: `study_scrolls`, `might_gain`, and `normalized_minutes` are runtime `Int64` values for every row; zero negative or non-integral values.
- Zero-resource trees: Alliance Duel has 132 rows and Caravan Transport has 43 rows; both have `timber_m=0.0`, `grain_m=0.0`, and `herbs_m=0.0` on every row while retaining valid non-negative scroll and duration integers.
- Verdict: **CLEAN / COMPLETE**. No declared-count divergence, duplicate IDs, orphan references, negative numeric values, or type/unit violations observed in the canonical full dataset.
- Worktree note: pre-existing local modifications remain in `data/research/research_nodes.json`, `data/research/research_upgrade_costs.json`, `docs/architect_state.md`, and `docs/agent_signals/scout.md`; those were not reverted or treated as canonical. This PROBE signal file is the only file modified by this audit.

## EVIDENCE — 2026-08-31 Account state capture specification

- Status: **PARTIAL**. Drafted `docs/account_state_capture_spec.md` as a passive, zero-input specification for research, building, resource, and speedup state ingestion.
- Canonical grounding: repository is on `main` at `02c586f544fd4a9fc4210d83c26046c38a18a0b7`; requested base `3ea55cddb388a8312dfc56e784a18b5460845a82` was not checked out, and no Git state was changed.
- Implementation evidence: requested `src/last_asylum_doctor/client/shadow_observer.py` is absent. The draft is grounded in the available `src/last_asylum_doctor/probe/shadow_observer.py` and `tools/probe_phase1_ui_ocr.py`, including immutable screenshot hashes, foreground/package metadata, OCR anchors, crop coordinates, preprocessing variants, confidence, validation status, and passive provenance.
- Current schema evidence: `data/research/research_user_state.json` parses as schema version 1 with 23 states and 116 target deltas for the Commando slice; it has no building or inventory sections. The draft therefore defines the 18-tree/348-node and building/inventory shapes as a proposed versioned extension, not as an existing canonical contract.
- Specification coverage: all 18 research branches are required by catalog join; research levels require exact node identity plus current-level evidence; Sanctuary, Research Lab, and Training Grounds use a separate building record; resources and speedups require explicit canonical units; `REVIEW`/`FAIL` candidates never mutate canonical state; conflicts remain conflicts; raw evidence remains hash-linked and read-only.
- Validation: `git diff --check -- docs/account_state_capture_spec.md` passed. No canonical application code, JSON data, or Git history was modified.
