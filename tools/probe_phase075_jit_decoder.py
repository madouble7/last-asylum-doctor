"""Bounded, non-decoding inspection of the three Phase 0.75 JIT payloads.

This intentionally stops at the UnityPy TextAsset boundary.  It records the
container, object type, byte fingerprints, and standard-format signatures for
BuildingLevel, BuildingUpgrade, and CollegeTechLevel.  It does not attempt
decompression, deobfuscation, decryption, deserialization, or row extraction.

Requires UnityPy (tested with 1.25.3).  This is inspection tooling, not game
runtime code.
"""

from __future__ import annotations

import argparse
import json
import math
import zipfile
from collections import Counter
from pathlib import Path

import UnityPy


BUNDLE = "assets/ABAsset/gamedata_basedb_f_basedata_jit.assetbundles"
FAMILIES = ("BuildingLevel", "BuildingUpgrade", "CollegeTechLevel")


def payload_bytes(obj: object) -> bytes:
    data = obj.read()
    value = getattr(data, "m_Script", b"")
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    return str(value).encode("utf-8", errors="replace")


def printable_ratio(payload: bytes) -> float:
    if not payload:
        return 0.0
    count = sum(byte in (9, 10, 13) or 32 <= byte <= 126 for byte in payload)
    return count / len(payload)


def entropy(payload: bytes) -> float:
    if not payload:
        return 0.0
    counts = Counter(payload)
    size = len(payload)
    return -sum((count / size) * math.log2(count / size) for count in counts.values())


def signatures(payload: bytes) -> dict[str, bool]:
    return {
        "gzip": payload.startswith(b"\x1f\x8b"),
        "zlib": len(payload) >= 2 and payload[:2] in {b"\x78\x01", b"\x78\x5e", b"\x78\x9c", b"\x78\xda"},
        "lz4_frame": payload.startswith(b"\x04\x22\x4d\x18"),
        "unityfs": payload.startswith(b"UnityFS"),
        "lua_bytecode": payload.startswith(b"\x1bLua"),
    }


def inspect(apk: Path) -> dict[str, object]:
    with zipfile.ZipFile(apk) as archive:
        bundle_bytes = archive.read(BUNDLE)

    environment = UnityPy.load(bundle_bytes)
    object_types = Counter(obj.type.name for obj in environment.objects)
    found: dict[str, dict[str, object]] = {}

    for obj in environment.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.read()
        name = str(getattr(data, "m_Name", ""))
        if name not in FAMILIES:
            continue
        payload = payload_bytes(obj)
        found[name] = {
            "text_asset_name": name,
            "container": str(getattr(obj, "container", "")),
            "length": len(payload),
            "header_hex": payload[:48].hex(" "),
            "printable_ratio": round(printable_ratio(payload), 6),
            "entropy_bits_per_byte": round(entropy(payload), 6),
            "standard_signatures": signatures(payload),
        }

    return {
        "bundle": BUNDLE,
        "bundle_bytes": len(bundle_bytes),
        "unitypy_object_count": len(environment.objects),
        "object_types": dict(sorted(object_types.items())),
        "targets": [found[name] for name in FAMILIES if name in found],
        "decoder_action": "stopped at TextAsset bytes; no decode or row parsing attempted",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.apk), ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
