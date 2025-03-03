import math
from statistics import mean
from textwrap import dedent
from time import monotonic, time
from typing import Sequence

import glm

from textual import events
from textual.app import App, ComposeResult, RenderResult
from textual.containers import Container
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Footer,
    Header,
    Label,
    Markdown,
    Sparkline,
    Static,
    Input,
)
from textual.validation import Function, Number, ValidationResult, Validator

from tt3de.asset_fastloader import MaterialPerfab, Prefab2D
from textual.css.query import NoMatches

from tt3de.prefab3d import Prefab3D
from tt3de.textual.widgets import (
    CameraConfig,
    EngineLog,
    FloatSelector,
    RenderInfo,
    RustRenderContextInfo,
    Vector3Selector,
)
from tt3de.textual_widget import TT3DView

from tt3de.tt_2dnodes import TT2DMesh, TT2DNode, TT2Polygon
from tt3de.tt_3dnodes import TT3DNode


class GLMTester(TT3DView):
    def __init__(self):
        super().__init__()

    def initialize(self):
        # prepare a bunch of material
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        # create a root 3D node
        self.root3Dnode = TT3DNode()

        self.root3Dnode.add_child(Prefab3D.gizmo_points())

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 5
        tri.local_transform = glm.translate(glm.vec3(-1.1, 1, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 6
        tri.local_transform = glm.translate(glm.vec3(0, 1, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 7
        tri.local_transform = glm.translate(glm.vec3(1.1, 1, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 8
        tri.local_transform = glm.translate(glm.vec3(0, 2, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 9
        tri.local_transform = glm.translate(glm.vec3(1.1, 2, 0))
        self.root3Dnode.add_child(tri)
        tri = Prefab3D.unitary_triangle()
        tri.material_id = 10
        tri.local_transform = glm.translate(glm.vec3(-1.1, 2, 0))
        self.root3Dnode.add_child(tri)

        # final append
        self.rc.append(self.root3Dnode)

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
        cc.refresh_camera_zoom(self.camera.zoom_2D)
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

    async def on_event(self, event: events.Event):
        await super().on_event(event)

        match event.__class__:
            case events.Leave:
                pass
                # info_box: Static = self.parent.query_one(".lastevent")
                # info_box.update(f"leaving!")

            case events.Key:
                event: events.Key = event
                match event.key:
                    case "a":
                        pass
            case events.MouseDown:
                event: events.MouseDown = event
                match event.button:
                    case 1:
                        screen_click_position = glm.vec3(
                            float(event.x), float(event.y), 0.0
                        )
                        # convert to screen to clip space
                        clip_click_position = glm.vec3(
                            screen_click_position.x / self.size.width * 2 - 1,
                            1 - screen_click_position.y / self.size.height * 2,
                            0.0,
                        )

                        # convert to world space using the view matrix
                        world_click_position = (
                            glm.inverse(self.camera.view_matrix_2D)
                            * clip_click_position
                        )

                        self.camera.view_matrix_2D
                        # self.root2Dnode.local_transform = glm.translate(small_tr_vector)*self.root2Dnode.local_transform
                        self.parent.query_one("EngineLog").add_line(
                            f"click ! {str(world_click_position)}"
                        )

            case events.MouseScrollDown:
                self.camera.set_zoom_2D(self.camera.zoom_2D * 0.9)
            case events.MouseScrollUp:
                self.camera.set_zoom_2D(self.camera.zoom_2D * 1.1)
            case _:
                try:
                    info_box: Static = self.parent.query_one(".lastevent")
                    info_box.update(f"{event.__class__}: \n{str(event)}")
                except NoMatches:
                    pass


class Content(Static):
    def compose(self) -> ComposeResult:
        with Container(classes="someinfo"):
            yield Static("", classes="lastevent")
            yield EngineLog()
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
