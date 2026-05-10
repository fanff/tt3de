# -*- coding: utf-8 -*-
"""Launch any demo under ``demos/2d/`` or ``demos/3d/`` from a Textual menu.

Demos are listed in **two side-by-side panels** (``demos/2d`` and ``demos/3d``). Select
with Enter (Tab moves between panels). Escape returns from a running demo. A rolling
median FPS overlay (last 50 samples) is shown while a demo runs.

Run from the repository root (``models/`` and other assets are cwd-relative):

    uv run python demos/all.py

The launcher changes the process working directory to the repo root on startup
so asset paths resolve.
"""

from __future__ import annotations

import importlib.util
import inspect
import os
import statistics
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Literal

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, OptionList, Rule, Static
from textual.widgets.option_list import Option

from tt3de.textual_standalone import TT3DViewStandAlone


REPO_ROOT = Path(__file__).resolve().parents[1]


def discover_demo_paths(repo_root: Path) -> list[tuple[Literal["2d", "3d"], Path]]:
    """Return sorted ``(category, path)`` pairs for each ``demos/{2d,3d}/*.py``."""
    out: list[tuple[Literal["2d", "3d"], Path]] = []
    for sub in ("2d", "3d"):
        d = repo_root / "demos" / sub
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.py")):
            out.append((sub, p.resolve()))
    return out


def load_demo_module(category: str, path: Path):
    """Load a demo file as a module (no ``demos`` package required)."""
    module_name = f"tt3de_demo_launcher.{category}.{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_standalone_view_class(
    module,
) -> tuple[type[TT3DViewStandAlone] | None, str | None]:
    """Find exactly one concrete ``TT3DViewStandAlone`` subclass defined in *module*."""
    candidates: list[type[TT3DViewStandAlone]] = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        if not issubclass(obj, TT3DViewStandAlone) or obj is TT3DViewStandAlone:
            continue
        if inspect.isabstract(obj):
            continue
        candidates.append(obj)
    if len(candidates) == 1:
        return candidates[0], None
    if len(candidates) == 0:
        return None, "No TT3DViewStandAlone subclass found in module."
    names = ", ".join(sorted(c.__name__ for c in candidates))
    return None, f"Multiple viewer classes ({names}); expected exactly one."


@dataclass(frozen=True)
class DemoEntry:
    category: Literal["2d", "3d"]
    path: Path
    label: str
    view_cls: type[TT3DViewStandAlone] | None
    load_error: str | None


def analyze_demo(category: Literal["2d", "3d"], path: Path) -> DemoEntry:
    label = f"{category}/{path.name}"
    try:
        mod = load_demo_module(category, path)
        cls, err = find_standalone_view_class(mod)
        if err:
            return DemoEntry(category, path, label, None, err)
        return DemoEntry(category, path, label, cls, None)
    except Exception as exc:  # noqa: BLE001 — surface loader failures in the UI
        return DemoEntry(category, path, label, None, str(exc))


def build_demo_entries(repo_root: Path) -> list[DemoEntry]:
    return [
        analyze_demo(cat, p) for cat, p in discover_demo_paths(repo_root)
    ]


