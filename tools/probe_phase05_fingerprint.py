"""Bounded UnityFS object/type fingerprinting for Phase 0.5.

This script reads only explicitly selected Unity asset bundles embedded in the
already-pulled abPack1 APK. It enumerates serialized object types and inspects
TextAsset names/content for small tracer terms; it does not extract or write
game assets.

Requires UnityPy (tested with 1.25.3) and is intentionally not part of the
application runtime.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import UnityPy


DEFAULT_TARGETS = (
    "assets/ABAsset/gamedata_basedb_f_basedata_jit.assetbundles",
    "assets/ABAsset/gamedata_basedb_f_en.assetbundles",
    "assets/ABAsset/gamedata_language_f_en.assetbundles",
    "assets/ABAsset/gamedata_pb_f.assetbundles",
    "assets/ABAsset/gamedata_atlasconfig_f.assetbundles",
    "assets/ABAsset/luascript_logic.assetbundles",
    "assets/ABAsset/luascript_eyu_logic_datas_building.assetbundles",
    "assets/ABAsset/luascript_eyu_logic_ui_item_hero.assetbundles",
    "assets/ABAsset/luascript_eyu_logic_ui_item_tech.assetbundles",
)
TRACERS = ("Antitoxin", "Study Scroll", "Gearstone", "Sanctuary", "Research Lab", "Training Grounds")
CONTEXT_LIMIT = 240


def text_asset_record(obj: object) -> dict[str, object]:
    data = obj.read()
    script = getattr(data, "m_Script", "")
    if isinstance(script, bytes):
        text = script.decode("utf-8", errors="replace")
    else:
        text = str(script)
    name = str(getattr(data, "m_Name", ""))
    path_name = str(getattr(obj, "container", ""))
    return {
        "name": name,
        "path": path_name,
        "length": len(text),
        "text": text,
    }


def safe_context(text: str, term: str) -> str:
    match = re.search(re.escape(term), text, flags=re.IGNORECASE)
    if not match:
        return ""
    start = max(0, match.start() - CONTEXT_LIMIT // 2)
    end = min(len(text), match.end() + CONTEXT_LIMIT // 2)
    return re.sub(r"\s+", " ", text[start:end])


def classify_text(path: str, text: str) -> dict[str, object]:
    stripped = text.lstrip("\ufeff \t\r\n")
    extension = Path(path).suffix.lower()
    printable = sum(char.isprintable() or char in "\r\n\t" for char in text)
    human_readable = bool(text) and printable / len(text) >= 0.85
    kind = "binary/serialized TextAsset"
    keys: list[str] = []
    if not human_readable:
        return {"kind": kind, "keys": keys, "human_readable": False}
    kind = "text"
    if extension == ".json" or stripped.startswith(("{", "[")):
        try:
            value = json.loads(stripped)
            kind = "JSON"
            if isinstance(value, dict):
                keys = list(value)[:30]
        except json.JSONDecodeError:
            kind = "JSON-like/unparsed"
    elif extension in {".csv", ".tsv"} or ("\n" in text and "," in text[:1000]):
        kind = "CSV/TSV-like"
        first_line = text.splitlines()[0] if text.splitlines() else ""
        keys = [part.strip() for part in re.split(r"[,\t]", first_line)[:30]]
    elif "function " in text or "local " in text or "require(" in text:
        kind = "Lua-like text"
    return {"kind": kind, "keys": keys, "human_readable": "\x00" not in text}


def inspect_bundle(apk: Path, target: str) -> dict[str, object]:
    with zipfile.ZipFile(apk) as archive:
        payload = archive.read(target)
    environment = UnityPy.load(payload)
    object_types = Counter(obj.type.name for obj in environment.objects)
    text_assets: list[dict[str, object]] = []
    for obj in environment.objects:
        if obj.type.name == "TextAsset":
            record = text_asset_record(obj)
            record["classification"] = classify_text(str(record["path"]), str(record["text"]))
            text_assets.append(record)
    tracer_hits = []
    for asset in text_assets:
        text = str(asset["text"])
        for term in TRACERS:
            if re.search(re.escape(term), text, flags=re.IGNORECASE):
                tracer_hits.append(
                    {
                        "term": term,
                        "asset_name": asset["name"],
                        "asset_path": asset["path"],
                        "length": asset["length"],
                        "context": safe_context(text, term),
                        "classification": asset["classification"],
                    }
                )
    for asset in text_assets:
        del asset["text"]
    return {
        "bundle": target,
        "bundle_bytes": len(payload),
        "object_count": len(environment.objects),
        "object_types": dict(sorted(object_types.items())),
        "text_asset_count": len(text_assets),
        "text_asset_names": [str(asset["name"]) for asset in text_assets[:40]],
        "interesting_text_assets": [
            asset
            for asset in text_assets
            if re.search(
                r"(?i)(item|building|research|tech|resource|curio|raven|antitoxin|sanctuary|study|gear|cost|level|progress|training|lab)",
                str(asset["name"]),
            )
        ][:80],
        "tracer_hits": tracer_hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    parser.add_argument("--target", action="append", dest="targets")
    args = parser.parse_args()
    targets = args.targets or list(DEFAULT_TARGETS)
    for target in targets:
        try:
            print(json.dumps(inspect_bundle(args.apk, target), ensure_ascii=True))
        except Exception as exc:  # keep one unsupported bundle from hiding others
            print(json.dumps({"bundle": target, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
