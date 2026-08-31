"""Regression checks for the complete normalized research corpus."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = REPOSITORY_ROOT / "data" / "research" / "all"
CANONICAL_REF = "origin/main"

NODE_FILE = "research_nodes.json"
COST_FILE = "research_upgrade_costs.json"
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
    path = RESEARCH_ROOT / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raw = subprocess.check_output(
        ["git", "show", f"{CANONICAL_REF}:data/research/all/{filename}"],
        cwd=REPOSITORY_ROOT,
    )
    return json.loads(raw)


def _load_optional_json(filename: str) -> dict[str, object] | None:
    path = RESEARCH_ROOT / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{CANONICAL_REF}:data/research/all/{filename}"],
        cwd=REPOSITORY_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode:
        return None
    raw = subprocess.check_output(
        ["git", "show", f"{CANONICAL_REF}:data/research/all/{filename}"],
        cwd=REPOSITORY_ROOT,
    )
    return json.loads(raw)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _assert_root(
    payload: dict[str, object], required_keys: set[str]
) -> list[dict[str, object]]:
    assert required_keys <= payload.keys()
    assert _is_int(payload["schema_version"])
    for key in ("dataset", "source_corpus", "source_site", "source_generated_at"):
        assert isinstance(payload[key], str)
    assert _is_int(payload["record_count"])
    records = payload["records"]
    assert isinstance(records, list)
    assert payload["record_count"] == len(records)
    assert all(isinstance(record, dict) for record in records)
    return records


def _assert_string_fields(record: dict[str, object], keys: set[str]) -> None:
    assert keys <= record.keys()
    assert all(isinstance(record[key], str) for key in keys)


def _assert_integer_fields(record: dict[str, object], keys: set[str]) -> None:
    assert keys <= record.keys()
    assert all(_is_int(record[key]) for key in keys)


def test_all_trees_node_count_and_uniqueness() -> None:
    payload = _load_json(NODE_FILE)
    records = _assert_root(payload, NODE_ROOT_KEYS)
    assert len(records) == 348

    node_ids = [record["node_id"] for record in records]
    assert len(set(node_ids)) == 348
    assert all(
        isinstance(node_id, str) and re.fullmatch(r"\d+", node_id)
        for node_id in node_ids
    )
    assert len({record["branch"] for record in records}) == 18

    for record in records:
        _assert_string_fields(record, NODE_KEYS - {"max_level"})
        assert _is_int(record["max_level"])
        assert record["max_level"] > 0


def test_all_trees_cost_rows_and_units() -> None:
    nodes = _load_json(NODE_FILE)["records"]
    costs_payload = _load_json(COST_FILE)
    records = _assert_root(costs_payload, COST_ROOT_KEYS)
    assert len(records) == 2287

    units = costs_payload["units"]
    assert units == {
        "timber_m": "millions",
        "grain_m": "millions",
        "herbs_m": "millions",
        "study_scrolls": "integer_count",
        "normalized_minutes": "integer_minutes",
    }
    assert isinstance(costs_payload["duration_normalization"], str)

    node_by_id = {record["node_id"]: record for record in nodes}
    cost_ids: set[str] = set()
    levels_by_node: dict[str, set[int]] = {node_id: set() for node_id in node_by_id}
    for record in records:
        _assert_string_fields(
            record,
            COST_KEYS
            - {
                "level",
                "timber_m",
                "grain_m",
                "herbs_m",
                "study_scrolls",
                "raw_duration_seconds",
                "normalized_minutes",
                "might_gain",
                "source_record_id",
            },
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
        assert record["node_id"] in node_by_id
        assert record["cost_id"] not in cost_ids
        cost_ids.add(record["cost_id"])
        level = record["level"]
        assert 1 <= level <= node_by_id[record["node_id"]]["max_level"]
        levels_by_node[record["node_id"]].add(level)
        for key in ("timber_m", "grain_m", "herbs_m"):
            assert type(record[key]) is float
            assert record[key] >= 0.0
        assert record["study_scrolls"] >= 0
        assert record["normalized_minutes"] >= 0

    for node_id, node in node_by_id.items():
        assert levels_by_node[node_id] == set(range(1, node["max_level"] + 1))


def test_zero_resource_trees() -> None:
    nodes = _load_json(NODE_FILE)["records"]
    costs = _load_json(COST_FILE)["records"]
    branches = {record["node_id"]: record["branch"] for record in nodes}

    for branch in ("Caravan Transport", "Alliance Duel"):
        rows = [row for row in costs if branches[row["node_id"]] == branch]
        assert rows
        for row in rows:
            assert all(row[key] == 0.0 for key in ("timber_m", "grain_m", "herbs_m"))
            assert _is_int(row["study_scrolls"]) and row["study_scrolls"] >= 0
            assert _is_int(row["normalized_minutes"]) and row["normalized_minutes"] >= 0


def test_prerequisite_graph_acyclic() -> None:
    payload = _load_optional_json(PREREQUISITE_FILE)
    if payload is None:
        pytest.skip("no all-tree prerequisite dataset has been generated")

    nodes = _load_json(NODE_FILE)["records"]
    node_ids = {record["node_id"] for record in nodes}
    records = _assert_root(payload, PREREQUISITE_ROOT_KEYS)
    graph = {node_id: set() for node_id in node_ids}
    indegree = dict.fromkeys(node_ids, 0)

    for record in records:
        _assert_string_fields(
            record, PREREQUISITE_KEYS - {"target_level", "required_level"}
        )
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
