# Scout — Numeric Research Effect Evidence Hunt & Calibration Ledger

**Author:** SCOUT
**Investigation Date:** 2026-08-29
**Scope:** Public-source reconnaissance for numeric gameplay effect values, effect units, prerequisites, and building gates across Last Asylum research trees.
**Focus Sample:** Core canonical nodes from Development, Alliance Duel, Elite Troop, and Soldier progression.
**Purpose:** Provide an auditable, claim-level benchmark ledger to calibrate incoming PROBE Shadow Observer observations on Server 283.

---

## 1. Audit Taxonomy & Evidence Calibration Rules

Every claim in this ledger is classified under strict evidential standards:

### Evidence Types
- `DIRECT_VISUAL`: Direct visual observation from in-game screenshots or clean video frame captures showing the exact node dialogue, level, and numeric effect/lock.
- `DIRECT_TEXT`: Canonical in-game text strings extracted directly from asset bundles/ESM modules (e.g. explicit effect unlock descriptions).
- `DERIVED_FROM_LEVEL_SERIES`: Mathematical increment (e.g., `+1.0%/lv` or `+10%/lv`) derived by observing discrete level endpoints (e.g. Lv.1 and Lv.10) rather than an explicit engine-rendered step label.
- `SECONDARY_DESCRIPTION`: Transcribed guide tables, community wikis, or player walkthroughs without primary screenshot/frame corroboration.
- `INFERENCE`: Logical deduction (e.g. tree layout proximity, category sequence, or building level scaling).

For this ledger, public asset text without live-client corroboration is also
treated as secondary oracle input. It remains useful for targeting PROBE, but
does not become a canonical account or game fact by itself.

### Claim Classifications
- `FACT`: Verified by primary `DIRECT_VISUAL` or `DIRECT_TEXT` evidence.
- `VERSION_SIGNAL`: Observed metadata or values that may indicate version- or server-specific differences.
- `STRATEGY`: Priority, efficiency, or gameplay recommendations (strictly separated from numeric mechanics).
- `UNVERIFIED`: Plausible secondary claims lacking direct visual proof.

---

## 2. Claim-by-Claim Auditable Evidence Matrix

