# ruff: noqa: E501, E701
from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook

from last_asylum_doctor.cli import main
from last_asylum_doctor.database import EconomicDatabase
from last_asylum_doctor.economic import inspect_shop_doctor_workbook


def test_shop_doctor_reader_normalizes_speedups_and_choices(tmp_path: Path) -> None:
    path = _workbook(tmp_path / "shop_doctor.xlsx")

    workbook = inspect_shop_doctor_workbook(path)

    assert len(workbook.offers) == 7
    assert {offer.normalized_quantity for offer in workbook.offers} == {
        1,
        5,
        60,
        180,
        480,
        600,
        6_000,
    }
    assert {offer.item_name for offer in workbook.offers} == {"Speedup"}
    assert all(offer.actual_package_item == "Speedup" for offer in workbook.offers)
    assert len(workbook.relationships) == 10
    deluxe = [
        value
        for value in workbook.relationships
        if value.container_name == "Deluxe Choice Chest"
    ]
    assert {value.option_name for value in deluxe} == {
        "Raven Essence",
        "Gearstone",
        "Raven Gear Chest Lv5",
        "UR Resource Supply",
    }
    assert workbook.cash_packs[0].assumed_bonus_diamonds == 499
    assert workbook.cash_packs[0].valuation_status == "PARTIAL / MINIMUM KNOWN"


def test_economic_database_is_idempotent_and_keeps_research_bridge(
    tmp_path: Path,
) -> None:
    path = _workbook(tmp_path / "shop_doctor.xlsx")
    workbook = inspect_shop_doctor_workbook(path)
    database_path = tmp_path / "doctor.db"

    with EconomicDatabase(database_path) as database:
        first = database.store_shop_doctor(workbook)
        second = database.store_shop_doctor(workbook)
        validation = database.validate_economic_data()
        speedup_prices = database.get_item_prices("speedup")
        grain = database.get_item("grain")

    assert first.snapshot_created is True
    assert first.offers_created == 7
    assert first.cash_packs_created == 1
    assert first.pack_components_created == 1
    assert second.snapshot_created is False
    assert second.offers_created == 0
    assert validation["valid"] is True
    assert validation["table_counts"]["source_snapshots"] == 1
    assert validation["research_resource_bridges"] == {
        "farms": "grain",
        "herbs": "herbs",
        "lumber": "timber",
        "study_scroll": "study-scroll",
    }
    assert speedup_prices is not None and len(speedup_prices) == 7
    assert grain is not None
    assert {entry["source_key"] for entry in grain["research_resource_bridges"]} == {
        "farms"
    }


def test_shop_doctor_cli_inspection_and_item_queries(
    tmp_path: Path, capsys: object
) -> None:
    path = _workbook(tmp_path / "shop_doctor.xlsx")
    database_path = tmp_path / "doctor.db"

    assert main(["inspect-shop-doctor", str(path)]) == 0
    assert '"offers": 7' in capsys.readouterr().out  # type: ignore[attr-defined]
    assert (
        main(
            [
                "ingest-shop-doctor",
                str(path),
                "--store-db",
                "--database",
                str(database_path),
            ]
        )
        == 0
    )
    capsys.readouterr()  # type: ignore[attr-defined]
    assert (
        main(["show-item", "deluxe-choice-chest", "--database", str(database_path)])
        == 0
    )
    assert "UR Resource Supply" in capsys.readouterr().out  # type: ignore[attr-defined]
    assert main(["show-item-prices", "speedup", "--database", str(database_path)]) == 0
    assert "VIP 1m" in capsys.readouterr().out  # type: ignore[attr-defined]


