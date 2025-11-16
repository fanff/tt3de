# -*- coding: utf-8 -*-

import glm
from textual.containers import Container
from textual.widgets import (
    Header,
    Static,
)
from textual.app import App, ComposeResult
from tt3de.asset_fastloader import MaterialPerfab
from tt3de.glm_camera import ViewportScaleMode
from tt3de.points import Point3D
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt_2dnodes import TT2DNode, TT2DPoints, TT2DRect
from tt3de.textual.widgets import CameraConfig2D, VisualViewportScaleModeSelector


class DemoContent(TT3DViewStandAlone):
    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

        self.root2Dnode = TT2DNode()
        self.root2Dnode.add_child(
            TT2DPoints(point_list=[Point3D(0.0, 0.0, 0)], material_id=1)
        )
        self.root2Dnode.add_child(
            TT2DPoints(point_list=[Point3D(1, 0.0, 0)], material_id=2)
        )
        self.root2Dnode.add_child(
            TT2DPoints(point_list=[Point3D(0.0, 1, 0)], material_id=3)
        )

        self.moving_point = TT2DPoints(point_list=[Point3D(0.2, 0.1, 0)], material_id=3)
        self.root2Dnode.add_child(self.moving_point)

        self.rect = TT2DRect(width=0.5, height=0.3, material_id=8)
        self.root2Dnode.add_child(self.rect)

        self.rc.append_root(self.root2Dnode)

    def update_step(self, delta_time: float):
        t = self.time_since_start() * 2
        x = glm.sin(t * 0.7)
        y = glm.cos(t * 1.3)
        self.moving_point.set_local_transform(glm.translate(glm.vec3(x, y, 0.0)))


class DebuggedView(Static):
    DEFAULT_CSS = """
    DebuggedView {
        layout: horizontal;
        height: 100%;
        }
    .someinfo {
        height: 100%;
        width: 1fr;
        border: solid red;
    }

    .tt3dview {
        height: 100%;
        width: 4fr;
    }
    """

    def compose(self) -> ComposeResult:
        self.democontent = DemoContent(classes="tt3dview")
        self.democontent.debugger_component = self
        self.cameraconfig = CameraConfig2D(
            init_camera_zoom=self.democontent.camera.zoom_2D,
            init_character_factor=self.democontent.camera.character_factor,
        )

        with Container(classes="someinfo"):
            yield self.cameraconfig
            yield VisualViewportScaleModeSelector(
                initial_value=self.democontent.camera.current_method
            )

        yield self.democontent

    def container_event(self, event):
        pass

    def on_camera_config2d_zoom_changed(self, event: CameraConfig2D.ZoomChanged):
        self.democontent.camera.set_zoom_2D(event.value)

    def on_camera_config2d_character_factor_changed(
        self, event: CameraConfig2D.CharacterFactorChanged
    ):
        self.democontent.camera.set_character_factor(event.value)

    def on_visual_viewport_scale_mode_selector_scale_mode_changed(
        self, event: VisualViewportScaleModeSelector.ScaleModeChanged
    ):
        self.democontent.camera.set_viewport_scale_mode(ViewportScaleMode(event.value))


class CameraTest2D(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DebuggedView()


if __name__ == "__main__":
    app = CameraTest2D()
    app._disable_tooltips = True
    app.run()
