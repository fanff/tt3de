
import array
import itertools
from math import exp
import math
from typing import Iterable, List, Tuple
from tt3de.asset_load import extract_palette
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

from c_triangle_raster import c_glm_triangle_render_to_buffer
from c_triangle_raster import iterate_pixel_buffer,TrianglesBuffer
from c_triangle_raster import TrianglesBuffer,apply_stage2
from c_triangle_raster import make_per_pixel_index_buffer,make_per_pixel_data_buffer,make_per_mesh_data_buffer,make_uniform_data_buffer



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
        self.perspective = glm.perspectiveFovZO(self.fov_radians, self.screen_width, self.screen_height*self.character_factor, self.dist_min, self.dist_max)
        #self.perspective = glm.perspectiveFovRH_ZO(self.fov_radians, self.screen_width, self.screen_height*self.character_factor, self.dist_min, self.dist_max)
        #self.perspective = glm.orthoZO(-self.screen_width, self.screen_width, -self.screen_height, self.screen_height, 1, 100.0)
    
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


class GLM2DMappedTexture(TextureAscii):
    def __init__(self, img_data):
        self.img_data = img_data
        self.image_height = len(self.img_data)
        self.image_width = len(self.img_data[0])

        self.size_vec = glm.vec2(self.image_width-1,self.image_height-1)
        self.img_color=[] 
        self.output_cached=False
    def render_point(self, uvcoord, info) -> int:
        cuv = glm.fract(uvcoord)*self.size_vec
        #cuv = glm.clamp(cuv, glm.vec2(0),glm.vec2(self.image_width-1,self.image_height-1))
        
        return self.img_color[round(cuv.y)][round(cuv.x)]

    def cache_output(self, segmap: "Segmap"):
        if self.output_cached: return
        self.output_cached=True
        black = Color.from_rgb(0, 0, 0)
        buff_color_to_int = {}
        for palette_idx,(r, g, b) in enumerate(extract_palette(self.img_data)):
            c = Color.from_rgb(r, g, b)

            s = Segment(" ",style=Style(color=black, bgcolor=c))

            charidx = segmap.add_char(s)
            #self.color_to_idx[palette_idx] = charidx

            buff_color_to_int[c] = charidx

        for r in self.img_data:
            crow = []
            for _ in r:
                c = Color.from_rgb(*_)
                palette_idx = buff_color_to_int[c]
                crow.append(palette_idx)
            self.img_color.append(crow)

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


#def glmiterate(adjoint,idx1,idx2,x ,screen_height):
#
#    l2y = line_equation_from_adjoint(adjoint, idx1, x)
#    l1y = line_equation_from_adjoint(adjoint, idx2, x)
#    
#    if l2y == None or l1y == None:
#        return
#
#    if l1y<l2y:
#        minyi = math.floor(l1y)
#        maxyi = math.ceil(l2y)
#    else:
#        minyi = math.floor(l2y)
#        maxyi = math.ceil(l1y)
#    
#    if minyi == maxyi and minyi<screen_height and minyi>0:
#        yield minyi
#    else:
#        for yi in range(max(minyi,0),min(maxyi,screen_height-1)):
#            yield yi

from glm import determinant,iround,clamp,row

