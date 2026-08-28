"""Read-only BlueStacks screenshot capture and bounded OCR benchmark.

The capture command only permits device discovery, package metadata queries,
and ``exec-out screencap -p``.  It has no input/event command path.  Captures
and OCR observations are written below ignored ``data/raw/probe`` paths.

Examples:
    py -3.13 tools/probe_phase1_ui_ocr.py capture
    py -3.13 tools/probe_phase1_ui_ocr.py ocr path/to/screenshot.png
    py -3.13 tools/probe_phase1_ui_ocr.py ocr path/to/screenshot.png --crop 0,0,800,400
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR


DEFAULT_ADB = Path(r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe")
PACKAGE = "com.phs.global"
DEFAULT_SERVER = "283"
SCREENSHOT_DIR = Path("data/raw/probe/screenshots")


def run_adb(adb: Path, *args: str, serial: str | None = None) -> bytes:
    command = [str(adb)]
    if serial:
        command += ["-s", serial]
    command += list(args)
    return subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


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
    output = run_adb(adb, "shell", "dumpsys", "package", PACKAGE, serial=serial).decode(
        "utf-8", errors="replace"
    )
    version_name = re.search(r"versionName=([^\s]+)", output)
    version_code = re.search(r"versionCode=(\d+)", output)
    if not version_name or not version_code:
        raise RuntimeError("package version metadata was not found")
    return {"version_name": version_name.group(1), "version_code": version_code.group(1)}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def capture(args: argparse.Namespace) -> int:
    adb = Path(args.adb)
    serial = detect_device(adb, args.serial)
    version = package_version(adb, serial)
    if version != {"version_name": "1.0.97", "version_code": "97"}:
        raise RuntimeError(f"unexpected client version: {version}")
    png = run_adb(adb, "exec-out", "screencap", "-p", serial=serial)
    digest = sha256(png)
    captured_at = datetime.now(timezone.utc)
    stamp = captured_at.strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"{stamp}_{digest[:12]}.png"
    metadata_path = image_path.with_suffix(".json")
    image_path.write_bytes(png)
    metadata = {
        "captured_at_utc": captured_at.isoformat(),
        "device_serial": serial,
        "package": PACKAGE,
        "client_version_name": version["version_name"],
        "client_version_code": int(version["version_code"]),
        "server": args.server,
        "sha256": digest,
        "screenshot_path": str(image_path),
        "adb_operation": "exec-out screencap -p",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


def parse_crop(value: str, shape: tuple[int, ...]) -> tuple[int, int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("crop must be x,y,w,h")
    x, y, width, height = parts
    image_height, image_width = shape[:2]
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > image_width or y + height > image_height:
        raise ValueError(f"crop is outside image bounds {image_width}x{image_height}: {value}")
    return x, y, width, height


def preprocess(crop: np.ndarray) -> dict[str, np.ndarray]:
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    enlarged = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(enlarged)
    _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9
    )
    return {"gray_up2": enlarged, "clahe_up2": clahe, "otsu_up2": otsu, "adaptive_up2": adaptive}


def rapidocr_rows(engine: RapidOCR, image: np.ndarray, scale: float = 1.0) -> list[dict[str, Any]]:
    result, _ = engine(image)
    if result is None:
        return []
    rows = []
    for item in result:
        box, text, confidence = item
        rows.append(
            {
                "raw_ocr_text": str(text),
                "normalized_value": re.sub(r"\s+", " ", str(text)).strip(),
                "confidence": round(float(confidence), 6),
                "bbox_source_crop_pixels": [
                    [round(float(point[0]) / scale, 2), round(float(point[1]) / scale, 2)]
                    for point in box
                ],
            }
        )
    return rows


def ocr(args: argparse.Namespace) -> int:
    image_path = Path(args.image)
    source = image_path.read_bytes()
    image = cv2.imdecode(np.frombuffer(source, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"unable to read PNG/JPEG: {image_path}")
    crop = parse_crop(args.crop, image.shape) if args.crop else (0, 0, image.shape[1], image.shape[0])
    x, y, width, height = crop
    cropped = image[y : y + height, x : x + width]
    engine = RapidOCR()
    observations = []
    digest = sha256(source)
    for variant, prepared in preprocess(cropped).items():
        for row in rapidocr_rows(engine, prepared, scale=2.0):
            row.update(
                {
                    "source_screenshot_sha256": digest,
                    "crop_coordinates_xywh": [x, y, width, height],
                    "preprocessing_variant": variant,
                    "validation_status": "REVIEW" if args.expected is None else "FAIL",
                }
            )
            if args.expected is not None and row["normalized_value"] == args.expected:
                row["validation_status"] = "PASS"
            observations.append(row)
    report = {
        "source_screenshot": str(image_path),
        "source_screenshot_sha256": digest,
        "image_size_xy": [int(image.shape[1]), int(image.shape[0])],
        "crop_coordinates_xywh": list(crop),
        "expected_normalized_value": args.expected,
        "acceptance_rule": "PASS/FAIL only when --expected is supplied; otherwise REVIEW pending pixel comparison",
        "observations": observations,
    }
    output = Path(args.output) if args.output else image_path.with_suffix(".ocr.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--adb", default=str(DEFAULT_ADB))
    capture_parser.add_argument("--serial")
    capture_parser.add_argument("--server", default=DEFAULT_SERVER)
    capture_parser.add_argument("--output-dir", default=str(SCREENSHOT_DIR))
    capture_parser.set_defaults(function=capture)

    ocr_parser = subparsers.add_parser("ocr")
    ocr_parser.add_argument("image")
    ocr_parser.add_argument("--crop")
    ocr_parser.add_argument("--expected", help="exact normalized value for acceptance testing")
    ocr_parser.add_argument("--output")
    ocr_parser.set_defaults(function=ocr)
    args = parser.parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
