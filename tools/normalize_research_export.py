"""Normalize science corpus records into canonical Layer 1 research JSON.

This utility projects source-backed node and level facts into the two
canonical datasets that can be derived from ``research_corpus.json``:

* ``research_nodes.json``
* ``research_upgrade_costs.json``

It intentionally does not create prerequisite rules or player state. Those
datasets require evidence that is not present in the science corpus.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("data/processed/research_corpus.json")
DEFAULT_OUTPUT_DIR = Path("data/exports/normalized-research")

RESOURCE_KEYS = frozenset({"farms", "lumber", "herbs", "study_scroll"})
TREE_BRANCH_ALIASES = {"Elite Troop": "Commando"}
BRANCH_TREE_ALIASES = {
    branch.casefold(): tree for tree, branch in TREE_BRANCH_ALIASES.items()
}

UNITS = {
    "timber_m": "millions",
    "grain_m": "millions",
    "herbs_m": "millions",
    "study_scrolls": "integer_count",
    "normalized_minutes": "integer_minutes",
}
DURATION_NORMALIZATION = "round(time_seconds / 60) to nearest integer minute"

NODE_RECORD_FIELDS = (
    "node_id",
    "branch",
    "source_branch",
    "slug",
    "name",
    "max_level",
    "source_url",
    "retrieved_at",
)
COST_RECORD_FIELDS = (
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
)

JsonObject = dict[str, Any]


class NormalizationError(ValueError):
    """Raised when source data cannot be mapped without guessing."""


@dataclass(frozen=True)
class NodeSelection:
    """One mutually exclusive way to select corpus nodes."""

    tree: str | None = None
    branch: str | None = None
    node_ids: tuple[int, int] | None = None
    all_nodes: bool = False

    def __post_init__(self) -> None:
        modes = sum(
            value is not None for value in (self.tree, self.branch, self.node_ids)
        ) + int(self.all_nodes)
        if modes != 1:
            raise ValueError("exactly one node-selection mode is required")
        if self.node_ids is not None and self.node_ids[0] > self.node_ids[1]:
            raise ValueError("node ID range start must not exceed its end")


def load_corpus(path: Path) -> JsonObject:
    """Load a JSON corpus and require its expected top-level object shape."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise NormalizationError(f"{path}: invalid JSON: {error}") from error
    except OSError as error:
        raise NormalizationError(f"{path}: cannot read input: {error}") from error
    return dict(_mapping(value, "corpus"))


def normalize_research_export(
    corpus: Mapping[str, Any],
    *,
    selection: NodeSelection,
    dataset: str | None = None,
    source_corpus: str = "data/processed/research_corpus.json",
) -> tuple[JsonObject, JsonObject]:
    """Return canonical node and upgrade-cost documents for a selection."""

    source_site = _text(corpus.get("source_site"), "corpus.source_site")
    source_generated_at = _text(corpus.get("generated_at"), "corpus.generated_at")
    raw_nodes = _list(corpus.get("successful_nodes"), "corpus.successful_nodes")
    selected_nodes = _select_nodes(raw_nodes, selection)

    node_records: list[JsonObject] = []
    cost_records: list[JsonObject] = []
    seen_node_ids: set[str] = set()

    for raw_node in selected_nodes:
        node = _mapping(raw_node, "corpus.successful_nodes[]")
        node_id = _node_id(node.get("research_id"), "node.research_id")
        if node_id in seen_node_ids:
            raise NormalizationError(f"duplicate selected node_id: {node_id}")
        seen_node_ids.add(node_id)

        node_record, node_costs = _normalize_node(node, node_id)
        node_records.append(node_record)
        cost_records.extend(node_costs)

    if not node_records:
        raise NormalizationError("the requested selection matched no corpus nodes")

    selected_dataset = _dataset_name(dataset, node_records)
    nodes_document: JsonObject = {
        "schema_version": 1,
        "dataset": selected_dataset,
        "source_corpus": source_corpus,
        "source_site": source_site,
        "source_generated_at": source_generated_at,
        "record_count": len(node_records),
        "records": node_records,
    }
    costs_document: JsonObject = {
        "schema_version": 1,
        "dataset": selected_dataset,
        "source_corpus": source_corpus,
        "source_site": source_site,
        "source_generated_at": source_generated_at,
        "units": dict(UNITS),
        "duration_normalization": DURATION_NORMALIZATION,
        "record_count": len(cost_records),
        "records": cost_records,
    }
    validate_documents(nodes_document, costs_document)
    return nodes_document, costs_document


