import math
from statistics import mean
from textwrap import dedent
from time import monotonic, time
from typing import Sequence
from textual.screen import Screen
import glm

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
from textual.validation import Function, Number, ValidationResult, Validator

from tt3de.asset_fastloader import MaterialPerfab, Prefab2D, fast_load


from tt3de.prefab3d import Prefab3D
from tt3de.textual.widgets import (
    CameraConfig,
    EngineLog,
    FloatSelector,
    RenderInfo,
    RustRenderContextInfo,
    Vector3Selector,
)
from tt3de.textual_widget import TT3DView

from tt3de.tt_2dnodes import TT2DMesh, TT2DNode, TT2Polygon
from tt3de.tt_3dnodes import TT3DNode


class GLMTester(TT3DView):
    use_native_python = False

    def __init__(self):
        super().__init__()

    def initialize(self):
        
        # prepare a bunch of material
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        # create a root 3D node 
        self.root3Dnode = TT3DNode()


        tri = Prefab3D.unitary_square()
        tri.material_id = 8
        tri.local_transform = glm.translate(
            glm.vec3(-1.1,1,0)
        )
        self.root3Dnode.add_child(tri)

        poly = Prefab3D.unitary_circle(5)
        poly.material_id = 8
        poly.local_transform = glm.translate(
            glm.vec3(1.1,0,0)
        )
        self.root3Dnode.add_child(poly)

        poly = Prefab3D.unitary_circle(12)
        poly.material_id = 8
        poly.local_transform = glm.translate(
            glm.vec3(1.1,1.1,0)
        )
        self.root3Dnode.add_child(poly)


        poly = Prefab3D.unitary_circle(24)
        poly.material_id = 8
        poly.local_transform = glm.translate(
            glm.vec3(1.1,2.1,0)
        )
        self.root3Dnode.add_child(poly)


        # final append
        self.rc.append(self.root3Dnode)

        # setup a time reference, to avoid trigonometry issues
        self.reftime = time()

    def update_step(self, timediff):
        pass

    def post_render_step(self):
        pass




class ContentScreen(Screen):
    def compose(self) -> ComposeResult:
        yield GLMTester()

    def on_camera_config_projection_changed(
        self, event: CameraConfig.ProjectionChanged
    ):
        viewelem: GLMTester = self.query_one("GLMTester")

        fov, dist_min, dist_max, charfactor = event.value
        viewelem.camera.set_projectioninfo(
            math.radians(fov), dist_min, dist_max, charfactor
        )


class Demo3dView(App):
    DEFAULT_CSS = """
    Content {
        layout: horizontal;
        height: 100%;
        
    }
    TT3DView {
        
        height: 100%;
        width: 4fr;
    }

    .someinfo {
        height: 100%;
        width: 1fr;
        border: solid red;
    }
    
    """
    SCREENS = {"cscreen": ContentScreen()}

    async def on_mount(self) -> None:
        await self.push_screen("cscreen")

if __name__ == "__main__":

    app = Demo3dView()
    app._disable_tooltips = True
    app.run()
