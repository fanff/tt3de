# -*- coding: utf-8 -*-
from time import time

from pyglm import glm

from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
)

from tt3de.asset_fastloader import fast_load
from tt3de.tt3de import find_glyph_indices_py, materials


from tt3de.textual_widget import TT3DFpsView

from tt3de.tt_3dnodes import TT3DNode
from tt3de.tt3de import toglyphmethod


class GLMTester(TT3DFpsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, vertex_buffer_size=4096 * 3, **kwargs)

    def initialize(self):
        # prepare a bunch of material
        img = fast_load("models/cities/TownColor_256.bmp")
        tex_idx = self.rc.texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )
        HALF_BLOCK = find_glyph_indices_py("▀")
        self.rc.material_buffer.add_static((200, 10, 10), (50, 50, 50), 0)  # 0
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
                glyph_method=toglyphmethod.ToGlyphMethodPyStatic(HALF_BLOCK),
            )
        )

        # create a root 3D node
        self.root3Dnode = TT3DNode()

        self.city = fast_load(
            "models/cities/Town_2.obj",
            flip_triangles=True,
        )
        self.city.material_id = mat_id
        self.root3Dnode.add_child(self.city)

        # final append
        self.rc.append_root(self.root3Dnode)

        # setup a time reference, to avoid trigonometry issues
        self.reftime = time()

    def update_step(self, timediff):
        time_since_start = time() - self.reftime

        self.city.set_local_transform(
            glm.rotate(time_since_start / 2, glm.vec3(0, 1, 0))
        )


class Demo3dView(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield GLMTester()


if __name__ == "__main__":
    app = Demo3dView()
    app._disable_tooltips = True
    app.run()
