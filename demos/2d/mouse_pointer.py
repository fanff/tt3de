# -*- coding: utf-8 -*-
"""
2D mouse-pointer sprite from the bundled raster font sheet.

Tracks the real mouse with ``mouse_pointer`` (hotspot at the top-left of the
tile). Left-click toggles ``cross`` (hotspot at the center; usable as a
crosshair). Glyph textures and ``ShaderPy`` materials come from ``RasterFont``.

Run:
    uv run python demos/2d/mouse_pointer.py
"""

from pathlib import Path

from pyglm import glm
from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Header

from tt3de.glm_camera import ViewportScaleMode
from tt3de.raster_font import RasterFont
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py  # type: ignore[reportMissingImports]
from tt3de.tt_2dnodes import TT2DNode, TT2DUnitSquare

POINTER_NAME = "mouse_pointer"
CROSS_NAME = "cross"
POINTER_SIZE = 1.0


class MousePointerView(TT3DViewStandAlone):
    def initialize(self) -> None:
        # Cleared depth samples use material_id=0; keep slot 0 a static fill.
        self.rc.material_buffer.add_static(
            (0, 0, 0), (0, 0, 0), find_glyph_indices_py(" ")
        )
        font_path = (
            Path(__file__).resolve().parents[2]
            / "models"
            / "fonts"
            / "default_32px.png"
        )
        self.font = RasterFont.load(
            self.rc.texture_buffer,
            self.rc.material_buffer,
            font_path,
        )

        self.camera.set_zoom_2D(0.12)
        self.camera.set_viewport_scale_mode(ViewportScaleMode.FILL)

        self._pointer_name = POINTER_NAME
        self._cursor_world = glm.vec3(0.0, 0.0, 0.0)

        self.root2Dnode = TT2DNode()
        self.pointer = TT2DUnitSquare(
            material_id=self.font.material_named(self._pointer_name),
        )
        self.pointer.transparent = True
        self.pointer.scale = glm.vec2(POINTER_SIZE, POINTER_SIZE)
        self.root2Dnode.add_child(self.pointer)
        self.rc.append_root(self.root2Dnode)
        self._place_pointer()

    def on_mount(self) -> None:
        super().on_mount()
        # Keep receiving moves if the pointer leaves the widget briefly.
        self.capture_mouse()

    def update_step(self, delta_time: float) -> None:
        self._place_pointer()

    def post_render_step(self) -> None:
        pass

    async def on_event(self, event: events.Event) -> None:
        await super().on_event(event)
        if isinstance(event, events.MouseMove):
            self._cursor_world = self._screen_to_world(float(event.x), float(event.y))
            self._place_pointer()
        elif isinstance(event, events.Click) and event.button == 1:
            self._toggle_pointer()

    def _toggle_pointer(self) -> None:
        self._pointer_name = (
            CROSS_NAME if self._pointer_name == POINTER_NAME else POINTER_NAME
        )
        self.pointer.set_material_id(self.font.material_named(self._pointer_name))
        self._place_pointer()

    def _hotspot_local(self) -> glm.vec2:
        # Unit square is Y-up: (0, 1) is the top-left corner of the quad.
        if self._pointer_name == CROSS_NAME:
            return glm.vec2(0.5, 0.5)
        return glm.vec2(0.0, 1.0)

    def _place_pointer(self) -> None:
        hot = self._hotspot_local()
        scale = self.pointer.scale
        self.pointer.position = glm.vec3(
            self._cursor_world.x - hot.x * scale.x,
            self._cursor_world.y - hot.y * scale.y,
            0.0,
        )

    def _screen_to_world(self, x: float, y: float) -> glm.vec3:
        width = max(self.size.width, 1)
        height = max(self.size.height, 1)
        clip = glm.vec4(
            x / width * 2.0 - 1.0,
            1.0 - y / height * 2.0,
            0.0,
            1.0,
        )
        world = glm.inverse(self.camera.view_matrix_2D) * clip
        return glm.vec3(world.x, world.y, 0.0)


class MousePointerApp(App):
    TITLE = "tt3de mouse pointer"
    SUB_TITLE = "left-click toggles pointer / crosshair"

    def compose(self) -> ComposeResult:
        yield Header()
        yield MousePointerView()


if __name__ == "__main__":
    app = MousePointerApp()
    app._disable_tooltips = True
    app.run()
