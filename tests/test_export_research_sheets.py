"""Regression checks for spreadsheet-ready research exports."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from tools.export_research_sheets import (
    ALL_TREE_FIELDS,
    TARGET_PATH_FIELDS,
    export_all_trees,
    export_target_path,
)


def test_export_all_trees_writes_flat_canonical_table(tmp_path: Path) -> None:
    csv_path, json_path = export_all_trees(output_dir=tmp_path)

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    bundle = json.loads(json_path.read_text(encoding="utf-8"))

    assert len(rows) == 2_287
    assert bundle["tree_count"] == 18
    assert bundle["record_count"] == 2_287
    assert list(rows[0]) == list(ALL_TREE_FIELDS)
    assert rows[0]["Node ID"] == "1001"
    assert bundle["records"] == [_csv_record(row) for row in rows]


def test_export_target_path_writes_totals_deficit_and_timeline(tmp_path: Path) -> None:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "inventory": {
                    "timber_m": 1_000_000,
                    "grain_m": 1_000_000,
                    "herbs_m": 1_000_000,
                    "study_scrolls": 1_000_000,
                    "universal_speedups_minutes": 0,
                    "research_speedups_minutes": 0,
                }
            }
        ),
        encoding="utf-8",
    )

    csv_path, json_path = export_target_path(
        "11023",
        1,
        output_dir=tmp_path,
        inventory_file=inventory_path,
    )

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    bundle = json.loads(json_path.read_text(encoding="utf-8"))

    assert len(rows) == 116
    assert list(rows[0]) == list(TARGET_PATH_FIELDS)
    assert bundle["step_count"] == 116
    assert bundle["target"] == {"node_id": "11023", "level": 1}
    assert bundle["inventory_source"].endswith("inventory.json")
    assert bundle["deficit"]["Scrolls"] == 0
    assert bundle["timeline"]["Scroll Bottleneck Days"] == 0.0
    assert bundle["timeline"]["Scroll Bottleneck Unbounded"] is False


def _csv_record(row: dict[str, str]) -> dict[str, object]:
    text_fields = {"Node ID", "Branch", "Name"}
    return {
        field: row[field] if field in text_fields else _json_value(row[field])
        for field in ALL_TREE_FIELDS
    }


def _json_value(value: str) -> object:
    if value == "":
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value