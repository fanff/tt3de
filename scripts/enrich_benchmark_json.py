#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-process pytest-benchmark JSON: add explicit timestamp fields.

pytest-benchmark already writes a top-level ``datetime`` (ISO-8601). This script
adds:

- ``timestamp``: same instant as ``datetime`` (explicit alias for readers)
- ``timestamp_unix``: UTC seconds since epoch (float)

Usage::

    python scripts/enrich_benchmark_json.py benchmarks/to_textual.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _parse_iso_datetime(value: str) -> datetime:
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def enrich(data: dict[str, Any]) -> dict[str, Any]:
    dt_raw = data.get("datetime")
    if isinstance(dt_raw, str) and dt_raw:
        try:
            dt = _parse_iso_datetime(dt_raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            data["timestamp"] = dt_raw
            data["timestamp_unix"] = dt.timestamp()
            return data
        except ValueError:
            pass

    now = datetime.now(timezone.utc)
    iso = now.isoformat()
    data["datetime"] = iso
    data["timestamp"] = iso
    data["timestamp_unix"] = now.timestamp()
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to pytest-benchmark --benchmark-json output",
    )
    args = parser.parse_args()
    path: Path = args.json_path
    if not path.is_file():
        print(f"enrich_benchmark_json: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    payload = json.loads(path.read_text(encoding="utf-8"))
    enrich(payload)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
