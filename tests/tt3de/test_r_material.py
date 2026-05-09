# -*- coding: utf-8 -*-
import unittest
from textwrap import dedent

from pyglm import glm

from tt3de.tt3de import (
    DrawingBufferPy,
    MaterialBufferPy,
    PrimitiveBufferPy,
    TextureBufferPy,
    VertexBufferPy,
    apply_material_py,
    materials,
)
from tt3de.ttsl.compiler import GLOBAL_VAR_TT_TIME, all_passes_compilation

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

        with self.assertRaises(TypeError):
            mb.add_material(cb)
        self.assertEqual(mb.count(), 0)

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


class Test_ShaderPyAccessors(unittest.TestCase):
    """Rust ``ShaderPy``: Python-visible fields match ``materials.pyi``."""

    def test_ctor_exposes_bytecode_time_reg_default_glyph(self):
        bytecode = bytes([82, 0, 3, 2, 1, 0])
        mat = materials.ShaderPy(
            bytecode, time_f32_reg=11, default_glyph=219
        )
        self.assertEqual(mat.bytecode, bytecode)
        self.assertEqual(mat.time_f32_reg, 11)
        self.assertEqual(mat.default_glyph, 219)

    def test_optional_time_and_glyph_none(self):
        mat = materials.ShaderPy(b"\xaa\xbb", time_f32_reg=None, default_glyph=None)
        self.assertEqual(mat.bytecode, b"\xaa\xbb")
        self.assertIsNone(mat.time_f32_reg)
        self.assertIsNone(mat.default_glyph)
        self.assertIsNone(mat.register_seed)

    def test_register_seed_roundtrip(self):
        seed = [{}, {1: 0.5}, {}, {}, {}, {}]
        mat = materials.ShaderPy(b"\x01", register_seed=seed)
        self.assertEqual(mat.register_seed, seed)

    def test_setters_roundtrip(self):
        mat = materials.ShaderPy(b"")
        mat.bytecode = b"\x01\x02"
        mat.time_f32_reg = 5
        mat.default_glyph = 64
        self.assertEqual(mat.bytecode, b"\x01\x02")
        self.assertEqual(mat.time_f32_reg, 5)
        self.assertEqual(mat.default_glyph, 64)

        mat.time_f32_reg = None
        mat.default_glyph = None
        self.assertIsNone(mat.time_f32_reg)
        self.assertIsNone(mat.default_glyph)


class Test_ShaderPySetShaderTimeCompiled(unittest.TestCase):
    """
    Compiled TTSL + ``ShaderPy`` + ``MaterialBufferPy.set_shader_time`` updates the
    VM seed register so ``apply_material_py`` sees ``tt_Time``.
    """

    _DUMMY_SRC = dedent(
        """
        def dummy_time_red(tt_TexCoord0: vec2) -> tuple[vec3, vec3, int]:
            c: vec3 = vec3(tt_Time, 0.0, 0.0)
            return (c, c, 0)
        """
    )

    def _apply_shader_at_origin(self, mb: MaterialBufferPy, mat_idx: int) -> dict:
        draw = DrawingBufferPy(4, 4)
        draw.hard_clear(10.0)
        draw.set_depth_content(
            0,
            0,
            glm.vec3(0.0, 0.0, 1.0),
            1.0,
            glm.vec2(0.25, 0.75),
            glm.vec2(0.0, 0.0),
            0,
            0,
            mat_idx,
            0,
        )
        apply_material_py(
            mb,
            TextureBufferPy(4),
            VertexBufferPy(16, 16, 16),
            PrimitiveBufferPy(8),
            draw,
        )
        return draw.get_canvas_cell(0, 0)

    def test_set_shader_time_updates_compiled_dummy_shader_output(self):
        bytecode, reg_settings = all_passes_compilation(
            self._DUMMY_SRC, "dummy_time_red", {GLOBAL_VAR_TT_TIME: float}
        )
        _, time_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_TIME]

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode, time_f32_reg=time_reg, default_glyph=None
        )
        mat_idx = mb.add_shader(shader_mat)
        self.assertEqual(mat_idx, 0)

        mb.set_shader_time(mat_idx, 0.25)
        cell_a = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_a["f_g"], 0)
        self.assertEqual(cell_a["f_b"], 0)
        self.assertEqual(cell_a["f_r"], int(0.25 * 256.0))

        mb.set_shader_time(mat_idx, 0.5)
        cell_b = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_b["f_r"], int(0.5 * 256.0))

    def test_set_shader_time_wrong_material_raises(self):
        mb = MaterialBufferPy()
        mb.add_static((255, 0, 0, 255), (0, 0, 0, 255), 0)
        with self.assertRaises(ValueError):
            mb.set_shader_time(0, 1.0)

    def test_add_shader_rejects_register_seed_wrong_length(self):
        mb = MaterialBufferPy()
        bad = materials.ShaderPy(
            bytes([82, 0, 0, 0, 0, 0]),
            register_seed=[{}, {}, {}],
        )
        with self.assertRaises(ValueError):
            mb.add_shader(bad)
