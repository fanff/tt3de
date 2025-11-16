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


class TT3DViewStandAlone(Container):
    DEFAULT_CSS = """
    TT3DViewStandAlone {
        height: 100%;
        width: 100%;
    }
    """
    can_focus = True  # see https://textual.textualize.io/guide/input/#focusable-widgets

    frame_idx: int = 0
    camera: GLMCamera = None
    last_frame_time = 0.0
    engine_start_time = 0.0

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
        self.debugger_component = None
        self.camera = GLMCamera(
            glm.vec3(0, 2, 7),
            90,
            90,
            use_left_hand_perspective=use_left_hand_perspective,
        )
        self.camera.set_yaw_pitch(math.radians(180), 0)
        self.camera.set_zoom_2D(0.1)
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
        self.engine_start_time = time()
        self.target_fps = target_fps
        self.target_dt = 1.0 / target_fps

    def on_mount(self):
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
            return [Strip([]) for h in crop.height]

        ts = time()
        if ts > self.last_frame_time + self.target_dt:
            self.frame_idx += 1
            self.render_step()

            ts = time()
            result = self.rc.to_textual_2(crop)

            self.last_frame_time = time()
            return result
        else:
            result = self.rc.to_textual_2(crop)
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

            ts = time()
            self.rc.clear_canvas()

            ts = time()
            self.rc.render(self.camera)
            if self.is_debugged():
                self.debugger_component.has_just_rendered()
            self.post_render_step()
            return True
        return False

    def time_since_start(self) -> float:
        return time() - self.engine_start_time
