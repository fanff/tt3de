# -*- coding: utf-8 -*-


import unittest
from tt3de.tt3de import find_glyph_indices_py


class Test_DrawBuffer(unittest.TestCase):
    def test_find_glyph(self):
        self.assertEqual(find_glyph_indices_py(" "), 0)
        self.assertEqual(find_glyph_indices_py("2"), 18)
        self.assertEqual(find_glyph_indices_py("E"), 37)
        self.assertEqual(find_glyph_indices_py("X"), 56)
        self.assertEqual(find_glyph_indices_py("k"), 75)

        self.assertEqual(find_glyph_indices_py("~"), 94)
        self.assertEqual(find_glyph_indices_py("▀"), 95)
        self.assertEqual(find_glyph_indices_py("█"), 103)
