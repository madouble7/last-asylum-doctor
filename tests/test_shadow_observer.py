from __future__ import annotations

import binascii
import hashlib
import json
import shutil
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from last_asylum_doctor.probe import shadow_observer as shadow_observer_module
from last_asylum_doctor.probe.navigation import Frame, OCRAnchor
from last_asylum_doctor.probe.shadow_observer import (
    AdbShadowFrameSource,
    ObservationStore,
    ObservationStoreCorruptionError,
    ShadowObserver,
    ShadowObserverConfig,
    ShadowSpool,
    ShadowSpoolError,
    ShadowSpoolWorker,
    _SingleWorkerLock,
    extract_candidate_values,
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
    frame_metadata: dict[str, object] = {
        "client_version_name": "1.0.97",
        "client_version_code": 97,
        "package": "com.phs.global",
        "foreground_package": "com.phs.global",
        "foreground_status": "confirmed_game",
    }
    if metadata:
        frame_metadata.update(metadata)
    return Frame(
        screenshot=content,
        screenshot_hash="fixture-hash",
        width=100,
        height=100,
        ocr_anchors=tuple(OCRAnchor(text, 0.95) for text in texts),
        metadata=frame_metadata,
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


def test_cumulative_drift_compares_against_last_recorded_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fingerprints = {
        b"a": "0000000000000000",
        b"b": "0000000000000001",
        b"c": "000000000000003f",
    }
    monkeypatch.setattr(
        shadow_observer_module,
        "perceptual_fingerprint",
        lambda screenshot: fingerprints[screenshot],
    )
    source = FixtureSource(
        frame(b"a", "Research Lab", "Research"), frame(b"b"), frame(b"c")
    )
    active = observer(tmp_path, source, change_threshold=0.08)

    first = active.run_once()
    second = active.run_once()
    third = active.run_once()

    assert first is not None
    assert second is None
    assert third is not None
    assert third["change_score"] == 0.09375
    assert active.suppressed_count == 1


def test_meaningful_change_records_transition_and_evidence(tmp_path: Path) -> None:
    source = FixtureSource(
        frame(b"before", "Research Lab", "Research"),
        frame(b"after", "Training Grounds", "Current Level", "Next Level", "Back"),
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


def test_unknown_foreground_is_review_only_and_skips_ocr(tmp_path: Path) -> None:
    perceiver = RecordingOcr()
    active = ShadowObserver(
        FixtureSource(
            frame(
                b"unknown-foreground",
                "Research Lab",
                metadata={"foreground_package": None, "foreground_status": "unknown"},
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
    assert observation["current_screen_state"] == "foreground_unknown"
    assert observation["validation_status"] == "REVIEW"
    assert observation["foreground_status"] == "unknown"
    assert observation["screenshot_path"] is None
    assert perceiver.calls == 0
    assert not list((tmp_path / "screenshots").glob("*.png"))


def test_malformed_foreground_dump_is_unknown() -> None:
    screenshot = png(2, 2, (10, 20, 30))

    def runner(adb: Path, *args: str, serial: str | None = None) -> bytes:
        del adb, serial
        if args == ("devices", "-l"):
            return b"emulator-5554\tdevice\n"
        if args[:3] == ("shell", "dumpsys", "package"):
            return b"versionName=1.0.97 versionCode=97"
        if args[:3] == ("shell", "dumpsys", "activity"):
            return b"activity service returned no resumed activity"
        return screenshot

    captured = AdbShadowFrameSource(runner=runner).capture()

    assert captured.metadata["foreground_package"] is None
    assert captured.metadata["foreground_status"] == "unknown"
    assert captured.metadata["foreground_parser"]["matched"] is False


def test_ocr_failure_is_recorded_with_diagnostic(tmp_path: Path) -> None:
    class FailingOcr:
        def detect(self, screenshot: bytes) -> list[OCRAnchor]:
            del screenshot
            raise ValueError("decoder unavailable")

    active = ShadowObserver(
        FixtureSource(frame(b"ocr-failure")),
        ObservationStore(
            tmp_path / "observations.jsonl",
            tmp_path / "screenshots",
            max_captures=10,
        ),
        ocr_perceiver=FailingOcr(),
        session_id="test-session",
    )

    observation = active.run_once()

    assert observation["error_reason"] == "ocr_failed"
    assert observation["error_diagnostic"]["stage"] == "ocr"
    assert observation["error_diagnostic"]["exception_type"] == "ValueError"
    assert observation["validation_status"] == "FAIL"


def test_recognizer_failure_is_recorded_with_diagnostic(tmp_path: Path) -> None:
    class FailingRecognizer:
        def recognize(self, frame: Frame) -> None:
            del frame
            raise RuntimeError("recognizer unavailable")

    active = ShadowObserver(
        FixtureSource(frame(b"recognizer-failure")),
        ObservationStore(
            tmp_path / "observations.jsonl",
            tmp_path / "screenshots",
            max_captures=10,
        ),
        recognizer=FailingRecognizer(),
        session_id="test-session",
    )

    observation = active.run_once()

    assert observation["error_reason"] == "recognition_failed"
    assert observation["error_diagnostic"]["stage"] == "recognition"
    assert observation["current_screen_state"] == "unavailable"


def test_storage_failure_is_returned_without_false_persistence(tmp_path: Path) -> None:
    class FailingStore:
        def append(self, *args: object, **kwargs: object) -> dict[str, object]:
            del args, kwargs
            raise OSError("disk full")

    active = ShadowObserver(
        FixtureSource(frame(b"storage-failure", "Research Lab", "Research")),
        FailingStore(),
        session_id="test-session",
    )

    observation = active.run_once()

    assert observation["error_reason"] == "storage_failed"
    assert observation["error_diagnostic"]["stage"] == "storage"
    assert observation["error_diagnostic"]["original_failure"]["stage"] == "storage"


def test_timing_schema_and_run_summary(tmp_path: Path) -> None:
    active = observer(
        tmp_path, FixtureSource(frame(b"timed", "Research Lab", "Research"))
    )

    result = active.run(duration=0)
    saved = json.loads(active.store.output.read_text(encoding="utf-8"))

    assert set(saved["timing_ms"]) == {
        "capture_duration_ms",
        "ocr_duration_ms",
        "recognition_extraction_duration_ms",
        "persistence_duration_ms",
        "total_duration_ms",
    }
    assert result["timing_samples"] == 1
    assert result["timing_ms_total"]["total_duration_ms"] >= 0


def test_candidate_extraction_preserves_observed_formats() -> None:
    candidates = extract_candidate_values(
        tuple(
            OCRAnchor(text)
            for text in (
                "Lv.100 Wandering Blight",
                "Lv.25-26",
                "My Rank: 12",
                "My Total Points: 120",
                "00:32:06",
                "1K Grain",
            )
        )
    )

    assert {item["value"] for item in candidates if item["key"] == "level"} == {
        "100",
        "25-26",
    }
    values = {item["key"]: item["value"] for item in candidates}
    assert set(
        {
            "rank": "12",
            "total_points": "120",
            "time": "00:32:06",
            "quantity": "1K",
        }.items()
    ) <= set(values.items())
    assert all(item["source_text"] for item in candidates)


def spool_capture(
    spool: ShadowSpool,
    capture_id: str,
    screenshot: bytes,
    **metadata: object,
) -> Path:
    digest = hashlib.sha256(screenshot).hexdigest()
    values: dict[str, object] = {
        "spool_schema_version": "0.3",
        "capture_id": capture_id,
        "session_id": "capture-session",
        "captured_at_utc": "2026-08-29T12:00:00+00:00",
        "capture_duration_ms": 1.0,
        "capture_staging_duration_ms": 1.0,
        "spool_write_duration_ms": 1.0,
        "package": "com.phs.global",
        "foreground_package": "com.phs.global",
        "foreground_status": "confirmed_game",
        "foreground_parser": {},
        "client_version_name": "1.0.97",
        "client_version_code": 97,
        "server": "283",
        "screenshot_hash": digest,
        "perceptual_fingerprint": "0000000000000000",
        "change_score": 1.0,
        "framebuffer_width": 2,
        "framebuffer_height": 2,
        "png_byte_length": len(screenshot),
        "spool_enqueued_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    values.update(metadata)
    return spool.enqueue(capture_id, screenshot, values)


def worker(tmp_path: Path, spool: ShadowSpool, perceiver: object | None = None):
    store = ObservationStore(
        tmp_path / "observations.jsonl", tmp_path / "screenshots", max_captures=10
    )
    return ShadowSpoolWorker(spool, store, ocr_perceiver=perceiver), store


def test_spool_commit_exposes_complete_capture_directory_without_ocr(
    tmp_path: Path,
) -> None:
    perceiver = RecordingOcr()
    active = ShadowObserver(
        FixtureSource(frame(png(2, 2, (1, 2, 3)))),
        ObservationStore(
            tmp_path / "unused.jsonl", tmp_path / "unused", max_captures=1
        ),
        ocr_perceiver=perceiver,
        session_id="capture-session",
    )
    spool = ShadowSpool(tmp_path / "spool")

    result = active.spool_once(spool)

    assert result["status"] == "SPOOLED"
    assert perceiver.calls == 0
    inbox = spool.root / "inbox" / result["capture_id"]
    sidecar = json.loads((inbox / "capture.json").read_text(encoding="utf-8"))
    assert sorted(path.name for path in inbox.iterdir()) == [
        "capture.json",
        "frame.png",
    ]
    assert result["capture_total_duration_ms"] >= 0
    assert "capture_total_duration_ms" not in sidecar
    assert sidecar["capture_staging_duration_ms"] >= 0
    assert not list((spool.root / "tmp").iterdir())


def test_spool_precommit_failure_stays_out_of_inbox_with_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spool = ShadowSpool(tmp_path / "spool")

    def fail_commit(source: Path, destination: Path) -> None:
        del source, destination
        raise OSError("commit unavailable")

    monkeypatch.setattr(shadow_observer_module.os, "replace", fail_commit)

    with pytest.raises(OSError, match="commit unavailable"):
        spool_capture(spool, "uncommitted", png(2, 2, (1, 2, 3)))

    temporary = next((spool.root / "tmp").iterdir())
    assert not (spool.root / "inbox" / "uncommitted").exists()
    assert (temporary / "failure.json").exists()
    assert json.loads((temporary / "failure.json").read_text())["failure_class"] == (
        "uncommitted_capture"
    )


def test_worker_success_lifecycle_preserves_capture_and_separates_timing(
    tmp_path: Path,
) -> None:
    class ResearchOcr:
        def detect(self, screenshot: bytes) -> list[OCRAnchor]:
            del screenshot
            return [OCRAnchor("Research Lab", 0.95), OCRAnchor("Research", 0.95)]

    spool = ShadowSpool(tmp_path / "spool")
    path = spool_capture(spool, "capture-1", png(2, 2, (1, 2, 3)))
    active, store = worker(tmp_path, spool, ResearchOcr())

    result = active.process_pending()
    saved = json.loads(store.output.read_text(encoding="utf-8"))

    assert result["processed"] == 1
    assert (spool.root / "processed" / path.name / "frame.png").exists()
    assert not (spool.root / "inbox" / path.name).exists()
    assert saved["capture_id"] == "capture-1"
    assert saved["timestamp"] == "2026-08-29T12:00:00+00:00"
    assert "timing_ms" not in saved
    assert set(saved["capture_timing_ms"]) == {
        "capture_duration_ms",
        "capture_staging_duration_ms",
        "spool_write_duration_ms",
    }
    assert saved["processing_timing_ms"]["queue_latency_ms"] >= 0


def test_exact_replay_of_processed_capture_is_idempotent_and_discarded(
    tmp_path: Path,
) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    spool_capture(spool, "replay", png(2, 2, (1, 2, 3)))
    active, store = worker(tmp_path, spool)
    assert active.process_pending()["processed"] == 1
    shutil.copytree(
        spool.root / "processed" / "replay", spool.root / "inbox" / "replay"
    )

    result = active.process_pending()

    assert result["already_processed"] == 1
    assert not (spool.root / "inbox" / "replay").exists()
    assert not (spool.root / "processing" / "replay").exists()
    assert (spool.root / "processed" / "replay").exists()
    assert len(store.output.read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("metadata", "spool_metadata_invalid"),
        ("png", "screenshot_integrity_mismatch"),
    ],
)
def test_worker_moves_invalid_evidence_to_failed_with_diagnostic(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    path = spool_capture(spool, "bad-capture", png(2, 2, (1, 2, 3)))
    if mutation == "metadata":
        (path / "capture.json").write_text("{}", encoding="utf-8")
    else:
        (path / "frame.png").write_bytes(png(2, 2, (9, 8, 7)))
    active, _ = worker(tmp_path, spool)

    result = active.process_pending()
    failed = spool.root / "failed" / "bad-capture"
    diagnostic = json.loads((failed / "failure.json").read_text(encoding="utf-8"))

    assert result["failed"] == 1
    assert diagnostic["error_reason"] == reason
    assert (failed / "frame.png").exists()


def test_worker_ocr_failure_is_terminal_and_retains_evidence(tmp_path: Path) -> None:
    class FailingOcr:
        def detect(self, screenshot: bytes) -> list[OCRAnchor]:
            del screenshot
            raise RuntimeError("OCR engine unavailable")

    spool = ShadowSpool(tmp_path / "spool")
    path = spool_capture(spool, "ocr-failure", png(2, 2, (1, 2, 3)))
    original_png = (path / "frame.png").read_bytes()
    active, _ = worker(tmp_path, spool, FailingOcr())

    result = active.process_pending()
    failure = json.loads(
        (spool.root / "failed" / path.name / "failure.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["failed"] == 1
    assert failure["error_reason"] == "processing_failed"
    assert failure["failure_class"] == "validated_capture_processing_failure"
    assert failure["error_diagnostic"]["stage"] == "worker"
    assert (
        spool.root / "failed" / path.name / "frame.png"
    ).read_bytes() == original_png


def test_worker_rejects_same_id_with_different_payload_after_processing(
    tmp_path: Path,
) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    first_path = spool_capture(spool, "same-id", png(2, 2, (1, 2, 3)))
    active, store = worker(tmp_path, spool)
    assert active.process_pending()["processed"] == 1
    second_path = spool_capture(spool, "same-id", png(2, 2, (9, 8, 7)))

    result = active.process_pending()
    failure = json.loads(
        (spool.root / "failed" / second_path.name / "failure.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["failed"] == 1
    assert failure["error_reason"] == "capture_id_collision"
    assert failure["failure_class"] == "validated_capture_processing_failure"
    assert (spool.root / "processed" / first_path.name).exists()
    assert store.observation_count == 1


@pytest.mark.parametrize(
    "metadata_update",
    [
        {"remove": "foreground_status"},
        {"foreground_status": "not-a-status"},
        {
            "foreground_status": "confirmed_game",
            "foreground_package": "com.other.app",
        },
    ],
)
def test_worker_foreground_context_fails_closed(
    tmp_path: Path, metadata_update: dict[str, object]
) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    path = spool_capture(spool, "foreground-check", png(2, 2, (1, 2, 3)))
    metadata = json.loads((path / "capture.json").read_text(encoding="utf-8"))
    removed = metadata_update.get("remove")
    if isinstance(removed, str):
        metadata.pop(removed)
    else:
        metadata.update(metadata_update)
    (path / "capture.json").write_text(json.dumps(metadata), encoding="utf-8")
    active, store = worker(tmp_path, spool)

    result = active.process_pending()

    assert result["failed"] == 1
    assert not store.output.exists()
    failure = json.loads(
        (spool.root / "failed" / path.name / "failure.json").read_text(
            encoding="utf-8"
        )
    )
    assert failure["error_reason"] == (
        "spool_metadata_invalid"
        if removed is not None
        else "foreground_context_invalid"
    )


def test_valid_unknown_foreground_remains_unknown(tmp_path: Path) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    spool_capture(
        spool,
        "unknown-foreground",
        png(2, 2, (1, 2, 3)),
        foreground_package=None,
        foreground_status="unknown",
    )
    active, store = worker(tmp_path, spool)

    result = active.process_pending()
    saved = json.loads(store.output.read_text(encoding="utf-8"))

    assert result["processed"] == 1
    assert saved["foreground_status"] == "unknown"
    assert saved["current_screen_state"] == "foreground_unknown"


def test_worker_recovers_processing_and_does_not_duplicate_jsonl_after_restart(
    tmp_path: Path,
) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    path = spool_capture(spool, "restart-capture", png(2, 2, (1, 2, 3)))
    first, store = worker(tmp_path, spool)
    first.process_pending()
    (spool.root / "processed" / path.name).replace(
        spool.root / "processing" / path.name
    )

    second = ShadowSpoolWorker(
        spool,
        ObservationStore(
            store.output, tmp_path / "screenshots-2", max_captures=10
        ),
    )
    result = second.process_pending()

    assert result["recovered"] == ["restart-capture"]
    assert result["already_processed"] == 1
    assert len(store.output.read_text(encoding="utf-8").splitlines()) == 1
    assert (spool.root / "processed" / path.name).exists()


def test_observation_append_flushes_and_fsynchronizes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sync_calls = 0

    def record_fsync(file_descriptor: int) -> None:
        nonlocal sync_calls
        assert file_descriptor >= 0
        sync_calls += 1

    monkeypatch.setattr(shadow_observer_module.os, "fsync", record_fsync)
    store = ObservationStore(tmp_path / "observations.jsonl", tmp_path, max_captures=1)

    store.append({"capture_id": "durable", "timestamp": "now"})

    assert sync_calls == 1


@pytest.mark.parametrize(
    "damaged", [b'{"capture_id":"abc"', b'{"capture_id":"abc"\n', b"\xff\xfe"]
)
def test_final_jsonl_tail_is_quarantined_and_truncated(
    tmp_path: Path, damaged: bytes
) -> None:
    output = tmp_path / "observations.jsonl"
    valid = b'{"capture_id":"good","timestamp":"now"}\n'
    output.write_bytes(valid + damaged)

    store = ObservationStore(output, tmp_path / "screenshots", max_captures=1)

    assert output.read_bytes() == valid
    artifacts = list(tmp_path.glob("observations.jsonl.corrupt-tail.*.bin"))
    assert len(artifacts) == 1
    assert artifacts[0].read_bytes() == damaged
    assert store.contains_capture_id("good")


def test_valid_jsonl_without_final_newline_gets_clean_boundary_on_append(
    tmp_path: Path,
) -> None:
    output = tmp_path / "observations.jsonl"
    output.write_bytes(b'{"capture_id":"good","timestamp":"now"}')
    store = ObservationStore(output, tmp_path / "screenshots", max_captures=1)

    store.append({"capture_id": "next", "timestamp": "later"})

    assert len(output.read_text(encoding="utf-8").splitlines()) == 2
    assert store.contains_capture_id("next")


def test_malformed_middle_jsonl_record_fails_clearly(tmp_path: Path) -> None:
    output = tmp_path / "observations.jsonl"
    output.write_bytes(
        b'{"capture_id":"first"}\n{not-json}\n{"capture_id":"last"}\n'
    )

    with pytest.raises(ObservationStoreCorruptionError, match="final tail"):
        ObservationStore(output, tmp_path / "screenshots", max_captures=1)

    assert output.read_bytes().count(b"{not-json}") == 1


def test_capture_id_idempotence_survives_tail_recovery(tmp_path: Path) -> None:
    output = tmp_path / "observations.jsonl"
    output.write_bytes(
        b'{"capture_id":"stable","screenshot_hash":"hash"}\n'
        b'{"capture_id":"torn"'
    )
    store = ObservationStore(output, tmp_path / "screenshots", max_captures=1)

    result = store.append(
        {"capture_id": "stable", "screenshot_hash": "hash", "timestamp": "later"}
    )

    assert result["capture_id"] == "stable"
    assert len(output.read_text(encoding="utf-8").splitlines()) == 1


def test_spool_rejects_capture_id_collision_without_replacing_existing_payload(
    tmp_path: Path,
) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    first = spool_capture(spool, "collision", png(2, 2, (1, 2, 3)))
    original_png = (first / "frame.png").read_bytes()

    with pytest.raises(ShadowSpoolError, match="already exists"):
        spool_capture(spool, "collision", png(2, 2, (9, 8, 7)))

    assert (first / "frame.png").read_bytes() == original_png
    assert len(spool.inbox_items()) == 1


def test_second_worker_refuses_to_operate_while_lock_is_held(tmp_path: Path) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    first, _ = worker(tmp_path, spool)
    second, _ = worker(tmp_path, spool)

    with _SingleWorkerLock(spool.root):
        with pytest.raises(ShadowSpoolError, match="another Shadow Spool worker"):
            second.process_pending()

    assert first.process_pending()["processed"] == 0


def test_second_worker_is_refused_before_store_tail_recovery(tmp_path: Path) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    output = tmp_path / "observations.jsonl"
    valid = b'{"capture_id":"good","timestamp":"now"}\n'
    output.write_bytes(valid + b'{"capture_id":"torn"')
    store_created = False

    def create_store() -> ObservationStore:
        nonlocal store_created
        store_created = True
        return ObservationStore(output, tmp_path / "screenshots", max_captures=1)

    second = ShadowSpoolWorker(spool, store_factory=create_store)
    original = output.read_bytes()
    with _SingleWorkerLock(spool.root):
        with pytest.raises(ShadowSpoolError, match="another Shadow Spool worker"):
            second.process_pending()

    assert not store_created
    assert output.read_bytes() == original


def test_worker_keeps_processing_item_when_failure_diagnostic_is_not_durable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spool = ShadowSpool(tmp_path / "spool")
    spool_capture(spool, "diagnostic-failure", png(2, 2, (1, 2, 3)))
    active, _ = worker(tmp_path, spool)

    class FailingOcr:
        def detect(self, screenshot: bytes) -> list[OCRAnchor]:
            del screenshot
            raise RuntimeError("OCR failed")

    original_write = shadow_observer_module._write_durable_json

    def fail_failure_json(path: Path, payload: dict[str, object]) -> None:
        if path.name == "failure.json":
            raise OSError("diagnostic disk failure")
        original_write(path, payload)

    monkeypatch.setattr(
        shadow_observer_module, "_write_durable_json", fail_failure_json
    )
    active.observer = None
    active._ocr_perceiver = FailingOcr()
    result = active.process_pending()

    assert result["results"][0]["status"] == "DIAGNOSTIC_PERSISTENCE_FAILED"
    assert result["failed"] == 0
    assert (spool.root / "processing" / "diagnostic-failure").exists()
    assert not (spool.root / "failed" / "diagnostic-failure").exists()
