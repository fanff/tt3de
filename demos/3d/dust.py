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

from tt3de.obj_loader import load_obj

from tt3de.textual.widgets import (
    CameraConfig,
    RenderInfo,
    RustRenderContextInfo,
)
from tt3de.textual_widget import TT3DFpsView

from tt3de.tt_3dnodes import TT3DNode


class GLMTester(TT3DFpsView):
    use_native_python = False

    def __init__(self):
        super().__init__(
            vertex_buffer_size=4096 * 2,
            geometry_buffer_size=4096 * 2,
            texture_buffer_size=64,
            transform_buffer_size=4096 * 2,
        )

    def initialize(self):
        self.rc.material_buffer.add_static((200, 10, 10), (50, 50, 50), 0)  # 0

        # create a root 3D node
        self.root3Dnode = TT3DNode()

        obj_file = os.path.join(current_demo_folder, "Dust/Dust.obj")

        polys, polyfans = load_obj(
            obj_file, self.rc.texture_buffer, self.rc.material_buffer
        )

        for poly in polys:
            self.root3Dnode.add_child(poly)
        for polyfan in polyfans:
            self.root3Dnode.add_child(polyfan)

        self.root3Dnode.local_transform = glm.rotate(
            math.radians(90), glm.vec3(-1, 0, 0)
        )
        # final append
        self.rc.append_root(self.root3Dnode)

        # setup a time reference, to avoid trigonometry issues
        self.reftime = time()

    def update_step(self, timediff):
        pass

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


def download_extract(url, dest, folder_name="Dust"):
    import requests
    import zipfile
    import io

    if not os.path.exists(os.path.join(dest, folder_name)):
        # download the zip file
        r = requests.get(url)
        # extract the file content in the current folder
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(dest)


if __name__ == "__main__":
    import os

    current_demo_folder = os.path.dirname(__file__)
    download_extract(
        "https://www.models-resource.com/download/28161/", current_demo_folder
    )
    app = Demo3dView()
    app._disable_tooltips = True
    app.run()
