# -*- coding: utf-8 -*-
import math
from time import time

from pyglm import glm

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import (
    Header,
    Static,
)

from tt3de.asset_fastloader import fast_load
from tt3de.tt3de import find_glyph_indices_py

from tt3de.textual.widgets import (
    CameraConfig,
    RenderInfo,
    RustRenderContextInfo,
)
from tt3de.textual_widget import TT3DView

from tt3de.tt_3dnodes import TT3DNode


class GLMTester(TT3DView):
    use_native_python = False

    def __init__(self):
        super().__init__(primitive_buffer_size=4096 * 2)

    def initialize(self):
        # prepare a bunch of material
        img = fast_load("models/cities/TownColor_256.bmp")
        self.rc.texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )

        self.rc.material_buffer.add_static((200, 10, 10), (50, 50, 50), 0)  # 0
        self.rc.material_buffer.add_textured(0, find_glyph_indices_py("▀"))  # idx = 1

        # create a root 3D node
        self.root3Dnode = TT3DNode()

        self.city = fast_load(
            "models/cities/Town_2.obj",
            reverse_uv_u=False,
            reverse_uv_v=True,
            inverse_uv=True,
        )
        self.city.material_id = 1
        self.city.local_transform = glm.translate(glm.vec3(0, 0, 0))
        self.root3Dnode.add_child(self.city)

        # final append
        self.rc.append(self.root3Dnode)

        # setup a time reference, to avoid trigonometry issues
        self.reftime = time()

    def update_step(self, timediff):
        self.city.set_transform(
            self.rc, glm.rotate(time() - self.reftime, glm.vec3(0, 1, 0))
        )

    def post_render_step(self):
        cc: CameraConfig = self.parent.query_one("CameraConfig")
        v = self.camera.position_vector()
        cc.refresh_camera_position((v.x, v.y, v.z))
        cc.refresh_camera_rotation(
            (math.degrees(self.camera.yaw), math.degrees(self.camera.pitch))
        )

        self.parent.query_one("RenderInfo").append_frame_duration(self.timing_registry)

        context_log: RustRenderContextInfo = self.parent.query_one(
            RustRenderContextInfo
        )

        context_log.update_counts(
            {
                "geom": self.rc.geometry_buffer.geometry_count(),
                "prim": self.rc.primitive_buffer.primitive_count(),
            }
        )


class Content(Static):
    def compose(self) -> ComposeResult:
        with Container(classes="someinfo"):
            yield CameraConfig()
            yield RenderInfo()
            yield RustRenderContextInfo()

        yield GLMTester()

    def on_camera_config_projection_changed(
        self, event: CameraConfig.ProjectionChanged
    ):
        viewelem: GLMTester = self.query_one("GLMTester")

        fov, dist_min, dist_max, charfactor = event.value
        viewelem.camera.set_projectioninfo(
            math.radians(fov), dist_min, dist_max, charfactor
        )


class Demo3dView(App):
    DEFAULT_CSS = """
    Content {
        layout: horizontal;
        height: 100%;

    }
    TT3DView {

        height: 100%;
        width: 4fr;
    }

    .someinfo {
        height: 100%;
        width: 1fr;
        border: solid red;
    }

    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Content()


if __name__ == "__main__":
    app = Demo3dView()
    app._disable_tooltips = True
    app.run()
