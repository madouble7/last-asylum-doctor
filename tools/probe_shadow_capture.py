"""Capture passive Shadow Observer frames into the local filesystem spool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from last_asylum_doctor.probe.shadow_observer import (
    DEFAULT_SPOOL_ROOT,
    AdbShadowFrameSource,
    ShadowObserver,
    ShadowObserverConfig,
    ShadowSpool,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture read-only frames into the Shadow Observer filesystem spool."
        )
    )
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--spool-root", default=str(DEFAULT_SPOOL_ROOT))
    parser.add_argument("--adb", default=r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe")
    parser.add_argument("--serial")
    parser.add_argument("--server", default="283")
    parser.add_argument("--change-threshold", type=float, default=0.08)
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count must be at least 1")

    observer = ShadowObserver(
        AdbShadowFrameSource(
            adb=Path(args.adb), serial=args.serial, server=args.server
        ),
        object(),
        config=ShadowObserverConfig(
            interval=args.interval,
            change_threshold=args.change_threshold,
            server=args.server,
        ),
    )
    spool = ShadowSpool(Path(args.spool_root))
    for index in range(args.count):
        result = observer.spool_once(spool)
        print(result)
        if result["status"] == "FAIL":
            return 1
        if index + 1 < args.count:
            observer.sleeper(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
