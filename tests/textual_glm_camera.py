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
from tt3de.glm.pyglmtexture import GLMMesh3D, GLMNode3D
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



class GLMTester(TT3DView):
    use_native_python = False


    def __init__(self):
        super().__init__()

    def initialize(self):
        meshclass = GLMMesh3D


        texture3 = fast_load("models/cubetest3.bmp")
        

        self.root3d_node = GLMNode3D()

        # adding one cube

        m = fast_load("models/cube.obj",meshclass)
        m.material_id = 1


        cube1node = GLMNode3D()
        cube1node.elems.append(m)
        cube1node.local_transform = glm.translate(glm.vec3(0.0,5.0,0.0))
        self.root3d_node.elems.append(cube1node)
        
        # adding a second cube 
        m2:GLMMesh3D = fast_load("models/cube.obj",meshclass)
        m2.material_id = 1
        
        cube2node = GLMNode3D()
        cube2node.local_transform = glm.translate(glm.vec3(5.0,0.0,0.0))
        cube2node.elems.append(m2)

        self.root3d_node.elems.append(cube2node)
        

        manynodes =  GLMNode3D()

        manynodes.local_transform = glm.scale(glm.vec3(20,20, 0 ))
        for i in range(1):
            for j in range(1):
                awall_node = GLMNode3D()
                awall_node.local_transform = glm.translate(glm.vec3(i-0.5,j-.5, 0.01 ))
                pref = prefab_mesh_single_triangle(GLMMesh3D)
                pref.material_id = 2
                awall_node.elems.append(pref)
                manynodes.elems.append( awall_node )

        #cube2node.elems.append(manynodes)
        self.root3d_node.elems.append(manynodes)


        
        
        
        
        
        
        
        # add the root 
        self.rc.append(self.root3d_node)

        # this won't work because bellow the cameraConfig 
        # widget will update the camera at the init time
        #self.camera.move_at(glm.vec3(5,  0, 5))
        #self.camera.point_at(glm.vec3(0.0, 0, 0))

        #self.root2Dnode = GLM2DNode() 

        #meshtext = fast_load("models/test_screen32.bmp",GLM2DMappedTexture)
        #for i in range(3):
        #    a2dnode =GLM2DNode() 
        #    a2dmesh:GLM2DMesh =Prefab2D.unitary_square(GLM2DMesh)
        #    a2dmesh.texture = meshtext
        #    a2dnode.elements.append(a2dmesh)
        #    a2dnode.local_transform=glm.translate(glm.vec2(2*i,0.0))
        #    self.root2Dnode.elements.append(a2dnode)

        #self.rc.append(self.root2Dnode)
        
        self.reftime = time()
        self.write_debug_inside = True
        self.capture_mouse_events=False


    def update_step(self, timediff):
        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)
        ts = self.reftime-time()

        tsfactor = 0.5

        rot = ts*tsfactor

        #*glm.rotate(rot)*glm.scale(glm.vec2(.2,.2))
        

        atransform = glm.translate(glm.vec3(.5,.5,.5))*glm.rotate(rot*(1+1),glm.vec3(1,0,0))

        #self.root3d_node.local_transform = atransform


        scalefactor = 2.0

        scalevalue = math.cos(ts*scalefactor)+1.7
        self.root3d_node.elems[0].local_transform = glm.scale(glm.vec3(scalevalue,scalevalue,scalevalue))

        

    def post_render_step(self):
        rinfo:RenderInfo = self.parent.query_one("RenderInfo")
        rinfo.append_frame_duration(self.last_frame_data_info.get("tsrender_dur", 0))
        rinfo.update_frame_count(self.frame_idx)
        cc:CameraConfig = self.parent.query_one("CameraConfig")
        cc.refresh_camera_position((self.camera.pos.x,self.camera.pos.y,self.camera.pos.z))
        cc.refresh_camera_rotation((math.degrees(self.camera.yaw),math.degrees(self.camera.pitch)))

    
    async def on_event(self, event: events.Event):
        await super().on_event(event)

        match event.__class__:
            case events.Leave:
                info_box: Static = self.parent.query_one(".lastevent")
                info_box.update(f"leaving!")
            case _:
                info_box: Static = self.parent.query_one(".lastevent")
                info_box.update(f"{event.__class__}: \n{str(event)}")
 
class Content(Static):
    def compose(self) -> ComposeResult:
        
        with Container(classes="someinfo"):
            yield Static("", classes="lastevent")
            yield RenderInfo()
            yield CameraConfig((0.0,0.0,3.0))
                

        yield GLMTester()

            
    def on_camera_config_position_changed(self,event:CameraConfig.PositionChanged):
        x,y,z = event.value
        viewelem:GLMTester = self.query_one("GLMTester")
        viewelem.camera.move_at(glm.vec3(x,y,z))
    def on_camera_config_orientation_changed(self,event:CameraConfig.OrientationChanged):
        viewelem:GLMTester = self.query_one("GLMTester")
        y,p = event.value
        viewelem.camera.set_yaw_pitch(math.radians(y),math.radians(p))

    def on_camera_config_projection_changed(self,event:CameraConfig.ProjectionChanged):
        viewelem:GLMTester = self.query_one("GLMTester")

        fov,dist_min,dist_max,charfactor = event.value
        viewelem.camera.set_projectioninfo(math.radians(fov),dist_min,dist_max,charfactor)

class Demo3dView(App):
    DEFAULT_CSS = """
    Content {
        layout: horizontal;
        height: 100%;
        border: solid red;
    }
    GLMTester {
        height: 100%;
        width: 5fr;
    }
    .someinfo {
        height: auto;
        width: 1fr;
        border: solid red;
    }
    
    """

    def compose(self) -> ComposeResult:

        yield Header()
        yield Content()

    async def on_mount(self):
        pass


async def run():
    pass


if __name__ == "__main__":

    app = Demo3dView()
    app._disable_tooltips=True
    app.run()
