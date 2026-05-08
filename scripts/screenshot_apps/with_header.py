# -*- coding: utf-8 -*-

from textual.app import App, ComposeResult
from textual.widgets import Header

from screenshot_apps.red_triangle import RedTriangleView


class RedTriangleHeaderDemoApp(App):
    """Same scene as red triangle with Textual chrome (Header)."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield RedTriangleView(target_fps=0)
