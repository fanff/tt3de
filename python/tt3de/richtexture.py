# -*- coding: utf-8 -*-
import itertools
from typing import List


from tt3de.asset_load import extract_palette


class TextureAscii:
    pass


class ImageTexture(TextureAscii):
    def __init__(self, img_data):
        self.img_data: List[List[int]] = img_data
        self.image_height = len(self.img_data)
        self.image_width = len(self.img_data[0])

        self.color_palette = extract_palette(self.img_data)

        self.img_color = []

    def chained_data(self):
        return list(itertools.chain(*self.img_data))
