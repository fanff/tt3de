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
    pass


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
    
