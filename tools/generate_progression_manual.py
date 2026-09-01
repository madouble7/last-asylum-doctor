"""Generate a factual, calculation-driven research progression manual.

The command is intentionally a read-mostly adapter around the canonical
progression resolver and deficit calculator.  It does not change canonical
datasets or account state; only the requested Markdown output is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from last_asylum_doctor.progression import (  # noqa: E402
    InventoryState,
    PathTotals,
    ProgressionGraph,
    calculate_deficit,
    estimate_timeline,
)

ALL_RESEARCH_ROOT = REPOSITORY_ROOT / "data" / "research" / "all"
DEFAULT_STATE = REPOSITORY_ROOT / "data" / "research" / "research_user_state.json"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "docs" / "progression_manual_s283_commando_t10.md"
INVENTORY_FIELDS = (
    "timber_m",
    "grain_m",
    "herbs_m",
    "study_scrolls",
    "universal_speedups_minutes",
    "research_speedups_minutes",
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _state_current_level(document: Mapping[str, Any], node_id: str) -> int:
    states = document.get("states")
    if not isinstance(states, Sequence) or isinstance(states, (str, bytes)):
        raise ValueError("user state must contain a states array")
    for state in states:
        if isinstance(state, Mapping) and str(state.get("node_id")) == node_id:
            value = state.get("current_level")
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"current_level for {node_id} must be an integer")
            return value
    raise ValueError(f"user state has no current level for target node {node_id}")


def _state_for_resolution(
    document: Mapping[str, Any], node_records: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Any], int]:
    """Fill absent node levels with explicit zero scenario values.

    The shipped S283 snapshot is a Commando slice, while the all-tree graph can
    expose a prerequisite in another branch (for example Top Rewards).  The
    resolver requires a level for every referenced prerequisite.  Adding a
    clearly labelled zero scenario lets the CLI render the closure without
    promoting an unobserved level to an account fact.
    """

    states = document.get("states")
    if not isinstance(states, list):
        raise ValueError("user state must contain a states array")
    present = {
        str(item.get("node_id"))
        for item in states
        if isinstance(item, Mapping) and item.get("node_id") is not None
    }
    missing = [
        str(record["node_id"])
        for record in node_records
        if str(record["node_id"]) not in present
    ]
    if not missing:
        return dict(document), 0
    resolved = dict(document)
    resolved["states"] = [*states]
    resolved["states"].extend(
        {
            "node_id": node_id,
            "current_level": 0,
            "state_label": "DEFAULT_ZERO_SCENARIO",
        }
        for node_id in missing
    )
    return resolved, len(missing)


def _inventory_from_file(path: Path | None) -> tuple[InventoryState, str]:
    if path is None:
        return InventoryState(), "DEFAULT_ZERO_SCENARIO (not observed inventory)"
    document = _load_json(path)
    values = document.get("inventory", document)
    if not isinstance(values, Mapping):
        raise ValueError(f"{path} inventory must be an object")
    unknown = sorted(set(values) - set(INVENTORY_FIELDS))
    if unknown:
        raise ValueError(f"{path} contains unknown inventory fields: {unknown}")
    kwargs: dict[str, Any] = {}
    for field in INVENTORY_FIELDS:
        if field not in values:
            continue
        value = values[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{path} inventory.{field} must be numeric")
        kwargs[field] = float(value) if field.endswith("_m") else int(value)
    return InventoryState(**kwargs), f"EXPLICIT_FILE {path} (sha256:{_sha256(path)})"


def _fmt(value: Decimal | float | int) -> str:
    if isinstance(value, Decimal):
        text = format(value, "f")
    elif isinstance(value, float):
        text = f"{value:.3f}"
    else:
        text = str(value)
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _inventory_text(inventory: InventoryState) -> str:
    speedups = (
        inventory.universal_speedups_minutes
        + inventory.research_speedups_minutes
    )
    return (
        f"timber {inventory.timber_m:g}M, grain {inventory.grain_m:g}M, "
        f"herbs {inventory.herbs_m:g}M, scrolls {inventory.study_scrolls}, "
        f"speedups {speedups} min"
    )


def _node_records(path: Path) -> list[dict[str, Any]]:
    records = _load_json(path).get("records")
    if not isinstance(records, list) or not all(
        isinstance(item, dict) for item in records
    ):
        raise ValueError(f"{path} records must be an array of objects")
    return records


def _totals_row(totals: PathTotals, inventory: InventoryState) -> str:
    deficit = calculate_deficit(totals, inventory)
    return (
        f"| {_fmt(totals.timber_m)} | {_fmt(totals.grain_m)} | "
        f"{_fmt(totals.herbs_m)} | {totals.study_scrolls} | "
        f"{totals.normalized_minutes} | {_fmt(deficit.timber_m)} | "
        f"{_fmt(deficit.grain_m)} | {_fmt(deficit.herbs_m)} | "
        f"{deficit.study_scrolls} | {deficit.speedup_minutes_deficit} |"
    )


def _render_manual(
    *,
    graph: ProgressionGraph,
    path_steps: tuple[Any, ...],
    node_by_id: Mapping[str, Mapping[str, Any]],
    state: Mapping[str, Any],
    state_path: Path,
    inventory: InventoryState,
    inventory_source: str,
    target_node_id: str,
    target_level: int,
    daily_scrolls: int,
    daily_speedups: int,
    research_speed: float,
    source_paths: Sequence[Path],
    defaulted_state_nodes: int,
) -> str:
    target = node_by_id[target_node_id]
    current_level = _state_current_level(state, target_node_id)
    totals = graph.calculate_path_totals(path_steps)
    deficit = calculate_deficit(totals, inventory)
    timeline = estimate_timeline(
        deficit,
        daily_scroll_income=daily_scrolls,
        daily_speedup_income_minutes=daily_speedups,
        research_speed_pct=research_speed,
    )

    grouped: OrderedDict[str, list[Any]] = OrderedDict()
    for step in path_steps:
        branch = str(node_by_id[step.node_id]["branch"])
        grouped.setdefault(branch, []).append(step)

    rows: list[str] = []
    cumulative: list[Any] = []
    for branch, steps in grouped.items():
        cumulative.extend(steps)
        branch_totals = graph.calculate_path_totals(cumulative)
        rows.append(
            f"| {branch} | {len(steps)} | "
            f"{_totals_row(branch_totals, inventory)[2:]}"
        )
    branch_rows = "\n".join(rows) if rows else (
        "| — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |"
    )
    scroll_horizon = (
        "unbounded"
        if math.isinf(timeline.scroll_bottleneck_days)
        else f"{timeline.scroll_bottleneck_days:.2f} days"
    )

    path_lines = []
    for index, step in enumerate(path_steps, start=1):
        node = node_by_id[step.node_id]
        path_lines.append(
            f"{index}. `{step.node_id}` — {node['name']} level {step.level} "
            f"(`[KNOWN]` cost row `{step.cost_id}`)"
        )
    path_text = "\n".join(path_lines) if path_lines else "No upgrades required."
    event_status = "UNKNOWN (no event points or multiplier supplied)"
    source_hashes = ", ".join(f"`{p.name}` `{_sha256(p)}`" for p in source_paths)
    roadmap_rows = "\n".join(
        (
            "| Foundation | Development and Economy capacity | "
            "Prerequisites already completed or surfaced before the target | "
            "`[KNOWN]` only for loaded node/cost facts |",
            "| Core | Full Development, Hero, and squad efficiency | "
            "Fund and shorten the military transition | "
            "MES requires verified effects; absent effects remain `[UNKNOWN]` |",
            "| Gateway | Commando/Elite Troop and tactical branches | "
            "Resolve explicit cross-tree edges before advanced branches | "
            "Public percentage/building gates may remain `[UNKNOWN]` |",
            "| Unlock | Target node and final level transition | "
            "Execute the requested "
            f"`{target_node_id}:{target_level}` endpoint | `[CALCULATED]` path, "
            "not a universal strategy |",
        )
    )
    totals_header = (
        "| Timber (M) | Grain (M) | Herbs (M) | Study Scrolls | Time (min) | "
        "Timber deficit (M) | Grain deficit (M) | Herbs deficit (M) | "
        "Scroll deficit | Speedup deficit (min) |"
    )
    branch_header = (
        "| Branch | Steps | Timber (M) | Grain (M) | Herbs (M) | Scrolls | "
        "Time (min) | Timber deficit | Grain deficit | Herbs deficit | "
        "Scroll deficit | Speedup deficit |"
    )
    return f"""# Doctor's Progression Manual — S283

