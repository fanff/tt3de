import math
from statistics import mean
from textwrap import dedent
from time import monotonic, time
from typing import Sequence

import glm

from context import tt3de
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
    Static,Input
)
from textual.validation import Function, Number, ValidationResult, Validator

from tt3de.asset_fastloader import Prefab2D, fast_load, prefab_mesh_single_triangle
from tt3de.glm.pyglmtexture import  GLM2DMappedTexture, GLM2DMesh, GLM2DNode, GLMMesh3D
from tt3de.richtexture import (
    DistGradBGShade,
    ImageTexture,
    RenderContext,
    StaticTexture,
    build_gizmo_arrows,
    get_cube_vertices,
)


from tt3de.textual.widgets import CameraConfig, FloatSelector, RenderInfo, Vector3Selector
from tt3de.textual_widget import TT3DView
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Node3D, Point3D, PointElem, Quaternion, Triangle3D




class GLMTester2(TT3DView):
    use_native_python = False


    def __init__(self):
        super().__init__()

    def initialize(self):
        pass
    def update_step(self, timediff):
        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)


class GLMTester(TT3DView):
    use_native_python = False


    def __init__(self):
        super().__init__()

    def initialize(self):
        texture3 = fast_load("models/cubetest3.bmp")
        
        meshclass = GLMMesh3D
        m = fast_load("models/cube.obj",meshclass)

        m.set_texture(texture3)
        self.rc.append(m)

        # this won't work because bellow the cameraConfig 
        # widget will update the camera at the init time
        #self.camera.move_at(glm.vec3(5,  0, 5))
        #self.camera.point_at(glm.vec3(0.0, 0, 0))

        self.root2Dnode = GLM2DNode() 

        meshtext = fast_load("models/test_screen32.bmp",GLM2DMappedTexture)
        for i in range(3):
            a2dnode =GLM2DNode() 

            a2dmesh:GLM2DMesh =Prefab2D.unitary_square(GLM2DMesh)
            a2dmesh.texture = meshtext

            a2dnode.elements.append(a2dmesh)

            a2dnode.local_transform=glm.translate(glm.vec2(2*i,0.0))

            self.root2Dnode.elements.append(a2dnode)



        self.rc.append(self.root2Dnode)

        self.reftime = time()
        self.write_debug_inside = True
        self.capture_mouse_events=False


    def update_step(self, timediff):
        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)
        ts = self.reftime-time()

        tsfactor = 2

        rot = ts*tsfactor

        #glm.translate(glm.vec2(.5,.5))*glm.rotate(rot)*glm.scale(glm.vec2(.2,.2))

        atransform =glm.scale(glm.vec2(2,2))* glm.translate(glm.vec2(-.5,-.5))

        for idx , e in enumerate(self.root2Dnode.elements):
            e.local_transform = glm.translate(glm.vec2(2*(idx),0.0))*glm.rotate(rot*(idx+1))*atransform
        self.root2Dnode.local_transform = glm.translate(glm.vec2(.5,.5))*glm.scale(glm.vec2(.2,.2))

        
class Content(Static):
    def compose(self) -> ComposeResult:
        yield GLMTester2()
        yield GLMTester()

            
class Demo3dView(App):
    DEFAULT_CSS = """
    Content {
        layout: horizontal;
        height: 100%;
        
    }
    TT3DView {
        
        height: 100%;
        width: 1fr;
    }

    GLMTester2 {
        
    }
    
    """

    def compose(self) -> ComposeResult:

        yield Header()
        yield Content()

if __name__ == "__main__":

    app = Demo3dView()
    app._disable_tooltips=True
    app.run()
