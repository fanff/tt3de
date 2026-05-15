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
from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_DELTA_TIME,
    GLOBAL_VAR_TT_FAR,
    GLOBAL_VAR_TT_FRAME,
    GLOBAL_VAR_TT_NEAR,
    GLOBAL_VAR_TT_RESOLUTION,
    GLOBAL_VAR_TT_TIME,
    PIXELVAR_TT_FRONT_FACING,
    PIXELVAR_TT_FRAG_DEPTH,
    PIXELVAR_TT_LINE_COORD,
    PIXELVAR_TT_POINT_COORD,
    PIXELVAR_TT_PRIMITIVE_ID,
    PIXELVAR_TT_VIEW_POS,
    PIXELVAR_TT_NORMAL,
    all_passes_compilation,
)
from tt3de.ttsl.ttsl_assembly import IRType
from tt3de.ttsl.ttisa.ttisa_opcodes import OP_JMP_IF_FALSE, OP_RET

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
        bytecode = bytes([83, 0, 3, 2, 1, 0])
        mat = materials.ShaderPy(
            bytecode, time_f32_reg=11, default_glyph=219
        )
        self.assertEqual(mat.bytecode, bytecode)
        self.assertEqual(mat.time_f32_reg, 11)
        self.assertIsNone(mat.delta_time_f32_reg)
        self.assertIsNone(mat.frame_i32_reg)
        self.assertIsNone(mat.resolution_v2_reg)
        self.assertIsNone(mat.near_f32_reg)
        self.assertIsNone(mat.far_f32_reg)
        self.assertIsNone(mat.front_facing_bool_reg)
        self.assertIsNone(mat.frag_depth_f32_reg)
        self.assertIsNone(mat.line_coord_f32_reg)
        self.assertIsNone(mat.point_coord_v2_reg)
        self.assertEqual(mat.default_glyph, 219)

    def test_optional_time_and_glyph_none(self):
        mat = materials.ShaderPy(b"\xaa\xbb", time_f32_reg=None, default_glyph=None)
        self.assertEqual(mat.bytecode, b"\xaa\xbb")
        self.assertIsNone(mat.time_f32_reg)
        self.assertIsNone(mat.delta_time_f32_reg)
        self.assertIsNone(mat.frame_i32_reg)
        self.assertIsNone(mat.resolution_v2_reg)
        self.assertIsNone(mat.near_f32_reg)
        self.assertIsNone(mat.far_f32_reg)
        self.assertIsNone(mat.front_facing_bool_reg)

    def test_register_seed_roundtrip(self):
        seed = [{}, {1: 0.5}, {}, {}, {}, {}]
        mat = materials.ShaderPy(b"\x01", register_seed=seed)
        self.assertEqual(mat.register_seed, seed)

    def test_setters_roundtrip(self):
        mat = materials.ShaderPy(b"")
        mat.bytecode = b"\x01\x02"
        mat.time_f32_reg = 5
        mat.delta_time_f32_reg = 9
        mat.frame_i32_reg = 6
        mat.resolution_v2_reg = 8
        mat.near_f32_reg = 12
        mat.far_f32_reg = 13
        mat.front_facing_bool_reg = 3
        mat.frag_depth_f32_reg = 4
        mat.line_coord_f32_reg = 7
        mat.point_coord_v2_reg = 8
        mat.default_glyph = 64
        self.assertEqual(mat.bytecode, b"\x01\x02")
        self.assertEqual(mat.time_f32_reg, 5)
        self.assertEqual(mat.delta_time_f32_reg, 9)
        self.assertEqual(mat.frame_i32_reg, 6)
        self.assertEqual(mat.resolution_v2_reg, 8)
        self.assertEqual(mat.near_f32_reg, 12)
        self.assertEqual(mat.far_f32_reg, 13)
        self.assertEqual(mat.front_facing_bool_reg, 3)
        self.assertEqual(mat.frag_depth_f32_reg, 4)
        self.assertEqual(mat.line_coord_f32_reg, 7)
        self.assertEqual(mat.point_coord_v2_reg, 8)
        self.assertEqual(mat.default_glyph, 64)

        mat.time_f32_reg = None
        mat.delta_time_f32_reg = None
        mat.frame_i32_reg = None
        mat.resolution_v2_reg = None
        mat.near_f32_reg = None
        mat.far_f32_reg = None
        mat.front_facing_bool_reg = None
        mat.frag_depth_f32_reg = None
        mat.line_coord_f32_reg = None
        mat.point_coord_v2_reg = None
        mat.default_glyph = None
        self.assertIsNone(mat.time_f32_reg)
        self.assertIsNone(mat.delta_time_f32_reg)
        self.assertIsNone(mat.frame_i32_reg)
        self.assertIsNone(mat.resolution_v2_reg)
        self.assertIsNone(mat.near_f32_reg)
        self.assertIsNone(mat.far_f32_reg)
        self.assertIsNone(mat.front_facing_bool_reg)
        self.assertIsNone(mat.frag_depth_f32_reg)
        self.assertIsNone(mat.line_coord_f32_reg)
        self.assertIsNone(mat.point_coord_v2_reg)
        self.assertIsNone(mat.default_glyph)


