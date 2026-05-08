# -*- coding: utf-8 -*-
"""
Generate the two high-level API documentation screenshots.

Invokes ``dev_tt3de_screenshot.py`` once per example, writing SVG files into
``source/_static/screenshots/``.  Designed to run in CI (docbuild) and locally.

Usage (from repo root, after ``maturin develop``)::

    uv run --no-sync python scripts/gen_doc_example_screenshots.py

Pass ``--png`` to also produce PNG siblings (requires ``cairosvg``).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCREENSHOTS = [
    {
        "app": "screenshot_apps.primitives_2d:Primitives2DDemoApp",
        "output": "source/_static/screenshots/primitives_2d.svg",
        "width": "120",
        "height": "40",
        "title": "2D Primitives",
    },
    {
        "app": "screenshot_apps.primitives_3d:Primitives3DDemoApp",
        "output": "source/_static/screenshots/primitives_3d.svg",
        "width": "120",
        "height": "40",
        "title": "3D Primitives",
    },
]


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    script = repo_root / "scripts" / "dev_tt3de_screenshot.py"

    if not script.is_file():
        print(f"ERROR: missing {script}", file=sys.stderr)
        return 1

    extra_args: list[str] = []
    if "--png" in sys.argv[1:]:
        extra_args.append("--png")

    for entry in SCREENSHOTS:
        out = repo_root / entry["output"]
        out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(script),
            "-o",
            str(out),
            "--app",
            entry["app"],
            "--width",
            entry["width"],
            "--height",
            entry["height"],
            "--title",
            entry["title"],
            *extra_args,
        ]
        print(f">>> {' '.join(cmd)}")
        subprocess.run(cmd, check=True, cwd=str(repo_root))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
