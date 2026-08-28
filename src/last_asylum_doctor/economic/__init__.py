"""Workbook-backed economic and acquisition data ingestion."""

from .shop_doctor import ShopDoctorWorkbookError, inspect_shop_doctor_workbook

__all__ = ["ShopDoctorWorkbookError", "inspect_shop_doctor_workbook"]
