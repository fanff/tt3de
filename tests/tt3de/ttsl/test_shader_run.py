# -*- coding: utf-8 -*-
from textwrap import dedent
import unittest

from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_FRAME,
    GLOBAL_VAR_TT_RESOLUTION,
    PIXELVAR_TT_FRAGPOS,
    PIXELVAR_TT_FRONT_FACING,
    PIXELVAR_TT_PRIMITIVE_ID,
    PIXELVAR_TT_TEXCOORD0,
    all_passes_compilation,
    passthrough_ssa_json,
)
from tt3de.ttsl.ttsl_assembly import IRType

from pyglm import glm

from tests.tt3de.ttsl.shade import shade


class Test_OPCodes(unittest.TestCase):
    def test_emptyshader(self):
        regs = [{}] * 6
        run_result = shade(regs, passthrough_ssa_json())
        assert isinstance(run_result, tuple)
        assert len(run_result) == 3

    def test_returnshader(self):
        regs = [{}] * 6
        regs[5] = {1: glm.vec4(0.5, 0.5, 0.0, 1.0)}
        run_result = shade(regs, passthrough_ssa_json(front_reg=1, back_reg=1, glyph_reg=0))
        assert isinstance(run_result, tuple)
        assert len(run_result) == 3
        front, back, glyphidx = run_result
        assert front == glm.vec4(0.5, 0.5, 0.0, 1.0)
        assert back == glm.vec4(0.5, 0.5, 0.0, 1.0)
        assert glyphidx == 0


