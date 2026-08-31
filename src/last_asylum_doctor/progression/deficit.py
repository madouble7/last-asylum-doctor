"""Deterministic progression deficits and coarse timeline projections.

This Layer 2 module calculates only from supplied progression totals,
inventory balances, and run-rate assumptions. It does not infer missing
inventory, resource income, pack availability, or monetary value. The zero
defaults on :class:`InventoryState` are explicit scenario values; callers
must not use them as substitutes for unknown account observations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

from .resolver import PathTotals

_MINUTES_PER_DAY = Decimal(1_440)
_ZERO = Decimal(0)

_LIMITING_FACTORS = frozenset(
    {
        "none",
        "research_time",
        "study_scrolls",
        "research_time_and_study_scrolls",
        "resources_unmodeled",
        "resources_unmodeled_and_study_scrolls",
    }
)


@dataclass(frozen=True, slots=True)
class InventoryState:
    """Explicit inventory balances applicable to a research path.

    Resource values use millions. Speedup values use minutes. Universal and
    research speedups are both considered applicable to research; other
    speedup types intentionally do not appear here.
    """

    timber_m: float = 0.0
    grain_m: float = 0.0
    herbs_m: float = 0.0
    study_scrolls: int = 0
    universal_speedups_minutes: int = 0
    research_speedups_minutes: int = 0

    def __post_init__(self) -> None:
        _non_negative_float(self.timber_m, "InventoryState.timber_m")
        _non_negative_float(self.grain_m, "InventoryState.grain_m")
        _non_negative_float(self.herbs_m, "InventoryState.herbs_m")
        _non_negative_int(self.study_scrolls, "InventoryState.study_scrolls")
        _non_negative_int(
            self.universal_speedups_minutes,
            "InventoryState.universal_speedups_minutes",
        )
        _non_negative_int(
            self.research_speedups_minutes,
            "InventoryState.research_speedups_minutes",
        )


@dataclass(frozen=True, slots=True)
class PathDeficit:
    """Remaining requirements after applying explicit inventory balances.

    ``raw_time_minutes`` preserves the path's source-normalized duration.
    ``speedup_minutes_deficit`` is that duration less currently owned,
    applicable speedups, before a scenario-specific research-speed bonus.
    """

    timber_m: float
    grain_m: float
    herbs_m: float
    study_scrolls: int
    raw_time_minutes: int
    speedup_minutes_deficit: int

    def __post_init__(self) -> None:
        _non_negative_float(self.timber_m, "PathDeficit.timber_m")
        _non_negative_float(self.grain_m, "PathDeficit.grain_m")
        _non_negative_float(self.herbs_m, "PathDeficit.herbs_m")
        _non_negative_int(self.study_scrolls, "PathDeficit.study_scrolls")
        _non_negative_int(
            self.raw_time_minutes, "PathDeficit.raw_time_minutes"
        )
        _non_negative_int(
            self.speedup_minutes_deficit,
            "PathDeficit.speedup_minutes_deficit",
        )
        if self.speedup_minutes_deficit > self.raw_time_minutes:
            raise ValueError(
                "PathDeficit.speedup_minutes_deficit cannot exceed "
                "raw_time_minutes"
            )


@dataclass(frozen=True, slots=True)
class TimelineProjection:
    """Continuous-rate projection for the modeled timeline dimensions.

    Base-resource acquisition is not projected because the function receives
    no timber, grain, or herb income rates. If any such deficit remains,
    ``limiting_factor`` reports an unmodeled resource blocker and the day
    fields are timer/scroll projections rather than a complete readiness
    date.
    """

    natural_days: float
    accelerated_days: float
    scroll_bottleneck_days: float
    limiting_factor: str

    def __post_init__(self) -> None:
        _non_negative_float(self.natural_days, "TimelineProjection.natural_days")
        _non_negative_float(
            self.accelerated_days, "TimelineProjection.accelerated_days"
        )
        if (
            isinstance(self.scroll_bottleneck_days, bool)
            or not isinstance(self.scroll_bottleneck_days, (int, float))
            or math.isnan(float(self.scroll_bottleneck_days))
            or self.scroll_bottleneck_days < 0
        ):
            raise ValueError(
                "TimelineProjection.scroll_bottleneck_days must be "
                "non-negative"
            )
        if self.limiting_factor not in _LIMITING_FACTORS:
            raise ValueError(
                "TimelineProjection.limiting_factor must be one of: "
                + ", ".join(sorted(_LIMITING_FACTORS))
            )


def calculate_deficit(
    totals: PathTotals, inventory: InventoryState
) -> PathDeficit:
    """Return net positive path requirements after applying inventory.

    Resource subtraction is performed with :class:`~decimal.Decimal` because
    canonical ``PathTotals`` stores resource millions as decimals while the
    requested inventory boundary uses floats. Conversion through ``str``
    avoids introducing binary floating-point residue into the subtraction.
    Might gain is intentionally excluded because it is an outcome, not a
    progression cost.
    """

    if not isinstance(totals, PathTotals):
        raise TypeError("totals must be a PathTotals instance")
    if not isinstance(inventory, InventoryState):
        raise TypeError("inventory must be an InventoryState instance")

    _non_negative_decimal(totals.timber_m, "PathTotals.timber_m")
    _non_negative_decimal(totals.grain_m, "PathTotals.grain_m")
    _non_negative_decimal(totals.herbs_m, "PathTotals.herbs_m")
    _non_negative_int(totals.study_scrolls, "PathTotals.study_scrolls")
    _non_negative_int(
        totals.normalized_minutes, "PathTotals.normalized_minutes"
    )

    speedups_available = (
        inventory.universal_speedups_minutes
        + inventory.research_speedups_minutes
    )
    return PathDeficit(
        timber_m=_resource_deficit(totals.timber_m, inventory.timber_m),
        grain_m=_resource_deficit(totals.grain_m, inventory.grain_m),
        herbs_m=_resource_deficit(totals.herbs_m, inventory.herbs_m),
        study_scrolls=max(totals.study_scrolls - inventory.study_scrolls, 0),
        raw_time_minutes=totals.normalized_minutes,
        speedup_minutes_deficit=max(
            totals.normalized_minutes - speedups_available, 0
        ),
    )


def estimate_timeline(
    deficit: PathDeficit,
    daily_scroll_income: int = 0,
    daily_speedup_income_minutes: int = 0,
    research_speed_pct: float = 0.0,
) -> TimelineProjection:
    """Project research and scroll horizons from explicit scenario inputs.

    ``natural_days`` applies the constant research-speed bonus but no
    speedups. ``accelerated_days`` also applies currently owned speedups and
    assumes the supplied daily speedup income accrues continuously and is
    used immediately. ``scroll_bottleneck_days`` uses the same continuous
    average convention; it is infinity when scrolls are required but the
    supplied scroll income is zero.

    The aggregate calculation does not model upgrade-by-upgrade collection,
    queue downtime, discrete daily claims, or base-resource income. It is a
    deterministic scenario projection, not an observed completion date.
    """

    if not isinstance(deficit, PathDeficit):
        raise TypeError("deficit must be a PathDeficit instance")
    _non_negative_int(daily_scroll_income, "daily_scroll_income")
    _non_negative_int(
        daily_speedup_income_minutes, "daily_speedup_income_minutes"
    )
    _non_negative_float(research_speed_pct, "research_speed_pct")

    speed_multiplier = Decimal(1) + Decimal(str(research_speed_pct)) / Decimal(100)
    adjusted_timer_minutes = Decimal(deficit.raw_time_minutes) / speed_multiplier
    owned_speedups_applied = Decimal(
        deficit.raw_time_minutes - deficit.speedup_minutes_deficit
    )
    remaining_timer_minutes = max(
        adjusted_timer_minutes - owned_speedups_applied, _ZERO
    )

    natural_days_value = adjusted_timer_minutes / _MINUTES_PER_DAY
    accelerated_rate = _MINUTES_PER_DAY + Decimal(
        daily_speedup_income_minutes
    )
    accelerated_days_value = remaining_timer_minutes / accelerated_rate

    if deficit.study_scrolls == 0:
        scroll_days_value: Decimal | None = _ZERO
    elif daily_scroll_income == 0:
        scroll_days_value = None
    else:
        scroll_days_value = Decimal(deficit.study_scrolls) / Decimal(
            daily_scroll_income
        )

    limiting_factor = _limiting_factor(
        deficit, accelerated_days_value, scroll_days_value
    )
    return TimelineProjection(
        natural_days=_finite_float(natural_days_value, "natural_days"),
        accelerated_days=_finite_float(
            accelerated_days_value, "accelerated_days"
        ),
        scroll_bottleneck_days=(
            math.inf
            if scroll_days_value is None
            else _finite_float(scroll_days_value, "scroll_bottleneck_days")
        ),
        limiting_factor=limiting_factor,
    )


def _limiting_factor(
    deficit: PathDeficit,
    accelerated_days: Decimal,
    scroll_days: Decimal | None,
) -> str:
    resources_unmodeled = (
        deficit.timber_m > 0 or deficit.grain_m > 0 or deficit.herbs_m > 0
    )
    if resources_unmodeled and scroll_days is None:
        return "resources_unmodeled_and_study_scrolls"
    if resources_unmodeled:
        return "resources_unmodeled"
    if scroll_days is None:
        return "study_scrolls"
    if accelerated_days == _ZERO and scroll_days == _ZERO:
        return "none"
    if accelerated_days > scroll_days:
        return "research_time"
    if scroll_days > accelerated_days:
        return "study_scrolls"
    return "research_time_and_study_scrolls"


def _resource_deficit(required: Decimal, available: float) -> float:
    remaining = max(required - Decimal(str(available)), _ZERO)
    return _finite_float(remaining, "resource deficit")


def _non_negative_decimal(value: Decimal, field: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be a Decimal")
    if not value.is_finite() or value < 0:
        raise ValueError(f"{field} must be non-negative and finite")


def _non_negative_int(value: int, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")


def _non_negative_float(value: float, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{field} must be non-negative and finite")


def _finite_float(value: Decimal, field: str) -> float:
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"{field} is too large for a finite float") from error
    if not math.isfinite(result):
        raise ValueError(f"{field} is too large for a finite float")
    return result