def validate_documents(
    nodes_document: Mapping[str, Any], costs_document: Mapping[str, Any]
) -> None:
    """Validate canonical record shapes and cross-file identities."""

    node_records = _list(nodes_document.get("records"), "nodes.records")
    cost_records = _list(costs_document.get("records"), "costs.records")
    _matching_count(nodes_document, "record_count", node_records, "nodes")
    _matching_count(costs_document, "record_count", cost_records, "costs")

    node_levels: dict[str, int] = {}
    for index, value in enumerate(node_records):
        path = f"nodes.records[{index}]"
        record = _mapping(value, path)
        _exact_fields(record, NODE_RECORD_FIELDS, path)
        node_id = _node_id(record["node_id"], f"{path}.node_id")
        if node_id in node_levels:
            raise NormalizationError(f"{path}.node_id: duplicate {node_id}")
        node_levels[node_id] = _positive_int(record["max_level"], f"{path}.max_level")
        for field in (
            "branch",
            "source_branch",
            "slug",
            "name",
            "source_url",
            "retrieved_at",
        ):
            _text(record[field], f"{path}.{field}")

    seen_cost_ids: set[str] = set()
    observed_levels: dict[str, set[int]] = {node_id: set() for node_id in node_levels}
    for index, value in enumerate(cost_records):
        path = f"costs.records[{index}]"
        record = _mapping(value, path)
        _exact_fields(record, COST_RECORD_FIELDS, path)
        node_id = _node_id(record["node_id"], f"{path}.node_id")
        if node_id not in node_levels:
            raise NormalizationError(f"{path}.node_id: unknown node {node_id}")
        level = _positive_int(record["level"], f"{path}.level")
        expected_cost_id = _level_id(node_id, level)
        if record["cost_id"] != expected_cost_id:
            raise NormalizationError(f"{path}.cost_id: expected {expected_cost_id!r}")
        if expected_cost_id in seen_cost_ids:
            raise NormalizationError(f"{path}.cost_id: duplicate {expected_cost_id}")
        seen_cost_ids.add(expected_cost_id)
        observed_levels[node_id].add(level)

        for field in ("timber_m", "grain_m", "herbs_m"):
            if not isinstance(record[field], float) or record[field] < 0:
                raise NormalizationError(
                    f"{path}.{field}: expected a non-negative float"
                )
        for field in (
            "study_scrolls",
            "raw_duration_seconds",
            "normalized_minutes",
            "might_gain",
            "source_record_id",
        ):
            _non_negative_int(record[field], f"{path}.{field}")
        for field in ("raw_duration", "source_url", "retrieved_at"):
            _text(record[field], f"{path}.{field}")

    for node_id, max_level in node_levels.items():
        expected_levels = set(range(1, max_level + 1))
        if observed_levels[node_id] != expected_levels:
            raise NormalizationError(
                f"node {node_id}: cost levels do not equal 1..{max_level}"
            )


def write_documents(
    output_dir: Path,
    nodes_document: Mapping[str, Any],
    costs_document: Mapping[str, Any],
) -> tuple[Path, Path]:
    """Write both canonical documents with deterministic JSON formatting."""

    output_dir.mkdir(parents=True, exist_ok=True)
    nodes_path = output_dir / "research_nodes.json"
    costs_path = output_dir / "research_upgrade_costs.json"
    _write_json(nodes_path, nodes_document)
    _write_json(costs_path, costs_document)
    return nodes_path, costs_path


def _normalize_node(
    node: Mapping[str, Any], node_id: str
) -> tuple[JsonObject, list[JsonObject]]:
    slug = _text(node.get("slug"), f"node {node_id}.slug")
    name = _text(node.get("name"), f"node {node_id}.name")
    source_branch = _text(node.get("tree"), f"node {node_id}.tree")
    max_level = _positive_int(node.get("max_level"), f"node {node_id}.max_level")
    source_url = _text(node.get("source_page_url"), f"node {node_id}.source_page_url")
    retrieval = _mapping(node.get("retrieval"), f"node {node_id}.retrieval")
    retrieved_at = _text(
        retrieval.get("retrieved_at"), f"node {node_id}.retrieval.retrieved_at"
    )
    raw_levels = _list(node.get("levels"), f"node {node_id}.levels")
    if len(raw_levels) != max_level:
        raise NormalizationError(
            f"node {node_id}.levels: expected {max_level}, found {len(raw_levels)}"
        )

    levels = sorted(
        (_mapping(value, f"node {node_id}.levels[]") for value in raw_levels),
        key=lambda value: _positive_int(value.get("level"), f"node {node_id}.level"),
    )
    level_numbers = [
        _positive_int(level.get("level"), f"node {node_id}.level") for level in levels
    ]
    if level_numbers != list(range(1, max_level + 1)):
        raise NormalizationError(
            f"node {node_id}.levels: levels must be contiguous from 1"
        )

    node_record: JsonObject = {
        "node_id": node_id,
        "branch": _canonical_branch(source_branch),
        "source_branch": source_branch,
        "slug": slug,
        "name": name,
        "max_level": max_level,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
    }
    cost_records = [
        _normalize_level(
            level,
            node_id=node_id,
            slug=slug,
            source_url=source_url,
            retrieved_at=retrieved_at,
        )
        for level in levels
    ]
    return node_record, cost_records


