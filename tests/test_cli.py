"""Tests for the starter package and command-line entry point."""

from pathlib import Path

import pytest

import last_asylum_doctor
from last_asylum_doctor.cli import main
from last_asylum_doctor.models import (
    ResearchLevel,
    ResearchNode,
    RetrievalMetadata,
)
from last_asylum_doctor.scraping.audit import ScienceSchemaAuditResult
from last_asylum_doctor.scraping.science import IngestionResult


def test_package_imports() -> None:
    """The package can be imported."""
    assert last_asylum_doctor is not None


def test_entry_point_prints_status(capsys) -> None:
    """The entry point prints its expected starter message."""
    assert main([]) == 0

    assert capsys.readouterr().out == "Last Asylum Doctor is alive.\n"


def test_targeted_cli_passes_only_explicit_slugs(monkeypatch, capsys, tmp_path) -> None:
    received: dict[str, object] = {}

    def fake_run(
        slugs: list[str],
        *,
        output_path: Path,
        cache_dir: Path,
        refresh: bool,
    ) -> IngestionResult:
        received.update(
            slugs=slugs,
            output_path=output_path,
            cache_dir=cache_dir,
            refresh=refresh,
        )
        return IngestionResult(
            nodes=(),
            sitemap_science_slug_count=348,
            output_path=output_path,
            main_bundle_url="https://example.test/assets/index-Hash.js",
        )

    monkeypatch.setattr("last_asylum_doctor.cli.run_science_ingestion", fake_run)
    output = tmp_path / "sample.json"

    exit_code = main(
        [
            "ingest-science",
            "def-boost-iii",
            "training-points",
            "--output",
            str(output),
            "--refresh",
        ]
    )

    assert exit_code == 0
    assert received["slugs"] == ["def-boost-iii", "training-points"]
    assert received["output_path"] == output
    assert received["refresh"] is True
    assert "Sitemap science slugs: 348" in capsys.readouterr().out


def test_full_corpus_mode_requires_explicit_all_and_database() -> None:
    with pytest.raises(SystemExit, match="2"):
        main(["ingest-science"])
    with pytest.raises(SystemExit, match="2"):
        main(["ingest-science", "--all"])
    with pytest.raises(SystemExit, match="2"):
        main(["ingest-science", "def-boost-iii", "--all", "--store-db"])


def test_cli_can_initialize_store_and_show_factual_data(
    monkeypatch, capsys, tmp_path
) -> None:
    database_path = tmp_path / "facts.db"
    output_path = tmp_path / "sample.json"
    node = _cli_node()

    assert main(["init-db", "--database", str(database_path)]) == 0
    assert "Initialized factual research database" in capsys.readouterr().out

    def fake_run(
        slugs: list[str],
        *,
        output_path: Path,
        cache_dir: Path,
        refresh: bool,
    ) -> IngestionResult:
        del slugs, cache_dir, refresh
        return IngestionResult(
            nodes=(node,),
            sitemap_science_slug_count=348,
            output_path=output_path,
            main_bundle_url="https://example.test/assets/index-Hash.js",
        )

    monkeypatch.setattr("last_asylum_doctor.cli.run_science_ingestion", fake_run)
    assert (
        main(
            [
                "ingest-science",
                node.slug,
                "--output",
                str(output_path),
                "--store-db",
                "--database",
                str(database_path),
            ]
        )
        == 0
    )
    assert "Stored factual data" in capsys.readouterr().out

    assert main(["show-research", node.slug, "--database", str(database_path)]) == 0
    output = capsys.readouterr().out
    assert '"slug": "sample"' in output
    assert '"power": 15020' in output
    assert "recommend" not in output.lower()


def test_cli_runs_bounded_schema_audit(monkeypatch, capsys, tmp_path) -> None:
    output_path = tmp_path / "science_schema_audit.json"
    received: dict[str, object] = {}

    def fake_run(
        *,
        output_path: Path,
        cache_dir: Path,
        sample_size: int,
        refresh: bool,
    ) -> ScienceSchemaAuditResult:
        received.update(
            output_path=output_path,
            cache_dir=cache_dir,
            sample_size=sample_size,
            refresh=refresh,
        )
        return ScienceSchemaAuditResult(
            sampled_slugs=("def-boost-iii", "training-points", "sample"),
            successful_parse_count=3,
            failed_parse_count=0,
            output_path=output_path,
            sitemap_science_slug_count=348,
        )

    monkeypatch.setattr("last_asylum_doctor.cli.run_science_schema_audit", fake_run)
    assert (
        main(
            [
                "audit-science-schema",
                "--sample-size",
                "3",
                "--output",
                str(output_path),
                "--refresh",
            ]
        )
        == 0
    )

    assert received["sample_size"] == 3
    assert received["refresh"] is True
    assert (
        "Audited 3 science module(s): 3 succeeded, 0 failed"
        in capsys.readouterr().out
    )


def _cli_node() -> ResearchNode:
    level = ResearchLevel(
        research_id="1",
        research_slug="sample",
        source_record_id=1,
        level=1,
        time_source="1s",
        time_seconds=1,
        power=15_020,
        costs={},
        source_costs=(),
    )
    return ResearchNode(
        research_id="1",
        slug="sample",
        name="Sample",
        tree="Test",
        tree_slug="test",
        effect="Test effect",
        max_level=1,
        levels=(level,),
        source_page_url="https://example.test/science/sample",
        source_asset_url="https://example.test/assets/sample.js",
        retrieval=RetrievalMetadata(
            source_url="https://example.test/assets/sample.js",
            retrieved_at="2026-08-26T00:00:00+00:00",
            sha256="a" * 64,
        ),
    )
