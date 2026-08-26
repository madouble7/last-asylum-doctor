"""Network-independent tests for factual research SQLite persistence."""

import sqlite3
from dataclasses import replace

import pytest

from last_asylum_doctor.database import ResearchDatabase
from last_asylum_doctor.models import (
    ResearchCost,
    ResearchLevel,
    ResearchNode,
    RetrievalMetadata,
)


def test_initialization_enables_foreign_keys_and_creates_schema(tmp_path) -> None:
    database_path = tmp_path / "facts.db"

    with ResearchDatabase(database_path) as database:
        assert database.connection is not None
        assert database.connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert database.table_counts() == {
            "research_nodes": 0,
            "research_levels": 0,
            "research_level_costs": 0,
            "research_source_observations": 0,
            "ingestion_runs": 0,
        }
        with pytest.raises(sqlite3.IntegrityError):
            database.connection.execute(
                """
                INSERT INTO research_levels (
                    research_node_id, level, power, research_time_seconds, time_source
                ) VALUES (999, 1, 1, 1, '1s')
                """
            )

    assert database_path.exists()


def test_generic_costs_and_repeated_ingestion_are_idempotent(tmp_path) -> None:
    node = _node()

    with ResearchDatabase(tmp_path / "facts.db") as database:
        first = database.store_research_nodes([node], [node.slug])
        first_counts = database.table_counts()
        second = database.store_research_nodes([node], [node.slug])
        second_counts = database.table_counts()

        stored = database.get_research(node.slug)

    assert first.status == "completed"
    assert second.status == "completed"
    assert first_counts == {
        "research_nodes": 1,
        "research_levels": 2,
        "research_level_costs": 3,
        "research_source_observations": 1,
        "ingestion_runs": 1,
    }
    assert second_counts == {
        "research_nodes": 1,
        "research_levels": 2,
        "research_level_costs": 3,
        "research_source_observations": 2,
        "ingestion_runs": 2,
    }
    assert stored is not None
    assert stored["levels"][0]["costs"] == [
        {
            "resource_identifier": "farms",
            "source_label": "Farms",
            "amount": 31_736_000,
            "item_id": None,
            "source_amount": "31736000",
        },
        {
            "resource_identifier": "study_scroll",
            "source_label": "Study Scroll",
            "amount": 1_440,
            "item_id": "item_research_info",
            "source_amount": "1440",
        },
    ]


def test_changed_facts_update_current_rows_and_keep_provenance(tmp_path) -> None:
    original = _node()
    changed = _node(power=15_021, farms=31_736_001, checksum="b" * 64)

    with ResearchDatabase(tmp_path / "facts.db") as database:
        database.store_research_nodes([original], [original.slug])
        database.store_research_nodes([changed], [changed.slug])
        stored = database.get_research(changed.slug)
        counts = database.table_counts()

    assert stored is not None
    assert stored["levels"][0]["power"] == 15_021
    assert stored["levels"][0]["costs"][0]["amount"] == 31_736_001
    assert stored["latest_source_observation"]["content_sha256"] == "b" * 64
    assert counts["research_nodes"] == 1
    assert counts["research_levels"] == 2
    assert counts["research_level_costs"] == 3
    assert counts["research_source_observations"] == 2


def _node(
    *,
    power: int = 15_020,
    farms: int = 31_736_000,
    checksum: str = "a" * 64,
) -> ResearchNode:
    costs_level_one = (
        ResearchCost(
            resource="farms",
            source_label="Farms",
            amount=farms,
            source_amount=str(farms),
        ),
        ResearchCost(
            resource="study_scroll",
            source_label="Study Scroll",
            amount=1_440,
            item_id="item_research_info",
            source_amount="1440",
        ),
    )
    level_one = ResearchLevel(
        research_id="11022",
        research_slug="def-boost-iii",
        source_record_id=11_022_001,
        level=1,
        time_source="11d 3h 46m 40s",
        time_seconds=964_000,
        power=power,
        costs={cost.resource: cost.amount for cost in costs_level_one},
        source_costs=costs_level_one,
    )
    level_two_cost = ResearchCost(
        resource="study_scroll",
        source_label="Study Scroll",
        amount=1_600,
        item_id="item_research_info",
        source_amount="1600",
    )
    level_two = replace(
        level_one,
        source_record_id=11_022_002,
        level=2,
        time_source="13d 10h 13m 20s",
        time_seconds=1_160_000,
        power=34_510,
        costs={level_two_cost.resource: level_two_cost.amount},
        source_costs=(level_two_cost,),
    )
    return ResearchNode(
        research_id="11022",
        slug="def-boost-iii",
        name="DEF Boost III",
        tree="Elite Troop",
        tree_slug="elite-troop",
        effect="Soldier DEF",
        max_level=2,
        levels=(level_one, level_two),
        source_page_url="https://example.test/science/def-boost-iii",
        source_asset_url="https://example.test/assets/def-boost-iii-Hash.js",
        retrieval=RetrievalMetadata(
            source_url="https://example.test/assets/def-boost-iii-Hash.js",
            retrieved_at="2026-08-26T00:00:00+00:00",
            sha256=checksum,
            etag='"test"',
        ),
        tech_type=11,
    )
