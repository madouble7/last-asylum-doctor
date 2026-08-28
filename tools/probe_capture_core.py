"""Lightweight, read-only ADB framebuffer capture primitives.

This module intentionally uses only the Python standard library.  In
particular, capture-only callers must not need OpenCV, NumPy, ONNX Runtime, or
RapidOCR installed.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ADB = Path(r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe")
PACKAGE = "com.phs.global"
DEFAULT_SERVER = "283"
SCREENSHOT_DIR = Path("data/raw/probe/screenshots")
EXPECTED_CLIENT_VERSION = {"version_name": "1.0.97", "version_code": "97"}


def run_adb(adb: Path, *args: str, serial: str | None = None) -> bytes:
    command = [str(adb)]
    if serial:
        command += ["-s", serial]
    command += list(args)
    return subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def detect_device(adb: Path, requested_serial: str | None = None) -> str:
    output = run_adb(adb, "devices", "-l").decode("utf-8", errors="replace")
    devices = []
    for line in output.splitlines():
        match = re.match(r"^(\S+)\s+(device)\b", line.strip())
        if match:
            devices.append(match.group(1))
    if requested_serial:
        if requested_serial not in devices:
            raise RuntimeError(f"requested device is not ready: {requested_serial}")
        return requested_serial
    if len(devices) != 1:
        raise RuntimeError(f"expected exactly one ready device, found: {devices}")
    return devices[0]


def package_version(adb: Path, serial: str) -> dict[str, str]:
    output = run_adb(
        adb,
        "shell",
        "dumpsys",
        "package",
        PACKAGE,
        serial=serial,
    ).decode("utf-8", errors="replace")
    version_name = re.search(r"versionName=([^\s]+)", output)
    version_code = re.search(r"versionCode=(\d+)", output)
    if not version_name or not version_code:
        raise RuntimeError("package version metadata was not found")
    return {
        "version_name": version_name.group(1),
        "version_code": version_code.group(1),
    }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_label(label: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", label.strip()).strip("-._")
    if not cleaned:
        raise ValueError("label must contain at least one filename-safe character")
    return cleaned[:80]


def capture_frame(
    adb: Path,
    requested_serial: str | None,
    server: str,
    output_dir: Path,
    label: str | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    serial = detect_device(adb, requested_serial)
    version = package_version(adb, serial)
    if version != EXPECTED_CLIENT_VERSION:
        raise RuntimeError(f"unexpected client version: {version}")
    png = run_adb(adb, "exec-out", "screencap", "-p", serial=serial)
    digest = sha256(png)
    captured_at = datetime.now(timezone.utc)
    stamp = captured_at.strftime("%Y%m%dT%H%M%SZ")
    output_dir.mkdir(parents=True, exist_ok=True)
    label_prefix = f"{safe_label(label)}_" if label is not None else ""
    image_path = output_dir / f"{stamp}_{label_prefix}{digest[:12]}.png"
    metadata_path = image_path.with_suffix(".json")
    image_path.write_bytes(png)
    metadata = {
        "captured_at_utc": captured_at.isoformat(),
        "device_serial": serial,
        "package": PACKAGE,
        "client_version_name": version["version_name"],
        "client_version_code": int(version["version_code"]),
        "server": server,
        "sha256": digest,
        "screenshot_path": str(image_path),
        "adb_operation": "exec-out screencap -p",
    }
    if label is not None:
        metadata["label"] = label
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("a", encoding="utf-8", newline="\n") as manifest:
            manifest.write(json.dumps(metadata, ensure_ascii=True) + "\n")
    return metadata
