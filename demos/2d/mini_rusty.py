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


from tt3de.textual.widgets import (
    CameraConfig,
    FloatSelector,
    RenderInfo,
    RustRenderContextInfo,
    Vector3Selector,
)
from tt3de.textual_widget import TT3DView

from tt3de.tt_2dnodes import TT2DMesh, TT2DNode, TT2Polygon


class GLMTester(TT3DView):
    use_native_python = False

    def __init__(self):
        super().__init__()

    def initialize(self):
        
        # prepare a bunch of material
        self.rc.texture_array, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        # create a root node 
        self.root2Dnode = TT2DNode()

        # first triangle 
        a2dmesh: TT2Polygon = Prefab2D.unitary_triangle(TT2Polygon)
        a2dmesh.material_id = 2
        a2dmesh.local_transform = glm.translate(
            glm.vec3(float(0) + 0.1, float(0) + 0.1,0.0)
        ) * glm.rotate(0.3,glm.vec3(0.0, 0.0,1.0))* glm.scale(glm.vec3(0.4, 1.2,1.0)) 

        self.root2Dnode.elements.append(a2dmesh)

        # final append
        self.rc.append(self.root2Dnode)

        self.absolute_location = glm.vec4(0.0, 0.0, 1.0,1.0)
        # setup a time reference, to avoid trigonometry issues
        self.reftime = time()

    def update_step(self, timediff):
        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)
        ts = self.reftime - time()

        tsfactor = 2

        rot = ts * tsfactor

    def post_render_step(self):
        cc: CameraConfig = self.parent.query_one("CameraConfig")
        cc.refresh_camera_position(
            (self.camera.pos.x, self.camera.pos.y, self.camera.pos.z)
        )
        cc.refresh_camera_rotation(
            (math.degrees(self.camera.yaw), math.degrees(self.camera.pitch))
        )
        context_log:RustRenderContextInfo = self.parent.query_one(RustRenderContextInfo)

        context_log.update_counts({"geom":self.rc.geometry_buffer.geometry_count(),
                                   "prim":self.rc.primitive_buffer.primitive_count()})
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
                        relx_px = (
                            (float(event.x) - (self.camera.screen_width / 2))
                        ) / (self.camera.screen_width * self.camera.zoom_2D)
                        rely_px = (
                            (float(event.y) - (self.camera.screen_height / 2))
                        ) / (self.camera.screen_height * self.camera.zoom_2D)


                        small_tr_vector = glm.vec3(-relx_px, -rely_px, 0.0)
                        
                        self.root2Dnode.local_transform = glm.translate(small_tr_vector)*self.root2Dnode.local_transform

            case events.MouseScrollDown:
                self.camera.set_zoom_2D(self.camera.zoom_2D * 0.9)
            case events.MouseScrollUp:
                self.camera.set_zoom_2D(self.camera.zoom_2D * 1.1)
            case _:
                info_box: Static = self.parent.query_one(".lastevent")
                info_box.update(f"{event.__class__}: \n{str(event)}")


class Content(Static):
    def compose(self) -> ComposeResult:

        with Container(classes="someinfo"):
            yield Static("", classes="lastevent")
            yield CameraConfig()
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
        width: 5fr;
    }

    .someinfo {
        height: auto;
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