def _normalize_level(
    level: Mapping[str, Any],
    *,
    node_id: str,
    slug: str,
    source_url: str,
    retrieved_at: str,
) -> JsonObject:
    number = _positive_int(level.get("level"), f"node {node_id}.level")
    level_node_id = _node_id(
        level.get("research_id"), f"node {node_id}.level {number}.research_id"
    )
    if level_node_id != node_id:
        raise NormalizationError(
            f"node {node_id}.level {number}: research_id is {level_node_id}"
        )
    level_slug = _text(
        level.get("research_slug"),
        f"node {node_id}.level {number}.research_slug",
    )
    if level_slug != slug:
        raise NormalizationError(
            f"node {node_id}.level {number}: research_slug is {level_slug!r}"
        )

    costs = _mapping(level.get("costs"), f"node {node_id}.level {number}.costs")
    unexpected_resources = set(costs) - RESOURCE_KEYS
    if unexpected_resources:
        names = ", ".join(sorted(map(str, unexpected_resources)))
        raise NormalizationError(
            f"node {node_id}.level {number}.costs: unsupported resources: {names}"
        )

    lumber = _non_negative_int(
        costs.get("lumber", 0), f"node {node_id}.level {number}.costs.lumber"
    )
    farms = _non_negative_int(
        costs.get("farms", 0), f"node {node_id}.level {number}.costs.farms"
    )
    herbs = _non_negative_int(
        costs.get("herbs", 0), f"node {node_id}.level {number}.costs.herbs"
    )
    study_scrolls = _non_negative_int(
        costs.get("study_scroll", 0),
        f"node {node_id}.level {number}.costs.study_scroll",
    )
    time_seconds = _non_negative_int(
        level.get("time_seconds", 0),
        f"node {node_id}.level {number}.time_seconds",
    )
    might_gain = _non_negative_int(
        level.get("power", 0), f"node {node_id}.level {number}.power"
    )

    return {
        "cost_id": _level_id(node_id, number),
        "node_id": node_id,
        "level": number,
        "timber_m": round(lumber / 1_000_000, 6),
        "grain_m": round(farms / 1_000_000, 6),
        "herbs_m": round(herbs / 1_000_000, 6),
        "study_scrolls": study_scrolls,
        "raw_duration": _text(
            level.get("time_source"),
            f"node {node_id}.level {number}.time_source",
        ),
        "raw_duration_seconds": time_seconds,
        "normalized_minutes": int(round(time_seconds / 60)),
        "might_gain": might_gain,
        "source_record_id": _non_negative_int(
            level.get("source_record_id"),
            f"node {node_id}.level {number}.source_record_id",
        ),
        "source_url": source_url,
        "retrieved_at": retrieved_at,
    }


def _select_nodes(
    raw_nodes: list[Any], selection: NodeSelection
) -> list[Mapping[str, Any]]:
    nodes = [
        _mapping(value, f"corpus.successful_nodes[{index}]")
        for index, value in enumerate(raw_nodes)
    ]
    if selection.all_nodes:
        selected = nodes
    elif selection.node_ids is not None:
        start, end = selection.node_ids
        selected = [
            node
            for node in nodes
            if start
            <= _numeric_node_id(node.get("research_id"), "node.research_id")
            <= end
        ]
    else:
        requested_tree = selection.tree
        if selection.branch is not None:
            requested_tree = BRANCH_TREE_ALIASES.get(
                selection.branch.casefold(), selection.branch
            )
        assert requested_tree is not None
        actual_tree = _resolve_tree_name(nodes, requested_tree)
        selected = [
            node
            for node in nodes
            if _text(node.get("tree"), "node.tree") == actual_tree
        ]

    return sorted(
        selected,
        key=lambda node: _numeric_node_id(node.get("research_id"), "node.research_id"),
    )


