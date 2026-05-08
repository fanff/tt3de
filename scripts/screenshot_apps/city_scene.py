# -*- coding: utf-8 -*-
"""City block loaded from OBJ + BMP, top-down camera (doc screenshot scene)."""

from pyglm import glm
from textual.app import App, ComposeResult

from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import (
    MaterialBufferPy,
    TextureBufferPy,
    find_glyph_indices_py,
    materials,
    toglyphmethod,
)
from tt3de.tt_3dnodes import TT3DNode


class CityBlockScene(TT3DViewStandAlone):
    """Town_1 OBJ with TownColor_256 texture, angled top-down view."""

    def initialize(self):
        self.rc.material_buffer = MaterialBufferPy()
        self.rc.texture_buffer = TextureBufferPy(32)

        self.rc.material_buffer.add_static((0, 0, 0), (0, 0, 0), 0)

        img: ImageTexture = fast_load("models/cities/TownColor_256.bmp")
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
        city = fast_load("models/cities/Town_1.obj", flip_triangles=True)
        city.material_id = mat_id
        root.add_child(city)
        self.rc.append_root(root)

        self.camera.move_at(glm.vec3(3.0, 4.0, -3.0))
        self.camera.point_at(glm.vec3(0.0, 0.0, 1.0))

    def update_step(self, delta_time: float):
        pass

    def post_render_step(self):
        pass


class CityBlockDemoApp(App):
    """Fullscreen city block view."""

    DEFAULT_CSS = """
    CityBlockDemoApp {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield CityBlockScene(target_fps=0, vertex_buffer_size=8192)
