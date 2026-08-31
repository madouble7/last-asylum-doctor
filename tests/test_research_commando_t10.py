"""Regression checks for the Commando T10 research data export."""

from __future__ import annotations

import json
import subprocess
from decimal import Decimal
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = REPOSITORY_ROOT / "data" / "research"
CANONICAL_COMMIT = "7a64af4857920cfded6a09b180160c678cb5bab6"

NODE_FILE = "research_nodes.json"
COST_FILE = "research_upgrade_costs.json"
STATE_FILE = "research_user_state.json"
PREREQUISITE_FILE = "research_prerequisites.json"

NODE_ROOT_KEYS = {
    "schema_version",
    "dataset",
    "source_corpus",
    "source_site",
    "source_generated_at",
    "record_count",
    "records",
}
NODE_KEYS = {
    "node_id",
    "branch",
    "source_branch",
    "slug",
    "name",
    "max_level",
    "source_url",
    "retrieved_at",
}
COST_ROOT_KEYS = {
    "schema_version",
    "dataset",
    "source_corpus",
    "source_site",
    "source_generated_at",
    "units",
    "duration_normalization",
    "record_count",
    "records",
}
COST_KEYS = {
    "cost_id",
    "node_id",
    "level",
    "timber_m",
    "grain_m",
    "herbs_m",
    "study_scrolls",
    "raw_duration",
    "raw_duration_seconds",
    "normalized_minutes",
    "might_gain",
    "source_record_id",
    "source_url",
    "retrieved_at",
}
STATE_ROOT_KEYS = {
    "schema_version",
    "dataset",
    "source_corpus",
    "source_site",
    "source_generated_at",
    "account_scope",
    "state_labels",
    "state_record_count",
    "target_delta_count",
    "states",
    "target_deltas",
}
STATE_KEYS = {
    "node_id",
    "current_level",
    "target_level",
    "state_label",
    "account_scope",
}
DELTA_KEYS = {
    "delta_id",
    "node_id",
    "level",
    "current_level",
    "target_level",
    "state_label",
    "account_scope",
}
PREREQUISITE_ROOT_KEYS = {
    "schema_version",
    "dataset",
    "source_corpus",
    "source_site",
    "source_generated_at",
    "evidence_status",
    "source_note",
    "reported_compact_rule_count",
    "record_count",
    "records",
}
PREREQUISITE_KEYS = {
    "rule_id",
    "target_node_id",
    "target_level",
    "required_node_id",
    "required_level",
}


def _load_json(filename: str) -> dict[str, object]:
    """Load the worktree fixture, or the requested canonical Git fixture."""

    path = RESEARCH_ROOT / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raw = subprocess.check_output(
        ["git", "show", f"{CANONICAL_COMMIT}:data/research/{filename}"],
        cwd=REPOSITORY_ROOT,
    )
    return json.loads(raw)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _assert_root(
    payload: dict[str, object],
    required_keys: set[str],
    record_key: str,
    count_key: str = "record_count",
) -> list[dict[str, object]]:
    assert required_keys <= payload.keys()
    assert _is_int(payload["schema_version"])
    assert isinstance(payload["dataset"], str)
    assert isinstance(payload["source_corpus"], str)
    assert isinstance(payload["source_site"], str)
    assert isinstance(payload["source_generated_at"], str)
    assert _is_int(payload[count_key])
    records = payload[record_key]
    assert isinstance(records, list)
    assert payload[count_key] == len(records)
    assert all(isinstance(record, dict) for record in records)
    return records


def _assert_string_fields(record: dict[str, object], keys: set[str]) -> None:
    for key in keys:
        assert key in record
        assert isinstance(record[key], str)


def _assert_integer_fields(record: dict[str, object], keys: set[str]) -> None:
    for key in keys:
        assert key in record
        assert _is_int(record[key])


def test_research_nodes_schema_and_count() -> None:
    payload = _load_json(NODE_FILE)
    records = _assert_root(payload, NODE_ROOT_KEYS, "records")
    assert len(records) == 23
    assert [record["node_id"] for record in records] == [
        str(node_id) for node_id in range(11001, 11024)
    ]

    for record in records:
        _assert_string_fields(
            record,
            {
                "node_id",
                "branch",
                "source_branch",
                "slug",
                "name",
                "source_url",
                "retrieved_at",
            },
        )
        assert _is_int(record["max_level"])
        assert record["max_level"] > 0


