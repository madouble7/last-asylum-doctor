"""User-driven, read-only BlueStacks screenshot capture.

Matt manually navigates to a screen, then runs this command.  The command
only detects the device, reads package metadata, and calls ``screencap``; it
has no ADB input/event operation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from probe_capture_core import (
    DEFAULT_ADB,
    DEFAULT_SERVER,
    SCREENSHOT_DIR,
    capture_frame,
)


DEFAULT_MANIFEST = SCREENSHOT_DIR / "capture_manifest.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture the current BlueStacks framebuffer after Matt manually "
            "navigates to a screen."
        )
    )
    parser.add_argument(
        "--label",
        required=True,
        help="human-readable screen label, e.g. research-lab-upgrade",
    )
    parser.add_argument(
        "--adb",
        default=str(DEFAULT_ADB),
        help="BlueStacks ADB bridge executable",
    )
    parser.add_argument(
        "--serial",
        help="device serial; auto-detects one ready device when omitted",
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help="server/account label recorded in metadata",
    )
    parser.add_argument(
        "--output-dir",
        default=str(SCREENSHOT_DIR),
        help="ignored screenshot directory",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="ignored JSONL capture manifest",
    )
    args = parser.parse_args()
    metadata = capture_frame(
        adb=Path(args.adb),
        requested_serial=args.serial,
        server=args.server,
        output_dir=Path(args.output_dir),
        label=args.label,
        manifest_path=Path(args.manifest),
    )
    print(f"Saved screenshot: {metadata['screenshot_path']}")
    print(f"SHA-256: {metadata['sha256']}")
    print(f"Manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
