"""Passive, bounded BlueStacks observation with no game-control operations."""

from __future__ import annotations

import hashlib
import json
import re
import struct
import subprocess
import time
import uuid
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from .navigation import (
    DEFAULT_ADB,
    DEFAULT_SERVER,
    PACKAGE,
    Frame,
    OCRAnchor,
    StateRecognizer,
    run_adb,
)

DEFAULT_OUTPUT = Path("data/raw/probe/shadow/observations.jsonl")
DEFAULT_EVIDENCE_DIR = Path("data/raw/probe/shadow/screenshots")


class ShadowObserverError(RuntimeError):
    """A recoverable capture failure with a machine-readable reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class OCRPerceiver(Protocol):
    def detect(self, png: bytes) -> list[OCRAnchor]: ...


AdbRunner = Callable[..., bytes]


@dataclass(frozen=True)
class ShadowObserverConfig:
    interval: float = 5.0
    change_threshold: float = 0.08
    max_captures: int = 100
    server: str = DEFAULT_SERVER
    package: str = PACKAGE

    def __post_init__(self) -> None:
        if self.interval <= 0:
            raise ValueError("interval must be greater than zero")
        if not 0.0 <= self.change_threshold <= 1.0:
            raise ValueError("change_threshold must be between 0 and 1")
        if self.max_captures < 1:
            raise ValueError("max_captures must be at least 1")


class AdbShadowFrameSource:
    """Read-only ADB source for one framebuffer and its installed metadata."""

    def __init__(
        self,
        adb: Path = DEFAULT_ADB,
        serial: str | None = None,
        server: str = DEFAULT_SERVER,
        package: str = PACKAGE,
        runner: AdbRunner = run_adb,
    ) -> None:
        self.adb = adb
        self.serial = serial
        self.server = server
        self.package = package
        self.runner = runner
        self._resolved_serial: str | None = None

    def capture(self, label: str | None = None) -> Frame:
        del label
        try:
            serial = self._device()
            version = self._package_version(serial)
            foreground = self._foreground_package(serial)
            png = self._run("exec-out", "screencap", "-p", serial=serial)
        except ShadowObserverError:
            raise
        except FileNotFoundError as error:
            raise ShadowObserverError("adb_unavailable", str(error)) from error
        except (OSError, subprocess.CalledProcessError) as error:
            raise ShadowObserverError("adb_disconnected", str(error)) from error

        width, height = _png_size(png)
        return Frame(
            screenshot=png,
            screenshot_hash=hashlib.sha256(png).hexdigest(),
            width=width,
            height=height,
            metadata={
                "device_serial": serial,
                "package": self.package,
                "client_version_name": version["version_name"],
                "client_version_code": int(version["version_code"]),
                "server": self.server,
                "foreground_package": foreground,
                "adb_operation": "exec-out screencap -p",
            },
        )

    def _run(self, *args: str, serial: str | None = None) -> bytes:
        return self.runner(self.adb, *args, serial=serial)

    def _device(self) -> str:
        if self._resolved_serial is not None:
            return self._resolved_serial
        try:
            output = self._run("devices", "-l").decode("utf-8", errors="replace")
        except FileNotFoundError as error:
            raise ShadowObserverError("adb_unavailable", str(error)) from error
        except (OSError, subprocess.CalledProcessError) as error:
            raise ShadowObserverError("adb_disconnected", str(error)) from error
        devices = [
            match.group(1)
            for line in output.splitlines()
            if (match := re.match(r"^(\S+)\s+device\b", line.strip()))
        ]
        if self.serial:
            if self.serial not in devices:
                raise ShadowObserverError(
                    "adb_disconnected",
                    f"requested device is not ready: {self.serial}",
                )
            self._resolved_serial = self.serial
            return self.serial
        if len(devices) != 1:
            raise ShadowObserverError(
                "adb_disconnected",
                f"expected exactly one ready device, found: {devices}",
            )
        self._resolved_serial = devices[0]
        return devices[0]

    def _package_version(self, serial: str) -> dict[str, str]:
        try:
            output = self._run(
                "shell", "dumpsys", "package", self.package, serial=serial
            ).decode("utf-8", errors="replace")
        except (OSError, subprocess.CalledProcessError) as error:
            raise ShadowObserverError("adb_disconnected", str(error)) from error
        version_name = re.search(r"versionName=([^\s]+)", output)
        version_code = re.search(r"versionCode=(\d+)", output)
        if not version_name or not version_code:
            raise ShadowObserverError(
                "package_metadata_unavailable",
                "package version metadata was not found",
            )
        return {
            "version_name": version_name.group(1),
            "version_code": version_code.group(1),
        }

    def _foreground_package(self, serial: str) -> str | None:
        try:
            output = self._run(
                "shell", "dumpsys", "activity", "activities", serial=serial
            ).decode("utf-8", errors="replace")
        except (OSError, subprocess.CalledProcessError) as error:
            raise ShadowObserverError("adb_disconnected", str(error)) from error
        match = re.search(
            r"(?:mResumedActivity|ResumedActivity):\s+[^\s]+\s+([^/\s]+)/",
            output,
        )
        return match.group(1) if match else None


class ObservationStore:
    """Append observations and retain at most ``max_captures`` PNGs."""

    def __init__(
        self,
        output: Path,
        evidence_dir: Path,
        *,
        max_captures: int,
    ) -> None:
        if max_captures < 1:
            raise ValueError("max_captures must be at least 1")
        self.output = output
        self.evidence_dir = evidence_dir
        self.max_captures = max_captures
        self.capture_count = 0
        self.observation_count = 0

    def append(
        self,
        observation: dict[str, Any],
        screenshot: bytes | None = None,
    ) -> dict[str, Any]:
        if screenshot is not None and self.capture_count < self.max_captures:
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            digest = observation["screenshot_hash"]
            stamp = _timestamp_for_filename(observation["timestamp"])
            path = self.evidence_dir / f"{stamp}_{digest[:12]}.png"
            path.write_bytes(screenshot)
            observation["screenshot_path"] = str(path)
            observation["raw_capture_retained"] = True
            self.capture_count += 1
        elif screenshot is not None:
            observation["raw_capture_retained"] = False
            observation["retention_note"] = "maximum raw captures reached"
        else:
            observation["raw_capture_retained"] = False

        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(observation, ensure_ascii=True) + "\n")
        self.observation_count += 1
        return observation


class ShadowObserver:
    """Poll a frame source and record only novel, locally classified screens."""

    def __init__(
        self,
        source: AdbShadowFrameSource | Any,
        store: ObservationStore,
        *,
        config: ShadowObserverConfig | None = None,
        recognizer: StateRecognizer | None = None,
        ocr_perceiver: OCRPerceiver | None = None,
        session_id: str | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.source = source
        self.store = store
        self.config = config or ShadowObserverConfig()
        self.recognizer = recognizer or StateRecognizer()
        self.ocr_perceiver = ocr_perceiver
        self.session_id = session_id or uuid.uuid4().hex
        self.clock = clock
        self.sleeper = sleeper
        self._previous_sample: tuple[str, str] | None = None
        self._previous_observation_id: str | None = None
        self._previous_state: str | None = None
        self._sequence = 0
        self.suppressed_count = 0

    def run_once(self) -> dict[str, Any] | None:
        try:
            frame = self.source.capture("shadow-poll")
        except Exception as error:
            return self._record_capture_failure(error)

        screenshot_hash = hashlib.sha256(frame.screenshot).hexdigest()
        fingerprint = perceptual_fingerprint(frame.screenshot)
        if self._previous_sample is not None:
            previous_hash, previous_fingerprint = self._previous_sample
            score = change_score(
                previous_hash,
                screenshot_hash,
                previous_fingerprint,
                fingerprint,
            )
            if score < self.config.change_threshold:
                self.suppressed_count += 1
                self._previous_sample = (screenshot_hash, fingerprint)
                return None
        else:
            score = 1.0
        self._previous_sample = (screenshot_hash, fingerprint)

        package = str(frame.metadata.get("package", self.config.package))
        foreground = frame.metadata.get("foreground_package")
        game_is_foreground = foreground is None or foreground == package
        anchors = tuple(frame.ocr_anchors)
        if game_is_foreground and not anchors and self.ocr_perceiver is not None:
            anchors = tuple(self.ocr_perceiver.detect(frame.screenshot))
        frame = Frame(
            screenshot=frame.screenshot,
            screenshot_hash=screenshot_hash,
            width=frame.width,
            height=frame.height,
            ocr_anchors=anchors,
            metadata=frame.metadata,
        )
        observation = self._build_observation(frame, fingerprint, score)
        evidence = (
            None
            if observation["current_screen_state"] == "not_game_foreground"
            else frame.screenshot
        )
        return self.store.append(observation, evidence)

    def run(self, duration: float | None = None) -> dict[str, Any]:
        if duration is not None and duration < 0:
            raise ValueError("duration must be zero or greater")
        started = self.clock()
        stop_reason = "duration_reached"
        while True:
            observation = self.run_once()
            if observation and observation.get("validation_status") == "FAIL":
                stop_reason = observation.get("error_reason", "capture_failed")
                break
            if duration is not None and self.clock() - started >= duration:
                break
            self.sleeper(self.config.interval)
        return {
            "session_id": self.session_id,
            "observations_recorded": self.store.observation_count,
            "captures_retained": self.store.capture_count,
            "duplicates_suppressed": self.suppressed_count,
            "stop_reason": stop_reason,
            "output": str(self.store.output),
        }

    def _build_observation(
        self, frame: Frame, fingerprint: str, score: float
    ) -> dict[str, Any]:
        metadata = frame.metadata
        package = str(metadata.get("package", self.config.package))
        foreground = metadata.get("foreground_package")
        if foreground is not None and foreground != package:
            current_state = "not_game_foreground"
            validation = "REVIEW"
            anchors: list[dict[str, Any]] = []
            candidates: list[dict[str, str]] = []
        else:
            state = self.recognizer.recognize(frame)
            current_state = state.state_id
            validation = "PASS" if current_state != "unknown" else "REVIEW"
            anchors = [_anchor_dict(anchor) for anchor in frame.ocr_anchors]
            candidates = extract_candidate_values(frame.ocr_anchors)

        self._sequence += 1
        observation_id = f"{self.session_id}-{self._sequence:06d}"
        timestamp = _utc_now()
        observation = {
            "observation_id": observation_id,
            "timestamp": timestamp,
            "session_id": self.session_id,
            "package": package,
            "client_version_name": metadata.get("client_version_name"),
            "client_version_code": metadata.get("client_version_code"),
            "server": metadata.get("server", self.config.server),
            "screenshot_hash": frame.screenshot_hash,
            "screenshot_path": None,
            "previous_screen_state": self._previous_state,
            "current_screen_state": current_state,
            "ocr_anchors": anchors,
            "ocr_raw_output": [_anchor_dict(anchor) for anchor in frame.ocr_anchors],
            "extracted_candidate_values": candidates,
            "validation_status": validation,
            "transition_provenance": {
                "kind": "passive_local_observation",
                "method": "sha256+perceptual_hash+state_recognizer",
                "previous_observation_id": self._previous_observation_id,
            },
            "change_score": round(score, 6),
            "perceptual_fingerprint": fingerprint,
            "raw_capture_retained": False,
        }
        self._previous_observation_id = observation_id
        self._previous_state = current_state
        return observation

    def _record_capture_failure(self, error: Exception) -> dict[str, Any]:
        self._sequence += 1
        reason = getattr(error, "reason", _failure_reason(error))
        timestamp = _utc_now()
        observation = {
            "observation_id": f"{self.session_id}-{self._sequence:06d}",
            "timestamp": timestamp,
            "session_id": self.session_id,
            "package": self.config.package,
            "client_version_name": None,
            "client_version_code": None,
            "server": self.config.server,
            "screenshot_hash": None,
            "screenshot_path": None,
            "previous_screen_state": self._previous_state,
            "current_screen_state": "unavailable",
            "ocr_anchors": [],
            "ocr_raw_output": [],
            "extracted_candidate_values": [],
            "validation_status": "FAIL",
            "transition_provenance": {
                "kind": "passive_local_observation",
                "method": "adb_read_failure",
                "previous_observation_id": self._previous_observation_id,
            },
            "change_score": None,
            "perceptual_fingerprint": None,
            "raw_capture_retained": False,
            "error_reason": reason,
            "error": str(error),
        }
        self._previous_observation_id = observation["observation_id"]
        self._previous_state = "unavailable"
        return self.store.append(observation)


def perceptual_fingerprint(png: bytes) -> str:
    """Return a deterministic 64-bit average hash, with a byte fallback."""

    try:
        pixels = _png_grayscale_pixels(png)
    except (ValueError, struct.error, zlib.error):
        return hashlib.sha256(png).hexdigest()[:16]
    samples = [
        pixels[(row * len(pixels)) // 8][(column * len(pixels[0])) // 8]
        for row in range(8)
        for column in range(8)
    ]
    average = sum(samples) / len(samples)
    bits = sum(1 << index for index, value in enumerate(samples) if value >= average)
    return f"{bits:016x}"


def change_score(
    previous_hash: str,
    current_hash: str,
    previous_fingerprint: str,
    current_fingerprint: str,
) -> float:
    if previous_hash == current_hash:
        return 0.0
    try:
        distance = sum(
            left != right
            for left, right in zip(
                f"{int(previous_fingerprint, 16):064b}",
                f"{int(current_fingerprint, 16):064b}",
            )
        )
        return distance / 64
    except ValueError:
        return 1.0


def extract_candidate_values(anchors: tuple[OCRAnchor, ...]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    patterns = (
        ("level", r"\blevel\s*[:#]?\s*(\d+)"),
        ("effect", r"\beffect\s*[:#]?\s*([+-]?\d+(?:[.,]\d+)?%?)"),
        ("power", r"\bpower\s*[:#]?\s*([+-]?\d+(?:[.,]\d+)?%?)"),
        ("cost", r"\bcost\s*[:#]?\s*([+-]?\d+(?:[.,]\d+)?%?)"),
        ("time", r"\btime\s*[:#]?\s*([0-9]+(?::[0-9]{2})*)"),
    )
    for anchor in anchors:
        normalized = re.sub(r"\s+", " ", anchor.text.casefold()).strip()
        for key, pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                candidates.append(
                    {"key": key, "value": match.group(1), "source_text": anchor.text}
                )
    return candidates


def _anchor_dict(anchor: OCRAnchor) -> dict[str, Any]:
    return {
        "text": anchor.text,
        "confidence": anchor.confidence,
        "bbox_pixels": [list(point) for point in anchor.bbox_pixels],
    }


def _png_grayscale_pixels(png: bytes) -> list[list[int]]:
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    offset = 8
    width = height = bit_depth = color_type = None
    compressed = bytearray()
    while offset < len(png):
        length = struct.unpack(">I", png[offset : offset + 4])[0]
        chunk_type = png[offset + 4 : offset + 8]
        chunk = png[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", chunk)
            )
            if bit_depth != 8 or compression != 0 or filtering != 0 or interlace != 0:
                raise ValueError("unsupported PNG format")
        elif chunk_type == b"IDAT":
            compressed.extend(chunk)
        elif chunk_type == b"IEND":
            break
    if width is None or height is None or color_type not in (0, 2, 4, 6):
        raise ValueError("incomplete PNG")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    row_size = width * channels
    raw = zlib.decompress(bytes(compressed))
    if len(raw) < height * (row_size + 1):
        raise ValueError("truncated PNG pixels")
    rows: list[list[int]] = []
    previous = bytearray(row_size)
    for row_index in range(height):
        start = row_index * (row_size + 1)
        filter_type = raw[start]
        encoded = raw[start + 1 : start + 1 + row_size]
        row = bytearray(row_size)
        for index, value in enumerate(encoded):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            up_left = previous[index - channels] if index >= channels else 0
            if filter_type == 0:
                row[index] = value
            elif filter_type == 1:
                row[index] = (value + left) & 255
            elif filter_type == 2:
                row[index] = (value + up) & 255
            elif filter_type == 3:
                row[index] = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                predictor = left + up - up_left
                distance_left = abs(predictor - left)
                distance_up = abs(predictor - up)
                distance_up_left = abs(predictor - up_left)
                nearest = (
                    left
                    if distance_left <= distance_up
                    and distance_left <= distance_up_left
                    else up
                    if distance_up <= distance_up_left
                    else up_left
                )
                row[index] = (value + nearest) & 255
            else:
                raise ValueError("unsupported PNG filter")
        rows.append(_row_grayscale(row, channels, color_type))
        previous = row
    return rows


def _row_grayscale(row: bytearray, channels: int, color_type: int) -> list[int]:
    if color_type in (0, 4):
        return [row[index] for index in range(0, len(row), channels)]
    return [
        (row[index] * 299 + row[index + 1] * 587 + row[index + 2] * 114) // 1000
        for index in range(0, len(row), channels)
    ]


def _png_size(png: bytes) -> tuple[int, int]:
    if png[:8] != b"\x89PNG\r\n\x1a\n" or png[12:16] != b"IHDR":
        raise ShadowObserverError(
            "invalid_frame", "ADB did not return a PNG framebuffer"
        )
    return struct.unpack(">II", png[16:24])


def _timestamp_for_filename(timestamp: str) -> str:
    return re.sub(r"[^0-9TZ]", "", timestamp)[:20]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _failure_reason(error: Exception) -> str:
    if isinstance(error, FileNotFoundError):
        return "adb_unavailable"
    if isinstance(error, (OSError, subprocess.CalledProcessError)):
        return "adb_disconnected"
    return "capture_failed"
