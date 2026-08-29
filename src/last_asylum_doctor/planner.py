"""Deterministic recovery and progression planning for a Doctor account."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

RESOURCES = ("antitoxin", "grain", "timber", "herbs")
TG27_REQUIREMENTS = {
    "antitoxin": 56_000_000,
    "grain": 252_000_000,
    "timber": 252_000_000,
    "herbs": 107_000_000,
}
RL27_REQUIREMENTS = {
    "antitoxin": 114_000_000,
    "grain": 423_000_000,
    "timber": 423_000_000,
    "herbs": 134_000_000,
}
TG27_BASE_SECONDS = 14 * 86_400 + 11 * 3_600 + 17 * 60 + 56
RL27_BASE_SECONDS = 19 * 86_400 + 5 * 3_600 + 10 * 60 + 55
CONFIRMED_PROVENANCE = "Server 283 client UI observations"


@dataclass(frozen=True, slots=True)
class AccountState:
    """Known account values; unknown future fields are intentionally ignored."""

    resources: dict[str, int]
    sanctuary_27_remaining_seconds: int
    construction_speedup_minutes: int
    training_speedup_minutes: int
    universal_speedup_minutes: int
    current_t8_troops: int
    recoverable_or_wounded_troops: int | None
    desired_combat_ready_troops: int | None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> AccountState:
        return cls(
            resources={
                resource: _required_int(data, resource) for resource in RESOURCES
            },
            sanctuary_27_remaining_seconds=_required_int(
                data, "sanctuary_27_remaining_seconds"
            ),
            construction_speedup_minutes=_required_int(
                data, "construction_speedup_minutes"
            ),
            training_speedup_minutes=_required_int(data, "training_speedup_minutes"),
            universal_speedup_minutes=_required_int(data, "universal_speedup_minutes"),
            current_t8_troops=_required_int(data, "current_t8_troops"),
            recoverable_or_wounded_troops=_optional_int(
                data.get("recoverable_or_wounded_troops")
            ),
            desired_combat_ready_troops=_optional_int(
                data.get("desired_combat_ready_troops")
            ),
        )


@dataclass(frozen=True, slots=True)
class PlannerReport:
    account: AccountState
    t9_readiness: dict[str, Any]
    s28_preparation: dict[str, Any]
    combined_s27_follow_on_bank: dict[str, Any]
    post_war_recovery: dict[str, Any]
    speedup_readiness: dict[str, Any]
    known_limitations: tuple[str, ...]


def plan_recovery(data: Mapping[str, Any] | AccountState) -> PlannerReport:
    account = (
        data if isinstance(data, AccountState) else AccountState.from_mapping(data)
    )
    tg = _funding(account.resources, TG27_REQUIREMENTS)
    rl = _funding(account.resources, RL27_REQUIREMENTS)
    combined = {
        resource: TG27_REQUIREMENTS[resource] + RL27_REQUIREMENTS[resource]
        for resource in RESOURCES
    }
    construction_seconds = account.construction_speedup_minutes * 60
    universal_seconds = account.universal_speedup_minutes * 60
    remaining = account.sanctuary_27_remaining_seconds
    troop_gap = None
    if account.desired_combat_ready_troops is not None:
        troop_gap = max(
            account.desired_combat_ready_troops - account.current_t8_troops, 0
        )
    speedup_message = (
        "Accelerating S27 can genuinely advance the T9 timeline; "
        "this is not an economic-optimality claim."
        if tg["ready"]
        else "TG27 is not funded, so accelerating S27 may only move the "
        "resource bottleneck earlier."
    )
    return PlannerReport(
        account=account,
        t9_readiness={
            "status": "READY" if tg["ready"] else "NOT READY",
            "requirements": TG27_REQUIREMENTS,
            "gaps": tg["gaps"],
            "readiness_percentage": tg["percentage"],
            "base_construction_seconds": TG27_BASE_SECONDS,
            "gated_by": "Sanctuary 27",
            "provenance": CONFIRMED_PROVENANCE,
        },
        s28_preparation={
            "status": "READY" if rl["ready"] else "NOT READY",
            "requirements": RL27_REQUIREMENTS,
            "gaps": rl["gaps"],
            "base_construction_seconds": RL27_BASE_SECONDS,
            "purpose": "Subsequent Sanctuary progression toward Sanctuary 28",
            "provenance": CONFIRMED_PROVENANCE,
        },
        combined_s27_follow_on_bank={
            "requirements": combined,
            "gaps": _gaps(account.resources, combined),
            "note": "TG27 + RL27 bank; distinct from the immediate T9 requirement",
            "provenance": CONFIRMED_PROVENANCE,
        },
        post_war_recovery={
            "current_t8_troops": account.current_t8_troops,
            "recoverable_or_wounded_troops": account.recoverable_or_wounded_troops,
            "desired_combat_ready_troops": account.desired_combat_ready_troops,
            "additional_troops_needed_for_target": troop_gap,
            "natural_rebuild": "UNKNOWN duration and costs",
            "speedup_assisted_rebuild": "OPTIONAL; exact benefit is UNKNOWN",
            "future_t9_transition": (
                "Separate future transition; no T9 costs or times supplied"
            ),
        },
        speedup_readiness={
            "sanctuary_27_remaining_seconds": remaining,
            "construction_speedup_minutes": account.construction_speedup_minutes,
            "construction_speedup_seconds_applied": min(
                construction_seconds, remaining
            ),
            "remaining_after_construction_speedups_seconds": max(
                remaining - construction_seconds, 0
            ),
            "universal_speedup_minutes": account.universal_speedup_minutes,
            "universal_speedup_seconds_shown_separately": universal_seconds,
            "maximum_seconds_sooner_if_all_available_used": min(
                construction_seconds + universal_seconds, remaining
            ),
            "message": speedup_message,
            "training_speedup_minutes": account.training_speedup_minutes,
            "training_speedups_note": (
                "Reserved for troop training; no training time is known"
            ),
        },
        known_limitations=(
            "No troop training costs, T9 costs, or troop training times were supplied.",
            "Speedups are not evaluated for economic optimality.",
            "Resource and duration milestones are confirmed from Server 283 UI "
            "observations.",
        ),
    )


def load_account(path: Path) -> AccountState:
    with path.open(encoding="utf-8") as input_file:
        return AccountState.from_mapping(json.load(input_file))


def report_as_dict(report: PlannerReport) -> dict[str, Any]:
    return asdict(report)


def render_report(report: PlannerReport) -> str:
    account, t9, rl = report.account, report.t9_readiness, report.s28_preparation
    recovery, speedups = report.post_war_recovery, report.speedup_readiness
    lines = [
        "DOCTOR STATUS",
        f"Resources (USER ENTERED): {account.resources}",
        "Sanctuary 27 remaining seconds (USER ENTERED): "
        f"{account.sanctuary_27_remaining_seconds}",
        "",
        "T9 READINESS",
        f"Training Grounds 27 (CONFIRMED FACT): {t9['status']}",
        f"Resource gaps (CALCULATED): {t9['gaps']}",
        "Readiness percentage (CALCULATED; minimum resource ratio, capped at 100): "
        f"{t9['readiness_percentage']}%",
        f"Milestone provenance (CONFIRMED FACT): {t9['provenance']}",
        "",
        "S28 PREPARATION",
        f"Research Lab 27 (CONFIRMED FACT): {rl['status']}",
        f"Resource gaps (CALCULATED): {rl['gaps']}",
        "Combined S27 follow-on bank gaps (CALCULATED): "
        f"{report.combined_s27_follow_on_bank['gaps']}",
        "",
        "POST-WAR RECOVERY",
        f"Current T8 troops (USER ENTERED): {recovery['current_t8_troops']}",
        "Recoverable/wounded troops (USER ENTERED): "
        f"{recovery['recoverable_or_wounded_troops']}",
        "Additional troops needed for target (CALCULATED): "
        f"{recovery['additional_troops_needed_for_target']}",
        "Natural rebuild (UNKNOWN): "
        f"{recovery['natural_rebuild']}; future T9 transition (UNKNOWN): "
        f"{recovery['future_t9_transition']}",
        "",
        "SPEEDUP READINESS",
        "Construction speedups (USER ENTERED): "
        f"{speedups['construction_speedup_minutes']} minutes",
        "S27 could finish up to "
        f"{speedups['maximum_seconds_sooner_if_all_available_used']} seconds sooner "
        "(CALCULATED)",
        "Universal speedups shown separately (USER ENTERED): "
        f"{speedups['universal_speedup_minutes']} minutes",
        "Training speedups (USER ENTERED): "
        f"{speedups['training_speedup_minutes']} minutes; rebuild benefit (UNKNOWN)",
        speedups["message"],
        "",
        "KNOWN LIMITATIONS",
        *[f"- {limitation}" for limitation in report.known_limitations],
    ]
    return "\n".join(lines)


def _funding(
    holdings: Mapping[str, int], requirements: Mapping[str, int]
) -> dict[str, Any]:
    gaps = _gaps(holdings, requirements)
    ratios = [holdings[resource] / requirements[resource] for resource in RESOURCES]
    return {
        "ready": all(gap == 0 for gap in gaps.values()),
        "gaps": gaps,
        "percentage": round(min(ratios) * 100, 2),
    }


def _gaps(
    holdings: Mapping[str, int], requirements: Mapping[str, int]
) -> dict[str, int]:
    return {
        resource: max(requirements[resource] - holdings[resource], 0)
        for resource in RESOURCES
    }


def _required_int(data: Mapping[str, Any], key: str) -> int:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer")
    return value


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("optional troop values must be null or a non-negative integer")
    return value
