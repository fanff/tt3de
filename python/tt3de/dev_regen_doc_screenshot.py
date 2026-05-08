# -*- coding: utf-8 -*-
"""
Regenerate the Sphinx static triptych SVG (development; run from repository root only).

Note: ``uv run tt3de-regen-doc-screenshot`` may reinstall the editable package before
launch. Prefer ``uv run --no-sync python scripts/dev_tt3de_screenshot.py ...``,
``make regen-doc-screenshot``, or ``scripts/regen_doc_screenshot.{ps1,sh}`` for faster iteration.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DEFAULT_REL_OUT = Path("source") / "_static" / "screenshots" / "triple_panel.svg"


def main() -> None:
    cwd = Path.cwd()
    if not (cwd / "source" / "conf.py").is_file():
        raise SystemExit(
            "tt3de-regen-doc-screenshot: run from the tt3de repository root (expected source/conf.py)."
        )

    script = cwd / "scripts" / "dev_tt3de_screenshot.py"
    if not script.is_file():
        raise SystemExit(f"tt3de-regen-doc-screenshot: missing {script}.")

    out = cwd / DEFAULT_REL_OUT
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(script),
        "-o",
        str(out),
        "--width",
        "132",
        "--height",
        "28",
    ]
    subprocess.run(cmd, check=True, cwd=str(cwd))
    print(f"wrote {out}")
