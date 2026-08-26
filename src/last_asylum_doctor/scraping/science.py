"""Targeted LastAsylumDatabase.com science ingestion pipeline."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from last_asylum_doctor.models import (
    ResearchCost,
    ResearchLevel,
    ResearchNode,
    ResearchValidationError,
    RetrievalMetadata,
    validate_research_node,
)

from .client import DEFAULT_USER_AGENT, CachedHttpClient
from .discovery import (
    SourceDiscoveryError,
    discover_main_bundle,
    discover_science_asset_urls,
    discover_science_pages,
    ensure_robots_allowed,
    validate_slug,
)
from .esm import ModuleParseError, parse_research_module

DEFAULT_BASE_URL = "https://lastasylumdatabase.com/"
MAX_TARGETED_SLUGS = 25


class ScienceIngestionError(RuntimeError):
    """Raised when science data cannot be safely ingested."""


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Summary and data from one targeted ingestion run."""

    nodes: tuple[ResearchNode, ...]
    sitemap_science_slug_count: int
    output_path: Path
    main_bundle_url: str


class ScienceIngestor:
    """Discover and ingest only explicitly requested science nodes."""

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
        slugs: list[str],
        output_path: Path,
        *,
        refresh: bool = False,
    ) -> IngestionResult:
        """Ingest explicitly named slugs and write normalized sample JSON."""
        requested_slugs = _validate_requested_slugs(slugs)
        robots_url = urljoin(self.base_url, "robots.txt")
        science_url = urljoin(self.base_url, "science")
        sitemap_url = urljoin(self.base_url, "sitemap.xml")

        robots = self.client.fetch(robots_url, refresh=refresh)
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
        asset_urls = discover_science_asset_urls(main_bundle.text, main_bundle_url)
        page_urls = discover_science_pages(sitemap.text, self.base_url)

        nodes: list[ResearchNode] = []
        for slug in requested_slugs:
            if slug not in page_urls:
                raise ScienceIngestionError(
                    f"Science slug {slug!r} was not present in sitemap.xml"
                )
            asset_url = asset_urls.get(slug)
            if asset_url is None:
                raise ScienceIngestionError(
                    f"Science slug {slug!r} was not present in the main bundle map"
                )
            ensure_robots_allowed(
                robots.text, robots_url, self.user_agent, [asset_url]
            )
            asset = self.client.fetch(asset_url, refresh=refresh)
            try:
                payload = parse_research_module(asset.text)
                node = normalize_research_payload(
                    payload,
                    expected_slug=slug,
                    source_page_url=page_urls[slug],
                    source_asset_url=asset_url,
                    retrieval=asset.metadata,
                )
            except (ModuleParseError, ResearchValidationError, TypeError) as error:
                raise ScienceIngestionError(
                    f"Could not accept science data for {slug!r}: {error}"
                ) from error
            nodes.append(node)

        generated_at = datetime.now(timezone.utc).isoformat()
        output = {
            "schema_version": 1,
            "generated_at": generated_at,
            "source_site": self.base_url,
            "main_bundle_url": main_bundle_url,
            "sitemap_science_slug_count": len(page_urls),
            "nodes": [node.to_dict() for node in nodes],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return IngestionResult(
            nodes=tuple(nodes),
            sitemap_science_slug_count=len(page_urls),
            output_path=output_path,
            main_bundle_url=main_bundle_url,
        )


def normalize_research_payload(
    payload: dict[str, Any],
    *,
    expected_slug: str,
    source_page_url: str,
    source_asset_url: str,
    retrieval: RetrievalMetadata,
) -> ResearchNode:
    """Normalize one parsed source payload while preserving source semantics."""
    research_id = _required_text(payload, "id")
    slug = _required_text(payload, "slug")
    if slug != expected_slug:
        raise ResearchValidationError(
            f"Requested slug {expected_slug!r}, but module contained {slug!r}"
        )
    name = _required_text(payload, "name")
    effect = _required_text(payload, "description")
    tree = _required_text(payload, "tab")
    tree_slug = _required_text(payload, "tab_slug")
    max_level = _required_int(payload, "max_level")
    levels_count = _required_int(payload, "levels_count")
    if levels_count != max_level:
        raise ResearchValidationError(
            f"{slug}: source levels_count {levels_count} does not equal "
            f"max_level {max_level}"
        )

    raw_levels = payload.get("levels")
    if not isinstance(raw_levels, list):
        raise ResearchValidationError(f"{slug}: levels must be an array")
    levels = tuple(
        _normalize_level(research_id, slug, raw_level)
        for raw_level in raw_levels
    )

    node = ResearchNode(
        research_id=research_id,
        slug=slug,
        name=name,
        tree=tree,
        tree_slug=tree_slug,
        effect=effect,
        max_level=max_level,
        levels=levels,
        source_page_url=source_page_url,
        source_asset_url=source_asset_url,
        retrieval=retrieval,
        tech_type=_optional_int(payload, "tech_type"),
        image=_optional_text(payload, "image"),
        position=_optional_text(payload, "pos"),
    )
    validate_research_node(node)
    return node


def _normalize_level(
    research_id: str, slug: str, raw_level: object
) -> ResearchLevel:
    if not isinstance(raw_level, dict):
        raise ResearchValidationError(f"{slug}: each level must be an object")
    level_number = _required_int(raw_level, "level")
    raw_costs = raw_level.get("costs")
    if not isinstance(raw_costs, list):
        raise ResearchValidationError(
            f"{slug} level {level_number}: costs must be an array"
        )

    costs: dict[str, int] = {}
    source_costs: list[ResearchCost] = []
    for raw_cost in raw_costs:
        if not isinstance(raw_cost, dict):
            raise ResearchValidationError(
                f"{slug} level {level_number}: each cost must be an object"
            )
        source_label = _required_text(raw_cost, "resource")
        resource = _resource_identifier(source_label)
        amount = _required_int(raw_cost, "amount")
        if resource in costs:
            raise ResearchValidationError(
                f"{slug} level {level_number}: duplicate resource {resource!r}"
            )
        costs[resource] = amount
        source_costs.append(
            ResearchCost(
                resource=resource,
                source_label=source_label,
                amount=amount,
                item_id=_optional_text(raw_cost, "item_id"),
                source_amount=_optional_text(raw_cost, "amount_fmt"),
            )
        )

    return ResearchLevel(
        research_id=research_id,
        research_slug=slug,
        source_record_id=_optional_int(raw_level, "raw_id"),
        level=level_number,
        time_source=_required_text(raw_level, "time"),
        time_seconds=_required_int(raw_level, "time_sec"),
        power=_required_int(raw_level, "power"),
        costs=costs,
        source_costs=tuple(source_costs),
    )


def _validate_requested_slugs(slugs: list[str]) -> list[str]:
    if not slugs:
        raise ScienceIngestionError(
            "At least one explicit science slug is required; "
            "broad ingestion is disabled"
        )
    if len(slugs) > MAX_TARGETED_SLUGS:
        raise ScienceIngestionError(
            f"Targeted ingestion accepts at most {MAX_TARGETED_SLUGS} slugs"
        )
    result: list[str] = []
    seen: set[str] = set()
    for slug in slugs:
        try:
            valid_slug = validate_slug(slug)
        except SourceDiscoveryError as error:
            raise ScienceIngestionError(str(error)) from error
        if valid_slug in seen:
            raise ScienceIngestionError(f"Duplicate science slug: {valid_slug}")
        seen.add(valid_slug)
        result.append(valid_slug)
    return result


def _required_text(values: dict[str, Any], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ResearchValidationError(f"{key} must be non-blank text")
    return value


def _optional_text(values: dict[str, Any], key: str) -> str | None:
    value = values.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ResearchValidationError(f"{key} must be text when present")
    return value


def _required_int(values: dict[str, Any], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ResearchValidationError(f"{key} must be an integer")
    return value


def _optional_int(values: dict[str, Any], key: str) -> int | None:
    value = values.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ResearchValidationError(f"{key} must be an integer when present")
    return value


def _resource_identifier(source_label: str) -> str:
    identifier = re.sub(r"[^a-z0-9]+", "_", source_label.lower()).strip("_")
    if not identifier:
        raise ResearchValidationError(
            f"Cannot create a source-preserving identifier for {source_label!r}"
        )
    return identifier
