"""Run the passive, read-only PROBE Shadow Observer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from last_asylum_doctor.probe.navigation import RapidOcrPerceiver
from last_asylum_doctor.probe.shadow_observer import (
    DEFAULT_EVIDENCE_DIR,
    DEFAULT_OUTPUT,
    AdbShadowFrameSource,
    ObservationStore,
    ShadowObserver,
    ShadowObserverConfig,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Observe Last Asylum through BlueStacks without game-control operations."
        )
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="seconds between framebuffer polls (default: 5)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="seconds to run; zero means until Ctrl+C (default: 0)",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="append-only JSONL observation stream",
    )
    parser.add_argument(
        "--evidence-dir",
        default=str(DEFAULT_EVIDENCE_DIR),
        help="bounded raw screenshot directory",
    )
    parser.add_argument(
        "--adb",
        default=r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe",
        help="BlueStacks ADB bridge executable",
    )
    parser.add_argument("--serial", help="device serial; auto-detect one ready device")
    parser.add_argument("--server", default="283", help="server label in observations")
    parser.add_argument(
        "--max-captures",
        type=int,
        default=100,
        help="maximum retained raw screenshots per observer session",
    )
    parser.add_argument(
        "--change-threshold",
        type=float,
        default=0.08,
        help="minimum perceptual change score to record (default: 0.08)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print each recorded observation",
    )
    args = parser.parse_args(argv)

    config = ShadowObserverConfig(
        interval=args.interval,
        change_threshold=args.change_threshold,
        max_captures=args.max_captures,
        server=args.server,
    )
    source = AdbShadowFrameSource(
        adb=Path(args.adb),
        serial=args.serial,
        server=args.server,
    )
    store = ObservationStore(
        Path(args.output),
        Path(args.evidence_dir),
        max_captures=args.max_captures,
    )
    observer = ShadowObserver(
        source,
        store,
        config=config,
        ocr_perceiver=RapidOcrPerceiver(),
    )

    print(f"PROBE Shadow Observer session: {observer.session_id}")
    try:
        result = observer.run(None if args.duration == 0 else args.duration)
    except KeyboardInterrupt:
        result = {
            "session_id": observer.session_id,
            "observations_recorded": store.observation_count,
            "captures_retained": store.capture_count,
            "duplicates_suppressed": observer.suppressed_count,
            "stop_reason": "keyboard_interrupt",
            "output": str(store.output),
        }
    print(result)
    if args.verbose:
        print(f"Observation stream: {store.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
