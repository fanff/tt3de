import array
from math import exp
from typing import Iterable, List
from tt3de.asset_load import extract_palette
from tt3de.tt3de import (
    Camera,
    Drawable3D,
    Line3D,
    Node3D,
    PPoint2D,
    Point3D,
    PointElem,
    TextureTT3DE,
    Triangle3D,
    exp_grad,
)
from rich.color import Color
from rich.style import Style
from rich.text import Segment
from textual.strip import Strip

class TextureAscii(TextureTT3DE):
    def render_point(self, p: PPoint2D) -> int:
        pass

    def cache_output(self, segmap: "Segmap"):
        pass


class StaticTexture(TextureAscii):
    def __init__(self, char="#", color="white", bgcolor="black"):
        self.s = Segment(char, style=Style(color=color, bgcolor=bgcolor))
        self.value = 4

    def render_point(self, p: PPoint2D) -> int:
        return self.value

    def cache_output(self, segmap: "Segmap"):
        self.value = segmap.add_char(self.s)


class DistGradBGShade(TextureAscii):
    def __init__(self, bgcolor="red"):
        self.native_color = Color.parse(bgcolor)
        self.shade_to_idx: dict[int, int] = {}
        self.shade_count = 8

    def render_point(self, p: PPoint2D) -> int:
        f = exp_grad(self.shade_count - 1, 0.3, minv=1)
        return self.shade_to_idx[f(p.depth)]

    def cache_output(self, segmap: "Segmap"):

        for i in range(self.shade_count):
            colorshade = 1.0 - (i / self.shade_count)
            r, g, b = self.native_color.triplet.normalized
            triplet = (r * colorshade * 255, g * colorshade * 255, b * colorshade * 255)

            c = Color.from_rgb(*triplet)
            s = Segment(" ", style=Style(color="white", bgcolor=c))
            charidx = segmap.add_char(s)

            self.shade_to_idx[i] = charidx


class DistanceCharShare(TextureAscii):
    def __init__(self, bgcolor="red"):
        self.native_color = Color.parse(bgcolor)
        self.shader_chars = [" ", "░", "▒", "▓", "█"]
        self.shade_count = len(self.shader_chars)
        self.shade_to_idx: dict[int, int] = {}

    def render_point(self, p: PPoint2D) -> int:
        f = exp_grad(self.shade_count - 1, 0.5, minv=1)
        return self.shade_to_idx[f(p.depth)]

    def cache_output(self, segmap: "Segmap"):
        black = Color.from_rgb(0, 0, 0)
        for i in range(self.shade_count):
            s = Segment(
                self.shader_chars[i],
                style=Style(color=black, bgcolor=self.native_color),
            )
            charidx = segmap.add_char(s)
            self.shade_to_idx[i] = charidx

def clamp(v,mv,maxv):
    return max(min(v,maxv),mv)

class ImageTexture(TextureAscii):
    def __init__(self, img_data,shade_count=4):
        self.img_data = img_data
        self.image_height = len(self.img_data)
        self.image_width = len(self.img_data[0])

        self.color_palette = extract_palette(self.img_data)
        
        self.img_color=[]
        
        # the shading , then the color idx
        self.shade_to_idx: List[List[int]]
        self.shade_count = shade_count

    def unshaded_render(self, uvpoint):

        import glm
        tranf = glm.vec2(1,1)+(glm.vec2(-1,-1)*uvpoint)
        imgspace = tranf*glm.vec2(self.image_width-1,self.image_height-1)
        cuv = glm.clamp(imgspace, glm.vec2(0),glm.vec2(self.image_width-1,self.image_height-1))
        
        palette_idx:int = self.img_color[round(cuv.y)][round(cuv.x)]

        return self.shade_to_idx[0][palette_idx]

    def render_point(self, p: PPoint2D) -> int:
        
        shade_idx = clamp(self.shade_count-round(abs(p.dotval)*self.shade_count),0,self.shade_count-1)

        imgx:int = (self.image_width-1) - int(p.uv.x *  self.image_width) 
        imgy:int = (self.image_height-1) - int(p.uv.y *  self.image_height) 

        palette_idx:int = self.img_color[imgy][imgx]
        return self.shade_to_idx[shade_idx][palette_idx]

    def cache_output(self, segmap: "Segmap"):
        buff_color_to_int = {}

        self.shade_to_idx = []
        for i in range(self.shade_count):
            colorshade = 1.0 - (i / self.shade_count)
            self.shade_to_idx.append([0]*len(self.color_palette))
            
            for palette_idx,(r, g, b) in enumerate(self.color_palette):
                background_c = Color.from_rgb(r * colorshade , g * colorshade , b * colorshade )
                front_c = Color.from_rgb(r , g , b )
                s = Segment("▒", style=Style(color=front_c, bgcolor=background_c))
                charidx = segmap.add_char(s)
                self.shade_to_idx[i][palette_idx] = charidx

                if i == 0:
                    # keep the color unshaded with the palette_idx value of the color
                    buff_color_to_int[background_c] = palette_idx

        for r in self.img_data:
            crow = []
            for _ in r:
                c = Color.from_rgb(*_)
                palette_idx = buff_color_to_int[c]
                crow.append(palette_idx)
            self.img_color.append(crow)


