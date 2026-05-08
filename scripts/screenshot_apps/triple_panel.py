# -*- coding: utf-8 -*-
"""Single Textual `App` that lays out three titled, bordered TT3DE columns (doc smoke
screenshot)."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Label

from screenshot_apps.multi_triangle import MultiTriangleScene
from screenshot_apps.red_triangle import RedTriangleView


class TriplePanelDemoApp(App):
    """
    Three columns: red, blue, green chrome (border + title) around distinct TT3D views
    so the triptych layout is obvious at a glance.
    """

    DEFAULT_CSS = """
    TriplePanelDemoApp {
        width: 100%;
        height: 100%;
    }

    TriplePanelDemoApp Horizontal#main_row {
        width: 100%;
        height: 100%;
        padding: 0 1;
    }

    Vertical.panel {
        width: 1fr;
        height: 100%;
        min-width: 0;
    }

    Label.panel-title {
        width: 100%;
        height: 3;
        text-align: center;
        text-style: bold;
        border-bottom: solid;
    }

    Container.panel-frame {
        width: 100%;
        height: 1fr;
        min-height: 0;
        padding: 0 1;
    }

    Vertical.panel-red {
        border: tall $error;
        background: $error 8%;
    }
    Vertical.panel-red Label.panel-title {
        border-bottom: solid $error;
        background: $error 15%;
    }

    Vertical.panel-blue {
        border: tall $primary;
        background: $primary 8%;
    }
    Vertical.panel-blue Label.panel-title {
        border-bottom: solid $primary;
        background: $primary 15%;
    }

    Vertical.panel-green {
        border: tall $success;
        background: $success 8%;
    }
    Vertical.panel-green Label.panel-title {
        border-bottom: solid $success;
        background: $success 15%;
    }

    Container.panel-frame Header {
        height: auto;
        min-height: 1;
    }
    Container.panel-frame RedTriangleView {
        height: 1fr;
        min-height: 0;
    }
    Container.panel-frame MultiTriangleScene {
        height: 1fr;
        min-height: 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="main_row"):
            with Vertical(classes="panel panel-red"):
                yield Label("[red] minimal triangle — one mesh", classes="panel-title")
                with Container(classes="panel-frame"):
                    yield RedTriangleView(target_fps=0, id="triple_col_minimal")

            with Vertical(classes="panel panel-blue"):
                yield Label(
                    "[blue] multi-triangle RGB scene",
                    classes="panel-title",
                )
                with Container(classes="panel-frame"):
                    yield MultiTriangleScene(target_fps=0, id="triple_col_multi")

            with Vertical(classes="panel panel-green"):
                yield Label(
                    "[green] header + triangle (chrome)",
                    classes="panel-title",
                )
                with Container(classes="panel-frame"):
                    yield Header()
                    yield RedTriangleView(
                        target_fps=0, id="triple_col_with_header_view"
                    )
