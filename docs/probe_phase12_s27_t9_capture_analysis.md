# PROBE Phase 1.2 — Manual S27/T9 Capture Analysis

Date: 2026-08-28

Scope: four manually prepared screenshots only; no new capture, ADB input,
game interaction, or canonical-data write

Validation meanings:

- **PASS** — the visible pixels and at least one reliable OCR result agree;
  the multi-variant result has no unresolved digit ambiguity.
- **REVIEW** — the pixels, OCR variants, or field semantics leave a material
  ambiguity.
- **FAIL** — OCR did not recover the field reliably. A failed OCR variant is
  never silently normalized into a fact.

## Executive result

The batch confirms the shortest visible T9 chain:

```text
Sanctuary 27
    -> Training Grounds 27
    -> Soldier Training Level 9 / T9
```

The T9 lock says exactly **“Requires Lv.27 Training Grounds.”** It does not
show a Research Lab, Sanctuary, named-research, other-building, or resource
condition. Research Lab 27 is separately locked behind Sanctuary 27, but the
captures do not connect Research Lab 27 to T9.

The Training Grounds 26 -> 27 screen shows direct requirements of `56.0M`
Antitoxin, `252M` Grain, `252M` Timber, and `107M` Herbs, plus an effective
upgrade timer of `16d 11:17:56`. These are sufficient to estimate the direct
building resources to bank for the confirmed post-S27 T9 gate, at the compact
precision rendered by the game. T9 troop-training costs are not shown.

Speeding Sanctuary 27 is therefore **tactically useful for an earliest-T9
goal**: S27 is the visible lock on Training Grounds 27, which is the visible
lock on T9. The captures do not establish whether spending speedups now is
economically optimal relative to events or later queues.

## 1. Capture provenance

All PNG hashes were recomputed from the files and exactly match both the JSONL
manifest and individual sidecars. Every selected record identifies
`com.phs.global`, client `1.0.97`, version code `97`, server `283`, device
`emulator-5554`, and capture operation `exec-out screencap -p`.

| Label | Captured at UTC | Verified SHA-256 | Client | Server |
|---|---|---|---|---|
| `research-lab-building` | `2026-08-28T20:28:09.591581+00:00` | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` | `1.0.97 (97)` | `283` |
| `training-grounds-building` | `2026-08-28T20:30:46.433566+00:00` | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` | `1.0.97 (97)` | `283` |
| `t9-locked-requirements` | `2026-08-28T20:31:08.699973+00:00` | `cd2e476b710f4998515de9fd427279b1d105119ec63ef5818cb2fa3d2144814a` | `1.0.97 (97)` | `283` |
| `sanctuary-27-construction` | `2026-08-28T20:31:35.162637+00:00` | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` | `1.0.97 (97)` | `283` |

The label is operator-supplied provenance. It is not substituted for text
that is absent from the screenshot.

## 2. OCR and visual-review method

Each 900 x 1600 PNG was processed with the existing pipeline's four 2x
variants: grayscale, CLAHE, Otsu, and adaptive Gaussian thresholding. Focused
crops were then run for both building cost/timer regions, the T9 requirement,
and the Sanctuary countdown.

CLAHE and grayscale were the most consistently accurate general variants.
Otsu recovered one comma that the other Training Grounds variants rendered as
a period. Adaptive thresholding was the weakest on punctuation and small
digits. Examples retained as failures include:

- `19d 05810855` instead of `19d 05:10:55`;
- `16d 11817856` instead of `16d 11:17:56`;
- `1.4V/107V` instead of `1.4M/107M`;
- `13507`, `20001`, and `512.31` in the T9 stat panel.

These outputs were not normalized. Final PASS values below were accepted only
after direct pixel review and agreement from a reliable variant/crop.

## 3. Research Lab building

Static identity mapping supplied by the mission: **1007 = Research Lab**.
This is the building-upgrade panel, not an internal research-node dialog.

| Visible observation | Validation | Evidence SHA-256 |
|---|---|---|
| Title `Research Lab`; current `Lv.26`; `Next Level 27` | **PASS** | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` |
| Next-level Antitoxin line: `114M` | **PASS** | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` |
| Might `183,200 +34,000`; Research Speed `13.2% +0.5%` | **PASS** | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` |
| Red lock/prerequisite text: `Sanctuary Lv.27` | **PASS** | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` |
| Grain display `2.6M/423M`; Timber `4.2M/423M`; Herbs `17.3K/134M` | **PASS** as rendered strings | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` |
| `Original Time: 37d 22:50:03`; Upgrade `19d 05:10:55` | **PASS** | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` |
| Instant button `1,106,777` diamonds | **PASS** | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` |
| Exact unrounded resource integers and active construction modifiers | **REVIEW / not shown** | `85b3d3716123f1b0cca3024c2b3f739d4aeeeaee82cd6f8b0978202f6f5b3647` |

