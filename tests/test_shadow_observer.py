from __future__ import annotations

import binascii
import json
import struct
import zlib
from pathlib import Path

import pytest

from last_asylum_doctor.probe.navigation import Frame, OCRAnchor
from last_asylum_doctor.probe.shadow_observer import (
    AdbShadowFrameSource,
    ObservationStore,
    ShadowObserver,
    ShadowObserverConfig,
    perceptual_fingerprint,
)


def png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    row = b"\x00" + bytes(rgb) * width
    raw = row * height

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def frame(
    content: bytes,
    *texts: str,
    metadata: dict[str, object] | None = None,
) -> Frame:
    return Frame(
        screenshot=content,
        screenshot_hash="fixture-hash",
        width=100,
        height=100,
        ocr_anchors=tuple(OCRAnchor(text, 0.95) for text in texts),
        metadata=metadata
        or {"client_version_name": "1.0.97", "client_version_code": 97},
    )


class FixtureSource:
    def __init__(self, *frames: Frame) -> None:
        self.frames = list(frames)

    def capture(self, label: str | None = None) -> Frame:
        del label
        return self.frames.pop(0)


class RecordingOcr:
    def __init__(self) -> None:
        self.calls = 0

    def detect(self, screenshot: bytes) -> list[OCRAnchor]:
        del screenshot
        self.calls += 1
        return [OCRAnchor("Unexpected popup", 0.95)]


def observer(
    tmp_path: Path, source: FixtureSource, **config_values: object
) -> ShadowObserver:
    config = ShadowObserverConfig(**config_values)
    store = ObservationStore(
        tmp_path / "observations.jsonl",
        tmp_path / "screenshots",
        max_captures=config.max_captures,
    )
    return ShadowObserver(source, store, config=config, session_id="test-session")


def test_no_generated_game_control_operation_path_exists() -> None:
    calls: list[tuple[str, ...]] = []
    screenshot = png(2, 2, (10, 20, 30))

    def runner(adb: Path, *args: str, serial: str | None = None) -> bytes:
        del adb, serial
        calls.append(args)
        if args == ("devices", "-l"):
            return b"List of devices attached\nemulator-5554\tdevice\n"
        if args[:3] == ("shell", "dumpsys", "package"):
            return b"versionName=1.0.97 versionCode=97"
        if args[:3] == ("shell", "dumpsys", "activity"):
            return b"mResumedActivity: ActivityRecord{ com.phs.global/.MainActivity }"
        assert args == ("exec-out", "screencap", "-p")
        return screenshot

    source = AdbShadowFrameSource(runner=runner)
    source.capture()

    command_text = " ".join(" ".join(call) for call in calls).casefold()
    assert all(
        term not in command_text for term in (" input ", "tap", "swipe", "keyevent")
    )


def test_duplicate_frame_is_suppressed(tmp_path: Path) -> None:
    source = FixtureSource(frame(b"same", "Research Lab", "Research"), frame(b"same"))
    active = observer(tmp_path, source)

    first = active.run_once()
    second = active.run_once()

    assert first is not None
    assert second is None
    assert active.suppressed_count == 1
    assert len(active.store.output.read_text(encoding="utf-8").splitlines()) == 1


def test_meaningful_change_records_transition_and_evidence(tmp_path: Path) -> None:
    source = FixtureSource(
        frame(b"before", "Research Lab", "Research"),
        frame(b"after", "Training Grounds"),
    )
    active = observer(tmp_path, source)

    first = active.run_once()
    second = active.run_once()

    assert first is not None and second is not None
    assert first["current_screen_state"] == "research_lab"
    assert second["previous_screen_state"] == "research_lab"
    assert second["current_screen_state"] == "training_grounds"
    assert second["transition_provenance"]["previous_observation_id"] == first[
        "observation_id"
    ]
    assert Path(second["screenshot_path"]).exists()
    assert second["validation_status"] == "PASS"


def test_unknown_state_is_recorded_for_review(tmp_path: Path) -> None:
    active = observer(tmp_path, FixtureSource(frame(b"unknown", "Unexpected popup")))

    observation = active.run_once()

    assert observation is not None
    assert observation["current_screen_state"] == "unknown"
    assert observation["validation_status"] == "REVIEW"
    assert observation["ocr_raw_output"][0]["text"] == "Unexpected popup"


