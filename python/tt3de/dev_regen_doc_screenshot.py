# -*- coding: utf-8 -*-
"""
Regenerate the Sphinx static triptych SVG (development; run from repository root only).

Prefer ``make regen-doc-screenshot``, ``bash scripts/regen_doc_screenshot.sh``, or
``powershell -ExecutionPolicy Bypass -File scripts/regen_doc_screenshot.ps1``.

Optional Python entry (sets ``COLORTERM`` for export)::

    uv run --no-sync python python/tt3de/dev_regen_doc_screenshot.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

DEFAULT_REL_OUT = Path("source") / "_static" / "screenshots" / "triple_panel.svg"


def main() -> None:
    cwd = Path.cwd()
    if not (cwd / "source" / "conf.py").is_file():
        raise SystemExit(
            "dev_regen_doc_screenshot: run from the tt3de repository root (expected source/conf.py)."
        )

    script = cwd / "scripts" / "dev_tt3de_screenshot.py"
    if not script.is_file():
        raise SystemExit(f"dev_regen_doc_screenshot: missing {script}.")

    out = cwd / DEFAULT_REL_OUT
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(script),
        "-o",
        str(out),
        "--width",
        "200",
        "--height",
        "56",
    ]
    env = os.environ.copy()
    env["COLORTERM"] = "truecolor"
    env.pop("NO_COLOR", None)
    subprocess.run(cmd, check=True, cwd=str(cwd), env=env)
    print(f"wrote {out}")
