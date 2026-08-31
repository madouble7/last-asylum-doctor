"""Deterministic research progression and dependency resolution.

The resolver operates only on supplied Layer 1 research nodes, costs, and
prerequisite rules. It does not infer missing edges or Institute/building
gates. Results are therefore complete only for the prerequisite evidence
loaded into :class:`ProgressionGraph`.
"""

from __future__ import annotations

import heapq
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class ProgressionDataError(ValueError):
    """Raised when progression input is incomplete, invalid, or ambiguous."""


class ProgressionCycleError(ProgressionDataError):
    """Raised when prerequisite records do not form a directed acyclic graph."""


@dataclass(frozen=True, slots=True)
class ResearchNode:
    """Identity and level bounds for one research node."""

    node_id: str
    branch: str
    name: str
    max_level: int


@dataclass(frozen=True, slots=True)
class ResearchUpgradeCost:
    """Canonical cost and gain values for one node-level transition."""

    cost_id: str
    node_id: str
    level: int
    timber_m: Decimal
    grain_m: Decimal
    herbs_m: Decimal
    study_scrolls: int
    might_gain: int
    normalized_minutes: int


@dataclass(frozen=True, slots=True)
class PrerequisiteRule:
    """One level-specific directed prerequisite rule."""

    rule_id: str
    target_node_id: str
    target_level: int
    required_node_id: str
    required_level: int


@dataclass(frozen=True, slots=True)
class UpgradeStep:
    """One required level transition in a resolved progression path."""

    node_id: str
    level: int
    cost: ResearchUpgradeCost

    @property
    def cost_id(self) -> str:
        """Return the stable ``node_id:level`` identity for this step."""

        return self.cost.cost_id


@dataclass(frozen=True, slots=True)
class PathTotals:
    """Aggregated resources, time, and might for a progression path."""

    timber_m: Decimal
    grain_m: Decimal
    herbs_m: Decimal
    study_scrolls: int
    might_gain: int
    normalized_minutes: int


@dataclass(frozen=True, slots=True)
class MissingPrerequisite:
    """A direct prerequisite whose required level is not currently met."""

    rule_id: str
    target_node_id: str
    target_level: int
    required_node_id: str
    required_level: int
    current_level: int


@dataclass(frozen=True, slots=True)
class _ParsedUserState:
    current_levels: dict[str, int]
    planned_levels: dict[str, int]


