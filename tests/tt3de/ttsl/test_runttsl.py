# -*- coding: utf-8 -*-
from tt3de.ttsl.ttisa.ttisa_opcodes import OP_RET, OP_JMP
from tests.benchs.ttsl.test_bench_ttsl import SHADER_CODE
from tt3de.ttsl.enrich import PassPrintConsole
from textwrap import dedent
import unittest

from tt3de.ttsl.compiler import (
    PIXELVAR_TTSL_UV0,
    PassSSARenamer,
    compile_ttsl,
    PassPhiNodeLowering,
    CFGSimplifyPass,
    RegisterAllocatorPass,
    PassNormalizeTerminators,
    PassToByteCode,
    all_passes_compilation,
)
from tt3de.ttsl.ttsl_assembly import build_cfg_from_ir, IRType

from pyglm import glm

from tt3de.tt3de import ttsl_run


class Test_OPCodes(unittest.TestCase):
    def test_emptyshader(self):
        regs = [{}] * 6
        bytecode = b""
        run_result = ttsl_run(*regs, bytecode)

    def test_returnshader(self):
        regs = [{}] * 6

        regs[4] = {1: glm.vec3(0.5, 0.5, 0.0)}  # setting register 1 = something not 0

        bytecode = bytes(
            [OP_RET, 0, 1, 1, 0, 0] + [OP_RET, 0, 0, 0, 0, 0]
        )  # asking to immediately return register 1
        run_result = ttsl_run(*regs, bytecode)
        assert isinstance(run_result, tuple)
        assert len(run_result) == 3
        front, back, glyphidx = run_result
        assert front == glm.vec3(0.5, 0.5, 0.0)
        assert back == glm.vec3(0.5, 0.5, 0.0)
        assert glyphidx == 0

    def test_jump(self):
        regs = [{}] * 6

        regs[4] = {1: glm.vec3(0.5, 0.5, 0.0)}  # setting register 1 = something not 0

        bytecode = bytes(
            [
                OP_JMP,
                1,
                0,
                0,
                0,
                0,
            ]  # jump to the instruction 1, (which is the next one)
            + [
                OP_RET,
                0,
                1,
                1,
                0,
                0,
            ]  # return reg 1
        )
        run_result = ttsl_run(*regs, bytecode)
        assert isinstance(run_result, tuple)
        assert len(run_result) == 3
        front, back, glyphidx = run_result
        assert front == glm.vec3(0.5, 0.5, 0.0)
        assert back == glm.vec3(0.5, 0.5, 0.0)
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
        # prepare sample bytecode
        bytecode: bytes = b""
        regs.append(bytecode)
        run_result = ttsl_run(*regs)
        assert isinstance(run_result, tuple)
        assert len(run_result) == 3

        front, back, glyphidx = run_result
        assert isinstance(front, glm.vec3)
        assert isinstance(back, glm.vec3)
        assert isinstance(glyphidx, int)

        assert front == glm.vec3(0.0, 1.0, 2.0)
        assert back == glm.vec3(0.0, 1.0, 2.0)
        assert glyphidx == 2

    def test_with_compiled_code(self):

        shader_code = dedent(
            """
        def frag(pos: vec2) -> vec3:
            return vec3(ttsl_uv0.x, ttsl_uv0.y, 0.0)
        """
        )
        bytecode, reg_settings = all_passes_compilation(shader_code, "frag", {})
        # reg_settings.set_variable(GLOBAL_VAR_TTSL_TIME, 1221.1)
        reg_settings.set_variable(PIXELVAR_TTSL_UV0, glm.vec2(0.5, 0.5))
        # reg_settings.set_variable(PIXELVAR_TTSL_UV1, glm.vec2(0.5, 0.5))
        # reg_settings.set_variable(ON_SCREEN_POSITION_VAR_NAME, glm.vec2(0.5, 0.5))

        # from the rar, prepare the registers
        regs = reg_settings.get_register_list()

        run_result = ttsl_run(*regs, bytecode)
        assert isinstance(run_result, tuple)
        assert len(run_result) == 3
        front, back, glyphidx = run_result
        assert front == glm.vec3(0.5, 0.5, 0.0)
        assert back == glm.vec3(0.0, 0.0, 0.0)
        assert glyphidx == 0
