from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest


TOOLS_DIR = Path(__file__).parents[1] / "tools"


def test_capture_entrypoint_imports_without_ocr_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(TOOLS_DIR))
    for module in ("cv2", "numpy", "onnxruntime", "rapidocr_onnxruntime"):
        monkeypatch.setitem(sys.modules, module, None)

    namespace = runpy.run_path(
        str(TOOLS_DIR / "probe_capture.py"),
        run_name="probe_capture_import_test",
    )

    assert namespace["DEFAULT_MANIFEST"].name == "capture_manifest.jsonl"
    assert callable(namespace["capture_frame"])


def test_safe_label_is_bounded_and_filename_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(TOOLS_DIR))
    from probe_capture_core import safe_label

    assert safe_label("  T9 locked / requirements  ") == "T9-locked-requirements"
    assert len(safe_label("x" * 100)) == 80
    with pytest.raises(ValueError):
        safe_label(" / ")
