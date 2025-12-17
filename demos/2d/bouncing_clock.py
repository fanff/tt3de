# -*- coding: utf-8 -*-

import datetime
from pyglm import glm
from textual.widgets import (
    Header,
)
from textual.app import App, ComposeResult
from tt3de.asset_fastloader import MaterialPerfab
from tt3de.glm_camera import ViewportScaleMode
from tt3de.textual.debugged_view import DebuggedView
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py
from tt3de.tt_2dnodes import TT2DNode, TT2DUnitSquare


class BouncingClock(TT3DViewStandAlone):
    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer, self.sprite_sheet_map = (
            MaterialPerfab.rust_set_0(with_sprite_map=True)
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
        self.clock_chars = list("00:00:00")
        self.digit_nodes = []

        char_pos_x = 0.0
        for i, ch in enumerate(self.clock_chars):
            mat_id = self.sprite_sheet_map.map_string_to_matidx(ch)[0]
            left_shift = 0 if ch.isdigit() else -0.2
            digit_point = TT2DUnitSquare(
                material_id=mat_id,
            )
            digit_point.position = glm.vec3(char_pos_x + left_shift, 0.0, 0.0)
            char_pos_x += 0.8 if ch.isdigit() else 0.4

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

    def update_step(self, delta_time: float):
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

        for i, (ch, mat_id) in enumerate(
            zip(now_str, self.sprite_sheet_map.map_string_to_matidx(now_str))
        ):
            if self.clock_chars[i] != ch:
                self.clock_chars[i] = ch
                self.digit_nodes[i].set_material_id(mat_id)


class CameraTest2D(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DebuggedView(BouncingClock())


if __name__ == "__main__":
    app = CameraTest2D()
    app._disable_tooltips = True
    app.run()
