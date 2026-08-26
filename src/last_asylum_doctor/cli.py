"""Command-line entry point for Last Asylum Doctor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from last_asylum_doctor.database import (
    DatabaseError,
    IngestionRunSummary,
    ResearchDatabase,
)
from last_asylum_doctor.scraping import (
    CachedHttpClient,
    IngestionResult,
    ScienceIngestionError,
    ScienceIngestor,
    SourceFetchError,
)
from last_asylum_doctor.scraping.audit import (
    DEFAULT_AUDIT_SAMPLE_SIZE,
    ScienceAuditError,
    ScienceSchemaAuditor,
    ScienceSchemaAuditResult,
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
            database_run = None
            if parsed.store_db:
                database_run = store_ingested_research(
                    result,
                    requested_slugs=parsed.slugs,
                    database_path=parsed.database,
                )
        except (
            DatabaseError,
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
        if database_run is not None:
            print(
                f"Stored factual data in {parsed.database} "
                f"(ingestion run {database_run.run_id}; "
                f"{database_run.succeeded_count} node(s))"
            )
        return 0
    if parsed.command == "init-db":
        try:
            with ResearchDatabase(parsed.database):
                pass
        except (DatabaseError, OSError) as error:
            print(f"Database initialization failed: {error}", file=sys.stderr)
            return 1
        print(f"Initialized factual research database at {parsed.database}")
        return 0
    if parsed.command == "show-research":
        if not parsed.database.exists():
            print(
                f"Database does not exist: {parsed.database}. Run init-db first.",
                file=sys.stderr,
            )
            return 1
        try:
            with ResearchDatabase(parsed.database) as database:
                research = database.get_research(parsed.slug)
        except (DatabaseError, OSError) as error:
            print(f"Could not read factual research data: {error}", file=sys.stderr)
            return 1
        if research is None:
            print(f"Research slug not found: {parsed.slug}", file=sys.stderr)
            return 1
        print(json.dumps(research, indent=2, ensure_ascii=False))
        return 0
    if parsed.command == "audit-science-schema":
        try:
            result = run_science_schema_audit(
                output_path=parsed.output,
                cache_dir=parsed.cache_dir,
                sample_size=parsed.sample_size,
                refresh=parsed.refresh,
            )
        except (
            OSError,
            ScienceAuditError,
            SourceDiscoveryError,
            SourceFetchError,
        ) as error:
            print(f"Science schema audit failed: {error}", file=sys.stderr)
            return 1
        print(
            f"Audited {len(result.sampled_slugs)} science module(s): "
            f"{result.successful_parse_count} succeeded, "
            f"{result.failed_parse_count} failed"
        )
        print(f"Sitemap science slugs: {result.sitemap_science_slug_count}")
        print(f"Wrote schema audit to {result.output_path}")
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


def store_ingested_research(
    result: IngestionResult,
    *,
    requested_slugs: list[str],
    database_path: Path,
) -> IngestionRunSummary:
    """Store a successful targeted ingestion as factual SQLite records."""
    with ResearchDatabase(database_path) as database:
        return database.store_research_nodes(result.nodes, requested_slugs)


def run_science_schema_audit(
    *,
    output_path: Path,
    cache_dir: Path,
    sample_size: int,
    refresh: bool,
) -> ScienceSchemaAuditResult:
    """Run a bounded science schema audit without SQLite storage."""
    with CachedHttpClient(cache_dir) as client:
        return ScienceSchemaAuditor(client).audit(
            output_path,
            sample_size=sample_size,
            refresh=refresh,
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
    ingest.add_argument(
        "--store-db",
        action="store_true",
        help="also store normalized factual records in SQLite",
    )
    ingest.add_argument(
        "--database",
        type=Path,
        default=Path("data/last_asylum.db"),
        help="SQLite database path used with --store-db",
    )
    init_db = commands.add_parser(
        "init-db",
        help="initialize the factual research SQLite database",
    )
    init_db.add_argument(
        "--database",
        type=Path,
        default=Path("data/last_asylum.db"),
        help="SQLite database path",
    )
    show = commands.add_parser(
        "show-research",
        help="print factual stored research data as JSON",
    )
    show.add_argument("slug", help="stored research slug to inspect")
    show.add_argument(
        "--database",
        type=Path,
        default=Path("data/last_asylum.db"),
        help="SQLite database path",
    )
    audit = commands.add_parser(
        "audit-science-schema",
        help="profile a bounded, representative science-module sample",
    )
    audit.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_AUDIT_SAMPLE_SIZE,
        help="number of detailed science modules to audit (3 through 30)",
    )
    audit.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/science_schema_audit.json"),
        help="generated JSON audit output path",
    )
    audit.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/raw/http"),
        help="raw content-addressed HTTP cache directory",
    )
    audit.add_argument(
        "--refresh",
        action="store_true",
        help="refresh source responses instead of using a recent cache entry",
    )
    return parser