The denominator values appear under the panel's `Cost` heading and are the
visible requirement amounts. The numerator values are preserved exactly as
screen-local compact displays; because they changed between captures and are
rounded to `M`/`K`, they are not promoted to one canonical account balance.

## 4. Training Grounds building

Static identity mapping supplied by the mission: **1020 = Training Grounds**.

| Visible observation | Validation | Evidence SHA-256 |
|---|---|---|
| Title `Training Grounds`; current `Lv.26`; `Next Level 27` | **PASS** | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |
| Next-level Antitoxin line: `56.0M` | **PASS** | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |
| Might `142,400 +26,300`; Training Capacity `+531 +13` | **PASS** | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |
| `Soldier Training Level 8 +1` | **PASS** | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |
| Red lock/prerequisite text: `Sanctuary Lv.27` | **PASS** | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |
| Grain display `4.7M/252M`; Timber `6.3M/252M`; Herbs `1.4M/107M` | **PASS** as rendered strings | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |
| `Original Time: 32d 12:42:54`; Upgrade `16d 11:17:56` | **PASS** | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |
| Instant button visually reads `709,415`; only Otsu preserved the comma while other variants emitted `709.415` | **REVIEW** | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |
| Exact unrounded resource integers and active construction modifiers | **REVIEW / not shown** | `ab33b02945c73170103988174484bc67b4f5f986d02f69acda3ee520d418cbb9` |

The visible troop-tier relationship is direct: upgrading this building from
26 to 27 changes Soldier Training Level from 8 to 9.

## 5. T9 locked-requirements screen

This is the highest-confidence result in the batch. A focused crop recovered
the requirement exactly in CLAHE, grayscale, and Otsu; adaptive OCR produced
the retained failure `Reguires` while preserving the numeric condition.

| Visible observation | Validation | Evidence SHA-256 |
|---|---|---|
| Panel title `Training Grounds`; T9 is selected and locked; T10 is also locked | **PASS** | `cd2e476b710f4998515de9fd427279b1d105119ec63ef5818cb2fa3d2144814a` |
| Exact requirement: `Requires Lv.27 Training Grounds` | **PASS** | `cd2e476b710f4998515de9fd427279b1d105119ec63ef5818cb2fa3d2144814a` |
| Action text: `Upgrade Training Grounds` | **PASS** | `cd2e476b710f4998515de9fd427279b1d105119ec63ef5818cb2fa3d2144814a` |
| No Research Lab level, Sanctuary level, named research, other building, resource, or other condition is shown in the T9 lock panel | **PASS for “not shown on this screen”** | `cd2e476b710f4998515de9fd427279b1d105119ec63ef5818cb2fa3d2144814a` |
| T9 stats: Might `1350`; Troop Load `2000`; Morale `512.5`; Soldier ATK `21.8`; Soldier DEF `21.6`; Soldier HP `9492.8` | **PASS** | `cd2e476b710f4998515de9fd427279b1d105119ec63ef5818cb2fa3d2144814a` |
| T9 troop-training resource cost, batch size, and training time | **FAIL / not visible** | `cd2e476b710f4998515de9fd427279b1d105119ec63ef5818cb2fa3d2144814a` |

