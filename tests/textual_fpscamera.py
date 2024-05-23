import math
from statistics import mean
from time import monotonic, time
from typing import Sequence
from context import tt3de
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
)

from tt3de.asset_fastloader import fast_load, prefab_mesh_single_triangle
from tt3de.richtexture import (
    DistGradBGShade,
    ImageTexture,
    RenderContext,
    StaticTexture,
    build_gizmo_arrows,
    get_cube_vertices,
)
from tt3de.textual.widgets import CameraConfig, RenderInfo
from tt3de.textual_widget import TT3DView
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Node3D, Point3D, PointElem, Quaternion, Triangle3D

class MyView(TT3DView):
    use_native_python = True
    def initialize(self):

        texture1 = fast_load("models/cube_texture.bmp")
        texture2 = fast_load("models/cubetest2.bmp")
        texture3 = fast_load("models/cubetest3.bmp")
        
        meshclass = Mesh3D
        cube_mesh:Mesh3D = fast_load("models/cube.obj",meshclass)
        cube_mesh.set_texture(texture3)
        self.rc.append(cube_mesh)

        #m=prefab_mesh_single_triangle(meshclass)
        #m.set_texture(texture2)
        #
        #self.rc.append(m)
        
        self.write_debug_inside = True
        self.capture_mouse_events=True


    def update_step(self, timediff):
        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)

    def post_render_step(self):
        rinfo:RenderInfo = self.parent.query_one("RenderInfo")
        rinfo.append_frame_duration(self.last_frame_data_info.get("tsrender_dur", 0))
        rinfo.update_frame_count(self.frame_idx)
        cc:CameraConfig = self.parent.query_one("CameraConfig")
        cc.refresh_camera_position((self.camera.pos.x,self.camera.pos.y,self.camera.pos.z))
        cc.refresh_camera_rotation((math.degrees(self.camera.yaw),math.degrees(self.camera.pitch)))

    async def on_event(self, event: events.Event):
        await super().on_event(event)

        if isinstance(event,events.MouseMove):
            pass
        elif isinstance(event,events.Leave):
            info_box: Static = self.parent.query_one(".lastevent")
            info_box.update(f"leaving!")
        else:
            info_box: Static = self.parent.query_one(".lastevent")
            info_box.update(f"{event.__class__}: \n{str(event)}")


class Content(Static):
    def compose(self) -> ComposeResult:
        with Container(classes="someinfo"):
            yield Static("", classes="lastevent")
            yield RenderInfo()
            yield CameraConfig((0,0,-3))

        yield MyView()

    def on_camera_config_position_changed(self,event:CameraConfig.PositionChanged):
        x,y,z = event.value
        viewelem:MyView = self.query_one("MyView")
        viewelem.camera.move_at(Point3D(x,y,z))

    def on_camera_config_orientation_changed(self,event:CameraConfig.OrientationChanged):
        viewelem:MyView = self.query_one("MyView")
        y,p = event.value
        viewelem.camera.set_yaw_pitch(math.radians(y),math.radians(p))
    def on_camera_config_projection_changed(self,event:CameraConfig.ProjectionChanged):
        viewelem:MyView = self.query_one("MyView")

        fov,dist_min,dist_max,charfactor = event.value
        viewelem.camera.set_projectioninfo(math.radians(fov),dist_min,dist_max,charfactor)
class Demo3dView(App):
    DEFAULT_CSS = """
    Content {
        layout: horizontal;
        height: 100%;
        border: solid red;
    }
    MyView {
        height: 100%;
        width: 5fr;
    }
    .someinfo {
        height: 100%;
        width: 1fr;
        border: solid red;
    }

    Sparkline {
        margin: 2;
        height: 5;
    }
    """

    def compose(self) -> ComposeResult:

        yield Header()
        yield Content()

    async def on_mount(self):
        pass


async def run():
    pass


if __name__ == "__main__":

    app = Demo3dView()
    app._disable_tooltips=True
    app.run()
