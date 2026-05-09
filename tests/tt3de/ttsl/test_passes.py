# -*- coding: utf-8 -*-

from textwrap import dedent
import unittest
from pyglm import glm
from tt3de.ttsl.compiler import (
    PassSSARenamer,
    compile_ttsl,
    PassPhiNodeLowering,
    CFGSimplifyPass,
    RegisterAllocatorPass,
    PassNormalizeTerminators,
    PassToByteCode,
    all_passes_compilation,
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_TEXCOORD0,
    PIXELVAR_TT_TEXCOORD1,
)
from tt3de.ttsl.ttsl_assembly import build_cfg_from_ir


class Test_SSARenaming(unittest.TestCase):
    def test_simple_case(self):
        src = dedent(
            """

            def my_shader(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                # accessing variables coming from the fragment:
                return (vec3(1.0, -2.0, 0.0), vec3(1.0, -2.0, 0.0), 0)

            """
        )
        func_name = "my_shader"
        globals_dict = {}
        ttsl_cc = compile_ttsl(src, func_name, globals_dict)
        build_cfg_from_ir(ttsl_cc)
        PassSSARenamer(ttsl_cc).run()


class Test_SampleCompilation(unittest.TestCase):
    def test_sample_shader_compilation(self):
        src = dedent(
            """
                @ttsl(globals={})
                def my_shader(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:  # noqa: F811
                    # calculate a skybox background based on tt_FragCoord (from -1 to 1)
                    color_sky: vec3 = vec3(0.2, 0.4, 0.8)
                    color_horizon: vec3 = vec3(0.8, 0.9, 1.0)
                    t: float = (tt_FragCoord.y + 1.0) / 2.0
                    mixed: vec3 = color_sky * (1.0 - t) + color_horizon * t

                    return (mixed, mixed, 0)
            """
        )
        func_name = "my_shader"
        globals_dict = {}
        ttsl_cc = compile_ttsl(src, func_name, globals_dict)
        build_cfg_from_ir(ttsl_cc)
        PassSSARenamer(ttsl_cc).run()

        PassPhiNodeLowering(ttsl_cc).run()
        CFGSimplifyPass(ttsl_cc).run()
        rar = RegisterAllocatorPass(ttsl_cc).run()

        PassNormalizeTerminators(ttsl_cc).run()
        final_byte_code = PassToByteCode(ttsl_cc).run(rar)

    def test_onecall_compilateion(self):
        src = dedent(
            """
                @ttsl(globals={})
                def my_shader(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:  # noqa: F811
                    # calculate a skybox background based on tt_FragCoord (from -1 to 1)
                    color_sky: vec3 = vec3(0.2, 0.4, 0.8)
                    color_horizon: vec3 = vec3(0.8, 0.9, 1.0)
                    t: float = (tt_FragCoord.y + 1.0) / 2.0
                    mixed: vec3 = color_sky * (1.0 - t) + color_horizon * t

                    return (mixed, mixed, 0)
            """
        )
        func_name = "my_shader"
        globals_dict = {}
        _final_byte_code, reg_settings = all_passes_compilation(
            src, func_name, globals_dict
        )
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.5, 0.5))
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD1, glm.vec2(0.5, 0.5))
        reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(0.5, 0.5))
