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
    GLOBAL_VAR_TTSL_TIME,
    PIXELVAR_TTSL_UV0,
    PIXELVAR_TTSL_UV1,
    ON_SCREEN_POSITION_VAR_NAME,
)
from tt3de.ttsl.ttsl_assembly import build_cfg_from_ir


class Test_SSARenaming(unittest.TestCase):
    def test_simple_case(self):
        src = dedent(
            """

            def my_shader(pos: vec2) -> vec3:
                # accessing variables coming from the fragment:
                return vec3(1.0, -2.0, 0.0)

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
                def my_shader(pos: vec2) -> vec3:  # noqa: F811
                    # calculate a skybox background based on pos (from -1 to 1)
                    color_sky: vec3 = vec3(0.2, 0.4, 0.8)
                    color_horizon: vec3 = vec3(0.8, 0.9, 1.0)
                    t: float = (pos.y + 1.0) / 2.0
                    mixed: vec3 = mix(color_sky, color_horizon, t)

                    return mixed
            """
        )
        func_name = "my_shader"
        globals_dict = {"time": float}
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
                def my_shader(pos: vec2) -> vec3:  # noqa: F811
                    # calculate a skybox background based on pos (from -1 to 1)
                    color_sky: vec3 = vec3(0.2, 0.4, 0.8)
                    color_horizon: vec3 = vec3(0.8, 0.9, 1.0)
                    t: float = (pos.y + 1.0) / 2.0
                    mixed: vec3 = mix(color_sky, color_horizon, t)

                    return mixed
            """
        )
        func_name = "my_shader"
        globals_dict = {"time": float}
        _final_byte_code, reg_settings = all_passes_compilation(
            src, func_name, globals_dict
        )
        reg_settings.set_variable(GLOBAL_VAR_TTSL_TIME, 1221.1)
        reg_settings.set_variable(PIXELVAR_TTSL_UV0, glm.vec2(0.5, 0.5))
        reg_settings.set_variable(PIXELVAR_TTSL_UV1, glm.vec2(0.5, 0.5))
        reg_settings.set_variable(ON_SCREEN_POSITION_VAR_NAME, glm.vec2(0.5, 0.5))
        reg_settings.set_variable("time", 1221.1)
