"""Bounded cash-pack valuation for explicit research-scroll deficits.

This Layer 2 bridge accepts normalized acquisition options supplied by a
caller and compares them with ``PathDeficit.study_scrolls``. It does not read
Shop Doctor or Pack Oracle directly, infer missing prices or purchase limits,
or treat a pack listing as verified game truth. Callers remain responsible for
adapting evidence-backed pack observations into :class:`AcquisitionOption`.

The current solver optimizes only Study Scroll coverage. Consequently,
``resource_coverage_pct`` and ``speedup_coverage_pct`` are returned as ``0.0``
to mean *not evaluated by this API*, not factual zero coverage. A future API
would need explicit resource and speedup deficits before those percentages
could be calculated honestly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

_HUNDRED = Decimal(100)
_NOT_EVALUATED_COVERAGE = 0.0


@dataclass(frozen=True, slots=True)
class AcquisitionOption:
    """One explicitly supplied, bounded cash acquisition option.

    Resource quantities use millions and speedup quantities use minutes.
    ``purchase_limit`` is the maximum number available in the evaluated
    scenario; zero means the option is currently unavailable.
    """

    pack_id: str
    name: str
    cost_usd: float
    timber_m: float = 0.0
    grain_m: float = 0.0
    herbs_m: float = 0.0
    study_scrolls: int = 0
    universal_speedups_min: int = 0
    research_speedups_min: int = 0
    purchase_limit: int = 1

    def __post_init__(self) -> None:
        _non_empty_string(self.pack_id, "AcquisitionOption.pack_id")
        _non_empty_string(self.name, "AcquisitionOption.name")
        _positive_float(self.cost_usd, "AcquisitionOption.cost_usd")
        _non_negative_float(self.timber_m, "AcquisitionOption.timber_m")
        _non_negative_float(self.grain_m, "AcquisitionOption.grain_m")
        _non_negative_float(self.herbs_m, "AcquisitionOption.herbs_m")
        _non_negative_int(self.study_scrolls, "AcquisitionOption.study_scrolls")
        _non_negative_int(
            self.universal_speedups_min,
            "AcquisitionOption.universal_speedups_min",
        )
        _non_negative_int(
            self.research_speedups_min,
            "AcquisitionOption.research_speedups_min",
        )
        _non_negative_int(self.purchase_limit, "AcquisitionOption.purchase_limit")


@dataclass(frozen=True, slots=True)
class PackCoverageResult:
    """Minimum-cost scroll coverage selected from bounded options.

    A successful result always fully covers the requested scroll deficit.
    ``resource_coverage_pct`` and ``speedup_coverage_pct`` are currently the
    documented ``0.0`` not-evaluated sentinel described in the module
    docstring.
    """

    selected_packs: list[tuple[AcquisitionOption, int]]
    total_cost_usd: float
    scroll_coverage_pct: float
    resource_coverage_pct: float
    speedup_coverage_pct: float

    def __post_init__(self) -> None:
        if not isinstance(self.selected_packs, list):
            raise TypeError("PackCoverageResult.selected_packs must be a list")

        seen_pack_ids: set[str] = set()
        for index, selection in enumerate(self.selected_packs):
            if not isinstance(selection, tuple) or len(selection) != 2:
                raise TypeError(
                    "PackCoverageResult.selected_packs entries must be "
                    "(AcquisitionOption, quantity) tuples"
                )
            option, quantity = selection
            if not isinstance(option, AcquisitionOption):
                raise TypeError(
                    "PackCoverageResult.selected_packs entries must contain "
                    "AcquisitionOption instances"
                )
            _positive_int(
                quantity,
                f"PackCoverageResult.selected_packs[{index}].quantity",
            )
            if quantity > option.purchase_limit:
                raise ValueError(
                    f"selected quantity for {option.pack_id!r} exceeds its "
                    "purchase_limit"
                )
            if option.pack_id in seen_pack_ids:
                raise ValueError(
                    "PackCoverageResult.selected_packs contains duplicate "
                    f"pack_id {option.pack_id!r}"
                )
            seen_pack_ids.add(option.pack_id)

        _non_negative_float(self.total_cost_usd, "PackCoverageResult.total_cost_usd")
        _percentage(
            self.scroll_coverage_pct,
            "PackCoverageResult.scroll_coverage_pct",
        )
        _percentage(
            self.resource_coverage_pct,
            "PackCoverageResult.resource_coverage_pct",
        )
        _percentage(
            self.speedup_coverage_pct,
            "PackCoverageResult.speedup_coverage_pct",
        )


@dataclass(frozen=True, slots=True)
class _Candidate:
    cost: Decimal
    scrolls: int
    counts: tuple[int, ...]


def evaluate_pack_scroll_efficiency(
    options: list[AcquisitionOption],
) -> list[tuple[AcquisitionOption, float]]:
    """Return options ranked by descending Study Scrolls per USD.

    The calculation is a transparent marginal-value comparison only; its
    ranking is not used as a substitute for the exact bounded solver.
    Options with no Study Scrolls have an efficiency of ``0.0``.
    """

    checked_options = _validated_options(options)
    ranked = [
        (
            option,
            Decimal(option.study_scrolls) / Decimal(str(option.cost_usd)),
        )
        for option in checked_options
    ]
    ranked.sort(key=lambda item: (-item[1], item[0].pack_id, item[0].name))
    return [(option, float(efficiency)) for option, efficiency in ranked]


def solve_minimum_cost_scroll_coverage(
    scroll_deficit: int,
    options: list[AcquisitionOption],
) -> PackCoverageResult:
    """Return the exact minimum-cost bounded plan covering ``scroll_deficit``.

    Dynamic programming evaluates discrete purchase counts subject to every
    option's ``purchase_limit``. The primary objective is minimum USD cost;
    equal-cost plans prefer less overfill, fewer packs, and then a stable
    pack-ID selection order.

    Raises:
        ValueError: If the bounded catalog cannot cover the requested deficit.
    """

    _non_negative_int(scroll_deficit, "scroll_deficit")
    checked_options = _validated_options(options)
    ordered_options = sorted(
        checked_options, key=lambda option: (option.pack_id, option.name)
    )

    if scroll_deficit == 0:
        return PackCoverageResult(
            selected_packs=[],
            total_cost_usd=0.0,
            scroll_coverage_pct=100.0,
            resource_coverage_pct=_NOT_EVALUATED_COVERAGE,
            speedup_coverage_pct=_NOT_EVALUATED_COVERAGE,
        )

    maximum_capacity = sum(
        option.study_scrolls * option.purchase_limit for option in ordered_options
    )
    if maximum_capacity < scroll_deficit:
        shortfall = scroll_deficit - maximum_capacity
        raise ValueError(
            "scroll deficit cannot be satisfied: maximum bounded capacity is "
            f"{maximum_capacity:,} for a deficit of {scroll_deficit:,} "
            f"(shortfall {shortfall:,})"
        )

    usable_options = [
        option
        for option in ordered_options
        if option.study_scrolls > 0 and option.purchase_limit > 0
    ]
    states: dict[int, _Candidate] = {
        0: _Candidate(cost=Decimal(0), scrolls=0, counts=())
    }

    for option in usable_options:
        next_states: dict[int, _Candidate] = {}
        useful_limit = min(
            option.purchase_limit,
            _ceiling_division(scroll_deficit, option.study_scrolls),
        )
        option_cost = Decimal(str(option.cost_usd))

        for candidate in states.values():
            for quantity in range(useful_limit + 1):
                scrolls = candidate.scrolls + option.study_scrolls * quantity
                state_key = min(scrolls, scroll_deficit)
                proposal = _Candidate(
                    cost=candidate.cost + option_cost * quantity,
                    scrolls=scrolls,
                    counts=(*candidate.counts, quantity),
                )
                current = next_states.get(state_key)
                if current is None or _candidate_key(proposal) < _candidate_key(
                    current
                ):
                    next_states[state_key] = proposal
        states = next_states

    solution = states.get(scroll_deficit)
    if solution is None:
        raise RuntimeError(
            "bounded scroll solver failed despite sufficient catalog capacity"
        )

    selected_packs = [
        (option, quantity)
        for option, quantity in zip(usable_options, solution.counts, strict=True)
        if quantity > 0
    ]
    coverage = min(
        Decimal(solution.scrolls) / Decimal(scroll_deficit) * _HUNDRED,
        _HUNDRED,
    )
    return PackCoverageResult(
        selected_packs=selected_packs,
        total_cost_usd=float(solution.cost),
        scroll_coverage_pct=float(coverage),
        resource_coverage_pct=_NOT_EVALUATED_COVERAGE,
        speedup_coverage_pct=_NOT_EVALUATED_COVERAGE,
    )


def _candidate_key(candidate: _Candidate) -> tuple[Decimal, int, int, tuple[int, ...]]:
    return (
        candidate.cost,
        candidate.scrolls,
        sum(candidate.counts),
        tuple(-count for count in candidate.counts),
    )


def _validated_options(
    options: list[AcquisitionOption],
) -> list[AcquisitionOption]:
    if not isinstance(options, list):
        raise TypeError("options must be a list of AcquisitionOption instances")

    seen_pack_ids: set[str] = set()
    for index, option in enumerate(options):
        if not isinstance(option, AcquisitionOption):
            raise TypeError(f"options[{index}] must be an AcquisitionOption")
        if option.pack_id in seen_pack_ids:
            raise ValueError(f"options contains duplicate pack_id {option.pack_id!r}")
        seen_pack_ids.add(option.pack_id)
    return list(options)


def _ceiling_division(dividend: int, divisor: int) -> int:
    return (dividend + divisor - 1) // divisor


def _non_empty_string(value: str, field: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")


def _non_negative_int(value: int, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")


def _positive_int(value: int, field: str) -> None:
    _non_negative_int(value, field)
    if value == 0:
        raise ValueError(f"{field} must be positive")


def _non_negative_float(value: float, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{field} must be non-negative and finite")


def _positive_float(value: float, field: str) -> None:
    _non_negative_float(value, field)
    if value == 0:
        raise ValueError(f"{field} must be positive")


def _percentage(value: float, field: str) -> None:
    _non_negative_float(value, field)
    if value > 100:
        raise ValueError(f"{field} must not exceed 100")