“Not shown” does not mean “proven never required elsewhere.” It means this
specific lock screen names only Training Grounds 27.

## 6. Sanctuary construction screen

Static identity mapping supplied by the mission: **1001 = Sanctuary**.

| Visible observation | Validation | Evidence SHA-256 |
|---|---|---|
| `Construction Speedup` panel with active progress bar and `Sanctuary: Lv.26` | **PASS** | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` |
| Capture label says `sanctuary-27-construction`; the pixels do not independently print “target Lv.27” | **REVIEW** for the target; operator provenance plus surrounding screens supports the 26 -> 27 interpretation | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` |
| Remaining time `15d 02:00:33` at `2026-08-28T20:31:35.162637+00:00` | **PASS** | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` |
| Owned: 1-minute Construction Speedup `250`; 5-minute Construction Speedup `37`; 1-minute universal Speedup `653` | **PASS** | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` |
| The fully visible speedups equal `1,088` minutes = `18h 08m`; this is a lower bound because the next owned quantity is obscured | **PASS derived value** | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` |
| Instant completion button `35857` diamonds | **PASS as rendered** | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` |
| Unlabeled icon/value `28/28` | **REVIEW**; semantic meaning is not stated | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` |
| Numeric completion percentage, total/base construction time, and buff/modifier breakdown | **FAIL / not visible** | `0a50dda281680581adcda82439721b3d48042baa79131c84b4f30c44e08e4a4b` |

No percentage was estimated from the progress-bar width.

## 7. Cross-screen reconciliation

| Chain statement | Classification | Evidence |
|---|---|---|
| Account displays Research Lab 26 and Training Grounds 26 | **CONFIRMED CURRENT ACCOUNT FACT** | Both building panels and their respective verified hashes above. |
| Both level-27 building upgrades display `Sanctuary Lv.27` in red | **VISIBLE LOCK/REQUIREMENT** | Research Lab hash `85b3...3647`; Training Grounds hash `ab33...cbb9`. |
| Training Grounds 27 changes Soldier Training Level 8 -> 9 | **VISIBLE EFFECT** | Training Grounds hash `ab33...cbb9`. |
| T9 says `Requires Lv.27 Training Grounds` | **VISIBLE LOCK/REQUIREMENT** | T9 hash `cd2e...814a`. |
| S27 -> Training Grounds 27 -> T9 is the captured progression chain | **CONFIRMED FROM COMBINED EXPLICIT SCREENS** | Training Grounds and T9 hashes above. |
| Research Lab 27 is required for T9 | **UNKNOWN; NOT SHOWN** | The T9 panel contains no Research Lab condition. |
| A specific research is required for T9 | **UNKNOWN; NOT SHOWN** | No named research appears in the T9 panel. |
| The construction screenshot independently proves the target is S27 | **INFERENCE SUPPORTED BY CAPTURE LABEL** | Pixels show `Sanctuary: Lv.26`; the target-level text is absent. |

The factual graph is therefore:

```text
                         -> Research Lab 27 (available after S27; T9 link unknown)
Sanctuary 27 requirement
                         -> Training Grounds 27 -> Soldier Training Level 9 -> T9