class Test_ShaderPySetShaderTimeCompiled(unittest.TestCase):
    """Compiled TTSL + ``ShaderPy`` + ``MaterialBufferPy.set_shader_time`` updates the
    VM seed register so ``apply_material_py`` sees ``tt_Time``."""

    _DUMMY_SRC = dedent(
        """
        def dummy_time_red(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
            c: vec4 = vec4(tt_Time, 0.0, 0.0, 1.0)
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


class Test_ShaderPySetShaderDeltaTimeCompiled(unittest.TestCase):
    """``MaterialBufferPy.set_shader_delta_time`` updates the VM seed register for
    ``tt_DeltaTime`` (same seed-based contract as ``tt_Time``)."""

    _DUMMY_SRC = dedent(
        """
        def dummy_dt_green(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
            c: vec4 = vec4(0.0, tt_DeltaTime, 0.0, 1.0)
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

    def test_set_shader_delta_time_updates_compiled_dummy_shader_output(self):
        bytecode, reg_settings = all_passes_compilation(
            self._DUMMY_SRC, "dummy_dt_green", {GLOBAL_VAR_TT_DELTA_TIME: float}
        )
        _, dt_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_DELTA_TIME]

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode, delta_time_f32_reg=dt_reg, default_glyph=None
        )
        mat_idx = mb.add_shader(shader_mat)
        self.assertEqual(mat_idx, 0)

        mb.set_shader_delta_time(mat_idx, 0.25)
        cell_a = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_a["f_g"], int(0.25 * 256.0))

        mb.set_shader_delta_time(mat_idx, 0.5)
        cell_b = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_b["f_g"], int(0.5 * 256.0))

    def test_set_shader_delta_time_wrong_material_raises(self):
        mb = MaterialBufferPy()
        mb.add_static((255, 0, 0, 255), (0, 0, 0, 255), 0)
        with self.assertRaises(ValueError):
            mb.set_shader_delta_time(0, 1.0)


class Test_ShaderPySetShaderFrameCompiled(unittest.TestCase):
    """``MaterialBufferPy.set_shader_frame`` updates the VM seed register for
    ``tt_Frame``."""

    _DUMMY_SRC = dedent(
        """
        def dummy_frame_glyph(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
            c: vec4 = vec4(0.0, 0.0, 0.0, 1.0)
            return (c, c, tt_Frame)
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

    def test_set_shader_frame_updates_compiled_dummy_shader_output(self):
        bytecode, reg_settings = all_passes_compilation(
            self._DUMMY_SRC, "dummy_frame_glyph", {GLOBAL_VAR_TT_FRAME: int}
        )
        _, frame_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_FRAME]

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode, frame_i32_reg=frame_reg, default_glyph=None
        )
        mat_idx = mb.add_shader(shader_mat)
        self.assertEqual(mat_idx, 0)

        cell_default = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_default["glyph"], 0)

        mb.set_shader_frame(mat_idx, 23)
        cell_frame = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_frame["glyph"], 23)

    def test_set_shader_frame_wrong_material_raises(self):
        mb = MaterialBufferPy()
        mb.add_static((255, 0, 0, 255), (0, 0, 0, 255), 0)
        with self.assertRaises(ValueError):
            mb.set_shader_frame(0, 1)


class Test_ShaderPySetShaderResolutionCompiled(unittest.TestCase):
    """``MaterialBufferPy.set_shader_resolution`` updates ``tt_Resolution`` like
    ``tt_Time``."""

    _DUMMY_SRC = dedent(
        """
        def dummy_res_r(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
            c: vec4 = vec4(tt_Resolution.x / 100.0, 0.0, 0.0, 1.0)
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

    def test_set_shader_resolution_updates_compiled_shader_output(self):
        bytecode, reg_settings = all_passes_compilation(
            self._DUMMY_SRC, "dummy_res_r", {GLOBAL_VAR_TT_RESOLUTION: glm.vec2}
        )
        _, res_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_RESOLUTION]

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode,
            resolution_v2_reg=res_reg,
            default_glyph=None,
            register_seed=reg_settings.get_register_list(),
        )
        mat_idx = mb.add_shader(shader_mat)
        self.assertEqual(mat_idx, 0)

        cell_default = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_default["f_r"], int(1.0 / 100.0 * 256.0))

        mb.set_shader_resolution(mat_idx, 50.0, 10.0)
        cell_scaled = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_scaled["f_r"], int(50.0 / 100.0 * 256.0))

    def test_set_shader_resolution_wrong_material_raises(self):
        mb = MaterialBufferPy()
        mb.add_static((255, 0, 0, 255), (0, 0, 0, 255), 0)
        with self.assertRaises(ValueError):
            mb.set_shader_resolution(0, 4.0, 4.0)


