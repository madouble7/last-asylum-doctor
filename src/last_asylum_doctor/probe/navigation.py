"""Account-state-preserving navigation for bounded Last Asylum reconnaissance."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

PACKAGE = "com.phs.global"
DEFAULT_ADB = Path(r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe")
DEFAULT_SERVER = "283"
HISTORICAL_CLIENT_VERSION = {"version_name": "1.0.97", "version_code": "97"}


class SafeNavigationError(ValueError):
    """Raised when a proposed action is outside the navigation allowlist."""


@dataclass(frozen=True)
class OCRAnchor:
    text: str
    confidence: float = 0.0
    bbox_pixels: tuple[tuple[float, float], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Frame:
    screenshot: bytes
    screenshot_hash: str
    width: int
    height: int
    ocr_anchors: tuple[OCRAnchor, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScreenState:
    state_id: str
    semantic_name: str
    screenshot_hash: str
    perceptual_fingerprint: str
    ocr_anchors: tuple[str, ...]
    expected_controls: tuple[str, ...]
    confidence: float
    client_version: str
    first_seen: str
    last_seen: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SafeAction:
    action_type: str
    semantic_target: str
    source_state: str
    expected_next_state: str | None = None
    target_bbox: tuple[float, float, float, float] | None = None
    normalized_point: tuple[float, float] | None = None
    normalized_end: tuple[float, float] | None = None
    confidence: float = 0.0
    account_state_preserving: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FrameSource(Protocol):
    def capture(self, label: str | None = None) -> Frame: ...


class InputDriver(Protocol):
    def perform(self, action: SafeAction, frame: Frame) -> None: ...


class StateRecognizer:
    """Recognize only states supported by explicit OCR evidence."""

    _SPECS = (
        ("research_node_detail", ("research level", "current effect"), ("back",)),
        ("research_tree_index", ("development", "research"), ("back",)),
        (
            "sanctuary_main",
            ("research lab", "training grounds"),
            ("research lab", "training grounds"),
        ),
        ("research_lab", ("research lab",), ("research", "back")),
    )

    def recognize(self, frame: Frame) -> ScreenState:
        texts = tuple(_normalise(anchor.text) for anchor in frame.ocr_anchors)
        present = " ".join(texts)
        now = _utc_now()
        client_version = str(frame.metadata.get("client_version_name", "unknown"))

        if _has_text(texts, "bag") and _count_texts(
            texts, ("special", "resource", "speedup", "hero", "gear")
        ) >= 3:
            return self._state(
                frame,
                "bag_inventory",
                ("bag",),
                ("back",),
                now,
                client_version,
                confidence=0.95,
            )
        if (
            _has_text(texts, "insufficient items")
            and _has_text(texts, "owned")
            and _has_text(texts, "resource item")
            and _has_text(texts, "use")
        ):
            return self._state(
                frame,
                "insufficient_items",
                ("insufficient items", "owned", "resource item", "use"),
                ("back",),
                now,
                client_version,
                confidence=0.99,
            )
        if _has_text(texts, "kingdom war") and _count_texts(
            texts, ("weekly", "royal city", "overview", "match", "information")
        ) >= 2:
            return self._state(
                frame,
                "kingdom_war",
                ("kingdom war",),
                ("back",),
                now,
                client_version,
                confidence=0.96,
            )
        if _has_text(texts, "black ops") and _count_texts(
            texts, ("covert ops force", "treasure digger")
        ) >= 1:
            return self._state(
                frame,
                "black_ops",
                ("black ops",),
                ("back",),
                now,
                client_version,
                confidence=0.96,
            )
        if _has_text(texts, "loot") and _has_text(texts, "claim all"):
            return self._state(
                frame,
                "loot",
                ("loot", "claim all"),
                ("back",),
                now,
                client_version,
                confidence=0.99,
            )
        if (
            _has_text(texts, "upgrade")
            and _count_texts(texts, ("bag", "hero", "territory", "alliance", "mail"))
            >= 3
        ):
            return self._state(
                frame,
                "sanctuary_map",
                ("upgrade",),
                ("research lab", "training grounds"),
                now,
                client_version,
                confidence=0.92,
            )
        if _has_text(texts, "training grounds") and _count_texts(
            texts,
            (
                "upgrade training grounds",
                "current level",
                "next level",
                "soldier training",
                "requires lv.",
            ),
        ) >= 2:
            return self._state(
                frame,
                "training_grounds",
                ("training grounds",),
                ("back",),
                now,
                client_version,
                confidence=0.94,
            )
        if _has_text(texts, "upgrade") and _count_texts(
            texts,
            (
                "current level",
                "next level",
                "building level",
                "requires",
                "requirement",
                "build time",
                "construction",
            ),
        ) >= 1:
            return self._state(
                frame,
                "building_detail",
                ("upgrade",),
                ("back",),
                now,
                client_version,
                confidence=0.9,
            )
        for state_id, required, controls in self._SPECS:
            matched = tuple(term for term in required if term in present)
            if len(matched) != len(required):
                continue
            return self._state(
                frame,
                state_id,
                matched,
                controls,
                now,
                client_version,
                confidence=min(0.99, 0.55 + (0.2 * len(matched))),
            )
        return self._state(
            frame,
            "unknown",
            (),
            (),
            now,
            client_version,
            confidence=0.0,
        )

    def _state(
        self,
        frame: Frame,
        state_id: str,
        matched: tuple[str, ...],
        controls: tuple[str, ...],
        now: str,
        client_version: str,
        *,
        confidence: float,
    ) -> ScreenState:
        return ScreenState(
            state_id=state_id,
            semantic_name=state_id.replace("_", " "),
            screenshot_hash=frame.screenshot_hash,
            perceptual_fingerprint=frame.screenshot_hash[:16],
            ocr_anchors=matched,
            expected_controls=controls,
            confidence=confidence,
            client_version=client_version,
            first_seen=now,
            last_seen=now,
        )


class NavigationPolicy:
    """Explicit allowlist for account-state-preserving actions."""

    _ALLOWED_TARGETS = {
        "tap": frozenset(
            {
                "research_lab",
                "research",
                "training_grounds",
                "open_menu",
                "close_dialog",
                "switch_tab",
            }
        ),
        "swipe": frozenset({"scroll_menu"}),
        "back": frozenset({"android_back", "back"}),
    }

    def validate(self, action: SafeAction) -> None:
        if not action.account_state_preserving:
            raise SafeNavigationError("action is not marked account-state-preserving")
        allowed_targets = self._ALLOWED_TARGETS.get(action.action_type)
        if allowed_targets is None:
            raise SafeNavigationError(
                f"action type is not allowlisted: {action.action_type}"
            )
        if action.semantic_target not in allowed_targets:
            raise SafeNavigationError(
                f"semantic target is not allowlisted: {action.semantic_target}"
            )
        if not 0.0 <= action.confidence <= 1.0:
            raise SafeNavigationError("action confidence must be between 0 and 1")
        if (
            action.action_type == "tap"
            and action.normalized_point is None
            and action.target_bbox is None
        ):
            raise SafeNavigationError("tap requires a normalized point or bounding box")
        if action.action_type == "swipe" and (
            action.normalized_point is None or action.normalized_end is None
        ):
            raise SafeNavigationError("swipe requires normalized start and end points")
        for point in (action.normalized_point, action.normalized_end):
            if point is not None and not all(0.0 <= value <= 1.0 for value in point):
                raise SafeNavigationError(
                    "normalized coordinates must be between 0 and 1"
                )
        if action.target_bbox is not None and not all(
            0.0 <= value <= 1.0 for value in action.target_bbox
        ):
            raise SafeNavigationError(
                "normalized bounding boxes must be between 0 and 1"
            )


class NavigationGraph:
    """Small JSON trajectory store kept outside the factual game database."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.edges: dict[str, dict[str, Any]] = {}
        if path.exists():
            self.edges = dict(
                json.loads(path.read_text(encoding="utf-8")).get("edges", {})
            )

    def record_transition(
        self,
        action: SafeAction,
        actual_state: str,
        *,
        success: bool,
        before_hash: str,
        after_hash: str,
        client_version: str,
        verified_at: str | None = None,
    ) -> dict[str, Any]:
        key = "|".join(
            (
                action.source_state,
                action.semantic_target,
                action.expected_next_state or "",
            )
        )
        edge = self.edges.setdefault(
            key,
            {
                "source_state": action.source_state,
                "semantic_action": action.semantic_target,
                "action": action.to_dict(),
                "destination_state": action.expected_next_state,
                "success_count": 0,
                "failure_count": 0,
                "client_version": client_version,
                "evidence_screenshot_hashes": [],
            },
        )
        edge["destination_state"] = actual_state
        edge["client_version"] = client_version
        edge["last_verified_at"] = verified_at or _utc_now()
        edge["success_count" if success else "failure_count"] += 1
        for digest in (before_hash, after_hash):
            if digest not in edge["evidence_screenshot_hashes"]:
                edge["evidence_screenshot_hashes"].append(digest)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"version": 1, "edges": self.edges}, indent=2) + "\n",
            encoding="utf-8",
        )
        return edge


