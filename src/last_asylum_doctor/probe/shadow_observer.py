"""Passive, bounded BlueStacks observation with no game-control operations."""

from __future__ import annotations

import hashlib
import json
import os
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

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows uses msvcrt below.
    fcntl = None

if fcntl is None:  # pragma: no cover - exercised on Windows.
    import msvcrt

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
DEFAULT_SPOOL_ROOT = Path("data/raw/probe/shadow/spool")
SPOOL_SCHEMA_VERSION = "0.3"


class ShadowObserverError(RuntimeError):
    """A recoverable capture failure with a machine-readable reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class ShadowSpoolError(RuntimeError):
    """A filesystem spool lifecycle or ownership failure."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class ObservationStoreCorruptionError(RuntimeError):
    """Canonical JSONL contains malformed data before its final tail."""


_TIMING_KEYS = (
    "capture_duration_ms",
    "ocr_duration_ms",
    "recognition_extraction_duration_ms",
    "persistence_duration_ms",
    "total_duration_ms",
)


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


class ShadowSpool:
    """Filesystem spool whose inbox commit unit is one capture directory."""

    _DIRECTORIES = ("tmp", "inbox", "processing", "processed", "failed")

    def __init__(self, root: Path = DEFAULT_SPOOL_ROOT) -> None:
        self.root = root
        self.paths = {name: root / name for name in self._DIRECTORIES}

    def prepare(self) -> None:
        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)

    def enqueue(
        self,
        capture_id: str,
        screenshot: bytes,
        metadata: dict[str, Any],
        *,
        capture_duration_ms: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", capture_id):
            raise ValueError("capture_id contains unsafe path characters")
        self.prepare()
        temporary = self.paths["tmp"] / f".{capture_id}.{uuid.uuid4().hex}"
        destination = self.paths["inbox"] / capture_id
        if destination.exists():
            raise ShadowSpoolError(
                "capture_id_collision",
                f"inbox capture already exists: {capture_id}",
            )
        temporary.mkdir()
        try:
            spool_started = clock()
            _write_durable_bytes(temporary / "frame.png", screenshot)
            metadata["capture_staging_duration_ms"] = _elapsed_ms(
                spool_started, clock()
            )
            metadata["spool_write_duration_ms"] = _elapsed_ms(
                spool_started, clock()
            )
            if capture_duration_ms is not None:
                metadata["capture_duration_ms"] = capture_duration_ms
            _write_durable_json(temporary / "capture.json", metadata)
            os.replace(temporary, destination)
        except Exception:
            if temporary.exists():
                _write_failure_marker(temporary, capture_id)
            raise
        return destination

    def inbox_items(self) -> list[Path]:
        self.prepare()
        return sorted(path for path in self.paths["inbox"].iterdir() if path.is_dir())

    def claim(self, capture_id: str) -> Path:
        self.prepare()
        source = self.paths["inbox"] / capture_id
        destination = self.paths["processing"] / capture_id
        if destination.exists():
            raise ShadowSpoolError(
                "capture_already_processing",
                f"capture is already processing: {capture_id}",
            )
        source.replace(destination)
        return destination

    def move(self, capture_id: str, state: str) -> Path:
        if state not in {"processed", "failed"}:
            raise ValueError(f"unsupported spool terminal state: {state}")
        source = self.paths["processing"] / capture_id
        destination = self.paths[state] / capture_id
        self.prepare()
        if destination.exists():
            raise ShadowSpoolError(
                "capture_terminal_collision",
                f"terminal capture already exists: {destination}",
            )
        source.replace(destination)
        return destination

    def discard_processing(self, capture_id: str) -> None:
        processing = self.paths["processing"] / capture_id
        _remove_directory(processing)

    def recover_processing(self) -> list[str]:
        self.prepare()
        recovered: list[str] = []
        for path in sorted(self.paths["processing"].iterdir()):
            if not path.is_dir():
                continue
            destination = self.paths["inbox"] / path.name
            if destination.exists():
                continue
            path.replace(destination)
            recovered.append(path.name)
        return recovered


class _SingleWorkerLock:
    def __init__(self, root: Path) -> None:
        self.path = root / ".worker.lock"
        self._stream: Any | None = None

    def __enter__(self) -> _SingleWorkerLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = self.path.open("a+b")
        if self.path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if fcntl is not None:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except (OSError, PermissionError) as error:
            stream.close()
            raise ShadowSpoolError(
                "worker_already_running",
                f"another Shadow Spool worker owns {self.path}",
            ) from error
        self._stream = stream
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        del exc_type, exc_value, traceback
        if self._stream is None:
            return
        try:
            if fcntl is not None:
                fcntl.flock(self._stream.fileno(), fcntl.LOCK_UN)
            else:
                self._stream.seek(0)
                msvcrt.locking(self._stream.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self._stream.close()
            self._stream = None


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
                "foreground_package": foreground["package"],
                "foreground_status": _foreground_status(
                    foreground["package"], self.package
                ),
                "foreground_parser": foreground["parser"],
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

    def _foreground_package(self, serial: str) -> dict[str, Any]:
        try:
            output = self._run(
                "shell", "dumpsys", "activity", "activities", serial=serial
            ).decode("utf-8", errors="replace")
        except (OSError, subprocess.CalledProcessError) as error:
            raise ShadowObserverError("adb_disconnected", str(error)) from error
        match = re.search(
            r"(?:mResumedActivity|ResumedActivity|mCurrentFocus|mFocusedApp)"
            r"[^\r\n]*?\b([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)/[^\s}]+",
            output,
        )
        return {
            "package": match.group(1) if match else None,
            "parser": {
                "source": "dumpsys activity activities",
                "matched": match is not None,
                "raw_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "raw_output_length": len(output),
            },
        }


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
        self._persisted_by_capture_id: dict[str, dict[str, Any]] = {}
        if output.exists():
            self._load_existing()

    def contains_capture_id(self, capture_id: str) -> bool:
        return capture_id in self._persisted_by_capture_id

    def get_capture(self, capture_id: str) -> dict[str, Any] | None:
        saved = self._persisted_by_capture_id.get(capture_id)
        return dict(saved) if saved is not None else None

    def append(
        self,
        observation: dict[str, Any],
        screenshot: bytes | None = None,
        *,
        timing_started: float | None = None,
        processing_started: float | None = None,
        processing_timing: dict[str, Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> dict[str, Any]:
        capture_id = observation.get("capture_id")
        if isinstance(capture_id, str) and capture_id in self._persisted_by_capture_id:
            return dict(self._persisted_by_capture_id[capture_id])
        persistence_started = clock()
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

        timing = observation.get("timing_ms")
        if isinstance(timing, dict):
            timing["persistence_duration_ms"] = _elapsed_ms(
                persistence_started, clock()
            )
            if timing_started is not None:
                timing["total_duration_ms"] = _elapsed_ms(timing_started, clock())
        if processing_timing is not None and processing_started is not None:
            processing_timing["persistence_duration_ms"] = _elapsed_ms(
                persistence_started, clock()
            )
            processing_timing["processing_total_duration_ms"] = _elapsed_ms(
                processing_started, clock()
            )
            observation["processing_timing_ms"] = dict(processing_timing)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("a", encoding="utf-8", newline="\n") as stream:
            if self.output.stat().st_size and not self.output.read_bytes().endswith(
                b"\n"
            ):
                stream.write("\n")
            stream.write(json.dumps(observation, ensure_ascii=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.observation_count += 1
        if isinstance(capture_id, str):
            self._persisted_by_capture_id[capture_id] = dict(observation)
        return observation

    def _load_existing(self) -> None:
        content = self.output.read_bytes()
        offset = 0
        for line in content.splitlines(keepends=True):
            line_end = offset + len(line)
            payload = line.rstrip(b"\r\n")
            if not payload:
                offset = line_end
                continue
            try:
                saved = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                if line_end == len(content):
                    self._recover_tail(content[offset:], offset)
                    return
                raise ObservationStoreCorruptionError(
                    f"malformed JSONL record before final tail at byte {offset}"
                ) from error
            if not isinstance(saved, dict):
                if line_end == len(content):
                    self._recover_tail(content[offset:], offset)
                    return
                raise ObservationStoreCorruptionError(
                    f"non-object JSONL record before final tail at byte {offset}"
                )
            self.observation_count += 1
            capture_id = saved.get("capture_id")
            if isinstance(capture_id, str):
                self._persisted_by_capture_id[capture_id] = saved
            offset = line_end

    def _recover_tail(self, damaged: bytes, offset: int) -> None:
        artifact = self.output.with_name(
            f"{self.output.name}.corrupt-tail.{uuid.uuid4().hex}.bin"
        )
        _write_durable_bytes(artifact, damaged)
        with self.output.open("r+b") as stream:
            stream.truncate(offset)
            stream.flush()
            os.fsync(stream.fileno())


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
        self._previous_observation_sample: tuple[str, str] | None = None
        self._previous_observation_id: str | None = None
        self._previous_state: str | None = None
        self._sequence = 0
        self._spool_sequence = 0
        self.suppressed_count = 0
        self._timing_samples = 0
        self._timing_totals = {key: 0.0 for key in _TIMING_KEYS}

    def spool_once(self, spool: ShadowSpool) -> dict[str, Any]:
        """Capture one novel frame into the durable spool without OCR."""

        total_started = self.clock()
        capture_started = self.clock()
        try:
            frame = self.source.capture("shadow-spool")
        except Exception as error:
            return {
                "status": "FAIL",
                "error_reason": _failure_reason(error),
                "error": str(error),
                "error_diagnostic": {
                    "stage": "capture",
                    "exception_type": type(error).__name__,
                    "message": str(error),
                },
                "capture_duration_ms": _elapsed_ms(capture_started, self.clock()),
                "capture_total_duration_ms": _elapsed_ms(
                    total_started, self.clock()
                ),
            }

        capture_duration = _elapsed_ms(capture_started, self.clock())
        screenshot_hash = hashlib.sha256(frame.screenshot).hexdigest()
        fingerprint = perceptual_fingerprint(frame.screenshot)
        if self._previous_observation_sample is not None:
            previous_hash, previous_fingerprint = self._previous_observation_sample
            score = change_score(
                previous_hash,
                screenshot_hash,
                previous_fingerprint,
                fingerprint,
            )
            if score < self.config.change_threshold:
                self.suppressed_count += 1
                return {
                    "status": "SUPPRESSED",
                    "screenshot_hash": screenshot_hash,
                    "perceptual_fingerprint": fingerprint,
                    "change_score": round(score, 6),
                }
        else:
            score = 1.0

        self._spool_sequence += 1
        metadata = frame.metadata
        package = str(metadata.get("package", self.config.package))
        foreground, foreground_package, foreground_parser = _foreground_context(
            metadata, package
        )
        capture_id = (
            f"{_safe_capture_id(self.session_id)}-"
            f"{self._spool_sequence:06d}-{screenshot_hash[:12]}"
        )
        captured_at = str(metadata.get("captured_at_utc", _utc_now()))
        capture_metadata = {
            "spool_schema_version": SPOOL_SCHEMA_VERSION,
            "capture_id": capture_id,
            "session_id": self.session_id,
            "poll_sequence": self._spool_sequence,
            "captured_at_utc": captured_at,
            "capture_duration_ms": capture_duration,
            "device_serial": metadata.get("device_serial"),
            "package": package,
            "foreground_package": foreground_package,
            "foreground_status": foreground,
            "foreground_parser": foreground_parser,
            "client_version_name": metadata.get("client_version_name"),
            "client_version_code": metadata.get("client_version_code"),
            "server": metadata.get("server", self.config.server),
            "screenshot_hash": screenshot_hash,
            "perceptual_fingerprint": fingerprint,
            "change_score": round(score, 6),
            "framebuffer_width": frame.width,
            "framebuffer_height": frame.height,
            "png_byte_length": len(frame.screenshot),
            "spool_enqueued_at_utc": _utc_now(),
        }
        try:
            path = spool.enqueue(
                capture_id,
                frame.screenshot,
                capture_metadata,
                capture_duration_ms=capture_duration,
                clock=self.clock,
            )
            capture_total_duration = _elapsed_ms(total_started, self.clock())
        except Exception as error:
            return {
                "status": "FAIL",
                "capture_id": capture_id,
                "error_reason": "spool_write_failed",
                "error": str(error),
                "error_diagnostic": {
                    "stage": "spool_write",
                    "exception_type": type(error).__name__,
                    "message": str(error),
                },
            }
        self._previous_observation_sample = (screenshot_hash, fingerprint)
        return {
            "status": "SPOOLED",
            "capture_id": capture_id,
            "spool_path": str(path),
            "capture_total_duration_ms": capture_total_duration,
            **capture_metadata,
        }

    def process_spooled_frame(
        self,
        frame: Frame,
        *,
        capture_id: str,
        captured_at_utc: str,
        capture_timing_ms: dict[str, Any],
        queue_latency_ms: float,
    ) -> dict[str, Any]:
        """Process immutable spool evidence without invoking the capture source."""

        processing_started = self.clock()
        processing_timing = {
            "queue_latency_ms": round(queue_latency_ms, 3),
            "ocr_duration_ms": 0.0,
            "recognition_extraction_duration_ms": 0.0,
            "persistence_duration_ms": 0.0,
            "processing_total_duration_ms": 0.0,
        }
        package = str(frame.metadata.get("package", self.config.package))
        foreground, _, _ = _foreground_context(frame.metadata, package)
        anchors = tuple(frame.ocr_anchors)
        if (
            foreground == "confirmed_game"
            and not anchors
            and self.ocr_perceiver is not None
        ):
            ocr_started = self.clock()
            anchors = tuple(self.ocr_perceiver.detect(frame.screenshot))
            processing_timing["ocr_duration_ms"] = _elapsed_ms(
                ocr_started, self.clock()
            )
        frame = Frame(
            screenshot=frame.screenshot,
            screenshot_hash=frame.screenshot_hash,
            width=frame.width,
            height=frame.height,
            ocr_anchors=anchors,
            metadata=frame.metadata,
        )
        recognition_started = self.clock()
        fingerprint = str(
            frame.metadata.get("perceptual_fingerprint")
            or perceptual_fingerprint(frame.screenshot)
        )
        observation = self._build_observation(
            frame,
            fingerprint,
            float(frame.metadata.get("change_score", 1.0)),
            timing=None,
            capture_id=capture_id,
            captured_at_utc=captured_at_utc,
            capture_timing_ms=capture_timing_ms,
            processing_timing_ms=processing_timing,
        )
        processing_timing["recognition_extraction_duration_ms"] = _elapsed_ms(
            recognition_started, self.clock()
        )
        processing_timing["processing_total_duration_ms"] = _elapsed_ms(
            processing_started, self.clock()
        )
        observation["processing_timing_ms"] = dict(processing_timing)
        evidence = (
            frame.screenshot
            if observation["foreground_status"] == "confirmed_game"
            else None
        )
        result = self.store.append(
            observation,
            evidence,
            processing_started=processing_started,
            processing_timing=processing_timing,
            clock=self.clock,
        )
        return result

    def run_once(self) -> dict[str, Any] | None:
        total_started = self.clock()
        timing = _new_timing()
        capture_started = self.clock()
        try:
            frame = self.source.capture("shadow-poll")
        except Exception as error:
            timing["capture_duration_ms"] = _elapsed_ms(capture_started, self.clock())
            return self._record_capture_failure(error, timing, total_started)
        timing["capture_duration_ms"] = _elapsed_ms(capture_started, self.clock())

        screenshot_hash = hashlib.sha256(frame.screenshot).hexdigest()
        fingerprint = perceptual_fingerprint(frame.screenshot)
        if self._previous_observation_sample is not None:
            previous_hash, previous_fingerprint = self._previous_observation_sample
            score = change_score(
                previous_hash,
                screenshot_hash,
                previous_fingerprint,
                fingerprint,
            )
            if score < self.config.change_threshold:
                self.suppressed_count += 1
                return None
        else:
            score = 1.0

        package = str(frame.metadata.get("package", self.config.package))
        foreground, _, _ = _foreground_context(frame.metadata, package)
        game_is_foreground = foreground == "confirmed_game"
        anchors = tuple(frame.ocr_anchors)
        if game_is_foreground and not anchors and self.ocr_perceiver is not None:
            ocr_started = self.clock()
            try:
                anchors = tuple(self.ocr_perceiver.detect(frame.screenshot))
            except Exception as error:
                timing["ocr_duration_ms"] = _elapsed_ms(ocr_started, self.clock())
                return self._record_pipeline_failure(
                    "ocr", error, frame, timing, total_started, score, fingerprint
                )
            timing["ocr_duration_ms"] = _elapsed_ms(ocr_started, self.clock())
        frame = Frame(
            screenshot=frame.screenshot,
            screenshot_hash=screenshot_hash,
            width=frame.width,
            height=frame.height,
            ocr_anchors=anchors,
            metadata=frame.metadata,
        )
        recognition_started = self.clock()
        try:
            observation = self._build_observation(
                frame, fingerprint, score, timing=timing
            )
        except Exception as error:
            timing["recognition_extraction_duration_ms"] = _elapsed_ms(
                recognition_started, self.clock()
            )
            return self._record_pipeline_failure(
                "recognition", error, frame, timing, total_started, score, fingerprint
            )
        timing["recognition_extraction_duration_ms"] = _elapsed_ms(
            recognition_started, self.clock()
        )
        evidence = (
            None
            if observation["foreground_status"] != "confirmed_game"
            else frame.screenshot
        )
        try:
            result = self.store.append(
                observation,
                evidence,
                timing_started=total_started,
                clock=self.clock,
            )
        except Exception as error:
            return self._record_pipeline_failure(
                "storage", error, frame, timing, total_started, score, fingerprint
            )
        self._previous_observation_sample = (screenshot_hash, fingerprint)
        self._note_timing(result["timing_ms"])
        return result

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
            "timing_samples": self._timing_samples,
            "timing_ms_total": {
                key: round(value, 3) for key, value in self._timing_totals.items()
            },
        }

    def _build_observation(
        self,
        frame: Frame,
        fingerprint: str,
        score: float,
        *,
        timing: dict[str, float] | None,
        capture_id: str | None = None,
        captured_at_utc: str | None = None,
        capture_timing_ms: dict[str, Any] | None = None,
        processing_timing_ms: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = frame.metadata
        package = str(metadata.get("package", self.config.package))
        foreground, foreground_package, foreground_parser = _foreground_context(
            metadata, package
        )
        if foreground == "confirmed_non_game":
            current_state = "not_game_foreground"
            validation = "REVIEW"
            anchors: list[dict[str, Any]] = []
            candidates: list[dict[str, str]] = []
        elif foreground == "unknown":
            current_state = "foreground_unknown"
            validation = "REVIEW"
            anchors = []
            candidates = []
        else:
            state = self.recognizer.recognize(frame)
            current_state = state.state_id
            validation = "PASS" if current_state != "unknown" else "REVIEW"
            anchors = [_anchor_dict(anchor) for anchor in frame.ocr_anchors]
            candidates = extract_candidate_values(frame.ocr_anchors)

        self._sequence += 1
        observation_id = f"{self.session_id}-{self._sequence:06d}"
        timestamp = captured_at_utc or _utc_now()
        observation = {
            "observation_id": observation_id,
            "timestamp": timestamp,
            "session_id": metadata.get("session_id", self.session_id),
            "package": package,
            "client_version_name": metadata.get("client_version_name"),
            "client_version_code": metadata.get("client_version_code"),
            "server": metadata.get("server", self.config.server),
            "foreground_package": foreground_package,
            "foreground_status": foreground,
            "foreground_parser": foreground_parser,
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
        if timing is not None:
            observation["timing_ms"] = dict(timing)
        if capture_id is not None:
            observation.update(
                {
                    "capture_id": capture_id,
                    "captured_at_utc": timestamp,
                    "capture_timing_ms": dict(capture_timing_ms or {}),
                    "processing_timing_ms": dict(processing_timing_ms or {}),
                }
            )
        observation["observation_id"] = (
            capture_id or observation["observation_id"]
        )
        self._previous_observation_id = observation["observation_id"]
        self._previous_state = current_state
        return observation

    def _record_capture_failure(
        self,
        error: Exception,
        timing: dict[str, float],
        total_started: float,
    ) -> dict[str, Any]:
        return self._record_failure(
            _failure_reason(error), error, None, timing, total_started
        )

    def _record_pipeline_failure(
        self,
        stage: str,
        error: Exception,
        frame: Frame,
        timing: dict[str, float],
        total_started: float,
        score: float | None,
        fingerprint: str | None,
    ) -> dict[str, Any]:
        return self._record_failure(
            f"{stage}_failed",
            error,
            frame,
            timing,
            total_started,
            score=score,
            fingerprint=fingerprint,
            stage=stage,
        )

    def _record_failure(
        self,
        reason: str,
        error: Exception,
        frame: Frame | None,
        timing: dict[str, float],
        total_started: float,
        *,
        score: float | None = None,
        fingerprint: str | None = None,
        stage: str = "capture",
    ) -> dict[str, Any]:
        self._sequence += 1
        reason = getattr(error, "reason", reason)
        metadata = frame.metadata if frame is not None else {}
        package = str(metadata.get("package", self.config.package))
        foreground, foreground_package, foreground_parser = _foreground_context(
            metadata, package
        )
        timestamp = _utc_now()
        observation = {
            "observation_id": f"{self.session_id}-{self._sequence:06d}",
            "timestamp": timestamp,
            "session_id": self.session_id,
            "package": package,
            "client_version_name": metadata.get("client_version_name"),
            "client_version_code": metadata.get("client_version_code"),
            "server": metadata.get("server", self.config.server),
            "foreground_package": foreground_package,
            "foreground_status": foreground,
            "foreground_parser": foreground_parser,
            "screenshot_hash": frame.screenshot_hash if frame else None,
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
            "change_score": score,
            "perceptual_fingerprint": fingerprint,
            "raw_capture_retained": False,
            "error_reason": reason,
            "error": str(error),
            "error_diagnostic": {
                "stage": stage,
                "exception_type": type(error).__name__,
                "message": str(error),
            },
            "timing_ms": dict(timing),
        }
        self._previous_observation_id = observation["observation_id"]
        self._previous_state = "unavailable"
        _complete_timing(observation["timing_ms"], total_started, self.clock())
        try:
            result = self.store.append(
                observation,
                timing_started=total_started,
                clock=self.clock,
            )
        except Exception as storage_error:
            storage_observation = self._failure_without_persistence(
                "storage_failed",
                storage_error,
                observation,
                original_error=error,
                original_stage=stage,
            )
            self._note_timing(storage_observation["timing_ms"])
            return storage_observation
        self._note_timing(result["timing_ms"])
        return result

    def _failure_without_persistence(
        self,
        reason: str,
        error: Exception,
        original: dict[str, Any],
        *,
        original_error: Exception,
        original_stage: str,
    ) -> dict[str, Any]:
        self._sequence += 1
        timing = dict(original["timing_ms"])
        observation = {
            **original,
            "observation_id": f"{self.session_id}-{self._sequence:06d}",
            "current_screen_state": "unavailable",
            "validation_status": "FAIL",
            "screenshot_path": None,
            "raw_capture_retained": False,
            "error_reason": reason,
            "error": str(error),
            "error_diagnostic": {
                "stage": "storage",
                "exception_type": type(error).__name__,
                "message": str(error),
                "original_failure": {
                    "stage": original_stage,
                    "exception_type": type(original_error).__name__,
                    "message": str(original_error),
                },
            },
            "timing_ms": timing,
        }
        _complete_timing(timing, None, self.clock())
        self._previous_observation_id = observation["observation_id"]
        self._previous_state = "unavailable"
        return observation

    def _note_timing(self, timing: dict[str, Any]) -> None:
        self._timing_samples += 1
        for key in _TIMING_KEYS:
            value = timing.get(key)
            if isinstance(value, (int, float)):
                self._timing_totals[key] += float(value)


class ShadowSpoolWorker:
    """Process one filesystem spool with one reusable OCR perceiver."""

    _REQUIRED_METADATA = {
        "spool_schema_version",
        "capture_id",
        "session_id",
        "captured_at_utc",
        "package",
        "screenshot_hash",
        "perceptual_fingerprint",
        "change_score",
        "framebuffer_width",
        "framebuffer_height",
        "png_byte_length",
        "capture_staging_duration_ms",
        "spool_enqueued_at_utc",
        "foreground_package",
        "foreground_status",
    }

    def __init__(
        self,
        spool: ShadowSpool,
        store: ObservationStore | None = None,
        *,
        store_factory: Callable[[], ObservationStore] | None = None,
        recognizer: StateRecognizer | None = None,
        ocr_perceiver: OCRPerceiver | None = None,
        config: ShadowObserverConfig | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.spool = spool
        self.store = store
        if store is None and store_factory is None:
            raise ValueError("store or store_factory is required")
        self.store_factory = store_factory
        self.clock = clock
        self.observer: ShadowObserver | None = None
        self._observer_config = config
        self._recognizer = recognizer
        self._ocr_perceiver = ocr_perceiver

    def process_pending(self, limit: int | None = None) -> dict[str, Any]:
        if limit is not None and limit < 1:
            raise ValueError("limit must be at least 1")
        with _SingleWorkerLock(self.spool.root):
            self._ensure_observer()
            recovered = self.spool.recover_processing()
            results: list[dict[str, Any]] = []
            for item in self.spool.inbox_items()[:limit]:
                results.append(self._process_one(item.name))
        return {
            "processed": sum(item["status"] == "PROCESSED" for item in results),
            "already_processed": sum(
                item["status"] == "ALREADY_PROCESSED" for item in results
            ),
            "failed": sum(item["status"] == "FAILED" for item in results),
            "recovered": recovered,
            "results": results,
        }

    def process_one(self, capture_id: str) -> dict[str, Any]:
        with _SingleWorkerLock(self.spool.root):
            self._ensure_observer()
            return self._process_one(capture_id)

    def _ensure_observer(self) -> None:
        if self.observer is not None:
            return
        if self.store is None:
            assert self.store_factory is not None
            self.store = self.store_factory()
        self.observer = ShadowObserver(
            None,
            self.store,
            config=self._observer_config,
            recognizer=self._recognizer,
            ocr_perceiver=self._ocr_perceiver,
            session_id="spool-worker",
            clock=self.clock,
        )

    def _process_one(self, capture_id: str) -> dict[str, Any]:
        metadata: dict[str, Any] | None = None
        try:
            processing_path = self.spool.claim(capture_id)
        except FileNotFoundError:
            return {"capture_id": capture_id, "status": "MISSING"}
        try:
            metadata, frame = self._load(processing_path)
            existing = self.store.get_capture(capture_id)
            if existing is not None and existing.get("screenshot_hash") != metadata[
                "screenshot_hash"
            ]:
                raise ShadowSpoolError(
                    "capture_id_collision",
                    "capture ID has a different persisted screenshot hash",
                )
            if existing is not None:
                processed = self.spool.paths["processed"] / capture_id
                if processed.exists() and not self._same_capture_payload(
                    processing_path, processed, metadata
                ):
                    raise ShadowSpoolError(
                        "capture_id_collision",
                        "replayed capture differs from processed evidence",
                    )
                if processed.exists():
                    self.spool.discard_processing(capture_id)
                else:
                    self.spool.move(capture_id, "processed")
                return {
                    "capture_id": capture_id,
                    "status": "ALREADY_PROCESSED",
                }
            result = self._process(metadata, frame)
            self.spool.move(capture_id, "processed")
            return {
                "capture_id": capture_id,
                "status": "PROCESSED",
                "observation_id": result["observation_id"],
            }
        except Exception as error:
            failure = self._write_failure(
                processing_path,
                error,
                metadata,
            )
            if failure["status"] == "DIAGNOSTIC_PERSISTENCE_FAILED":
                return failure
            try:
                self.spool.move(capture_id, "failed")
            except FileNotFoundError:
                pass
            return failure

    def _load(self, processing_path: Path) -> tuple[dict[str, Any], Frame]:
        metadata_path = processing_path / "capture.json"
        frame_path = processing_path / "frame.png"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ShadowObserverError(
                "spool_metadata_invalid", "capture.json is missing or malformed"
            ) from error
        if not isinstance(metadata, dict) or not self._REQUIRED_METADATA <= set(
            metadata
        ):
            raise ShadowObserverError(
                "spool_metadata_invalid", "capture.json is missing required fields"
            )
        if metadata["spool_schema_version"] != SPOOL_SCHEMA_VERSION:
            raise ShadowObserverError(
                "spool_metadata_invalid", "unsupported spool schema version"
            )
        foreground_status = metadata["foreground_status"]
        if foreground_status not in {"confirmed_game", "confirmed_non_game", "unknown"}:
            raise ShadowObserverError(
                "foreground_context_invalid", "unsupported captured foreground status"
            )
        foreground_package = metadata["foreground_package"]
        package = metadata["package"]
        if foreground_status == "confirmed_game" and foreground_package != package:
            raise ShadowObserverError(
                "foreground_context_invalid",
                "confirmed_game foreground does not match captured package",
            )
        if (
            foreground_status == "confirmed_non_game"
            and (
                not isinstance(foreground_package, str)
                or foreground_package == package
            )
        ):
            raise ShadowObserverError(
                "foreground_context_invalid",
                "confirmed_non_game foreground is inconsistent with captured package",
            )
        capture_id = metadata["capture_id"]
        if capture_id != processing_path.name:
            raise ShadowObserverError(
                "spool_metadata_invalid", "capture_id does not match directory name"
            )
        try:
            screenshot = frame_path.read_bytes()
        except FileNotFoundError as error:
            raise ShadowObserverError(
                "spool_metadata_invalid", "frame.png is missing"
            ) from error
        digest = hashlib.sha256(screenshot).hexdigest()
        if digest != metadata["screenshot_hash"]:
            raise ShadowObserverError(
                "screenshot_integrity_mismatch",
                "frame.png SHA-256 does not match capture.json",
            )
        if len(screenshot) != metadata["png_byte_length"]:
            raise ShadowObserverError(
                "screenshot_integrity_mismatch",
                "frame.png byte length does not match capture.json",
            )
        try:
            width, height = _png_size(screenshot)
        except (ShadowObserverError, struct.error) as error:
            raise ShadowObserverError(
                "screenshot_integrity_mismatch", "frame.png is not a valid PNG"
            ) from error
        if (width, height) != (
            metadata["framebuffer_width"],
            metadata["framebuffer_height"],
        ):
            raise ShadowObserverError(
                "screenshot_integrity_mismatch",
                "frame dimensions do not match capture.json",
            )
        return metadata, Frame(
            screenshot=screenshot,
            screenshot_hash=digest,
            width=width,
            height=height,
            metadata=metadata,
        )

    def _same_capture_payload(
        self, processing_path: Path, processed_path: Path, metadata: dict[str, Any]
    ) -> bool:
        try:
            terminal_metadata = json.loads(
                (processed_path / "capture.json").read_text(encoding="utf-8")
            )
            terminal_frame = (processed_path / "frame.png").read_bytes()
        except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError):
            return False
        immutable_keys = (
            "capture_id",
            "session_id",
            "captured_at_utc",
            "package",
            "foreground_package",
            "foreground_status",
            "client_version_name",
            "client_version_code",
            "server",
            "screenshot_hash",
            "perceptual_fingerprint",
            "change_score",
            "framebuffer_width",
            "framebuffer_height",
            "png_byte_length",
        )
        return (
            isinstance(terminal_metadata, dict)
            and all(
                terminal_metadata.get(key) == metadata.get(key)
                for key in immutable_keys
            )
            and terminal_frame == (processing_path / "frame.png").read_bytes()
        )

    def _process(self, metadata: dict[str, Any], frame: Frame) -> dict[str, Any]:
        enqueued = _parse_utc(metadata["spool_enqueued_at_utc"])
        queue_latency = max(
            0.0,
            (datetime.now(timezone.utc) - enqueued).total_seconds() * 1000,
        )
        capture_timing = {
            key: metadata.get(key, 0.0)
            for key in (
                "capture_duration_ms",
                "capture_staging_duration_ms",
                "spool_write_duration_ms",
            )
        }
        return self.observer.process_spooled_frame(
            frame,
            capture_id=metadata["capture_id"],
            captured_at_utc=metadata["captured_at_utc"],
            capture_timing_ms=capture_timing,
            queue_latency_ms=queue_latency,
        )

    def _write_failure(
        self,
        processing_path: Path,
        error: Exception,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        capture_id = processing_path.name
        payload = {
            "capture_id": capture_id,
            "failed_at_utc": _utc_now(),
            "error_reason": getattr(error, "reason", "processing_failed"),
            "failure_class": (
                "validated_capture_processing_failure"
                if metadata is not None
                else "untrusted_spool_evidence"
            ),
            "error": str(error),
            "error_diagnostic": {
                "stage": "worker",
                "exception_type": type(error).__name__,
                "message": str(error),
            },
        }
        if metadata is not None:
            payload["capture_metadata"] = dict(metadata)
            payload.update(
                {
                    "validation_status": "FAIL",
                    "captured_at_utc": metadata.get("captured_at_utc"),
                    "screenshot_hash": metadata.get("screenshot_hash"),
                }
            )
        try:
            _write_durable_json(processing_path / "failure.json", payload)
        except OSError as write_error:
            return {
                "capture_id": capture_id,
                "status": "DIAGNOSTIC_PERSISTENCE_FAILED",
                "error_reason": "failure_diagnostic_persistence_failed",
                "error": str(write_error),
                "error_diagnostic": {
                    "stage": "failure_diagnostic_persistence",
                    "exception_type": type(write_error).__name__,
                    "message": str(write_error),
                    "original_failure": payload,
                },
            }
        return {"capture_id": capture_id, "status": "FAILED", **payload}


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
        ("rank", r"\bmy\s+rank\s*[:#]?\s*(\d+)"),
        ("total_points", r"\bmy\s+total\s+points\s*[:#]?\s*(\d+)"),
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
        level_match = re.search(r"\blv\.?\s*(\d+)(?:\s*[-/]\s*(\d+))?\b", normalized)
        if level_match:
            value = level_match.group(1)
            if level_match.group(2):
                value = f"{value}-{level_match.group(2)}"
            candidates.append(
                {"key": "level", "value": value, "source_text": anchor.text}
            )
        if re.fullmatch(r"(?:\d+:)?\d{1,2}:\d{2}", normalized):
            candidates.append(
                {
                    "key": "time",
                    "value": anchor.text.strip(),
                    "source_text": anchor.text,
                }
            )
        quantity_match = re.fullmatch(
            r"(\d+(?:[.,]\d+)?[km])\s+([a-z][a-z ]*)", normalized
        )
        if quantity_match:
            candidates.append(
                {
                    "key": "quantity",
                    "value": quantity_match.group(1).upper(),
                    "source_text": anchor.text,
                }
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


def _write_durable_bytes(path: Path, content: bytes) -> None:
    with path.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _write_durable_json(path: Path, payload: dict[str, Any]) -> None:
    _write_durable_bytes(
        path, (json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n").encode()
    )


def _write_failure_marker(path: Path, capture_id: str) -> None:
    try:
        _write_durable_json(
            path / "failure.json",
            {
                "capture_id": capture_id,
                "failure_class": "uncommitted_capture",
                "error_reason": "spool_enqueue_failed",
                "message": "capture directory never reached the inbox commit point",
            },
        )
    except OSError:
        pass


def _remove_directory(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            _remove_directory(child)
        else:
            child.unlink()
    path.rmdir()


def _safe_capture_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return cleaned[:80] or "session"


def _parse_utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ShadowObserverError("spool_metadata_invalid", "UTC timestamp is missing")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ShadowObserverError(
            "spool_metadata_invalid", "UTC timestamp is malformed"
        ) from error
    if parsed.tzinfo is None:
        raise ShadowObserverError(
            "spool_metadata_invalid", "UTC timestamp has no timezone"
        )
    return parsed.astimezone(timezone.utc)


def _new_timing() -> dict[str, float]:
    return {key: 0.0 for key in _TIMING_KEYS}


def _elapsed_ms(started: float, finished: float) -> float:
    return round(max(0.0, finished - started) * 1000, 3)


def _complete_timing(
    timing: dict[str, float], started: float | None, finished: float
) -> None:
    if started is not None:
        timing["total_duration_ms"] = _elapsed_ms(started, finished)


def _foreground_status(foreground_package: Any, package: str) -> str:
    if not foreground_package:
        return "unknown"
    if foreground_package == package:
        return "confirmed_game"
    return "confirmed_non_game"


def _foreground_context(
    metadata: dict[str, Any], package: str
) -> tuple[str, str | None, dict[str, Any] | None]:
    foreground_package = metadata.get("foreground_package")
    parser = metadata.get("foreground_parser")
    declared_status = metadata.get("foreground_status")
    if declared_status == "confirmed_game" and foreground_package == package:
        status = "confirmed_game"
    elif declared_status == "confirmed_non_game" and foreground_package:
        status = "confirmed_non_game"
    else:
        status = _foreground_status(foreground_package, package)
    return status, foreground_package, parser