def _resolve_tree_name(nodes: list[Mapping[str, Any]], requested_tree: str) -> str:
    matches = {
        tree
        for node in nodes
        if (tree := _text(node.get("tree"), "node.tree")).casefold()
        == requested_tree.casefold()
    }
    if not matches:
        raise NormalizationError(f"unknown tree or branch: {requested_tree!r}")
    if len(matches) != 1:
        raise NormalizationError(
            f"tree name {requested_tree!r} is ambiguous: {sorted(matches)}"
        )
    return matches.pop()


def _canonical_branch(source_branch: str) -> str:
    return TREE_BRANCH_ALIASES.get(source_branch, source_branch)


def _dataset_name(dataset: str | None, records: list[JsonObject]) -> str:
    if dataset is not None:
        return _text(dataset, "dataset")
    branches = sorted({str(record["branch"]) for record in records})
    if branches == ["Commando"]:
        return "commando_t10"
    if len(branches) == 1:
        return _slug(branches[0])
    return "all_research_trees"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    if not slug:
        raise NormalizationError(f"cannot derive dataset name from {value!r}")
    return slug


def _level_id(node_id: str, level: int) -> str:
    return f"{node_id}:{level:02d}"


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise NormalizationError(f"{path}: expected an object")
    if any(not isinstance(key, str) for key in value):
        raise NormalizationError(f"{path}: object keys must be strings")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise NormalizationError(f"{path}: expected an array")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NormalizationError(f"{path}: expected non-empty text")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool):
        raise NormalizationError(f"{path}: expected an integer, not boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        return int(value)
    raise NormalizationError(f"{path}: expected an integer or integer text")


def _non_negative_int(value: Any, path: str) -> int:
    result = _integer(value, path)
    if result < 0:
        raise NormalizationError(f"{path}: expected a non-negative integer")
    return result


def _positive_int(value: Any, path: str) -> int:
    result = _integer(value, path)
    if result <= 0:
        raise NormalizationError(f"{path}: expected a positive integer")
    return result


def _node_id(value: Any, path: str) -> str:
    node_id = str(value)
    if isinstance(value, bool) or not re.fullmatch(r"\d+", node_id):
        raise NormalizationError(f"{path}: expected a numeric string ID")
    return node_id


def _numeric_node_id(value: Any, path: str) -> int:
    return int(_node_id(value, path))


def _exact_fields(
    record: Mapping[str, Any], expected: tuple[str, ...], path: str
) -> None:
    if tuple(record) != expected:
        raise NormalizationError(
            f"{path}: expected fields {expected}, found {tuple(record)}"
        )


def _matching_count(
    document: Mapping[str, Any],
    field: str,
    records: list[Any],
    path: str,
) -> None:
    count = _non_negative_int(document.get(field), f"{path}.{field}")
    if count != len(records):
        raise NormalizationError(
            f"{path}.{field}: expected {len(records)}, found {count}"
        )


def _write_json(path: Path, document: Mapping[str, Any]) -> None:
    try:
        with path.open("w", encoding="utf-8", newline="\n") as output:
            json.dump(document, output, indent=2, ensure_ascii=False)
            output.write("\n")
    except OSError as error:
        raise NormalizationError(f"{path}: cannot write output: {error}") from error


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--dataset",
        help="Dataset identifier; inferred deterministically when omitted.",
    )
    parser.add_argument(
        "--source-corpus-label",
        help="Metadata label for the input path; defaults to the --input value.",
    )

    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--tree", help="Select one source tree name, such as 'Elite Troop'."
    )
    selection.add_argument(
        "--branch", help="Select one canonical branch name, such as 'Commando'."
    )
    selection.add_argument(
        "--node-ids",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Select an inclusive numeric node ID range.",
    )
    selection.add_argument(
        "--all", action="store_true", help="Normalize every corpus node."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line normalizer."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        selection = NodeSelection(
            tree=arguments.tree,
            branch=arguments.branch,
            node_ids=(tuple(arguments.node_ids) if arguments.node_ids else None),
            all_nodes=arguments.all,
        )
        corpus = load_corpus(arguments.input)
        source_label = arguments.source_corpus_label or arguments.input.as_posix()
        nodes_document, costs_document = normalize_research_export(
            corpus,
            selection=selection,
            dataset=arguments.dataset,
            source_corpus=source_label,
        )
        nodes_path, costs_path = write_documents(
            arguments.output_dir, nodes_document, costs_document
        )
    except (NormalizationError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")

    print(
        f"Wrote {nodes_document['record_count']} nodes to {nodes_path} "
        f"and {costs_document['record_count']} costs to {costs_path}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
