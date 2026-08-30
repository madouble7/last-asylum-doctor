"""Workbook-backed economic ingestion and read-only oracle comparison."""

from .oracle import (
    OracleError,
    PublicOracleClient,
    compare_oracle,
    load_canonical_economics,
    load_fixture,
    render_report,
)
from .shop_doctor import ShopDoctorWorkbookError, inspect_shop_doctor_workbook

__all__ = [
    "OracleError",
    "PublicOracleClient",
    "ShopDoctorWorkbookError",
    "compare_oracle",
    "inspect_shop_doctor_workbook",
    "load_canonical_economics",
    "load_fixture",
    "render_report",
]
