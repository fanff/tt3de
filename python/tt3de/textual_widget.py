# -*- coding: utf-8 -*-
import math
from abc import abstractmethod
from time import time

import glm
from textual import events
from textual.containers import Container
from textual.geometry import Region
from textual.strip import Strip

from tt3de.glm_camera import GLMCamera
from tt3de.render_context_rust import RustRenderContext


class TimingRegistry:
    def __init__(self):
        self.data = {}

    def set_duration(self, name, duration):
        self.data[name] = duration

    def get_duration(self, name) -> float:
        return self.data.get(name, -1.0)


class TT3DView(Container):
    DEFAULT_CSS = """
    TT3DView {
        height: 100%;
        width: 100%;
    }
    """
    can_focus = True  # see https://textual.textualize.io/guide/input/#focusable-widgets

    enableMouseFpsCamera = False

    frame_idx: int = 0

    timing_registry = TimingRegistry()

    camera: GLMCamera = None
    last_frame_time = 0.0

    def __init__(
        self,
        # parameters for the widget
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        # parameters for the engine
        target_fps: int = 24,
        # parameters for the render context
        vertex_buffer_size=4096,
        geometry_buffer_size=256,
        primitive_buffer_size=4096,
        transform_buffer_size=64,
        texture_buffer_size=32,
        # parameters for the camera
        use_left_hand_perspective=True,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

        self.camera = GLMCamera(
            glm.vec3(0, 2, 7),
            90,
            90,
            use_left_hand_perspective=use_left_hand_perspective,
        )
        self.camera.set_yaw_pitch(math.radians(180), 0)
        self.rc = RustRenderContext(
            90,
            90,
            vertex_buffer_size=vertex_buffer_size,
            geometry_buffer_size=geometry_buffer_size,
            primitive_buffer_size=primitive_buffer_size,
            transform_buffer_size=transform_buffer_size,
            texture_buffer_size=texture_buffer_size,
        )

        self.initialize()
        self.last_frame_time = time() - 1.0
        self.target_fps = target_fps
        self.target_dt = 1.0 / target_fps

    def on_mount(self):
        self.auto_refresh = self.target_dt

    async def on_event(self, event: events.Event):
        if self.enableMouseFpsCamera and isinstance(event, events.MouseMove):
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
            self.enableMouseFpsCamera = True

        elif isinstance(event, events.Key):
            # the event.key depends on the keyboard Layout

            # here is the azerty layout
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
                    self.camera.move_side(-0.3)
                case "d":
                    self.camera.move_side(0.3)
                case "escape":
                    self.enableMouseFpsCamera = False

        elif isinstance(event, events.Resize):
            event.virtual_size
            event.size

            w = max(self.size.width, 3)
            h = max(self.size.height, 3)
            self.rc.update_wh(w, h)
            self.camera.recalc_fov_h(w, h)
        else:
            await super().on_event(event)

    def render_lines(self, crop: Region) -> list[Strip]:
        """
        Render the widget into lines.

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
        if ts > self.last_frame_time + self.target_dt:
            self.frame_idx += 1
            self.render_step()
            self.timing_registry.set_duration("render_step", time() - ts)

            ts = time()
            result = self.rc.to_textual_2(crop)
            self.timing_registry.set_duration("to_textual_", time() - ts)

            self.last_frame_time = time()
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

    def render_step(self):
        if self.size.width > 1 and self.size.height > 1:
            ts = time()
            self.update_step(ts - self.last_frame_time)  # time since last frame
            update_dur = time() - ts

            ts = time()
            self.rc.clear_canvas()
            render_clear_dur = time() - ts

            ts = time()
            self.rc.render(self.camera)
            tsrender_dur = time() - ts

            self.timing_registry.set_duration("frame_idx", self.frame_idx)
            self.timing_registry.set_duration("update_dur", update_dur)
            self.timing_registry.set_duration("render_clear_dur", render_clear_dur)
            self.timing_registry.set_duration("tsrender_dur", tsrender_dur)

            self.post_render_step()
            return True
        return False
