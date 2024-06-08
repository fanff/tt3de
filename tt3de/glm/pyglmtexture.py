
import array
import itertools
from math import exp
import math
from typing import Iterable, List, Tuple
from tt3de.asset_load import extract_palette
from tt3de.glm.triangle_clipping import Triangle, clip_triangle_in_planes, clipping_space_planes, extract_planes, is_front_facing
from tt3de.richtexture import ImageTexture, Segmap, StaticTexture, TextureAscii
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
from glm import array as glma, i32vec2, ivec2, ivec3, mat3, mat4, vec2
from glm import quat 
from glm import vec3, vec4

from tt3de.glm.c_triangle_raster import c_glm_triangle_render_to_buffer
from tt3de.glm.c_triangle_raster import iterate_pixel_buffer,TrianglesBuffer
from tt3de.glm.c_triangle_raster import TrianglesBuffer,apply_stage2
from tt3de.glm.c_triangle_raster import make_per_pixel_index_buffer,make_per_pixel_data_buffer,make_per_mesh_data_buffer,make_uniform_data_buffer


def p2d_tovec2(p:Point2D)->vec2:
    return vec2(p.x,p.y)

def p2d_uv_tomatrix(ps:tuple[Point2D,Point2D,Point2D])-> glm.mat3x2:
    return glm.mat3x2(p2d_tovec2(ps[0]),p2d_tovec2(ps[1]),p2d_tovec2(ps[2]))


def vec3_str(v)->str: 
    return f"vec3({v.x:.2f},{v.y:.2f},{v.z:.2f})"
def p3d_tovec3(p:Point3D)->vec3:
    return vec3(p.x,p.y,p.z)
def p3d_triplet_to_matrix(ps:tuple[Point3D,Point3D,Point3D])->mat3:
    a,b,c = ps

    return mat3(p3d_tovec3(a),p3d_tovec3(b),p3d_tovec3(c))

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


def clampi(x,minx,maxx):
    return min( maxx,max(x,minx))
GLMTexturecoord = glm.vec2
GLMTriangle=glm.mat3
IVEC2_YES = ivec2(1,1)
VEC3_YES = vec3(1.0,1.0,1.0)
VEC3_ZERO = vec3(0.0,0.0,0.0)




