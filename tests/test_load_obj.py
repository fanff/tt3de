import math
import unittest

from tt3de.asset_fastloader import fast_load
from tt3de.asset_load import extract_palette, load_bmp, round_to_palette
from tt3de.tt3de import Point3D


def assertAlmostEqualP3D(a: Point3D, b: Point3D, limit=0.00001):
    assert (a - b).magnitude() < limit, f"a = {a},b = {b} "


class TestLoad(unittest.TestCase):

    def test_simplecube(self):
        Mesh3D = None
        amesh = fast_load("models/cube.obj", Mesh3D)

        self.assertEqual(len(amesh.triangles), 12)

        for t in amesh.triangles:
            print(t)

    def test_simpleimg(self):
        with open("models/cube_texture.bmp", "rb") as fin:
            pxdata = load_bmp(fin)

    def test_palette6bits(self):
        imgpalette = load_bmp(open("models/RGB_6bits.bmp", "rb"))

        palette = extract_palette(imgpalette)
        self.assertEqual(len(palette), 64)

        print(len(imgpalette), len(imgpalette[0]))

    def test_paletteAlign(self):
        imgpalette = load_bmp(open("models/RGB_6bits.bmp", "rb"))

        palette = extract_palette(imgpalette)
        self.assertEqual(len(palette), 64)
        pxdata = load_bmp(open("models/cube_texture.bmp", "rb"))
        roundedimg = round_to_palette(pxdata, palette)

        self.assertLessEqual(len(extract_palette(roundedimg)), 64)


