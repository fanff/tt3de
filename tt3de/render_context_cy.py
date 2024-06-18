import array
import itertools
from math import exp
import math
from typing import Iterable, List, Tuple
from tests.c_code.drawing_buffer.test_draw_buffer import drawbuffer_to_pil
from tt3de.asset_fastloader import fast_load
from tt3de.asset_load import extract_palette
from tt3de.glm import material
from tt3de.glm.pyglmtexture import GLMCamera, GLMMesh3D
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

from rich.color_triplet import ColorTriplet
from rich.color import Color
from rich.style import Style
from rich.text import Segment
from textual.strip import Strip
from textual.geometry import Region
import glm
from glm import array as glma, i32vec2, ivec2, ivec3, mat3, mat4, vec2
from glm import quat
from glm import vec3, vec4


from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de.glm.primitives.primitives import PrimitivesBuffer
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer


from tt3de.glm.primitives.primitive_builder import build_primitives

from tt3de.glm.geometry.geometry import GeometryBuffer
from tt3de.glm.material.c_material import apply_pixel_shader
from tt3de.glm.c_texture import TextureArray
from tt3de.glm.material.c_material import MaterialBuffer


class CyRenderContext:

    LINE_RETURN_SEG = Segment("\n", Style(color="white"))
    EMPTY_SEGMENT = Segment(" ", Style(color="white"))

    def __init__(self, screen_width, screen_height):
        self.elements: List[GLMMesh3D] = []

        self.depth_array: array.array[float] = array.array("d", [])
        self.canvas_array: array.array[int] = array.array("i", [])

        self.screen_width: int = screen_width
        self.screen_height: int = screen_height

        self.drawing_buffer = None

        # create a geometry buffer to hold the initial elemnts
        self.geometry_buffer = GeometryBuffer(2000)
        self.primitive_buffer = PrimitivesBuffer(2000)

        self.texture_array = TextureArray()

        self.material_buffer = MaterialBuffer()

        self.setup_canvas()
        self.segmap = Segmap().init()
        self.split_map = dict[int:object]
        self.pre_calc_bigbuffer()

    def setup_segment_cache(self, console):
        self.split_map = self.segmap.to_split_map(console)

    def setup_canvas(self):
        w, h = self.screen_width, self.screen_height

        if w * h > 0:
            # the depth array with empty version
            self.drawing_buffer = DrawingBuffer(w, h)
            self.drawing_buffer.set_bit_reduction([6]*6)
            self.auto_buffer = {}
            self.drawing_buffer.hard_clear(float("inf"))
        else:
            self.drawing_buffer = DrawingBuffer(3, 3)
            self.drawing_buffer.set_bit_reduction([7]*6)
            self.auto_buffer = {}
            self.drawing_buffer.hard_clear(float("inf"))

    def update_wh(self, w, h):
        if w != self.screen_width or h != self.screen_height:
            self.screen_width = w
            self.screen_height = h
            self.setup_canvas()

    def clear_canvas(self):
        self.drawing_buffer.hard_clear(100000.0)
        self.geometry_buffer.clear()
        self.primitive_buffer.clear()

    def render(self, camera: GLMCamera):

        for elemnt in self.elements:
            elemnt.draw(camera, self.geometry_buffer)

        build_primitives(self.geometry_buffer, self.primitive_buffer)

        raster_precalc(self.primitive_buffer, self.drawing_buffer)
        raster_all(self.primitive_buffer, self.drawing_buffer, self.material_buffer)

        apply_pixel_shader(
            self.primitive_buffer,
            self.drawing_buffer,
            self.material_buffer,
            self.geometry_buffer,
            self.texture_array,
        )

    def write_text(self, txt: str, x: int = 0, y: int = 0):
        pass
        # for idx, c in enumerate(txt):
        #    if c.isprintable():
        #        ordc = ord(c)
        #        if ordc in self.segmap:
        #            aidx = (self.screen_height - y - 1) * self.screen_width + idx + x
        #            self.canvas_array[aidx] = ordc

    def append(self, elem: Drawable3D):
        elem.cache_output(self.segmap)
        self.elements.append(elem)

    def extend(self, elems: List[Drawable3D]):
        for e in elems:
            self.append(e)

    def to_textual_(self, crop: Region) -> List[Strip]:
        """Converts the drawing buffer to textual representation.

        Returns:
            List[Strip]: A list of Strip objects representing the textual representation of the drawing buffer.
        """
        max_x = crop.x + crop.width
        max_y = crop.y + crop.height
        if self.screen_width == 0 or self.screen_height == 0:
            return []

        factor = len(self.allchars)
        result = []
        currentLine = []
        last_processed_line = 0
        for idx, (fr, fg, fb, br, bg, bb, g1, g2) in enumerate(
            (self.drawing_buffer.canvas_to_list())
        ):
            curr_x = idx % self.screen_width
            curr_y = idx // self.screen_width

            if curr_x < crop.x or curr_x > max_x or curr_y < crop.y or curr_y > max_y:
                continue  # skip this

            if curr_y > last_processed_line:

                last_processed_line = curr_y
                # we just found a end of line
                s = Strip(currentLine)
                result.append(s)
                currentLine = []

            # quickly calculate a kind of hash
            segid = g2 + factor * (
                bb // self.mult
                + self.cut_factor_by_channel
                * (
                    bg // self.mult
                    + self.cut_factor_by_channel
                    * (
                        br // self.mult
                        + self.cut_factor_by_channel
                        * (
                            fb // self.mult
                            + self.cut_factor_by_channel
                            * (
                                fg // self.mult
                                + self.cut_factor_by_channel * (fr // self.mult)
                            )
                        )
                    )
                )
            )
            # currentLine.append(self.big_buffer[segid])

            # for testing terminal speed
            # currentLine.append(random.choice(self.big_buffer))

            #
            asegment = self.auto_buffer.get(segid, None)
            if asegment is None:
                asegment = Segment(
                    self.allchars[g2],
                    Style(
                        color=Color.from_triplet(ColorTriplet(fr, fg, fb)),
                        bgcolor=Color.from_triplet(ColorTriplet(br, bg, bb)),
                    ),
                )

                self.auto_buffer[segid] = asegment
            currentLine.append(asegment)

            # currentLine.append(Segment("?",style=self.big_buffer[segid]))

        s = Strip(currentLine)
        result.append(s)
        return result
    
    def to_textual_2(self, crop: Region) -> List[Strip]:
        """Converts the drawing buffer to textual representation.

        Returns:
            List[Strip]: A list of Strip objects representing the textual representation of the drawing buffer.
        """
        if self.screen_width == 0 or self.screen_height == 0:
            return []
        return self.drawing_buffer.canvas_to_list_hashed(crop.x,crop.y,crop.width,crop.height,self.auto_buffer,self.allchars)
        
            

        
    def pre_calc_bigbuffer(self):
        self.auto_buffer = {}
        self.big_buffer = []  # 8^6 =  262 144 values
        self.allchars_text = [chr(i) for i in range(32, 126)]
        self.all_chars_b6 = [
            c for c in "⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯⠰⠱⠲⠳⠴⠵⠶⠷⠸⠹⠺⠻⠼⠽⠾⠿"
        ]
        self.all_chars_block = [c for c in "▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐░▒▓▔▕▖▗▘▚▙▛▜▝▞▟"]

        self.allchars = self.allchars_text + self.all_chars_b6 + self.all_chars_block

        self.cut_factor_by_channel = (
            32  # the more you cut, the more you kinda limit the auto buffer size
        )
        self.mult = 256 // self.cut_factor_by_channel

        return