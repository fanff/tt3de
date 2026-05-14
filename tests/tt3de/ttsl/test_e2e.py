# -*- coding: utf-8 -*-
"""End-to-end TTSL compilation: parse → IR → CFG → SSA → bytecode."""

from textwrap import dedent
import math
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
    GLOBAL_VAR_TT_FAR,
    GLOBAL_VAR_TT_NEAR,
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
            def my_shader(tt_FragCoord: glm.vec2) -> tuple[glm.vec4, glm.vec4, int]:
                uv: glm.vec2 = tt_TexCoord0
                pulse: float = abs(glm.sin(tt_Time * 1.25))
                if uv.x > uv.y:
                    return (
                        glm.vec4(uv.x, uv.y, pulse, 1.0),
                        glm.vec4(uv.x, uv.y, pulse, 1.0),
                        0,
                    )
                else:
                    return (
                        glm.vec4(0.0, pulse, 1.0 - pulse, 1.0),
                        glm.vec4(0.0, pulse, 1.0 - pulse, 1.0),
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
            def my_shader(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
                # Make motion clearly visible at terminal framerate.
                phase: float = tt_Time * 4.0
                wave_x: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.x * 18.0) + phase)
                wave_y: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.y * 14.0) - phase * 1.2)
                blue: float = 0.5 + 0.5 * glm.sin(
                    phase * 0.7 + (tt_TexCoord0.x + tt_TexCoord0.y) * 8.0
                )
                rgb: vec4 = vec4(wave_x, wave_y, blue, 1.0)
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
            def my_shader(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
                phase: float = tt_Time * 4.0
                wave_x: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.x * 18.0) + phase)
                wave_y: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.y * 14.0) - phase * 1.2)
                blue: float = 0.5 + 0.5 * glm.sin(
                    phase * 0.7 + (tt_TexCoord0.x + tt_TexCoord0.y) * 8.0
                )
                rgb: vec4 = vec4(wave_x, wave_y, blue, 1.0)
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
            def shade(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
                sample: vec4 = tt_texture(0, tt_TexCoord0)
                rgb: vec4 = vec4(sample.x, sample.y, sample.z, 1.0)
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
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                a: float = 7.0 + tt_FragDepth
                b: float = 7.0 - tt_FragDepth
                out: float = a + b
                return (vec4(out, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
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
            def depth_floor(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                ndc: float = tt_FragDepth
                denom: float = 100.0 - ndc * 99.9
                d: float = 10.0 / denom
                t: float = 30.0 / (d + 30.0)
                rgb: vec4 = vec4(0.42 * t, 0.36 * t, 0.30 * t, 1.0)
                return (rgb, vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "depth_floor", {})

        def python_reference(ndc: float) -> glm.vec4:
            denom = 100.0 - ndc * 99.9
            d = 10.0 / denom
            t = 30.0 / (d + 30.0)
            return glm.vec4(0.42 * t, 0.36 * t, 0.30 * t, 1.0)

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
                back, glm.vec4(0.0, 0.0, 0.0, 1.0),
                msg=f"back should be black at ndc={ndc}",
            )
            self.assertEqual(glyph, 0, msg=f"glyph should be 0 at ndc={ndc}")

    def test_depth_fog_glyph_shader_vm_vs_python_reference(self):
        """Mirror ``depth_fog_glyph`` (demos fog + quantized glyph bands): VM vs Python.

        Regression: cascading ``if cond: return ...`` (no ``else``) used to flow
        through every conditional and run the final return because
        ``build_layout_with_fallthrough`` did not pin the ``JMP_IF_FALSE`` true
        branch as the next block in bytecode. The fix records ``JMP_IF_FALSE``
        fall-through as required next-in-layout.
        """
        src = dedent(
            """
            def depth_fog_glyph(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                z_n: float = 2.0 * tt_FragDepth - 1.0
                d: float = (2.0 * tt_Near * tt_Far) / (tt_Far + tt_Near - z_n * (tt_Far - tt_Near))
                t: float = 1.0 - d / (d + 10.0)
                band: float = floor(t * 4.0)
                if band >= 4.0:
                    band = 3.0
                blk: vec4 = vec4(0.0, 0.0, 0.0, 1.0)
                if band >= 3.0:
                    return (blk, u_albedo, u_g3)
                if band >= 2.0:
                    return (blk, u_albedo, u_g2)
                if band >= 1.0:
                    return (blk, u_albedo, u_g1)
                return (blk, u_albedo, u_g0)
            """
        )
        globals_dict = {
            GLOBAL_VAR_TT_NEAR: float,
            GLOBAL_VAR_TT_FAR: float,
            "u_albedo": glm.vec4,
            "u_g0": int,
            "u_g1": int,
            "u_g2": int,
            "u_g3": int,
        }
        bytecode, reg_settings = all_passes_compilation(
            src, "depth_fog_glyph", globals_dict
        )

        def python_reference(
            frag_depth: float,
            near: float,
            far: float,
            albedo: glm.vec4,
            g0: int,
            g1: int,
            g2: int,
            g3: int,
        ) -> tuple[glm.vec4, glm.vec4, int]:
            z_n = 2.0 * frag_depth - 1.0
            d = (2.0 * near * far) / (far + near - z_n * (far - near))
            t = 1.0 - d / (d + 10.0)
            band = float(math.floor(t * 4.0))
            if band >= 4.0:
                band = 3.0
            blk = glm.vec4(0.0, 0.0, 0.0, 1.0)
            if band >= 3.0:
                return (blk, albedo, g3)
            if band >= 2.0:
                return (blk, albedo, g2)
            if band >= 1.0:
                return (blk, albedo, g1)
            return (blk, albedo, g0)

        near_f = 0.1
        far_f = 100.0
        albedo = glm.vec4(0.7, 0.55, 0.4, 1.0)
        g0, g1, g2, g3 = 10, 20, 30, 40

        reg_settings.set_variable(GLOBAL_VAR_TT_NEAR, near_f)
        reg_settings.set_variable(GLOBAL_VAR_TT_FAR, far_f)
        reg_settings.set_variable("u_albedo", albedo)
        reg_settings.set_variable("u_g0", g0)
        reg_settings.set_variable("u_g1", g1)
        reg_settings.set_variable("u_g2", g2)
        reg_settings.set_variable("u_g3", g3)

        test_depths = [0.0, 0.05, 0.2, 0.5, 0.75, 0.9, 1.0]
        for frag_depth in test_depths:
            reg_settings.set_variable(PIXELVAR_TT_FRAG_DEPTH, frag_depth)
            reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(2.0, 3.0))
            reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.0, 0.0))
            reg_settings.set_variable(PIXELVAR_TT_TEXCOORD1, glm.vec2(0.0, 0.0))
            regs = reg_settings.get_register_list()

            front, back, glyph = ttsl_run(*regs, bytecode)
            exp_front, exp_back, exp_g = python_reference(
                frag_depth, near_f, far_f, albedo, g0, g1, g2, g3
            )

            self.assertAlmostEqual(
                front.x, exp_front.x, places=4,
                msg=f"front.x @ tt_FragDepth={frag_depth}: VM={front.x}, ref={exp_front.x}",
            )
            self.assertAlmostEqual(
                front.y, exp_front.y, places=4,
                msg=f"front.y @ tt_FragDepth={frag_depth}: VM={front.y}, ref={exp_front.y}",
            )
            self.assertAlmostEqual(
                front.z, exp_front.z, places=4,
                msg=f"front.z @ tt_FragDepth={frag_depth}: VM={front.z}, ref={exp_front.z}",
            )
            self.assertAlmostEqual(
                back.x, exp_back.x, places=4,
                msg=f"back.x @ tt_FragDepth={frag_depth}: VM={back.x}, ref={exp_back.x}",
            )
            self.assertAlmostEqual(
                back.y, exp_back.y, places=4,
                msg=f"back.y @ tt_FragDepth={frag_depth}: VM={back.y}, ref={exp_back.y}",
            )
            self.assertAlmostEqual(
                back.z, exp_back.z, places=4,
                msg=f"back.z @ tt_FragDepth={frag_depth}: VM={back.z}, ref={exp_back.z}",
            )
            self.assertEqual(
                glyph, exp_g,
                msg=f"glyph @ tt_FragDepth={frag_depth}: VM={glyph}, ref={exp_g}",
            )

    def test_user_uniforms_vec3_vec2_ttsl_run(self):
        """User globals from globals_dict occupy VM registers; seed via RegisterSettings."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                c: vec4 = u_color + vec4(u_uv_bias.x, u_uv_bias.y, 0.0, 1.0)
                return (c, c, 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(
            src,
            "shade",
            {"u_color": glm.vec4, "u_uv_bias": glm.vec2},
        )
        reg_settings.set_variable("u_color", glm.vec4(0.1, 0.2, 0.3, 1.0))
        reg_settings.set_variable("u_uv_bias", glm.vec2(0.4, 0.5))

        front, back, glyph = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertEqual(glyph, 0)
        want = glm.vec4(0.5, 0.7, 0.3, 1.0)
        self.assertAlmostEqual(front.x, want.x, places=5)
        self.assertAlmostEqual(front.y, want.y, places=5)
        self.assertAlmostEqual(front.z, want.z, places=5)
        self.assertEqual(back, front)

    def test_user_uniform_material_apply_seed_matches_ttsl_run(self):
        """ShaderPy.register_seed must align bytecode user-uniform slots with the VM."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (u_color, u_color, 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(
            src, "shade", {"u_color": glm.vec4}
        )
        reg_settings.set_variable("u_color", glm.vec4(0.25, 0.5, 0.75, 1.0))
        seed = reg_settings.get_register_list()

        vm_front, _, vm_g = ttsl_run(*seed, bytecode)
        self.assertEqual(vm_g, 0)

        mb = MaterialBufferPy()
        mb.add_static((0, 0, 0), (0, 0, 0), find_glyph_indices_py(" "))
        mat_idx = mb.add_shader(
            materials.ShaderPy(
                bytecode,
                default_glyph=None,
                register_seed=seed,
            )
        )

        draw = DrawingBufferPy(4, 4)
        draw.hard_clear(10.0)
        draw.set_depth_content(
            0,
            0,
            glm.vec3(0.0, 0.0, 1.0),
            1.0,
            glm.vec2(0.0, 0.0),
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
        cell = draw.get_canvas_cell(0, 0)
        # Canvas stores 8-bit channels; allow quantization slack vs float VM output.
        self.assertAlmostEqual(cell["f_r"] / 255.0, vm_front.x, delta=2 / 255.0)
        self.assertAlmostEqual(cell["f_g"] / 255.0, vm_front.y, delta=2 / 255.0)
        self.assertAlmostEqual(cell["f_b"] / 255.0, vm_front.z, delta=2 / 255.0)


class Test_FloorCeilFractMod(unittest.TestCase):
    """End-to-end tests for floor, ceil, fract, and mod builtins."""

    def test_floor_f32_compiles_and_runs(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: float = floor(3.7)
                return (vec4(v, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        regs = reg_settings.get_register_list()
        front, _back, _glyph = ttsl_run(*regs, bytecode)
        self.assertAlmostEqual(front.x, 3.0, places=4)

    def test_floor_negative(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: float = floor(-1.3)
                return (vec4(v, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, -2.0, places=4)

    def test_ceil_f32(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: float = ceil(2.1)
                return (vec4(v, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 3.0, places=4)

    def test_fract_f32(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: float = fract(5.75)
                return (vec4(v, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 0.75, places=4)

    def test_mod_f32_basic(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: float = mod(7.5, 3.0)
                return (vec4(v, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 1.5, places=4)

    def test_mod_f32_negative_glsl_semantics(self):
        """GLSL mod(x,y) = x - y*floor(x/y), so mod(-1.0, 4.0) = 3.0."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: float = mod(-1.0, 4.0)
                return (vec4(v, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        expected = -1.0 - 4.0 * (-1.0 / 4.0).__floor__()
        self.assertAlmostEqual(front.x, expected, places=4)

    def test_floor_with_variable_input(self):
        """floor applied to a runtime uniform, not just a compile-time constant."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                scaled: float = tt_FragDepth * 4.0
                band: float = floor(scaled)
                return (vec4(band, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})

        for depth, expected_band in [(0.0, 0.0), (0.3, 1.0), (0.5, 2.0), (0.8, 3.0)]:
            reg_settings.set_variable(PIXELVAR_TT_FRAG_DEPTH, depth)
            regs = reg_settings.get_register_list()
            front, _, _ = ttsl_run(*regs, bytecode)
            self.assertAlmostEqual(
                front.x, expected_band, places=4,
                msg=f"floor(depth={depth} * 4.0) should be {expected_band}, got {front.x}",
            )

    def test_mod_with_variable_wrapping(self):
        """mod wraps a computed index back into [0, 4) — the fog-band use case."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                raw: float = tt_FragDepth * 4.0 + 2.0
                wrapped: float = mod(raw, 4.0)
                return (vec4(wrapped, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})

        for depth, expected in [(0.0, 2.0), (0.25, 3.0), (0.5, 0.0), (0.75, 1.0)]:
            reg_settings.set_variable(PIXELVAR_TT_FRAG_DEPTH, depth)
            front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
            self.assertAlmostEqual(
                front.x, expected, places=4,
                msg=f"mod(depth={depth}*4+2, 4) should be {expected}, got {front.x}",
            )

    def test_glm_floor_spelling(self):
        """glm.floor(...) must compile identically to bare floor(...)."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: float = glm.floor(3.7)
                return (vec4(v, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 3.0, places=4)

    def test_glm_mod_spelling(self):
        """glm.mod(x, y) must compile identically to bare mod(x, y)."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: float = glm.mod(7.5, 3.0)
                return (vec4(v, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 1.5, places=4)


class Test_Normalize(unittest.TestCase):
    """End-to-end tests for normalize builtin."""

    def test_normalize_v3_happy_path(self):
        """normalize(vec3) returns unit-length vector."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: vec3 = vec3(3.0, 0.0, 0.0)
                n: vec3 = normalize(v)
                return (vec4(n.x, n.y, n.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 1.0, places=5)
        self.assertAlmostEqual(front.y, 0.0, places=5)
        self.assertAlmostEqual(front.z, 0.0, places=5)

    def test_normalize_v3_non_unit(self):
        """normalize of a non-unit vector yields a unit vector."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: vec3 = vec3(2.0, 2.0, 1.0)
                n: vec3 = normalize(v)
                return (vec4(n.x, n.y, n.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        ref = glm.vec3(2.0, 2.0, 1.0)
        expected = glm.normalize(ref)
        self.assertAlmostEqual(front.x, expected.x, places=5)
        self.assertAlmostEqual(front.y, expected.y, places=5)
        self.assertAlmostEqual(front.z, expected.z, places=5)

    def test_normalize_v3_zero_vector(self):
        """normalize(zero) returns zero vector (guarded in Rust VM)."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: vec3 = vec3(0.0, 0.0, 0.0)
                n: vec3 = normalize(v)
                return (vec4(n.x, n.y, n.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 0.0, places=5)
        self.assertAlmostEqual(front.y, 0.0, places=5)
        self.assertAlmostEqual(front.z, 0.0, places=5)

    def test_normalize_v2(self):
        """normalize(vec2) works."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: vec2 = vec2(3.0, 4.0)
                n: vec2 = normalize(v)
                return (vec4(n.x, n.y, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        expected = glm.normalize(glm.vec2(3.0, 4.0))
        self.assertAlmostEqual(front.x, expected.x, places=5)
        self.assertAlmostEqual(front.y, expected.y, places=5)

    def test_normalize_v4(self):
        """normalize(vec4) works."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: vec4 = vec4(1.0, 2.0, 2.0, 0.0)
                n: vec4 = normalize(v)
                return (vec4(n.x, n.y, n.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        expected = glm.normalize(glm.vec4(1.0, 2.0, 2.0, 0.0))
        self.assertAlmostEqual(front.x, expected.x, places=5)
        self.assertAlmostEqual(front.y, expected.y, places=5)
        self.assertAlmostEqual(front.z, expected.z, places=5)

    def test_normalize_with_variable_input(self):
        """normalize works with runtime (non-constant) inputs."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                x: float = tt_FragCoord.x
                y: float = tt_FragCoord.y
                v: vec3 = vec3(x, y, 0.0)
                n: vec3 = normalize(v)
                return (vec4(n.x, n.y, n.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(3.0, 4.0))
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        expected = glm.normalize(glm.vec3(3.0, 4.0, 0.0))
        self.assertAlmostEqual(front.x, expected.x, places=5)
        self.assertAlmostEqual(front.y, expected.y, places=5)
        self.assertAlmostEqual(front.z, expected.z, places=5)

    def test_glm_normalize_spelling(self):
        """glm.normalize(v) must compile identically to bare normalize(v)."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                v: vec3 = vec3(4.0, 0.0, 0.0)
                n: vec3 = glm.normalize(v)
                return (vec4(n.x, n.y, n.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 1.0, places=5)


class Test_Dot(unittest.TestCase):
    """End-to-end tests for dot builtin."""

    def test_dot_v3_orthogonal(self):
        """dot(orthogonal vectors) = 0."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                a: vec3 = vec3(1.0, 0.0, 0.0)
                b: vec3 = vec3(0.0, 1.0, 0.0)
                d: float = dot(a, b)
                return (vec4(d, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 0.0, places=5)

    def test_dot_v3_parallel(self):
        """dot(parallel unit vectors) = 1."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                a: vec3 = vec3(1.0, 0.0, 0.0)
                b: vec3 = vec3(1.0, 0.0, 0.0)
                d: float = dot(a, b)
                return (vec4(d, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 1.0, places=5)

    def test_dot_v3_opposite(self):
        """dot(opposite unit vectors) = -1."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                a: vec3 = vec3(1.0, 0.0, 0.0)
                b: vec3 = vec3(-1.0, 0.0, 0.0)
                d: float = dot(a, b)
                return (vec4(d, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, -1.0, places=5)

    def test_dot_v2(self):
        """dot(vec2, vec2) works."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                a: vec2 = vec2(1.0, 2.0)
                b: vec2 = vec2(3.0, 4.0)
                d: float = dot(a, b)
                return (vec4(d, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        expected = glm.dot(glm.vec2(1.0, 2.0), glm.vec2(3.0, 4.0))
        self.assertAlmostEqual(front.x, expected, places=5)

    def test_dot_v4(self):
        """dot(vec4, vec4) works."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                a: vec4 = vec4(1.0, 2.0, 3.0, 4.0)
                b: vec4 = vec4(5.0, 6.0, 7.0, 8.0)
                d: float = dot(a, b)
                return (vec4(d, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        expected = glm.dot(glm.vec4(1.0, 2.0, 3.0, 4.0), glm.vec4(5.0, 6.0, 7.0, 8.0))
        self.assertAlmostEqual(front.x, expected, places=5)

    def test_dot_with_variable_input(self):
        """dot works with runtime (non-constant) vectors."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                x: float = tt_FragCoord.x
                y: float = tt_FragCoord.y
                v: vec3 = vec3(x, y, 0.0)
                d: float = dot(v, v)
                return (vec4(d, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(3.0, 4.0))
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 25.0, places=5)

    def test_glm_dot_spelling(self):
        """glm.dot(a, b) must compile identically to bare dot(a, b)."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                a: vec3 = vec3(2.0, 0.0, 0.0)
                b: vec3 = vec3(3.0, 0.0, 0.0)
                d: float = glm.dot(a, b)
                return (vec4(d, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        bytecode, reg_settings = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*reg_settings.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 6.0, places=5)


class Test_Length(unittest.TestCase):
    """End-to-end tests for length builtin."""

    def test_length_v3_unit(self):
        """length(unit vector) = 1."""
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            v: vec3 = vec3(1.0, 0.0, 0.0)
            l: float = length(v)
            return (vec4(l, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 1.0, places=5)

    def test_length_v3_zero(self):
        """length(zero) = 0."""
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            v: vec3 = vec3(0.0, 0.0, 0.0)
            l: float = length(v)
            return (vec4(l, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 0.0, places=5)

    def test_length_v2_v4(self):
        """length(vec2) and length(vec4)."""
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            v2: vec2 = vec2(3.0, 4.0)
            v4: vec4 = vec4(1.0, 2.0, 2.0, 0.0)
            l2: float = length(v2)
            l4: float = length(v4)
            return (vec4(l2, l4, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 5.0, places=5)
        self.assertAlmostEqual(front.y, 3.0, places=5)

    def test_glm_length_spelling(self):
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            l: float = glm.length(vec3(3.0, 4.0, 0.0))
            return (vec4(l, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 5.0, places=5)


class Test_Max(unittest.TestCase):
    """End-to-end tests for max builtin."""

    def test_max_f32(self):
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            m: float = max(3.0, 7.0)
            return (vec4(m, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 7.0, places=5)

    def test_max_f32_negative(self):
        """max with negative values."""
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            m: float = max(-2.0, -5.0)
            return (vec4(m, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, -2.0, places=5)

    def test_max_vec3(self):
        """max(vec3, vec3) component-wise."""
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            a: vec3 = vec3(1.0, 5.0, 3.0)
            b: vec3 = vec3(4.0, 2.0, 6.0)
            m: vec3 = max(a, b)
            return (vec4(m.x, m.y, m.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 4.0, places=5)
        self.assertAlmostEqual(front.y, 5.0, places=5)
        self.assertAlmostEqual(front.z, 6.0, places=5)

    def test_glm_max_spelling(self):
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            m: float = glm.max(1.0, 2.0)
            return (vec4(m, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 2.0, places=5)


class Test_Clamp(unittest.TestCase):
    """End-to-end tests for clamp builtin."""

    def test_clamp_f32_within_range(self):
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            c: float = clamp(0.5, 0.0, 1.0)
            return (vec4(c, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 0.5, places=5)

    def test_clamp_f32_below_lo(self):
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            c: float = clamp(-1.0, 0.0, 1.0)
            return (vec4(c, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 0.0, places=5)

    def test_clamp_f32_above_hi(self):
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            c: float = clamp(5.0, 0.0, 1.0)
            return (vec4(c, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 1.0, places=5)

    def test_clamp_vec3(self):
        """clamp(vec3, vec3, vec3) component-wise."""
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            x: vec3 = vec3(-0.5, 0.5, 1.5)
            lo: vec3 = vec3(0.0, 0.0, 0.0)
            hi: vec3 = vec3(1.0, 1.0, 1.0)
            c: vec3 = clamp(x, lo, hi)
            return (vec4(c.x, c.y, c.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 0.0, places=5)
        self.assertAlmostEqual(front.y, 0.5, places=5)
        self.assertAlmostEqual(front.z, 1.0, places=5)

    def test_glm_clamp_spelling(self):
        src = dedent("""
        def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
            c: float = glm.clamp(0.5, 0.0, 1.0)
            return (vec4(c, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
        """)
        bytecode, rs = all_passes_compilation(src, "shade", {})
        front, _, _ = ttsl_run(*rs.get_register_list(), bytecode)
        self.assertAlmostEqual(front.x, 0.5, places=5)


if __name__ == "__main__":
    unittest.main()