class ProgressionGraph:
    """Validated research graph with deterministic path resolution."""

    def __init__(
        self,
        node_records: Iterable[Mapping[str, Any]],
        cost_records: Iterable[Mapping[str, Any]],
        prerequisite_records: Iterable[Mapping[str, Any]],
    ) -> None:
        self._nodes = self._parse_nodes(node_records)
        self._costs = self._parse_costs(cost_records)
        self._rules, self._rules_by_target = self._parse_prerequisites(
            prerequisite_records
        )
        self._validate_cost_coverage()
        self._validate_acyclic()

    @classmethod
    def from_documents(
        cls,
        nodes_document: Mapping[str, Any],
        costs_document: Mapping[str, Any],
        prerequisites_document: Mapping[str, Any],
    ) -> ProgressionGraph:
        """Build a graph from the three canonical JSON root objects."""

        return cls(
            _records(nodes_document, "research nodes"),
            _records(costs_document, "research costs"),
            _records(prerequisites_document, "research prerequisites"),
        )

    @classmethod
    def from_json_files(
        cls,
        nodes_path: str | Path,
        costs_path: str | Path,
        prerequisites_path: str | Path,
    ) -> ProgressionGraph:
        """Load canonical JSON files and build a validated graph."""

        return cls.from_documents(
            _load_document(nodes_path),
            _load_document(costs_path),
            _load_document(prerequisites_path),
        )

    def resolve_target_path(
        self,
        target_node_id: str | int,
        target_level: int,
        current_user_state: Mapping[Any, Any],
    ) -> tuple[UpgradeStep, ...]:
        """Resolve the minimal, deterministic transition sequence.

        A plain ``{node_id: current_level}`` state resolves only the requested
        target and its supplied prerequisite closure. A canonical state
        document containing ``states`` also contributes every declared
        ``target_level`` as an explicit planned goal. This preserves user
        intent without treating those planned levels as prerequisite facts.
        """

        target_id = self._known_node_id(target_node_id, "target_node_id")
        requested_level = self._valid_node_level(
            target_id, target_level, "target_level"
        )
        state = self._parse_user_state(current_user_state)
        if target_id not in state.current_levels:
            raise ProgressionDataError(
                f"current_user_state has no observed level for target {target_id}"
            )
        requirements = self._initial_requirements(target_id, requested_level, state)
        self._expand_prerequisite_requirements(requirements, state.current_levels)
        node_order = self._topological_requirement_order(requirements)

        steps: list[UpgradeStep] = []
        for node_id in node_order:
            first_level = state.current_levels[node_id] + 1
            for level in range(first_level, requirements[node_id] + 1):
                cost = self._costs[(node_id, level)]
                steps.append(UpgradeStep(node_id=node_id, level=level, cost=cost))
        return tuple(steps)

    def find_missing_prerequisites(
        self,
        node_id: str | int,
        level: int,
        current_user_state: Mapping[Any, Any],
    ) -> tuple[MissingPrerequisite, ...]:
        """Return direct, currently unsatisfied prerequisite rules."""

        target_id = self._known_node_id(node_id, "node_id")
        target_level = self._valid_node_level(target_id, level, "level")
        state = self._parse_user_state(current_user_state)
        missing: list[MissingPrerequisite] = []
        for rule in self._active_rules(target_id, target_level):
            if rule.required_node_id not in state.current_levels:
                raise ProgressionDataError(
                    "current_user_state has no observed level for prerequisite "
                    f"{rule.required_node_id}"
                )
            current_level = state.current_levels[rule.required_node_id]
            if current_level < rule.required_level:
                missing.append(
                    MissingPrerequisite(
                        rule_id=rule.rule_id,
                        target_node_id=rule.target_node_id,
                        target_level=rule.target_level,
                        required_node_id=rule.required_node_id,
                        required_level=rule.required_level,
                        current_level=current_level,
                    )
                )
        return tuple(missing)

    def calculate_path_totals(self, path_steps: Iterable[UpgradeStep]) -> PathTotals:
        """Aggregate stored row values for a sequence of upgrade steps.

        ``might_gain`` is summed exactly as stored. The resolver does not
        reinterpret whether the source field is marginal or cumulative.
        """

        timber_m = Decimal(0)
        grain_m = Decimal(0)
        herbs_m = Decimal(0)
        study_scrolls = 0
        might_gain = 0
        normalized_minutes = 0

        for step in path_steps:
            expected_cost = self._costs.get((step.node_id, step.level))
            if expected_cost is None or step.cost != expected_cost:
                raise ProgressionDataError(
                    f"path step {step.node_id}:{step.level:02d} "
                    "does not belong to this graph"
                )
            timber_m += step.cost.timber_m
            grain_m += step.cost.grain_m
            herbs_m += step.cost.herbs_m
            study_scrolls += step.cost.study_scrolls
            might_gain += step.cost.might_gain
            normalized_minutes += step.cost.normalized_minutes

        return PathTotals(
            timber_m=timber_m,
            grain_m=grain_m,
            herbs_m=herbs_m,
            study_scrolls=study_scrolls,
            might_gain=might_gain,
            normalized_minutes=normalized_minutes,
        )

    def _parse_nodes(
        self, records: Iterable[Mapping[str, Any]]
    ) -> dict[str, ResearchNode]:
        nodes: dict[str, ResearchNode] = {}
        for index, record in enumerate(records):
            path = f"research_nodes.records[{index}]"
            node_id = _text(record.get("node_id"), f"{path}.node_id")
            if node_id in nodes:
                raise ProgressionDataError(f"duplicate node_id: {node_id}")
            nodes[node_id] = ResearchNode(
                node_id=node_id,
                branch=_text(record.get("branch"), f"{path}.branch"),
                name=_text(record.get("name"), f"{path}.name"),
                max_level=_positive_int(record.get("max_level"), f"{path}.max_level"),
            )
        if not nodes:
            raise ProgressionDataError("research node dataset is empty")
        return nodes

    def _parse_costs(
        self, records: Iterable[Mapping[str, Any]]
    ) -> dict[tuple[str, int], ResearchUpgradeCost]:
        costs: dict[tuple[str, int], ResearchUpgradeCost] = {}
        seen_cost_ids: set[str] = set()
        for index, record in enumerate(records):
            path = f"research_upgrade_costs.records[{index}]"
            node_id = self._known_node_id(record.get("node_id"), f"{path}.node_id")
            level = self._valid_node_level(
                node_id, record.get("level"), f"{path}.level"
            )
            key = (node_id, level)
            if key in costs:
                raise ProgressionDataError(
                    f"duplicate research cost for {node_id} level {level}"
                )
            cost_id = _text(record.get("cost_id"), f"{path}.cost_id")
            expected_cost_id = _level_id(node_id, level)
            if cost_id != expected_cost_id:
                raise ProgressionDataError(
                    f"{path}.cost_id must be {expected_cost_id!r}"
                )
            if cost_id in seen_cost_ids:
                raise ProgressionDataError(f"duplicate cost_id: {cost_id}")
            seen_cost_ids.add(cost_id)
            costs[key] = ResearchUpgradeCost(
                cost_id=cost_id,
                node_id=node_id,
                level=level,
                timber_m=_non_negative_decimal(
                    record.get("timber_m"), f"{path}.timber_m"
                ),
                grain_m=_non_negative_decimal(record.get("grain_m"), f"{path}.grain_m"),
                herbs_m=_non_negative_decimal(record.get("herbs_m"), f"{path}.herbs_m"),
                study_scrolls=_non_negative_int(
                    record.get("study_scrolls"), f"{path}.study_scrolls"
                ),
                might_gain=_non_negative_int(
                    record.get("might_gain"), f"{path}.might_gain"
                ),
                normalized_minutes=_non_negative_int(
                    record.get("normalized_minutes"),
                    f"{path}.normalized_minutes",
                ),
            )
        return costs

    def _parse_prerequisites(
        self, records: Iterable[Mapping[str, Any]]
    ) -> tuple[
        tuple[PrerequisiteRule, ...],
        dict[str, tuple[PrerequisiteRule, ...]],
    ]:
        rules: list[PrerequisiteRule] = []
        rules_by_target: defaultdict[str, list[PrerequisiteRule]] = defaultdict(list)
        seen_rule_ids: set[str] = set()
        seen_edges: set[tuple[str, int, str, int]] = set()

        for index, record in enumerate(records):
            path = f"research_prerequisites.records[{index}]"
            rule_id = _text(record.get("rule_id"), f"{path}.rule_id")
            if rule_id in seen_rule_ids:
                raise ProgressionDataError(f"duplicate rule_id: {rule_id}")
            seen_rule_ids.add(rule_id)
            target_node_id = self._known_node_id(
                record.get("target_node_id"), f"{path}.target_node_id"
            )
            required_node_id = self._known_node_id(
                record.get("required_node_id"), f"{path}.required_node_id"
            )
            target_level = self._valid_node_level(
                target_node_id, record.get("target_level"), f"{path}.target_level"
            )
            required_level = self._valid_node_level(
                required_node_id,
                record.get("required_level"),
                f"{path}.required_level",
            )
            edge = (
                target_node_id,
                target_level,
                required_node_id,
                required_level,
            )
            if edge in seen_edges:
                raise ProgressionDataError(
                    f"duplicate prerequisite tuple in rule {rule_id}"
                )
            seen_edges.add(edge)
            rule = PrerequisiteRule(
                rule_id=rule_id,
                target_node_id=target_node_id,
                target_level=target_level,
                required_node_id=required_node_id,
                required_level=required_level,
            )
            rules.append(rule)
            rules_by_target[target_node_id].append(rule)

        rules.sort(key=_rule_sort_key)
        frozen_by_target = {
            node_id: tuple(sorted(node_rules, key=_rule_sort_key))
            for node_id, node_rules in rules_by_target.items()
        }
        return tuple(rules), frozen_by_target

    def _validate_cost_coverage(self) -> None:
        for node_id, node in self._nodes.items():
            missing = [
                level
                for level in range(1, node.max_level + 1)
                if (node_id, level) not in self._costs
            ]
            if missing:
                raise ProgressionDataError(
                    f"node {node_id} is missing costs for levels {missing}"
                )

    def _validate_acyclic(self) -> None:
        successors: dict[str, set[str]] = {node_id: set() for node_id in self._nodes}
        indegree = dict.fromkeys(self._nodes, 0)
        for rule in self._rules:
            if rule.target_node_id not in successors[rule.required_node_id]:
                successors[rule.required_node_id].add(rule.target_node_id)
                indegree[rule.target_node_id] += 1

        ready = [
            (_node_sort_key(node_id), node_id)
            for node_id, degree in indegree.items()
            if degree == 0
        ]
        heapq.heapify(ready)
        visited = 0
        while ready:
            _, node_id = heapq.heappop(ready)
            visited += 1
            for successor in sorted(successors[node_id], key=_node_sort_key):
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    heapq.heappush(ready, (_node_sort_key(successor), successor))

        if visited != len(self._nodes):
            cycle_nodes = sorted(
                (node_id for node_id, degree in indegree.items() if degree > 0),
                key=_node_sort_key,
            )
            raise ProgressionCycleError(
                "research prerequisite cycle detected among nodes: "
                + ", ".join(cycle_nodes)
            )

    def _parse_user_state(
        self, current_user_state: Mapping[Any, Any]
    ) -> _ParsedUserState:
        if not isinstance(current_user_state, Mapping):
            raise ProgressionDataError("current_user_state must be a mapping")
        current_levels: dict[str, int] = {}
        planned_levels: dict[str, int] = {}

        if "states" in current_user_state:
            raw_states = _sequence(
                current_user_state["states"], "current_user_state.states"
            )
            for index, value in enumerate(raw_states):
                path = f"current_user_state.states[{index}]"
                record = _mapping(value, path)
                node_id = self._known_node_id(record.get("node_id"), f"{path}.node_id")
                if node_id in current_levels:
                    raise ProgressionDataError(
                        f"ambiguous duplicate state for node {node_id}"
                    )
                current_levels[node_id] = self._valid_state_level(
                    node_id, record.get("current_level"), f"{path}.current_level"
                )
                if "target_level" in record:
                    planned_levels[node_id] = self._valid_state_level(
                        node_id,
                        record["target_level"],
                        f"{path}.target_level",
                    )
        else:
            for raw_node_id, value in current_user_state.items():
                node_id = self._known_node_id(raw_node_id, "current_user_state key")
                if node_id in current_levels:
                    raise ProgressionDataError(
                        f"ambiguous duplicate state key for node {node_id}"
                    )
                if isinstance(value, Mapping):
                    current_levels[node_id] = self._valid_state_level(
                        node_id,
                        value.get("current_level"),
                        f"current_user_state[{node_id}].current_level",
                    )
                    if "target_level" in value:
                        planned_levels[node_id] = self._valid_state_level(
                            node_id,
                            value["target_level"],
                            f"current_user_state[{node_id}].target_level",
                        )
                else:
                    current_levels[node_id] = self._valid_state_level(
                        node_id, value, f"current_user_state[{node_id}]"
                    )

        return _ParsedUserState(current_levels, planned_levels)

    def _initial_requirements(
        self,
        target_node_id: str,
        target_level: int,
        state: _ParsedUserState,
    ) -> dict[str, int]:
        goals = dict(state.planned_levels)
        goals[target_node_id] = max(goals.get(target_node_id, 0), target_level)
        return {
            node_id: level
            for node_id, level in goals.items()
            if level > state.current_levels[node_id]
        }

    def _expand_prerequisite_requirements(
        self, requirements: dict[str, int], current_levels: Mapping[str, int]
    ) -> None:
        pending = list(requirements)
        while pending:
            node_id = pending.pop()
            for rule in self._active_rules(node_id, requirements[node_id]):
                if rule.required_node_id not in current_levels:
                    raise ProgressionDataError(
                        "current_user_state has no observed level for prerequisite "
                        f"{rule.required_node_id}"
                    )
                current_level = current_levels[rule.required_node_id]
                previous_requirement = requirements.get(rule.required_node_id, 0)
                if (
                    rule.required_level > current_level
                    and rule.required_level > previous_requirement
                ):
                    requirements[rule.required_node_id] = rule.required_level
                    pending.append(rule.required_node_id)

    def _topological_requirement_order(
        self, requirements: Mapping[str, int]
    ) -> tuple[str, ...]:
        ordered: list[str] = []
        complete: set[str] = set()
        visiting: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in complete:
                return
            if node_id in visiting:
                raise ProgressionCycleError(
                    f"research prerequisite cycle reached at node {node_id}"
                )
            visiting.add(node_id)
            required_nodes = {
                rule.required_node_id
                for rule in self._active_rules(node_id, requirements[node_id])
                if rule.required_node_id in requirements
            }
            for required_node_id in sorted(required_nodes, key=_node_sort_key):
                visit(required_node_id)
            visiting.remove(node_id)
            complete.add(node_id)
            ordered.append(node_id)

        for node_id in sorted(requirements, key=_node_sort_key):
            visit(node_id)
        return tuple(ordered)

    def _active_rules(
        self, node_id: str, target_level: int
    ) -> tuple[PrerequisiteRule, ...]:
        return tuple(
            rule
            for rule in self._rules_by_target.get(node_id, ())
            if rule.target_level <= target_level
        )

    def _known_node_id(self, value: Any, path: str) -> str:
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ProgressionDataError(f"{path} must be a string or integer node ID")
        node_id = str(value)
        if not node_id or node_id.strip() != node_id:
            raise ProgressionDataError(f"{path} must be a non-empty node ID")
        if node_id not in self._nodes:
            raise ProgressionDataError(f"{path} references unknown node {node_id!r}")
        return node_id

    def _valid_node_level(self, node_id: str, value: Any, path: str) -> int:
        level = _positive_int(value, path)
        if level > self._nodes[node_id].max_level:
            raise ProgressionDataError(
                f"{path} exceeds node {node_id} max level "
                f"{self._nodes[node_id].max_level}"
            )
        return level

    def _valid_state_level(self, node_id: str, value: Any, path: str) -> int:
        level = _non_negative_int(value, path)
        if level > self._nodes[node_id].max_level:
            raise ProgressionDataError(
                f"{path} exceeds node {node_id} max level "
                f"{self._nodes[node_id].max_level}"
            )
        return level


