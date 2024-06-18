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
    Vector3Selector,
)
from tt3de.textual_widget import TT3DView

from tt3de.tt_2dnodes import TT2DMesh, TT2DNode


class GLMTester(TT3DView):
    use_native_python = False

    def __init__(self):
        super().__init__()

    def initialize(self):

        self.rc.texture_array, self.rc.material_buffer = MaterialPerfab.set_1()
        self.root2Dnode = TT2DNode()

        materialidx = 1
        for j in range(3):

            if materialidx>=4 : continue
            a2dnode = TT2DNode()

            a2dmesh: TT2DMesh = Prefab2D.unitary_square(TT2DMesh)
            a2dmesh.material_id = materialidx
            materialidx += 1
            a2dnode.elements.append(a2dmesh)

            if j==2:
                a2dnode.local_transform = glm.translate(
                    glm.vec3(0.0, float(j) ,0.0)
                ) * glm.scale(glm.vec3(1.7777778, 1.0,1.0))
            else:
                a2dnode.local_transform = glm.translate(
                    glm.vec3(0.0, float(j) + 0.1,0.0)
                ) * glm.scale(glm.vec3(0.8, 0.8,1.0))

            self.root2Dnode.elements.append(a2dnode)

        a2dnode = TT2DNode()
        a2dmesh: TT2DMesh = Prefab2D.unitary_square(TT2DMesh)
        a2dmesh.material_id = 3
        a2dnode.elements.append(a2dmesh)
        a2dnode.local_transform = glm.translate(
            glm.vec3(2, float(2) ,0.0)
        ) * glm.scale(glm.vec3(1.7777778, 1.0,1.0))
        
        self.root2Dnode.elements.append(a2dnode)
        

        # adding a long stuff to have a repeated texture
        a2dnode = TT2DNode()
        a2dmesh: TT2DMesh = Prefab2D.unitary_square(TT2DMesh)
        a2dmesh.material_id = 3
        a2dnode.elements.append(a2dmesh)

        for uva, uvb, uvc in a2dmesh.uvmap:
            uva.x = uva.x*2.0
            uvb.x = uvb.x*2.0
            uvc.x = uvc.x*2.0
            uva.y = uva.y
            uvb.y = uvb.y
            uvc.y = uvc.y


        a2dnode.local_transform = glm.translate(
            glm.vec3(1.0, float(.0) ,0.0)
        ) *glm.scale(glm.vec3(1.7777778*2, 1.0,1.0))
        
        self.root2Dnode.elements.append(a2dnode)




        # final append
        self.rc.append(self.root2Dnode)

        self.square_spining = True

        self.absolute_location = glm.vec3(0.0, 0.0, 1.0)
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

        self.parent.query_one("RenderInfo").append_frame_duration(self.timing_registry)

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
                        self.square_spining = not self.square_spining
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
            yield RenderInfo()
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