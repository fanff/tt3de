
import array
from math import exp
import math
from typing import Iterable, List, Tuple
from tt3de.richtexture import ImageTexture, Segmap
from tt3de.tt3de import (
    Camera,
    Drawable3D,
    FPSCamera,
    Line3D,
    Mesh3D,
    Node3D,
    PPoint2D,
    Point2D,
    Point3D,
    PointElem,
    TextureCoordinate,
    TextureTT3DE,
    Triangle3D,
)
from rich.color import Color
from rich.style import Style
from rich.text import Segment
from textual.strip import Strip

import glm
from glm import array as glma, vec4
from glm import quat 
from glm import vec3

def quat_from_euler(x, y, z):
    return quat(vec3(x,y,z))

def quat_from_axis_angle(axis, angle):
    half_angle = angle / 2
    sin_half_angle = math.sin(half_angle)
    return quat(
        math.cos(half_angle),
        axis[0] * sin_half_angle,
        axis[1] * sin_half_angle,
        axis[2] * sin_half_angle,
    )
def mat_from_axis_angle(axis, angle):
    return glm.rotate(angle, axis) 

GLMTexturecoord = glm.vec2



class GLMCamera():
    def __init__(self, pos: Point3D, screen_width: int = 100, screen_height: int = 100, 
                 fov_radians=70, 
                 dist_min=1, 
                 dist_max=100,
                 character_factor=1.8):
        self.pos = glm.vec3(pos.x, pos.y, pos.z)

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.pitch = 0
        self.yaw = 0

        self.fov_radians=fov_radians
        self.dist_min=dist_min
        self.dist_max=dist_max
        self.character_factor = character_factor


        self.perspective:glm.mat4 = glm.mat4(1.0)
        self._rotation:glm.mat4 = glm.mat4(1.0)
        self.update_rotation()
        self.update_perspective()

    def recalc_fov_h(self, w, h):
        if self.screen_width!=w or self.screen_height!=h:
            self.screen_width = w
            self.screen_height = h
            self.update_perspective()

    def set_projectioninfo(self, fov_radians:float=None, 
                 dist_min:float=None, 
                 dist_max:float=None,
                 character_factor:float=None):
        
        if fov_radians is not None:
            self.fov_radians=fov_radians
        if dist_min is not None:
            self.dist_min=dist_min
        if dist_max is not None:
            self.dist_max=dist_max
        if character_factor is not None:
            self.character_factor=character_factor
            
        self.update_perspective()


    def update_perspective(self):
        self.perspective = glm.perspectiveFovZO(self.fov_radians, self.screen_width, self.screen_height*self.character_factor, self.dist_min, self.dist_max)

        #self.perspective = glm.orthoZO(-self.screen_width, self.screen_width, -self.screen_height, self.screen_height, 1, 100.0)
    
    def move(self, delta:  glm.vec3):
        self.pos += delta
        self.update_rotation()


    def move_at(self, pos: glm.vec3):
        self.pos = pos
        self.update_rotation()

    def move_side(self, dist: float):
        self.pos -= glm.cross(self.direction_vector(), glm.vec3(0,1,0))*dist
        self.update_rotation()


    def move_forward(self, dist: float):
        self.pos += self.direction_vector()*dist
        self.update_rotation()


    def rotate_left_right(self, angle: float):
        self.yaw -= angle
        self.update_rotation()

    def rotate_up_down(self, angle: float):
        self.pitch = self.pitch + angle
        self.update_rotation()


    def set_yaw_pitch(self,yaw:float,pitch:float):
        self.yaw = yaw
        self.pitch = pitch
        self.update_rotation()

    def update_rotation(self):
        # pitch is around x axis , yaw is around y axis
        self._rotation = glm.rotate(self.yaw, glm.vec3(0,1,0))*glm.rotate(self.pitch, glm.vec3(1,0,0))

        self._model= glm.inverse(self._rotation)*glm.translate(-self.pos)

    def project(self, point: glm.vec3, perspective:glm.mat4x4) -> glm.vec3:
        

        # transformation to gtive to the model
        #model = glm.mat4(1.0)

        view = glm.translate(-self.pos)
        #p = (perspective*glm.inverse(model)*view*point)
        #return p
        return glm.projectZO( point, glm.inverse(self._rotation)*view, perspective, glm.vec4(0,0,1,1))
        


    def point_at(self, target:glm.vec3):
        direction = target - self.pos
        self.yaw = glm.atan(direction.x, direction.z)#math.atan2(direction.x, direction.z)
        self.pitch = glm.atan(-direction.y, glm.length(direction.xz))

        self.update_rotation()
    def direction_vector(self) -> glm.vec3:
        # directional vector extracted from the matrix
        return self._rotation*glm.vec3(0,0,1)
        
    def __str__(self):
        return f"GLMCamera({self.pos,self.direction_vector()},yaw={self.yaw},pitch={self.pitch})"

    def __repr__(self):
        return str(self)





