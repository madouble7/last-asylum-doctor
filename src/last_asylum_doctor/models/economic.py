"""Typed, source-preserving records from the Shop Doctor workbook."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class WorkbookItem:
    name: str
    base_unit: str
    category: str | None
    item_type: str | None
    data_status: str | None
    source: str | None
    notes: str | None
    aliases: tuple[str, ...]
    doctor_resource_key: str | None
    source_row: int
    model_values: dict[str, float | str | None]


@dataclass(frozen=True, slots=True)
class WorkbookOffer:
    offer_id: str
    active: str | None
    date_seen: date
    shop_name: str
    shop_snapshot_id: str
    item_name: str
    normalized_quantity: float
    cost: float
    currency_name: str
    direct_cash_price: float | None
    repeat_limit: float | None
    notes: str | None
    source: str | None
    actual_package_item: str | None
    actual_item_count: float | None
    base_units_per_item: float | None
    normalized_quantity_check: float | None
    speedup_type: str | None
    package_display: str | None
    source_row: int


@dataclass(frozen=True, slots=True)
class WorkbookCashPack:
    pack_id: str
    active: str | None
    date_seen: date
    name: str
    price_usd: float | None
    assumed_bonus_diamonds: int | None
    snapshot_id: str
    repeat_limit: float | None
    notes: str | None
    source: str | None
    valuation_status: str | None
    components_valued: str | None
    source_row: int


@dataclass(frozen=True, slots=True)
class WorkbookPackComponent:
    pack_id: str
    item_name: str
    normalized_quantity: float
    notes: str | None
    actual_package_item: str | None
    actual_item_count: float | None
    base_units_per_item: float | None
    normalized_quantity_check: float | None
    speedup_type: str | None
    data_status: str | None
    package_display: str | None
    normalization_check: str | None
    source_row: int


@dataclass(frozen=True, slots=True)
class WorkbookRelationship:
    container_name: str
    context: str | None
    contents_rule: str
    option_name: str
    option_quantity: float
    source_row: int


@dataclass(frozen=True, slots=True)
class CurrencyAssumption:
    currency_name: str
    value_per_unit: float | None
    classification: str
    basis: str | None
    active: str | None
    notes: str | None
    source_row: int


@dataclass(frozen=True, slots=True)
class ShopDoctorWorkbook:
    filename: str
    sha256: str
    size_bytes: int
    sheet_names: tuple[str, ...]
    snapshot_date: date
    items: tuple[WorkbookItem, ...]
    offers: tuple[WorkbookOffer, ...]
    cash_packs: tuple[WorkbookCashPack, ...]
    pack_components: tuple[WorkbookPackComponent, ...]
    relationships: tuple[WorkbookRelationship, ...]
    currency_assumptions: tuple[CurrencyAssumption, ...]
    model_observations: tuple[tuple[str, str, float | str | None, int], ...]
