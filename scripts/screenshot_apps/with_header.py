# -*- coding: utf-8 -*-

from textual.app import App, ComposeResult
from textual.widgets import Header

from screenshot_apps.red_triangle import TexturedCubeView


class CubeHeaderDemoApp(App):
    """Textured cube scene with Textual chrome (Header)."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield TexturedCubeView(target_fps=0)