```

## 8. Current decision support

### A. Is speeding up Sanctuary 27 currently useful?

**Yes for the narrow goal of reaching T9 sooner.** Completing S27 sooner
removes the visible lock on Training Grounds 27, and that building is the
only requirement named by the T9 screen. The screenshot shows `15d 02:00:33`
remaining at capture time and at least `18h 08m` of fully visible owned
speedups.

**No conclusion about optimal spending.** The batch does not show event
timing, the complete speedup inventory, competing build queues, or the value
of retaining speedups. It proves schedule utility, not economic optimality.

### B. What must Matt build/research immediately after S27?

For T9, the only confirmed next action is **upgrade Training Grounds 26 ->
27**. The captured T9 panel names no research. Research Lab 27 becomes
available after S27 and has visible costs/effects, but this batch does not
show it as part of the T9 gate.

### C. Can the resources to bank be estimated?

**Yes, at displayed compact precision for the building upgrades.**

| Immediate objective | Antitoxin | Grain | Timber | Herbs | Effective timer |
|---|---:|---:|---:|---:|---:|
| Confirmed T9 gate: Training Grounds 27 | `56.0M` | `252M` | `252M` | `107M` | `16d 11:17:56` |
| Separate S27-unlocked Research Lab 27 | `114M` | `423M` | `423M` | `134M` | `19d 05:10:55` |
| Both upgrades, display-level sum | `170M` | `675M` | `675M` | `241M` | Do not sum: separate queues/upgrades |

The Training Grounds screenshot's screen-local holdings imply approximate
shortfalls of `247.3M` Grain, `245.7M` Timber, and `105.6M` Herbs. Those are
**REVIEW**, not exact, because inputs such as `4.7M` are rounded displays.
Antitoxin does not show a current/required pair, so no Antitoxin shortfall is
calculated. T9 troop-training costs remain unknown.

### D. Exact remaining gaps

- total/base S27 construction time and a numeric completion percentage;
- complete speedup inventory and any event/opportunity-cost context needed to
  judge optimal use;
- T9 troop batch size, resource cost, and training time after it unlocks;
- any non-lock prerequisite that might appear only after Training Grounds 27.

None of those gaps changes the explicit Training Grounds 27 lock.

## 9. Minimum additional manual capture

No additional screenshot is needed to establish the S27 -> Training Grounds
27 -> T9 gate or the resources for the Training Grounds upgrade.

For an end-to-end T9 resource estimate, request **one future manual capture
after Training Grounds reaches level 27**:

- **Navigate to:** Training Grounds -> select T9 -> open the troop-training
  quantity/confirmation panel without confirming training.
- **Keep visible:** selected troop count/batch size, Grain/Timber/Herb or
  other resource costs, training time, and any remaining lock text.
- **Suggested label:** `t9-training-cost-and-time`.

Do not request another Research Lab screen unless the unlocked T9 panel adds a
Research Lab or named-research condition not present here.

## 10. OCR reliability verdict

**Reliable for reviewed UI extraction; not reliable for unattended numeric
ingestion.** The decisive lock text was exact in 3/4 focused variants, and
building costs/timers were recoverable with CLAHE/grayscale plus pixel review.
Small stylized punctuation and digits still fail materially in individual
variants. Every accepted fact remains tied to its screenshot hash, and no OCR
output was written to canonical tables.

## 11. Capture-harness cleanup

Capture-only ADB/frame logic now lives in
`tools/probe_capture_core.py`, which imports only the Python standard library.
`tools/probe_capture.py` imports that lightweight module and no longer imports
the OCR program. `tools/probe_phase1_ui_ocr.py` imports the same capture core
plus OpenCV, NumPy, and RapidOCR for OCR operations.

The existing `probe` optional dependency group in `pyproject.toml` declares
`opencv-python-headless` and `rapidocr-onnxruntime`; a manual unrecorded
RapidOCR installation is no longer the project setup path. The capture-only
boundary was verified with:

```text
py -3.13 -S tools/probe_capture.py --help
```

This succeeds with site packages disabled. A regression test also blocks
`cv2`, `numpy`, `onnxruntime`, and `rapidocr_onnxruntime` while importing the
capture entry point.

## 12. Repository safety

No screenshot, manifest, account-specific sidecar, OCR output, database, or
game file is committed. OCR analysis artifacts remain under ignored
`data/raw/probe/` paths.