class GLMMesh3D(Mesh3D):
    def __init__(self):
        self.vertices: List[Point3D] = []
        self.texture_coords: List[List[GLMTexturecoord]] = [[] for _ in range(8)]
        self.normals: List[Point3D] = []
        self.triangles: List[Triangle3D] = []
        self.texture:ImageTexture=None

    def cache_output(self,segmap):
        self.glm_verticesv4 = glma([vec4(p.x,p.y,p.z,1) for p in self.vertices])
        self.glm_vertices = glma([vec3(p.x,p.y,p.z) for p in self.vertices])
        self.glm_normals = glma([vec3(t.normal.x,t.normal.y,t.normal.z) for t in self.triangles])
        self.texture_coords = [[GLMTexturecoord(p.x,p.y) for p in coordlayer] for coordlayer in self.texture_coords]
        self.texture.cache_output(segmap)

        self.glm_uvmap = [[[glm.vec2(uv.x,uv.y) for uv in uvlayer] for uvlayer in t.uvmap] for t in self.triangles]


    def render_point(self,weight_to_vertex:glm.vec3,vertex_idx:tuple[int,int,int],face_idx:int):

        uv1,uv2,uv3 = self.glm_uvmap[face_idx][0]

        uvcoord = (weight_to_vertex.x*uv1 +
                    weight_to_vertex.y*uv2+
                    weight_to_vertex.z*uv3)

        return self.texture.unshaded_render(uvcoord)
        
        #
        #yield glm.vec2(px,py),glm.vec4(uvpoint.x,uvpoint.y,ddot_prod,appdepth)


    def proj_vertices(self, camera: GLMCamera,perspective_matrix, screen_width, screen_height) :
        
        
        screeninfo = glm.vec4(0,0,1,1)
        
        #def projfunction (v:glm.vec3):
        #    return glm.projectZO( v, modelmatrix , perspective_matrix, screeninfo)
        #proj_vertices = self.glm_vertices.map(projfunction)


        proj_vertices = ([glm.projectZO( v, camera._model , perspective_matrix, screeninfo) for v in self.glm_vertices])
        #quicktransofr = perspective_matrix*modelmatrix
        #proj_vertices = self.glm_verticesv4*quicktransofr
        #glm.projectZO( self.glm_vertices, modelmatrix , perspective_matrix, screeninfo)
        
        #proj_vertices = self.glm_vertices

        
        vert_camera = self.glm_vertices-camera.pos
        vert_camera_dist = vert_camera.map(glm.length)
        
        
        #vert_camera_dist = [0]*len(self.glm_vertices)
        for pa,pb,pc in self.triangles_vindex:
            rp1 = proj_vertices[pa]
            rp2 = proj_vertices[pb]
            rp3 = proj_vertices[pc]

            dist1 = vert_camera_dist[pa]
            dist2 = vert_camera_dist[pb]
            dist3 = vert_camera_dist[pc]

            
            
            
            #yield ((rp1,vec4(0.0,0.0,0.0,dist1)),
            #       (rp2,vec4(0.0,0.0,0.0,dist2)),
            #       (rp3,vec4(0.0,0.0,0.0,dist3)))
            yield ( (rp1,(dist1)),
                    (rp2,(dist2)),
                    (rp3,(dist3)))
            

    def draw(self, camera:GLMCamera, screen_width, screen_height) -> Iterable[tuple[vec3,vec3,tuple]]:
        
        perspective_matrix = camera.perspective
        screeninfo = glm.vec4(0,0,screen_width,screen_height)
        proj_vertices = ([glm.projectZO( v, camera._model , perspective_matrix, screeninfo) for v in self.glm_vertices])
        
        vert_camera = (self.glm_vertices-camera.pos)
        vert_camera_dist = vert_camera.map(glm.length)

        # rotate normals
        # using self.glm_normals 
        rnormals = [glm.inverse(camera._model)*n for n in self.glm_normals]

        cam_dir = camera.direction_vector()

        for (triangle_idx,(pa,pb,pc)),tnormal in zip(enumerate(self.triangles_vindex),rnormals):
            
            rp1 = proj_vertices[pa]
            rp2 = proj_vertices[pb]
            rp3 = proj_vertices[pc]

            facing = glm.dot(tnormal,cam_dir )
            #dotp1 = glm.dot(rnormals[pa],cam_dir )
            #dotp2 = glm.dot(rnormals[pb],cam_dir )
            #dotp3 = glm.dot(rnormals[pc],cam_dir )

            # (dotp1<0 or dotp2<0 or dotp3<0) or 
            # (rp1.z<1 and rp2.z<1 and rp3.z<0)or ()
            # rp1.z<1 and rp2.z<1 and rp3.z<0)or (
            # dotp1>0 or dotp2>0 or dotp3>0) or (
            #c = (facing>0 ) or (
            #    rp1.x<=0 and rp2.x <=0 and rp3.x <= 0) or (
            #    rp1.y<=0 and rp2.y <=0 and rp3.y <= 0) or (
            #    rp1.x>sw and rp2.x >sw and rp3.x >sw) or (
            #    rp1.y>sh and rp2.y >sh and rp3.y >sh)
            #print(f"triangle {pa},{pb},{pc} c={c}")
            #print(f"rps {rp1},{rp2},{rp3}")
            #print(f"dots {dotp1},{dotp2},{dotp3}")

            

            if facing<0 and  (rp1.z>0 and rp2.z>0 and rp3.z>0) and (rp1.z<10 and rp2.z<10 and rp3.z<10):
                
                
                # in screen space as float
                #p1f = (rp1*glm.vec3(screen_width,screen_height,vert_camera_dist[pa]))-glm.vec3(0.0,0.0,1.0)
                #p2f = (rp2*glm.vec3(screen_width,screen_height,vert_camera_dist[pb]))-glm.vec3(0.0,0.0,1.0)
                #p3f = (rp3*glm.vec3(screen_width,screen_height,vert_camera_dist[pc]))-glm.vec3(0.0,0.0,1.0)
                

                


                bd = (((rp2.y - rp3.y)*
                (rp1.x-rp3.x))  +
                ((rp3.x - rp2.x) *
                (rp1.y - rp3.y)))

                if abs(bd) < 0.0001:
                    continue
                
                mins = glm.max(vec3(0.0,0.0,0.0),glm.min(rp1,rp2,rp3))
                maxes = glm.min(vec3(screen_width-1,screen_height-1,0.0),glm.max(rp1,rp2,rp3))


                px = mins.x
                py = mins.y
                while px <= maxes.x:
                    pxi = round(px)
                    
                    while py <= maxes.y:
                        pyi = round(py)
                        #passyield glm.ivec2(px,py),glm.vec4(0.0,0.0,0.0,0.0)
                        # w1 = (((p2f.y - p3f.y) * (px - p3f.x)) + ((p3f.x - p2f.x) * (py - p3f.y)))/bd
                        # w2 = (((p3f.y - p1f.y) * (px - p3f.x) + (p1f.x - p3f.x) * (py - p3f.y)))/bd
                        # w3 = 1 - w1 - w2
                        w1 = (((rp2.y - rp3.y) * (px - rp3.x)) + ((rp3.x - rp2.x) * (py - rp3.y)))/bd
                        w2 = (((rp3.y - rp1.y) * (px - rp3.x) + (rp1.x - rp3.x) * (py - rp3.y)))/bd
                        w3 = 1 - w1 - w2
                        if w1 >= 0 and w2 >= 0 and w3 >= 0:

                            dist1 = vert_camera_dist[pa]
                            dist2 = vert_camera_dist[pb]
                            dist3 = vert_camera_dist[pc]


                            #appxp = rp1*w1 + rp2*w2 + rp3*w3
                            appdepth = w1 * dist1 + w2 * dist2 + w3 * dist3

                            yield (pxi,pyi,appdepth),vec3(w1,w2,w3),(pa,pb,pc),triangle_idx

                            #continue
                            #ddot_prod = w1 * dotp1 + w2 * dotp2 + w3 * dotp3
                            ## calculate uv vector 
                            #uv1 = self.texture_coords[0][pa]
                            #uv2 = self.texture_coords[0][pb]
                            #uv3 = self.texture_coords[0][pc]
                            #uvpoint = uv1*w1 + uv2*w2 + uv3*w3
                            #
                            #yield glm.vec2(px,py),glm.vec4(uvpoint.x,uvpoint.y,ddot_prod,appdepth)

                        py += 1
                    px += 1
                    py = mins.y



