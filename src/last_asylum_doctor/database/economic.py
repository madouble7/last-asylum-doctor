"""SQLite persistence for source-backed Shop Doctor economic facts."""
# ruff: noqa: E501

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from last_asylum_doctor.models.economic import ShopDoctorWorkbook

from .research import ResearchDatabase


@dataclass(frozen=True, slots=True)
class EconomicIngestionSummary:
    """Counts from one safe Shop Doctor workbook ingestion."""

    snapshot_id: int
    snapshot_created: bool
    items_created: int
    aliases_created: int
    offers_created: int
    cash_packs_created: int
    pack_components_created: int
    relationships_created: int
    model_observations_created: int


class EconomicDatabase(ResearchDatabase):
    """The same factual SQLite database, extended with economic source records."""

    def initialize(self) -> None:
        super().initialize()
        connection = self._connection()
        with connection:
            connection.executescript(_ECONOMIC_SCHEMA)
            columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(offer_observations)")
            }
            if "package_display" not in columns:
                connection.execute(
                    "ALTER TABLE offer_observations ADD COLUMN package_display TEXT"
                )

    def store_shop_doctor(
        self, workbook: ShopDoctorWorkbook
    ) -> EconomicIngestionSummary:
        """Upsert a workbook snapshot without replacing historical observations."""
        connection = self._connection()
        now = _now()
        with connection:
            snapshot_id, snapshot_created = self._ensure_snapshot(
                connection, workbook, now
            )
            if not snapshot_created:
                self._assert_foreign_keys(connection)
                return EconomicIngestionSummary(
                    snapshot_id=snapshot_id,
                    snapshot_created=False,
                    items_created=0,
                    aliases_created=0,
                    offers_created=0,
                    cash_packs_created=0,
                    pack_components_created=0,
                    relationships_created=0,
                    model_observations_created=0,
                )
            item_ids, items_created, aliases_created, item_model_created = (
                self._store_items(connection, workbook, snapshot_id, now)
            )
            shop_ids = self._store_shops(connection, workbook, snapshot_id)
            currency_ids = self._store_currencies(connection, workbook, item_ids)
            self._store_currency_assumptions(
                connection, workbook, snapshot_id, currency_ids
            )
            group_ids, relationships_created = self._store_relationships(
                connection, workbook, snapshot_id, item_ids
            )
            offers_created = self._store_offers(
                connection,
                workbook,
                snapshot_id,
                item_ids,
                shop_ids,
                currency_ids,
                group_ids,
            )
            pack_ids, cash_packs_created = self._store_packs(
                connection, workbook, snapshot_id
            )
            pack_components_created = self._store_components(
                connection, workbook, snapshot_id, pack_ids, item_ids
            )
            model_created = item_model_created + self._store_model_observations(
                connection, workbook, snapshot_id
            )
            self._store_research_bridges(connection, item_ids, snapshot_id)
            self._assert_foreign_keys(connection)
        return EconomicIngestionSummary(
            snapshot_id=snapshot_id,
            snapshot_created=snapshot_created,
            items_created=items_created,
            aliases_created=aliases_created,
            offers_created=offers_created,
            cash_packs_created=cash_packs_created,
            pack_components_created=pack_components_created,
            relationships_created=relationships_created,
            model_observations_created=model_created,
        )

    def get_item(self, identifier: str) -> dict[str, Any] | None:
        """Return one canonical item with its source-backed relationships."""
        connection = self._connection()
        key = _key(identifier)
        row = connection.execute(
            "SELECT * FROM items WHERE canonical_key = ?", (key,)
        ).fetchone()
        if row is None:
            row = connection.execute(
                """
                SELECT i.* FROM items AS i JOIN item_aliases AS a ON a.item_id = i.id
                WHERE a.alias_key = ?
                """,
                (key,),
            ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item_id = int(item.pop("id"))
        item["aliases"] = [
            dict(value)
            for value in connection.execute(
                "SELECT alias, source_terminology FROM item_aliases WHERE item_id = ? ORDER BY alias",
                (item_id,),
            )
        ]
        item["research_resource_bridges"] = [
            dict(value)
            for value in connection.execute(
                "SELECT domain, source_key FROM item_domain_keys WHERE item_id = ? ORDER BY domain, source_key",
                (item_id,),
            )
        ]
        item["conversions"] = [
            dict(value)
            for value in connection.execute(
                """
                SELECT i.name AS container, c.context, c.contents_rule, o.option_index,
                       target.name AS option_item, o.quantity
                FROM choice_groups AS c
                JOIN choice_options AS o ON o.choice_group_id = c.id
                JOIN items AS i ON i.id = c.container_item_id
                JOIN items AS target ON target.id = o.option_item_id
                WHERE c.container_item_id = ? OR o.option_item_id = ?
                ORDER BY c.id, o.option_index
                """,
                (item_id, item_id),
            )
        ]
        item["pack_occurrences"] = [
            dict(value)
            for value in connection.execute(
                """
                SELECT p.name AS pack, p.date_seen, c.normalized_quantity,
                       c.package_display, c.data_status
                FROM cash_pack_components AS c JOIN cash_packs AS p ON p.id = c.cash_pack_id
                WHERE c.item_id = ? ORDER BY p.date_seen, p.name
                """,
                (item_id,),
            )
        ]
        return item

    def get_item_prices(self, identifier: str) -> list[dict[str, Any]] | None:
        """Return immutable raw price history for an item."""
        item = self.get_item(identifier)
        if item is None:
            return None
        connection = self._connection()
        return [
            dict(value)
            for value in connection.execute(
                """
                SELECT o.original_offer_id, o.date_seen, s.name AS shop,
                       o.normalized_quantity, o.cost, c.name AS currency,
                       o.direct_cash_price, o.package_display, o.speedup_type,
                       o.source_text, snapshot.filename, snapshot.sha256
                FROM offer_observations AS o
                JOIN items AS i ON i.id = o.item_id
                JOIN shops AS s ON s.id = o.shop_id
                JOIN currencies AS c ON c.id = o.currency_id
                JOIN source_snapshots AS snapshot ON snapshot.id = o.source_snapshot_id
                WHERE i.canonical_key = ?
                ORDER BY o.date_seen, o.id
                """,
                (item["canonical_key"],),
            )
        ]

    def economic_table_counts(self) -> dict[str, int]:
        connection = self._connection()
        tables = (
            "source_snapshots",
            "items",
            "item_aliases",
            "item_domain_keys",
            "shops",
            "currencies",
            "currency_valuation_assumptions",
            "offer_observations",
            "choice_groups",
            "choice_options",
            "cash_packs",
            "cash_pack_components",
            "economic_model_observations",
        )
        return {
            table: int(
                connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            )
            for table in tables
        }

    def validate_economic_data(self) -> dict[str, Any]:
        connection = self._connection()
        issues: list[dict[str, Any]] = []
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        if integrity != ["ok"]:
            issues.append({"check": "sqlite_integrity", "details": integrity})
        foreign_keys = [
            tuple(row) for row in connection.execute("PRAGMA foreign_key_check")
        ]
        if foreign_keys:
            issues.append({"check": "foreign_keys", "details": foreign_keys})
        duplicate_names = connection.execute(
            "SELECT name FROM items GROUP BY canonical_key HAVING count(*) > 1"
        ).fetchall()
        if duplicate_names:
            issues.append(
                {
                    "check": "duplicate_items",
                    "details": [tuple(row) for row in duplicate_names],
                }
            )
        checks = connection.execute(
            """
            SELECT original_offer_id FROM offer_observations
            WHERE normalized_quantity <= 0
               OR (actual_item_count IS NOT NULL AND base_units_per_item IS NOT NULL
                   AND abs(normalized_quantity - actual_item_count * base_units_per_item) > 0.000000001)
            """
        ).fetchall()
        if checks:
            issues.append(
                {"check": "normalization", "details": [tuple(row) for row in checks]}
            )
        invalid_choice = connection.execute(
            """
            SELECT c.id FROM choice_groups AS c LEFT JOIN choice_options AS o
            ON o.choice_group_id = c.id GROUP BY c.id HAVING count(o.id) = 0
            """
        ).fetchall()
        if invalid_choice:
            issues.append(
                {
                    "check": "empty_choice_groups",
                    "details": [tuple(row) for row in invalid_choice],
                }
            )
        bridges = {
            str(row[0]): str(row[1])
            for row in connection.execute(
                """
                SELECT d.source_key, i.canonical_key FROM item_domain_keys AS d
                JOIN items AS i ON i.id = d.item_id WHERE d.domain = 'research_cost'
                """
            )
        }
        return {
            "valid": not issues,
            "table_counts": self.economic_table_counts(),
            "research_resource_bridges": bridges,
            "issues": issues,
        }

    def _ensure_snapshot(
        self, connection: sqlite3.Connection, workbook: ShopDoctorWorkbook, now: str
    ) -> tuple[int, bool]:
        existing = connection.execute(
            "SELECT id FROM source_snapshots WHERE sha256 = ?", (workbook.sha256,)
        ).fetchone()
        if existing is not None:
            return int(existing[0]), False
        cursor = connection.execute(
            """
            INSERT INTO source_snapshots (
                source_name, filename, sha256, size_bytes, sheet_names_json, snapshot_date, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Shop Doctor",
                workbook.filename,
                workbook.sha256,
                workbook.size_bytes,
                json.dumps(workbook.sheet_names),
                workbook.snapshot_date.isoformat(),
                now,
            ),
        )
        return int(cursor.lastrowid), True

    def _store_items(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        snapshot_id: int,
        now: str,
    ) -> tuple[dict[str, int], int, int, int]:
        ids: dict[str, int] = {}
        created = aliases = model_created = 0
        for item in workbook.items:
            cursor = connection.execute(
                """
                INSERT INTO items (canonical_key, name, base_unit, category, item_type, data_status,
                    source_text, notes, doctor_resource_key, first_snapshot_id, last_snapshot_id, first_seen_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_key) DO UPDATE SET name=excluded.name, base_unit=excluded.base_unit,
                    category=excluded.category, item_type=excluded.item_type, data_status=excluded.data_status,
                    source_text=excluded.source_text, notes=excluded.notes, doctor_resource_key=excluded.doctor_resource_key,
                    last_snapshot_id=excluded.last_snapshot_id, last_seen_at=excluded.last_seen_at
                """,
                (
                    _key(item.name),
                    item.name,
                    item.base_unit,
                    item.category,
                    item.item_type,
                    item.data_status,
                    item.source,
                    item.notes,
                    item.doctor_resource_key,
                    snapshot_id,
                    snapshot_id,
                    now,
                    now,
                ),
            )
            created += int(cursor.rowcount == 1)
            item_id = int(
                connection.execute(
                    "SELECT id FROM items WHERE canonical_key = ?", (_key(item.name),)
                ).fetchone()[0]
            )
            ids[item.name] = item_id
            for alias in (item.name, *item.aliases):
                alias_cursor = connection.execute(
                    "INSERT OR IGNORE INTO item_aliases (item_id, alias, alias_key, source_terminology, source_snapshot_id, source_row) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        item_id,
                        alias,
                        _key(alias),
                        "ITEM CATALOG",
                        snapshot_id,
                        item.source_row,
                    ),
                )
                aliases += int(alias_cursor.rowcount == 1)
            for metric, value in item.model_values.items():
                model_created += self._insert_model(
                    connection,
                    snapshot_id,
                    "item",
                    item.name,
                    metric,
                    value,
                    "ITEM CATALOG",
                    item.source_row,
                )
        return ids, created, aliases, model_created

    def _store_shops(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        snapshot_id: int,
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        for name in sorted({offer.shop_name for offer in workbook.offers}):
            kind = (
                "virtual_choice_route"
                if name.startswith("[Choice]")
                else "shop_or_event"
            )
            connection.execute(
                "INSERT OR IGNORE INTO shops (name, kind, source_snapshot_id) VALUES (?, ?, ?)",
                (name, kind, snapshot_id),
            )
            result[name] = int(
                connection.execute(
                    "SELECT id FROM shops WHERE name = ?", (name,)
                ).fetchone()[0]
            )
        return result

    def _store_currencies(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        item_ids: dict[str, int],
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        assumption_names = {
            value.currency_name for value in workbook.currency_assumptions
        }
        for name in sorted(
            {offer.currency_name for offer in workbook.offers}.union(assumption_names)
        ):
            kind = (
                "internal_choice_container"
                if name in item_ids and name not in assumption_names
                else "currency"
            )
            connection.execute(
                "INSERT OR IGNORE INTO currencies (name, kind) VALUES (?, ?)",
                (name, kind),
            )
            result[name] = int(
                connection.execute(
                    "SELECT id FROM currencies WHERE name = ?", (name,)
                ).fetchone()[0]
            )
        return result

    def _store_currency_assumptions(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        snapshot_id: int,
        currency_ids: dict[str, int],
    ) -> None:
        for value in workbook.currency_assumptions:
            connection.execute(
                """INSERT OR REPLACE INTO currency_valuation_assumptions (
                    source_snapshot_id, currency_id, value_per_unit, classification, basis, active, notes, source_sheet, source_row
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ADVANCED SETTINGS', ?)""",
                (
                    snapshot_id,
                    currency_ids[value.currency_name],
                    value.value_per_unit,
                    value.classification,
                    value.basis,
                    value.active,
                    value.notes,
                    value.source_row,
                ),
            )

    def _store_relationships(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        snapshot_id: int,
        item_ids: dict[str, int],
    ) -> tuple[dict[str, int], int]:
        group_ids: dict[str, int] = {}
        created = 0
        grouped: dict[tuple[str, str | None, str, int], list[Any]] = {}
        for relation in workbook.relationships:
            grouped.setdefault(
                (
                    relation.container_name,
                    relation.context,
                    relation.contents_rule,
                    relation.source_row,
                ),
                [],
            ).append(relation)
        for (container, context, rule, row), relations in grouped.items():
            cursor = connection.execute(
                "INSERT OR IGNORE INTO choice_groups (source_snapshot_id, container_item_id, context, contents_rule, source_sheet, source_row) VALUES (?, ?, ?, ?, 'ITEM CATALOG', ?)",
                (snapshot_id, item_ids[container], context, rule, row),
            )
            created += int(cursor.rowcount == 1)
            group_id = int(
                connection.execute(
                    "SELECT id FROM choice_groups WHERE source_snapshot_id=? AND container_item_id=? AND source_row=?",
                    (snapshot_id, item_ids[container], row),
                ).fetchone()[0]
            )
            group_ids[container] = group_id
            for index, relation in enumerate(relations, start=1):
                connection.execute(
                    "INSERT OR IGNORE INTO choice_options (choice_group_id, option_index, option_item_id, quantity) VALUES (?, ?, ?, ?)",
                    (
                        group_id,
                        index,
                        item_ids[relation.option_name],
                        relation.option_quantity,
                    ),
                )
        return group_ids, created

    def _store_offers(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        snapshot_id: int,
        item_ids: dict[str, int],
        shop_ids: dict[str, int],
        currency_ids: dict[str, int],
        group_ids: dict[str, int],
    ) -> int:
        created = 0
        for offer in workbook.offers:
            package_item_id = item_ids.get(offer.actual_package_item or "")
            choice_group_id = (
                group_ids.get(offer.currency_name)
                if offer.shop_name.startswith("[Choice]")
                else None
            )
            cursor = connection.execute(
                """INSERT OR IGNORE INTO offer_observations (
                    source_snapshot_id, source_sheet, source_row, original_offer_id, active, date_seen,
                    shop_id, shop_snapshot_id, item_id, normalized_quantity, cost, currency_id,
                    direct_cash_price, repeat_limit, notes, source_text, actual_package_item_id,
                    actual_package_item_text, actual_item_count, base_units_per_item, normalized_quantity_check,
                    speedup_type, package_display, choice_group_id
                ) VALUES (?, 'LIVE OFFERS', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot_id,
                    offer.source_row,
                    offer.offer_id,
                    offer.active,
                    offer.date_seen.isoformat(),
                    shop_ids[offer.shop_name],
                    offer.shop_snapshot_id,
                    item_ids[offer.item_name],
                    offer.normalized_quantity,
                    offer.cost,
                    currency_ids[offer.currency_name],
                    offer.direct_cash_price,
                    offer.repeat_limit,
                    offer.notes,
                    offer.source,
                    package_item_id,
                    offer.actual_package_item,
                    offer.actual_item_count,
                    offer.base_units_per_item,
                    offer.normalized_quantity_check,
                    offer.speedup_type,
                    offer.package_display,
                    choice_group_id,
                ),
            )
            created += int(cursor.rowcount == 1)
        return created

    def _store_packs(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        snapshot_id: int,
    ) -> tuple[dict[str, int], int]:
        result: dict[str, int] = {}
        created = 0
        for pack in workbook.cash_packs:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO cash_packs (
                    source_snapshot_id, source_sheet, source_row, original_pack_id, active, date_seen, name,
                    price_usd, assumed_bonus_diamonds, bonus_diamonds_status, snapshot_label, repeat_limit,
                    notes, source_text, valuation_status, components_valued
                ) VALUES (?, 'CASH PACKS', ?, ?, ?, ?, ?, ?, ?, 'DERIVED_ASSUMPTION', ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot_id,
                    pack.source_row,
                    pack.pack_id,
                    pack.active,
                    pack.date_seen.isoformat(),
                    pack.name,
                    pack.price_usd,
                    pack.assumed_bonus_diamonds,
                    pack.snapshot_id,
                    pack.repeat_limit,
                    pack.notes,
                    pack.source,
                    pack.valuation_status,
                    pack.components_valued,
                ),
            )
            created += int(cursor.rowcount == 1)
            result[pack.pack_id] = int(
                connection.execute(
                    "SELECT id FROM cash_packs WHERE source_snapshot_id=? AND source_row=?",
                    (snapshot_id, pack.source_row),
                ).fetchone()[0]
            )
        return result, created

    def _store_components(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        snapshot_id: int,
        pack_ids: dict[str, int],
        item_ids: dict[str, int],
    ) -> int:
        created = 0
        for component in workbook.pack_components:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO cash_pack_components (
                    source_snapshot_id, source_sheet, source_row, cash_pack_id, item_id, normalized_quantity,
                    notes, actual_package_item_id, actual_package_item_text, actual_item_count, base_units_per_item,
                    normalized_quantity_check, speedup_type, data_status, package_display, normalization_check
                ) VALUES (?, 'PACK CONTENTS', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot_id,
                    component.source_row,
                    pack_ids[component.pack_id],
                    item_ids[component.item_name],
                    component.normalized_quantity,
                    component.notes,
                    item_ids.get(component.actual_package_item or ""),
                    component.actual_package_item,
                    component.actual_item_count,
                    component.base_units_per_item,
                    component.normalized_quantity_check,
                    component.speedup_type,
                    component.data_status,
                    component.package_display,
                    component.normalization_check,
                ),
            )
            created += int(cursor.rowcount == 1)
        return created

    def _store_model_observations(
        self,
        connection: sqlite3.Connection,
        workbook: ShopDoctorWorkbook,
        snapshot_id: int,
    ) -> int:
        created = 0
        for subject, metric, value, row in workbook.model_observations:
            created += self._insert_model(
                connection,
                snapshot_id,
                "offer",
                subject,
                metric,
                value,
                "CALC ENGINE",
                row,
            )
        return created

    def _insert_model(
        self,
        connection: sqlite3.Connection,
        snapshot_id: int,
        subject_type: str,
        subject_key: str,
        metric: str,
        value: float | str | None,
        sheet: str,
        row: int,
    ) -> int:
        number = value if isinstance(value, float) else None
        text = value if isinstance(value, str) else None
        cursor = connection.execute(
            "INSERT OR IGNORE INTO economic_model_observations (source_snapshot_id, subject_type, subject_key, metric, numeric_value, text_value, status, source_sheet, source_row) VALUES (?, ?, ?, ?, ?, ?, 'WORKBOOK_MODEL', ?, ?)",
            (snapshot_id, subject_type, subject_key, metric, number, text, sheet, row),
        )
        return int(cursor.rowcount == 1)

    def _store_research_bridges(
        self, connection: sqlite3.Connection, item_ids: dict[str, int], snapshot_id: int
    ) -> None:
        bridge = {
            "farms": "Grain",
            "lumber": "Timber",
            "herbs": "Herbs",
            "study_scroll": "Study Scroll",
        }
        for source_key, item_name in bridge.items():
            connection.execute(
                "INSERT OR IGNORE INTO item_domain_keys (domain, source_key, item_id, source_snapshot_id, notes) VALUES ('research_cost', ?, ?, ?, 'Explicit Doctor identity bridge; source research vocabulary is retained')",
                (source_key, item_ids[item_name], snapshot_id),
            )


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_ECONOMIC_SCHEMA = """
CREATE TABLE IF NOT EXISTS source_snapshots (
    id INTEGER PRIMARY KEY, source_name TEXT NOT NULL, filename TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE, size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
    sheet_names_json TEXT NOT NULL, snapshot_date TEXT NOT NULL, ingested_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY, canonical_key TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
    base_unit TEXT NOT NULL, category TEXT, item_type TEXT, data_status TEXT,
    source_text TEXT, notes TEXT, doctor_resource_key TEXT,
    first_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),
    last_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),
    first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS item_aliases (
    id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    alias TEXT NOT NULL, alias_key TEXT NOT NULL, source_terminology TEXT NOT NULL,
    source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id), source_row INTEGER NOT NULL,
    UNIQUE(item_id, alias_key)
);
CREATE TABLE IF NOT EXISTS item_domain_keys (
    id INTEGER PRIMARY KEY, domain TEXT NOT NULL, source_key TEXT NOT NULL,
    item_id INTEGER NOT NULL REFERENCES items(id), source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),
    notes TEXT, UNIQUE(domain, source_key)
);
CREATE TABLE IF NOT EXISTS shops (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id));
CREATE TABLE IF NOT EXISTS currencies (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, kind TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS currency_valuation_assumptions (
    id INTEGER PRIMARY KEY, source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),
    currency_id INTEGER NOT NULL REFERENCES currencies(id), value_per_unit REAL,
    classification TEXT NOT NULL, basis TEXT, active TEXT, notes TEXT, source_sheet TEXT NOT NULL, source_row INTEGER NOT NULL,
    UNIQUE(source_snapshot_id, currency_id, source_row)
);
CREATE TABLE IF NOT EXISTS choice_groups (
    id INTEGER PRIMARY KEY, source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),
    container_item_id INTEGER NOT NULL REFERENCES items(id), context TEXT, contents_rule TEXT NOT NULL,
    source_sheet TEXT NOT NULL, source_row INTEGER NOT NULL,
    UNIQUE(source_snapshot_id, container_item_id, source_row)
);
CREATE TABLE IF NOT EXISTS choice_options (
    id INTEGER PRIMARY KEY, choice_group_id INTEGER NOT NULL REFERENCES choice_groups(id) ON DELETE CASCADE,
    option_index INTEGER NOT NULL, option_item_id INTEGER NOT NULL REFERENCES items(id), quantity REAL NOT NULL CHECK(quantity > 0),
    UNIQUE(choice_group_id, option_index)
);
CREATE TABLE IF NOT EXISTS offer_observations (
    id INTEGER PRIMARY KEY, source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),
    source_sheet TEXT NOT NULL, source_row INTEGER NOT NULL, original_offer_id TEXT NOT NULL,
    active TEXT, date_seen TEXT NOT NULL, shop_id INTEGER NOT NULL REFERENCES shops(id), shop_snapshot_id TEXT NOT NULL,
    item_id INTEGER NOT NULL REFERENCES items(id), normalized_quantity REAL NOT NULL CHECK(normalized_quantity > 0),
    cost REAL NOT NULL CHECK(cost >= 0), currency_id INTEGER NOT NULL REFERENCES currencies(id), direct_cash_price REAL,
    repeat_limit REAL, notes TEXT, source_text TEXT, actual_package_item_id INTEGER REFERENCES items(id),
    actual_package_item_text TEXT, actual_item_count REAL, base_units_per_item REAL, normalized_quantity_check REAL,
    speedup_type TEXT, package_display TEXT, choice_group_id INTEGER REFERENCES choice_groups(id),
    UNIQUE(source_snapshot_id, source_sheet, source_row)
);
CREATE TABLE IF NOT EXISTS cash_packs (
    id INTEGER PRIMARY KEY, source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id), source_sheet TEXT NOT NULL,
    source_row INTEGER NOT NULL, original_pack_id TEXT NOT NULL, active TEXT, date_seen TEXT NOT NULL, name TEXT NOT NULL,
    price_usd REAL, assumed_bonus_diamonds INTEGER, bonus_diamonds_status TEXT NOT NULL, snapshot_label TEXT NOT NULL,
    repeat_limit REAL, notes TEXT, source_text TEXT, valuation_status TEXT, components_valued TEXT,
    UNIQUE(source_snapshot_id, source_sheet, source_row)
);
CREATE TABLE IF NOT EXISTS cash_pack_components (
    id INTEGER PRIMARY KEY, source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id), source_sheet TEXT NOT NULL,
    source_row INTEGER NOT NULL, cash_pack_id INTEGER NOT NULL REFERENCES cash_packs(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id), normalized_quantity REAL NOT NULL CHECK(normalized_quantity > 0), notes TEXT,
    actual_package_item_id INTEGER REFERENCES items(id), actual_package_item_text TEXT, actual_item_count REAL,
    base_units_per_item REAL, normalized_quantity_check REAL, speedup_type TEXT, data_status TEXT,
    package_display TEXT, normalization_check TEXT,
    UNIQUE(source_snapshot_id, source_sheet, source_row)
);
CREATE TABLE IF NOT EXISTS economic_model_observations (
    id INTEGER PRIMARY KEY, source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id), subject_type TEXT NOT NULL,
    subject_key TEXT NOT NULL, metric TEXT NOT NULL, numeric_value REAL, text_value TEXT, status TEXT NOT NULL,
    source_sheet TEXT NOT NULL, source_row INTEGER NOT NULL,
    UNIQUE(source_snapshot_id, subject_type, subject_key, metric, source_sheet, source_row)
);
CREATE INDEX IF NOT EXISTS idx_economic_offer_item ON offer_observations(item_id, date_seen);
CREATE INDEX IF NOT EXISTS idx_economic_alias_key ON item_aliases(alias_key);
CREATE INDEX IF NOT EXISTS idx_economic_components_item ON cash_pack_components(item_id);
"""