## Executive Dashboard & Target Definition

- **Account:** `{state.get('account_scope', 'UNKNOWN')}` (`[USER-ENTERED]`)
- **Target:** `{target_node_id}` — {target['name']} level {target_level}
  (`[CALCULATOR_TARGET]`; current level {current_level})
- **Branch:** {target['branch']}
- **Resolved steps:** {len(path_steps)}
- **Objective:** complete the requested target path with explicit prerequisite closure.
- **Inventory scenario:** {_inventory_text(inventory)} (`{inventory_source}`)
- **Timeline inputs:** {daily_scrolls} scrolls/day, {daily_speedups} speedup min/day,
  {research_speed:g}% research speed.
- **Unobserved prerequisite levels:** {defaulted_state_nodes} node(s) rendered as
  explicit zero scenarios (`[UNKNOWN]` account state), because the supplied
  snapshot is not a complete 18-tree capture.

The resolver output is a Layer-2 calculation over the canonical facts. It is not
a claim that unmodeled Institute, Sanctuary, event, or account gates are absent.

## Phased Roadmap (Foundation → Core → Gateway → Unlock)

| Phase | Focus | This path's role | Evidence boundary |
| --- | --- | --- | --- |
{roadmap_rows}

Resolved action sequence:

{path_text}

## Cumulative Resource & Scroll Deficit Tables

### Full path totals