def _load_document(path: str | Path) -> Mapping[str, Any]:
    source_path = Path(path)
    try:
        value = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ProgressionDataError(f"{source_path}: invalid JSON: {error}") from error
    except OSError as error:
        raise ProgressionDataError(f"{source_path}: cannot read: {error}") from error
    return _mapping(value, str(source_path))


def _records(document: Mapping[str, Any], name: str) -> tuple[Mapping[str, Any], ...]:
    values = _sequence(document.get("records"), f"{name}.records")
    return tuple(
        _mapping(value, f"{name}.records[{index}]")
        for index, value in enumerate(values)
    )


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProgressionDataError(f"{path} must be an object")
    return value


def _sequence(value: Any, path: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ProgressionDataError(f"{path} must be an array")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProgressionDataError(f"{path} must be non-empty text")
    return value


def _non_negative_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProgressionDataError(f"{path} must be a non-negative integer")
    return value


def _positive_int(value: Any, path: str) -> int:
    result = _non_negative_int(value, path)
    if result == 0:
        raise ProgressionDataError(f"{path} must be a positive integer")
    return result


def _non_negative_decimal(value: Any, path: str) -> Decimal:
    if isinstance(value, bool):
        raise ProgressionDataError(f"{path} must be a non-negative number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ProgressionDataError(f"{path} must be a number") from error
    if not result.is_finite() or result < 0:
        raise ProgressionDataError(f"{path} must be a non-negative finite number")
    return result


def _level_id(node_id: str, level: int) -> str:
    return f"{node_id}:{level:02d}"


def _node_sort_key(node_id: str) -> tuple[int, int, str]:
    if node_id.isdigit():
        return (0, int(node_id), node_id)
    return (1, 0, node_id)


def _rule_sort_key(rule: PrerequisiteRule) -> tuple[Any, ...]:
    return (
        _node_sort_key(rule.target_node_id),
        rule.target_level,
        _node_sort_key(rule.required_node_id),
        rule.required_level,
        rule.rule_id,
    )
