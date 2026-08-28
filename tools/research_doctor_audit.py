"""Read-only capability audit for the local research corpus.

The script intentionally reads the existing SQLite database and processed
corpus only. It does not fetch sources, mutate the database, or infer
prerequisites/effects from names or positions.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

TABLES = (
    "research_nodes",
    "research_levels",
    "research_level_costs",
    "research_source_observations",
    "ingestion_runs",
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/last_asylum.db"))
    parser.add_argument(
        "--corpus", type=Path, default=Path("data/processed/research_corpus.json")
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _totals(
    nodes: list[dict[str, Any]], slug: str, first: int, last: int
) -> dict[str, int]:
    node = next(node for node in nodes if node["slug"] == slug)
    levels = [level for level in node["levels"] if first <= level["level"] <= last]
    result: Counter[str] = Counter()
    result["levels"] = len(levels)
    result["power"] = sum(level["power"] for level in levels)
    result["research_time_seconds"] = sum(level["time_seconds"] for level in levels)
    for level in levels:
        result.update(level["costs"])
    return dict(result)


def audit(database_path: Path, corpus_path: Path) -> dict[str, Any]:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    nodes = corpus["successful_nodes"]
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        schema = {
            table: [
                dict(row) for row in connection.execute(f"PRAGMA table_info({table})")
            ]
            for table in TABLES
        }
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in TABLES
        }
        tree_counts = {
            row["tree"]: row["count"]
            for row in connection.execute(
                "SELECT tree, COUNT(*) AS count FROM research_nodes "
                "GROUP BY tree ORDER BY tree"
            )
        }
        null_counts = {
            column: connection.execute(
                f"SELECT COUNT(*) FROM research_nodes WHERE {column} IS NULL"
            ).fetchone()[0]
            for column in ("tech_type", "image", "position")
        }
        cost_resources = {
            row["resource_identifier"]: row["count"]
            for row in connection.execute(
                """
                SELECT resource_identifier, COUNT(*) AS count
                FROM research_level_costs
                GROUP BY resource_identifier ORDER BY resource_identifier
                """
            )
        }

    node_keys = sorted({key for node in nodes for key in node})
    level_keys = sorted(
        {key for node in nodes for level in node["levels"] for key in level}
    )
    cost_keys = sorted(
        {
            key
            for node in nodes
            for level in node["levels"]
            for cost in level["source_costs"]
            for key in cost
        }
    )
    shape_counts = Counter(
        ",".join(sorted(level["costs"]))
        for node in nodes
        for level in node["levels"]
    )
    node_level_counts = Counter(len(node["levels"]) for node in nodes)
    all_sources_complete = all(
        node.get("source_page_url")
        and node.get("source_asset_url")
        and node.get("retrieval", {}).get("sha256")
        for node in nodes
    )
    examples = {
        "def_boost_iii_1_to_10": _totals(nodes, "def-boost-iii", 1, 10),
        "additional_farmland_level_1": _totals(nodes, "additional-farmland", 1, 1),
    }
    for node in nodes:
        if any("study_scroll" in level["costs"] for level in node["levels"]):
            examples["first_scroll_node"] = {
                "slug": node["slug"],
                "name": node["name"],
                "levels_1_to_max": _totals(nodes, node["slug"], 1, node["max_level"]),
            }
            break

    return {
        "database": str(database_path),
        "corpus": str(corpus_path),
        "counts": counts,
        "tree_count": len(tree_counts),
        "tree_counts": tree_counts,
        "node_level_count_distribution": dict(sorted(node_level_counts.items())),
        "schema": schema,
        "normalized_corpus_keys": {
            "node": node_keys,
            "level": level_keys,
            "source_cost": cost_keys,
        },
        "null_counts": null_counts,
        "cost_resource_row_counts": cost_resources,
        "cost_shape_level_observations": dict(shape_counts),
        "source_provenance_complete": all_sources_complete,
        "effect_data": {
            "node_effect_is_nonempty_text": all(
                isinstance(node.get("effect"), str) and node["effect"]
                for node in nodes
            ),
            "structured_effect_amount_field": False,
            "effect_unit_field": False,
            "cumulative_effect_field": False,
            "multiple_effects_field": False,
        },
        "prerequisite_data": {
            "research_node_table": False,
            "research_level_table": False,
            "building_or_sanctuary_gate": False,
            "tree_unlock_gate": False,
            "position_metadata": True,
        },
        "calculation_examples": examples,
    }


def main() -> None:
    arguments = _args()
    result = audit(arguments.database, arguments.corpus)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
