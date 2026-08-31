"""Property and edge-case checks for deterministic progression resolution."""

from __future__ import annotations

import copy
import json
import os
from decimal import Decimal
from pathlib import Path

import pytest

from last_asylum_doctor.progression.resolver import (
    ProgressionCycleError,
    ProgressionGraph,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = Path(
    os.environ.get("PROBE_RESEARCH_DATA_ROOT", REPOSITORY_ROOT / "data" / "research")
)


def _load(name: str, *, all_trees: bool = False) -> dict[str, object]:
    root = RESEARCH_ROOT / "all" if all_trees else RESEARCH_ROOT
    return json.loads((root / name).read_text(encoding="utf-8"))


def _commando_graph() -> ProgressionGraph:
    return ProgressionGraph.from_documents(
        _load("research_nodes.json"),
        _load("research_upgrade_costs.json"),
        _load("research_prerequisites.json"),
    )


def _current_levels(state_document: dict[str, object]) -> dict[str, int]:
    states = state_document["states"]
    assert isinstance(states, list)
    return {state["node_id"]: state["current_level"] for state in states}


def _minimal_cost(node_id: str, level: int) -> dict[str, object]:
    return {
        "cost_id": f"{node_id}:{level:02d}",
        "node_id": node_id,
        "level": level,
        "timber_m": 0.0,
        "grain_m": 0.0,
        "herbs_m": 0.0,
        "study_scrolls": 1,
        "raw_duration": "1m",
        "raw_duration_seconds": 60,
        "normalized_minutes": 1,
        "might_gain": 1,
    }


def test_resolver_commando_full_scenario() -> None:
    graph = _commando_graph()
    state = _load("research_user_state.json")

    path = graph.resolve_target_path("11023", 1, state)

    assert len(path) == 116
    assert path[-1].node_id == "11023"
    assert path[-1].level == 1
    assert {(step.node_id, step.level) for step in path} == {
        (delta["node_id"], delta["level"])
        for delta in state["target_deltas"]
    }


def test_resolver_minimal_dependency_closure() -> None:
    graph = _commando_graph()
    state = _load("research_user_state.json")
    current_levels = _current_levels(state)

    path = graph.resolve_target_path("11023", 1, current_levels)

    assert len(path) == 60
    assert path[-1].node_id == "11023"
    assert path[-1].level == 1
    assert {step.node_id for step in path} == {
        "11010",
        "11011",
        "11012",
        "11013",
        "11014",
        "11015",
        "11016",
        "11017",
        "11018",
        "11019",
        "11020",
        "11021",
        "11022",
        "11023",
    }


def test_resolver_missing_prerequisites_detection() -> None:
    graph = _commando_graph()
    state = _load("research_user_state.json")
    current_levels = _current_levels(state)

    missing = graph.find_missing_prerequisites("11023", 1, current_levels)

    assert len(missing) == 1
    assert missing[0].rule_id == "prerequisite-18"
    assert missing[0].required_node_id == "11022"
    assert missing[0].required_level == 10
    assert missing[0].current_level == 0


def test_resolver_cycle_rejection() -> None:
    nodes = [
        {"node_id": "1", "branch": "Test", "name": "A", "max_level": 1},
        {"node_id": "2", "branch": "Test", "name": "B", "max_level": 1},
    ]
    costs = [_minimal_cost("1", 1), _minimal_cost("2", 1)]
    prerequisites = [
        {
            "rule_id": "a-requires-b",
            "target_node_id": "1",
            "target_level": 1,
            "required_node_id": "2",
            "required_level": 1,
        },
        {
            "rule_id": "b-requires-a",
            "target_node_id": "2",
            "target_level": 1,
            "required_node_id": "1",
            "required_level": 1,
        },
    ]

    with pytest.raises(ProgressionCycleError):
        ProgressionGraph(nodes, costs, prerequisites)


def test_resolver_zero_cost_trees() -> None:
    nodes = _load("research_nodes.json", all_trees=True)["records"]
    costs = _load("research_upgrade_costs.json", all_trees=True)["records"]
    assert isinstance(nodes, list)
    assert isinstance(costs, list)
    graph = ProgressionGraph(nodes, costs, [])
    node_by_branch = {
        node["branch"]: node for node in nodes if node["branch"] in {
            "Caravan Transport",
            "Alliance Duel",
        }
    }
    current_levels = {node["node_id"]: 0 for node in node_by_branch.values()}
    path = tuple(
        step
        for node in node_by_branch.values()
        for step in graph.resolve_target_path(
            node["node_id"], node["max_level"], current_levels
        )
    )

    totals = graph.calculate_path_totals(path)

    assert {node["node_id"] for node in node_by_branch.values()} == {
        step.node_id for step in path
    }
    assert totals.timber_m == Decimal("0")
    assert totals.grain_m == Decimal("0")
    assert totals.herbs_m == Decimal("0")
    assert totals.study_scrolls > 0
    assert totals.normalized_minutes > 0


def test_resolver_state_immutability() -> None:
    graph = _commando_graph()
    state = _load("research_user_state.json")
    original = copy.deepcopy(state)

    graph.resolve_target_path("11023", 1, state)
    graph.find_missing_prerequisites("11023", 1, state)

    assert state == original
