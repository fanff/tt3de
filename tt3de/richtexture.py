import array
import itertools
from math import exp
from typing import Iterable, List

import glm
from tt3de.asset_load import extract_palette
from tt3de.tt3de import (
    Drawable3D,
    PPoint2D,
    Point3D,
)
from rich.color import Color
from rich.style import Style
from rich.text import Segment
from textual.strip import Strip


class TextureAscii():
    def render_point(self, *args) -> int:
        pass

    def cache_output(self, segmap: "Segmap"):
        pass


class StaticTexture(TextureAscii):
    def __init__(self, char="#", color="white", bgcolor="black"):
        self.s = Segment(char, style=Style(color=color, bgcolor=bgcolor))
        self.value = 4

    def render_point(self, *args) -> int:
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


def clamp(v, mv, maxv):
    return max(min(v, maxv), mv)


class ImageTexture(TextureAscii):
    def __init__(self, img_data, shade_count=4):
        self.img_data:List[List[int]] = img_data
        self.image_height = len(self.img_data)
        self.image_width = len(self.img_data[0])

        self.color_palette = extract_palette(self.img_data)

        self.img_color = []

        # the shading , then the color idx
        self.shade_to_idx: List[List[int]]
        self.shade_count = shade_count
    def chained_data(self):
        return list(itertools.chain(*self.img_data))
    def glm_render(self, uvpoint: glm.vec2, normal_dot: float):

        import glm

        cuv = glm.fract(uvpoint) * glm.vec2(self.image_width - 1, self.image_height - 1)
        palette_idx: int = self.img_color[round(cuv.y)][round(cuv.x)]

        shade_idx = clamp(
            self.shade_count - round(abs(normal_dot) * self.shade_count),
            0,
            self.shade_count - 1,
        )

        return self.shade_to_idx[shade_idx][palette_idx]

    def render_point(self, p: PPoint2D) -> int:

        shade_idx = 0  # clamp(self.shade_count-round(abs(p.dotval)*self.shade_count),0,self.shade_count-1)

        imgx: int = (self.image_width - 1) - int(p.uv.x * self.image_width)
        imgy: int = (self.image_height - 1) - int(p.uv.y * self.image_height)

        palette_idx: int = self.img_color[imgy][imgx]
        return self.shade_to_idx[shade_idx][palette_idx]

    def cache_output(self, segmap: "Segmap"):

        buff_color_to_int = {}

        self.shade_to_idx = []
        for i in range(self.shade_count):
            colorshade = 1.0 - (i / (self.shade_count))
            self.shade_to_idx.append([0] * len(self.color_palette))

            for palette_idx, (r, g, b) in enumerate(self.color_palette):
                background_c = Color.from_rgb(
                    r * colorshade, g * colorshade, b * colorshade
                )
                front_c = Color.from_rgb(r, g, b)
                s = Segment(
                    "⠿",
                    style=Style(
                        color=background_c, bgcolor=front_c, dim=False, reverse=False
                    ),
                )
                charidx = segmap.add_char(s)
                self.shade_to_idx[i][palette_idx] = charidx

                if i == 0:
                    # keep the color unshaded with the palette_idx value of the color
                    buff_color_to_int[front_c] = palette_idx

        for r in self.img_data:
            crow = []
            for _ in r:
                c = Color.from_rgb(*_)
                palette_idx = buff_color_to_int[c]
                crow.append(palette_idx)
            self.img_color.append(crow)

