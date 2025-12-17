# -*- coding: utf-8 -*-
import math

from textual import events


from tt3de.textual_standalone import TT3DViewStandAlone


class TimingRegistry:
    def __init__(self):
        self.data: dict[str, float] = {}

    def set_duration(self, name: str, duration: float):
        self.data[name] = duration

    def get_duration(self, name: str) -> float:
        return self.data.get(name, -1.0)


class TT3DFpsView(TT3DViewStandAlone):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enableMouseFpsCamera = False

    async def on_event(self, event: events.Event):
        if self.enableMouseFpsCamera and isinstance(event, events.MouseMove):
            if event.delta_x != 0:
                angle = math.radians(event.delta_x * (800.0 / self.size.width))

                angle = angle * (-1 if not self.camera.use_left_hand_perspective else 1)
                self.camera.rotate_left_right(angle)
            if event.delta_y != 0:
                offset = self.screen.get_offset(self)
                p = math.radians(
                    (((event.y - offset.y) / self.size.height) - 0.5) * 160
                )
                p = p * (-1 if not self.camera.use_left_hand_perspective else 1)
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
                    self.camera.move_side(-0.3)
                case "l":
                    self.camera.move_side(0.3)
                case "z":
                    self.camera.move_forward(0.3)
                case "w":
                    self.camera.move_forward(0.3)
                case "s":
                    self.camera.move_forward(-0.3)
                case "q":
                    self.camera.move_side(-0.3)
                case "a":
                    self.camera.move_side(-0.3)
                case "d":
                    self.camera.move_side(0.3)
                case "escape":
                    self.enableMouseFpsCamera = False
        else:
            await super().on_event(event)
