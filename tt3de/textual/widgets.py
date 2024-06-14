from dataclasses import dataclass
from statistics import mean
from typing import Any, Coroutine, List
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
    Input,
)
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

from textual.message import Message
from textual.layouts import horizontal

from tt3de.textual_widget import TT3DView
from tt3de.tt3de import (
    FPSCamera,
    Line3D,
    Mesh3D,
    Node3D,
    Point3D,
    PointElem,
    Quaternion,
    Triangle3D,
)


class FloatSelector(Widget, can_focus=False):
    DEFAULT_CSS = """

    FloatSelector{
        layout: horizontal;
        
        height:auto;
    }
    FloatSelector > Button {
        border: none;
        width: 3;
        min-width:2;

        height: 3;
        min-height:2;

    }
    FloatSelector > Input{
        align-horizontal: center;
        width: 1fr;
    }

    FloatSelector > .minus-1{
        align-horizontal: left;
        
        
    }
    FloatSelector > .plus-1{
        align-horizontal: right;
    }

    """
    minvalue: float = reactive(1)
    maxvalue: float = reactive(10)

    current_value: float = reactive(1.0)
    current_buffer: float = reactive(1.0)

    inclusive_left: bool = reactive(False)
    inclusive_right: bool = reactive(True)

    accuracy = 0.01

    round_figures: int = reactive(3)
    mouse_factor: float = 0.5
    button_factor: float = 5.0

    is_mouse_clicking = False

    @dataclass
    class Changed(Message):
        """Posted when the value changes.

        Can be handled using `on_float_selector_changed` in a subclass of `FloatSelector` or in a parent
        widget in the DOM.
        """

        input: "FloatSelector"
        """The `FloatSelector` widget that was changed."""

        value: float
        """The value that the input was changed to."""

        value_str: str

    def __init__(
        self,
        minvalue=1.0,
        maxvalue=100.0,
        initial_value=None,
        mouse_factor: float = 0.5,
        button_factor: float = 5.0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(id=id, classes=classes, disabled=disabled, name=name)
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.current_value = (
            initial_value
            if initial_value is not None
            else (self.maxvalue + self.minvalue) / 2
        )
        self.current_buffer = (
            initial_value
            if initial_value is not None
            else (self.maxvalue + self.minvalue) / 2
        )

        self.mouse_factor = mouse_factor
        self.button_factor = button_factor

    def compose(self):

        yield Button("-", classes="minus-1")
        yield Input(f"{round(self.current_value,self.round_figures)}")
        yield Button("+", classes="plus-1")

    def on_button_pressed(self, event: Button.Pressed):
        match str(event.button.label):
            case "-":
                self.current_buffer -= self.button_factor
            case "+":
                self.current_buffer += self.button_factor

    async def _on_mouse_down(
        self, event: events.MouseDown
    ) -> Coroutine[Any, Any, None]:
        self.is_mouse_clicking = True
        # myinp = self.query_one(Input)
        # myinp.value = "lol"
        return super()._on_mouse_down(event)

    async def _on_mouse_up(self, event: events.MouseUp) -> None:
        self.is_mouse_clicking = False
        return await super()._on_mouse_up(event)

    async def on_event(self, event: events.Event):
        if self.is_mouse_clicking:
            if isinstance(event, events.Leave):
                pass  # TODO : Find why I can't catch this dude ?!
                self.is_mouse_clicking = False
            if isinstance(event, (events.DescendantBlur, events.DescendantFocus)):
                self.is_mouse_clicking = False

        if isinstance(event, events.Leave):
            1 / 0  # traying to capture randomly

        await super().on_event(event)

    def on_mouse_move(self, event: events.MouseMove):
        if self.is_mouse_clicking:
            diff = event.delta_x
            self.current_buffer = self.current_value + (self.mouse_factor * diff)

    def watch_current_buffer(self, buffered_value):
        self._set_current_value(buffered_value)

    def watch_current_value(self, value):
        myinp = None
        try:
            myinp = self.query_one(Input)
            myinp.value = f"{round(value,self.round_figures)}"
        except NoMatches:
            pass

    def _set_current_value(self, value):
        min_bound_c = (
            value >= self.minvalue if self.inclusive_left else value > self.minvalue
        )
        max_bound_c = (
            value <= self.maxvalue if self.inclusive_right else value < self.maxvalue
        )
        if min_bound_c:
            if max_bound_c:
                self.current_value = value
            else:
                self.current_value = (
                    self.maxvalue
                    if self.inclusive_right
                    else self.maxvalue - self.accuracy
                )
        else:
            self.current_value = (
                self.minvalue if self.inclusive_left else self.minvalue + self.accuracy
            )

        self.post_message(
            self.Changed(
                self,
                self.current_value,
                f"{round(self.current_value,self.round_figures)}",
            )
        )


class Vector3Selector(Widget):
    DEFAULT_CSS = """

    Vector3Selector{
        height:auto;
    }
    """

    @dataclass
    class Changed(Message):
        """Posted when the value changes.

        Can be handled using `on_vector_selector_changed` in a subclass of `Vector3Selector` or in a parent
        widget in the DOM.
        """

        input: "Vector3Selector"
        """The `FloatSelector` widget that was changed."""

        value: tuple[float]
        """The value that the input was changed to."""

    _selector_list: List[FloatSelector] = []
    _init_info = []

    def __init__(
        self,
        minvalue=(1.0, -1.0, -1.0),
        maxvalue=(100.0, 100.0, 100.0),
        initial_value=(3.0, 3.0, 3.0),
        mouse_factor: float = (0.5, 0.5, 0.5),
        button_factor: float = (5.0, 5.0, 5.0),
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(id=id, classes=classes, disabled=disabled, name=name)

        self._init_info = [
            minvalue,
            maxvalue,
            initial_value,
            mouse_factor,
            button_factor,
        ]

    def compose(self):
        self._selector_list = []
        (minvalue, maxvalue, initial_value, mouse_factor, button_factor) = (
            self._init_info
        )
        for sidx in range(3):
            s = FloatSelector()

            s.minvalue = minvalue[sidx]
            s.maxvalue = maxvalue[sidx]
            s.mouse_factor = mouse_factor[sidx]
            s.button_factor = button_factor[sidx]
            s.current_buffer = initial_value[sidx]
            self._selector_list.append(s)

        yield from self._selector_list

    def on_float_selector_changed(self, event: FloatSelector.Changed) -> None:
        event.bubble = False
        current_value = tuple([s.current_value for s in self._selector_list])
        self.post_message(Vector3Selector.Changed(self, current_value))


class CameraConfig(Widget):
    DEFAULT_CSS = """

    CameraConfig{
        height:auto;
    }
    """

    @dataclass
    class PositionChanged(Message):
        """Posted when the value changes.

        Can be handled using `on_camera_config_position_changed` in a subclass of `PositionChanged` or in a parent
        widget in the DOM.
        """

        input: "CameraConfig"
        """The `FloatSelector` widget that was changed."""

        value: tuple[float, float, float]
        """The value that the input was changed to."""

    @dataclass
    class ProjectionChanged(Message):
        input: "CameraConfig"
        value: tuple[float, float, float, float]

    @dataclass
    class OrientationChanged(Message):
        input: "CameraConfig"
        value: tuple[float, float]

    _init_camera_position = None

    def __init__(
        self,
        initial_cam_position=(0.0, 0.0, 0.0),
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(id=id, classes=classes, disabled=disabled, name=name)
        self._init_camera_position = initial_cam_position

    def compose(self):
        yield Label("Position:")
        yield Vector3Selector(
            minvalue=(-10, -10, -10),
            maxvalue=(10, 10, 10),
            initial_value=self._init_camera_position,
            id="input_camera_position",
        )

        yield Label("Angle: Yaw,Pitch")

        yield FloatSelector(
            -1200.0,
            1200.0,
            0.0,
            mouse_factor=3.0,
            button_factor=10.0,
            id="input_camera_yaw",
        )
        yield FloatSelector(
            -110.0,
            110,
            0.0,
            mouse_factor=3.0,
            button_factor=10.0,
            id="input_camera_pitch",
        )

        yield Label("Projection: Fov,min/max depth, factor")
        yield FloatSelector(
            30, 130, 50, mouse_factor=1.0, button_factor=1.0, id="input_camera_fov"
        )
        yield FloatSelector(0.00, 20, 0.2, 0.01, 0.1, id="input_camera_mindepth")
        yield FloatSelector(10, 1000, 100.0, id="input_camera_maxdepth")
        yield FloatSelector(
            0.3,
            3.5,
            1.8,
            mouse_factor=0.1,
            button_factor=0.1,
            id="input_character_factor",
        )

    # async def on_event(self,event):
    #    await super().on_event(event)
    #    if not isinstance(event,(events.MouseEvent,events.Compose,events.Mount,events.Resize,events.Show,events.Unmount)):
    #        if not isinstance(event,(events.Enter,events.Leave,events.DescendantBlur,events.DescendantFocus)):
    #            print("")
    def on_float_selector_changed(self, event: FloatSelector.Changed) -> None:
        proj_ids = [
            "input_camera_fov",
            "input_camera_mindepth",
            "input_camera_maxdepth",
            "input_character_factor",
        ]

        rots_ids = ["input_camera_yaw", "input_camera_pitch"]

        if event.input.id in proj_ids:
            event.bubble = False
            v = [self.query_one(f"#{wid}").current_value for wid in proj_ids]
            self.post_message(self.ProjectionChanged(self, v))

        elif event.input.id in rots_ids:
            event.bubble = False
            v = [self.query_one(f"#{wid}").current_value for wid in rots_ids]
            self.post_message(self.OrientationChanged(self, v))
        else:
            raise Exception("must be an error ?!")

    def on_vector3selector_changed(self, event: Vector3Selector.Changed) -> None:
        if event.input.id == "input_camera_position":
            event.bubble = False
            self.post_message(CameraConfig.PositionChanged(self, event.value))

    def refresh_camera_position(
        self, position: tuple[float, float, float], no_events=True
    ):
        elem: Vector3Selector = self.query_one("#input_camera_position")
        x, y, z = position

        if no_events:
            elem._selector_list[0].current_value = x
            elem._selector_list[1].current_value = y
            elem._selector_list[2].current_value = z
        else:
            elem._selector_list[0].current_buffer = x
            elem._selector_list[1].current_buffer = y
            elem._selector_list[2].current_buffer = z

    def refresh_camera_rotation(self, attitude: tuple[float, float], no_events=True):
        yaw, pitch = attitude
        if no_events:
            self.query_one(f"#input_camera_yaw").current_value = yaw
            self.query_one(f"#input_camera_pitch").current_value = pitch


class RenderInfo(Widget, can_focus=False):
    DEFAULT_CSS = """

    RenderInfo{
        height:auto;
    }

    RenderInfo > Sparkline {
        margin: 1;
    }

    """

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(id=id, classes=classes, disabled=disabled, name=name)

    def compose(self) -> ComposeResult:

        keep_count = 50
        yield Label("Frame idx", id="frame_idx")
        yield Label("fps", id="timeinfo")
        yield Sparkline(
            [0] * keep_count, summary_function=mean, id="render_duration_sl"
        )

    def append_frame_duration(self, duration: float):
        spark: Sparkline = self.query_one(Sparkline)
        spark.data = spark.data[1:] + [duration]

        mean_dur_sec = mean(spark.data)

        if mean_dur_sec == 0.0:
            fps_render = float("nan")
        else:
            fps_render = 1.0 / mean_dur_sec

        l: Label = self.query_one("#timeinfo")
        l.update(f"Render: {(1000*mean(spark.data)):.2f} ms ({fps_render:.1f} rps)")

    def update_frame_count(self, frame_count: int):
        l: Label = self.query_one("#frame_idx")
        l.update(f"Frame: {frame_count}")
