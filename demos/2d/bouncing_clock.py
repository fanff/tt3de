# -*- coding: utf-8 -*-
"""
Bouncing digital clock using TTSL texture sampling for glyph sprites.

The clock keeps movement/collision and HH:MM:SS updates in Python, while each
digit/colon quad now uses a compiled TTSL shader (`clock_tex`) to sample a
per-character texture.

Run:
    uv run python demos/2d/bouncing_clock.py
"""

# -*- coding: utf-8 -*-
from pathlib import Path
from textwrap import dedent
from typing import Dict, List

import datetime
from pyglm import glm
from textual.widgets import (
    Header,
)
from textual.app import App, ComposeResult
from tt3de.asset_fastloader import DefaultSpriteSheet32px, MaterialPerfab
from tt3de.asset_load import load_bmp
from tt3de.glm_camera import ViewportScaleMode
from tt3de.richtexture import ImageTexture
from tt3de.textual.debugged_view import DebuggedView
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py, materials  # type: ignore[reportMissingImports]
from tt3de.tt_2dnodes import TT2DNode, TT2DUnitSquare
from tt3de.ttsl.compiler import all_passes_compilation

SPRITE_SIZE_PX = 32
SHADER_UNIFORM_TEXIDX = "u_TextureIndex"

SHADER_SRC = dedent(
    """
    def clock_tex(tt_TexCoord0: vec2, tt_TexCoord1: vec2) -> tuple[vec4, vec4, int]:
        sampled_top: vec4 = tt_texture(u_TextureIndex, tt_TexCoord0)
        sampled_bottom: vec4 = tt_texture(u_TextureIndex, tt_TexCoord1)
        # Shader materials write final colors directly (no alpha compositing pass), so
        # each half-cell must black out its own transparent texels to avoid key-color
        # fringes from the sprite sheet at glyph boundaries.
        if sampled_top.w < 0.5:
            top_rgb: vec4 = vec4(0.0, 0.0, 0.0, 1.0)
        else:
            top_rgb: vec4 = vec4(sampled_top.x, sampled_top.y, sampled_top.z, 1.0)
        if sampled_bottom.w < 0.5:
            bottom_rgb: vec4 = vec4(0.0, 0.0, 0.0, 1.0)
        else:
            bottom_rgb: vec4 = vec4(sampled_bottom.x, sampled_bottom.y, sampled_bottom.z, 1.0)
        return (top_rgb, bottom_rgb, 0)
    """
)


def _sprite_to_texture_data(
    sprite_sheet: ImageTexture, sprite_idx: int
) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    """Extract one 32x32 sprite tile as a standalone texture payload."""
    cols = sprite_sheet.image_width // SPRITE_SIZE_PX
    tile_row_from_bottom = cols - (sprite_idx // cols) - 1
    tile_col = sprite_idx % cols
    start_x = tile_col * SPRITE_SIZE_PX
    start_y = tile_row_from_bottom * SPRITE_SIZE_PX

    tile_pixels: list[tuple[int, int, int, int]] = []
    for y in range(start_y, start_y + SPRITE_SIZE_PX):
        row = sprite_sheet.img_data[y]
        tile_pixels.extend(row[start_x : start_x + SPRITE_SIZE_PX])

    return (SPRITE_SIZE_PX, SPRITE_SIZE_PX, tile_pixels)


class BouncingClock(TT3DViewStandAlone):
    def initialize(self) -> None:
        # Keep prefab slot-0 as a static material; shader materials are appended for digits.
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        self._bytecode, reg_settings = all_passes_compilation(
            SHADER_SRC,
            "clock_tex",
            {SHADER_UNIFORM_TEXIDX: int},
        )
        half_upper_block = find_glyph_indices_py("▀")
        self.shader_mat_by_sprite: Dict[DefaultSpriteSheet32px, int] = {}

        sprite_sheet_path = (
            Path(__file__).resolve().parents[2] / "models" / "sprite_sheet_32px.bmp"
        )
        with sprite_sheet_path.open("rb") as fin:
            sprite_sheet_img = ImageTexture(
                load_bmp(fin, alpha=255, transparent_colors=[(0, 0, 255)])
            )

        sprite_texture_by_sprite: Dict[DefaultSpriteSheet32px, int] = {}
        for sprite in DefaultSpriteSheet32px:
            w, h, chained_data = _sprite_to_texture_data(sprite_sheet_img, sprite.value)
            tex_idx = self.rc.texture_buffer.add_texture(
                w,
                h,
                chained_data,
                False,
                False,
            )
            sprite_texture_by_sprite[sprite] = tex_idx

        for sprite in DefaultSpriteSheet32px:
            shader_regs = reg_settings.fork()
            shader_regs.set_variable(
                SHADER_UNIFORM_TEXIDX, sprite_texture_by_sprite[sprite]
            )
            mat_idx = self.rc.material_buffer.add_shader(
                materials.ShaderPy(
                    self._bytecode,
                    default_glyph=half_upper_block,
                    register_seed=shader_regs.get_register_list(),
                )
            )
            self.shader_mat_by_sprite[sprite] = mat_idx

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
            sprite = DefaultSpriteSheet32px.convert_string_to_sprites(ch)[0]
            mat_id = self.shader_mat_by_sprite[sprite]
            char_width = 0.8 if ch.isdigit() else 0.4
            digit_point = TT2DUnitSquare(
                material_id=mat_id,
            )
            # Shader materials don't alpha-blend transparent texels like BaseTexturePy,
            # so keep quads non-overlapping to avoid visible character collisions.
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

        for i, (ch, mat_id) in enumerate(
            zip(
                now_str,
                [
                    self.shader_mat_by_sprite[sprite]
                    for sprite in DefaultSpriteSheet32px.convert_string_to_sprites(
                        now_str
                    )
                ],
            )
        ):
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