def glmtriangle_render(tri:glm.mat3,tri_inv:glm.mat3,screen_width:int,screen_height:int) -> Iterable[tuple[int,int]]:
    adjoint = determinant(tri)* tri_inv

    ax,bx,cx = iround(clamp(row(tri,0),0.0,screen_width-1))#round(xclamped.x),round(xclamped.y),round(xclamped.z)
    ay,by,cy = iround(clamp(row(tri,1),0.0,screen_height-1))#round(yclamped.x),round(yclamped.y),round(yclamped.z)

    #xv = glm.row(tri,0)
    #yv = glm.row(tri,1)
    #ax,bx,cx = round(xv.x),round(xv.y),round(xv.z)
    #ay,by,cy = round(yv.x),round(yv.y),round(yv.z)
    #ax = 0 if ax < 0 else (screen_width if ax > screen_width else ax)
    #bx = 0 if bx < 0 else (screen_width if bx > screen_width else bx)
    #cx = 0 if cx < 0 else (screen_width if cx > screen_width else cx)
    #ay = 0 if ax < 0 else (screen_height if ay > screen_height else ay)
    #by = 0 if bx < 0 else (screen_height if by > screen_height else by)
    #cy = 0 if cx < 0 else (screen_height if cy > screen_height else cy)

    # segment index 
    # 0: CB
    # 1: AC
    # 2: AB
    # identifying triangle positionning

    if ax < cx:
        if cx < bx:
            #  ..-C.
            # A-----B
            # 
            minxi= ax
            maxxi= bx
            cutx = cx

            # seg1 to seg2; then seg3 to seg4
            seg1 = 2  # AB
            seg2 = 1  # AC
            seg3 = 2  
            seg4 = 0  # CB
            # heights to use, for min, cut, max
            ys = ay,cy,by
        else:
            if ax<bx:
                #       _---C.
                #   .-^    /
                # A-----B/
                # common branch is upper
                minxi = ax
                maxxi = cx
                cutx = bx

                seg1 = 2 # AB
                seg2 = 1 # AC
                seg3 = 0 # CB
                seg4 = 1 # AC
                ys = ay, by, cy    
            else:
                #     A   
                #         C
                #  B    
                #   
                minxi= bx
                maxxi= cx
                cutx = ax

                seg1 = 0 # CB
                seg2 = 2 # AB
                seg3 = 0 # CB
                seg4 = 1 # AC
                ys = by,ay,cy
    else:
        if ax < bx:
            #    C        B 
            #    
            #         A          
            #   common branch is upper
            minxi= cx
            maxxi= bx
            cutx = ax

            seg1 = 1 # AC
            seg2 = 0 # CB
            seg3 = 2 # AB
            seg4 = 0 # CB
            ys = cy,ay,by
        else:
            
            if cx<bx:
                #      B      
                #    
                #   C        A          
                #   
                minxi= cx
                maxxi= ax
                cutx = bx

                seg1 = 1 # AC
                seg2 = 0 # CB
                seg3 = 1 # AC
                seg4 = 2 # AB
                ys = cy,by,ay


            else:
                #   B        A   
                #       
                #        C
                # common branch is upper
                minxi= bx
                maxxi= ax
                cutx = cx

                seg1 = 0 # CB
                seg2 = 2 # AB
                seg3 = 1 # AC
                seg4 = 2 # AB
                ys = by,cy,ay

    # first part
    # from left to the cutindex
    # the drawing is NOT including the cut 
    match cutx-minxi:
        case 0:
            # its a vertical stuff
            yield minxi,ys[0] # returning left point height
        case 1:
            for yi in range(ys[0],ys[1]):  # from left height, to cut height
                yield minxi,yi
        case _ :

            # left corner return
            yield minxi,ys[0]
            
            for xi in range(minxi+1,cutx):
                miny = math.floor(yvalue_from_adjoint_unprotected(adjoint, seg1, xi))
                maxy = math.ceil(yvalue_from_adjoint_unprotected(adjoint, seg2, xi))
                miny =0 if miny < 0 else (screen_height if miny > screen_height else miny)
                maxy =0 if maxy < 0 else (screen_height if maxy > screen_height else maxy)
                for yi in range(miny,maxy):
                    yield xi,yi

                #for yi in glmiterate(adjoint,seg1,seg2,xi,screen_height):
                #    yield xi,yi

    # second part
    match maxxi-cutx:
        case 0:
            # its a vertical line. 
            yield cutx,ys[0]
        case 1:
            for yi in range(ys[1],ys[2]):
                yield cutx,yi
            yield maxxi,ys[2]
        case _ :
            for xi in range(cutx,maxxi):
                miny = math.floor(yvalue_from_adjoint_unprotected(adjoint, seg3, xi))
                maxy = math.ceil(yvalue_from_adjoint_unprotected(adjoint, seg4, xi))
                miny =0 if miny < 0 else (screen_height if miny > screen_height else miny)
                maxy =0 if maxy < 0 else (screen_height if maxy > screen_height else maxy)

                for yi in range(miny,maxy):
                    yield xi,yi
            #yfl = line_equation_from_adjoint(adjoint, seg1, cutx)
            #if yfl is not None:
            #    top = round(yfl)
            #    top = min(max(top,0),screen_height-1)
            #    r = range(ys[1],top) if ys[1]<top else range(top,ys[1])
            #    for yi in r:
            #        yield cutx,yi
            #for xi in range(cutx+1,maxxi):
            #    for yi in glmiterate(adjoint,seg1,seg3,xi,screen_height):
            #        yield xi,yi
    
    
    
