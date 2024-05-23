import math
from statistics import mean
from textwrap import dedent
from time import monotonic, time
from typing import Sequence

import glm

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
    Static,Input
)
from textual.validation import Function, Number, ValidationResult, Validator

from tt3de.asset_fastloader import fast_load, prefab_mesh_single_triangle
from tt3de.glm.pyglmtexture import GLMMesh3D
from tt3de.richtexture import (
    DistGradBGShade,
    ImageTexture,
    RenderContext,
    StaticTexture,
    build_gizmo_arrows,
    get_cube_vertices,
)


from tt3de.textual.widgets import FloatSelector
from tt3de.textual_widget import TT3DView
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Node3D, Point3D, PointElem, Quaternion, Triangle3D

def vec3_str(v): 
    return f"vec3({v.x:.2f},{v.y:.2f},{v.z:.2f})"
class MyView(TT3DView):
    use_native_python = False


    def __init__(self):
        super().__init__()

    def initialize(self):
        texture1 = fast_load("models/cube_texture.bmp")
        texture2 = fast_load("models/cubetest2.bmp")
        texture3 = fast_load("models/cubetest3.bmp")
        
        meshclass = GLMMesh3D
        m = fast_load("models/cube.obj",meshclass)


        m.set_texture(texture3)
        self.rc.append(m)


        self.camera.move_at(glm.vec3(5,  0, 5))
        self.camera.point_at(glm.vec3(0.0, 0, 0))

        self.write_debug_inside = True
        self.capture_mouse_events=False


    def update_step(self, timediff):
        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)

    def post_render_step(self):
        spark: Sparkline = self.parent.query_one(".tsrender_dur")
        spark.data = spark.data[1:] + [self.last_frame_data_info.get("tsrender_dur", 0)]

        l: Label = self.parent.query_one(".frame_idx")
        l.update(f"Frame: {self.frame_idx}")

        l: Label = self.parent.query_one(".render_label")
        l.update(f"Render: {(1000*mean(spark.data)):.2f} ms")
        
        camera_msg = dedent(f"""Pos: {vec3_str(self.camera.pos)}
Dir: {self.camera.direction_vector()}
Yaw: {self.camera.yaw:.2f} Pitch: {self.camera.pitch:.2f}""")
        self.parent.query_one(".camera_label").update(camera_msg)

    async def on_event(self, event: events.Event):
        await super().on_event(event)

        match event.__class__:
            case events.Leave:
                info_box: Static = self.parent.query_one(".lastevent")
                info_box.update(f"leaving!")
            case _:
                info_box: Static = self.parent.query_one(".lastevent")
                info_box.update(f"{event.__class__}: \n{str(event)}")
 
class Content(Static):
    def compose(self) -> ComposeResult:
        keep_count = 50
        with Container(classes="someinfo"):
            yield Static("", classes="lastevent")


            with Container() as c:
                yield Label("Render", classes="render_label")
                yield Label("Frame idx", classes="frame_idx")
                yield Sparkline(
                    [0] * keep_count, summary_function=mean, classes="tsrender_dur"
                )
            with Container() as c:
                yield Label("Camera")
                yield Static("", classes="camera_label")

                yield FloatSelector(50,130,80,id="input_camera_fov")
                yield FloatSelector(0.1,20,1.0, id="input_camera_mindepth")
                yield FloatSelector(10,100,50.,id="input_camera_maxdepth")
                yield FloatSelector(0.5,2.5,1.8,id="input_character_factor")
                #yield Input(value="90",placeholder="90",type="integer",id="input_camera_fov",
                #            validators=[Number(minimum=1,maximum=180)],validate_on="changed")
                #yield Input(value="1.0",placeholder="1.0",type="number",id="input_camera_mindepth",
                #            validators=[Number(minimum=1,maximum=100000)])
                #yield Input(value="100.0",placeholder="100",type="number",id="input_camera_maxdepth",
                #            validators=[Number(minimum=1,maximum=100000)])
                #yield Input(value="1.8",placeholder="1.8",type="number",id="input_character_factor",
                #            validators=[Number(minimum=0.1,maximum=5)])



        yield MyView()

            #    case _:
            #        return 
    def on_float_selector_changed(self,event:FloatSelector.Changed) -> None:
        viewelem:MyView = self.query_one("MyView")
        valuef = float(event.value)
        match event.input.id:
            case "input_camera_fov":
                viewelem.camera.set_projectioninfo(fov_radians=math.radians(valuef))
            case "input_camera_mindepth":
                viewelem.camera.set_projectioninfo(dist_min=valuef)
            case "input_camera_maxdepth":
                viewelem.camera.set_projectioninfo(dist_max=valuef)
            case "input_character_factor":
                viewelem.camera.set_projectioninfo(character_factor=valuef)



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
