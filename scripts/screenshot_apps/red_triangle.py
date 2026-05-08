# -*- coding: utf-8 -*-
"""Textured 3D cube loaded from OBJ + BMP (doc screenshot scene)."""

import math

from pyglm import glm
from textual.app import App, ComposeResult

from tt3de.asset_fastloader import MaterialPerfab, fast_load
from tt3de.richtexture import ImageTexture
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py, materials, toglyphmethod
from tt3de.tt_3dnodes import TT3DNode


class TexturedCubeView(TT3DViewStandAlone):
    """A textured cube showing OBJ loading, BMP textures, and UV mapping."""

    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

        img: ImageTexture = fast_load("models/cube_texture.bmp")
        tex_idx = self.rc.texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )
        mat_id = self.rc.material_buffer.add_base_texture(
            materials.BaseTexturePy(
                albedo_texture_idx=tex_idx,
                albedo_texture_subid=0,
                glyph_texture_idx=0,
                glyph_texture_subid=0,
                front=True,
                back=True,
                glyph=True,
                glyph_uv_0=True,
                front_uv_0=True,
                back_uv_0=False,
                glyph_method=toglyphmethod.ToGlyphMethodPyStatic(
                    find_glyph_indices_py("▀")
                ),
            )
        )

        root = TT3DNode()
        cube = fast_load("models/cube.obj", flip_triangles=True)
        cube.material_id = mat_id
        cube.local_transform = glm.rotate(
            math.radians(35), glm.vec3(0, 1, 0)
        ) * glm.rotate(math.radians(15), glm.vec3(1, 0, 0))
        root.add_child(cube)
        self.rc.append_root(root)

        self.camera.move_at(glm.vec3(1.0, 1.5, -3.5))
        self.camera.point_at(glm.vec3(0.0, 0.3, 0.0))

    def update_step(self, delta_time: float):
        pass

    def post_render_step(self):
        pass


class TexturedCubeDemoApp(App):
    """Fullscreen textured cube view."""

    DEFAULT_CSS = """
    TexturedCubeDemoApp {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield TexturedCubeView(target_fps=0)