class GLM2DNode(Drawable3D):
    def __init__(self):
        
        self.elements:List[GLM2DNode]=[]
        self.local_transform = mat3(1.0)

    def cache_output(self,segmap):
        for e in self.elements:
            e.cache_output(segmap)
    def render_point(self,some_info)->int:
        
        (elem,pixinfo) = some_info
        return elem.render_point(pixinfo)
        
    def draw(self,camera:GLMCamera,transform=None,*args):
        if transform is not None:
            localchange = transform*self.local_transform
        else:
            localchange = self.local_transform
        for elem in self.elements:
            for pixcoord,pixinfo in elem.draw(camera,localchange):
                yield pixcoord,(elem,pixinfo)

class GLM2DMesh(GLM2DNode):

    def __init__(self):
        
        self.elements=[]
        self.uvmap = []
        self.texture:TextureAscii = StaticTexture()

    def cache_output(self,segmap):
        self.texture.cache_output(segmap)
        self.glm_elements=[p3d_triplet_to_matrix(elment)
            for elment in self.elements]
        
        self.glm_uvmap =[p2d_uv_tomatrix(uv) for uv in self.uvmap]


    def render_point(self,some_info)->int:

        vertid,mode,weights = some_info
        

        match mode:
            case 1:
                uvmat = self.glm_uvmap[vertid]
                #uvcoord = glm.saturate(uvmat*weights)
                uvcoord = (uvmat*weights)
                return self.texture.render_point(uvcoord,None)
            case 2:
                return vertid+1
        return 5
    

    def draw(self,camera:GLMCamera,transform=None,*args):

        screen_width, screen_height = camera.screen_width,camera.screen_height
        scc = min(screen_width,screen_height)
        screenscaling = glm.scale(vec2(scc*camera.character_factor,scc))

        final_transform = screenscaling*transform if transform is not None else screenscaling
        for faceidx,trimat in enumerate(self.glm_elements):
            transformed = final_transform*trimat
            tri_inv = glm.inverse(transformed)

            for pxi,pyi in glmtriangle_render(transformed,tri_inv,screen_width,screen_height):
                weights = tri_inv*glm.vec3(pxi,pyi,1)

                if (weights>VEC3_ZERO) == VEC3_YES:
                    yield (pxi,pyi,0),(faceidx,1,weights)

            #vertidx = 0
            #for pxi,pyi in glm_triangle_vertex_pixels(transformed, screen_width,screen_height):
            #    yield (pxi,pyi,-1),(vertidx,2,(1.0,0.0,0.0))
            #    vertidx+=1