class DemoRunnerPane(Container):
    """Hosts the engine widget with an FPS overlay (median over last 50 samples)."""

    DEFAULT_CSS = """
    DemoRunnerPane {
        height: 1fr;
        width: 100%;
        layers: base overlay;
    }

    #demo-slot {
        layer: base;
        width: 100%;
        height: 100%;
    }

    #fps-row {
        layer: overlay;
        dock: top;
        height: auto;
        width: 100%;
    }
    #fps-row-spacer {
        width: 1fr;
    }
    #fps-overlay {
        width: auto;
        height: auto;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self, entry: DemoEntry) -> None:
        super().__init__()
        self._entry = entry
        self._fps_samples: deque[float] = deque(maxlen=50)
        self._last_frame_idx: int = 0
        self._last_sample_t: float = perf_counter()
        self._primed: bool = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="fps-row"):
            yield Static("", id="fps-row-spacer")
            yield Static("…", id="fps-overlay", markup=False)
        yield Container(id="demo-slot")

    async def on_mount(self) -> None:
        assert self._entry.view_cls is not None
        demo = self._entry.view_cls()
        slot = self.query_one("#demo-slot")
        await slot.mount(demo)
        demo.focus()
        self._last_frame_idx = demo.frame_idx
        self._last_sample_t = perf_counter()
        self._primed = True
        self.set_interval(1 / 120.0, self._tick_fps)

    def _tick_fps(self) -> None:
        if not self._primed:
            return
        try:
            demo = self.query_one(TT3DViewStandAlone)
        except Exception:
            return
        overlay = self.query_one("#fps-overlay", Static)
        idx = demo.frame_idx
        now = perf_counter()
        if idx > self._last_frame_idx:
            dt = now - self._last_sample_t
            if dt > 1e-9:
                delta = idx - self._last_frame_idx
                self._fps_samples.append(delta / dt)
            self._last_frame_idx = idx
            self._last_sample_t = now
        w, h = demo.size.width, demo.size.height
        render_ms = demo.frame_timings.render_duration * 1000.0
        if self._fps_samples:
            fps_median = statistics.median(self._fps_samples)
            overlay.update(
                f"{w}x{h}  FPS: {fps_median:.1f}  r: {render_ms:.2f} ms"
            )
        else:
            overlay.update(f"{w}x{h}  FPS: …  r: {render_ms:.2f} ms")


class DemoRunScreen(Screen):
    """Fullscreen demo with Escape to return to the menu."""

    BINDINGS = [
        Binding("escape", "back", "Menu", priority=True),
    ]

    def __init__(self, entry: DemoEntry) -> None:
        super().__init__()
        self._entry = entry

    def compose(self) -> ComposeResult:
        yield Header()
        yield DemoRunnerPane(self._entry)

    def on_mount(self) -> None:
        self.app.title = "TT3DE Demo Launcher"
        self.app.sub_title = self._entry.label

    def action_back(self) -> None:
        self.app.pop_screen()
        self.app.sub_title = ""


class DemoMenuScreen(Screen):
    """Pick a demo from ``demos/2d`` and ``demos/3d`` (two styled columns)."""

    DEFAULT_CSS = """
    #menu-column {
        height: 100%;
    }
    #hint-line {
        margin: 0 0 1 0;
        color: $text-muted;
    }
    #demo-panels {
        height: 1fr;
        min-height: 10;
    }
    .demo-panel {
        width: 1fr;
        height: 100%;
        padding: 1 2;
        background: $boost;
        border: round $panel;
    }
    .demo-panel.panel-2d {
        margin-right: 1;
        border: round $accent;
    }
    .demo-panel.panel-3d {
        margin-left: 1;
        border: round $primary;
    }
    .panel-title {
        text-style: bold;
        margin-bottom: 0;
    }
    .demo-panel.panel-2d .panel-title {
        color: $accent;
    }
    .demo-panel.panel-3d .panel-title {
        color: $primary;
    }
    .panel-path {
        color: $text-muted;
        margin-top: 0;
        margin-bottom: 1;
    }
    .panel-rule {
        margin: 0 0 1 0;
        color: $border;
    }
    #demo-options-2d, #demo-options-3d {
        height: 1fr;
        min-height: 6;
        border: none;
        background: transparent;
    }
    """

    def __init__(self, entries: list[DemoEntry]) -> None:
        super().__init__()
        self._entries_2d = [e for e in entries if e.category == "2d"]
        self._entries_3d = [e for e in entries if e.category == "3d"]

    @staticmethod
    def _options_for(entries: list[DemoEntry]) -> list[Option]:
        return [
            Option(
                (
                    f"[dim]{e.label}[/] — {e.load_error}"
                    if e.view_cls is None
                    else e.label
                ),
                id=str(i),
                disabled=e.view_cls is None,
            )
            for i, e in enumerate(entries)
        ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu-column"):
            yield Static(
                "Enter runs the highlighted demo · Tab switches panel · Escape exits a demo · Ctrl+Q quits",
                id="hint-line",
                markup=False,
            )
            with Horizontal(id="demo-panels"):
                with Vertical(classes="demo-panel panel-2d"):
                    yield Static("2D", classes="panel-title", markup=False)
                    yield Static(
                        f"demos/2d · {len(self._entries_2d)} files",
                        classes="panel-path",
                        markup=False,
                    )
                    yield Rule(line_style="heavy", classes="panel-rule")
                    yield OptionList(
                        *self._options_for(self._entries_2d),
                        id="demo-options-2d",
                    )
                with Vertical(classes="demo-panel panel-3d"):
                    yield Static("3D", classes="panel-title", markup=False)
                    yield Static(
                        f"demos/3d · {len(self._entries_3d)} files",
                        classes="panel-path",
                        markup=False,
                    )
                    yield Rule(line_style="heavy", classes="panel-rule")
                    yield OptionList(
                        *self._options_for(self._entries_3d),
                        id="demo-options-3d",
                    )

    def on_mount(self) -> None:
        self.app.title = "TT3DE Demo Launcher"
        self.app.sub_title = ""
        if self._entries_2d:
            self.query_one("#demo-options-2d", OptionList).focus()
        elif self._entries_3d:
            self.query_one("#demo-options-3d", OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        ol = event.option_list
        if ol.id == "demo-options-2d":
            entries = self._entries_2d
        elif ol.id == "demo-options-3d":
            entries = self._entries_3d
        else:
            return
        entry = entries[event.option_index]
        if entry.view_cls is None:
            self.app.notify(
                entry.load_error or "Demo unavailable",
                title="Cannot load demo",
                severity="error",
                timeout=8,
            )
            return
        self.app.push_screen(DemoRunScreen(entry))


class DemoLauncherApp(App):
    """Textual app: demo menu + stacked run screens."""

    TITLE = "TT3DE Demo Launcher"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(self, entries: list[DemoEntry]) -> None:
        super().__init__()
        self._entries = entries

    def on_mount(self) -> None:
        os.chdir(REPO_ROOT)
        self.push_screen(DemoMenuScreen(self._entries))


def main() -> None:
    entries = build_demo_entries(REPO_ROOT)
    app = DemoLauncherApp(entries)
    app._disable_tooltips = True
    app.run()


if __name__ == "__main__":
    main()
