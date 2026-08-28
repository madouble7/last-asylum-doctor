# Probe Phase 0 — Last Asylum Installed Client Reconnaissance

Date: 2026-08-28  
Scope: read-only host inspection; no game interaction, ADB input, runtime modification, or protection bypass.

## Executive verdict

BlueStacks is installed and its configured `Pie64` instance has a host-side
AppCache record for **Last Asylum: Plague** (`com.phs.global`, version name
`1.0.97`, version code `97`). The package is therefore present in BlueStacks'
local application metadata, but the package-manager facts and APK contents could
not be verified in this pass.

The blocking boundary is explicit: BlueStacks has Android Debug Bridge disabled
(`bst.enable_adb_access="0"`), and no emulator/player process is running. The
bundled ADB daemon was reachable locally, but it reported no Android devices.
The probe instructions require stopping when enabling ADB needs a user-visible
setting change. No setting was changed and no workaround was attempted.

## A. BlueStacks / ADB result

### Confirmed

- BlueStacks installation: `C:\Program Files\BlueStacks_nxt`
- BlueStacks version: `5.22.255.1014`
  - corroborated by `HD-Player.exe` file version and the BlueStacks uninstall
    registry entry
- BlueStacks Services version: `3.0.9`
- Bundled ADB: `C:\Program Files\BlueStacks_nxt\HD-Adb.exe`
- ADB version: `Android Debug Bridge version 1.0.36`, revision
  `6e8ac8fa2d76-android`
- Configured instance: `Pie64`, display name `BlueStacks App Player`
- Configured ADB port: `5555`
- Configured ABI list: `x86,x64,arm,arm64`
- The local ADB daemon started normally on `127.0.0.1:5037`.
- `adb devices -l` returned an empty device list.
- BlueStacks service processes were running, but no `HD-Player` process was
  running at inspection time.

### Blocking setting

The local configuration contains:

```text
bst.enable_adb_access="0"
bst.enable_adb_remote_access="0"
```

Matt must enable BlueStacks' **Android Debug Bridge (ADB)** switch for the
`Pie64` instance in the normal BlueStacks settings UI (the ADB switch is under
Settings → Advanced in this BlueStacks generation), then leave the instance
running for a rerun. Remote ADB access is not required; do not enable it for
this static inspection.

This is the exact user-visible change required by the probe. The local config
was not edited by this run.

### Not confirmed

- Android release/API level: not obtained from a live device.
- Live emulator ABI: the ABI list above is configuration metadata, not a live
  `getprop` result.
- A running emulator instance: none observed.

## B. Installed Last Asylum version

### Confirmed from host-side BlueStacks AppCache

The file `C:\ProgramData\BlueStacks_nxt\Engine\Pie64\AppCache\AppCache.json`
contains this application record:

| Field | Value |
|---|---|
| App label | `Last Asylum: Plague` |
| Package | `com.phs.global` |
| Version name | `1.0.97` |
| Version code | `97` |
| Activity | `com.games37.sdk.AtlasPluginDemoActivity` |
| Orientation | Portrait |
| Host-side install date | `16.08.2026` |

This establishes the version recorded by BlueStacks' host metadata. It is not
equivalent to a live package-manager query, so the APK/package-manager version
remains **not independently verified**.

## C. Base/split APK inventory

No package-manager query was possible because no device was available through
ADB. Consequently the following remain unavailable:

- base APK path and filename
- base APK size
- split APK paths, filenames, and sizes
- complete split inventory
- split names as reported by Android

No APK or split was pulled. The ignored `data/raw/` location remains unchanged.

## D. `abPack1` verified status and actual type

**Unverified on this installation.** The prior lead that a split named
`abPack1` exists was not tested against this device's package manager or files.
There is no local evidence in the inspected host metadata that establishes its
filename, path, size, container type, magic/header, or contents.

The name `abPack1` is not treated as evidence of an AssetBundle or any other
format.

## E. Engine/framework evidence

No installed APK/split archive was available for inspection. Therefore all
client-engine findings below are **UNCONFIRMED** in this pass:

- Unity markers (`libunity.so`, `UnityPlayer`, `assets/bin/Data`,
  `globalgamemanagers`, `data.unity3d`, `*.assets`, `*.resS`, AssetBundle
  manifests, Addressables catalogs): untested.
- Other engine/framework markers: untested.

The host-side activity namespace (`com.games37.sdk`) is not sufficient to
classify the game engine.

## F. IL2CPP / Mono evidence

Both classifications are **UNCONFIRMED** because the native libraries and APK
contents were not accessible through the permitted route:

- IL2CPP (`libil2cpp.so`, `global-metadata.dat`): untested.
- Mono managed assemblies/DLL structure: untested.

No decompilation or reverse-engineering toolchain was installed.

## G. Structured-data candidates

No package or split was available to scan. There are therefore no confirmed
game-data candidates from this Phase 0 run.

The following candidate classes remain **unavailable/unassessed**:

- JSON, CSV/TSV, XML, SQLite, protobuf/schema indicators
- localization tables and configuration files
- Addressables catalogs
- item/resource, hero, building, research, gear, Raven, or Curio identifiers
- cost/level tables and prerequisite/unlock definitions
- shop/event configuration
- server/season configuration

No parser tooling appears justified until package access is enabled and a file
listing demonstrates a real need.

## H. Localization / ID evidence

The requested fingerprint terms were not searched inside the client because no
APK/split contents were accessible. There are no Phase 0 localization or
nearby-ID findings for:

`Study Scroll`, `Gearstone`, `Raven Essence`, `Raven Fruit`, `Antitoxin`,
`Skill Badge`, and `Sanctuary`.

The host AppCache label confirms only the display name and package metadata; it
does not contain gameplay localization or numeric truth.

## I. Whether useful static extraction appears feasible

**Not yet assessable.** The presence of a locally recorded application and
configured emulator storage indicates that a static package inspection may be
feasible after normal ADB access is enabled. This run provides no evidence
about whether useful structured game data is actually embedded in the APK,
splits, downloaded asset files, or only delivered/validated by the server.

## J. What static data appears unavailable/server-driven

Because package contents were not inspected, no static/server-driven split can
be made. In particular, progression tables, prices, unlock conditions,
inventory truth, shop/event data, and season configuration are all unavailable
from this run and must not be inferred from the package name or host metadata.

## K. Highest-value next experiment

After Matt enables the normal BlueStacks ADB setting and starts `Pie64`, rerun
the bounded sequence:

1. `HD-Adb.exe devices -l`
2. `shell getprop` for Android release/ABI metadata
3. `shell pm path com.phs.global`
4. `shell dumpsys package com.phs.global` for version and split metadata
5. Pull only the APK/split files to the ignored versioned probe directory.

Then record hashes and inspect archive listings/signatures, stopping if useful
structured data is found. No input/tap/swipe commands are needed.

## L. Whether MINER should be created now

**No.** MINER should not be created until a real package/split listing shows
that accessible, useful structured data exists and its format is understood.

## M. Security/protection boundary encountered

The required boundary was the disabled ADB setting. The probe stopped before
any package-manager query, file pull, archive inspection, decryption, brute
force, patching, hooking, memory access, packet interception, certificate
bypass, rooting, or anti-cheat work.

No purchases, upgrades, battles, item use, reward claims, gameplay, or
game-state-changing taps occurred.

## Commit / working-tree note

This report is the only intended repository change from the reconnaissance.
No binary client files, extracted assets, credentials, or emulator disk images
were copied into the repository.
