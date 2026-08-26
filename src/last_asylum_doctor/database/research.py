"""SQLite persistence for factual research data only."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from last_asylum_doctor.models import ResearchNode, validate_research_node


class DatabaseError(RuntimeError):
    """Raised when factual research records cannot be stored safely."""


@dataclass(frozen=True, slots=True)
class IngestionRunSummary:
    """The persisted outcome of one database ingestion run."""

    run_id: int
    requested_count: int
    succeeded_count: int
    failed_count: int
    status: str
    new_source_count: int = 0
    changed_source_count: int = 0
    unchanged_source_count: int = 0


class ResearchDatabase:
    """Small SQLite repository for normalized, auditable research facts."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> ResearchDatabase:
        self.initialize()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def initialize(self) -> None:
        """Create the database schema and enable foreign-key enforcement."""
        if self.connection is not None:
            return
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            connection.executescript(_SCHEMA)
        self.connection = connection

    def close(self) -> None:
        """Close the SQLite connection if one is open."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def store_research_nodes(
        self,
        nodes: Iterable[ResearchNode],
        requested_slugs: Iterable[str],
        failures: dict[str, str] | None = None,
    ) -> IngestionRunSummary:
        """Upsert accepted nodes and accurately record partial source failures.

        A source-node failure does not make already validated factual records
        invalid. Those records are committed in one transaction, while the run is
        marked ``failed`` with explicit succeeded/failed counts. A database write
        failure still rolls back the factual transaction.
        """
        connection = self._connection()
        node_list = tuple(nodes)
        requested_slug_list = tuple(requested_slugs)
        failure_map = dict(failures or {})
        _validate_store_request(node_list, requested_slug_list, failure_map)

        started_at = _now()
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO ingestion_runs (
                    started_at, status, requested_slugs_json, requested_count,
                    succeeded_count, failed_count
                ) VALUES (?, 'running', ?, ?, 0, 0)
                """,
                (started_at, json.dumps(requested_slug_list), len(requested_slug_list)),
            )
        run_id = int(cursor.lastrowid)

        try:
            with connection:
                source_changes = self._source_change_counts(connection, node_list)
                for node in node_list:
                    self._upsert_node(connection, run_id, node, _now())
                self._assert_foreign_keys(connection)
                status = "completed" if not failure_map else "failed"
                error_message = (
                    None
                    if not failure_map
                    else json.dumps({"source_failures": failure_map}, sort_keys=True)
                )
                connection.execute(
                    """
                    UPDATE ingestion_runs SET
                        completed_at = ?, status = ?, succeeded_count = ?,
                        failed_count = ?, error_message = ?
                    WHERE id = ?
                    """,
                    (
                        _now(),
                        status,
                        len(node_list),
                        len(failure_map),
                        error_message,
                        run_id,
                    ),
                )
        except Exception as error:
            with connection:
                connection.execute(
                    """
                    UPDATE ingestion_runs
                    SET completed_at = ?, status = 'failed', failed_count = ?,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (_now(), len(requested_slug_list), str(error), run_id),
                )
            if isinstance(error, DatabaseError):
                raise
            raise DatabaseError(
                f"Could not store factual research data: {error}"
            ) from error

        return IngestionRunSummary(
            run_id=run_id,
            requested_count=len(requested_slug_list),
            succeeded_count=len(node_list),
            failed_count=len(failure_map),
            status="completed" if not failure_map else "failed",
            new_source_count=source_changes["new"],
            changed_source_count=source_changes["changed"],
            unchanged_source_count=source_changes["unchanged"],
        )

    def _source_change_counts(
        self,
        connection: sqlite3.Connection,
        nodes: tuple[ResearchNode, ...],
    ) -> dict[str, int]:
        """Compare each accepted asset checksum to its previous observation."""
        counts = {"new": 0, "changed": 0, "unchanged": 0}
        for node in nodes:
            previous = connection.execute(
                """
                SELECT o.content_sha256
                FROM research_source_observations AS o
                JOIN research_nodes AS n ON n.id = o.research_node_id
                WHERE n.slug = ?
                ORDER BY o.id DESC LIMIT 1
                """,
                (node.slug,),
            ).fetchone()
            if previous is None:
                counts["new"] += 1
            elif str(previous[0]) == node.retrieval.sha256:
                counts["unchanged"] += 1
            else:
                counts["changed"] += 1
        return counts

    def get_research(self, slug: str) -> dict[str, Any] | None:
        """Return one stored factual research record with levels and costs."""
        connection = self._connection()
        node_row = connection.execute(
            "SELECT * FROM research_nodes WHERE slug = ?", (slug,)
        ).fetchone()
        if node_row is None:
            return None

        node = dict(node_row)
        node_id = int(node.pop("id"))
        latest_observation = connection.execute(
            """
            SELECT * FROM research_source_observations
            WHERE research_node_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (node_id,),
        ).fetchone()
        if latest_observation is not None:
            node["latest_source_observation"] = dict(latest_observation)

        levels: list[dict[str, Any]] = []
        level_rows = connection.execute(
            """
            SELECT * FROM research_levels
            WHERE research_node_id = ?
            ORDER BY level
            """,
            (node_id,),
        ).fetchall()
        for level_row in level_rows:
            level = dict(level_row)
            level_id = int(level.pop("id"))
            level.pop("research_node_id")
            costs = connection.execute(
                """
                SELECT resource_identifier, source_label, amount, item_id, source_amount
                FROM research_level_costs
                WHERE research_level_id = ?
                ORDER BY resource_identifier
                """,
                (level_id,),
            ).fetchall()
            level["costs"] = [dict(cost) for cost in costs]
            levels.append(level)
        node["levels"] = levels
        return node

    def table_counts(self) -> dict[str, int]:
        """Return counts useful for factual-ingestion verification."""
        connection = self._connection()
        return {
            table: int(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            )
            for table in (
                "research_nodes",
                "research_levels",
                "research_level_costs",
                "research_source_observations",
                "ingestion_runs",
            )
        }

    def _upsert_node(
        self,
        connection: sqlite3.Connection,
        run_id: int,
        node: ResearchNode,
        seen_at: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO research_nodes (
                slug, source_research_id, name, tree, tree_slug, effect, max_level,
                tech_type, image, position, source_page_url, source_asset_url,
                first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                source_research_id = excluded.source_research_id,
                name = excluded.name,
                tree = excluded.tree,
                tree_slug = excluded.tree_slug,
                effect = excluded.effect,
                max_level = excluded.max_level,
                tech_type = excluded.tech_type,
                image = excluded.image,
                position = excluded.position,
                source_page_url = excluded.source_page_url,
                source_asset_url = excluded.source_asset_url,
                last_seen_at = excluded.last_seen_at
            """,
            (
                node.slug,
                node.research_id,
                node.name,
                node.tree,
                node.tree_slug,
                node.effect,
                node.max_level,
                node.tech_type,
                node.image,
                node.position,
                node.source_page_url,
                node.source_asset_url,
                seen_at,
                seen_at,
            ),
        )
        node_id = int(
            connection.execute(
                "SELECT id FROM research_nodes WHERE slug = ?", (node.slug,)
            ).fetchone()[0]
        )
        self._insert_observation(connection, run_id, node_id, node, seen_at)
        self._upsert_levels(connection, node_id, node)

    def _insert_observation(
        self,
        connection: sqlite3.Connection,
        run_id: int,
        node_id: int,
        node: ResearchNode,
        observed_at: str,
    ) -> None:
        metadata = node.retrieval
        connection.execute(
            """
            INSERT INTO research_source_observations (
                ingestion_run_id, research_node_id, observed_at, source_page_url,
                source_asset_url, source_retrieved_at, content_sha256, etag,
                last_modified, content_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                node_id,
                observed_at,
                node.source_page_url,
                node.source_asset_url,
                metadata.retrieved_at,
                metadata.sha256,
                metadata.etag,
                metadata.last_modified,
                metadata.content_type,
            ),
        )

    def _upsert_levels(
        self,
        connection: sqlite3.Connection,
        node_id: int,
        node: ResearchNode,
    ) -> None:
        current_level_numbers = [level.level for level in node.levels]
        placeholders = ", ".join("?" for _ in current_level_numbers)
        connection.execute(
            "DELETE FROM research_levels "
            f"WHERE research_node_id = ? AND level NOT IN ({placeholders})",
            (node_id, *current_level_numbers),
        )

        for level in node.levels:
            connection.execute(
                """
                INSERT INTO research_levels (
                    research_node_id, level, source_record_id, power,
                    research_time_seconds, time_source
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(research_node_id, level) DO UPDATE SET
                    source_record_id = excluded.source_record_id,
                    power = excluded.power,
                    research_time_seconds = excluded.research_time_seconds,
                    time_source = excluded.time_source
                """,
                (
                    node_id,
                    level.level,
                    level.source_record_id,
                    level.power,
                    level.time_seconds,
                    level.time_source,
                ),
            )
            level_id = int(
                connection.execute(
                    """
                    SELECT id FROM research_levels
                    WHERE research_node_id = ? AND level = ?
                    """,
                    (node_id, level.level),
                ).fetchone()[0]
            )
            connection.execute(
                "DELETE FROM research_level_costs WHERE research_level_id = ?",
                (level_id,),
            )
            connection.executemany(
                """
                INSERT INTO research_level_costs (
                    research_level_id, resource_identifier, source_label, amount,
                    item_id, source_amount
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        level_id,
                        cost.resource,
                        cost.source_label,
                        cost.amount,
                        cost.item_id,
                        cost.source_amount,
                    )
                    for cost in level.source_costs
                ],
            )

    def _assert_foreign_keys(self, connection: sqlite3.Connection) -> None:
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise DatabaseError(f"Foreign-key validation failed: {violations}")

    def _connection(self) -> sqlite3.Connection:
        if self.connection is None:
            raise DatabaseError("Database is not initialized")
        return self.connection


def _validate_store_request(
    nodes: tuple[ResearchNode, ...],
    requested_slugs: tuple[str, ...],
    failures: dict[str, str],
) -> None:
    if not requested_slugs:
        raise DatabaseError("An ingestion run requires explicitly requested slugs")
    if len(set(requested_slugs)) != len(requested_slugs):
        raise DatabaseError("Requested slugs must be unique")
    node_slugs = [node.slug for node in nodes]
    if len(set(node_slugs)) != len(node_slugs):
        raise DatabaseError("Cannot store duplicate research nodes in one run")
    failure_slugs = set(failures)
    if not failure_slugs.issubset(requested_slugs):
        raise DatabaseError("Source failures must be among requested slugs")
    if set(node_slugs).intersection(failure_slugs):
        raise DatabaseError("A source slug cannot be both stored and failed")
    if set(node_slugs).union(failure_slugs) != set(requested_slugs):
        raise DatabaseError(
            "Each requested slug must be either stored or have a source failure"
        )
    if any(not reason.strip() for reason in failures.values()):
        raise DatabaseError("Source failure reasons cannot be blank")
    for node in nodes:
        validate_research_node(node)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    requested_slugs_json TEXT NOT NULL,
    requested_count INTEGER NOT NULL CHECK (requested_count >= 0),
    succeeded_count INTEGER NOT NULL DEFAULT 0 CHECK (succeeded_count >= 0),
    failed_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_count >= 0),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS research_nodes (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    source_research_id TEXT NOT NULL,
    name TEXT NOT NULL,
    tree TEXT NOT NULL,
    tree_slug TEXT NOT NULL,
    effect TEXT NOT NULL,
    max_level INTEGER NOT NULL CHECK (max_level > 0),
    tech_type INTEGER,
    image TEXT,
    position TEXT,
    source_page_url TEXT NOT NULL,
    source_asset_url TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_levels (
    id INTEGER PRIMARY KEY,
    research_node_id INTEGER NOT NULL REFERENCES research_nodes(id) ON DELETE CASCADE,
    level INTEGER NOT NULL CHECK (level > 0),
    source_record_id INTEGER,
    power INTEGER NOT NULL CHECK (power >= 0),
    research_time_seconds INTEGER NOT NULL CHECK (research_time_seconds >= 0),
    time_source TEXT NOT NULL,
    UNIQUE(research_node_id, level)
);

CREATE TABLE IF NOT EXISTS research_level_costs (
    id INTEGER PRIMARY KEY,
    research_level_id INTEGER NOT NULL
        REFERENCES research_levels(id) ON DELETE CASCADE,
    resource_identifier TEXT NOT NULL,
    source_label TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount >= 0),
    item_id TEXT,
    source_amount TEXT,
    UNIQUE(research_level_id, resource_identifier)
);

CREATE TABLE IF NOT EXISTS research_source_observations (
    id INTEGER PRIMARY KEY,
    ingestion_run_id INTEGER NOT NULL
        REFERENCES ingestion_runs(id) ON DELETE RESTRICT,
    research_node_id INTEGER NOT NULL
        REFERENCES research_nodes(id) ON DELETE RESTRICT,
    observed_at TEXT NOT NULL,
    source_page_url TEXT NOT NULL,
    source_asset_url TEXT NOT NULL,
    source_retrieved_at TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    etag TEXT,
    last_modified TEXT,
    content_type TEXT,
    UNIQUE(ingestion_run_id, research_node_id)
);

CREATE INDEX IF NOT EXISTS idx_research_levels_node
    ON research_levels(research_node_id, level);
CREATE INDEX IF NOT EXISTS idx_research_level_costs_level
    ON research_level_costs(research_level_id, resource_identifier);
CREATE INDEX IF NOT EXISTS idx_research_observations_node
    ON research_source_observations(research_node_id, id DESC);
"""
