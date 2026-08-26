"""Command-line entry point for Last Asylum Doctor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from last_asylum_doctor.scraping import (
    CachedHttpClient,
    IngestionResult,
    ScienceIngestionError,
    ScienceIngestor,
    SourceFetchError,
)
from last_asylum_doctor.scraping.discovery import SourceDiscoveryError


def main(argv: Sequence[str] | None = None) -> int:
    """Run a targeted command or print the starter status message."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        print("Last Asylum Doctor is alive.")
        return 0

    parser = _build_parser()
    parsed = parser.parse_args(arguments)
    if parsed.command == "ingest-science":
        try:
            result = run_science_ingestion(
                parsed.slugs,
                output_path=parsed.output,
                cache_dir=parsed.cache_dir,
                refresh=parsed.refresh,
            )
        except (
            OSError,
            ScienceIngestionError,
            SourceDiscoveryError,
            SourceFetchError,
        ) as error:
            print(f"Science ingestion failed: {error}", file=sys.stderr)
            return 1
        print(
            f"Ingested {len(result.nodes)} science node(s) to "
            f"{result.output_path}"
        )
        print(f"Sitemap science slugs: {result.sitemap_science_slug_count}")
        return 0
    parser.error("A command is required")


def run_science_ingestion(
    slugs: list[str],
    *,
    output_path: Path,
    cache_dir: Path,
    refresh: bool,
) -> IngestionResult:
    """Run targeted science ingestion with the production HTTP client."""
    with CachedHttpClient(cache_dir) as client:
        return ScienceIngestor(client).ingest(
            slugs, output_path=output_path, refresh=refresh
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="last-asylum-doctor")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser(
        "ingest-science",
        help="ingest only explicitly listed research slugs",
    )
    ingest.add_argument(
        "slugs",
        nargs="+",
        help="one or more explicit science slugs; there is no crawl-all default",
    )
    ingest.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/research_sample.json"),
        help="normalized JSON output path",
    )
    ingest.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/raw/http"),
        help="raw content-addressed HTTP cache directory",
    )
    ingest.add_argument(
        "--refresh",
        action="store_true",
        help="refresh source responses instead of using a recent cache entry",
    )
    return parser
