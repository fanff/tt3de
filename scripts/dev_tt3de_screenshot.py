# -*- coding: utf-8 -*-
"""
Dev-only helper: capture Textual Apps as SVG via headless run_test.

Default: one screenshot with three TT3DE demos side-by-side (see
`screenshot_apps.triple_panel:TriplePanelDemoApp`). Use `--app` for a single App
or any other module:Class / path.py:Class.

Pass ``--png`` to also convert the SVG to a PNG sibling file (requires
``cairosvg``).  The PNG path is derived from ``--output`` by replacing the
extension; override with ``--png-output``.

This file lives under scripts/ — it is NOT installed via the published wheel.

Example:

    uv run python scripts/dev_tt3de_screenshot.py -o artifacts/out.svg

    uv run python scripts/dev_tt3de_screenshot.py -o artifacts/out.svg --png

    uv run python scripts/dev_tt3de_screenshot.py -o artifacts/single.svg \\
        --app screenshot_apps.red_triangle:TexturedCubeDemoApp
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import os
import sys
import uuid
from pathlib import Path

from textual.app import App


DEFAULT_APP_REF = "screenshot_apps.triple_panel:TriplePanelDemoApp"


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
        return app.export_screenshot(title=screenshot_title)


def svg_to_png(svg_text: str, png_path: Path, *, scale: float = 2.0) -> None:
    """Convert an SVG string to a PNG file using *cairosvg*."""
    try:
        import cairosvg
    except ImportError as exc:
        raise SystemExit(
            "cairosvg is required for --png conversion. "
            "Install it with: uv pip install cairosvg"
        ) from exc

    png_path.parent.mkdir(parents=True, exist_ok=True)
    png_bytes = cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), scale=scale)
    png_path.write_bytes(png_bytes)
    print(f"wrote PNG ({len(png_bytes)} bytes, scale={scale}): {png_path.resolve()}")


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
    parser.add_argument(
        "--png",
        action="store_true",
        default=False,
        help="Also convert the SVG to PNG (requires cairosvg).",
    )
    parser.add_argument(
        "--png-output",
        type=Path,
        default=None,
        help="PNG output path (defaults to --output with .png extension). Implies --png.",
    )
    parser.add_argument(
        "--png-scale",
        type=float,
        default=2.0,
        help="Scale factor for the PNG rasterization (default: 2.0 for retina-quality).",
    )

    ns = parser.parse_args(argv)
    if ns.png_output is not None:
        ns.png = True

    cwd = Path(ns.chdir).resolve() if ns.chdir else repo_root_from_script()
    if not cwd.is_dir():
        raise SystemExit(f"--chdir is not a directory: {cwd}")

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

    if ns.png:
        png_path = (
            Path(ns.png_output)
            if ns.png_output
            else Path(ns.output).with_suffix(".png")
        )
        svg_to_png(svg, png_path, scale=ns.png_scale)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
