"""Typed factual models for Last Asylum research data."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


class ResearchValidationError(ValueError):
    """Raised when source data cannot form a valid research record."""


@dataclass(frozen=True, slots=True)
class RetrievalMetadata:
    """Provenance for one retrieved source response."""

    source_url: str
    retrieved_at: str
    sha256: str
    etag: str | None = None
    last_modified: str | None = None
    content_type: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchCost:
    """One source-preserving, resource-agnostic research cost."""

    resource: str
    source_label: str
    amount: int
    item_id: str | None = None
    source_amount: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchLevel:
    """The factual requirements and result for one research level."""

    research_id: str
    research_slug: str
    source_record_id: int | None
    level: int
    time_source: str
    time_seconds: int
    power: int
    costs: dict[str, int]
    source_costs: tuple[ResearchCost, ...]


@dataclass(frozen=True, slots=True)
class ResearchNode:
    """A normalized research node and all of its levels."""

    research_id: str
    slug: str
    name: str
    tree: str
    tree_slug: str
    effect: str
    max_level: int
    levels: tuple[ResearchLevel, ...]
    source_page_url: str
    source_asset_url: str
    retrieval: RetrievalMetadata
    tech_type: int | None = None
    image: str | None = None
    position: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def validate_research_node(node: ResearchNode) -> None:
    """Validate invariants without filling or guessing missing facts."""
    required_text = {
        "research_id": node.research_id,
        "slug": node.slug,
        "name": node.name,
        "tree": node.tree,
        "effect": node.effect,
        "source_page_url": node.source_page_url,
        "source_asset_url": node.source_asset_url,
    }
    blank_fields = [name for name, value in required_text.items() if not value.strip()]
    if blank_fields:
        raise ResearchValidationError(
            f"Required fields cannot be blank: {', '.join(blank_fields)}"
        )

    if node.max_level <= 0:
        raise ResearchValidationError("max_level must be positive")
    if len(node.levels) != node.max_level:
        raise ResearchValidationError(
            f"{node.slug}: expected {node.max_level} levels, got {len(node.levels)}"
        )

    actual_levels = [level.level for level in node.levels]
    expected_levels = list(range(1, node.max_level + 1))
    if actual_levels != expected_levels:
        raise ResearchValidationError(
            f"{node.slug}: levels must be contiguous 1..{node.max_level}; "
            f"got {actual_levels}"
        )

    for level in node.levels:
        if level.research_id != node.research_id:
            raise ResearchValidationError(
                f"{node.slug} level {level.level}: research ID does not match node"
            )
        if level.research_slug != node.slug:
            raise ResearchValidationError(
                f"{node.slug} level {level.level}: research slug does not match node"
            )
        if level.time_seconds < 0:
            raise ResearchValidationError(
                f"{node.slug} level {level.level}: time cannot be negative"
            )
        if level.power < 0:
            raise ResearchValidationError(
                f"{node.slug} level {level.level}: power cannot be negative"
            )
        for resource, amount in level.costs.items():
            if not resource:
                raise ResearchValidationError(
                    f"{node.slug} level {level.level}: resource cannot be blank"
                )
            if amount < 0:
                raise ResearchValidationError(
                    f"{node.slug} level {level.level}: {resource} cannot be negative"
                )
