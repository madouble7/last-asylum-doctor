"""Offline regressions for the read-only Shop Doctor pack oracle diff."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from last_asylum_doctor.database import EconomicDatabase
from last_asylum_doctor.economic import inspect_shop_doctor_workbook
from last_asylum_doctor.economic.oracle import (
    CanonicalEconomics,
    CanonicalItem,
    CanonicalPack,
    CanonicalPackComponent,
    ExternalItem,
    ExternalOracleSnapshot,
    ExternalPack,
    ExternalPackComponent,
    OracleError,
    compare_oracle,
    load_canonical_economics,
    load_fixture,
    open_read_only_database,
    render_report,
)
from tests.test_shop_doctor import _workbook


def test_fixture_snapshot_has_hash_schema_and_deterministic_metadata(
    tmp_path: Path,
) -> None:
    fixture = {
        "Item": [
            {
                "item_id": "StudyScroll",
                "item_name": "Study Scroll",
                "analysis_value": 999999,
                "created_date": "2026-03-20T00:00:00Z",
                "updated_date": "2026-03-21T00:00:00Z",
            }
        ],
        "ComplexItem": [],
        "Pack": [],
    }
    path = tmp_path / "oracle.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    snapshot = load_fixture(path)

    item_fetch = next(value for value in snapshot.fetches if value.entity == "Item")
    assert item_fetch.row_count == 1
    assert item_fetch.response_sha256
    assert item_fetch.schema_keys == (
        "analysis_value",
        "created_date",
        "item_id",
        "item_name",
        "updated_date",
    )
    assert item_fetch.oldest_source_timestamp == "2026-03-20T00:00:00Z"
    assert item_fetch.newest_source_timestamp == "2026-03-21T00:00:00Z"
    assert snapshot.items[0].name == "Study Scroll"


def test_oracle_gold_set_statuses_preserve_opaque_fields_and_nested_choices() -> None:
    canonical = _canonical()
    external = ExternalOracleSnapshot(
        items=(),
        complex_items=(),
        packs=(
            _pack(
                "Raven Gear",
                "gear-pack",
                [
                    ("Raven Gear", 3),
                    ("Raven Gear", 3),
                    ("Unrelated", 1),
                ],
                pack_price="999 Banknote",
            ),
            _pack(
                "Raven Essence",
                "essence-pack",
                [("Raven Essence", 20), ("Study Scroll", 10)],
            ),
            _pack("Study Scroll", "scroll-pack", [("Study Scroll", 60)]),
            _pack("Skill Badge Pack", "skill-pack", [("SkillBadge", 10)]),
            _pack("Curio Chest", "curio-pack", [("Curio Chest", 1)]),
        ),
        fetches=(),
    )

    result = compare_oracle(canonical, external)
    statuses = {value["name"]: value["status"] for value in result.pack_comparisons}

    assert statuses["Raven Gear"] == "EXACT_COMPONENT_MATCH"
    assert statuses["Raven Essence"] == "PROPORTIONAL_TIER_CANDIDATE"
    assert statuses["Study Scroll"] == "EXACT_COMPONENT_MATCH"
    assert statuses["Skill Badge Pack"] == "EXTERNAL_ONLY"
    assert statuses["Curio Chest"] == "EXTERNAL_ONLY"
    raven = next(
        value for value in result.pack_comparisons if value["name"] == "Raven Gear"
    )
    assert raven["pack_price"] == "999 Banknote"
    assert raven["price_interpretation"] is None


def test_alias_candidate_and_analysis_value_are_not_canonicalized() -> None:
    canonical = _canonical()
    external = ExternalOracleSnapshot(
        items=(ExternalItem("SkillBadge", "Skill Badge", (), ()),),
        complex_items=(),
        packs=(),
        fetches=(),
    )

    result = compare_oracle(canonical, external)

    assert result.item_comparisons[0]["status"] == "ALIAS_CANDIDATE"
    assert result.item_comparisons[0]["canonical_candidates"] == ["SkillBadge"]
    assert result.to_dict()["item_comparisons"][0].get("analysis_value") is None


def test_choice_and_complex_item_data_are_retained_without_analysis_value() -> None:
    canonical = _canonical()
    external = ExternalOracleSnapshot(
        items=(),
        complex_items=(),
        packs=(
            ExternalPack(
                "choice-pack",
                "Choice Pack",
                "Shop",
                42,
                "Default",
                None,
                (),
                ({"item_id": "RavenEssence", "amount": 20},),
                (),
            ),
        ),
        fetches=(),
    )

    result = compare_oracle(canonical, external)

    assert result.pack_comparisons[0]["choice_status"] == "UNKNOWN"
    assert external.packs[0].choice_items == (
        {"item_id": "RavenEssence", "amount": 20},
    )


def test_diff_reads_canonical_database_without_mutation(tmp_path: Path) -> None:
    workbook_path = _workbook(tmp_path / "shop_doctor.xlsx")
    database_path = tmp_path / "doctor.db"
    with EconomicDatabase(database_path) as database:
        database.store_shop_doctor(inspect_shop_doctor_workbook(workbook_path))
        before = database.economic_table_counts()
        canonical = load_canonical_economics(database.connection)
        compare_oracle(canonical, ExternalOracleSnapshot((), (), (), ()))
        after = database.economic_table_counts()

    assert before == after


def test_oracle_database_connection_rejects_writes_and_preserves_file(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "doctor.db"
    with EconomicDatabase(database_path):
        pass
    before_hash = _sha256(database_path)
    tables = (
        "items",
        "item_aliases",
        "cash_packs",
        "cash_pack_components",
        "choice_groups",
        "choice_options",
    )

    with open_read_only_database(database_path) as connection:
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        before_counts = {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in tables
        }
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("CREATE TABLE oracle_write_probe (id INTEGER)")

    with open_read_only_database(database_path) as connection:
        after_counts = {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in tables
        }
    assert before_counts == after_counts
    assert _sha256(database_path) == before_hash


def test_incomplete_oracle_schema_fails_without_migration(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE items (id INTEGER)")
    before_hash = _sha256(database_path)

    with pytest.raises(OracleError, match="missing tables"):
        with open_read_only_database(database_path):
            pass

    assert _sha256(database_path) == before_hash
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert tables == {"items"}


def test_report_is_deterministic() -> None:
    diff = compare_oracle(_canonical(), ExternalOracleSnapshot((), (), (), ()))
    assert render_report(diff) == render_report(diff)


def _canonical() -> CanonicalEconomics:
    items = (
        CanonicalItem("raven-gear", "Raven Gear", ()),
        CanonicalItem("raven-essence", "Raven Essence", ()),
        CanonicalItem("study-scroll", "Study Scroll", ()),
        CanonicalItem("skillbadge", "SkillBadge", ("Skill Badge",)),
        CanonicalItem("curio-shard", "Universal Curio Shard", ("Curio Shard",)),
    )
    return CanonicalEconomics(
        items=items,
        packs=(
            CanonicalPack(
                1,
                "raven-gear-pack",
                "Raven Gear",
                (
                    CanonicalPackComponent("raven-gear", "Raven Gear", 3, None, None),
                    CanonicalPackComponent("raven-gear", "Raven Gear", 3, None, None),
                ),
            ),
            CanonicalPack(
                2,
                "raven-essence-pack",
                "Raven Essence",
                (
                    CanonicalPackComponent(
                        "raven-essence", "Raven Essence", 40, None, None
                    ),
                    CanonicalPackComponent(
                        "study-scroll", "Study Scroll", 20, None, None
                    ),
                ),
            ),
            CanonicalPack(
                3,
                "study-scroll-pack",
                "Study Scroll",
                (
                    CanonicalPackComponent(
                        "study-scroll", "Study Scroll", 60, None, None
                    ),
                ),
            ),
        ),
        choices=(),
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pack(
    name: str,
    external_id: str,
    components: list[tuple[str, float]],
    *,
    pack_price: object = 999,
) -> ExternalPack:
    return ExternalPack(
        external_id=external_id,
        name=name,
        location="Pack Shop",
        pack_price=pack_price,
        pack_format="Default",
        note=None,
        components=tuple(
            ExternalPackComponent(item, item, "primitive", amount, 100, 0, None)
            for item, amount in components
        ),
        choice_items=(),
        source_timestamps=(),
    )
