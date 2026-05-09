# -*- coding: utf-8 -*-
"""End-to-end TTSL compilation: parse → IR → CFG → SSA → bytecode."""

from textwrap import dedent
import unittest

from pyglm import glm

from tt3de.tt3de import (
    DrawingBufferPy,
    MaterialBufferPy,
    PrimitiveBufferPy,
    TextureBufferPy,
    VertexBufferPy,
    apply_material_py,
    apply_material_py_parallel,
    find_glyph_indices_py,
    materials, # pyright: ignore
    ttsl_run,
)
from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_TIME,
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_FRAG_DEPTH,
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
            def my_shader(tt_FragCoord: glm.vec2) -> tuple[glm.vec3, glm.vec3, int]:
                uv: glm.vec2 = tt_TexCoord0
                pulse: float = abs(glm.sin(tt_Time * 1.25))
                if uv.x > uv.y:
                    return (
                        glm.vec3(uv.x, uv.y, pulse),
                        glm.vec3(uv.x, uv.y, pulse),
                        0,
                    )
                else:
                    return (
                        glm.vec3(0.0, pulse, 1.0 - pulse),
                        glm.vec3(0.0, pulse, 1.0 - pulse),
                        0,
                    )
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
            def my_shader(tt_TexCoord0: vec2) -> tuple[vec3, vec3, int]:
                # Make motion clearly visible at terminal framerate.
                phase: float = tt_Time * 4.0
                wave_x: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.x * 18.0) + phase)
                wave_y: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.y * 14.0) - phase * 1.2)
                blue: float = 0.5 + 0.5 * glm.sin(
                    phase * 0.7 + (tt_TexCoord0.x + tt_TexCoord0.y) * 8.0
                )
                rgb: vec3 = vec3(wave_x, wave_y, blue)
                return (rgb, rgb, 0)
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

    def test_ttsl_square_demo_shader_time_changes_pixels_material_apply(self):
        """
        Same shader as ``demos/2d/ttsl_square.py``: compiled bytecode plus constant seed
        registers, ``MaterialBufferPy.set_shader_time``, then sequential and parallel
        ``apply_material_*`` must reflect changing ``tt_Time`` in the raster output.
        """
        src = dedent(
            """
            def my_shader(tt_TexCoord0: vec2) -> tuple[vec3, vec3, int]:
                phase: float = tt_Time * 4.0
                wave_x: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.x * 18.0) + phase)
                wave_y: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.y * 14.0) - phase * 1.2)
                blue: float = 0.5 + 0.5 * glm.sin(
                    phase * 0.7 + (tt_TexCoord0.x + tt_TexCoord0.y) * 8.0
                )
                rgb: vec3 = vec3(wave_x, wave_y, blue)
                return (rgb, rgb, 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(
            src, "my_shader", {GLOBAL_VAR_TT_TIME: float}
        )
        _, time_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_TIME]

        mb = MaterialBufferPy()
        mat_idx = mb.add_shader(
            materials.ShaderPy(
                bytecode,
                time_f32_reg=time_reg,
                default_glyph=None,
                register_seed=reg_settings.get_register_list(),
            )
        )

        def sample_rgb_after_apply(time_seconds: float, apply_fn) -> tuple[int, int, int]:
            mb.set_shader_time(mat_idx, time_seconds)
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
            apply_fn(
                mb,
                TextureBufferPy(4),
                VertexBufferPy(16, 16, 16),
                PrimitiveBufferPy(8),
                draw,
            )
            cell = draw.get_canvas_cell(0, 0)
            return (cell["f_r"], cell["f_g"], cell["f_b"])

        self.assertNotEqual(
            sample_rgb_after_apply(0.0, apply_material_py),
            sample_rgb_after_apply(3.0, apply_material_py),
            "shader output should depend on tt_Time (sequential apply_material path)",
        )
        self.assertNotEqual(
            sample_rgb_after_apply(0.0, apply_material_py_parallel),
            sample_rgb_after_apply(2.0, apply_material_py_parallel),
            "shader output should depend on tt_Time (parallel apply_material path)",
        )

    def test_tt_texture_shader_samples_bound_texture(self):
        """Bytecode ``tt_texture`` must read the live ``TextureBuffer`` during apply_material."""
        src = dedent(
            """
            def shade(tt_TexCoord0: vec2) -> tuple[vec3, vec3, int]:
                sample: vec4 = tt_texture(0, tt_TexCoord0)
                rgb: vec3 = vec3(sample.x, sample.y, sample.z)
                return (rgb, rgb, 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})

        tb = TextureBufferPy(8)
        tb.add_texture(1, 1, [(255, 40, 80, 255)], True, True)

        mb = MaterialBufferPy()
        mb.add_static((0, 0, 0), (0, 0, 0), find_glyph_indices_py(" "))
        mat_idx = mb.add_shader(
            materials.ShaderPy(
                bytecode,
                default_glyph=None,
                register_seed=reg_settings.get_register_list(),
            )
        )

        def sample_rgb(apply_fn) -> tuple[int, int, int]:
            draw = DrawingBufferPy(4, 4)
            draw.hard_clear(10.0)
            draw.set_depth_content(
                0,
                0,
                glm.vec3(0.0, 0.0, 1.0),
                1.0,
                glm.vec2(0.5, 0.5),
                glm.vec2(0.0, 0.0),
                0,
                0,
                mat_idx,
                0,
            )
            apply_fn(
                mb,
                tb,
                VertexBufferPy(16, 16, 16),
                PrimitiveBufferPy(8),
                draw,
            )
            cell = draw.get_canvas_cell(0, 0)
            return (cell["f_r"], cell["f_g"], cell["f_b"])

        for apply_fn in (apply_material_py, apply_material_py_parallel):
            r, g, b = sample_rgb(apply_fn)
            self.assertGreater(r, 240, msg=f"expected red channel from texture ({apply_fn})")
            self.assertLess(g, 80, msg=f"expected low green ({apply_fn})")
            self.assertGreater(b, 40, msg=f"expected blue channel from texture ({apply_fn})")
            self.assertLess(b, 120, msg=f"expected bounded blue ({apply_fn})")


    def test_duplicate_float_constant_seeded_in_all_allocated_registers(self):
        """Regression: when the front-end emits two ``LOAD_CONST`` for the same
        constant pool index, register allocation gives each ``LOAD_CONST``'s ``dst``
        Temp its own physical register, but seeding must populate **every** such
        register — not only the last one keyed by ``const_id``. Two reads of the
        literal ``7.0`` in independent sub-expressions must both be ``7.0`` at
        runtime."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                a: float = 7.0 + tt_FragDepth
                b: float = 7.0 - tt_FragDepth
                out: float = a + b
                return (vec3(out, 0.0, 0.0), vec3(0.0, 0.0, 0.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        reg_settings.set_variable(PIXELVAR_TT_FRAG_DEPTH, 0.5)
        reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(0.0, 0.0))
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.0, 0.0))
        reg_settings.set_variable(PIXELVAR_TT_TEXCOORD1, glm.vec2(0.0, 0.0))
        regs = reg_settings.get_register_list()

        front, _back, _glyph = ttsl_run(*regs, bytecode)
        self.assertAlmostEqual(
            front.x, 14.0, places=4,
            msg=(
                f"both occurrences of literal 7.0 must seed their allocated "
                f"f32 registers (got {front.x}; if ~7.0 only one literal was seeded)"
            ),
        )

    def test_depth_floor_shader_vm_vs_python_reference(self):
        """Compile depth_floor shader, run via ttsl_run with several tt_FragDepth
        values, and compare against a pure-Python reference to catch compiler/VM
        divergence."""
        src = dedent(
            """
            def depth_floor(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                ndc: float = tt_FragDepth
                denom: float = 100.0 - ndc * 99.9
                d: float = 10.0 / denom
                t: float = 30.0 / (d + 30.0)
                rgb: vec3 = vec3(0.42 * t, 0.36 * t, 0.30 * t)
                return (rgb, vec3(0.0, 0.0, 0.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "depth_floor", {})

        def python_reference(ndc: float) -> glm.vec3:
            denom = 100.0 - ndc * 99.9
            d = 10.0 / denom
            t = 30.0 / (d + 30.0)
            return glm.vec3(0.42 * t, 0.36 * t, 0.30 * t)

        test_depths = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
        for ndc in test_depths:
            reg_settings.set_variable(PIXELVAR_TT_FRAG_DEPTH, ndc)
            reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(5.0, 5.0))
            reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.0, 0.0))
            reg_settings.set_variable(PIXELVAR_TT_TEXCOORD1, glm.vec2(0.0, 0.0))
            regs = reg_settings.get_register_list()

            front, back, glyph = ttsl_run(*regs, bytecode)
            expected = python_reference(ndc)

            self.assertAlmostEqual(
                front.x, expected.x, places=4,
                msg=f"front.x mismatch at ndc={ndc}: VM={front.x}, python={expected.x}",
            )
            self.assertAlmostEqual(
                front.y, expected.y, places=4,
                msg=f"front.y mismatch at ndc={ndc}: VM={front.y}, python={expected.y}",
            )
            self.assertAlmostEqual(
                front.z, expected.z, places=4,
                msg=f"front.z mismatch at ndc={ndc}: VM={front.z}, python={expected.z}",
            )
            self.assertEqual(
                back, glm.vec3(0.0, 0.0, 0.0),
                msg=f"back should be black at ndc={ndc}",
            )
            self.assertEqual(glyph, 0, msg=f"glyph should be 0 at ndc={ndc}")


if __name__ == "__main__":
    unittest.main()