class SessionJournal:
    """Write machine-readable JSON and a concise human-readable journal."""

    def __init__(
        self,
        directory: Path,
        *,
        goal: str,
        client_version: str,
        server: str,
        session_id: str | None = None,
    ) -> None:
        self.directory = directory
        self.session_id = (
            session_id
            or _utc_now().replace(":", "").replace("+00", "Z")
            + "-"
            + uuid.uuid4().hex[:8]
        )
        self.goal = goal
        self.client_version = client_version
        self.server = server
        self.started_at = _utc_now()
        self.states: list[dict[str, Any]] = []
        self.actions: list[dict[str, Any]] = []
        self.observations: list[str] = []
        self.stop_reason: str | None = None
        self._write()

    @property
    def json_path(self) -> Path:
        return self.directory / f"{self.session_id}.json"

    @property
    def markdown_path(self) -> Path:
        return self.directory / f"{self.session_id}.md"

    def record_state(self, state: ScreenState, *, phase: str) -> None:
        self.states.append(
            {"phase": phase, "state": state.to_dict(), "detected_at": _utc_now()}
        )
        self._write()

    def record_action(
        self,
        action: SafeAction,
        *,
        status: str,
        before: ScreenState,
        after: ScreenState | None = None,
        error: str | None = None,
    ) -> None:
        self.actions.append(
            {
                "action": action.to_dict(),
                "status": status,
                "before_screenshot_hash": before.screenshot_hash,
                "after_screenshot_hash": after.screenshot_hash if after else None,
                "expected_transition": action.expected_next_state,
                "actual_transition": after.state_id if after else None,
                "ocr_anchors_used": list(before.ocr_anchors),
                "error": error,
                "recorded_at": _utc_now(),
            }
        )
        self._write()

    def finish(self, stop_reason: str, observations: Sequence[str] = ()) -> None:
        self.stop_reason = stop_reason
        self.observations.extend(observations)
        self._write()

    def _payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "started_at": self.started_at,
            "finished_at": _utc_now() if self.stop_reason else None,
            "client_version": self.client_version,
            "server": self.server,
            "states": self.states,
            "actions": self.actions,
            "stop_reason": self.stop_reason,
            "observations": self.observations,
        }

    def _write(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.json_path.write_text(
            json.dumps(self._payload(), indent=2) + "\n", encoding="utf-8"
        )
        lines = [
            f"# PROBE session {self.session_id}",
            "",
            f"- Goal: `{self.goal}`",
            f"- Client: `{self.client_version}`",
            f"- Server: `{self.server}`",
            f"- Stop reason: `{self.stop_reason or 'in progress'}`",
            "",
            "## States",
        ]
        for event in self.states:
            state = event["state"]
            lines.append(
                f"- {event['phase']}: `{state['state_id']}` ({state['confidence']:.2f})"
            )
        lines.append("\n## Actions")
        for event in self.actions:
            action = event["action"]
            lines.append(
                f"- `{action['action_type']} {action['semantic_target']}`: "
                f"{event['status']}"
            )
        if self.observations:
            lines.append("\n## Observations")
            lines.extend(f"- {observation}" for observation in self.observations)
        self.markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class NavigationAgent:
    """Run at most one verified safe transition at a time."""

    def __init__(
        self,
        frame_source: FrameSource,
        input_driver: InputDriver,
        *,
        recognizer: StateRecognizer | None = None,
        graph: NavigationGraph,
        journal: SessionJournal,
        dry_run: bool = True,
        max_steps: int = 1,
        transition_wait: float = 0.5,
        policy: NavigationPolicy | None = None,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self.frame_source = frame_source
        self.input_driver = input_driver
        self.recognizer = recognizer or StateRecognizer()
        self.graph = graph
        self.journal = journal
        self.dry_run = dry_run
        self.max_steps = max_steps
        self.transition_wait = transition_wait
        self.policy = policy or NavigationPolicy()

    def run(self, goal: str) -> dict[str, Any]:
        frame = self.frame_source.capture("before-step-0")
        state = self.recognizer.recognize(frame)
        self.journal.record_state(state, phase="before")
        seen = {state.perceptual_fingerprint}
        if goal == "inspect-current-screen":
            self.journal.finish("goal_inspected")
            return self._result("goal_inspected", state)
        if goal != "navigate-to-research-lab":
            self.journal.finish("unsupported_goal")
            return self._result("unsupported_goal", state)
        for step in range(self.max_steps):
            action = self.propose_action(goal, frame, state)
            if action is None:
                reason = (
                    "already_at_goal"
                    if state.state_id == "research_lab"
                    else "uncertain_no_safe_action"
                )
                self.journal.finish(reason)
                return self._result(reason, state)
            try:
                self.policy.validate(action)
            except SafeNavigationError as error:
                self.journal.record_action(
                    action, status="rejected", before=state, error=str(error)
                )
                self.journal.finish("unsafe_action_rejected")
                return self._result("unsafe_action_rejected", state, action)
            if self.dry_run:
                self.journal.record_action(action, status="proposed", before=state)
                self.journal.finish("dry_run")
                return self._result("dry_run", state, action)
            self.input_driver.perform(action, frame)
            if self.transition_wait:
                time.sleep(self.transition_wait)
            after_frame = self.frame_source.capture(f"after-step-{step}")
            after = self.recognizer.recognize(after_frame)
            self.journal.record_state(after, phase="after")
            success = after.state_id == action.expected_next_state
            self.graph.record_transition(
                action,
                after.state_id,
                success=success,
                before_hash=frame.screenshot_hash,
                after_hash=after_frame.screenshot_hash,
                client_version=after.client_version,
            )
            self.journal.record_action(
                action,
                status="success" if success else "failure",
                before=state,
                after=after,
                error=None if success else "expected state was not observed",
            )
            if after.perceptual_fingerprint in seen:
                self.journal.finish("loop_detected")
                return self._result("loop_detected", after, action)
            if not success:
                self.journal.finish("transition_failed")
                return self._result("transition_failed", after, action)
            if after.state_id == "research_lab":
                self.journal.finish("goal_reached")
                return self._result("goal_reached", after, action)
            seen.add(after.perceptual_fingerprint)
            frame, state = after_frame, after
        self.journal.finish("step_limit_reached")
        return self._result(
            "step_limit_reached", state, action if "action" in locals() else None
        )

    def propose_action(
        self, goal: str, frame: Frame, state: ScreenState
    ) -> SafeAction | None:
        if (
            goal != "navigate-to-research-lab"
            or state.state_id == "research_lab"
            or state.state_id != "sanctuary_main"
        ):
            return None
        anchor = _find_anchor(frame.ocr_anchors, "research lab")
        if (
            anchor is None
            or not anchor.bbox_pixels
            or frame.width <= 0
            or frame.height <= 0
        ):
            return None
        point = _bbox_center_normalized(anchor.bbox_pixels, frame.width, frame.height)
        return SafeAction(
            action_type="tap",
            semantic_target="research_lab",
            source_state=state.state_id,
            expected_next_state="research_lab",
            normalized_point=point,
            confidence=min(state.confidence, anchor.confidence),
        )

    def _result(
        self, stop_reason: str, state: ScreenState, action: SafeAction | None = None
    ) -> dict[str, Any]:
        return {
            "session_id": self.journal.session_id,
            "goal": self.journal.goal,
            "stop_reason": stop_reason,
            "state": state.to_dict(),
            "proposed_action": action.to_dict() if action else None,
            "dry_run": self.dry_run,
            "journal_json": str(self.journal.json_path),
            "journal_markdown": str(self.journal.markdown_path),
            "graph": str(self.graph.path),
        }


class AdbFrameSource:
    """Capture frames through the existing BlueStacks ADB bridge."""

    def __init__(
        self,
        adb: Path = DEFAULT_ADB,
        serial: str | None = None,
        server: str = DEFAULT_SERVER,
        output_dir: Path = Path("data/raw/probe/screenshots"),
        perceiver: Any | None = None,
    ) -> None:
        self.adb = adb
        self.serial = serial
        self.server = server
        self.output_dir = output_dir
        self.perceiver = perceiver or RapidOcrPerceiver()
        self._resolved_serial: str | None = None

    def capture(self, label: str | None = None) -> Frame:
        serial = self._device()
        version = package_version(self.adb, serial)
        png = run_adb(self.adb, "exec-out", "screencap", "-p", serial=serial)
        width, height = _png_size(png)
        digest = hashlib.sha256(png).hexdigest()
        timestamp = datetime.now(timezone.utc)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        prefix = f"{_safe_label(label)}_" if label else ""
        image_path = (
            self.output_dir
            / f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}_{prefix}{digest[:12]}.png"
        )
        image_path.write_bytes(png)
        metadata = {
            "captured_at_utc": timestamp.isoformat(),
            "device_serial": serial,
            "package": PACKAGE,
            "client_version_name": version["version_name"],
            "client_version_code": int(version["version_code"]),
            "server": self.server,
            "sha256": digest,
            "screenshot_path": str(image_path),
            "adb_operation": "exec-out screencap -p",
        }
        if label:
            metadata["label"] = label
        anchors = tuple(self.perceiver.detect(png))
        metadata["ocr_anchor_count"] = len(anchors)
        return Frame(png, digest, width, height, anchors, metadata)

    def _device(self) -> str:
        if self._resolved_serial is None:
            self._resolved_serial = detect_device(self.adb, self.serial)
        return self._resolved_serial


class AdbInputDriver:
    """Experimental adapter for explicitly enabled allowlisted input."""

    def __init__(self, adb: Path = DEFAULT_ADB, serial: str | None = None) -> None:
        self.adb = adb
        self.serial = serial

    def perform(self, action: SafeAction, frame: Frame) -> None:
        NavigationPolicy().validate(action)
        if action.action_type == "back":
            run_adb(self.adb, "shell", "input", "keyevent", "4", serial=self.serial)
            return
        if action.action_type == "tap":
            point = action.normalized_point or _bbox_center(action.target_bbox)
            x, y = _pixel_point(point, frame.width, frame.height)
            run_adb(
                self.adb, "shell", "input", "tap", str(x), str(y), serial=self.serial
            )
            return
        if action.action_type == "swipe":
            assert (
                action.normalized_point is not None
                and action.normalized_end is not None
            )
            start = _pixel_point(action.normalized_point, frame.width, frame.height)
            end = _pixel_point(action.normalized_end, frame.width, frame.height)
            run_adb(
                self.adb,
                "shell",
                "input",
                "swipe",
                str(start[0]),
                str(start[1]),
                str(end[0]),
                str(end[1]),
                "300",
                serial=self.serial,
            )


class RapidOcrPerceiver:
    """Optional adapter around the already-supported RapidOCR stack."""

    def __init__(
        self,
        *,
        engine_factory: Callable[[], Any] | None = None,
        image_decoder: Callable[[bytes], Any] | None = None,
    ) -> None:
        self._engine_factory = engine_factory
        self._image_decoder = image_decoder
        self._engine: Any | None = None

    def detect(self, png: bytes) -> list[OCRAnchor]:
        if self._image_decoder is None:
            try:
                import cv2
                import numpy as np
            except ImportError:
                return []
            image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
        else:
            image = self._image_decoder(png)
        if image is None:
            return []
        if self._engine is None:
            if self._engine_factory is not None:
                self._engine = self._engine_factory()
            else:
                try:
                    from rapidocr_onnxruntime import RapidOCR
                except ImportError:
                    return []
                self._engine = RapidOCR()
        result, _ = self._engine(image)
        if result is None:
            return []
        return [
            OCRAnchor(
                text=str(text),
                confidence=float(confidence),
                bbox_pixels=tuple((float(point[0]), float(point[1])) for point in box),
            )
            for box, text, confidence in result
        ]


def run_adb(adb: Path, *args: str, serial: str | None = None) -> bytes:
    command = [str(adb)]
    if serial:
        command += ["-s", serial]
    command += list(args)
    return subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def detect_device(adb: Path, requested_serial: str | None = None) -> str:
    output = run_adb(adb, "devices", "-l").decode("utf-8", errors="replace")
    devices = [
        match.group(1)
        for line in output.splitlines()
        if (match := re.match(r"^(\S+)\s+device\b", line.strip()))
    ]
    if requested_serial:
        if requested_serial not in devices:
            raise RuntimeError(f"requested device is not ready: {requested_serial}")
        return requested_serial
    if len(devices) != 1:
        raise RuntimeError(f"expected exactly one ready device, found: {devices}")
    return devices[0]


def package_version(adb: Path, serial: str) -> dict[str, str]:
    output = run_adb(adb, "shell", "dumpsys", "package", PACKAGE, serial=serial).decode(
        "utf-8", errors="replace"
    )
    version_name = re.search(r"versionName=([^\s]+)", output)
    version_code = re.search(r"versionCode=(\d+)", output)
    if not version_name or not version_code:
        raise RuntimeError("package version metadata was not found")
    return {
        "version_name": version_name.group(1),
        "version_code": version_code.group(1),
    }


def _find_anchor(anchors: Sequence[OCRAnchor], term: str) -> OCRAnchor | None:
    normalized_term = _normalise(term)
    return next(
        (anchor for anchor in anchors if normalized_term in _normalise(anchor.text)),
        None,
    )


def _bbox_center_normalized(
    bbox: Sequence[tuple[float, float]], width: int, height: int
) -> tuple[float, float]:
    xs = [point[0] for point in bbox]
    ys = [point[1] for point in bbox]
    return sum(xs) / len(xs) / width, sum(ys) / len(ys) / height


def _bbox_center(bbox: tuple[float, float, float, float] | None) -> tuple[float, float]:
    if bbox is None:
        raise SafeNavigationError("tap target geometry is missing")
    x, y, width, height = bbox
    return x + width / 2, y + height / 2


def _pixel_point(
    point: tuple[float, float], width: int, height: int
) -> tuple[int, int]:
    return round(point[0] * width), round(point[1] * height)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _has_text(texts: Sequence[str], term: str) -> bool:
    normalized_term = _normalise(term)
    return any(normalized_term in text for text in texts)


def _count_texts(texts: Sequence[str], terms: Sequence[str]) -> int:
    return sum(_has_text(texts, term) for term in terms)


def _safe_label(label: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", label.strip()).strip("-._")
    return cleaned[:80] or "frame"


def _png_size(png: bytes) -> tuple[int, int]:
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("ADB did not return a PNG framebuffer")
    return int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
