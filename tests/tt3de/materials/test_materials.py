# -*- coding: utf-8 -*-
import unittest

from tt3de.tt3de import (
    DrawingBufferPy,
    GeometryBufferPy,
    MaterialBufferPy,
    PrimitiveBufferPy,
    TextureBufferPy,
    TransformPackPy,
    VertexBufferPy,
    materials,
)
from tt3de.tt3de import apply_material_py
from tt3de.tt3de import toglyphmethod
from tt3de.tt3de.toglyphmethod import (
    ToGlyphMethodPyMap4Luminance,
    ToGlyphMethodPyStatic,
)
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture
from pyglm import glm


class InitSetup(unittest.TestCase):
    def setUp(self):
        self.mb = MaterialBufferPy()

        self.mb.add_static_color(
            materials.StaticColorPy(
                False, False, False, (0, 0, 0, 255), (0, 0, 0, 255), 0
            )
        )
        self.drawing_buffer = DrawingBufferPy(512, 512)
        self.drawing_buffer.hard_clear(1000)
        self.vertex_buffer = VertexBufferPy(128, 128, 128)
        self.primitive_buffer = PrimitiveBufferPy(256)
        self.texture_buffer = TextureBufferPy(4)
        return super().setUp()


class Test_BaseTextured(InitSetup):
    def test_textured(self):
        mb = self.mb
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        data = img.chained_data()
        tex_idx = self.texture_buffer.add_texture(
            img.image_width,
            img.image_height,
            data,
        )
        glyph_method = ToGlyphMethodPyMap4Luminance((65, 66, 67, 68))
        glyph_method = ToGlyphMethodPyStatic(65)
        textured_front = materials.BaseTexturePy(
            albedo_texture_idx=tex_idx,
            albedo_texture_subid=0,
            glyph_texture_idx=tex_idx,
            glyph_texture_subid=0,
            front=True,
            back=True,
            glyph=True,
            front_uv_0=True,
            back_uv_0=False,
            glyph_uv_0=True,
            glyph_method=glyph_method,
        )
        tex_front_idx = mb.add_base_texture(textured_front)
        self.drawing_buffer.set_depth_content(
            0,
            0,
            glm.vec3(0, 0, 1),
            1.0,
            glm.vec2(0, 0),
            glm.vec2(0, 0),
            0,
            1,
            tex_front_idx,
            0,
        )
        apply_material_py(
            self.mb,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer,
        )

        cell_dict = self.drawing_buffer.get_canvas_cell(0, 0)
        self.assertNotEqual(cell_dict["f_r"], 0)
        self.assertNotEqual(cell_dict["f_g"], 0)
        self.assertNotEqual(cell_dict["f_b"], 0)
        self.assertNotEqual(cell_dict["b_r"], 0)
        self.assertNotEqual(cell_dict["b_g"], 0)
        self.assertNotEqual(cell_dict["b_b"], 0)
        self.assertEqual(cell_dict["glyph"], 65)

    def test_textured_flips(self):
        mb = self.mb
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        data = img.chained_data()
        tex_idx = self.texture_buffer.add_texture(
            img.image_width,
            img.image_height,
            data,
        )
        glyph_method = ToGlyphMethodPyMap4Luminance((65, 66, 67, 68))

        def front_is_set(cell_dict, *args):
            self.assertNotEqual(cell_dict["f_r"], 0)
            self.assertNotEqual(cell_dict["f_g"], 0)
            self.assertNotEqual(cell_dict["f_b"], 0)

        def front_is_zero(cell_dict, *args):
            self.assertEqual(cell_dict["f_r"], 0)
            self.assertEqual(cell_dict["f_g"], 0)
            self.assertEqual(cell_dict["f_b"], 0)

        def back_is_set(cell_dict, *args):
            self.assertNotEqual(cell_dict["b_r"], 0)
            self.assertNotEqual(cell_dict["b_g"], 0)
            self.assertNotEqual(cell_dict["b_b"], 0)

        def back_is_zero(cell_dict, *args):
            self.assertEqual(cell_dict["b_r"], 0)
            self.assertEqual(cell_dict["b_g"], 0)
            self.assertEqual(cell_dict["b_b"], 0)

        def glyph_is_zero(cell_dict, *args):
            self.assertEqual(cell_dict["glyph"], 0)

        def glyph_is(glyph_value):
            def c(cell_dict):
                assert cell_dict["glyph"] == glyph_value

            return c

        cases = [
            ((False, False, False), [front_is_zero, back_is_zero, glyph_is(0)]),
            ((True, False, False), [front_is_set, back_is_zero, glyph_is_zero]),
            ((True, False, True), [front_is_set, back_is_zero, glyph_is(68)]),
            ((False, False, True), [front_is_zero, back_is_zero, glyph_is(68)]),
            ((False, True, True), [front_is_zero, back_is_set, glyph_is(68)]),
        ]
        for (front, back, glyph), assertions in cases:
            with self.subTest(front=front, back=back, glyph=glyph):
                self.drawing_buffer = DrawingBufferPy(512, 512)
                self.drawing_buffer.hard_clear(1000)
                textured_front = materials.BaseTexturePy(
                    albedo_texture_idx=tex_idx,
                    albedo_texture_subid=0,
                    glyph_texture_idx=tex_idx,
                    glyph_texture_subid=0,
                    front=front,
                    back=back,
                    glyph=glyph,
                    front_uv_0=True,
                    back_uv_0=False,
                    glyph_uv_0=True,
                    glyph_method=glyph_method,
                )
                tex_front_idx = mb.add_base_texture(textured_front)
                self.drawing_buffer.set_depth_content(
                    0,
                    0,
                    glm.vec3(0, 0, 1),
                    1.0,
                    glm.vec2(0, 0),
                    glm.vec2(0, 0),
                    0,
                    1,
                    tex_front_idx,
                    0,
                )
                apply_material_py(
                    self.mb,
                    self.texture_buffer,
                    self.vertex_buffer,
                    self.primitive_buffer,
                    self.drawing_buffer,
                )

                cell_dict = self.drawing_buffer.get_canvas_cell(0, 0)
                for assertion in assertions:
                    assertion(cell_dict)


