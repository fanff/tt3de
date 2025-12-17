# -*- coding: utf-8 -*-

from tt3de.render_context_rust import RustRenderContext
from tt3de.textual.buffer_views import BufferViewPanel
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.textual.widgets import (
    CameraConfig,
    CameraConfig2D,
    CameraLoc2D,
    RenderInfo,
    VisualViewportScaleModeSelector,
)
from textual.containers import Container, ScrollableContainer
from textual.widgets import Static, Button, Label, Checkbox, Collapsible
from textual.app import ComposeResult

from tt3de.tt3de import DrawingBufferPy


class FrameBufferConfig(Static):
    DEFAULT_CSS = """
    FrameBufferConfig {
        height: auto;
        width: 100%;
        }
    """

    def __init__(
        self,
        rc: RustRenderContext,
        content="",
        *,
        expand=False,
        shrink=False,
        markup=True,
        name=None,
        id=None,
        classes=None,
        disabled=False,
    ):
        super().__init__(
            content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.rc = rc
        self.db: DrawingBufferPy = rc.drawing_buffer

    def compose(self) -> ComposeResult:
        self.width_label = Label(f"Init Width: {self.db.get_col_count()}")
        self.height_label = Label(f"Init Height: {self.db.get_row_count()}")
        self.aspect_label = Label("Aspect Ratio: 1.0")
        self.cache_size_label = Label(f"Cache Size: {self.db.get_cache_size()}")

        yield self.width_label
        yield self.height_label
        yield self.cache_size_label
        yield self.aspect_label

        self.flip_x_checkbox = Checkbox(label="Flip X", value=self.db.get_flip_x())
        self.flip_y_checkbox = Checkbox(label="Flip Y", value=self.db.get_flip_y())
        yield self.flip_x_checkbox
        yield self.flip_y_checkbox

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox == self.flip_x_checkbox:
            self.db.set_flip_x(event.value)
        elif event.checkbox == self.flip_y_checkbox:
            self.db.set_flip_y(event.value)
        else:
            raise Exception("Unknown checkbox changed")

    def refresh_content(self):
        self.db: DrawingBufferPy = self.rc.drawing_buffer
        assert isinstance(self.db, DrawingBufferPy)
        self.flip_x_checkbox.value = self.db.get_flip_x()
        self.flip_y_checkbox.value = self.db.get_flip_y()

        col = self.db.get_col_count()
        row = self.db.get_row_count()
        self.width_label.content = f"Width: {col}"
        self.height_label.content = f"Height: {row}"

        aspect = float(col) / (row) if row != 0 else 0
        aspectcf = float(col) / (row * 1.8) if row != 0 else 0
        self.aspect_label.content = f"Aspect Ratio: {aspect:.2f} ({aspectcf:.2f} cf)"

        self.cache_size_label.content = f"Cache Size: {self.db.get_cache_size()}"


class DebuggedView(Static):
    DEFAULT_CSS = """
    DebuggedView {
        layout: horizontal;
        height: 100%;
        }
    .config_panel {
        margin-top: 3;
        height: 100%;
        width: 1fr;
        display: block;
    }

    .buffers {
        layout: vertical;
        width: 4fr;
        height: 100%;
    }

    .demo_bottom {
        max-height: 20;
        width: 100%;
    }
    .tt3dview {

        height: 4fr;
        width: 100%;
    }

    .debugged_title {
        position: absolute;
        offset: 0 0;
        max-width: 5;
    }
    """

    def __init__(
        self,
        content_object: TT3DViewStandAlone,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.democontent: TT3DViewStandAlone = content_object
        self.democontent.debugger_component = self

    def compose(self) -> ComposeResult:
        self.democontent.add_class("tt3dview")

        self.cameraconfig = CameraConfig2D(camera=self.democontent.camera)
        self.modeinfo = VisualViewportScaleModeSelector(camera=self.democontent.camera)
        self.cloc = CameraLoc2D(camera=self.democontent.camera)
        self.render_info = RenderInfo(self.democontent)
        self.camera3dconfig = CameraConfig(camera=self.democontent.camera)
        self.framebufferconfig = FrameBufferConfig(self.democontent.rc)
        with ScrollableContainer(classes="config_panel"):
            with Collapsible(
                classes="collapse_render", title="Render Info", collapsed=False
            ):
                yield self.render_info
            with Collapsible(title="2D Camera Config"):
                yield self.cameraconfig
                yield self.modeinfo
                yield self.cloc
            with Collapsible(title="3D Camera Config"):
                yield self.camera3dconfig

            with Collapsible(title="Framebuffer Config"):
                yield self.framebufferconfig

        with Container(classes="buffers"):
            yield self.democontent
            with Collapsible(classes="demo_bottom"):
                self.bvp = BufferViewPanel(rc=self.democontent.rc)
                yield self.bvp

        yield Button("<", classes="debugged_title", id="config_toggle_button")

    def container_event(self, event):
        pass

    def has_just_rendered(self):
        self.cameraconfig.refresh_content()
        self.modeinfo.refresh_content()
        self.cloc.refresh_camera_position()
        self.bvp.refresh_content()
        self.render_info.refresh_content(self.democontent.frame_timings)
        self.framebufferconfig.refresh_content()

    def on_button_pressed(self, event: Button.Pressed):
        if "config_toggle_button" == event.button.id:
            config_panel = self.query_one(".config_panel")
            if config_panel.styles.display == "none":
                config_panel.styles.display = "block"
                event.button.label = "<"
            else:
                config_panel.styles.display = "none"
                event.button.label = ">"