class GLMMesh3D(Mesh3D):
    def __init__(self):
        self.vertices: List[Point3D] = []
        self.texture_coords: List[List[GLMTexturecoord]] = [[] for _ in range(8)]
        self.normals: List[Point3D] = []
        self.triangles: List[Triangle3D] = []
        self.texture:ImageTexture=None

    def cache_output(self,segmap):
        self.glm_vertices = glma([vec3(p.x,p.y,p.z) for p in self.vertices])
        self.glm_normals = glma([vec3(t.normal.x,t.normal.y,t.normal.z) for t in self.triangles])
        self.texture_coords = [[GLMTexturecoord(p.x,p.y) for p in coordlayer] for coordlayer in self.texture_coords]
        self.texture.cache_output(segmap)
        
        
        self.glm_uvmap = [[glm.mat3x2(*[glm.vec2(uv.x,1.0-uv.y) for uv in uvlayer]) for uvlayer in t.uvmap] for t in self.triangles]
        self.c_code_uvmap = [[tuple(itertools.chain(*[(uv.x,1.0-uv.y) for uv in uvlayer])) for uvlayer in t.uvmap] for t in self.triangles]
        #self.glm_uvmap = [[[glm.vec2(uv.x,uv.y) for uv in uvlayer] for uvlayer in t.uvmap] ]

        # 
        self.per_mesh_buffer_data:array.array[float] = make_per_mesh_data_buffer()
        #self.per_mesh_buffer_data[0:]
        



    def render_point(self,some_info:tuple[vec3,float,int]):
        return 4
        weight_to_vertex,normal_dot,face_idx = some_info
        uvmat = self.glm_uvmap[face_idx][0]

        uvcoord = uvmat*weight_to_vertex

        return self.texture.glm_render(uvcoord,normal_dot)
        
        #
        #yield glm.vec2(px,py),glm.vec4(uvpoint.x,uvpoint.y,ddot_prod,appdepth)


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
            
    def draw(self,camera:GLMCamera,tribuff:TrianglesBuffer):
        
        screen_width, screen_height = camera.screen_width,camera.screen_height
        perspective_matrix = camera.perspective
        screeninfo = glm.vec4(0,0,screen_width,screen_height)

        proj_vertices = self.glm_vertices.map(glm.projectZO,camera._model_inverse , perspective_matrix, screeninfo)
        

        # keeping the camera direction in the MESH store info
        camera_dir = camera.direction_vector()
        
        for triangle_idx,(pa,pb,pc) in enumerate(self.triangles_vindex):
            
            rp1 = proj_vertices[pa]
            rp2 = proj_vertices[pb]
            rp3 = proj_vertices[pc]

            rp3X3 = glm.mat3(rp1,rp2,rp3)
            facing = glm.determinant(rp3X3)
            zvalues = glm.row(rp3X3,2)
            
            #(0<rp1.z<1 and 0<rp2.z<1 and 0<rp3.z<1)
            if facing>0 and (zvalues>vec3(0.0)) * (zvalues<vec3(1.0))== vec3(1.0):
                
                # keep the FACE info (uv map and stuff) inside the the tribuff
                uvmap = self.c_code_uvmap[triangle_idx][0]
                
                # should add the triangle with material_id material _id here 
                # glm.mat3x3(vec3(rp1.xy,1),vec3(rp2.xy,1),vec3(rp3.xy,1))
                given_matrix = glm.mat3x3(vec3(rp1.xy,1.0),vec3(rp2.xy,1),vec3(rp3.xy,1))
                tribuff.add_triangle_info(given_matrix,material_id=1,uvmap=uvmap)


    def draw_old_version(self, camera:GLMCamera,transform=None,*args ) -> Iterable[tuple[vec3,vec3,tuple]]:
        screen_width, screen_height = camera.screen_width,camera.screen_height
        perspective_matrix = camera.perspective
        screeninfo = glm.vec4(0,0,screen_width,screen_height)

        proj_vertices = self.glm_vertices.map(glm.projectZO,camera._model_inverse , perspective_matrix, screeninfo)
        
        camera_dir = camera.direction_vector()

        for triangle_idx,(pa,pb,pc) in enumerate(self.triangles_vindex):
            
            rp1 = proj_vertices[pa]
            rp2 = proj_vertices[pb]
            rp3 = proj_vertices[pc]

            rp3X3 = glm.mat3(rp1,rp2,rp3)
            

            facing = glm.determinant(rp3X3)
            zvalues = glm.row(rp3X3,2)
            
            #(0<rp1.z<1 and 0<rp2.z<1 and 0<rp3.z<1)
            if facing>0 and (zvalues>vec3(0.0)) * (zvalues<vec3(1.0))== vec3(1.0):
                rp33 = glm.mat3x3(vec3(rp1.xy,1),vec3(rp2.xy,1),vec3(rp3.xy,1))
                rpi = glm.inverse(rp33)

                count = c_glm_triangle_render_to_buffer(rp3X3,
                                            screen_width,
                                            screen_height,
                                            self.pixel_buffer_array)
                for pxi,pyi in iterate_pixel_buffer(self.pixel_buffer_array,count):
                #for pxi,pyi in glmtriangle_render(rp33,rpi,screen_width,screen_height):
                    weights = rpi*glm.vec3(pxi,pyi,1)
                    
                    
                    if (weights>VEC3_ZERO) == VEC3_YES:
                        appx_point = rp3X3*weights
                        unprojected_point = glm.unProjectZO(vec3(pxi,pyi,appx_point.z),camera._model_inverse,perspective_matrix,screeninfo)
                        #appdepth = glm.dot(glm.row(rp3X3,2),weights)

                        w3d = glm.inverse(mat3(self.glm_vertices[pa],
                                               self.glm_vertices[pb],
                                               self.glm_vertices[pc]))*unprojected_point


                        yield (pxi,pyi,appx_point.z),(w3d,glm.dot(unprojected_point,camera_dir),triangle_idx)



def iterate_c_depth_array(depth_buffer:array.array,screen_width,screen_height):
    for xi in range(screen_width):
        for yi in range(screen_height):
            index = (((screen_height) * xi) + yi)
            index_d = index*4
            if depth_buffer[index_d] < 1000:
                yield (xi,yi,depth_buffer[index_d],depth_buffer[index_d+1],depth_buffer[index_d+2],depth_buffer[index_d+3] )



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
