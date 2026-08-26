"""Schema-compatibility profiling for a limited sample of science modules."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from last_asylum_doctor.models import ResearchValidationError

from .client import DEFAULT_USER_AGENT, CachedHttpClient
from .discovery import (
    discover_main_bundle,
    discover_science_asset_urls,
    discover_science_pages,
    ensure_robots_allowed,
)
from .esm import ModuleParseError, parse_research_module
from .science import DEFAULT_BASE_URL, normalize_research_payload

REQUIRED_AUDIT_SLUGS = (
    "def-boost-iii",
    "research-upgrade-iii",
    "training-points",
)
MAX_AUDIT_SAMPLE_SIZE = 30
DEFAULT_AUDIT_SAMPLE_SIZE = 25

_CATALOG = re.compile(
    r'''["']\.\./content/science_catalog\.json["']\s*:
        JSON\.parse\(\s*`(?P<catalog>.*?)`\s*\)''',
    re.VERBOSE | re.DOTALL,
)
_TOP_LEVEL_FIELD_CLASSIFICATIONS = {
    "id": ("A", "preserved as research_id"),
    "slug": ("A", "preserved as slug"),
    "name": ("A", "preserved as name"),
    "description": ("A", "preserved as effect"),
    "tab": ("A", "preserved as tree"),
    "tab_slug": ("A", "preserved as tree_slug"),
    "tech_type": ("A", "preserved as tech_type"),
    "max_level": ("A", "preserved as max_level"),
    "levels": ("A", "preserved as normalized ResearchLevel rows"),
    "image": ("A", "preserved as image"),
    "pos": ("A", "preserved as position"),
    "levels_count": ("B", "validated against max_level; redundant with levels"),
}
_LEVEL_FIELD_CLASSIFICATIONS = {
    "level": ("A", "preserved as level"),
    "raw_id": ("A", "preserved as source_record_id"),
    "time": ("A", "preserved as time_source"),
    "time_sec": ("A", "preserved as time_seconds"),
    "power": ("A", "preserved as power"),
    "costs": ("A", "preserved as generic ResearchCost rows"),
}
_COST_FIELD_CLASSIFICATIONS = {
    "resource": ("A", "preserved as source_label and mechanical resource ID"),
    "amount": ("A", "preserved as exact amount"),
    "item_id": ("A", "preserved when supplied"),
    "amount_fmt": ("A", "preserved as source_amount when supplied"),
}
_KNOWN_COST_ALIASES = {
    "cost_farms": "farms",
    "cost_lumber": "lumber",
    "cost_herbs": "herbs",
    "cost_food": "farms",
    "cost_wood": "lumber",
    "cost_iron": "herbs",
}


class ScienceAuditError(RuntimeError):
    """Raised when the bounded science schema audit cannot proceed safely."""


@dataclass(frozen=True, slots=True)
class ScienceSchemaAuditResult:
    """Result metadata for a completed bounded schema audit."""

    sampled_slugs: tuple[str, ...]
    successful_parse_count: int
    failed_parse_count: int
    output_path: Path
    sitemap_science_slug_count: int


class ScienceSchemaAuditor:
    """Profile source shapes without storing sampled records in SQLite."""

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

    def audit(
        self,
        output_path: Path,
        *,
        sample_size: int = DEFAULT_AUDIT_SAMPLE_SIZE,
        refresh: bool = False,
    ) -> ScienceSchemaAuditResult:
        """Audit no more than thirty deterministic, explicitly bounded modules."""
        if not len(REQUIRED_AUDIT_SLUGS) <= sample_size <= MAX_AUDIT_SAMPLE_SIZE:
            raise ScienceAuditError(
                f"sample_size must be between {len(REQUIRED_AUDIT_SLUGS)} and "
                f"{MAX_AUDIT_SAMPLE_SIZE}"
            )

        robots_url = urljoin(self.base_url, "robots.txt")
        science_url = urljoin(self.base_url, "science")
        sitemap_url = urljoin(self.base_url, "sitemap.xml")
        robots = self.client.fetch(robots_url, refresh=True)
        ensure_robots_allowed(
            robots.text, robots_url, self.user_agent, [science_url, sitemap_url]
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
        catalog, catalog_error = extract_science_catalog(main_bundle.text)
        sample = select_representative_sample(
            page_urls, asset_urls, catalog, sample_size=sample_size
        )

        node_reports: list[dict[str, Any]] = []
        for slug in sample:
            asset_url = asset_urls[slug]
            ensure_robots_allowed(
                robots.text, robots_url, self.user_agent, [asset_url]
            )
            asset = self.client.fetch(asset_url, refresh=refresh)
            node_reports.append(
                audit_module(
                    slug,
                    asset.text,
                    source_page_url=page_urls[slug],
                    source_asset_url=asset_url,
                    catalog_entry=catalog.get(slug),
                )
            )

        report = build_audit_report(
            node_reports,
            sample_method=(
                "required validation slugs; then deterministic tree medians from "
                "the embedded catalog; then evenly spaced sorted candidates"
            ),
            sitemap_science_slug_count=len(page_urls),
            main_bundle_url=main_bundle_url,
            catalog_error=catalog_error,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        failures = sum(node["status"] != "success" for node in node_reports)
        return ScienceSchemaAuditResult(
            sampled_slugs=tuple(sample),
            successful_parse_count=len(node_reports) - failures,
            failed_parse_count=failures,
            output_path=output_path,
            sitemap_science_slug_count=len(page_urls),
        )


def extract_science_catalog(
    bundle_source: str,
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Extract optional catalog metadata from the current Vite bundle."""
    match = _CATALOG.search(bundle_source)
    if match is None:
        return {}, "Embedded science catalog was not found in the main bundle"
    try:
        values = json.loads(match.group("catalog"))
    except json.JSONDecodeError as error:
        return {}, f"Embedded science catalog was not valid JSON: {error}"
    if not isinstance(values, list):
        return {}, "Embedded science catalog was not an array"
    catalog: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, dict) or not isinstance(value.get("slug"), str):
            return {}, "Embedded science catalog contained an invalid entry"
        catalog[value["slug"]] = value
    return catalog, None


