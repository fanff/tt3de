import math
import unittest

from tt3de.asset_fastloader import fast_load
from tt3de.asset_load import extract_palette, load_bmp, round_to_palette
from tt3de.points import Point3D


def assertAlmostEqualP3D(a: Point3D, b: Point3D, limit=0.00001):
    assert (a - b).magnitude() < limit, f"a = {a},b = {b} "


class TestLoad(unittest.TestCase):

    def test_simplecube(self):
        polygon3d = fast_load("models/cube.obj")

        self.assertEqual(len(polygon3d.vertex_list), 12 * 3)
        self.assertEqual(len(polygon3d.uvmap), 12)

    def test_simpleimg(self):
        with open("models/cube_texture.bmp", "rb") as fin:
            pxdata = load_bmp(fin)

    
    def test_paletteAlign(self):
        imgpalette = load_bmp(open("models/RGB_6bits.bmp", "rb"))

        palette = extract_palette(imgpalette)
        self.assertEqual(len(palette), 64)
        pxdata = load_bmp(open("models/cube_texture.bmp", "rb"))
        roundedimg = round_to_palette(pxdata, palette)

        self.assertLessEqual(len(extract_palette(roundedimg)), 64)
