# -*- coding: utf-8 -*-
"""End-to-end TTSL compilation: parse → IR → CFG → SSA → bytecode."""

from textwrap import dedent
import unittest

from pyglm import glm

from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_TIME,
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_TEXCOORD0,
    PIXELVAR_TT_TEXCOORD1,
    all_passes_compilation,
)


class Test_EndToEndCompilation(unittest.TestCase):
    def test_uv_pulse_branching_shader_compiles_to_bytecode(self):
        """
        Regression: if/else with returns on both branches uses builtins (tt_TexCoord0,
        tt_Time) and glm.* intrinsics. Previously failed in phi lowering when phis
        were attached to `_END_` without SSA-renamed destinations.
        """
        src = dedent(
            """
            def my_shader(tt_FragCoord: glm.vec2) -> glm.vec3:
                uv: glm.vec2 = tt_TexCoord0
                pulse: float = abs(glm.sin(tt_Time * 1.25))
                if uv.x > uv.y:
                    return glm.vec3(uv.x, uv.y, pulse)
                else:
                    return glm.vec3(0.0, pulse, 1.0 - pulse)
            """
        )
        bytecode, reg_settings = all_passes_compilation(
            src, "my_shader", {GLOBAL_VAR_TT_TIME: float}
        )
        self.assertIsInstance(bytecode, bytes)
        self.assertGreater(len(bytecode), 0)

        reg_settings.set_variable(GLOBAL_VAR_TT_TIME, 1.25)
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.8, 0.2))
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD1, glm.vec2(0.0, 0.0))
        reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(10.0, 20.0))

    def test_ttsl_square_demo_shader_compiles_to_bytecode(self):
        """
        Mirrors demos/2d/ttsl_square.py shader source.
        """
        src = dedent(
            """
            def my_shader(tt_TexCoord0: vec2) -> vec3:
                # Make motion clearly visible at terminal framerate.
                phase: float = tt_Time * 4.0
                wave_x: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.x * 18.0) + phase)
                wave_y: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.y * 14.0) - phase * 1.2)
                blue: float = 0.5 + 0.5 * glm.sin(
                    phase * 0.7 + (tt_TexCoord0.x + tt_TexCoord0.y) * 8.0
                )
                return vec3(wave_x, wave_y, blue)
            """
        )
        bytecode, reg_settings = all_passes_compilation(
            src, "my_shader", {GLOBAL_VAR_TT_TIME: float}
        )
        self.assertIsInstance(bytecode, bytes)
        self.assertGreater(len(bytecode), 0)

        reg_settings.set_variable(GLOBAL_VAR_TT_TIME, 0.5)
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.25, 0.75))
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD1, glm.vec2(0.0, 0.0))
        reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(12.0, 8.0))


if __name__ == "__main__":
    unittest.main()
