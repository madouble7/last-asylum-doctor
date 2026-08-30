"""Process a bounded batch from the local Shadow Observer filesystem spool."""

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
    DEFAULT_SPOOL_ROOT,
    ObservationStore,
    ShadowObserverConfig,
    ShadowSpool,
    ShadowSpoolError,
    ShadowSpoolWorker,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Process a bounded batch from the Shadow Observer spool."
    )
    parser.add_argument("--spool-root", default=str(DEFAULT_SPOOL_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--evidence-dir", default=str(DEFAULT_EVIDENCE_DIR))
    parser.add_argument("--max-captures", type=int, default=100)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--server", default="283")
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be at least 1")

    spool = ShadowSpool(Path(args.spool_root))
    worker = ShadowSpoolWorker(
        spool,
        store_factory=lambda: ObservationStore(
            Path(args.output),
            Path(args.evidence_dir),
            max_captures=args.max_captures,
        ),
        config=ShadowObserverConfig(
            max_captures=args.max_captures,
            server=args.server,
        ),
        ocr_perceiver=RapidOcrPerceiver(),
    )
    try:
        result = worker.process_pending(args.limit)
    except ShadowSpoolError as error:
        print(f"Shadow Spool worker refused: {error}", file=sys.stderr)
        return 2
    print(result)
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
