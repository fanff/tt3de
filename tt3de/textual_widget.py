
import math
from time import monotonic
from typing import Iterable
from rich.color import Color
from rich.style import Style
from rich.text import Segment
from textual import events
from textual.app import App, ComposeResult, RenderResult
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (

    Static,
)
from abc import ABC, abstractmethod
from tt3de.richtexture import RenderContext, StaticTexture, get_cube_vertices
from tt3de.tt3de import FPSCamera, Line3D, Point3D, PointElem


class TT3DView(Static):
    can_focus = True

    write_debug_inside = False

    last_frame_data_info = {}
    frame_idx = reactive(0)
    
    tsrender_dur = 0.0
    update_dur = 0.0
    render_clear_dur = 0.0
    camera = None
    update_timer = None

    cwr = None

    DEFAULT_CSS = """
    TT3DView {
        height: 100%;
        width: 100%;
    }
    """
    def __init__(self):
        super().__init__()
        self.camera = FPSCamera(pos=Point3D(0, 0,0))
        self.camera.point_at(Point3D(0,0,1))
        self.rc = RenderContext(self.size.width, self.size.height)
        self.cwr = Cwr(self.rc)
        self.initialize()
        self.update_timer = self.set_interval(1.0 / 30, self.calc_frame, pause=False)
        self.last_frame_data_info = {}
    @abstractmethod
    def initialize(self):
        pass
    @abstractmethod
    def update_step(self,tg):
        pass
    @abstractmethod
    def post_render_step(self):
        pass

    def calc_frame(self):
        self.frame_idx += 1

    async def on_event(self,event:events.Event):
        if isinstance(event,events.MouseEvent):
            self.frame_idx = 0
            if isinstance(event,events.MouseMove):
                event.delta_x
                event.delta_y

                self.camera.rotate_left_right(event.delta_x*5)
                self.camera.rotate_up_down(event.delta_y*5)
        elif isinstance(event,events.Key):
            match event.key:
                case "j":
                    self.camera.move_forward(0.3)
                case "k":
                    self.camera.move_forward(-0.3)
                case "h":
                    self.camera.move_side(0.3)
                case "l":
                    self.camera.move_side(-0.3)
                case "z":
                    self.camera.move_forward(0.3)
                case "s":
                    self.camera.move_forward(-0.3)
                case "q":
                    self.camera.move_side(0.3)
                case "d":
                    self.camera.move_side(-0.3)
            

    def render(self):
        if self.size.width > 1 and self.size.height > 1:

            ts = monotonic()
            self.update_step(0.2) # TODO fix the time of the update 
            self.update_dur = (monotonic() - ts) 

            ts = monotonic()
            self.rc.clear_canvas()
            self.render_clear_dur = (
                monotonic() - ts
            ) * 0.1 + self.render_clear_dur * 0.9

            ts = monotonic()
            self.rc.render(self.camera)
            self.tsrender_dur = monotonic() - ts

            if self.write_debug_inside:
                self.rc.write_text(f"{self.frame_idx}", 1, 1)
                self.rc.write_text(f"U:{self.update_dur*1000:.2f} ms", 1, 5)
                self.rc.write_text(f"C:{self.render_clear_dur*1000:.2f} ms", 1, 4)
                self.rc.write_text(f"R:{self.tsrender_dur*1000:.2f} ms;", 1, 3)

            self.last_frame_data_info = {"frame_idx":self.frame_idx,
                                         "update_dur":self.update_dur,
                                         "render_clear_dur":self.render_clear_dur,
                                         "tsrender_dur":self.tsrender_dur,
                                         }
            
            self.post_render_step()
            return self.cwr
        else:
            return ""


class Cwr:
    def __init__(self, rc):
        self.rc: RenderContext = rc

    def __rich_console__(
        self, console, options
    ) -> Iterable[Segment]:
        yield from self.rc.iter_canvas()


