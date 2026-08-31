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