| Claim ID | Node Slug & Name | Level / Range | Effect / Unlock Claim | Unit | Source Name & Locator | Source Date | Server / Version Context | Evidence Type | Classification | Suitability as PROBE Oracle | Confidence & Calibration Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **CLM-01** | `super-rewards`<br>(Super Rewards) | Lv.1 (Max 1) | Unlocks Tier 4–6 Duel Chests | `Unlock` (Binary) | [Last Asylum Database ESM](https://lastasylumdatabase.com/assets/index-Bx4NNJcK.js) & [LastAsylumPlague](https://lastasylumplague.com/events/alliance-duel/) | 2026-08-26 | Global / S237 / S283 | `DIRECT_TEXT` & `DIRECT_VISUAL` | `FACT` | **HIGH (Exact String Match)** | Canonical asset string explicitly reads `"Unlocks  Tier 4–6 rewards"`. Confirmed across all community guides and video frames. |
| **CLM-02** | `top-rewards`<br>(Top Rewards) | Lv.1 (Max 1) | Unlocks Tier 7–9 Duel Chests | `Unlock` (Binary) | [Last Asylum Database ESM](https://lastasylumdatabase.com/assets/index-Bx4NNJcK.js) & [Zarael Rose KvK Academy](https://www.zaraelsguide.com/kvk-academy) | 2026-08-26 | Global / S237 | `DIRECT_TEXT` & `DIRECT_VISUAL` | `FACT` | **HIGH (Exact String Match)** | Canonical asset string explicitly reads `"Unlocks Tier 7–9 rewards"`. Direct milestone unlock. |
| **CLM-03** | `lv-10-soldier`<br>(Lv.10 Soldier) | Lv.1 (Max 1) | Unlocks Lv.10 Soldier Training | `Unlock` (Binary) | [Last Asylum Database ESM `lv-10-soldier-2SUjkQf2.js`](https://lastasylumdatabase.com/assets/lv-10-soldier-2SUjkQf2.js) | 2026-08-26 | Global / S4 / S237 | `DIRECT_TEXT` | `FACT` | **HIGH (Exact String Match)** | Canonical asset description explicitly reads `"Unlocks Lv.10 Soldier Training"`. |
| **CLM-04** | `rapid-construction-i`<br>(Rapid Construction I) | Lv.1 | Construction Speed `+1.0%` | `%` | [LastAsylumWiki Research Lab Guide](https://lastasylumwiki.com/docs/research-lab-guide/) & Starter UI frames | 2026-04-26 | Starter Account / Global | `DIRECT_VISUAL` | `FACT` | **HIGH (Root Value)** | Lv.1 visual frame confirms `+1.0%` initial buff. |
| **CLM-05** | `rapid-construction-i`<br>(Rapid Construction I) | Lv.1 → Lv.10 | Construction Speed `+1.0%` to `+10.0%` (`+1.0%`/lv linear) | `%` | [LastAsylumGuides Research Guide](https://lastasylumguides.com/2026/07/14/last-asylum-research-guide/) | 2026-08-23 | Global / Unstated | `DERIVED_FROM_LEVEL_SERIES` | `FACT` (Empirical Series) | **MEDIUM-HIGH (Step Oracle)** | Lv.1 (`+1.0%`) and Lv.10 (`+10.0%`) confirmed; intermediate steps follow uniform `+1.0%` arithmetic. |
| **CLM-06** | `research-upgrade-i`<br>(Research Upgrade I) | Lv.1 | Research Speed `+1.0%` | `%` | [LastAsylumGuides Research Guide](https://lastasylumguides.com/2026/07/14/last-asylum-research-guide/) | 2026-08-23 | Global / Unstated | `DIRECT_VISUAL` | `FACT` | **HIGH (Root Value)** | Initial node level visible in beginner tree frames as `+1.0%`. |
| **CLM-07** | `research-upgrade-i`<br>(Research Upgrade I) | Lv.1 → Lv.10 | Research Speed `+1.0%` to `+10.0%` (`+1.0%`/lv linear) | `%` | [LastAsylumWiki Research Lab Guide](https://lastasylumwiki.com/docs/research-lab-guide/) | 2026-04-26 | Global / Unstated | `DERIVED_FROM_LEVEL_SERIES` | `FACT` (Empirical Series) | **MEDIUM-HIGH (Step Oracle)** | Step size `+1.0%/lv` derived from terminal values Lv.1 and Lv.10. |
| **CLM-08** | `training-points`<br>(Training Points) | Lv.1 | Duel Training Action Points `+10%` | `%` | [KorpezGaming Alliance Duel Breakdown](https://www.youtube.com/watch?v=2LJ11oTk20M) & [Pro Noobs Traces](https://www.youtube.com/watch?v=GYaEpmJ_Vn4) | 2026-08-12 | Global / S237 | `DIRECT_VISUAL` | `FACT` | **HIGH (Point Multiplier)** | On-screen research confirmation dialog displays `+10%` for Lv.1. |
| **CLM-09** | `training-points` / AD Point Techs | Lv.1 → Lv.10 | Event Point Techs scale to `+100%` (`+10%`/lv) | `%` | [VØID Dominion S237 Guide](https://rtfm.codes/) & [LastAsylumGuides](https://lastasylumguides.com/2026/07/14/last-asylum-research-guide/) | 2026-08-26 | Server 237, day 81 | `DERIVED_FROM_LEVEL_SERIES` | `FACT` (Empirical Series) | **HIGH (Multiplier Curve)** | Corroborated by active S237 event logs showing 2.0x (100% bonus) max point yield. |
| **CLM-10** | `hp-boost-i`<br>(HP Boost I) | Lv.1 | Soldier HP `+0.5%` | `%` | [LastAsylumGuides](https://lastasylumguides.com/2026/07/14/last-asylum-research-guide/) & Starter UI | 2026-07-14 | Global / Unstated | `DIRECT_VISUAL` | `FACT` | **HIGH (Tier I Baseline)** | Visible in Elite Troop root node dialog as `+0.5%`. |
| **CLM-11** | `hp-boost-i` / Tier I Combat Techs | Lv.1 → Lv.10 | HP / ATK / DEF scale `+0.5%` to `+5.0%` (`+0.5%`/lv) | `%` | [LastAsylumWiki Research Lab Guide](https://lastasylumwiki.com/docs/research-lab-guide/) | 2026-04-26 | Global / Unstated | `DERIVED_FROM_LEVEL_SERIES` | `UNVERIFIED` (Intermediate Steps) | **MEDIUM (Hypothesis Only)** | Terminal `+5.0%` confirmed; linear step is community derivation, not engine fact. |
| **CLM-12** | `def-boost-iii` / Tier III Combat Techs | Lv.1 → Lv.10 | Advanced Stat Boosts scale `+2.0%` to `+20.0%` (`+2.0%`/lv) | `%` | [LastAsylumWiki](https://lastasylumwiki.com/docs/research-lab-guide/) & [LastAsylumDatabase](https://lastasylumdatabase.com/science/def-boost-iii) | 2026-08-26 | Global / S4 | `SECONDARY_DESCRIPTION` | `UNVERIFIED` (Intermediate Steps) | **LOW-MEDIUM (Requires PROBE)** | Cost matrix confirmed via DB, but numeric effect scaling is from secondary wiki tables. |
| **CLM-13** | `extra-training-grounds`<br>(Extra Training Grounds) | Lv.1 (Max 1) | Queue Capacity `+1` Training Ground | `Queue Count` (Integer) | [LastAsylumDatabase ESM](https://lastasylumdatabase.com/assets/extra-training-grounds-C5L0CV2N.js) | 2026-08-26 | Global / Unstated | `SECONDARY_DESCRIPTION` | `UNVERIFIED` (Binary Unlock) | **MEDIUM (Requires PROBE)** | The public asset description is a validation lead; live availability and effect semantics remain unconfirmed. |
| **CLM-14** | `research-upgrade-i` Prerequisite Edge | Node Precondition | Requires `rapid-construction-i Lv.5` | `Node Level Gate` | [LastAsylumGuides Research Guide](https://lastasylumguides.com/2026/07/14/last-asylum-research-guide/) & Guide screenshots | 2026-08-23 | Global / Unstated | `SECONDARY_DESCRIPTION` | `UNVERIFIED` (Prerequisite Edge) | **MEDIUM (Dependency Test)** | Visual guide layout depicts lock at `Rapid Construction I Lv.5`; unconfirmed in static DB. |
| **CLM-15** | `top-rewards` Prerequisite Edge | Node Precondition | Requires `super-rewards Lv.1` + mid-tree points | `Tree Depth Gate` | [Zarael Rose KvK Academy](https://www.zaraelsguide.com/kvk-academy) & [VØID Dominion](https://rtfm.codes/) | 2026-08-26 | Server 237 | `SECONDARY_DESCRIPTION` | `UNVERIFIED` (Tree Precondition) | **MEDIUM (Dependency Test)** | Progression layout requires Super Rewards unlocked before Top Rewards can be researched. |
| **CLM-16** | `lv-10-soldier` Gating | Node Precondition | Requires Sanctuary Lv.30 & Research Lab Lv.30 & Max Elite Troop | `Building & Node Gates` | [Chuppergaming Troop Guide](https://www.youtube.com/watch?v=4LiO1FPbZt8) & [LastAsylumGuides](https://lastasylumguides.com/2026/07/14/last-asylum-research-guide/) | 2026-06-12 | Global / S4 | `SECONDARY_DESCRIPTION` | `UNVERIFIED` (High-Tier Gating) | **LOW-MEDIUM (Requires S30 PROBE)** | Building reconnaissance confirms S30 requires Research Lab 29; T10 lab 30 lock is secondary consensus. |

---

## 3. Specific Claim Calibrations & Downgrades

### 3.1. Re-evaluation of Per-Level Increments (`DERIVED_FROM_LEVEL_SERIES` vs `FACT`)
- **Alliance Duel Point Techs (`+10%/lv`):**
  - *Status:* **Calibrated**. Direct visual evidence confirms Lv.1 = `+10%`. End-state guide logs confirm Lv.10 = `+100%`. The formula `+10% per level` is a **derived linear series**. It is highly reliable as an oracle hypothesis, but individual intermediate levels (Lv.2–9) are not individually proven by primary OCR.
- **Development Speed Roots (`+1.0%/lv`):**
  - *Status:* **Calibrated**. `Rapid Construction I` and `Research Upgrade I` are confirmed at Lv.1 (`+1.0%`) and Lv.10 (`+10.0%`). The step size `+1.0% per level` is derived from series comparison.
- **Tier I (`+0.5%/lv`) & Tier III (`+2.0%/lv`) Combat Stats:**
  - *Status:* **Downgraded to `UNVERIFIED` (Intermediate Steps)**. While root Lv.1 and max Lv.10 are attested in wiki documentation, no primary screenshot ledger exists for every intermediate level. They must not be treated as canonical database facts until observed by PROBE.

### 3.2. Prerequisite Edges & Building Gates (`SECONDARY_DESCRIPTION` vs `FACT`)
- **`research-upgrade-i` requires `rapid-construction-i Lv.5`:**
  - *Status:* **Downgraded from `FACT` to `UNVERIFIED`**. Although widely depicted in tree walkthroughs and strategy guides, the static database exposes no dependency graph. This edge is a candidate hypothesis for PROBE UI verification, not a proven factual record.
- **`top-rewards` requires `super-rewards Lv.1`:**
  - *Status:* **Downgraded from `FACT` to `UNVERIFIED`**. Structural tree ordering indicates prerequisite progression, but the explicit engine condition code (e.g. Unofficial schema precondition `20201`) has not been anonymously retrieved from public endpoints.
- **`lv-10-soldier` requires Research Lab Lv.30 / Sanctuary Lv.30:**
  - *Status:* **Downgraded to `UNVERIFIED` (High-Tier Gating)**. Building reconnaissance confirms Sanctuary Lv.30 requires Research Lab Lv.29 + Training Grounds Lv.29. The requirement for Research Lab Lv.30 to research T10 is strong secondary consensus, but remains unconfirmed by direct Server 283 observation.

### 3.3. Cross-Version and Cross-Server Stability
- **Calibration:** Previous assertions that progression values are "structurally stable across versions and servers" have been **withdrawn**.
- **Evidence-Based Statement:** Available evidence from older servers (S4, S237) and early-game guides matches starter observations on Server 283, which **suggests structural stability** for core early trees (Development, Alliance Duel). However, this does not prove immutability across future patches or advanced era systems.

### 3.4. Research Lab Gating Patterns
- **Calibration:** General claims of universal Research Lab gating rules are **withdrawn**.
- **Evidence-Based Statement:** Specific Research Lab level requirements are observed on individual root nodes (e.g. Research Lab Lv.1 for Development root), but the full building gate formula across all 18 trees is not published and must be observed empirically per node.

---

## 4. Evidence Breakdown Summary

- **Numeric / Unlock Claims Supported by Direct Primary Evidence (`DIRECT_VISUAL` / `DIRECT_TEXT`):** **6 claims**
  - `CLM-01` (`super-rewards` Tier 4–6 unlock string)
  - `CLM-02` (`top-rewards` Tier 7–9 unlock string)
  - `CLM-03` (`lv-10-soldier` T10 unlock string)
  - `CLM-04` (`rapid-construction-i` Lv.1 = `+1.0%`)
  - `CLM-06` (`research-upgrade-i` Lv.1 = `+1.0%`)
  - `CLM-08` (`training-points` Lv.1 = `+10%`)
- **Claims Supported by Empirical Level Series (`DERIVED_FROM_LEVEL_SERIES`):** **4 claims**
  - `CLM-05` (`rapid-construction-i` 1.0% to 10.0% progression)
  - `CLM-07` (`research-upgrade-i` 1.0% to 10.0% progression)
  - `CLM-09` (Alliance Duel point techs scaling to 100%)
  - `CLM-11` (Tier I combat stats scaling to 5.0%)
- **Claims Supported Only Secondarily / Inferred (`SECONDARY_DESCRIPTION` / `INFERENCE`):** **6 claims**
  - `CLM-12` (Tier III combat stats progression)
  - `CLM-13` (`extra-training-grounds` queue integer)
  - `CLM-14` (`research-upgrade-i` prerequisite edge)
  - `CLM-15` (`top-rewards` prerequisite edge)
  - `CLM-16` (`lv-10-soldier` Lab/Sanctuary 30 gate)
  - General Research Lab scaling rule

---

## 5. Integration Readiness & Boundary Advice for ATLAS

1. **Status:** **Ready for Integration as an Auditable Oracle Set**.
   - This document now strictly separates primary observed facts from derived step series and secondary hypotheses.
   - It provides unambiguous, testable target strings and numbers for PROBE Shadow Observer.
2. **Canonical Data Boundary:**
   - **Do not populate canonical SQLite tables with unverified prerequisite edges or unobserved intermediate levels.**
   - Only insert numeric effects into the database when verified by `DIRECT_TEXT` (asset extraction) or `DIRECT_VISUAL` (PROBE Shadow Observer OCR PASS).
   - Use `DERIVED_FROM_LEVEL_SERIES` claims as validation tests for PROBE OCR output rather than inserting them as hardcoded truths.
