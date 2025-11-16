# -*- coding: utf-8 -*-
import unittest

from tt3de.tt3de import DrawingBufferPy, GeometryBufferPy, MaterialBufferPy, PrimitiveBufferPy, TextureBufferPy, TransformPackPy, VertexBufferPy, materials
from tt3de.tt3de import apply_material_py
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture
from pyglm import glm


class InitSetup(unittest.TestCase):
    def setUp(self):
        self.mb = MaterialBufferPy()
        self.mb.add_material(materials.StaticColorBackPy((0, 0, 0, 255)))
        self.drawing_buffer = DrawingBufferPy(512, 512)
        self.drawing_buffer.hard_clear(1000)
        self.vertex_buffer = VertexBufferPy(128,128,128)
        self.primitive_buffer = PrimitiveBufferPy(256)
        self.texture_buffer = TextureBufferPy(4)
        return super().setUp()
class Test_ComboMaterial(InitSetup):

    def test_render_combo_material(self):
        mb = self.mb
        static_idx = mb.add_material(materials.StaticColorBackPy((255, 0, 0, 255)))
        color_front_idx = mb.add_material(materials.StaticColorFrontPy((0, 255, 0, 255)))
        glyph_idx = mb.add_material(materials.StaticGlyphPy(42))
        cb = materials.ComboMaterialPy.from_list([static_idx, color_front_idx, glyph_idx])


class Test_StaticMaterial(InitSetup):

    def test_render_static_background_material(self):
        mb = self.mb
        static_idx = mb.add_material(materials.StaticColorBackPy((128, 0, 0, 255)))
        color_front_idx = mb.add_material(materials.StaticColorFrontPy((0, 255, 0, 255)))
        glyph_idx = mb.add_material(materials.StaticGlyphPy(42))
        self.drawing_buffer.set_depth_content(0,0,glm.vec3(0,0,1), 1.0, glm.vec2(0,0), glm.vec2(0,0),
                                              0,1,static_idx,0)



        apply_material_py(
            self.mb,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer)

        cell_dict  = self.drawing_buffer.get_canvas_cell(0,0)
        self.assertEqual(cell_dict['f_r'], 0)
        self.assertEqual(cell_dict['f_g'], 0)
        self.assertEqual(cell_dict['f_b'], 0)

        self.assertEqual(cell_dict['b_r'], 128)
        self.assertEqual(cell_dict['b_g'], 0)
        self.assertEqual(cell_dict['b_b'], 0)
        self.assertEqual(cell_dict['glyph'], 0)
    def test_render_static_front_material(self):
        mb = self.mb

        static_idx = mb.add_material(materials.StaticColorBackPy((255, 0, 0, 255)))
        color_front_idx = mb.add_material(materials.StaticColorFrontPy((0, 255, 0, 255)))
        glyph_idx = mb.add_material(materials.StaticGlyphPy(42))
        self.drawing_buffer.set_depth_content(0,0,glm.vec3(0,0,1), 1.0, glm.vec2(0,0), glm.vec2(0,0),
                                              0,1,color_front_idx,0)


        apply_material_py(
            self.mb,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer)

        cell_dict  = self.drawing_buffer.get_canvas_cell(0,0)
        self.assertEqual(cell_dict['f_r'], 0)
        self.assertEqual(cell_dict['f_g'], 255)
        self.assertEqual(cell_dict['f_b'], 0)

        self.assertEqual(cell_dict['b_r'], 0)
        self.assertEqual(cell_dict['b_g'], 0)
        self.assertEqual(cell_dict['b_b'], 0)
        self.assertEqual(cell_dict['glyph'], 0)

    def test_render_static_glyph_material(self):
        mb = self.mb
        static_idx = mb.add_material(materials.StaticColorBackPy((255, 0, 0, 255)))
        color_front_idx = mb.add_material(materials.StaticColorFrontPy((0, 255, 0, 255)))
        glyph_idx = mb.add_material(materials.StaticGlyphPy(42))

        self.drawing_buffer.set_depth_content(0,0,glm.vec3(0,0,1), 1.0, glm.vec2(0,0), glm.vec2(0,0),
                                              0,1,glyph_idx,0)



        apply_material_py(
            self.mb,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer)

        cell_dict  = self.drawing_buffer.get_canvas_cell(0,0)
        self.assertEqual(cell_dict['f_r'], 0)
        self.assertEqual(cell_dict['f_g'], 0)
        self.assertEqual(cell_dict['f_b'], 0)

        self.assertEqual(cell_dict['b_r'], 0)
        self.assertEqual(cell_dict['b_g'], 0)
        self.assertEqual(cell_dict['b_b'], 0)

        self.assertEqual(cell_dict['glyph'], 42)