def test_observation_jsonl_has_required_schema(tmp_path: Path) -> None:
    active = observer(
        tmp_path, FixtureSource(frame(b"known", "Research Lab", "Research"))
    )

    observation = active.run_once()
    saved = json.loads(active.store.output.read_text(encoding="utf-8"))

    assert saved == observation
    assert {
        "timestamp",
        "session_id",
        "package",
        "client_version_name",
        "client_version_code",
        "server",
        "screenshot_hash",
        "previous_screen_state",
        "current_screen_state",
        "ocr_anchors",
        "ocr_raw_output",
        "extracted_candidate_values",
        "validation_status",
        "transition_provenance",
        "change_score",
    } <= saved.keys()
    assert saved["session_id"] == "test-session"


def test_raw_storage_is_bounded_per_session(tmp_path: Path) -> None:
    source = FixtureSource(frame(b"one"), frame(b"two"), frame(b"three"))
    active = observer(tmp_path, source, max_captures=2)

    observations = [active.run_once(), active.run_once(), active.run_once()]
    retained = list((tmp_path / "screenshots").glob("*.png"))

    assert len([item for item in observations if item is not None]) == 3
    assert len(retained) == 2
    assert active.store.capture_count == 2
    assert observations[2]["raw_capture_retained"] is False
    assert observations[2]["retention_note"] == "maximum raw captures reached"


def test_disconnected_emulator_is_recorded_and_stops(tmp_path: Path) -> None:
    def runner(adb: Path, *args: str, serial: str | None = None) -> bytes:
        del adb, serial
        assert args == ("devices", "-l")
        return b"List of devices attached\n"

    source = AdbShadowFrameSource(runner=runner)
    active = observer(tmp_path, FixtureSource())
    active.source = source

    result = active.run(duration=10)
    saved = json.loads(active.store.output.read_text(encoding="utf-8"))

    assert result["stop_reason"] == "adb_disconnected"
    assert saved["current_screen_state"] == "unavailable"
    assert saved["validation_status"] == "FAIL"
    assert saved["screenshot_hash"] is None


def test_client_metadata_and_foreground_are_propagated(tmp_path: Path) -> None:
    screenshot = png(2, 2, (100, 110, 120))
    calls: list[tuple[str, ...]] = []

    def runner(adb: Path, *args: str, serial: str | None = None) -> bytes:
        del adb, serial
        calls.append(args)
        if args == ("devices", "-l"):
            return b"emulator-5554\tdevice\n"
        if args[:3] == ("shell", "dumpsys", "package"):
            return b"versionName=2.4.1 versionCode=241"
        if args[:3] == ("shell", "dumpsys", "activity"):
            return b"mResumedActivity: ActivityRecord{ com.phs.global/.MainActivity }"
        return screenshot

    source = AdbShadowFrameSource(runner=runner, server="283")
    active = observer(tmp_path, source)
    observation = active.run_once()

    assert observation["package"] == "com.phs.global"
    assert observation["client_version_name"] == "2.4.1"
    assert observation["client_version_code"] == 241
    assert observation["server"] == "283"
    assert (
        observation["screenshot_hash"]
        == __import__("hashlib").sha256(screenshot).hexdigest()
    )
    assert perceptual_fingerprint(screenshot) != ""


@pytest.mark.parametrize("foreground", ["com.other.app", "com.other.app/.Activity"])
def test_non_game_foreground_is_review_only(tmp_path: Path, foreground: str) -> None:
    active = observer(
        tmp_path,
        FixtureSource(
            frame(
                b"other-app",
                "Research Lab",
                metadata={
                    "package": "com.phs.global",
                    "foreground_package": foreground,
                },
            )
        ),
    )

    observation = active.run_once()

    assert observation["current_screen_state"] == "not_game_foreground"
    assert observation["validation_status"] == "REVIEW"
    assert observation["screenshot_path"] is None
    assert observation["ocr_anchors"] == []


def test_non_game_foreground_skips_ocr(tmp_path: Path) -> None:
    perceiver = RecordingOcr()
    active = ShadowObserver(
        FixtureSource(
            frame(
                b"other-app",
                metadata={
                    "package": "com.phs.global",
                    "foreground_package": "com.other.app",
                },
            )
        ),
        ObservationStore(
            tmp_path / "observations.jsonl",
            tmp_path / "screenshots",
            max_captures=10,
        ),
        ocr_perceiver=perceiver,
        session_id="test-session",
    )

    observation = active.run_once()

    assert observation is not None
    assert observation["current_screen_state"] == "not_game_foreground"
    assert perceiver.calls == 0
