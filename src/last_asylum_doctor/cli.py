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
    build_science_corpus_profile,
    validate_research_corpus,
    write_science_corpus_profile,
)
from last_asylum_doctor.scraping import (
    CachedHttpClient,
    FullCorpusIngestionResult,
    IngestionResult,
    ScienceCorpusIngestor,
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
        if parsed.all_nodes and parsed.slugs:
            parser.error("--all cannot be combined with explicit science slugs")
        if not parsed.all_nodes and not parsed.slugs:
            parser.error("provide explicit science slugs or use --all")
        if parsed.all_nodes and not parsed.store_db:
            parser.error("full-corpus ingestion requires --store-db")
        if parsed.all_nodes:
            return _run_full_corpus_command(parsed)
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
        print(f"Ingested {len(result.nodes)} science node(s) to {result.output_path}")
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


def run_full_science_ingestion(
    *,
    output_path: Path,
    cache_dir: Path,
    refresh: bool,
) -> FullCorpusIngestionResult:
    """Run the deliberate all-node source retrieval path."""
    with CachedHttpClient(cache_dir) as client:
        return ScienceCorpusIngestor(client).ingest(output_path, refresh=refresh)


def _run_full_corpus_command(parsed: argparse.Namespace) -> int:
    """Retrieve, persist, validate, and profile the explicit full corpus."""
    try:
        result = run_full_science_ingestion(
            output_path=parsed.output,
            cache_dir=parsed.cache_dir,
            refresh=parsed.refresh,
        )
        failure_map = {failure.slug: failure.reason for failure in result.failures}
        with ResearchDatabase(parsed.database) as database:
            database_run = database.store_research_nodes(
                result.nodes, result.requested_slugs, failure_map
            )
            validation = validate_research_corpus(database)
            profile = build_science_corpus_profile(database, validation)
            write_science_corpus_profile(profile, parsed.profile_output)
    except (
        DatabaseError,
        OSError,
        ScienceIngestionError,
        SourceDiscoveryError,
        SourceFetchError,
    ) as error:
        print(f"Full science ingestion failed: {error}", file=sys.stderr)
        return 1

    _print_reconciliation(result)
    print(
        f"Full ingestion accepted {len(result.nodes)} of "
        f"{len(result.requested_slugs)} science node(s); "
        f"{len(result.failures)} failed"
    )
    for failure in result.failures:
        print(f"Failed {failure.slug}: {failure.reason}", file=sys.stderr)
    print(
        f"Stored factual data in {parsed.database} "
        f"(ingestion run {database_run.run_id}; {database_run.status}; "
        f"{database_run.succeeded_count} succeeded, "
        f"{database_run.failed_count} failed)"
    )
    print(
        "Source content changes: "
        f"{database_run.new_source_count} new, "
        f"{database_run.changed_source_count} changed, "
        f"{database_run.unchanged_source_count} unchanged"
    )
    print(f"Wrote normalized corpus to {result.output_path}")
    print(f"Wrote corpus profile to {parsed.profile_output}")
    print(f"Corpus validation: {'passed' if validation['valid'] else 'failed'}")
    return 0 if not result.failures and validation["valid"] else 1


def _print_reconciliation(result: FullCorpusIngestionResult) -> None:
    reconciliation = result.reconciliation
    print(f"Sitemap science slugs: {reconciliation.sitemap_science_slug_count}")
    print(f"Import-map science slugs: {reconciliation.import_map_science_slug_count}")
    print(f"Usable intersection: {reconciliation.intersection_count}")
    print(
        "Sitemap-only slugs: "
        + (", ".join(reconciliation.sitemap_only_slugs) or "(none)")
    )
    print(
        "Import-map-only slugs: "
        + (", ".join(reconciliation.import_map_only_slugs) or "(none)")
    )


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
        help="ingest explicit research slugs or the deliberate full corpus",
    )
    ingest.add_argument(
        "slugs",
        nargs="*",
        help="explicit science slugs; omitted only when --all is provided",
    )
    ingest.add_argument(
        "--all",
        dest="all_nodes",
        action="store_true",
        help=(
            "explicitly ingest the reconciled full science corpus "
            "(requires --store-db)"
        ),
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
    ingest.add_argument(
        "--profile-output",
        type=Path,
        default=Path("data/processed/science_corpus_profile.json"),
        help="generated factual profile path used with --all",
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
