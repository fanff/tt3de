import math
from time import monotonic,time
from typing import Iterable
import glm
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
from tt3de.glm.pyglmtexture import GLMCamera, GLMRenderContext
from tt3de.richtexture import RenderContext, StaticTexture, get_cube_vertices
from tt3de.tt3de import FPSCamera, Line3D, Point3D, PointElem
from textual.strip import Strip
from textual.geometry import Region


class TT3DView(Widget):
    can_focus = True

    use_native_python = True

    write_debug_inside = False
    mouse_fps_camera_mode = False


    cached_result = []
    last_frame_data_info = {}
    frame_idx = reactive(0)
    last_processed_frame = reactive(0)

    tsrender_dur = 0.0
    update_dur = 0.0
    render_clear_dur = 0.0
    render_strips_dur = 0.0
    camera = None
    update_timer = None
    cwr = None

    DEFAULT_CSS = """
    TT3DView {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self,name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,):
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled
        )

        if self.use_native_python:
            self.camera = FPSCamera(pos=Point3D(0, 0, 0))
            self.camera.point_at(Point3D(0, 0, 1))
            self.rc = RenderContext(self.size.width, self.size.height)

        else:
            self.camera = GLMCamera(Point3D(0, 0, 0), 90, 90)
            self.camera.point_at(glm.vec3(0, 0, 1))
            self.rc = GLMRenderContext(self.size.width, self.size.height)
        self.initialize()
        self.update_timer = self.set_interval(1.0 / 30, self.calc_frame, pause=False)
        self.last_frame_data_info = {}  
        self.rc.setup_segment_cache(self.app.console)
        
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def update_step(self, tg):
        pass

    @abstractmethod
    def post_render_step(self):
        pass

    def calc_frame(self):
        self.frame_idx += 1
    

    # override for some performance gain
    def get_style_at(self,x,y):
        return Style()

    # overriden
    async def on_event(self, event: events.Event):
        if self.mouse_fps_camera_mode and isinstance(event, events.MouseMove):
            if event.delta_x!=0:
                self.camera.rotate_left_right(math.radians(event.delta_x *(800.0/self.size.width)))
            if event.delta_y!=0:
                offset = self.screen.get_offset(self)
                self.camera.pitch=math.radians((((event.y-offset.y)/self.size.height)-.5) * 160)
                self.camera.update_rotation()

        elif isinstance(event,events.Click):
            self.mouse_fps_camera_mode = True
            
        elif isinstance(event, events.Key):
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
                case "p":
                    self.update_timer.pause()
                case "P":
                    self.update_timer.resume()
                case "escape":
                    self.mouse_fps_camera_mode = False


    def render_lines(self, crop:Region) -> list[Strip]:
        """Render the widget in to lines.

        Args:
            crop: Region within visible area to render.

        Returns:
            A list of list of segments.
        """

        # trick to avoid the compositor "get_style" to force a render
        if crop.height==1:
            return []

        if self.last_processed_frame == self.frame_idx:
            return self.cached_result
        else:
            self.render_step()
            
        ts = time()

        sw = self.rc.screen_width
        strip_map = self.rc.split_map

        segmap = self.rc.segmap
        console = self.app.console
        result = []
        currentLine = []
        for idx, i in enumerate(self.rc.canvas_array):

            if idx > 0 and (idx % sw == 0):
                s = Strip(currentLine)
                #s.render(console)
                result.append(s)
                currentLine = []
            currentLine.append( segmap[i] )
            #yield self.segmap[i]
        s = Strip(currentLine)
        #s.render(console)
        result.append(s)

        self.render_strips_dur = time()-ts
        self.last_processed_frame = self.frame_idx

        self.cached_result = result
        return result

    def render(self):
        return "render called, should not happen actually :/"

    def render_step(self):
        if self.size.width > 1 and self.size.height > 1 and self.update_timer._active.is_set():

            ts = time()
            self.update_step(0.2)  # TODO fix the time of the update
            self.update_dur = time() - ts

            ts = time()
            self.rc.clear_canvas()
            self.render_clear_dur = time() - ts

            ts = time()
            self.rc.render(self.camera)
            self.tsrender_dur = time() - ts

            if self.write_debug_inside:
                l = f"Frame:{self.frame_idx}: size: {self.size.width} x {self.size.height}" 
                self.rc.write_text(l, 5, 6)

                self.rc.write_text(f"U:{self.update_dur*1000:.2f} ms", 1, 5)
                self.rc.write_text(f"C:{self.render_clear_dur*1000:.2f} ms", 1, 4)
                self.rc.write_text(f"R:{self.tsrender_dur*1000:.2f} ms;", 1, 3)
                self.rc.write_text(f"s:{self.render_strips_dur*1000:.2f} ms;", 1, 2)
            self.last_frame_data_info = {
                "frame_idx": self.frame_idx,
                "update_dur": self.update_dur,
                "render_clear_dur": self.render_clear_dur,
                "tsrender_dur": self.tsrender_dur,
            }

            self.post_render_step()
            return True
        return False
    