{totals_header}
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{_totals_row(totals, inventory)}

### Cumulative branch closure

{branch_header}
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{branch_rows}

## Event Timing & Alliance Duel Research Day Action Playbook

### Deterministic projection

- Natural timer horizon: **{timeline.natural_days:.2f} days**.
- Accelerated timer horizon: **{timeline.accelerated_days:.2f} days**.
- Study Scroll horizon: **{scroll_horizon}** under the supplied daily income.
- Limiting factor: `{timeline.limiting_factor}`.
- Event value: `{event_status}`.

### Marginal Efficiency Score (MES)

```text
B_i = sum(weight_k * verified_effect_delta_k / reference_k)
C_i = resource_weight * normalized_resource_cost
    + scroll_weight * scrolls / scroll_budget
    + time_weight * minutes / time_horizon
MES_i = B_i / (epsilon + C_i)
MES_i,event = (B_i + event_weight * verified_event_value_i)
             / (epsilon + C_i)
```

This run renders MES as **UNKNOWN** because the supplied corpus has no complete
verified effect vector, objective weights, or Alliance Duel point table. Source
Might is retained as a fact field and is not silently substituted for benefit.

### Research Day actions

1. Confirm the current S283 event day, league/bracket, multiplier, and point table.
2. Enumerate only eligible next-level actions and retain prerequisite closure.
3. Compare ordinary MES with event-adjusted MES only when event values are
   verified; no event points are inferred from Might or duration.
4. Protect the stated Study Scroll reserve and record any strategy override.
5. If event facts are stale or unavailable, use ordinary MES and label the event
   branch `[UNVERIFIED]`.

The canonical effect fields do not provide a complete normalized benefit vector
for this run, so MES is **UNKNOWN**, not a zero score. The playbook therefore
reports costs and timing without pretending to rank effects.

## Evidence Classification & Data Provenance Footer

- `[KNOWN]` Fact: node identity, level bounds, canonical cost/time/scroll rows,
  and loaded prerequisite records.
- `[CALCULATED]` Calculation: resolved path, cumulative totals, deficits, and
  timeline projection from explicit CLI parameters.
- `[STRATEGY]` Strategy: Research Day checklist and reserve guidance derived from
  `docs/progression_manual_spec.md`; it is not a game fact.
- `[USER-ENTERED]` Account state: `{state_path}` (`sha256:{_sha256(state_path)}`).
- `[UNKNOWN]` Missing effects, event points/multipliers, building gates, income
  rates, and any server/build scope not present in the supplied inputs.

Canonical source hashes: {source_hashes}.

Generated by `tools/generate_progression_manual.py`; generation does not mutate
canonical datasets or account state.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-node", default="11023")
    parser.add_argument("--target-level", type=int, default=1)
    parser.add_argument("--user-state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--inventory-file", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--daily-scrolls", type=int, default=0)
    parser.add_argument("--daily-speedups", type=int, default=0)
    parser.add_argument("--research-speed", type=float, default=0.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.target_level < 1:
        parser.error("--target-level must be positive")
    if arguments.daily_scrolls < 0 or arguments.daily_speedups < 0:
        parser.error("daily income parameters must be non-negative")
    if arguments.research_speed < 0:
        parser.error("--research-speed must be non-negative")

    nodes_path = ALL_RESEARCH_ROOT / "research_nodes.json"
    costs_path = ALL_RESEARCH_ROOT / "research_upgrade_costs.json"
    prerequisites_path = ALL_RESEARCH_ROOT / "research_prerequisites.json"
    try:
        protected_paths = {
            path.resolve()
            for path in (
                nodes_path,
                costs_path,
                prerequisites_path,
                arguments.user_state,
            )
        }
        if arguments.output.resolve() in protected_paths:
            raise ValueError("--output must not overwrite a canonical input file")
        node_records = _node_records(nodes_path)
        node_by_id = {str(record["node_id"]): record for record in node_records}
        state = _load_json(arguments.user_state)
        resolution_state, defaulted_state_nodes = _state_for_resolution(
            state, node_records
        )
        inventory, inventory_source = _inventory_from_file(arguments.inventory_file)
        graph = ProgressionGraph.from_json_files(
            nodes_path, costs_path, prerequisites_path
        )
        path_steps = graph.resolve_target_path(
            arguments.target_node, arguments.target_level, resolution_state
        )
        markdown = _render_manual(
            graph=graph,
            path_steps=path_steps,
            node_by_id=node_by_id,
            state=state,
            state_path=arguments.user_state,
            inventory=inventory,
            inventory_source=inventory_source,
            target_node_id=str(arguments.target_node),
            target_level=arguments.target_level,
            daily_scrolls=arguments.daily_scrolls,
            daily_speedups=arguments.daily_speedups,
            research_speed=arguments.research_speed,
            source_paths=(nodes_path, costs_path, prerequisites_path),
            defaulted_state_nodes=defaulted_state_nodes,
        )
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(markdown, encoding="utf-8")
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(f"Generated {arguments.output} ({len(path_steps)} steps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
