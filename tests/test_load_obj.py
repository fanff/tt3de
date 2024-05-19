
import math
import unittest

from context import tt3de

from tt3de.tt3de import Camera, FPSCamera, Mesh3D, Point3D, PointElem, extract_palette, load_bmp, round_to_palette


def assertAlmostEqualP3D(a: Point3D, b: Point3D, limit=0.00001):
    assert (a - b).magnitude() < limit, f"a = {a},b = {b} "



class TestLoad(unittest.TestCase):

    def test_simplecube(self):

        amesh = Mesh3D.from_obj("models/cube.obj")
        

        self.assertEqual(len(amesh.triangles),12)

        for t in amesh.triangles:
            print(t)

    def test_simpleimg(self):
        pxdata = load_bmp("models/cube_texture.bmp")

    def test_palette6bits(self):
        imgpalette = load_bmp("models/RGB_6bits.bmp")

        palette = extract_palette(imgpalette)
        self.assertEqual(len(palette),64)

        print(len(imgpalette),len(imgpalette[0]))
    def test_paletteAlign(self):
        imgpalette = load_bmp("models/RGB_6bits.bmp")

        palette = extract_palette(imgpalette)
        self.assertEqual(len(palette),64)
        pxdata = load_bmp("models/cube_texture.bmp")
        roundedimg = round_to_palette(pxdata,palette)

        self.assertLessEqual(len(extract_palette(roundedimg)),64)
        
if __name__ == "__main__":  
    unittest.main()