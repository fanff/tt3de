import math
from time import monotonic, time
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
from abc import  abstractmethod
from tt3de.glm.pyglmtexture import GLMCamera
from tt3de.render_context_rust import RustRenderContext
from textual.strip import Strip
from textual.geometry import Region
from textual.containers import Container

class TimingRegistry:

    def __init__(self):
        self.data = {}

    def set_duration(self, name, duration):
        self.data[name] = duration

    def get_duration(self, name) -> float:
        return self.data.get(name, -1.0)


class TT3DView(Container):
    can_focus = True

    use_native_python = True

    write_debug_inside = False
    mouse_fps_camera_mode = False

    frame_idx:int = reactive(0)
    last_processed_frame = 0

    timing_registry = TimingRegistry()

    camera :GLMCamera= None
    last_frame_time = 0.0
    cached_result = None
    cwr = None

    DEFAULT_CSS = """
    TT3DView {
        height: 100%;
        width: 100%;
        
    }
    """

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

        self.camera = GLMCamera(glm.vec3(0, 0, -5), 90, 90)
        self.rc = RustRenderContext(self.size.width, self.size.height)
        self.initialize()
        ##self.update_timer = self.set_interval(1.0 / 24, self.calc_frame, pause=False)
        self.last_frame_time = time()-1.0

    def on_mount(self):
        self.auto_refresh = 1.0/20.0

   
    async def on_event(self, event: events.Event):
        if self.mouse_fps_camera_mode and isinstance(event, events.MouseMove):
            if event.delta_x != 0:
                self.camera.rotate_left_right(
                    math.radians(event.delta_x * (800.0 / self.size.width))
                )
            if event.delta_y != 0:
                offset = self.screen.get_offset(self)
                p = math.radians(
                    (((event.y - offset.y) / self.size.height) - 0.5) * 160
                )
                self.camera.set_yaw_pitch(self.camera.yaw, p)

        elif isinstance(event, events.Click):
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
        else:
            await super().on_event(event)


    def render_lines(self, crop: Region) -> list[Strip]:
        """Render the widget in to lines.

        Args:
            crop: Region within visible area to render.

        Returns:
            A list of list of segments.
        """
        if crop.height == 0:
            return []
        if crop.width == 0:
            return [Strip([]) for h in crop.height]
        
        ts = time()
        if ts>self.last_frame_time+1.0/24.0:
            self.frame_idx+=1
            self.render_step()
            self.timing_registry.set_duration("render_step", time() - ts)

            ts = time()
            result = self.rc.to_textual_2(crop)
            self.timing_registry.set_duration("to_textual_", time() - ts)

            self.last_frame_time = time()
            self.cached_result = result
            return result
        else:
            result = self.rc.to_textual_2(crop)
            self.timing_registry.set_duration("to_textual_", time() - ts)
            return result

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def update_step(self, tg):
        pass

    @abstractmethod
    def post_render_step(self):
        pass

    #def render(self):
    #    return "render called, should not happen actually :/"

    def render_step(self):
        if (
            self.size.width > 1
            and self.size.height > 1
        ):

            ts = time()
            self.update_step(0.2)  # TODO fix the time of the update
            update_dur = time() - ts

            ts = time()
            self.rc.clear_canvas()
            render_clear_dur = time() - ts

            ts = time()
            self.rc.render(self.camera)
            tsrender_dur = time() - ts

            if self.write_debug_inside:
                l = f"Frame:{self.frame_idx}: size: {self.size.width} x {self.size.height}"
                self.rc.write_text(l, 5, 6)

                self.rc.write_text(f"U:{self.update_dur*1000:.2f} ms", 1, 5)
                self.rc.write_text(f"C:{self.render_clear_dur*1000:.2f} ms", 1, 4)
                self.rc.write_text(f"R:{self.tsrender_dur*1000:.2f} ms;", 1, 3)
                self.rc.write_text(f"s:{self.render_strips_dur*1000:.2f} ms;", 1, 2)

            self.timing_registry.set_duration("frame_idx", self.frame_idx)
            self.timing_registry.set_duration("update_dur", update_dur)
            self.timing_registry.set_duration("render_clear_dur", render_clear_dur)
            self.timing_registry.set_duration("tsrender_dur", tsrender_dur)

            self.post_render_step()
            return True
        return False
