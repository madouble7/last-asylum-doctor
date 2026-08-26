"""Database-wide factual validation and descriptive research-corpus profiling."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from .research import DatabaseError, ResearchDatabase


def validate_research_corpus(database: ResearchDatabase) -> dict[str, Any]:
    """Check stored factual data without modifying it."""
    connection = _connection(database)
    counts = database.table_counts()
    issues: list[dict[str, Any]] = []

    integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
    if integrity != ["ok"]:
        issues.append({"check": "sqlite_integrity", "details": integrity})
    foreign_keys = [
        tuple(row) for row in connection.execute("PRAGMA foreign_key_check")
    ]
    if foreign_keys:
        issues.append({"check": "foreign_keys", "details": foreign_keys})

    _add_query_issue(
        issues,
        "required_node_identity",
        connection,
        """
        SELECT slug FROM research_nodes
        WHERE trim(slug) = '' OR trim(source_research_id) = '' OR trim(name) = ''
           OR trim(tree) = '' OR trim(effect) = '' OR trim(source_page_url) = ''
           OR trim(source_asset_url) = ''
        ORDER BY slug
        """,
    )
    _add_query_issue(
        issues,
        "nonpositive_max_level",
        connection,
        "SELECT slug FROM research_nodes WHERE max_level <= 0 ORDER BY slug",
    )
    _add_query_issue(
        issues,
        "negative_cost_amount",
        connection,
        "SELECT id FROM research_level_costs WHERE amount < 0 ORDER BY id",
    )
    _add_query_issue(
        issues,
        "negative_research_time",
        connection,
        "SELECT id FROM research_levels WHERE research_time_seconds < 0 ORDER BY id",
    )
    _add_query_issue(
        issues,
        "duplicate_logical_levels",
        connection,
        """
        SELECT research_node_id, level FROM research_levels
        GROUP BY research_node_id, level HAVING count(*) > 1
        """,
    )
    _add_query_issue(
        issues,
        "duplicate_logical_costs",
        connection,
        """
        SELECT research_level_id, resource_identifier FROM research_level_costs
        GROUP BY research_level_id, resource_identifier HAVING count(*) > 1
        """,
    )
    _add_query_issue(
        issues,
        "missing_source_provenance",
        connection,
        """
        SELECT n.slug FROM research_nodes AS n
        LEFT JOIN research_source_observations AS o ON o.research_node_id = n.id
        GROUP BY n.id HAVING count(o.id) = 0 ORDER BY n.slug
        """,
    )
    _add_query_issue(
        issues,
        "unfinished_ingestion_runs",
        connection,
        "SELECT id FROM ingestion_runs WHERE status = 'running' ORDER BY id",
    )

    levels_by_slug: dict[str, list[int]] = defaultdict(list)
    for row in connection.execute(
        """
        SELECT n.slug, l.level FROM research_nodes AS n
        LEFT JOIN research_levels AS l ON l.research_node_id = n.id
        ORDER BY n.slug, l.level
        """
    ):
        if row[1] is not None:
            levels_by_slug[str(row[0])].append(int(row[1]))
    shape_failures: list[dict[str, Any]] = []
    for row in connection.execute(
        "SELECT slug, max_level FROM research_nodes ORDER BY slug"
    ):
        slug, max_level = str(row[0]), int(row[1])
        actual = levels_by_slug[slug]
        expected = list(range(1, max_level + 1))
        if actual != expected:
            shape_failures.append(
                {"slug": slug, "max_level": max_level, "stored_levels": actual}
            )
    if shape_failures:
        issues.append(
            {"check": "level_count_and_contiguity", "details": shape_failures}
        )

    run_statuses = {
        str(row[0]): int(row[1])
        for row in connection.execute(
            "SELECT status, count(*) FROM ingestion_runs "
            "GROUP BY status ORDER BY status"
        )
    }
    latest_row = connection.execute(
        """
        SELECT id, status, requested_count, succeeded_count, failed_count, error_message
        FROM ingestion_runs ORDER BY id DESC LIMIT 1
        """
    ).fetchone()
    latest_run = dict(latest_row) if latest_row is not None else None
    def_boost = _def_boost_level_one(connection)
    return {
        "valid": not issues,
        "table_counts": counts,
        "ingestion_run_statuses": run_statuses,
        "latest_ingestion_run": latest_run,
        "def_boost_iii_level_1": def_boost,
        "issues": issues,
    }


def build_science_corpus_profile(
    database: ResearchDatabase, validation: dict[str, Any]
) -> dict[str, Any]:
    """Describe stored facts only; never infer strategic meaning."""
    connection = _connection(database)
    max_levels = [
        int(row[0])
        for row in connection.execute(
            "SELECT max_level FROM research_nodes ORDER BY slug"
        )
    ]
    resources = _resource_inventory(connection)
    shape_counts, shape_nodes = _cost_shapes(connection)
    zero_cost_levels = _zero_cost_levels(connection)
    zero_time_levels = [
        {"slug": str(row[0]), "level": int(row[1])}
        for row in connection.execute(
            """
            SELECT n.slug, l.level FROM research_levels AS l
            JOIN research_nodes AS n ON n.id = l.research_node_id
            WHERE l.research_time_seconds = 0 ORDER BY n.slug, l.level
            """
        )
    ]
    optional_values = {
        "nodes_without_tech_type": _count(
            connection, "tech_type IS NULL", "research_nodes"
        ),
        "nodes_without_image": _count(connection, "image IS NULL", "research_nodes"),
        "nodes_without_position": _count(
            connection, "position IS NULL", "research_nodes"
        ),
        "levels_without_source_record_id": _count(
            connection, "source_record_id IS NULL", "research_levels"
        ),
        "cost_rows_without_item_id": _count(
            connection, "item_id IS NULL", "research_level_costs"
        ),
        "cost_rows_without_source_amount": _count(
            connection, "source_amount IS NULL", "research_level_costs"
        ),
    }
    failed_runs = [
        dict(row)
        for row in connection.execute(
            """
            SELECT id, status, requested_count, succeeded_count,
                   failed_count, error_message
            FROM ingestion_runs WHERE status = 'failed' ORDER BY id
            """
        )
    ]
    return {
        "schema_version": 1,
        "table_counts": validation["table_counts"],
        "research_trees": [
            {"tree": str(row[0]), "node_count": int(row[1])}
            for row in connection.execute(
                "SELECT tree, count(*) FROM research_nodes GROUP BY tree ORDER BY tree"
            )
        ],
        "resource_identifiers": resources,
        "source_item_ids": [
            str(row[0])
            for row in connection.execute(
                """
                SELECT DISTINCT item_id FROM research_level_costs
                WHERE item_id IS NOT NULL ORDER BY item_id
                """
            )
        ],
        "max_level_summary": {
            "minimum": min(max_levels) if max_levels else None,
            "maximum": max(max_levels) if max_levels else None,
            "median": median(max_levels) if max_levels else None,
            "nodes_by_max_level": [
                {"max_level": int(row[0]), "node_count": int(row[1])}
                for row in connection.execute(
                    """
                    SELECT max_level, count(*) FROM research_nodes
                    GROUP BY max_level ORDER BY max_level
                    """
                )
            ],
        },
        "cost_shape_counts": shape_counts,
        "cost_shape_nodes": shape_nodes,
        "zero_cost_levels": zero_cost_levels,
        "zero_time_levels": zero_time_levels,
        "optional_or_missing_values": optional_values,
        "source_parser_schema_anomalies": {
            "validation_issues": validation["issues"],
            "failed_ingestion_runs": failed_runs,
        },
    }


def write_science_corpus_profile(profile: dict[str, Any], output_path: Path) -> None:
    """Write generated, machine-readable factual profile evidence."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _connection(database: ResearchDatabase) -> sqlite3.Connection:
    if database.connection is None:
        raise DatabaseError("Database is not initialized")
    return database.connection


