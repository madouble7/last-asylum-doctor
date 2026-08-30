"""Read-only comparison of the public Last Asylum Unofficial oracle."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import httpx

ORACLE_APP_ID = "698a36b276613255c34c822b"
ORACLE_BASE_URL = "https://last-asylum-unofficial.com/api/apps"
ORACLE_ENTITIES = ("Item", "ComplexItem", "Pack")
STATUSES = (
    "EXACT_COMPONENT_MATCH",
    "PARTIAL_MATCH",
    "PROPORTIONAL_TIER_CANDIDATE",
    "IDENTITY_CANDIDATE",
    "ALIAS_CANDIDATE",
    "STRUCTURE_MISMATCH",
    "CANONICAL_ONLY",
    "EXTERNAL_ONLY",
    "CONFLICT",
    "UNKNOWN",
)
REQUIRED_CANONICAL_COLUMNS = {
    "items": {"id", "canonical_key", "name"},
    "item_aliases": {"item_id", "alias"},
    "cash_packs": {"id", "original_pack_id", "name"},
    "cash_pack_components": {
        "id",
        "cash_pack_id",
        "item_id",
        "normalized_quantity",
        "speedup_type",
        "package_display",
    },
    "choice_groups": {"id", "container_item_id", "context", "contents_rule"},
    "choice_options": {
        "choice_group_id",
        "option_item_id",
        "option_index",
        "quantity",
    },
}


class OracleError(RuntimeError):
    """Raised when the public oracle response cannot be safely interpreted."""


@dataclass(frozen=True, slots=True)
class OracleFetchSnapshot:
    entity: str
    endpoint: str
    retrieved_at_utc: str
    http_status: int | None
    result_status: str
    row_count: int
    response_sha256: str
    schema_keys: tuple[str, ...]
    source_url: str
    oldest_source_timestamp: str | None
    newest_source_timestamp: str | None


@dataclass(frozen=True, slots=True)
class ExternalItem:
    external_id: str
    name: str
    conversions: tuple[dict[str, Any], ...]
    source_timestamps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExternalComplexItem:
    external_id: str
    name: str
    components: tuple["ExternalPackComponent", ...]
    analysis_amount: Any
    source_timestamps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExternalPackComponent:
    item_id: str
    item_name: str | None
    item_type: str | None
    amount: Any
    chance_pct: Any
    token_cost: Any
    choice_structure: Any


@dataclass(frozen=True, slots=True)
class ExternalPack:
    external_id: str
    name: str
    location: Any
    pack_price: Any
    pack_format: Any
    note: Any
    components: tuple[ExternalPackComponent, ...]
    choice_items: tuple[dict[str, Any], ...]
    source_timestamps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExternalOracleSnapshot:
    items: tuple[ExternalItem, ...]
    complex_items: tuple[ExternalComplexItem, ...]
    packs: tuple[ExternalPack, ...]
    fetches: tuple[OracleFetchSnapshot, ...]


@dataclass(frozen=True, slots=True)
class CanonicalItem:
    canonical_key: str
    name: str
    aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CanonicalPackComponent:
    item_key: str
    item_name: str
    quantity: float
    speedup_type: str | None
    package_display: str | None


@dataclass(frozen=True, slots=True)
class CanonicalPack:
    pack_id: int
    original_pack_id: str
    name: str
    components: tuple[CanonicalPackComponent, ...]


@dataclass(frozen=True, slots=True)
class CanonicalChoice:
    container_key: str
    container_name: str
    context: str | None
    contents_rule: str
    options: tuple[tuple[str, str, float], ...]


@dataclass(frozen=True, slots=True)
class CanonicalEconomics:
    items: tuple[CanonicalItem, ...]
    packs: tuple[CanonicalPack, ...]
    choices: tuple[CanonicalChoice, ...]


@dataclass(frozen=True, slots=True)
class OracleDiff:
    snapshot: ExternalOracleSnapshot
    item_comparisons: tuple[dict[str, Any], ...]
    complex_item_comparisons: tuple[dict[str, Any], ...]
    pack_comparisons: tuple[dict[str, Any], ...]
    canonical_only_packs: tuple[dict[str, Any], ...]
    choice_mismatches: tuple[dict[str, Any], ...]
    counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_metadata": [
                {
                    "entity": snapshot.entity,
                    "endpoint": snapshot.endpoint,
                    "source_url": snapshot.source_url,
                    "retrieved_at_utc": snapshot.retrieved_at_utc,
                    "http_status": snapshot.http_status,
                    "result_status": snapshot.result_status,
                    "row_count": snapshot.row_count,
                    "response_sha256": snapshot.response_sha256,
                    "schema_keys": list(snapshot.schema_keys),
                    "oldest_source_timestamp": snapshot.oldest_source_timestamp,
                    "newest_source_timestamp": snapshot.newest_source_timestamp,
                }
                for snapshot in self.snapshot.fetches
            ],
            "counts": dict(self.counts),
            "item_comparisons": list(self.item_comparisons),
            "complex_item_comparisons": list(self.complex_item_comparisons),
            "pack_comparisons": list(self.pack_comparisons),
            "canonical_only_packs": list(self.canonical_only_packs),
            "choice_mismatches": list(self.choice_mismatches),
        }


class PublicOracleClient:
    """Fetch only the three anonymous public Base44 entities."""

    def __init__(
        self,
        *,
        base_url: str = ORACLE_BASE_URL,
        app_id: str = ORACLE_APP_ID,
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.app_id = app_id
        self.timeout = timeout

    def fetch(self) -> ExternalOracleSnapshot:
        records: dict[str, list[dict[str, Any]]] = {}
        fetches: list[OracleFetchSnapshot] = []
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            for entity in ORACLE_ENTITIES:
                endpoint = f"{self.base_url}/{self.app_id}/entities/{entity}"
                try:
                    response = client.get(endpoint, params={"limit": 1000})
                except httpx.HTTPError as error:
                    raise OracleError(
                        f"{entity} public endpoint request failed: {error}"
                    ) from error
                body = response.content
                retrieved = _now()
                payload = _decode_rows(response, entity)
                records[entity] = payload
                fetches.append(
                    _snapshot(
                        entity=entity,
                        endpoint=endpoint,
                        source_url=str(response.url),
                        retrieved_at=retrieved,
                        http_status=response.status_code,
                        result_status="ok" if response.is_success else "http_error",
                        body=body,
                        rows=payload,
                    )
                )
                if not response.is_success:
                    raise OracleError(
                        f"{entity} public endpoint returned HTTP {response.status_code}"
                    )
        return normalize_entities(records, tuple(fetches))


def load_fixture(path: Path) -> ExternalOracleSnapshot:
    """Load an offline fixture shaped as {Item, ComplexItem, Pack: [...]}"""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OracleError("oracle fixture must be an object keyed by entity")
    records: dict[str, list[dict[str, Any]]] = {}
    fetches: list[OracleFetchSnapshot] = []
    for entity in ORACLE_ENTITIES:
        rows = payload.get(entity, [])
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise OracleError(
                f"oracle fixture entity {entity} must be a list of objects"
            )
        records[entity] = rows
        body = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        fetches.append(
            _snapshot(
                entity=entity,
                endpoint=f"fixture://{entity}",
                source_url=f"fixture://{entity}",
                retrieved_at="fixture",
                http_status=200,
                result_status="fixture",
                body=body,
                rows=rows,
            )
        )
    return normalize_entities(records, tuple(fetches))


def normalize_entities(
    records: Mapping[str, Iterable[Mapping[str, Any]]],
    fetches: tuple[OracleFetchSnapshot, ...],
) -> ExternalOracleSnapshot:
    """Build transient, source-preserving records without valuation fields."""
    item_rows = tuple(records.get("Item", ()))
    item_names = {
        str(row.get("item_id")): _text(row.get("item_name"))
        for row in item_rows
        if row.get("item_id") is not None and _text(row.get("item_name"))
    }
    items = tuple(
        ExternalItem(
            external_id=str(row.get("item_id") or row.get("id") or ""),
            name=str(row.get("item_name") or row.get("item_id") or ""),
            conversions=tuple(_dict_values(row.get("conversions"))),
            source_timestamps=_timestamps(row),
        )
        for row in item_rows
    )
    complex_items = tuple(
        ExternalComplexItem(
            external_id=str(row.get("complex_item_id") or row.get("id") or ""),
            name=str(row.get("complex_item_name") or row.get("complex_item_id") or ""),
            components=tuple(
                _external_component(value, item_names)
                for value in _dict_values(row.get("components"))
            ),
            analysis_amount=row.get("analysis_amount"),
            source_timestamps=_timestamps(row),
        )
        for row in records.get("ComplexItem", ())
    )
    packs = tuple(
        ExternalPack(
            external_id=str(row.get("id") or row.get("pack_id") or ""),
            name=str(row.get("pack_name") or row.get("id") or ""),
            location=row.get("pack_location"),
            pack_price=row.get("pack_price"),
            pack_format=row.get("pack_format"),
            note=row.get("pack_note"),
            components=tuple(
                _external_component(value, item_names)
                for value in _dict_values(row.get("pack_items"))
            ),
            choice_items=tuple(_dict_values(row.get("choice_items"))),
            source_timestamps=_timestamps(row),
        )
        for row in records.get("Pack", ())
    )
    return ExternalOracleSnapshot(
        items=tuple(
            sorted(items, key=lambda value: (value.name.casefold(), value.external_id))
        ),
        complex_items=tuple(
            sorted(
                complex_items,
                key=lambda value: (value.name.casefold(), value.external_id),
            )
        ),
        packs=tuple(
            sorted(packs, key=lambda value: (value.name.casefold(), value.external_id))
        ),
        fetches=tuple(sorted(fetches, key=lambda value: value.entity)),
    )


def load_canonical_economics(connection: sqlite3.Connection) -> CanonicalEconomics:
    """Read canonical comparison tables without writing or changing the database."""
    item_rows = connection.execute(
        "SELECT id, canonical_key, name FROM items ORDER BY canonical_key"
    ).fetchall()
    aliases: dict[int, list[str]] = {int(row[0]): [] for row in item_rows}
    for row in connection.execute(
        "SELECT item_id, alias FROM item_aliases ORDER BY item_id, alias"
    ):
        aliases[int(row[0])].append(str(row[1]))
    items = tuple(
        CanonicalItem(str(row[1]), str(row[2]), tuple(aliases[int(row[0])]))
        for row in item_rows
    )
    item_by_id = {int(row[0]): (str(row[1]), str(row[2])) for row in item_rows}
    pack_rows = connection.execute(
        "SELECT id, original_pack_id, name FROM cash_packs ORDER BY name, id"
    ).fetchall()
    components_by_pack: dict[int, list[CanonicalPackComponent]] = {
        int(row[0]): [] for row in pack_rows
    }
    for row in connection.execute(
        """
        SELECT c.cash_pack_id, c.item_id, c.normalized_quantity, c.speedup_type,
               c.package_display
        FROM cash_pack_components AS c ORDER BY c.cash_pack_id, c.id
        """
    ):
        item_key, item_name = item_by_id[int(row[1])]
        components_by_pack[int(row[0])].append(
            CanonicalPackComponent(
                item_key=item_key,
                item_name=item_name,
                quantity=float(row[2]),
                speedup_type=_text(row[3]),
                package_display=_text(row[4]),
            )
        )
    packs = tuple(
        CanonicalPack(
            pack_id=int(row[0]),
            original_pack_id=str(row[1]),
            name=str(row[2]),
            components=tuple(components_by_pack[int(row[0])]),
        )
        for row in pack_rows
    )
    grouped_choices: dict[
        tuple[int, str | None, str], list[tuple[str, str, float]]
    ] = {}
    for row in connection.execute(
        """
        SELECT g.container_item_id, g.context, g.contents_rule,
               target.canonical_key, target.name, o.quantity
        FROM choice_groups AS g
        JOIN choice_options AS o ON o.choice_group_id = g.id
        JOIN items AS target ON target.id = o.option_item_id
        ORDER BY g.container_item_id, g.id, o.option_index
        """
    ):
        grouped_choices.setdefault(
            (int(row[0]), _text(row[1]), str(row[2])), []
        ).append((str(row[3]), str(row[4]), float(row[5])))
    choices = tuple(
        CanonicalChoice(
            container_key=item_by_id[item_id][0],
            container_name=item_by_id[item_id][1],
            context=context,
            contents_rule=rule,
            options=tuple(options),
        )
        for (item_id, context, rule), options in sorted(grouped_choices.items())
    )
    return CanonicalEconomics(items=items, packs=packs, choices=choices)


@contextmanager
def open_read_only_database(path: Path) -> Iterable[sqlite3.Connection]:
    """Open an existing canonical database without initialization or writes."""
    if not path.is_file():
        raise OracleError(f"canonical database does not exist: {path}")
    try:
        connection = sqlite3.connect(
            f"file:{path.resolve().as_posix()}?mode=ro", uri=True
        )
    except sqlite3.Error as error:
        raise OracleError(
            f"could not open canonical database read-only: {error}"
        ) from error
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        _validate_canonical_schema(connection)
        yield connection
    except sqlite3.Error as error:
        raise OracleError(
            f"canonical database is not compatible with the oracle schema: {error}"
        ) from error
    finally:
        connection.close()


def _validate_canonical_schema(connection: sqlite3.Connection) -> None:
    tables = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    missing_tables = sorted(set(REQUIRED_CANONICAL_COLUMNS) - tables)
    if missing_tables:
        raise OracleError(
            "canonical database schema is incomplete; missing tables: "
            + ", ".join(missing_tables)
        )
    missing_columns: dict[str, list[str]] = {}
    for table, required_columns in REQUIRED_CANONICAL_COLUMNS.items():
        columns = {
            str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")
        }
        missing = sorted(required_columns - columns)
        if missing:
            missing_columns[table] = missing
    if missing_columns:
        details = "; ".join(
            f"{table}: {', '.join(columns)}"
            for table, columns in sorted(missing_columns.items())
        )
        raise OracleError(
            "canonical database schema is incompatible; missing columns: " + details
        )


def compare_oracle(
    canonical: CanonicalEconomics, external: ExternalOracleSnapshot
) -> OracleDiff:
    """Compare external structures deterministically, without canonical mutation."""
    item_comparisons = tuple(
        _compare_item(item, canonical.items) for item in external.items
    )
    complex_comparisons = tuple(
        _compare_complex_item(item, canonical) for item in external.complex_items
    )
    pack_comparisons: list[dict[str, Any]] = []
    matched_pack_ids: set[int] = set()
    for pack in external.packs:
        candidates = _pack_candidates(pack, canonical)
        comparison = _compare_pack(pack, candidates, canonical)
        pack_comparisons.append(comparison)
        if comparison["status"] != "EXTERNAL_ONLY":
            matched_pack_id = comparison.get("canonical_pack_id")
            if matched_pack_id is not None:
                matched_pack_ids.add(int(matched_pack_id))
    canonical_only = tuple(
        {
            "status": "CANONICAL_ONLY",
            "pack_id": pack.pack_id,
            "name": pack.name,
        }
        for pack in canonical.packs
        if pack.pack_id not in matched_pack_ids
    )
    choice_mismatches = tuple(
        value
        for value in (*complex_comparisons, *pack_comparisons)
        if value.get("choice_status") in {"STRUCTURE_MISMATCH", "UNKNOWN"}
    )
    statuses = Counter(
        value["status"]
        for value in (*item_comparisons, *complex_comparisons, *pack_comparisons)
    )
    return OracleDiff(
        snapshot=external,
        item_comparisons=item_comparisons,
        complex_item_comparisons=complex_comparisons,
        pack_comparisons=tuple(pack_comparisons),
        canonical_only_packs=canonical_only,
        choice_mismatches=choice_mismatches,
        counts={status: statuses.get(status, 0) for status in STATUSES},
    )


def render_report(diff: OracleDiff) -> str:
    """Render a stable human-readable report from the machine result."""
    lines = ["Shop Doctor Pack Oracle Diff v0.1", "", "Snapshots:"]
    for snapshot in diff.snapshot.fetches:
        lines.append(
            f"- {snapshot.entity}: {snapshot.result_status}, "
            f"{snapshot.row_count} rows, "
            f"SHA-256 {snapshot.response_sha256}, {snapshot.source_url}"
        )
    lines.extend(
        [
            "",
            "Counts:",
            *[
                f"- {status}: {diff.counts[status]}"
                for status in STATUSES
                if diff.counts[status]
            ],
            "",
            "Canonical packs with external candidates:",
        ]
    )
    for comparison in diff.pack_comparisons:
        if comparison["status"] != "EXTERNAL_ONLY":
            lines.append(f"- {comparison['name']}: {comparison['status']}")
    lines.append("External-only pack candidates:")
    for comparison in diff.pack_comparisons:
        if comparison["status"] == "EXTERNAL_ONLY":
            lines.append(f"- {comparison['name']}: EXTERNAL_ONLY")
    lines.append("Alias candidates:")
    for comparison in diff.item_comparisons:
        if comparison["status"] == "ALIAS_CANDIDATE":
            lines.append(
                f"- {comparison['name']}: {comparison['canonical_candidates']}"
            )
    lines.append("Structural mismatches:")
    for comparison in (*diff.complex_item_comparisons, *diff.pack_comparisons):
        if comparison.get("status") == "STRUCTURE_MISMATCH":
            lines.append(f"- {comparison['name']}")
    lines.append("Selected detailed comparisons:")
    for comparison in diff.pack_comparisons[:10]:
        lines.append(
            f"- {comparison['name']}: {comparison['status']} "
            f"(matched {comparison['matched_component_count']}, "
            f"external {comparison['external_component_count']}, "
            f"canonical {comparison['canonical_component_count']})"
        )
    return "\n".join(lines)


def _compare_item(
    item: ExternalItem, canonical: tuple[CanonicalItem, ...]
) -> dict[str, Any]:
    exact = [value for value in canonical if _key(item.name) == value.canonical_key]
    if exact:
        return {
            "status": "EXACT_COMPONENT_MATCH",
            "external_id": item.external_id,
            "name": item.name,
            "canonical": exact[0].name,
        }
    aliases = [
        value.name
        for value in canonical
        if _key(item.name) in {_key(alias) for alias in value.aliases}
    ]
    if aliases:
        return {
            "status": "ALIAS_CANDIDATE",
            "external_id": item.external_id,
            "name": item.name,
            "canonical_candidates": aliases,
        }
    identity = [
        value.name
        for value in canonical
        if _compact(item.external_id)
        in {_compact(value.name), _compact(value.canonical_key)}
    ]
    if identity:
        return {
            "status": "IDENTITY_CANDIDATE",
            "external_id": item.external_id,
            "name": item.name,
            "canonical_candidates": identity,
        }
    return {
        "status": "EXTERNAL_ONLY",
        "external_id": item.external_id,
        "name": item.name,
    }


def _compare_complex_item(
    item: ExternalComplexItem, canonical: CanonicalEconomics
) -> dict[str, Any]:
    candidates = [
        value for value in canonical.items if _key(item.name) == value.canonical_key
    ]
    status = "UNKNOWN" if not candidates else "STRUCTURE_MISMATCH"
    return {
        "status": status,
        "external_id": item.external_id,
        "name": item.name,
        "component_count": len(item.components),
        "canonical_candidates": [value.name for value in candidates],
        "analysis_value_used": False,
    }


def _pack_candidates(
    pack: ExternalPack, canonical: CanonicalEconomics
) -> list[CanonicalPack]:
    named = [value for value in canonical.packs if _key(pack.name) == _key(value.name)]
    if named:
        return named
    exact_overlap = [
        value for value in canonical.packs if _component_overlap(pack.components, value)
    ]
    return sorted(
        exact_overlap,
        key=lambda value: (
            -_component_overlap(pack.components, value.components),
            value.name,
            value.pack_id,
        ),
    )[:3]


def _compare_pack(
    pack: ExternalPack, candidates: list[CanonicalPack], canonical: CanonicalEconomics
) -> dict[str, Any]:
    if not candidates:
        return _pack_result(pack, "EXTERNAL_ONLY", None, 0)
    candidate = max(
        ((_pack_score(pack, value), value) for value in candidates),
        key=lambda value: (value[0], value[1].name, -value[1].pack_id),
    )[1]
    status, matched = _component_comparison(pack.components, candidate.components)
    choice_status = _choice_status(pack, candidate, canonical)
    if choice_status == "STRUCTURE_MISMATCH" and status == "EXACT_COMPONENT_MATCH":
        status = "STRUCTURE_MISMATCH"
    return _pack_result(pack, status, candidate, matched, choice_status=choice_status)


def _pack_result(
    pack: ExternalPack,
    status: str,
    candidate: CanonicalPack | None,
    matched: int,
    *,
    choice_status: str = "UNKNOWN",
) -> dict[str, Any]:
    return {
        "status": status,
        "external_id": pack.external_id,
        "name": pack.name,
        "location": pack.location,
        "pack_price": pack.pack_price,
        "pack_format": pack.pack_format,
        "canonical_pack": candidate.name if candidate else None,
        "canonical_pack_id": candidate.pack_id if candidate else None,
        "matched_component_count": matched,
        "external_component_count": len(pack.components),
        "canonical_component_count": len(candidate.components) if candidate else 0,
        "choice_status": choice_status,
        "price_interpretation": None,
    }


def _component_comparison(
    external: tuple[ExternalPackComponent, ...],
    canonical: tuple[CanonicalPackComponent, ...],
) -> tuple[str, int]:
    if not canonical:
        return "UNKNOWN", 0
    matched = 0
    identity_matches = 0
    ratios: list[float] = []
    used: set[int] = set()
    for value in external:
        for index, target in enumerate(canonical):
            identity = _component_identity(value) == target.item_key
            subtype = (
                _text(value.item_id) == _text(target.package_display)
                or not target.speedup_type
            )
            if identity and subtype and index not in used:
                used.add(index)
                identity_matches += 1
                if _number_equal(value.amount, target.quantity):
                    matched += 1
                elif _positive_number(value.amount) and target.quantity > 0:
                    ratios.append(float(value.amount) / target.quantity)
                break
    if matched == len(canonical):
        return "EXACT_COMPONENT_MATCH", matched
    if identity_matches and ratios and _same_ratio(ratios):
        return "PROPORTIONAL_TIER_CANDIDATE", identity_matches
    if identity_matches:
        return "PARTIAL_MATCH", identity_matches
    if _same_item_set(external, canonical):
        return "CONFLICT", 0
    return "STRUCTURE_MISMATCH", 0


def _choice_status(
    pack: ExternalPack, candidate: CanonicalPack, canonical: CanonicalEconomics
) -> str:
    if not pack.choice_items:
        return "UNKNOWN"
    related = [
        value
        for value in canonical.choices
        if _key(value.container_name) == _key(candidate.name)
    ]
    if not related:
        return "UNKNOWN"
    external_ids = {
        _key(str(value.get("item_id") or value.get("name") or ""))
        for value in pack.choice_items
    }
    canonical_ids = {_key(option[1]) for value in related for option in value.options}
    return "UNKNOWN" if external_ids == canonical_ids else "STRUCTURE_MISMATCH"


def _component_identity(value: ExternalPackComponent) -> str:
    return _key(value.item_name or value.item_id)


def _component_overlap(
    external: tuple[ExternalPackComponent, ...], canonical: CanonicalPack
) -> int:
    matched = 0
    used: set[int] = set()
    for value in external:
        for index, target in enumerate(canonical.components):
            if index not in used and _component_identity(value) == target.item_key:
                used.add(index)
                matched += 1
                break
    return matched


def _pack_score(pack: ExternalPack, candidate: CanonicalPack) -> int:
    return _component_overlap(pack.components, candidate)


def _same_item_set(
    external: tuple[ExternalPackComponent, ...],
    canonical: tuple[CanonicalPackComponent, ...],
) -> bool:
    return {_component_identity(value) for value in external} == {
        value.item_key for value in canonical
    }


def _same_ratio(values: list[float]) -> bool:
    return bool(values) and max(values) - min(values) <= 1e-9


def _number_equal(left: Any, right: float) -> bool:
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return False


def _positive_number(value: Any) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _external_component(
    value: Mapping[str, Any], item_names: Mapping[str, str | None]
) -> ExternalPackComponent:
    item_id = str(value.get("item_id") or "")
    return ExternalPackComponent(
        item_id=item_id,
        item_name=item_names.get(item_id) or _text(value.get("item_name")),
        item_type=_text(value.get("item_type")),
        amount=value.get("amount"),
        chance_pct=value.get("chance_pct", value.get("percentage")),
        token_cost=value.get("token_cost"),
        choice_structure=value.get("choice_items", value.get("choices")),
    )


def _decode_rows(response: httpx.Response, entity: str) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as error:
        raise OracleError(f"{entity} endpoint did not return JSON") from error
    if not isinstance(payload, list) or not all(
        isinstance(row, dict) for row in payload
    ):
        raise OracleError(f"{entity} endpoint did not return a JSON row array")
    return payload


def _snapshot(**values: Any) -> OracleFetchSnapshot:
    if "retrieved_at" in values:
        values["retrieved_at_utc"] = values.pop("retrieved_at")
    rows = values.pop("rows")
    keys = sorted({str(key) for row in rows for key in row})
    timestamps = sorted(timestamp for row in rows for timestamp in _timestamps(row))
    return OracleFetchSnapshot(
        schema_keys=tuple(keys),
        row_count=len(rows),
        oldest_source_timestamp=timestamps[0] if timestamps else None,
        newest_source_timestamp=timestamps[-1] if timestamps else None,
        response_sha256=hashlib.sha256(values.pop("body")).hexdigest(),
        **values,
    )


def _dict_values(value: Any) -> list[dict[str, Any]]:
    return (
        [dict(item) for item in value]
        if isinstance(value, list) and all(isinstance(item, dict) for item in value)
        else []
    )


def _timestamps(row: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        sorted(
            str(row[key])
            for key in ("created_date", "updated_date", "created_at", "updated_at")
            if row.get(key)
        )
    )


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
