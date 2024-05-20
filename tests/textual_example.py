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

from tt3de.richtexture import (
    DistGradBGShade,
    ImageTexture,
    RenderContext,
    StaticTexture,
    build_gizmo_arrows,
    get_cube_vertices,
)
from tt3de.textual_widget import Cwr, TT3DView
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Node3D, Point3D, PointElem, Quaternion, Triangle3D, load_bmp, load_palette, round_to_palette


class MyView(TT3DView):



    def __init__(self):
        super().__init__()

    def initialize(self):

        
        #self.rc.extend(build_gizmo_arrows(Point3D(0, 0, 0)))
        #for i in range(3):
        #    self.rc.extend(get_cube_vertices(Point3D(0, i, 0), 0.7, DistGradBGShade))
        # self.rc.extend(get_cube_vertices(Point3D(11, 0, 1), 0.7, DistGradBGShade))
        # self.rc.extend(get_cube_vertices(Point3D(3, 0, 0), 0.7, DistGradBGShade))
        # self.rc.extend(get_cube_vertices(Point3D(1, 0, 0), 0.7, DistGradBGShade))


        # palette = load_palette("models/RGB_6bits.bmp")
        #roundedimg = round_to_palette(load_bmp("models/cube_texture.bmp"),palette)
        #roundedimg = round_to_palette(load_bmp("models/cubetest2.bmp"),palette)
        texture1 = ImageTexture(load_bmp("models/cube_texture.bmp"))
        texture2 = ImageTexture(load_bmp("models/cubetest2.bmp"))
        texture3 = ImageTexture(load_bmp("models/cubetest3.bmp"))

        m = Mesh3D.from_obj("models/cube.obj")
        m.set_texture(texture2)
        #m.triangles=m.triangles[3:4]
        #self.rc.append(m)

        
        n = Node3D()
        n.elems.append(m)
        n.set_translation(Point3D(0,2,0))
        
        

        cube2 = Mesh3D.from_obj("models/cube.obj")
        cube2.set_texture(texture3)
        n2 = Node3D()
        n2.set_translation(Point3D(2,0,0))
        n2.elems.append(cube2)

        n.elems.append(n2)


        cube3 = Mesh3D.from_obj("models/cube.obj")
        cube3.set_texture(texture1)
        n3 = Node3D()
        n3.set_translation(Point3D(6,0,0))
        n3.elems.append(cube3)


        
#       


        self.rc.append_node(n)
        self.rc.append_node(n3)
        #n2.set_translation(Point3D(1.5,0,0))
        #n2.elems.append(n)
        #self.rc.append_node(n2)

        self.write_debug_inside = True

        

        self.camera.move_at(Point3D(5,  0, 5))
        self.camera.point_at(Point3D(0.0, 0, 0))

        self.capture_mouse_events=False


    def update_step(self, timediff):
        ts = time()
        ampxz = 5
        ampy = 1
        tf = 1
        c1 = math.cos(tf * ts) * ampxz
        c2 = math.sin(tf * ts) * ampxz
        #self.camera.move_at(Point3D(c1,  math.cos(tf * ts) * ampy, c2))
        #self.camera.point_at(Point3D(0.0, 0, 0))

        self.rc.elements[0].rotation = Quaternion.from_euler(0,0,tf * ts)

        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)

    def post_render_step(self):

        spark: Sparkline = self.parent.query_one(".tsrender_dur")
        spark.data = spark.data[1:] + [self.last_frame_data_info.get("tsrender_dur", 0)]

        l: Label = self.parent.query_one(".frame_idx")
        l.update(f"Frame: {self.frame_idx}")

        l: Label = self.parent.query_one(".render_label")
        l.update(f"Render: {(1000*mean(spark.data)):.2f} ms")

    async def on_event(self, event: events.Event):
        await super().on_event(event)

        match event.__class__:
            case events.MouseMove:
                pass
            case _:
                info_box: Static = self.parent.query_one(".lastevent")
                info_box.update(str(event))


class Content(Static):
    def compose(self) -> ComposeResult:
        keep_count = 50
        with Container(classes="someinfo"):
            yield Static("", classes="lastevent")

            yield Label("Frame idx", classes="frame_idx")

            yield Label("Render", classes="render_label")
            yield Sparkline(
                [0] * keep_count, summary_function=mean, classes="tsrender_dur"
            )

        yield MyView()


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
