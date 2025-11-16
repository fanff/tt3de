# -*- coding: utf-8 -*-

from textual.containers import Container
from textual.widgets import (
    Header,
    Static,
)
from textual.app import App, ComposeResult
from tt3de.asset_fastloader import MaterialPerfab
from tt3de.textual_standalone import TT3DViewStandAlone

from tt3de.tt3de import find_glyph_indices_py, materials
from tt3de.tt_2dnodes import TT2DNode, TT2DRect
from tt3de.textual.widgets import (
    CameraConfig2D,
    CameraLoc2D,
    VisualViewportScaleModeSelector,
)


class DemoContent(TT3DViewStandAlone):
    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

        back_tex0 = self.rc.material_buffer.add_material(materials.TexturedBackPy(0))
        glyph = self.rc.material_buffer.add_material(
            materials.StaticGlyphPy(find_glyph_indices_py("#"))
        )

        mat_idx = self.rc.material_buffer.add_material(
            materials.ComboMaterialPy.from_list([glyph, back_tex0])
        )
        self.root2Dnode = TT2DNode()

        self.rect = TT2DRect(width=0.5, height=0.3, material_id=mat_idx)
        self.root2Dnode.add_child(self.rect)

        self.rc.append_root(self.root2Dnode)

    def update_step(self, delta_time: float):
        pass


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
        self.cameraconfig = CameraConfig2D(camera=self.democontent.camera)
        self.modeinfo = VisualViewportScaleModeSelector(camera=self.democontent.camera)
        self.cloc = CameraLoc2D(camera=self.democontent.camera)
        with Container(classes="someinfo"):
            yield self.cameraconfig
            yield self.modeinfo
            yield self.cloc

        yield self.democontent

    def container_event(self, event):
        pass

    def has_just_rendered(self):
        self.cameraconfig.refresh_content()
        self.modeinfo.refresh_content()
        self.cloc.refresh_camera_position()


class Material_Test(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DebuggedView()


if __name__ == "__main__":
    app = Material_Test()
    app._disable_tooltips = True
    app.run()
