"""Explicit, respectful full-corpus science ingestion."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from last_asylum_doctor.models import ResearchNode, ResearchValidationError

from .client import DEFAULT_USER_AGENT, CachedHttpClient, SourceFetchError
from .discovery import (
    SourceDiscoveryError,
    discover_main_bundle,
    discover_science_asset_urls,
    discover_science_pages,
    ensure_robots_allowed,
)
from .esm import ModuleParseError, parse_research_module
from .science import DEFAULT_BASE_URL, normalize_research_payload


@dataclass(frozen=True, slots=True)
class ScienceCorpusReconciliation:
    """The evidence-based overlap between public pages and import mappings."""

    sitemap_science_slug_count: int
    import_map_science_slug_count: int
    intersection_count: int
    sitemap_only_slugs: tuple[str, ...]
    import_map_only_slugs: tuple[str, ...]
    main_bundle_url: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable reconciliation report."""
        return {
            "sitemap_science_slug_count": self.sitemap_science_slug_count,
            "import_map_science_slug_count": self.import_map_science_slug_count,
            "intersection_count": self.intersection_count,
            "sitemap_only_slugs": list(self.sitemap_only_slugs),
            "import_map_only_slugs": list(self.import_map_only_slugs),
            "main_bundle_url": self.main_bundle_url,
        }


@dataclass(frozen=True, slots=True)
class ScienceCorpusFailure:
    """One node that was discovered but could not become a verified fact."""

    slug: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"slug": self.slug, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class FullCorpusIngestionResult:
    """The accepted nodes and explicit failures from one full-corpus retrieval."""

    nodes: tuple[ResearchNode, ...]
    requested_slugs: tuple[str, ...]
    failures: tuple[ScienceCorpusFailure, ...]
    reconciliation: ScienceCorpusReconciliation
    output_path: Path


class ScienceCorpusIngestor:
    """Ingest every currently reconcilable science node, sequentially."""

    def __init__(
        self,
        client: CachedHttpClient,
        *,
        base_url: str = DEFAULT_BASE_URL,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/") + "/"
        self.user_agent = user_agent

    def ingest(
        self,
        output_path: Path,
        *,
        refresh: bool = False,
    ) -> FullCorpusIngestionResult:
        """Reconcile sources, then accept every individually valid node.

        A malformed or unavailable detailed module is reported and does not erase
        already validated nodes. Discovery and robots failures remain run-stopping
        because they make the scope unsafe or unknowable.
        """
        robots_url = urljoin(self.base_url, "robots.txt")
        science_url = urljoin(self.base_url, "science")
        sitemap_url = urljoin(self.base_url, "sitemap.xml")

        # Always re-check the access policy at the beginning of a broad run.
        robots = self.client.fetch(robots_url, refresh=True)
        ensure_robots_allowed(
            robots.text,
            robots_url,
            self.user_agent,
            [science_url, sitemap_url],
        )
        science_page = self.client.fetch(science_url, refresh=refresh)
        sitemap = self.client.fetch(sitemap_url, refresh=refresh)
        main_bundle_url = discover_main_bundle(science_page.text, science_url)
        ensure_robots_allowed(
            robots.text, robots_url, self.user_agent, [main_bundle_url]
        )
        main_bundle = self.client.fetch(main_bundle_url, refresh=refresh)
        page_urls = discover_science_pages(sitemap.text, self.base_url)
        asset_urls = discover_science_asset_urls(main_bundle.text, main_bundle_url)
        reconciliation = reconcile_science_sources(
            page_urls, asset_urls, main_bundle_url
        )
        requested_slugs = tuple(
            sorted(set(page_urls).intersection(asset_urls))
        )
        if not requested_slugs:
            raise SourceDiscoveryError(
                "Sitemap and main bundle contain no shared science slugs"
            )

        # Check all detailed asset paths before requesting any of them. A robots
        # denial stops the run rather than turning into a misleading partial result.
        ensure_robots_allowed(
            robots.text,
            robots_url,
            self.user_agent,
            [asset_urls[slug] for slug in requested_slugs],
        )

        nodes: list[ResearchNode] = []
        failures: list[ScienceCorpusFailure] = []
        for slug in requested_slugs:
            try:
                asset_url = asset_urls[slug]
                asset = self.client.fetch(asset_url, refresh=refresh)
                payload = parse_research_module(asset.text)
                nodes.append(
                    normalize_research_payload(
                        payload,
                        expected_slug=slug,
                        source_page_url=page_urls[slug],
                        source_asset_url=asset_url,
                        retrieval=asset.metadata,
                    )
                )
            except (
                ModuleParseError,
                ResearchValidationError,
                SourceFetchError,
                TypeError,
            ) as error:
                failures.append(ScienceCorpusFailure(slug, str(error)))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source_site": self.base_url,
                    "reconciliation": reconciliation.to_dict(),
                    "requested_slugs": list(requested_slugs),
                    "successful_nodes": [node.to_dict() for node in nodes],
                    "failures": [failure.to_dict() for failure in failures],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return FullCorpusIngestionResult(
            nodes=tuple(nodes),
            requested_slugs=requested_slugs,
            failures=tuple(failures),
            reconciliation=reconciliation,
            output_path=output_path,
        )


def reconcile_science_sources(
    page_urls: dict[str, str], asset_urls: dict[str, str], main_bundle_url: str
) -> ScienceCorpusReconciliation:
    """Make sitemap/import-map disagreement visible before corpus retrieval."""
    sitemap_slugs = set(page_urls)
    asset_slugs = set(asset_urls)
    return ScienceCorpusReconciliation(
        sitemap_science_slug_count=len(sitemap_slugs),
        import_map_science_slug_count=len(asset_slugs),
        intersection_count=len(sitemap_slugs.intersection(asset_slugs)),
        sitemap_only_slugs=tuple(sorted(sitemap_slugs.difference(asset_slugs))),
        import_map_only_slugs=tuple(sorted(asset_slugs.difference(sitemap_slugs))),
        main_bundle_url=main_bundle_url,
    )