def test_research_upgrade_costs_count_and_units() -> None:
    nodes = _load_json(NODE_FILE)["records"]
    costs_payload = _load_json(COST_FILE)
    records = _assert_root(costs_payload, COST_ROOT_KEYS, "records")
    assert len(records) == 221

    units = costs_payload["units"]
    assert isinstance(units, dict)
    assert set(units) == {
        "timber_m",
        "grain_m",
        "herbs_m",
        "study_scrolls",
        "normalized_minutes",
    }
    assert all(isinstance(key, str) for key in units)
    assert all(isinstance(value, str) for value in units.values())
    assert isinstance(costs_payload["duration_normalization"], str)

    node_ids = {record["node_id"] for record in nodes}
    for record in records:
        _assert_string_fields(
            record,
            {"cost_id", "node_id", "raw_duration", "source_url", "retrieved_at"},
        )
        _assert_integer_fields(
            record,
            {
                "level",
                "study_scrolls",
                "raw_duration_seconds",
                "normalized_minutes",
                "might_gain",
                "source_record_id",
            },
        )
        assert record["node_id"] in node_ids
        assert record["study_scrolls"] > 0
        assert record["normalized_minutes"] > 0
        for key in ("timber_m", "grain_m", "herbs_m"):
            assert isinstance(record[key], (int, float))
            assert not isinstance(record[key], bool)
            assert record[key] > 0


def test_research_user_transition_totals() -> None:
    state_payload = _load_json(STATE_FILE)
    states = _assert_root(
        state_payload, STATE_ROOT_KEYS, "states", count_key="state_record_count"
    )
    deltas = state_payload["target_deltas"]
    assert isinstance(deltas, list)
    assert isinstance(state_payload["account_scope"], str)
    state_labels = state_payload["state_labels"]
    assert isinstance(state_labels, list)
    assert all(isinstance(label, str) for label in state_labels)
    assert _is_int(state_payload["target_delta_count"])
    assert state_payload["state_record_count"] == len(states) == 23
    assert state_payload["target_delta_count"] == len(deltas) == 116

    for record in states:
        assert isinstance(record, dict)
        _assert_string_fields(record, {"node_id", "state_label", "account_scope"})
        _assert_integer_fields(record, {"current_level", "target_level"})
    for record in deltas:
        assert isinstance(record, dict)
        _assert_string_fields(
            record, {"delta_id", "node_id", "state_label", "account_scope"}
        )
        _assert_integer_fields(record, {"level", "current_level", "target_level"})

    costs = _load_json(COST_FILE)["records"]
    assert isinstance(costs, list)
    costs_by_level = {(row["node_id"], row["level"]): row for row in costs}
    transition_costs = []
    for delta in deltas:
        key = (delta["node_id"], delta["level"])
        assert key in costs_by_level
        transition_costs.append(costs_by_level[key])

    assert sum(Decimal(str(row["timber_m"])) for row in transition_costs) == Decimal(
        "4687.215"
    )
    assert sum(Decimal(str(row["grain_m"])) for row in transition_costs) == Decimal(
        "4687.215"
    )
    assert sum(Decimal(str(row["herbs_m"])) for row in transition_costs) == Decimal(
        "14058.618"
    )
    assert sum(row["study_scrolls"] for row in transition_costs) == 138120
    assert sum(row["normalized_minutes"] for row in transition_costs) == 1555117


def test_research_prerequisites_acyclic() -> None:
    nodes_payload = _load_json(NODE_FILE)
    node_records = _assert_root(nodes_payload, NODE_ROOT_KEYS, "records")
    node_ids = {record["node_id"] for record in node_records}
    payload = _load_json(PREREQUISITE_FILE)
    records = _assert_root(payload, PREREQUISITE_ROOT_KEYS, "records")
    assert len(records) == 18
    assert isinstance(payload["evidence_status"], str)
    assert isinstance(payload["source_note"], str)
    assert _is_int(payload["reported_compact_rule_count"])

    graph = {node_id: set() for node_id in node_ids}
    indegree = dict.fromkeys(node_ids, 0)
    for record in records:
        _assert_string_fields(record, {"rule_id", "target_node_id", "required_node_id"})
        _assert_integer_fields(record, {"target_level", "required_level"})
        required = record["required_node_id"]
        target = record["target_node_id"]
        assert required in node_ids
        assert target in node_ids
        if target not in graph[required]:
            graph[required].add(target)
            indegree[target] += 1

    ready = [node_id for node_id, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        current = ready.pop()
        visited += 1
        for successor in graph[current]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
    assert visited == len(node_ids), "research prerequisite graph contains a cycle"

    gates = [record for record in records if record["target_node_id"] == "11023"]
    assert gates == [
        {
            "rule_id": "prerequisite-18",
            "target_node_id": "11023",
            "target_level": 1,
            "required_node_id": "11022",
            "required_level": 10,
        }
    ]
