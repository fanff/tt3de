# -*- coding: utf-8 -*-
import math
from abc import abstractmethod
from time import time

from pyglm import glm
from textual import events
from textual.containers import Container
from textual.geometry import Region
from textual.strip import Strip

from tt3de.glm_camera import GLMCamera
from tt3de.render_context_rust import RustRenderContext


class FrameTimings:
    update_duration: float = 0.0
    render_duration: float = 0.0
    to_textual_duration: float = 0.0


class TT3DViewStandAlone(Container):
    DEFAULT_CSS = """
    TT3DViewStandAlone {
        height: 100%;
        width: 100%;
    }
    """
    can_focus = True  # see https://textual.textualize.io/guide/input/#focusable-widgets

    frame_idx: int = 0

    def __init__(
        self,
        *children,
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
        material_buffer_size=256,
        # parameters for the camera
        use_left_hand_perspective=True,
    ):
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )
        self.debugger_component = None
        self.frame_timings = FrameTimings()

        if use_left_hand_perspective:
            init_camera_position = glm.vec3(0, 2, -7)
            init_yaw, init_pitch = math.radians(0), 0
        else:
            init_camera_position = glm.vec3(0, 2, -7)
            init_yaw, init_pitch = math.radians(180), 0
        self.camera: GLMCamera = GLMCamera(
            init_camera_position,
            90,
            90,
            use_left_hand_perspective=use_left_hand_perspective,
        )
        self.camera.set_yaw_pitch(init_yaw, init_pitch)
        self.camera.set_zoom_2D(1.0)
        self.rc = RustRenderContext(
            90,
            90,
            vertex_buffer_size=vertex_buffer_size,
            geometry_buffer_size=geometry_buffer_size,
            primitive_buffer_size=primitive_buffer_size,
            transform_buffer_size=transform_buffer_size,
            texture_buffer_size=texture_buffer_size,
            material_buffer_size=material_buffer_size,
        )

        self.initialize()
        self.last_frame_time: float = float(time() - 1.0)
        self.engine_start_time: float = float(time())
        if target_fps is not None and target_fps > 0:
            self.target_dt = 1.0 / target_fps
        else:
            self.target_dt = None

    def on_mount(self):
        if self.target_dt is not None:
            self.auto_refresh = self.target_dt

    async def on_event(self, event: events.Event):
        if isinstance(event, events.Resize):
            w = max(self.size.width, 3)
            h = max(self.size.height, 3)
            self.rc.update_wh(w, h)
            self.camera.recalc_fov_h(w, h)
        else:
            await super().on_event(event)

        if self.is_debugged():
            self.app.log.debug(f"Event in TT3DViewStandAlone: {event}")
            self.debugger_component.container_event(event)

    def is_debugged(self) -> bool:
        return self.debugger_component is not None and self.debugger_component

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
            return [Strip([]) for h in range(crop.height)]

        ts = time()
        target_dt = 0 if self.target_dt is None else self.target_dt
        if ts > self.last_frame_time + target_dt:
            self.frame_idx += 1
            self.update_frame()

            ts = time()
            result = self.rc.to_textual_2(crop)
            if self.is_debugged():
                self.frame_timings.to_textual_duration = time() - ts
            self.last_frame_time = time()
            return result
        else:
            result = self.rc.to_textual_2(crop)
            return result

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def update_step(self, delta_time: float):
        pass

    @abstractmethod
    def post_render_step(self):
        pass

    def update_frame(self):
        if self.is_debugged():
            self.update_frame_debugged()
        if self.size.width > 1 and self.size.height > 1:
            ts = time()
            self.update_step(
                min(ts - self.last_frame_time, 0.5)
            )  # time since last frame

            self.rc.clear_canvas()

            self.rc.render(self.camera)

            self.post_render_step()
            return True
        return False

    def update_frame_debugged(self):
        if self.size.width > 1 and self.size.height > 1:
            ts = time()
            self.update_step(
                min(ts - self.last_frame_time, 0.5)
            )  # time since last frame
            self.frame_timings.update_duration = time() - ts

            self.rc.clear_canvas()
            self.rc.render(self.camera)
            self.frame_timings.render_duration = (
                time() - ts - self.frame_timings.update_duration
            )
            self.debugger_component.has_just_rendered()
            self.post_render_step()
            return True
        return False

    def time_since_start(self) -> float:
        return time() - self.engine_start_time