class Test_RunTTSL(unittest.TestCase):
    def test_samplerun(self):

        reg_types = [
            IRType.BOOL,
            IRType.F32,
            IRType.I32,
            IRType.V2,
            IRType.V3,
            IRType.V4,
        ]

        # prepare sample registers
        regs = []
        for ty in reg_types:
            reg = {}
            for i in range(3):
                if ty == IRType.BOOL:
                    reg[i] = True
                elif ty == IRType.F32:
                    reg[i] = float(i) * 1.5
                elif ty == IRType.I32:
                    reg[i] = (i + 1) * 2
                elif ty == IRType.V2:
                    reg[i] = glm.vec2(float(i), float(i) + 1.0)
                elif ty == IRType.V3:
                    reg[i] = glm.vec3(float(i), float(i) + 1.0, float(i) + 2.0)
                elif ty == IRType.V4:
                    reg[i] = glm.vec4(
                        float(i), float(i) + 1.0, float(i) + 2.0, float(i) + 3.0
                    )
            regs.append(reg)
        # prepare sample shader (identity: return seeded v4[0] / v4[0] / i32[0])
        ssa_json = passthrough_ssa_json()
        run_result = shade(regs, ssa_json)
        assert isinstance(run_result, tuple)
        assert len(run_result) == 3

        front, back, glyphidx = run_result
        assert isinstance(front, glm.vec4)
        assert isinstance(back, glm.vec4)
        assert isinstance(glyphidx, int)

        assert front == glm.vec4(0.0, 1.0, 2.0, 3.0)
        assert back == glm.vec4(0.0, 1.0, 2.0, 3.0)
        assert glyphidx == 2

    def test_with_compiled_code(self):

        shader_code = dedent(
            """
        def frag(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            c: vec4 = vec4(tt_TexCoord0.x, tt_TexCoord0.y, 0.0, 1.0)
            return (c, c, 0)
        """
        )
        bytecode, reg_settings = all_passes_compilation(shader_code, "frag", {})
        # reg_settings.set_variable(GLOBAL_VAR_TT_TIME, 1221.1)
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.5, 0.5))
        # reg_settings.set_variable(PIXELVAR_TT_TEXCOORD1, glm.vec2(0.5, 0.5))
        # reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(0.5, 0.5))

        # from the rar, prepare the registers
        regs = reg_settings.get_register_list()

        run_result = shade(regs, reg_settings.ssa_json())
        assert isinstance(run_result, tuple)
        assert len(run_result) == 3
        front, back, glyphidx = run_result
        assert front == glm.vec4(0.5, 0.5, 0.0, 1.0)
        assert back == glm.vec4(0.5, 0.5, 0.0, 1.0)
        assert glyphidx == 0

    def test_with_compiled_code_tt_FragPos_register(self):
        shader_code = dedent(
            """
        def frag(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            c: vec4 = vec4(tt_FragPos.x, tt_FragPos.y, 0.0, 1.0)
            return (c, c, 0)
        """
        )
        bytecode, reg_settings = all_passes_compilation(shader_code, "frag", {})
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.0, 0.0))
        reg_settings.set_variable(PIXELVAR_TT_FRAGPOS, glm.vec2(0.25, -0.5))

        regs = reg_settings.get_register_list()
        front, back, glyphidx = shade(regs, reg_settings.ssa_json())
        assert front == glm.vec4(0.25, -0.5, 0.0, 1.0)
        assert back == glm.vec4(0.25, -0.5, 0.0, 1.0)
        assert glyphidx == 0

    def test_with_compiled_code_tt_Resolution_uniform(self):
        shader_code = dedent(
            """
        def frag(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            s: float = 0.1
            c: vec4 = vec4(tt_Resolution.x * s, tt_Resolution.y * s, 0.0, 1.0)
            return (c, c, 0)
        """
        )
        bytecode, reg_settings = all_passes_compilation(
            shader_code, "frag", {GLOBAL_VAR_TT_RESOLUTION: glm.vec2}
        )
        reg_settings.set_variable(GLOBAL_VAR_TT_RESOLUTION, glm.vec2(10.0, 20.0))
        regs = reg_settings.get_register_list()
        front, back, glyphidx = shade(regs, reg_settings.ssa_json())
        assert front == glm.vec4(1.0, 2.0, 0.0, 1.0)
        assert back == glm.vec4(1.0, 2.0, 0.0, 1.0)
        assert glyphidx == 0

    def test_with_compiled_code_tt_Frame_uniform(self):
        shader_code = dedent(
            """
        def frag(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), tt_Frame)
        """
        )
        bytecode, reg_settings = all_passes_compilation(
            shader_code, "frag", {GLOBAL_VAR_TT_FRAME: int}
        )
        reg_settings.set_variable(GLOBAL_VAR_TT_FRAME, 17)
        regs = reg_settings.get_register_list()
        front, back, glyphidx = shade(regs, reg_settings.ssa_json())
        assert front == glm.vec4(0.0, 0.0, 0.0, 1.0)
        assert back == glm.vec4(0.0, 0.0, 0.0, 1.0)
        assert glyphidx == 17

    def test_with_compiled_code_tt_PrimitiveID_in_glyph(self):
        """``tt_PrimitiveID`` is an always-present i32 pixel input; setting its register seed
        feeds the VM the same value ``ShaderMaterial`` would write per pixel from
        ``PixInfo::primitive_id``. Returning it as the glyph proves end-to-end plumbing."""
        shader_code = dedent(
            """
        def frag(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), tt_PrimitiveID)
        """
        )
        bytecode, reg_settings = all_passes_compilation(shader_code, "frag", {})
        reg_settings.set_variable(PIXELVAR_TT_PRIMITIVE_ID, 11)
        regs = reg_settings.get_register_list()
        front, back, glyphidx = shade(regs, reg_settings.ssa_json())
        assert front == glm.vec4(0.0, 0.0, 0.0, 1.0)
        assert back == glm.vec4(0.0, 0.0, 0.0, 1.0)
        assert glyphidx == 11

        reg_settings.set_variable(PIXELVAR_TT_PRIMITIVE_ID, 200)
        regs = reg_settings.get_register_list()
        _, _, glyphidx2 = shade(regs, reg_settings.ssa_json())
        assert glyphidx2 == 200

    def test_tt_FrontFacing_bool_register_colors_output(self):
        shader_code = dedent(
            """
        def facing_color(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            if tt_FrontFacing:
                c: vec4 = vec4(1.0, 0.0, 0.0, 1.0)
                return (c, c, 0)
            else:
                c2: vec4 = vec4(0.0, 1.0, 0.0, 1.0)
                return (c2, c2, 0)
        """
        )
        _, reg_settings = all_passes_compilation(shader_code, "facing_color", {})
        reg_settings.set_variable(PIXELVAR_TT_FRONT_FACING, True)
        front, _back, _g = shade(reg_settings)
        assert front.x > 0.99 and front.y < 0.01
        reg_settings.set_variable(PIXELVAR_TT_FRONT_FACING, False)
        front, _back, _g = shade(reg_settings)
        assert front.x < 0.01 and front.y > 0.99