class RenderContext:

    LINE_RETURN_SEG = Segment("\n",Style(color="white"))
    EMPTY_SEGMENT = Segment(" ",Style(color="white"))

    def __init__(self, screen_width, screen_height):
        self.elements: List[Drawable3D] = []

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

    def render(self, camera: Camera):
        for elemnt in self.elements:

            allpix = elemnt.draw(camera, self.screen_width, self.screen_height)
            for p in allpix:
                aidx = (self.screen_height - p.y - 1) * self.screen_width + p.x
                currdepth = self.depth_array[aidx]
                if p.depth < currdepth:
                    # self.canvas[p.y][p.x] = p.render_pixel(txt)
                    self.canvas_array[aidx] = elemnt.render_point(p)
                    self.depth_array[aidx] = p.depth
                
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

    def write_text(self, txt: str, x=0, y=0):
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

    def append_node(self, elem: Node3D):
        elem.cache_output(self.segmap)
        self.elements.append(elem)


class Segmap(dict):

    def init(self):
        self[0] = Segment(" ",Style(color="white"))
        for i in range(1, 10):
            self[i] = Segment(str(i), Style(color="white"))

        for i in range(10, 20):
            self[i] = Segment(str(i), Style(color="red"))
        for i in range(20, 30):
            self[i] = Segment(str(i), Style(color="blue"))
        for i in range(32, 126):
            self[i] = Segment(chr(i), Style(color="white"))
        return self

    def add_char(self, seg: Segment) -> int:
        idx = max(self.keys()) + 1
        self[idx] = seg
        return idx

    def to_split_map(self,console):
        strip_map = dict()
        for k,segment in self.items():
            s = Strip([segment])
            s = s.render(console)
            strip_map[k] = s
        return strip_map

def build_gizmo_arrows(center: Point3D):
    xline = Line3D(
        center + Point3D(0.1, 0, 0),
        center + Point3D(0.9, 0, 0),
        StaticTexture("x", "red"),
    )
    yline = Line3D(
        center + Point3D(0, 0.1, 0),
        center + Point3D(0, 0.9, 0),
        StaticTexture("y", "blue"),
    )
    zline = Line3D(
        center + Point3D(0, 0, 0.1),
        center + Point3D(0, 0, 0.9),
        StaticTexture("z", "green"),
    )

    p = PointElem(
        center,
        StaticTexture("O", "white"),
    )
    px = PointElem(center + Point3D(1, 0, 0), StaticTexture("X", "red"))
    py = PointElem(center + Point3D(0, 1, 0), StaticTexture("Y", "blue"))
    pz = PointElem(center + Point3D(0, 0, 1), StaticTexture("Z", "green"))

    return [xline, yline, zline, p, px, py, pz]


def get_cube_vertices(center: Point3D, width: float, shade_class=DistanceCharShare):
    half_width = width / 2

    # Calculate the 8 vertices of the cube
    btm_left_front = Point3D(
        center.x - half_width, center.y - half_width, center.z - half_width
    )
    btm_right_front = Point3D(
        center.x + half_width, center.y - half_width, center.z - half_width
    )
    top_left_front = Point3D(
        center.x - half_width, center.y + half_width, center.z - half_width
    )
    top_right_front = Point3D(
        center.x + half_width, center.y + half_width, center.z - half_width
    )
    btm_left_back = Point3D(
        center.x - half_width, center.y - half_width, center.z + half_width
    )
    btm_right_back = Point3D(
        center.x + half_width, center.y - half_width, center.z + half_width
    )
    top_left_back = Point3D(
        center.x - half_width, center.y + half_width, center.z + half_width
    )
    top_right_back = Point3D(
        center.x + half_width, center.y + half_width, center.z + half_width
    )

    # Bottom face
    btext = shade_class("#FF00FF")

    t1 = Triangle3D(btm_left_front, btm_left_back, btm_right_back, btext)
    t2 = Triangle3D(btm_left_front, btm_right_back, btm_right_front, btext)

    # Top face
    ttext = shade_class("#FFFFFF")
    t3 = Triangle3D(top_left_front, top_left_back, top_right_back, ttext)
    t4 = Triangle3D(top_left_front, top_right_back, top_right_front, ttext)

    # Front face

    ftext = shade_class("#FF0000")
    t5 = Triangle3D(btm_left_front, top_left_front, top_right_front, ftext)
    t6 = Triangle3D(btm_left_front, top_right_front, btm_right_front, ftext)

    # Back face
    Btext = shade_class("#0000FF")
    t7 = Triangle3D(btm_left_back, top_left_back, top_right_back, Btext)
    t8 = Triangle3D(btm_left_back, top_right_back, btm_right_back, Btext)

    # Left face
    ltext = shade_class("#00FF00")
    t9 = Triangle3D(btm_left_front, top_left_front, btm_left_back, ltext)
    t10 = Triangle3D(btm_left_back, top_left_front, top_left_back, ltext)

    # Right face
    rtext = shade_class("#1122DD")
    t11 = Triangle3D(btm_right_front, top_right_front, btm_right_back, rtext)
    t12 = Triangle3D(btm_right_back, top_right_front, top_right_back, rtext)

    return [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12]
