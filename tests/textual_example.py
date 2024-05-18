import math
from time import monotonic
from typing import Sequence
from context import tt3de 
from statistics import mean
from tt3de.richtexture import DistGradBGShade, RenderContext, StaticTexture, get_cube_vertices
from tt3de.textual_widget import Cwr, TT3DView
from tt3de.tt3de import FPSCamera, Line3D, Point3D, PointElem,Triangle3D
from textual import events
from textual.containers import Container
from textual.app import App, ComposeResult, RenderResult
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Footer,
    Header,
    Label,
    Markdown,
    Static,
    Sparkline
)
class MyView(TT3DView):
    def __init__(self):
        super().__init__()

    def initialize(self):
        self.rc.append(
            Line3D(Point3D(0.1, 0, 0), Point3D(0.9, 0, 0), StaticTexture("x", "red"))
        )
        self.rc.append(
            Line3D(Point3D(0, 0.1, 0), Point3D(0, 0.9, 0), StaticTexture("y", "blue"))
        )
        self.rc.append(
            Line3D(Point3D(0, 0, 0.1), Point3D(0, 0, 0.9), StaticTexture("z", "green"))
        )
        self.rc.append(
            PointElem(
                Point3D(0, 0, 0),
                StaticTexture("O", "white"),
            )
        )
        self.rc.append(PointElem(Point3D(1, 0, 0), StaticTexture("X", "red")))
        self.rc.append(PointElem(Point3D(0, 1, 0), StaticTexture("Y", "blue")))
        self.rc.append(PointElem(Point3D(0, 0, 1), StaticTexture("Z", "green")))

        for i in range(3):
            self.rc.extend(get_cube_vertices(Point3D(0, i, 0), 0.7,DistGradBGShade))
        self.rc.extend(get_cube_vertices(Point3D(2, 0, 0), 0.7,  DistGradBGShade))
        self.rc.extend(get_cube_vertices(Point3D(3, 0, 0), 0.7,  DistGradBGShade))
        self.rc.extend(get_cube_vertices(Point3D(1, 0, 0), 0.7,  DistGradBGShade))


        self.write_debug_inside=True
    def update_step(self,timediff):
        ts = monotonic()
        amp = 4
        tf = 0.8
        c1 = math.cos(tf * ts) * amp
        c2 = math.sin(tf * ts) * amp
        self.camera.move_at(Point3D(c1, 1 + math.cos(tf * ts / 2) * 3, c2))
        self.camera.point_at(Point3D(0.0, 0, 0))
        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)
    def post_render_step(self):


        spark:Sparkline = self.parent.query_one(".tsrender_dur")
        spark.data = spark.data[1:] + [self.last_frame_data_info.get("tsrender_dur",0)]
        l:Label = self.parent.query_one(".frame_idx")
        l.update(f"Frame: {self.frame_idx}")


        l:Label = self.parent.query_one(".render_label")
        l.update(f"Render: {(1000*mean(spark.data)):.2f} ms")
        #.update(str(self.last_frame_data_info))


    async def on_event(self,event:events.Event):
        # await super().on_event(event)
        info_box:Static= self.parent.query_one(".lastevent")
        info_box.update(str(event))
        

class Content(Static):
    def compose(self) -> ComposeResult:
        keep_count = 50
        with Container(classes="someinfo"):
            yield Static("",classes="lastevent")

            yield Label("Frame idx",classes="frame_idx")


            yield Label("Render",classes="render_label")
            yield Sparkline([0]*keep_count,summary_function=mean,classes="tsrender_dur")

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
    app.run()
