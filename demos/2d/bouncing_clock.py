# -*- coding: utf-8 -*-
"""
Bouncing digital clock using TTSL texture sampling for glyph sprites.

The clock keeps movement/collision and HH:MM:SS updates in Python. Glyph
textures and per-character ``ShaderPy`` materials come from ``RasterFont``.

Run:
    uv run python demos/2d/bouncing_clock.py
"""

from pathlib import Path
from typing import List

import datetime
from pyglm import glm
from textual.widgets import (
    Header,
)
from textual.app import App, ComposeResult
from tt3de.asset_fastloader import MaterialPerfab
from tt3de.glm_camera import ViewportScaleMode
from tt3de.raster_font import RasterFont
from tt3de.textual.debugged_view import DebuggedView
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py  # type: ignore[reportMissingImports]
from tt3de.tt_2dnodes import TT2DNode, TT2DUnitSquare


class BouncingClock(TT3DViewStandAlone):
    def initialize(self) -> None:
        # Keep prefab slot-0 as a static material; shader materials are appended for digits.
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
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

        self.border_x_dist = 8.0
        self.border_y_dist = 3.0

        # initial direction for the clock movement
        self.direction = glm.normalize(glm.vec3(2, 3, 0))
        self.speed = 1.5
        # creating the root 2D node
        self.root2Dnode = TT2DNode()

        self.clock_node = TT2DNode()

        # the clock format is "HH:MM:SS.ZZZ"
        self.clock_chars: List[str] = list("00:00:00")
        self.digit_nodes: List[TT2DUnitSquare] = []

        char_pos_x = 0.0
        for ch in self.clock_chars:
            mat_id = self.font.material_id(ch)
            char_width = 0.8 if ch.isdigit() else 0.4
            digit_point = TT2DUnitSquare(
                material_id=mat_id,
            )
            # Glyph shaders alpha-blend keyed texels; keep quads non-overlapping
            # so adjacent digits do not share a terminal cell.
            digit_point.transparent = True
            digit_point.scale = glm.vec2(char_width, 1.0)
            digit_point.position = glm.vec3(char_pos_x, 0.0, 0.0)
            char_pos_x += char_width

            self.digit_nodes.append(digit_point)
            self.clock_node.add_child(digit_point)

        # final clock width is the last char_pos_x
        self.clock_width = char_pos_x

        # adding background material and Rectangle node
        background_mat_idx = self.rc.material_buffer.add_static(
            (0, 0, 0), (0, 0, 0), find_glyph_indices_py("▀")
        )
        self.root2Dnode.add_child(
            TT2DUnitSquare(
                transform=glm.scale(
                    glm.vec3(self.border_x_dist * 2, self.border_y_dist * 2, 1.0)
                )
                * glm.translate(glm.vec3(0.0, 0.0, 1.0)),
                material_id=background_mat_idx,
                centered=True,
            )
        )

        self.root2Dnode.add_child(self.clock_node)
        self.rc.append_root(self.root2Dnode)

    def update_step(self, delta_time: float) -> None:
        # check for border collision and change direction if needed
        if self.clock_node.get_position().x + self.clock_width > self.border_x_dist:
            self.direction = glm.normalize(
                glm.vec3(-abs(self.direction.x), self.direction.y, 0)
            )
        elif self.clock_node.get_position().x < -self.border_x_dist:
            self.direction = glm.normalize(
                glm.vec3(abs(self.direction.x), self.direction.y, 0)
            )
        if self.clock_node.get_position().y + 1.0 > self.border_y_dist:
            self.direction = glm.normalize(
                glm.vec3(self.direction.x, -abs(self.direction.y), 0)
            )
        elif self.clock_node.get_position().y < -self.border_y_dist:
            self.direction = glm.normalize(
                glm.vec3(self.direction.x, abs(self.direction.y), 0)
            )

        # move the clock
        self.clock_node.position = (
            self.clock_node.position + self.direction * delta_time * self.speed
        )

        # update the clock digits
        now_str = datetime.datetime.now().strftime("%H:%M:%S")[: len(self.clock_chars)]
        if len(now_str) < len(self.clock_chars):
            # Right pad with spaces if needed
            now_str = now_str.ljust(len(self.clock_chars))

        mat_ids = self.font.material_ids(now_str)
        for i, (ch, mat_id) in enumerate(zip(now_str, mat_ids)):
            if self.clock_chars[i] != ch:
                self.clock_chars[i] = ch
                self.digit_nodes[i].set_material_id(mat_id)


debug_view = False


class CameraTest2D(App):
    def compose(self) -> ComposeResult:
        yield Header()
        if debug_view:
            yield DebuggedView(BouncingClock())
        else:
            yield BouncingClock()


if __name__ == "__main__":
    app = CameraTest2D()
    app._disable_tooltips = True
    app.run()