class GLMCamera():
    def __init__(self, pos: Point3D, screen_width: int = 100, screen_height: int = 100, 
                 fov_radians=math.radians(80), 
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

        w,h = self.screen_width, self.screen_height*self.character_factor


        self.perspective = glm.perspectiveFovZO((self.fov_radians*h)/w, w, h, self.dist_min, self.dist_max)



    def move(self, delta:  glm.vec3):
        self.pos += delta
        self.update_rotation()


    def move_at(self, pos: glm.vec3):
        self.pos = pos
        self.update_rotation()

    def move_side(self, dist: float):
        self.pos += glm.cross(self.direction_vector(), glm.vec3(0,1,0))*dist
        self.update_rotation()


    def move_forward(self, dist: float):
        self.pos -= self.direction_vector()*dist
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
        
        self.recalc_model_inverse()

    def recalc_model_inverse(self):
        self._model_inverse= glm.inverse(self._rotation)*glm.translate(-self.pos)

    def project(self, point: glm.vec3, perspective:glm.mat4x4,screen_info=glm.vec4(0,0,1,1)) -> glm.vec3:

        return glm.projectZO( point, self._model_inverse, perspective, screen_info)
        
    def point_at(self, target:glm.vec3):
        direction = target - self.pos
        self.yaw = glm.atan(direction.x, direction.z)#math.atan2(direction.x, direction.z)
        self.pitch = glm.atan(-direction.y, glm.length(direction.xz))

        self.update_rotation()

    def direction_vector(self) -> glm.vec3:
        # directional vector extracted from the matrix
        return glm.row(self._model_inverse,2).xyz
    
    def __str__(self):
        return f"GLMCamera({self.pos,self.direction_vector()},yaw={self.yaw},pitch={self.pitch})"

    def __repr__(self):
        return str(self)


def yvalue_from_adjoint_unprotected(adj_matrix:glm.mat3, side, x):
    a, b, c = glm.row(adj_matrix,side)
    alpha = -a/b
    intercept = -c/b
    return alpha * x + intercept


def line_equation_from_adjoint(adj_matrix:glm.mat3, side, x):
    a, b, c = glm.row(adj_matrix,side)

    CONST = 0.001
    if abs(b) > CONST : # Vertical line case
        alpha = -a/b
        intercept = -c/b
        return alpha * x + intercept



def glm_triangle_vertex_pixels(tri:GLMTriangle,screen_width,screen_height) -> Iterable[tuple[int,int]]:
    for i in range(3):
        point2f = glm.column(tri,i).xy
        xi = round(point2f.x)
        yi = round(point2f.y)
        if xi>=0 and xi<screen_width and yi>=0 and yi<screen_height:
            yield xi,yi




def glmtriangle_as_square(tri:glm.mat3,screen_width,screen_height) -> Iterable[tuple[int,int]]:
    adjoint = glm.determinant(tri)* glm.inverse(tri)
    
    xclamped = glm.clamp(glm.row(tri,0),0,screen_width)
    yclamped = glm.clamp(glm.row(tri,1),0,screen_height)
    minx = glm.min(xclamped)
    maxx = glm.max(xclamped)


    miny = glm.min(yclamped)
    maxy = glm.max(yclamped)
    minyi,maxyi = round(miny),round(maxy)

    maxxi= round(maxx)
    minxi = round(minx)
    for xi in range(minxi,maxxi+1):
        if xi == minxi or xi == maxxi:
            for yi in range(minyi,maxyi+1):
                yield (xi,yi)
        else:
            yield (xi,minyi)
            yield (xi,maxyi)

class GLMMesh3D(Mesh3D):
    def __init__(self):
        self.vertices: List[Point3D] = []
        self.texture_coords: List[List[GLMTexturecoord]] = [[] for _ in range(8)]
        self.normals: List[Point3D] = []
        self.triangles: List[Triangle3D] = []
        self.material_id: int = 0

    def cache_output(self,segmap):

        self.glm_vertices_4:glm.array[vec4] = glma([vec4(p.x,p.y,p.z,1.0) for p in self.vertices])

        self.glm_vertices = glma([vec3(p.x,p.y,p.z) for p in self.vertices])
        self.glm_normals = glma([vec3(t.normal.x,t.normal.y,t.normal.z) for t in self.triangles])

        uvfiller = [0.0]*42
        self.c_code_uvmap = [[list(itertools.chain(*[(1.0-uv.y,uv.x) for uv in uvlayer]))+uvfiller for uvlayer in t.uvmap] for t in self.triangles]
        #self.glm_uvmap = [[[glm.vec2(uv.x,uv.y) for uv in uvlayer] for uvlayer in t.uvmap] ]

    def proj_vertices(self, camera: GLMCamera,perspective_matrix, screen_width, screen_height) :
        screeninfo = glm.vec4(0,0,1,1)

        proj_vertices = ([glm.projectZO( v, camera._model_inverse , perspective_matrix, screeninfo) for v in self.glm_vertices])
        
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
            
    def draw(self,camera:GLMCamera,geometry_buffer , node_id = 0):
        
        screen_width, screen_height = camera.screen_width,camera.screen_height
        perspective_matrix = camera.perspective


        view_port_matrix = glm.scale(vec3(float(screen_width),float(screen_height),1.0)) * glm.translate(vec3(.5,.5,0.0))
        #in_view_space = [camera._model_inverse * glm.vec4(vertex, 1.0) for vertex in self.glm_vertices]
        view_space_vertices = [(camera._model_inverse) * vertex for vertex in self.glm_vertices_4]


        triangle_in_clip_space = [perspective_matrix * vertex for vertex in view_space_vertices]
        
        
        triangle_in_clip_space_divided = [vertex/vertex.w for vertex in triangle_in_clip_space] 
        #planes = extract_planes(perspective_matrix)
        plane_of_the_clip_space = clipping_space_planes()

        for triangle_idx,(v_idx1,v_idx2,v_idx3) in  enumerate(self.triangles_vindex):
            v_in_clip_space1 = triangle_in_clip_space_divided[v_idx1]
            v_in_clip_space2 = triangle_in_clip_space_divided[v_idx2]
            v_in_clip_space3 = triangle_in_clip_space_divided[v_idx3]

            v_in_view_space1 = view_space_vertices[v_idx1]
            v_in_view_space2 = view_space_vertices[v_idx2]
            v_in_view_space3 = view_space_vertices[v_idx3]


            
            v_in_clip_space_undiv_1 = triangle_in_clip_space[v_idx1]
            v_in_clip_space_undiv_2 = triangle_in_clip_space[v_idx2]
            v_in_clip_space_undiv_3 = triangle_in_clip_space[v_idx3]

            # perform a rejection test, if the triangle is like "all outside of the same plane. "
            a_triangle_in_clip_spance_not_divided = [v_in_clip_space_undiv_1,v_in_clip_space_undiv_2,v_in_clip_space_undiv_3]
            a_clip_space_test = []
            for vertice_in_clip_space in a_triangle_in_clip_spance_not_divided:
                sometest = [-vertice_in_clip_space.w < vertice_in_clip_space.x, 
                vertice_in_clip_space.x < vertice_in_clip_space.w ,
                -vertice_in_clip_space.w < vertice_in_clip_space.y ,
                vertice_in_clip_space.y < vertice_in_clip_space.w ,
                -vertice_in_clip_space.w < vertice_in_clip_space.z,
                vertice_in_clip_space.z < vertice_in_clip_space.w ]

                a_clip_space_test.append(sometest)
            clipe_space_rejection = [not(a_clip_space_test[0][plane_idx]) and not(a_clip_space_test[1][plane_idx]) and not(a_clip_space_test[2][plane_idx])
                                    for plane_idx in range(6)]
            # if any of the clip_space_rejection is True, it means that ALL vertices of the triangles are on the outside of this plane.
            if any(clipe_space_rejection):
                continue
            
            
            
            
            

            #if ((v_in_clip_space1.z<0 and v_in_clip_space2.z<0 and v_in_clip_space3.z<0) or (
            #    (v_in_clip_space1.x>1 and v_in_clip_space2.x>1 and v_in_clip_space3.x>1)) or (
            #    (v_in_clip_space1.x < -1 and v_in_clip_space2.x<-1 and v_in_clip_space3.x < -1)) or(
            #    (v_in_clip_space1.y>1 and v_in_clip_space2.y>1 and v_in_clip_space3.y>1)) or(
            #    (v_in_clip_space1.y < -1 and v_in_clip_space2.y<-1 and v_in_clip_space3.y<-1)
            #    )):
            #    continue
                
            triangle:Triangle = [v_in_clip_space1,
                                 v_in_clip_space2,
                                 v_in_clip_space3]

            clipped_triangles = clip_triangle_in_planes(triangle, plane_of_the_clip_space)
            for sub_triangle in clipped_triangles:
                #clipped_triangle_after_projection = [perspective_matrix * vertex for vertex in sub_triangle]
                
                    # lend in pixel coord
                    pixwin_coord = [view_port_matrix*(vertex) for vertex in sub_triangle] 

                    if is_front_facing(pixwin_coord):
                        a,b,c = pixwin_coord

                        a = [a.x,a.y,a.z]
                        b = [b.x,b.y,b.z]
                        c = [c.x,c.y,c.z]
                        

                        givenuv = list(self.c_code_uvmap[triangle_idx][0]  )
                        geometry_buffer.add_triangle_to_buffer(a,b,c,
                                            givenuv,   # uv list 
                                            node_id,  # node_id
                                            self.material_id)  # material_id
                    
        
        return

        for triangle_idx,(pa,pb,pc) in  enumerate(self.triangles_vindex):
            v1 = in_view_space[pa]
            v2 = in_view_space[pb]
            v3 = in_view_space[pc]
            triangles_to_draw = filter_clip_project(v1.xyz,v2.xyz,v3.xyz, camera.dist_min, glm.mat4(1.0)  ,perspective_matrix, screeninfo)

            for (rp1,rp2,rp3), normal in triangles_to_draw:
                if check_winding([rp1,rp2,rp3],vec3(0,0,-1.0)):
                    az = glm.unProject(rp1, glm.mat4(1.0)  ,perspective_matrix, screeninfo).z
                    bz = glm.unProject(rp2, glm.mat4(1.0)  ,perspective_matrix, screeninfo).z
                    cz = glm.unProject(rp3, glm.mat4(1.0)  ,perspective_matrix, screeninfo).z
                    a = [rp1.x*screen_width,rp1.y*screen_height,az]
                    b = [rp2.x*screen_width,rp2.y*screen_height,bz]
                    c = [rp3.x*screen_width,rp3.y*screen_height,cz]
                                    
                    givenuv = list(self.c_code_uvmap[triangle_idx][0]  )
                    geometry_buffer.add_triangle_to_buffer(a, 
                                        c, 
                                        b, 
                                        givenuv,   # uv list 
                                        node_id,  # node_id
                                        self.material_id)  # material_id
        return
        proj_vertices = [glm.projectZO(p.xyz,glm.mat4(1.0) , perspective_matrix, screeninfo) for p in in_view_space] 
        
        
        for triangle_idx,(pa,pb,pc) in enumerate(self.triangles_vindex):
            
            rp1 = proj_vertices[pa]
            rp2 = proj_vertices[pb]
            rp3 = proj_vertices[pc]

            rp3X3 = glm.mat3(rp1,rp2,rp3)
            facing = glm.determinant(rp3X3)
            a_flat = vec3(rp1.x,rp1.y,1.0)
            b_flat = vec3(rp2.x,rp2.y,1.0)
            c_flat = vec3(rp3.x,rp3.y,1.0)

            d2 = glm.determinant(glm.mat3(a_flat,b_flat,c_flat))

            #zvalues = glm.row(rp3X3,2)
            
            #(0<rp1.z<1 and 0<rp2.z<1 and 0<rp3.z<1)

            

            if facing>0 :
                a = [rp1.x*screen_width,rp1.y*screen_height,rp1.z]
                b = [rp2.x*screen_width,rp2.y*screen_height,rp2.z]
                c = [rp3.x*screen_width,rp3.y*screen_height,rp3.z]
                
                
                geometry_buffer.add_triangle_to_buffer(a , 
                                       b, 
                                       c, 
                                       self.c_code_uvmap[triangle_idx][0],   # uv list 
                                       node_id,  # node_id
                                       self.material_id)  # material_id



class GLMRenderContext:

    LINE_RETURN_SEG = Segment("\n",Style(color="white"))
    EMPTY_SEGMENT = Segment(" ",Style(color="white"))

    def __init__(self, screen_width, screen_height):
        self.elements: List[GLMMesh3D] = []
        
        self.depth_array: array.array[float] = array.array("d", [])
        self.canvas_array: array.array[int] = array.array("i", [])

        self.triangle_buffer = TrianglesBuffer(10000)
        self.triangle_buffer.clear()


        self.screen_width: int = screen_width
        self.screen_height: int = screen_height
        self.uniform_data:array.array[float] = make_uniform_data_buffer()

        self.setup_canvas()
        self.segmap = Segmap().init()
        self.split_map = dict[int:object]


        self.dummy_mesh_databuff = make_per_mesh_data_buffer()
    def setup_segment_cache(self,console):
        self.split_map = self.segmap.to_split_map(console)

    def setup_canvas(self):
        w, h = self.screen_width, self.screen_height

        # the depth array with empty version
        self.empty_depth_array = make_per_pixel_data_buffer(w,h,initial_value=float("inf"))
        self.depth_array = self.empty_depth_array.__copy__()

        # the canvas array with empty version
        self.empty_canvas_array = array.array("I",[0]*(w * h))
        self.canvas_array = self.empty_canvas_array.__copy__()

        # the buffer holding the pair (material_id, triangleid)
        self.empty_pixel_index_buffer = make_per_pixel_index_buffer(w,h)
        self.pixel_index_buffer = self.empty_pixel_index_buffer.__copy__()
        

    def update_wh(self, w, h):
        if w != self.screen_width or h != self.screen_height:
            self.screen_width = w
            self.screen_height = h
            self.setup_canvas()

    def clear_canvas(self):
        self.depth_array = self.empty_depth_array.__copy__()
        self.canvas_array = self.empty_canvas_array.__copy__()
        
        # clean up the info about what displayed where. 
        self.pixel_index_buffer = self.empty_pixel_index_buffer.__copy__()


    def render(self, camera: GLMCamera):
        self.triangle_buffer.clear()
        for elemnt in self.elements:
            elemnt.draw(camera,self.triangle_buffer)


        self.triangle_buffer.calculate_internal(self.screen_width,self.screen_height)
        self.triangle_buffer.raster_to_buffer(self.depth_array,self.pixel_index_buffer) 
        
        # in the uniform buffer putting the perspective 
        for idx,v in enumerate(itertools.chain(*camera.perspective)):
            self.uniform_data[idx] = v


        apply_stage2(self.triangle_buffer,
                     self.depth_array,
                     self.pixel_index_buffer,
                     self.screen_width,self.screen_height,
                     self.dummy_mesh_databuff,
                     self.uniform_data,
                     self.canvas_array
                     )
        
        #apply_stage2(TrianglesBuffer tr_buff, 
        #double[:] double_values_buff,    
        #unsigned int[:] integer_values_buff,
        
        #unsigned int screen_width,
        #unsigned int screen_height,
        #double[:] mesh_info,
        #double[:] uniformvalues, # the contextual data
        #unsigned int[:] output
        #):
    

#        return #
#        for elemnt in self.elements:
#            
#            pixel_iterator = elemnt.draw(camera)
#            for (pxi,pyi,appdepth),someinfo in pixel_iterator:
#                aidx = (pyi * self.screen_width) + pxi
#                currdepth = self.depth_array[aidx]
#                if appdepth < currdepth:
#                    # self.canvas[p.y][p.x] = p.render_pixel(txt)
#                    self.canvas_array[aidx] = elemnt.render_point(someinfo)
#                    self.depth_array[aidx] = appdepth



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



class GLMNode3D(Drawable3D):
    def __init__(self):
        self.local_translate:vec3 = vec3(.0,.0,.0)
        self.local_transform:mat4 = mat4(1.0)
        self.elems:list[GLMMesh3D] = []
        
    def set_transform(self,t:mat4):
        self.local_transform = t


    def draw(self, camera:GLMCamera,*args) -> Iterable[object]:
        
        cpos = camera.pos
        cmod = camera._model_inverse

        # move the camera 
        camera._model_inverse= camera._model_inverse*self.local_transform

        for element_idx, element in enumerate(self.elems):
            element.draw(camera,*args)
        # reset the camera
        camera.pos = cpos 
        camera._model_inverse = cmod
    def render_point(self,some_info):
        (otherinfo,element) = some_info
        return element.render_point(otherinfo)

    def cache_output(self,segmap):
        for e in self.elems:
            e.cache_output(segmap)