class Test_ShaderPySetShaderNearFarCompiled(unittest.TestCase):
    """``set_shader_near`` / ``set_shader_far`` update ``tt_Near`` / ``tt_Far`` seed
    registers."""

    _DUMMY_SRC = dedent(
        """
        def dummy_clip(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
            c: vec4 = vec4(tt_Near, tt_Far / 400.0, 0.0, 1.0)
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

    def test_set_shader_near_and_far_update_compiled_shader_output(self):
        bytecode, reg_settings = all_passes_compilation(
            self._DUMMY_SRC,
            "dummy_clip",
            {GLOBAL_VAR_TT_NEAR: float, GLOBAL_VAR_TT_FAR: float},
        )
        _, near_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_NEAR]
        _, far_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_FAR]

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode,
            near_f32_reg=near_reg,
            far_f32_reg=far_reg,
            default_glyph=None,
            register_seed=reg_settings.get_register_list(),
        )
        mat_idx = mb.add_shader(shader_mat)
        self.assertEqual(mat_idx, 0)

        mb.set_shader_near(mat_idx, 0.25)
        mb.set_shader_far(mat_idx, 100.0)
        cell = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell["f_r"], int(0.25 * 256.0))
        self.assertEqual(cell["f_g"], int((100.0 / 400.0) * 256.0))

        mb.set_shader_near(mat_idx, 0.5)
        mb.set_shader_far(mat_idx, 200.0)
        cell_b = self._apply_shader_at_origin(mb, mat_idx)
        self.assertEqual(cell_b["f_r"], int(0.5 * 256.0))
        self.assertEqual(cell_b["f_g"], int((200.0 / 400.0) * 256.0))

    def test_set_shader_near_wrong_material_raises(self):
        mb = MaterialBufferPy()
        mb.add_static((255, 0, 0, 255), (0, 0, 0, 255), 0)
        with self.assertRaises(ValueError):
            mb.set_shader_near(0, 1.0)

    def test_set_shader_far_wrong_material_raises(self):
        mb = MaterialBufferPy()
        mb.add_static((255, 0, 0, 255), (0, 0, 0, 255), 0)
        with self.assertRaises(ValueError):
            mb.set_shader_far(0, 100.0)


class Test_ShaderPyFrontFacingMaterialBridge(unittest.TestCase):
    """
    ``ShaderPy.front_facing_bool_reg`` matches ``PixInfo.front_facing`` from
    ``set_depth_content``.

    Uses hand-written branch bytecode (same minimal shape as ``test_runttsl`` and the Rust
    ``jmp_if_false_routes_to_else_ret_without_phi`` test) because compiled TTSL ``if`` /
    phi lowering for ``tt_FrontFacing`` is tracked separately.
    """

    _SEED_SRC = dedent(
        """
        def seed_ff(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """
    )

    def _cell_at_origin(self, mb: MaterialBufferPy, mat_idx: int, *, front_facing: bool):
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
            front_facing,
        )
        apply_material_py(
            mb,
            TextureBufferPy(4),
            VertexBufferPy(16, 16, 16),
            PrimitiveBufferPy(8),
            draw,
        )
        return draw.get_canvas_cell(0, 0)

    def test_front_facing_bool_register_colors_material_output(self):
        _, reg_settings = all_passes_compilation(self._SEED_SRC, "seed_ff", {})
        _, ff_reg = reg_settings.var_name_to_registers[PIXELVAR_TT_FRONT_FACING]
        red_v4_reg = 10
        green_v4_reg = 11
        reg_settings.set_register(IRType.V4, red_v4_reg, glm.vec4(1.0, 0.0, 0.0, 1.0))
        reg_settings.set_register(IRType.V4, green_v4_reg, glm.vec4(0.0, 1.0, 0.0, 1.0))
        seed_regs = reg_settings.get_register_list()

        bytecode = bytes(
            [
                OP_JMP_IF_FALSE,
                2,
                ff_reg,
                0,
                0,
                0,
                OP_RET,
                0,
                red_v4_reg,
                red_v4_reg,
                0,
                0,
                OP_RET,
                0,
                green_v4_reg,
                green_v4_reg,
                0,
                0,
            ]
        )
        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode,
            front_facing_bool_reg=ff_reg,
            default_glyph=None,
            register_seed=seed_regs,
        )
        mat_idx = mb.add_shader(shader_mat)
        self.assertEqual(mat_idx, 0)

        cell_front = self._cell_at_origin(mb, mat_idx, front_facing=True)
        self.assertGreater(cell_front["f_r"], 200)
        self.assertLess(cell_front["f_g"], 50)

        cell_back = self._cell_at_origin(mb, mat_idx, front_facing=False)
        self.assertLess(cell_back["f_r"], 50)
        self.assertGreater(cell_back["f_g"], 200)


class Test_ShaderPyPrimitiveIDFlow(unittest.TestCase):
    """End-to-end: ``tt_PrimitiveID`` flows from ``DrawingBufferPy.set_depth_content``
    (rasterizer surrogate) through ``PixInfo::primitive_id`` to a TTSL shader. No
    ``ShaderPy`` field is needed because ``tt_PrimitiveID`` is always-present and
    ``ShaderInputBinding::default()`` mirrors the allocator's pinned i32 reg 0.
    """

    _SRC = dedent(
        """
        def primid_glyph(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
            return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), tt_PrimitiveID)
        """
    )

    def _apply_with_primitive_id(
        self, mb: MaterialBufferPy, mat_idx: int, primitive_id: int
    ) -> dict:
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
            primitive_id,
        )
        apply_material_py(
            mb,
            TextureBufferPy(4),
            VertexBufferPy(16, 16, 16),
            # Capacity must exceed max primitive_id used below; ``apply_material`` indexes
            # ``primitive_buffer.content[pixinfo.primitive_id]`` directly
            # (see ``src/material/mod.rs``).
            PrimitiveBufferPy(256),
            draw,
        )
        return draw.get_canvas_cell(0, 0)

    def test_primitive_id_flows_into_compiled_shader_glyph(self):
        bytecode, reg_settings = all_passes_compilation(self._SRC, "primid_glyph", {})
        _ty, pid_reg = reg_settings.var_name_to_registers[PIXELVAR_TT_PRIMITIVE_ID]
        # Pinned by the allocator special-case to i32 reg 0 — matches
        # ``ShaderInputBinding::primitive_id_i32_reg`` (default 0).
        self.assertEqual(pid_reg, 0)

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(bytecode, default_glyph=None)
        mat_idx = mb.add_shader(shader_mat)

        for primitive_id in (0, 5, 99, 200):
            cell = self._apply_with_primitive_id(mb, mat_idx, primitive_id)
            self.assertEqual(
                cell["glyph"],
                primitive_id,
                f"shader glyph must mirror primitive_id={primitive_id}",
            )


class Test_ShaderPyViewPosMaterialBridge(unittest.TestCase):
    """``tt_ViewPos`` flows from ``DrawingBufferPy.set_depth_content(..., view_pos=...)`` through
    ``PixInfo::view_pos`` into the VM (``ShaderInputBinding::view_pos_v3_reg`` default ``3``).
    """

    _SRC = dedent(
        """
        def vp_rgb(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            return (
                vec4(tt_ViewPos.x, tt_ViewPos.y, tt_ViewPos.z, 1.0),
                vec4(0.0, 0.0, 0.0, 1.0),
                0,
            )
        """
    )

    def test_view_pos_flows_into_front_color(self):
        bytecode, reg_settings = all_passes_compilation(self._SRC, "vp_rgb", {})
        ty, rid = reg_settings.var_name_to_registers[PIXELVAR_TT_VIEW_POS]
        self.assertEqual(ty, IRType.V3)
        self.assertEqual(rid, 3)

        draw = DrawingBufferPy(4, 4)
        draw.hard_clear(10.0)
        vp = glm.vec3(0.1, 0.2, 0.3)
        draw.set_depth_content(
            0,
            0,
            glm.vec3(0.0, 0.0, 1.0),
            1.0,
            glm.vec2(0.25, 0.75),
            glm.vec2(0.0, 0.0),
            0,
            0,
            0,
            0,
            view_pos=vp,
        )
        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(bytecode, default_glyph=None)
        mat_idx = mb.add_shader(shader_mat)
        apply_material_py(
            mb,
            TextureBufferPy(4),
            VertexBufferPy(16, 16, 16),
            PrimitiveBufferPy(256),
            draw,
        )
        cell = draw.get_canvas_cell(0, 0)
        self.assertAlmostEqual(cell["f_r"] / 255.0, vp.x, places=2)
        self.assertAlmostEqual(cell["f_g"] / 255.0, vp.y, places=2)
        self.assertAlmostEqual(cell["f_b"] / 255.0, vp.z, places=2)


class Test_ShaderPyNormalMaterialBridge(unittest.TestCase):
    """``tt_Normal`` flows from ``DrawingBufferPy.set_depth_content`` (first ``glm.vec3`` arg)
    through ``PixInfo::normal`` into ``regs.v3[2]`` (``ShaderInputBinding::normal_v3_reg``).
    """

    _SRC = dedent(
        """
        def n_rgb(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            return (
                vec4(tt_Normal.x, tt_Normal.y, tt_Normal.z, 1.0),
                vec4(0.0, 0.0, 0.0, 1.0),
                0,
            )
        """
    )

    def test_normal_flows_into_front_color(self):
        bytecode, reg_settings = all_passes_compilation(self._SRC, "n_rgb", {})
        ty, rid = reg_settings.var_name_to_registers[PIXELVAR_TT_NORMAL]
        self.assertEqual(ty, IRType.V3)
        self.assertEqual(rid, 2)

        draw = DrawingBufferPy(4, 4)
        draw.hard_clear(10.0)
        n = glm.vec3(0.25, 0.5, 0.75)
        draw.set_depth_content(
            0,
            0,
            n,
            1.0,
            glm.vec2(0.25, 0.75),
            glm.vec2(0.0, 0.0),
            0,
            0,
            0,
            0,
        )
        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(bytecode, default_glyph=None)
        mat_idx = mb.add_shader(shader_mat)
        apply_material_py(
            mb,
            TextureBufferPy(4),
            VertexBufferPy(16, 16, 16),
            PrimitiveBufferPy(256),
            draw,
        )
        cell = draw.get_canvas_cell(0, 0)
        self.assertAlmostEqual(cell["f_r"] / 255.0, n.x, places=2)
        self.assertAlmostEqual(cell["f_g"] / 255.0, n.y, places=2)
        self.assertAlmostEqual(cell["f_b"] / 255.0, n.z, places=2)


class Test_ShaderPyFragDepthMaterialBridge(unittest.TestCase):
    """``ShaderPy.frag_depth_f32_reg`` receives ``DepthBufferCell::depth[layer]`` for the layer
    being shaded (same value passed into ``set_depth_content`` for a single-layer submission).
    """

    _SRC = dedent(
        """
        def depth_red(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            return (vec4(tt_FragDepth, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """
    )

    def _cell_at_origin(self, mb: MaterialBufferPy, mat_idx: int, *, depth: float) -> dict:
        draw = DrawingBufferPy(4, 4)
        draw.hard_clear(10.0)
        draw.set_depth_content(
            0,
            0,
            glm.vec3(0.0, 0.0, 1.0),
            depth,
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

    def test_frag_depth_flows_into_compiled_shader_front_color(self):
        bytecode, reg_settings = all_passes_compilation(self._SRC, "depth_red", {})
        _ty, fd_reg = reg_settings.var_name_to_registers[PIXELVAR_TT_FRAG_DEPTH]

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode,
            frag_depth_f32_reg=fd_reg,
            default_glyph=None,
        )
        mat_idx = mb.add_shader(shader_mat)

        depth = 0.375
        cell = self._cell_at_origin(mb, mat_idx, depth=depth)
        expected_r = int(depth * 256.0)
        self.assertEqual(cell["f_r"], expected_r)
        self.assertLess(cell["f_g"], 8)
        self.assertLess(cell["f_b"], 8)


class Test_ShaderPyLineCoordMaterialBridge(unittest.TestCase):
    """``ShaderPy.line_coord_f32_reg`` receives ``PixInfo::line_coord`` (see ``set_depth_content``)."""

    _SRC = dedent(
        """
        def line_red(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            return (vec4(tt_LineCoord, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """
    )

    def _cell_at_origin(self, mb: MaterialBufferPy, mat_idx: int, *, line_coord: float) -> dict:
        draw = DrawingBufferPy(4, 4)
        draw.hard_clear(10.0)
        draw.set_depth_content(
            0,
            0,
            glm.vec3(0.0, 0.0, 1.0),
            0.25,
            glm.vec2(0.0, 0.0),
            glm.vec2(0.0, 0.0),
            0,
            0,
            mat_idx,
            0,
            line_coord=line_coord,
        )
        apply_material_py(
            mb,
            TextureBufferPy(4),
            VertexBufferPy(16, 16, 16),
            PrimitiveBufferPy(8),
            draw,
        )
        return draw.get_canvas_cell(0, 0)

    def test_line_coord_flows_into_compiled_shader_front_color(self):
        bytecode, reg_settings = all_passes_compilation(self._SRC, "line_red", {})
        _ty, lc_reg = reg_settings.var_name_to_registers[PIXELVAR_TT_LINE_COORD]

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode,
            line_coord_f32_reg=lc_reg,
            default_glyph=None,
        )
        mat_idx = mb.add_shader(shader_mat)

        coord = 0.5
        cell = self._cell_at_origin(mb, mat_idx, line_coord=coord)
        expected_r = int(coord * 256.0)
        self.assertEqual(cell["f_r"], expected_r)
        self.assertLess(cell["f_g"], 8)
        self.assertLess(cell["f_b"], 8)


class Test_ShaderPyPointCoordMaterialBridge(unittest.TestCase):
    """``ShaderPy.point_coord_v2_reg`` receives ``PixInfo::point_coord`` (see ``set_depth_content``)."""

    _SRC = dedent(
        """
        def point_xy(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            return (vec4(tt_PointCoord.x, tt_PointCoord.y, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """
    )

    def _cell_at_origin(self, mb: MaterialBufferPy, mat_idx: int, *, pc: glm.vec2) -> dict:
        draw = DrawingBufferPy(4, 4)
        draw.hard_clear(10.0)
        draw.set_depth_content(
            0,
            0,
            glm.vec3(0.0, 0.0, 1.0),
            0.25,
            glm.vec2(0.0, 0.0),
            glm.vec2(0.0, 0.0),
            0,
            0,
            mat_idx,
            0,
            point_coord=pc,
        )
        apply_material_py(
            mb,
            TextureBufferPy(4),
            VertexBufferPy(16, 16, 16),
            PrimitiveBufferPy(8),
            draw,
        )
        return draw.get_canvas_cell(0, 0)

    def test_point_coord_flows_into_compiled_shader_front_color(self):
        bytecode, reg_settings = all_passes_compilation(self._SRC, "point_xy", {})
        _ty, pc_reg = reg_settings.var_name_to_registers[PIXELVAR_TT_POINT_COORD]

        mb = MaterialBufferPy()
        shader_mat = materials.ShaderPy(
            bytecode,
            point_coord_v2_reg=pc_reg,
            default_glyph=None,
        )
        mat_idx = mb.add_shader(shader_mat)

        pc = glm.vec2(0.25, 0.5)
        cell = self._cell_at_origin(mb, mat_idx, pc=pc)
        self.assertEqual(cell["f_r"], int(pc.x * 256.0))
        self.assertEqual(cell["f_g"], int(pc.y * 256.0))
        self.assertLess(cell["f_b"], 8)


class Test_ShaderPySeedValidation(unittest.TestCase):
    def test_add_shader_rejects_register_seed_wrong_length(self):
        mb = MaterialBufferPy()
        bad = materials.ShaderPy(
            bytes([83, 0, 0, 0, 0, 0]),
            register_seed=[{}, {}, {}],
        )
        with self.assertRaises(ValueError):
            mb.add_shader(bad)