def _add_query_issue(
    issues: list[dict[str, Any]], check: str, connection: sqlite3.Connection, query: str
) -> None:
    rows = [tuple(row) for row in connection.execute(query)]
    if rows:
        issues.append({"check": check, "details": rows})


def _def_boost_level_one(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT l.power, l.research_time_seconds, l.id
        FROM research_levels AS l JOIN research_nodes AS n ON n.id = l.research_node_id
        WHERE n.slug = 'def-boost-iii' AND l.level = 1
        """
    ).fetchone()
    if row is None:
        return None
    costs = {
        str(cost[0]): int(cost[1])
        for cost in connection.execute(
            """
            SELECT resource_identifier, amount FROM research_level_costs
            WHERE research_level_id = ? ORDER BY resource_identifier
            """,
            (row[2],),
        )
    }
    expected = {
        "power": 15_020,
        "research_time_seconds": 964_000,
        "farms": 31_736_000,
        "lumber": 31_736_000,
        "herbs": 97_332_000,
        "study_scroll": 1_440,
    }
    actual = {"power": int(row[0]), "research_time_seconds": int(row[1]), **costs}
    return {
        "present": True,
        "actual": actual,
        "expected": expected,
        "matches_expected": all(
            actual.get(key) == value for key, value in expected.items()
        ),
    }


def _resource_inventory(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT resource_identifier, source_label, item_id, count(*)
        FROM research_level_costs
        GROUP BY resource_identifier, source_label, item_id
        ORDER BY resource_identifier, source_label, item_id
        """
    ).fetchall()
    inventory: dict[str, dict[str, Any]] = {}
    for identifier, label, item_id, count in rows:
        entry = inventory.setdefault(
            str(identifier),
            {
                "resource_identifier": str(identifier),
                "source_labels": set(),
                "item_ids": set(),
                "occurrence_count": 0,
            },
        )
        entry["source_labels"].add(str(label))
        if item_id is not None:
            entry["item_ids"].add(str(item_id))
        entry["occurrence_count"] += int(count)
    return [
        {
            **entry,
            "source_labels": sorted(entry["source_labels"]),
            "item_ids": sorted(entry["item_ids"]),
        }
        for _, entry in sorted(inventory.items())
    ]


