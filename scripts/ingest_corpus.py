#!/usr/bin/env python
"""Ingest the corpus into pgvector."""

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.ingestion.pipeline import ingest_files  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def collect(source: str) -> list[Path]:
    data = ROOT / "data" / "raw"
    if source == "all":
        paths = list(data.rglob("*.html"))
    elif source == "nice":
        paths = list((data / "nice").glob("*.html"))
    elif source == "medlineplus":
        paths = list((data / "medlineplus").glob("*.html"))
    else:
        raise SystemExit(f"unknown source: {source}")
    return sorted(paths)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="all",
                    choices=["all", "nice", "medlineplus"])
    ap.add_argument("--path", type=Path, default=None)
    args = ap.parse_args()

    paths = [args.path] if args.path else collect(args.source)
    if not paths:
        raise SystemExit("no files found")

    print(f"Ingesting {len(paths)} files...")
    stats = ingest_files(paths)
    print("\nDone.")
    print(f"  Files processed: {stats['files']}")
    print(f"  Sections:        {stats['sections']}")
    print(f"  Chunks inserted: {stats['chunks']}")
    print(f"  Skipped:         {stats['skipped']}")


if __name__ == "__main__":
    main()