def select_representative_sample(
    page_urls: dict[str, str],
    asset_urls: dict[str, str],
    catalog: dict[str, dict[str, Any]],
    *,
    sample_size: int,
) -> list[str]:
    """Select a stable bounded sample, favoring category coverage first."""
    candidates = sorted(set(page_urls).intersection(asset_urls))
    missing_required = sorted(set(REQUIRED_AUDIT_SLUGS).difference(candidates))
    if missing_required:
        raise ScienceAuditError(
            "Required audit slugs were unavailable: " + ", ".join(missing_required)
        )
    if len(candidates) < sample_size:
        raise ScienceAuditError(
            f"Only {len(candidates)} science candidates are available"
        )

    selected = list(REQUIRED_AUDIT_SLUGS)
    categories: dict[str, list[str]] = defaultdict(list)
    for slug in candidates:
        entry = catalog.get(slug)
        category = entry.get("tab_slug") if entry else None
        if isinstance(category, str) and category:
            categories[category].append(slug)
    for category in sorted(categories):
        members = categories[category]
        candidate = members[(len(members) - 1) // 2]
        if candidate not in selected and len(selected) < sample_size:
            selected.append(candidate)
    if len(selected) == sample_size:
        return selected

    evenly_spaced = [
        candidates[round(index * (len(candidates) - 1) / (sample_size + 1))]
        for index in range(1, sample_size + 1)
    ]
    for candidate in evenly_spaced + candidates:
        if candidate not in selected:
            selected.append(candidate)
        if len(selected) == sample_size:
            return selected
    raise ScienceAuditError("Could not construct the requested deterministic sample")


def audit_module(
    slug: str,
    source: str,
    *,
    source_page_url: str,
    source_asset_url: str,
    catalog_entry: dict[str, Any] | None,
) -> dict[str, Any]:
    """Inspect one raw module and test it against current normalization rules."""
    report: dict[str, Any] = {
        "slug": slug,
        "source_page_url": source_page_url,
        "source_asset_url": source_asset_url,
        "catalog_tree": catalog_entry.get("tab") if catalog_entry else None,
        "status": "failure",
    }
    try:
        payload = parse_research_module(source)
    except ModuleParseError as error:
        report["failure_stage"] = "parser"
        report["error"] = str(error)
        return report

    report.update(profile_payload(payload))
    report["source_tree"] = payload.get("tab")
    report["source_tree_slug"] = payload.get("tab_slug")
    report["field_compatibility"] = classify_payload_fields(payload)
    try:
        normalize_research_payload(
            payload,
            expected_slug=slug,
            source_page_url=source_page_url,
            source_asset_url=source_asset_url,
            retrieval=_audit_retrieval(source_asset_url),
        )
    except (ResearchValidationError, TypeError) as error:
        report["failure_stage"] = "normalization_or_validation"
        report["error"] = str(error)
        return report
    report["status"] = "success"
    return report


def profile_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a field and value profile without discarding unknown source keys."""
    raw_levels = payload.get("levels")
    levels = raw_levels if isinstance(raw_levels, list) else []
    level_records = [level for level in levels if isinstance(level, dict)]
    top_keys = sorted(payload)
    level_keys = sorted({key for level in level_records for key in level})
    cost_records = [
        cost
        for level in level_records
        for cost in level.get("costs", [])
        if isinstance(cost, dict)
    ]
    cost_keys = sorted({key for cost in cost_records for key in cost})
    resource_inventory = _resource_inventory(cost_records)
    declared_max_level = payload.get("max_level")
    level_numbers = [level.get("level") for level in level_records]
    contiguous = (
        all(
            isinstance(level, int) and not isinstance(level, bool)
            for level in level_numbers
        )
        and level_numbers == list(range(1, len(level_numbers) + 1))
    )
    return {
        "top_level_keys": top_keys,
        "top_level_types": _field_types([payload]),
        "top_level_null_keys": sorted(
            key for key, value in payload.items() if value is None
        ),
        "level_record_keys": level_keys,
        "level_record_types": _field_types(level_records),
        "level_missing_counts": _missing_counts(level_records, level_keys),
        "level_null_counts": _null_counts(level_records, level_keys),
        "level_zero_counts": _zero_counts(level_records, level_keys),
        "cost_record_keys": cost_keys,
        "cost_record_types": _field_types(cost_records),
        "cost_missing_counts": _missing_counts(cost_records, cost_keys),
        "cost_null_counts": _null_counts(cost_records, cost_keys),
        "cost_zero_counts": _zero_counts(cost_records, cost_keys),
        "resource_inventory": resource_inventory,
        "declared_max_level": declared_max_level,
        "actual_level_record_count": len(levels),
        "level_record_object_count": len(level_records),
        "level_count_equals_max_level": len(levels) == declared_max_level,
        "levels_contiguous": contiguous,
        "unexpected_types": _unexpected_types(payload, level_records, cost_records),
    }


def classify_payload_fields(payload: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    """Classify every observed field by current model/database preservation."""
    raw_levels = payload.get("levels")
    levels = raw_levels if isinstance(raw_levels, list) else []
    level_records = [level for level in levels if isinstance(level, dict)]
    cost_records = [
        cost
        for level in level_records
        for cost in level.get("costs", [])
        if isinstance(cost, dict)
    ]
    return {
        "top_level": _classify_keys(
            payload.keys(), _TOP_LEVEL_FIELD_CLASSIFICATIONS
        ),
        "level": _classify_level_keys(level_records),
        "cost": _classify_keys(
            cost_records_keys(cost_records), _COST_FIELD_CLASSIFICATIONS
        ),
    }


def cost_records_keys(cost_records: list[dict[str, Any]]) -> set[str]:
    """Return all observed cost-record keys."""
    return {key for cost in cost_records for key in cost}


def build_audit_report(
    node_reports: list[dict[str, Any]],
    *,
    sample_method: str,
    sitemap_science_slug_count: int,
    main_bundle_url: str,
    catalog_error: str | None,
) -> dict[str, Any]:
    """Aggregate per-module profiles into a JSON-serializable audit report."""
    successful = [node for node in node_reports if node["status"] == "success"]
    failures = [node for node in node_reports if node["status"] != "success"]
    resource_inventory: dict[str, dict[str, Any]] = {}
    for node in successful:
        for item in node["resource_inventory"]:
            existing = resource_inventory.setdefault(
                item["resource_identifier"],
                {
                    "resource_identifier": item["resource_identifier"],
                    "source_labels": set(),
                    "item_ids": set(),
                    "occurrence_count": 0,
                },
            )
            existing["source_labels"].update(item["source_labels"])
            existing["item_ids"].update(item["item_ids"])
            existing["occurrence_count"] += item["occurrence_count"]
    normalized_resources = [
        {
            **item,
            "source_labels": sorted(item["source_labels"]),
            "item_ids": sorted(item["item_ids"]),
        }
        for _, item in sorted(resource_inventory.items())
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_method": sample_method,
        "sitemap_science_slug_count": sitemap_science_slug_count,
        "main_bundle_url": main_bundle_url,
        "catalog_metadata_error": catalog_error,
        "sampled_slugs": [node["slug"] for node in node_reports],
        "successful_parse_count": len(successful),
        "failed_parse_count": len(failures),
        "trees_encountered": sorted(
            {
                node.get("source_tree")
                for node in successful
                if isinstance(node.get("source_tree"), str)
            }
        ),
        "top_level_keys": _union_keys(successful, "top_level_keys"),
        "level_record_keys": _union_keys(successful, "level_record_keys"),
        "cost_record_keys": _union_keys(successful, "cost_record_keys"),
        "resource_inventory": normalized_resources,
        "meaningful_fields_currently_dropped": _dropped_fields(node_reports),
        "failures": failures,
        "nodes": node_reports,
    }


def _classify_keys(
    keys: Any, classifications: dict[str, tuple[str, str]]
) -> list[dict[str, str]]:
    result = []
    for key in sorted(keys):
        classification, reason = classifications.get(
            key,
            ("C", "meaningful factual field is not currently preserved"),
        )
        result.append(
            {"field": key, "classification": classification, "reason": reason}
        )
    return result


def _classify_level_keys(level_records: list[dict[str, Any]]) -> list[dict[str, str]]:
    keys = {key for level in level_records for key in level}
    result = _classify_keys(keys, _LEVEL_FIELD_CLASSIFICATIONS)
    by_field = {entry["field"]: entry for entry in result}
    for field in keys:
        if field == "ability":
            by_field[field].update(_duplicate_ability_classification(level_records))
        elif field.startswith("cost_"):
            by_field[field].update(_duplicate_cost_classification(field, level_records))
    return [by_field[field] for field in sorted(by_field)]


def _duplicate_ability_classification(
    levels: list[dict[str, Any]],
) -> dict[str, str]:
    if all(level.get("ability") == level.get("power") for level in levels):
        return {
            "classification": "B",
            "reason": "duplicates power in every sampled level where present",
        }
    return {
        "classification": "C",
        "reason": "does not consistently duplicate power; currently dropped",
    }


def _duplicate_cost_classification(
    field: str, levels: list[dict[str, Any]]
) -> dict[str, str]:
    expected_resource = _KNOWN_COST_ALIASES.get(field)
    comparisons = []
    for level in levels:
        costs = {
            _resource_identifier(str(cost.get("resource", ""))): cost.get("amount")
            for cost in level.get("costs", [])
            if isinstance(cost, dict)
        }
        if field == "cost_special":
            if level.get("cost_special") is None:
                expected = None
            else:
                special_name = level.get("cost_special_name")
                expected = costs.get(
                    _resource_identifier(str(special_name or "")), 0
                )
        elif field == "cost_special_name":
            special_amount = level.get("cost_special", 0)
            expected = "" if special_amount == 0 else None
            if special_amount:
                expected = next(
                    (
                        cost.get("resource")
                        for cost in level.get("costs", [])
                        if isinstance(cost, dict)
                        and cost.get("amount") == special_amount
                        and _resource_identifier(str(cost.get("resource", "")))
                        not in {"farms", "lumber", "herbs"}
                    ),
                    None,
                )
        else:
            expected = costs.get(expected_resource, 0) if expected_resource else None
        comparisons.append(level.get(field) == expected)
    if all(comparisons):
        return {
            "classification": "B",
            "reason": "duplicates a value already represented in generic costs",
        }
    return {
        "classification": "C",
        "reason": "does not consistently match generic costs; currently dropped",
    }


def _resource_identifier(source_label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", source_label.lower()).strip("_")


def _resource_inventory(cost_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inventory: dict[str, dict[str, Any]] = {}
    for cost in cost_records:
        source_label = cost.get("resource")
        if not isinstance(source_label, str):
            continue
        resource_identifier = _resource_identifier(source_label)
        item = inventory.setdefault(
            resource_identifier,
            {
                "resource_identifier": resource_identifier,
                "source_labels": set(),
                "item_ids": set(),
                "occurrence_count": 0,
            },
        )
        item["source_labels"].add(source_label)
        item_id = cost.get("item_id")
        if isinstance(item_id, str):
            item["item_ids"].add(item_id)
        item["occurrence_count"] += 1
    return [
        {
            **item,
            "source_labels": sorted(item["source_labels"]),
            "item_ids": sorted(item["item_ids"]),
        }
        for _, item in sorted(inventory.items())
    ]


def _field_types(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for record in records:
        for key, value in record.items():
            result[key].add(type(value).__name__)
    return {key: sorted(values) for key, values in sorted(result.items())}


def _missing_counts(records: list[dict[str, Any]], keys: list[str]) -> dict[str, int]:
    return {
        key: sum(key not in record for record in records)
        for key in keys
        if any(key not in record for record in records)
    }


def _null_counts(records: list[dict[str, Any]], keys: list[str]) -> dict[str, int]:
    return {
        key: sum(record.get(key) is None for record in records)
        for key in keys
        if any(key in record and record.get(key) is None for record in records)
    }


def _zero_counts(records: list[dict[str, Any]], keys: list[str]) -> dict[str, int]:
    return {
        key: sum(record.get(key) == 0 for record in records)
        for key in keys
        if any(
            isinstance(record.get(key), (int, float))
            and not isinstance(record.get(key), bool)
            and record.get(key) == 0
            for record in records
        )
    }


def _unexpected_types(
    payload: dict[str, Any],
    levels: list[dict[str, Any]],
    costs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_top = {
        "id": {"str"},
        "slug": {"str"},
        "name": {"str"},
        "description": {"str"},
        "tab": {"str"},
        "tab_slug": {"str"},
        "tech_type": {"int"},
        "max_level": {"int"},
        "levels_count": {"int"},
        "levels": {"list"},
        "image": {"str"},
        "pos": {"str"},
    }
    expected_level = {
        "level": {"int"},
        "time_sec": {"int"},
        "time": {"str"},
        "power": {"int"},
        "raw_id": {"int"},
        "costs": {"list"},
        "ability": {"int"},
        "cost_special": {"int", "NoneType"},
        "cost_special_name": {"str", "NoneType"},
    }
    expected_cost = {
        "resource": {"str"},
        "amount": {"int"},
        "amount_fmt": {"str"},
        "item_id": {"str"},
    }
    result = []
    for scope, records, expected in (
        ("top_level", [payload], expected_top),
        ("level", levels, expected_level),
        ("cost", costs, expected_cost),
    ):
        for field, types in _field_types(records).items():
            allowed = expected.get(
                field,
                {"int", "float", "str", "bool", "NoneType", "list", "dict"},
            )
            unexpected = sorted(set(types).difference(allowed))
            if unexpected:
                result.append(
                    {
                        "scope": scope,
                        "field": field,
                        "types": types,
                        "unexpected": unexpected,
                    }
                )
    return result


def _union_keys(nodes: list[dict[str, Any]], key: str) -> list[str]:
    return sorted({item for node in nodes for item in node.get(key, [])})


def _dropped_fields(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    dropped: dict[tuple[str, str], dict[str, str]] = {}
    for node in nodes:
        compatibility = node.get("field_compatibility", {})
        for scope, fields in compatibility.items():
            for field in fields:
                if field["classification"] in {"C", "D"}:
                    dropped[(scope, field["field"])] = {
                        "scope": scope,
                        "field": field["field"],
                        "classification": field["classification"],
                        "reason": field["reason"],
                    }
    return [dropped[key] for key in sorted(dropped)]


def _audit_retrieval(source_asset_url: str):
    """Create minimal metadata solely to exercise existing normalization."""
    from last_asylum_doctor.models import RetrievalMetadata

    return RetrievalMetadata(
        source_url=source_asset_url,
        retrieved_at="audit",
        sha256="audit",
    )
