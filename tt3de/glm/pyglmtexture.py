
import array
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
from glm import array as glma, i32vec2, ivec2, ivec3, mat3, vec2
from glm import quat 
from glm import vec3, vec4
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


def glmiterate(adjoint,idx1,idx2,x ,screen_height):

    l2y = line_equation_from_adjoint(adjoint, idx1, x)
    l1y = line_equation_from_adjoint(adjoint, idx2, x)
    
    if l2y == None or l1y == None:
        return

    if l1y<l2y:
        minyi = math.floor(l1y)
        maxyi = math.ceil(l2y)
    else:
        minyi = math.floor(l2y)
        maxyi = math.ceil(l1y)
    
    if minyi == maxyi and minyi<screen_height and minyi>0:
        yield minyi
    else:
        for yi in range(max(minyi,0),min(maxyi,screen_height-1)):
            yield yi


def glmtriangle_render(tri:glm.mat3,tri_inv,screen_width,screen_height) -> Iterable[tuple[int,int]]:
    adjoint = glm.determinant(tri)* tri_inv

    xclamped = glm.clamp(glm.row(tri,0),0,screen_width-1)
    yclamped = glm.clamp(glm.row(tri,1),0,screen_height-1)

    ax,bx,cx = round(xclamped.x),round(xclamped.y),round(xclamped.z)
    ay,by,cy = round(yclamped.x),round(yclamped.y),round(yclamped.z)

    if ax < cx:
        
        if cx < bx:

            minxi= ax
            maxxi= bx
            cutx = cx

            seg1 = 2
            seg2 = 1
            seg3 = 0

            ys = ay,cy,by
        else:
            if ax<bx:
                minxi = ax
                maxxi = cx
                cutx = bx

                seg1 = 1
                seg2 = 2
                seg3 = 0

                ys = ay,by,cy
            else:

                minxi= bx
                maxxi= cx
                cutx = ax

                seg1 = 0
                seg2 = 2
                seg3 = 1

                ys = by,ay,cy
    else:
        if ax < bx:
            
            minxi= cx
            maxxi= bx
            cutx = ax

            seg1 = 0
            seg2 = 1
            seg3 = 2

            ys = cy,ay,by
        else:
            if cx<bx:
                
                minxi= cx
                maxxi= ax
                cutx = bx

                seg1 = 1
                seg2 = 0
                seg3 = 2

                ys = cy,by,ay


            else:
                minxi= bx
                maxxi= ax
                cutx = cx

                seg1 = 2
                seg2 = 0
                seg3 = 1
                ys = by,cy,ay


    match cutx-minxi:
        case 0:
            yield minxi,ys[0]
        case 1:
            for yi in range(ys[0],ys[1]):
                yield minxi,yi
        case _ :
            yield minxi,ys[0]
            for xi in range(minxi+1,cutx):
                for yi in glmiterate(adjoint,seg1,seg2,xi,screen_height):
                    yield xi,yi

    match maxxi-cutx:
        case 0:
            yield cutx,ys[0]
        case 1:
            for yi in range(ys[1],ys[2]):
                yield cutx,yi
            yield maxxi,ys[2]
        case _ :
            yfl = line_equation_from_adjoint(adjoint, seg1, cutx)
            if yfl is not None:
                top = round(yfl)
                top = min(max(top,0),screen_height-1)
                r = range(ys[1],top) if ys[1]<top else range(top,ys[1])
                
                for yi in r:
                    yield cutx,yi
            for xi in range(cutx+1,maxxi):
                for yi in glmiterate(adjoint,seg1,seg3,xi,screen_height):
                    yield xi,yi
            #yield maxxi,ys[2]
    
    
    
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
                yield (pxi,pyi,0),(faceidx,1,weights)

            vertidx = 0
            for pxi,pyi in glm_triangle_vertex_pixels(transformed, screen_width,screen_height):
                yield (pxi,pyi,-1),(vertidx,2,(1.0,0.0,0.0))
                vertidx+=1



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
        
        
        self.glm_uvmap = [[glm.mat3x2(*[glm.vec2(uv.x,1-uv.y) for uv in uvlayer]) for uvlayer in t.uvmap] for t in self.triangles]
        
        #self.glm_uvmap = [[[glm.vec2(uv.x,uv.y) for uv in uvlayer] for uvlayer in t.uvmap] ]

    def render_point(self,some_info:tuple[vec3,float,int]):
        weight_to_vertex,normal_dot,face_idx = some_info
        uvmat = self.glm_uvmap[face_idx][0]

        uvcoord = glm.saturate(uvmat*weight_to_vertex)

        return self.texture.glm_render(uvcoord,normal_dot)
        
        #
        #yield glm.vec2(px,py),glm.vec4(uvpoint.x,uvpoint.y,ddot_prod,appdepth)


    def proj_vertices(self, camera: GLMCamera,perspective_matrix, screen_width, screen_height) :
        screeninfo = glm.vec4(0,0,1,1)

        proj_vertices = ([glm.projectZO( v, camera._model , perspective_matrix, screeninfo) for v in self.glm_vertices])
        
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
            

    def draw(self, camera:GLMCamera,transform=None,*args ) -> Iterable[tuple[vec3,vec3,tuple]]:
        screen_width, screen_height = camera.screen_width,camera.screen_height
        perspective_matrix = camera.perspective
        screeninfo = glm.vec4(0,0,screen_width,screen_height)

        proj_vertices = self.glm_vertices.map(glm.projectZO,camera._model , perspective_matrix, screeninfo)
        
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
                
                for pxi,pyi in glmtriangle_render(rp33,rpi,screen_width,screen_height):
                    weights = rpi*glm.vec3(pxi,pyi,1)
                    if (weights>vec3(0.0)) == VEC3_YES:
                        appdepth = glm.dot(glm.row(rp3X3,2),weights)
                        appx_point = rp3X3*weights
                        unprojected_point = glm.unProjectZO(appx_point,camera._model,perspective_matrix,screeninfo)
                        yield (pxi,pyi,appdepth),(weights,glm.dot(unprojected_point,camera_dir),triangle_idx)
                continue

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

            pixel_iterator = elemnt.draw(camera)
            for (pxi,pyi,appdepth),someinfo in pixel_iterator:
                aidx = (pyi * self.screen_width) + pxi
                currdepth = self.depth_array[aidx]
                if appdepth < currdepth:
                    # self.canvas[p.y][p.x] = p.render_pixel(txt)
                    self.canvas_array[aidx] = elemnt.render_point(someinfo)
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
        return
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
