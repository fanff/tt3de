# -*- coding: utf-8 -*-
"""
Single Textual `App` that lays out two titled TT3DE columns (doc smoke screenshot).

Regenerate the SVG with ``make regen-doc-screenshot`` or
``bash scripts/regen_doc_screenshot.sh`` (see ``scripts/README.md``).
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label

from screenshot_apps.city_scene import CityBlockScene
from screenshot_apps.multi_triangle import TaxiModelScene


class DualPanelDemoApp(App):
    """Two-column layout; each column uses a dark tint and a matching title bar."""

    TITLE = "TT3DE doc dual panel"

    DEFAULT_CSS = """
    DualPanelDemoApp {
        width: 100%;
        height: 100%;
        background: $surface;
    }

    DualPanelDemoApp Screen {
        background: $surface;
    }

    #outer {
        width: 100%;
        height: 100%;
        padding: 0;
    }

    #main_row {
        width: 100%;
        height: 1fr;
        min-height: 0;
    }

    .col {
        width: 1fr;
        height: 100%;
        min-width: 0;
    }

    .title {
        width: 100%;
        height: 3;
        text-align: center;
        text-style: bold;
        border-bottom: solid;
    }

    .box {
        width: 100%;
        height: 1fr;
        min-height: 0;
        padding: 0 1;
    }

    .col-blue {
        background: $primary 8%;
    }
    .col-blue .title {
        border-bottom: solid $primary;
        background: $primary 15%;
    }

    .col-green {
        background: $success 8%;
    }
    .col-green .title {
        border-bottom: solid $success;
        background: $success 15%;
    }

    .box TaxiModelScene,
    .box CityBlockScene {
        height: 1fr;
        min-height: 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="outer"):
            with Horizontal(id="main_row"):
                with Vertical(classes="col col-blue"):
                    yield Label(
                        "[blue] taxi car — 3D model",
                        classes="title",
                    )
                    with Container(classes="box"):
                        yield TaxiModelScene(target_fps=0, id="col_taxi")

                with Vertical(classes="col col-green"):
                    yield Label(
                        "[green] city block — top-down view",
                        classes="title",
                    )
                    with Container(classes="box"):
                        yield CityBlockScene(
                            target_fps=0,
                            id="col_city",
                            vertex_buffer_size=8192,
                        )