class Test_ComboMaterial(InitSetup):
    def test_render_combo_material(self):
        mb = self.mb
        color_back_idx = mb.add_static_color(
            materials.StaticColorPy(
                False, True, False, (0, 0, 0, 255), (128, 0, 0, 255), 0
            )
        )
        color_front_idx = mb.add_static_color(
            materials.StaticColorPy(
                True, False, False, (0, 255, 0, 255), (0, 0, 0, 255), 0
            )
        )
        glyph_idx = mb.add_static_color(
            materials.StaticColorPy(
                False, False, True, (0, 255, 0, 255), (0, 0, 0, 255), 42
            )
        )

        cb = materials.ComboMaterialPy.from_list(
            [color_back_idx, color_front_idx, glyph_idx]
        )
        cbidx = mb.add_combo_material(cb)
        self.drawing_buffer.set_depth_content(
            0, 0, glm.vec3(0, 0, 1), 1.0, glm.vec2(0, 0), glm.vec2(0, 0), 0, 1, cbidx, 0
        )
        apply_material_py(
            self.mb,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer,
        )

        cell_dict = self.drawing_buffer.get_canvas_cell(0, 0)
        self.assertEqual(cell_dict["f_r"], 0)
        self.assertEqual(cell_dict["f_g"], 255)
        self.assertEqual(cell_dict["f_b"], 0)

        self.assertEqual(cell_dict["b_r"], 128)
        self.assertEqual(cell_dict["b_g"], 0)
        self.assertEqual(cell_dict["b_b"], 0)
        self.assertEqual(cell_dict["glyph"], 42)


class Test_StaticMaterial(InitSetup):
    def test_render_static_background_material(self):
        mb = self.mb
        color_back_idx = mb.add_static_color(
            materials.StaticColorPy(
                False, True, False, (0, 0, 0, 255), (128, 0, 0, 255), 0
            )
        )

        self.drawing_buffer.set_depth_content(
            0,
            0,
            glm.vec3(0, 0, 1),
            1.0,
            glm.vec2(0, 0),
            glm.vec2(0, 0),
            0,
            1,
            color_back_idx,
            0,
        )

        apply_material_py(
            self.mb,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer,
        )

        cell_dict = self.drawing_buffer.get_canvas_cell(0, 0)
        self.assertEqual(cell_dict["f_r"], 0)
        self.assertEqual(cell_dict["f_g"], 0)
        self.assertEqual(cell_dict["f_b"], 0)

        self.assertEqual(cell_dict["b_r"], 128)
        self.assertEqual(cell_dict["b_g"], 0)
        self.assertEqual(cell_dict["b_b"], 0)
        self.assertEqual(cell_dict["glyph"], 0)

    def test_render_static_front_material(self):
        mb = self.mb

        color_front_idx = mb.add_static_color(
            materials.StaticColorPy(
                True, False, False, (0, 255, 0, 255), (0, 0, 0, 255), 0
            )
        )
        self.drawing_buffer.set_depth_content(
            0,
            0,
            glm.vec3(0, 0, 1),
            1.0,
            glm.vec2(0, 0),
            glm.vec2(0, 0),
            0,
            1,
            color_front_idx,
            0,
        )

        apply_material_py(
            self.mb,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer,
        )

        cell_dict = self.drawing_buffer.get_canvas_cell(0, 0)
        self.assertEqual(cell_dict["f_r"], 0)
        self.assertEqual(cell_dict["f_g"], 255)
        self.assertEqual(cell_dict["f_b"], 0)

        self.assertEqual(cell_dict["b_r"], 0)
        self.assertEqual(cell_dict["b_g"], 0)
        self.assertEqual(cell_dict["b_b"], 0)
        self.assertEqual(cell_dict["glyph"], 0)

    def test_render_static_glyph_material(self):
        mb = self.mb
        glyph_idx = mb.add_static_color(
            materials.StaticColorPy(
                False, False, True, (0, 255, 0, 255), (0, 0, 0, 255), 42
            )
        )

        self.drawing_buffer.set_depth_content(
            0,
            0,
            glm.vec3(0, 0, 1),
            1.0,
            glm.vec2(0, 0),
            glm.vec2(0, 0),
            0,
            1,
            glyph_idx,
            0,
        )

        apply_material_py(
            self.mb,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer,
        )

        cell_dict = self.drawing_buffer.get_canvas_cell(0, 0)
        self.assertEqual(cell_dict["f_r"], 0)
        self.assertEqual(cell_dict["f_g"], 0)
        self.assertEqual(cell_dict["f_b"], 0)

        self.assertEqual(cell_dict["b_r"], 0)
        self.assertEqual(cell_dict["b_g"], 0)
        self.assertEqual(cell_dict["b_b"], 0)

        self.assertEqual(cell_dict["glyph"], 42)