class GLMRenderContext:

    LINE_RETURN_SEG = Segment("\n",Style(color="white"))
    EMPTY_SEGMENT = Segment(" ",Style(color="white"))

    def __init__(self, screen_width, screen_height):
        self.elements: List[GLMMesh3D] = []

        self.depth_array: array[float] = array.array("f", [])
        self.canvas_array: array[int] = array.array("i", [])

        self.screen_width: int = screen_width
        self.screen_height: int = screen_height

        self.setup_canvas()
        self.segmap = Segmap().init()
        self.split_map = dict[int:object]

    def setup_segment_cache(self,console):
        self.split_map = self.segmap.to_split_map(console)

    def setup_canvas(self):
        w, h = self.screen_width, self.screen_height
        self.canvas = []
        self.depth = []

        self.empty_depth_array = array.array("f", [float("inf")] * (w * h))
        self.depth_array = self.empty_depth_array.__copy__()
        self.empty_canvas_array = array.array("i", [0] * (w * h))
        self.canvas_array = self.empty_canvas_array.__copy__()

    def update_wh(self, w, h):
        if w != self.screen_width or h != self.screen_height:
            self.screen_width = w
            self.screen_height = h
            self.setup_canvas()

    def clear_canvas(self):
        self.depth_array = self.empty_depth_array.__copy__()
        self.canvas_array = self.empty_canvas_array.__copy__()

    def render(self, camera: GLMCamera):

        for elemnt in self.elements:

            pixel_iterator = elemnt.draw(camera, self.screen_width, self.screen_height)
            for (pxi,pyi,appdepth),vertex_weight,vertex_idx,triangle_idx in pixel_iterator:
                aidx = (pyi * self.screen_width) + pxi
                currdepth = self.depth_array[aidx]
                if appdepth < currdepth:
                    # self.canvas[p.y][p.x] = p.render_pixel(txt)
                    self.canvas_array[aidx] = elemnt.render_point(vertex_weight,vertex_idx,triangle_idx)
                    self.depth_array[aidx] = appdepth
                
    def iter_canvas(self) -> Iterable[Segment]:
        for idx, i in enumerate(self.canvas_array):
            if idx > 0 and (idx % self.screen_width == 0):
                yield self.LINE_RETURN_SEG
            yield self.segmap[i]

    def iter_segments(self) -> Iterable[List[Segment]]:
        currentLine = []
        for idx, i in enumerate(self.canvas_array):

            if idx > 0 and (idx % self.screen_width == 0):
                yield currentLine
                currentLine = []
            currentLine.append( self.segmap[i] )
            #yield self.segmap[i]
        yield currentLine

    def write_text(self, txt: str, x:int=0, y:int=0):
        for idx, c in enumerate(txt):
            if c.isprintable():
                ordc = ord(c)
                if ordc in self.segmap:
                    aidx = (self.screen_height - y - 1) * self.screen_width + idx + x
                    self.canvas_array[aidx] = ordc

    def append(self, elem: Drawable3D):
        elem.cache_output(self.segmap)
        self.elements.append(elem)

    def extend(self, elems: List[Drawable3D]):
        for e in elems:
            self.append(e)
