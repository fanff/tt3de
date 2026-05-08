# -*- coding: utf-8 -*-
"""
Dev-only helper: capture Textual Apps as SVG via headless run_test.

Default: one screenshot with three TT3DE demos side-by-side (see
`screenshot_apps.triple_panel:TriplePanelDemoApp`). Use `--app` for a single App
or any other module:Class / path.py:Class.

This file lives under scripts/ — it is NOT installed via the published wheel.

Example:

    uv run python scripts/dev_tt3de_screenshot.py -o artifacts/out.svg

    uv run python scripts/dev_tt3de_screenshot.py -o artifacts/single.svg \\
        --app screenshot_apps.red_triangle:TexturedCubeDemoApp
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import os
import re
import sys
import uuid
from pathlib import Path

from textual.app import App


DEFAULT_APP_REF = "screenshot_apps.triple_panel:TriplePanelDemoApp"


# JetBrains Mono webfonts are served by jsDelivr (cdnjs does not host this
# package). We pin to the @2.304 tag for reproducible documentation builds.
_JETBRAINS_FONT_FACE_BLOCKS = """\
    @font-face {
        font-family: "JetBrains Mono";
        src: local("JetBrainsMono-Regular"),
                url("https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@2.304/web/woff2/JetBrainsMono-Regular.woff2") format("woff2"),
                url("https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@2.304/web/woff/JetBrainsMono-Regular.woff") format("woff");
        font-style: normal;
        font-weight: 400;
    }
    @font-face {
        font-family: "JetBrains Mono";
        src: local("JetBrainsMono-Bold"),
                url("https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@2.304/web/woff2/JetBrainsMono-Bold.woff2") format("woff2"),
                url("https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@2.304/web/woff/JetBrainsMono-Bold.woff") format("woff");
        font-style: normal;
        font-weight: 700;
    }"""


_FIRA_FONT_FACE_RE = re.compile(
    r'@font-face\s*\{[^}]*font-family:\s*"Fira Code"[^}]*\}'
)


def swap_font_to_jetbrains_mono(svg: str) -> str:
    """
    Rewrite Rich's default Fira Code SVG font hooks to JetBrains Mono.

    Textual's ``App.export_screenshot`` does not forward Rich's ``code_format``
    or ``font_aspect_ratio`` parameters, so we post-process the SVG: replace the
    two contiguous Fira Code ``@font-face`` blocks and the matrix
    ``font-family`` declaration. If the upstream template ever changes shape,
    no replacement happens and we keep the original SVG unchanged.
    """
    matches = list(_FIRA_FONT_FACE_RE.finditer(svg))
    if not matches:
        return svg
    first = matches[0].start()
    last = matches[-1].end()
    rewritten = svg[:first] + _JETBRAINS_FONT_FACE_BLOCKS + svg[last:]
    return rewritten.replace("Fira Code, monospace", "JetBrains Mono, monospace")


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent.parent


def scripts_dir() -> Path:
    return Path(__file__).resolve().parent


def load_app_class(ref: str) -> type[App]:
    left, sep, right = ref.rpartition(":")
    left, right = left.strip(), right.strip()
    if not sep or not left or not right:
        raise SystemExit(
            f"Invalid --app {ref!r}; expected MODULE_OR_PATH:CLASS (use rpartition-safe paths)."
        )

    candidate = Path(left)
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()

    if candidate.suffix == ".py" and candidate.is_file():
        mod_name = f"_tt3de_scr_{uuid.uuid4().hex}"
        spec = importlib.util.spec_from_file_location(mod_name, candidate)
        if spec is None or spec.loader is None:
            raise SystemExit(f"Could not load app module from {candidate}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    else:
        try:
            mod = importlib.import_module(left)
        except ModuleNotFoundError as e:
            raise SystemExit(
                f"Could not import module {left!r} (cwd={Path.cwd()}). {e}"
            ) from e

    try:
        obj = getattr(mod, right)
    except AttributeError as e:
        raise SystemExit(
            f"No attribute {right!r} in module loaded from {ref!r}."
        ) from e

    if not isinstance(obj, type):
        raise SystemExit(f"{ref!r} does not resolve to a class.")

    if not issubclass(obj, App):
        raise SystemExit(
            f"{ref!r} resolves to {obj!r}, which is not a subclass of textual.app.App."
        )

    return obj


async def capture_screenshot_svg(
    AppClass: type[App],
    width: int,
    height: int,
    *,
    delay: float,
    screenshot_title: str,
) -> str:
    app = AppClass()
    if hasattr(app, "_disable_tooltips"):
        app._disable_tooltips = True

    async with app.run_test(size=(width, height), tooltips=False) as pilot:
        await pilot.pause()
        await pilot.pause()
        await pilot.pause(0.05)
        if delay > 0:
            await asyncio.sleep(delay)
        svg = app.export_screenshot(title=screenshot_title)
        return swap_font_to_jetbrains_mono(svg)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Headless Textual screenshot of a TT3DE / Textual App (SVG). Dev-only tool."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="SVG output path.",
    )
    parser.add_argument(
        "--app",
        type=str,
        default=DEFAULT_APP_REF,
        help=(
            "Textual App as MODULE:Class or path/to/file.py:Class "
            f"(default: {DEFAULT_APP_REF})."
        ),
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait after paint stabilization before export (default: 0).",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="tt3de_dev_screenshot",
        help="Title passed to export_screenshot (default: tt3de_dev_screenshot).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=200,
        help="Synthetic terminal width (cols); default 200 fits the triptych default app.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=56,
        help="Synthetic terminal height (rows) for Textual snapshot.",
    )
    parser.add_argument(
        "--chdir",
        type=Path,
        default=None,
        help="Optional working directory (defaults to tt3de repo root).",
    )

    ns = parser.parse_args(argv)

    cwd = Path(ns.chdir).resolve() if ns.chdir else repo_root_from_script()
    if not cwd.is_dir():
        raise SystemExit(f"--chdir is not a directory: {cwd}")

    # Force Rich/Textual to always render with 24-bit color regardless of
    # how this script is invoked (direct, subprocess, CI, etc.).
    os.environ["COLORTERM"] = "truecolor"
    os.environ.pop("NO_COLOR", None)

    scripts_insert = str(scripts_dir())
    prev_cwd = Path.cwd()
    try:
        sys.path.insert(0, scripts_insert)
        os.chdir(cwd)
        AppClass = load_app_class(ns.app)
        svg = asyncio.run(
            capture_screenshot_svg(
                AppClass,
                ns.width,
                ns.height,
                delay=ns.delay,
                screenshot_title=ns.title,
            )
        )
    finally:
        try:
            sys.path.remove(scripts_insert)
        except ValueError:
            pass
        os.chdir(prev_cwd)

    Path(ns.output).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.output).write_text(svg, encoding="utf-8")
    print(f"wrote SVG ({len(svg)} bytes): {Path(ns.output).resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