def _cost_shapes(
    connection: sqlite3.Connection,
) -> tuple[dict[str, int], dict[str, list[str]]]:
    standard = {"farms", "lumber", "herbs"}
    resources_by_node: dict[str, set[str]] = defaultdict(set)
    for slug, resource in connection.execute(
        """
        SELECT n.slug, c.resource_identifier
        FROM research_nodes AS n
        LEFT JOIN research_levels AS l ON l.research_node_id = n.id
        LEFT JOIN research_level_costs AS c ON c.research_level_id = l.id
        ORDER BY n.slug
        """
    ):
        if resource is not None:
            resources_by_node[str(slug)].add(str(resource))
        else:
            resources_by_node.setdefault(str(slug), set())
    nodes = {
        "standard_resources_only": [],
        "study_scroll_only": [],
        "mixed_costs": [],
        "other_or_no_costs": [],
    }
    for slug, resources in sorted(resources_by_node.items()):
        if resources and resources.issubset(standard):
            nodes["standard_resources_only"].append(slug)
        elif resources == {"study_scroll"}:
            nodes["study_scroll_only"].append(slug)
        elif "study_scroll" in resources and len(resources) > 1:
            nodes["mixed_costs"].append(slug)
        else:
            nodes["other_or_no_costs"].append(slug)
    return ({key: len(value) for key, value in nodes.items()}, nodes)


def _zero_cost_levels(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        {"slug": str(row[0]), "level": int(row[1])}
        for row in connection.execute(
            """
            SELECT n.slug, l.level
            FROM research_levels AS l
            JOIN research_nodes AS n ON n.id = l.research_node_id
            LEFT JOIN research_level_costs AS c ON c.research_level_id = l.id
            GROUP BY l.id
            HAVING coalesce(sum(c.amount), 0) = 0
            ORDER BY n.slug, l.level
            """
        )
    ]


def _count(connection: sqlite3.Connection, condition: str, table: str) -> int:
    return int(
        connection.execute(
            f"SELECT count(*) FROM {table} WHERE {condition}"
        ).fetchone()[0]
    )