def _workbook(path: Path) -> Path:
    workbook = Workbook()
    workbook.remove(workbook.active)
    sheets = {
        name: workbook.create_sheet(name)
        for name in (
            "START HERE",
            "DASHBOARD",
            "LIVE OFFERS",
            "CASH PACKS",
            "PACK CONTENTS",
            "ITEM CATALOG",
            "CALC ENGINE",
            "ADVANCED SETTINGS",
        )
    }
    offers = sheets["LIVE OFFERS"]
    offers.append([])
    offers.append([])
    offers.append([])
    offers.append([])
    offers.append(
        [
            "Offer ID",
            "Active? (optional)",
            "Date Seen",
            "Shop / Event",
            "Shop Snapshot ID",
            "Canonical Item",
            "Normalized Qty (Base Units)",
            "Cost",
            "Currency",
            "Direct Cash $",
            "Repeat Limit",
            "Notes",
            "Source",
            "Actual Package Item",
            "Actual Item Count",
            "Base Units per Item",
            "Normalized Qty Check",
            "Speedup Type",
        ]
    )
    offer_specs = [
        ("VIP 1m", "VIP Shop", 1, 1, 1),
        ("VIP 5m", "VIP Shop", 1, 5, 5),
        ("VIP 60m", "VIP Shop", 1, 60, 60),
        ("VIP 3h", "VIP Shop", 1, 180, 180),
        ("Alliance 8h", "Alliance Shop", 1, 480, 480),
        ("Bazaar 10x60m", "Strange Bazaar", 10, 60, 600),
        ("Sanctuary Pack 100x60m", "Sanctuary Shop", 100, 60, 6000),
    ]
    for identifier, shop, count, units, normalized in offer_specs:
        offers.append(
            [
                identifier,
                "YES",
                date(2026, 8, 27),
                shop,
                "snapshot",
                "Speedup",
                normalized,
                1,
                "Diamonds",
                None,
                None,
                identifier,
                "fixture",
                "Speedup",
                count,
                units,
                normalized,
                "Universal",
            ]
        )

    packs = sheets["CASH PACKS"]
    for _ in range(4):
        packs.append([])
    packs.append(
        [
            "Pack ID",
            "Active? (optional)",
            "Date Seen",
            "Pack",
            "Price $",
            "Assumed Bonus Diamonds",
            "Snapshot ID",
            "Repeat Limit",
            "Notes",
            "Source",
            "Valuation Status",
            "Components Valued",
        ]
    )
    packs.append(
        [
            "pack-1",
            "YES",
            date(2026, 8, 27),
            "Fixture Pack",
            4.99,
            499,
            "snapshot",
            None,
            None,
            "fixture",
            "PARTIAL / MINIMUM KNOWN",
            "1 / 2",
        ]
    )

    components = sheets["PACK CONTENTS"]
    for _ in range(4):
        components.append([])
    components.append(
        [
            "Pack ID",
            "Canonical Item",
            "Normalized Qty (Base Units)",
            "Notes",
            "Actual Package Item",
            "Actual Item Count",
            "Base Units per Item",
            "Normalized Qty Check",
            "Speedup Type",
            "Data Status",
            "Package Display",
            "Normalization Check",
        ]
    )
    components.append(
        [
            "pack-1",
            "Speedup",
            6000,
            "fixture",
            "Speedup",
            100,
            60,
            6000,
            "Universal",
            "OBSERVED",
            "100 × 60m Speedup",
            "OK",
        ]
    )

    catalog = sheets["ITEM CATALOG"]
    for _ in range(4):
        catalog.append([])
    catalog.append(
        [
            "Canonical Item",
            "Base Unit",
            "Strategic Tier",
            "Personal Priority",
            "Category",
            "Intrinsic Progression",
            "Priority Bonus",
            "Focus Bonus",
            "Intrinsic + Bonuses",
            "AD Day",
            "Effective AD Pts / Base",
            "Published Base AD Pts / Base",
            "Verification",
            "Source",
            "Notes",
            "Choice 1 Item",
            "Choice 1 Qty (Base Units)",
            "Choice 2 Item",
            "Choice 2 Qty (Base Units)",
            "Choice 3 Item",
            "Choice 3 Qty (Base Units)",
            "Yield Basis",
            "Contents Rule",
            "Choice 4 Item",
            "Choice 4 Qty (Base Units)",
            "Data Status",
            "Item Type",
            "Speedup Type",
            "Aliases / Equivalencies",
            "Doctor Resource Key",
        ]
    )

    def item(
        name: str,
        unit: str,
        *,
        rule: str | None = None,
        choices: list[tuple[str, float]] | None = None,
        aliases: str | None = None,
        key: str | None = None,
    ) -> None:
        row = [
            name,
            unit,
            "Unrated",
            "NORMAL",
            "Resources",
            0,
            0,
            0,
            0,
            None,
            0,
            0,
            "fixture",
            "fixture",
            None,
        ]
        options = list(choices or []) + [(None, None)] * 4
        row.extend(options[0])
        row.extend(options[1])
        row.extend(options[2])
        row.extend(["Sanctuary Lv26", rule])
        row.extend(options[3])
        row.extend(["OBSERVED", "SUPPLY", None, aliases, key])
        catalog.append(row)

    item("Speedup", "1 minute", aliases="Speedups")
    item("Grain", "1 million", aliases="Farm, Farms", key="grain")
    item("Timber", "1 million", aliases="Lumber", key="timber")
    item("Herbs", "1 million", aliases="Herb", key="herbs")
    item("Study Scroll", "1 scroll", key="study_scroll")
    item("Raven Essence", "1 essence")
    item("Gearstone", "1 gearstone")
    item("Raven Gear Chest Lv5", "1 chest")
    item(
        "SSR Resource Supply",
        "1 supply",
        rule="CHOOSE ONE",
        choices=[("Grain", 1.17969), ("Timber", 1.17969), ("Herbs", 0.75201)],
    )
    item(
        "UR Resource Supply",
        "1 supply",
        rule="CHOOSE ONE",
        choices=[("Grain", 3.53906), ("Timber", 3.53906), ("Herbs", 2.25602)],
    )
    item(
        "Deluxe Choice Chest",
        "1 chest",
        rule="CHOOSE ONE",
        choices=[
            ("Raven Essence", 40),
            ("Gearstone", 5000),
            ("Raven Gear Chest Lv5", 1),
            ("UR Resource Supply", 15),
        ],
    )

    calc = sheets["CALC ENGINE"]
    for _ in range(4):
        calc.append([])
    calc.append(
        [
            "Offer ID",
            "VE$ / Package",
            "VE$ / Unit",
            "Historical Best Price",
            "Historical Median",
        ]
    )
    calc.append(["VIP 1m", 1.0, 1.0, 1.0, 1.0])

    settings = sheets["ADVANCED SETTINGS"]
    for _ in range(4):
        settings.append([])
    settings.append(
        [
            None,
            None,
            None,
            None,
            "Currency",
            "VE$ / Unit",
            "Confidence",
            "Basis",
            "Active?",
            "Notes",
        ]
    )
    settings.append(
        [
            None,
            None,
            None,
            None,
            "Diamonds",
            0.1,
            "DERIVED VALUATION ASSUMPTION",
            "fixture",
            "YES",
            "fixture",
        ]
    )
    settings.append(
        [
            None,
            None,
            None,
            None,
            "USD",
            1.0,
            "DIRECT / OBSERVED CASH ANCHOR",
            "fixture",
            "YES",
            "fixture",
        ]
    )
    workbook.save(path)
    return path
