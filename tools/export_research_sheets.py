"""Export canonical research data into spreadsheet-ready CSV and JSON bundles."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from last_asylum_doctor.progression import (
    InventoryState,
    PathDeficit,
    PathTotals,
    ProgressionDataError,
    ProgressionGraph,
    TimelineProjection,
    calculate_deficit,
    estimate_timeline,
)

DEFAULT_RESEARCH_ROOT = Path("data/research")
DEFAULT_OUTPUT_DIR = Path("data/exports/research-sheets")

ALL_TREE_FIELDS = (
    "Node ID",
    "Branch",
    "Name",
    "Max Level",
    "Cost Level",
    "Timber M",
    "Grain M",
    "Herbs M",
    "Scrolls",
    "Minutes",
    "Might",
)
TARGET_PATH_FIELDS = (
    "Step",
    "Node ID",
    "Branch",
    "Name",
    "Max Level",
    "Cost Level",
    "Current Level",
    "Target Level",
    "Timber M",
    "Grain M",
    "Herbs M",
    "Scrolls",
    "Minutes",
    "Might",
    "Cumulative Timber M",
    "Cumulative Grain M",
    "Cumulative Herbs M",
    "Cumulative Scrolls",
    "Cumulative Minutes",
    "Cumulative Might",
)
INVENTORY_FIELDS = (
    "timber_m",
    "grain_m",
    "herbs_m",
    "study_scrolls",
    "universal_speedups_minutes",
    "research_speedups_minutes",
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run one research-sheet export and print the generated file paths."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.all_trees:
            outputs = export_all_trees(
                research_root=arguments.research_root,
                output_dir=arguments.output_dir,
            )
        else:
            target_node_id, target_level = _parse_target_path(
                arguments.target_path, parser
            )
            outputs = export_target_path(
                target_node_id,
                target_level,
                research_root=arguments.research_root,
                output_dir=arguments.output_dir,
                state_file=arguments.state_file,
                inventory_file=arguments.inventory_file,
                daily_scroll_income=arguments.daily_scroll_income,
                daily_speedup_income_minutes=arguments.daily_speedup_income_minutes,
                research_speed_pct=arguments.research_speed_pct,
            )
    except (
        OSError,
        ProgressionDataError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(f"Research export failed: {error}")
        return 1

    for path in outputs:
        print(path)
    return 0


def _parse_target_path(
    target_path: list[str] | None, parser: argparse.ArgumentParser
) -> tuple[str, int]:
    if target_path is None:
        parser.error("--target-path is required")
    try:
        level = int(target_path[1])
    except ValueError as error:
        parser.error(f"target level must be an integer: {error}")
    return target_path[0], level


def export_all_trees(
    *,
    research_root: Path = DEFAULT_RESEARCH_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[Path, Path]:
    """Export every canonical node-level cost row as a flat table."""

    all_root = research_root / "all"
    nodes_document = _load_json(all_root / "research_nodes.json")
    costs_document = _load_json(all_root / "research_upgrade_costs.json")
    nodes = _records(nodes_document, "research_nodes")
    costs = _records(costs_document, "research_upgrade_costs")
    nodes_by_id = {str(node["node_id"]): node for node in nodes}
    records = []
    for cost in costs:
        node_id = str(cost["node_id"])
        try:
            node = nodes_by_id[node_id]
        except KeyError as error:
            raise ProgressionDataError(
                f"cost references unknown node {node_id}"
            ) from error
        records.append(
            {
                "Node ID": node_id,
                "Branch": node["branch"],
                "Name": node["name"],
                "Max Level": node["max_level"],
                "Cost Level": cost["level"],
                "Timber M": cost["timber_m"],
                "Grain M": cost["grain_m"],
                "Herbs M": cost["herbs_m"],
                "Scrolls": cost["study_scrolls"],
                "Minutes": cost["normalized_minutes"],
                "Might": cost["might_gain"],
            }
        )
    records.sort(
        key=lambda record: (_numeric_id(record["Node ID"]), record["Cost Level"])
    )
    bundle = {
        "schema_version": 1,
        "export_type": "all_research_trees",
        "source_files": {
            "nodes": _display_path(all_root / "research_nodes.json"),
            "costs": _display_path(all_root / "research_upgrade_costs.json"),
        },
        "tree_count": len({record["Branch"] for record in records}),
        "record_count": len(records),
        "columns": list(ALL_TREE_FIELDS),
        "records": records,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "research_all_trees.csv"
    json_path = output_dir / "research_all_trees.json"
    _write_csv(csv_path, ALL_TREE_FIELDS, records)
    _write_json(json_path, bundle)
    return csv_path, json_path


def export_target_path(
    target_node_id: str,
    target_level: int,
    *,
    research_root: Path = DEFAULT_RESEARCH_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    state_file: Path | None = None,
    inventory_file: Path | None = None,
    daily_scroll_income: int = 0,
    daily_speedup_income_minutes: int = 0,
    research_speed_pct: float = 0.0,
) -> tuple[Path, Path]:
    """Export a resolved path, cumulative totals, and explicit deficits."""

    state_path = state_file or research_root / "research_user_state.json"
    nodes_path = research_root / "research_nodes.json"
    costs_path = research_root / "research_upgrade_costs.json"
    prerequisites_path = research_root / "research_prerequisites.json"
    state = _load_json(state_path)
    graph = ProgressionGraph.from_json_files(
        nodes_path, costs_path, prerequisites_path
    )
    path = graph.resolve_target_path(target_node_id, target_level, state)
    totals = graph.calculate_path_totals(path)
    inventory, inventory_source = _load_inventory(inventory_file)
    deficit = calculate_deficit(totals, inventory)
    timeline = estimate_timeline(
        deficit,
        daily_scroll_income=daily_scroll_income,
        daily_speedup_income_minutes=daily_speedup_income_minutes,
        research_speed_pct=research_speed_pct,
    )

    nodes = {
        str(record["node_id"]): record
        for record in _records(_load_json(nodes_path), "research_nodes")
    }
    current_levels = _current_levels(state)
    target_rows = _target_rows(
        path,
        nodes,
        current_levels,
        target_node_id=str(target_node_id),
        requested_level=target_level,
    )
    bundle = {
        "schema_version": 1,
        "export_type": "research_target_path",
        "target": {"node_id": str(target_node_id), "level": target_level},
        "account_scope": state.get("account_scope"),
        "source_files": {
            "nodes": _display_path(nodes_path),
            "costs": _display_path(costs_path),
            "prerequisites": _display_path(prerequisites_path),
            "state": _display_path(state_path),
        },
        "inventory_source": inventory_source,
        "inventory": _inventory_dict(inventory),
        "research_speed_pct": research_speed_pct,
        "daily_scroll_income": daily_scroll_income,
        "daily_speedup_income_minutes": daily_speedup_income_minutes,
        "step_count": len(target_rows),
        "columns": list(TARGET_PATH_FIELDS),
        "path_steps": target_rows,
        "totals": _totals_dict(totals),
        "deficit": _deficit_dict(deficit),
        "timeline": _timeline_dict(timeline),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"research_target_{target_node_id}_{target_level:02d}"
    csv_path = output_dir / f"{stem}.csv"
    json_path = output_dir / f"{stem}.json"
    _write_csv(csv_path, TARGET_PATH_FIELDS, target_rows)
    _write_json(json_path, bundle)
    return csv_path, json_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--all-trees",
        action="store_true",
        help="export the complete 18-tree node-level cost table",
    )
    mode.add_argument(
        "--target-path",
        nargs=2,
        metavar=("NODE_ID", "LEVEL"),
        dest="target_path",
        help="export a resolved target path and deficit bundle",
    )
    parser.add_argument(
        "--research-root", type=Path, default=DEFAULT_RESEARCH_ROOT
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--inventory-file", type=Path)
    parser.add_argument("--daily-scroll-income", type=int, default=0)
    parser.add_argument(
        "--daily-speedup-income-minutes", type=int, default=0
    )
    parser.add_argument("--research-speed-pct", type=float, default=0.0)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProgressionDataError(f"{path} must contain a JSON object")
    return value


def _records(document: Mapping[str, Any], name: str) -> list[dict[str, Any]]:
    records = document.get("records")
    if not isinstance(records, list) or any(
        not isinstance(record, dict) for record in records
    ):
        raise ProgressionDataError(f"{name}.records must be an array of objects")
    return records


def _load_inventory(path: Path | None) -> tuple[InventoryState, str]:
    if path is None:
        return (
            InventoryState(),
            "explicit_zero_scenario_defaults_not_observed_inventory",
        )
    document = _load_json(path)
    values = document.get("inventory", document)
    if not isinstance(values, dict):
        raise ProgressionDataError(f"{path} inventory must be an object")
    unknown = sorted(set(values) - set(INVENTORY_FIELDS))
    if unknown:
        raise ProgressionDataError(
            f"{path} contains unknown inventory fields: {unknown}"
        )
    return InventoryState(**values), _display_path(path)


def _current_levels(state: Mapping[str, Any]) -> dict[str, int]:
    states = state.get("states")
    if isinstance(states, list):
        return {
            str(record["node_id"]): int(record["current_level"])
            for record in states
            if isinstance(record, dict)
            and "node_id" in record
            and "current_level" in record
        }
    return {
        str(node_id): int(
            value.get("current_level", 0) if isinstance(value, dict) else value
        )
        for node_id, value in state.items()
        if node_id not in {"account_scope", "states", "target_deltas"}
    }


def _target_rows(
    path: Sequence[Any],
    nodes: Mapping[str, Mapping[str, Any]],
    current_levels: Mapping[str, int],
    *,
    target_node_id: str,
    requested_level: int,
) -> list[dict[str, Any]]:
    rows = []
    timber = Decimal(0)
    grain = Decimal(0)
    herbs = Decimal(0)
    scrolls = 0
    minutes = 0
    might = 0
    for step_number, step in enumerate(path, start=1):
        node = nodes[step.node_id]
        timber += step.cost.timber_m
        grain += step.cost.grain_m
        herbs += step.cost.herbs_m
        scrolls += step.cost.study_scrolls
        minutes += step.cost.normalized_minutes
        might += step.cost.might_gain
        rows.append(
            {
                "Step": step_number,
                "Node ID": step.node_id,
                "Branch": node["branch"],
                "Name": node["name"],
                "Max Level": node["max_level"],
                "Cost Level": step.level,
                "Current Level": current_levels.get(step.node_id),
                "Target Level": (
                    requested_level if step.node_id == target_node_id else None
                ),
                "Timber M": float(step.cost.timber_m),
                "Grain M": float(step.cost.grain_m),
                "Herbs M": float(step.cost.herbs_m),
                "Scrolls": step.cost.study_scrolls,
                "Minutes": step.cost.normalized_minutes,
                "Might": step.cost.might_gain,
                "Cumulative Timber M": float(timber),
                "Cumulative Grain M": float(grain),
                "Cumulative Herbs M": float(herbs),
                "Cumulative Scrolls": scrolls,
                "Cumulative Minutes": minutes,
                "Cumulative Might": might,
            }
        )
    return rows


def _totals_dict(totals: PathTotals) -> dict[str, Any]:
    return {
        "Timber M": float(totals.timber_m),
        "Grain M": float(totals.grain_m),
        "Herbs M": float(totals.herbs_m),
        "Scrolls": totals.study_scrolls,
        "Minutes": totals.normalized_minutes,
        "Might": totals.might_gain,
    }


def _deficit_dict(deficit: PathDeficit) -> dict[str, Any]:
    return {
        "Timber M": deficit.timber_m,
        "Grain M": deficit.grain_m,
        "Herbs M": deficit.herbs_m,
        "Scrolls": deficit.study_scrolls,
        "Raw Minutes": deficit.raw_time_minutes,
        "Speedup Minutes Deficit": deficit.speedup_minutes_deficit,
    }


def _timeline_dict(timeline: TimelineProjection) -> dict[str, Any]:
    return {
        "Natural Days": timeline.natural_days,
        "Accelerated Days": timeline.accelerated_days,
        "Scroll Bottleneck Days": (
            timeline.scroll_bottleneck_days
            if math.isfinite(timeline.scroll_bottleneck_days)
            else None
        ),
        "Scroll Bottleneck Unbounded": not math.isfinite(
            timeline.scroll_bottleneck_days
        ),
        "Limiting Factor": timeline.limiting_factor,
    }


def _inventory_dict(inventory: InventoryState) -> dict[str, Any]:
    return {field: getattr(inventory, field) for field in INVENTORY_FIELDS}


def _write_csv(
    path: Path, fields: Sequence[str], records: Sequence[Mapping[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def _write_json(path: Path, document: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def _display_path(path: Path) -> str:
    return path.as_posix()


def _numeric_id(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    raise SystemExit(main())