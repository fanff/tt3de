# -*- coding: utf-8 -*-
import unittest

from tt3de.tt3de import MaterialBufferPy, TextureBufferPy, materials

from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture


class Test_MaterialBufferPy(unittest.TestCase):
    def setUp(self):
        self.mb = MaterialBufferPy()

    def test_create(self):
        mb = MaterialBufferPy()

        self.assertEqual(mb.count(), 0)

        self.assertEqual(mb.add_static((255, 90, 90, 255), (5, 10, 20, 255), 0), 0)

        self.assertEqual(mb.count(), 1)
        self.assertEqual(mb.add_static((255, 90, 90, 255), (5, 10, 20, 255), 2), 1)
        self.assertEqual(mb.count(), 2)

    def test_generic_add(self):
        mb = self.mb
        self.assertEqual(mb.count(), 0)
        cb = materials.ComboMaterialPy()
        cb.count = 2
        cb.idx0 = 0
        cb.idx1 = 1

        self.assertEqual(mb.add_material(cb), 0)
        self.assertEqual(mb.count(), 1)

    def test_add_combo_material(self):
        mb = self.mb
        self.assertEqual(mb.count(), 0)
        cb = materials.ComboMaterialPy()
        cb.count = 2
        cb.idx0 = 0
        cb.idx1 = 1

        self.assertEqual(mb.add_combo_material(cb), 0)
        self.assertEqual(mb.count(), 1)

        cb = materials.ComboMaterialPy.from_list([5, 6, 7])
        self.assertEqual(cb.count, 3)
        self.assertEqual(cb.idx0, 5)
        self.assertEqual(cb.idx1, 6)
        self.assertEqual(cb.idx2, 7)

    def test_add_texture(self):
        texture_array = TextureBufferPy(12)
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        data = img.chained_data()
        texture_array.add_texture(
            img.image_width,
            img.image_height,
            data,
            repeat_width=True,
            repeat_height=True,
        )
        self.assertEqual(texture_array.size(), 1)

        mb = MaterialBufferPy()
        self.assertEqual(mb.add_textured(0, 1), 0)
        self.assertEqual(mb.count(), 1)
