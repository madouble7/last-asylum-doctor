"""Tests for the starter package and command-line entry point."""

from pathlib import Path

import last_asylum_doctor
from last_asylum_doctor.cli import main
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
