# -*- coding: utf-8 -*-
import ast
from textwrap import dedent
from unittest.mock import patch

from pyglm import glm

from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_FAR,
    GLOBAL_VAR_TT_NEAR,
    CompileError,
    PIXELVAR_TT_FRAG_DEPTH,
    TTSLCompilerContext,
    all_passes_compilation,
    all_passes_compilation_with_state,
    compile_ttsl,
    shader_py_frag_depth_clip_kwargs,
)
import unittest


class Test_Compiler(unittest.TestCase):
    def test_type_mismatch_in_ann_assign(self):
        cc = TTSLCompilerContext({})

        source = dedent("""x: vec3 = vec2(1.0, 2.0)""")

        tree = ast.parse(source)
        try:
            cc.compile_block(tree.body)
        except CompileError as e:
            assert True
        else:
            assert False

    def test_assign(self):
        cc = TTSLCompilerContext({})

        source = dedent("""x = vec2(1.0, 2.0)""")

        tree = ast.parse(source)
        cc.compile_block(tree.body)

    def test_assign_again(self):
        cc = TTSLCompilerContext({})

        source = dedent(
            """
                        x = vec2(1.0, 2.0)
                        x = vec2(2.0, 3.0)
                        """
        )

        tree = ast.parse(source)
        cc.compile_block(tree.body)

    def test_assign_differenttype(self):
        cc = TTSLCompilerContext({})

        source = dedent(
            """
                        x = vec2(1.0, 2.0)
                        x = vec3(2.0, 3.0, 4.0)
                        """
        )

        tree = ast.parse(source)
        try:
            cc.compile_block(tree.body)
        except CompileError as e:
            assert True
        else:
            assert False

    def test_all_passes_compilation_with_state_success(self):
        """This test checks the happy path:
        compiling a valid shader should complete every stage and return bytecode plus
        intermediate artifacts (AST, compiler context, and register allocation)."""
        source = dedent(
            """
            def my_shader(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                uv: vec2 = tt_TexCoord0
                pulse: float = abs(sin(tt_Time))
                c: vec3 = vec3(uv.x, uv.y, pulse)
                return (c, c, 0)
            """
        )
        result = all_passes_compilation_with_state(
            source, "my_shader", {"tt_Time": float}
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.last_completed_stage, "bytecode")
        self.assertIsNotNone(result.ast_module)
        self.assertIsNotNone(result.context)
        self.assertIsNotNone(result.register_allocation)
        self.assertIsNotNone(result.final_byte_code)
        self.assertIsNotNone(result.byte_array)
        self.assertGreater(len(result.byte_array), 0)

    def test_all_passes_compilation_with_state_keeps_partial_state_on_late_failure(self):
        """This test checks failure reporting late in the pipeline:
        if bytecode generation crashes, earlier successful stages should still be
        preserved in the result so callers can inspect partial compilation state."""
        source = dedent(
            """
            def my_shader(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                uv: vec2 = tt_TexCoord0
                pulse: float = abs(sin(tt_Time))
                c: vec3 = vec3(uv.x, uv.y, pulse)
                return (c, c, 0)
            """
        )

        with patch(
            "tt3de.ttsl.compiler.PassToByteCode.run",
            side_effect=RuntimeError("forced bytecode failure"),
        ):
            result = all_passes_compilation_with_state(
                source, "my_shader", {"tt_Time": float}
            )

        self.assertFalse(result.ok)
        self.assertEqual(result.last_completed_stage, "normalize_terms")
        self.assertIsNotNone(result.ast_module)
        self.assertIsNotNone(result.context)
        self.assertIsNotNone(result.register_allocation)
        self.assertIsNone(result.final_byte_code)
        self.assertIsNone(result.byte_array)
        self.assertIn("forced bytecode failure", result.traceback_text)


class Test_ReturnTripleContract(unittest.TestCase):
    def test_single_vec3_return_rejected(self):
        src = dedent(
            """
            def f(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                return vec3(1.0, 0.0, 0.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "f", {})
        self.assertIn("3-tuple", str(ctx.exception))

    def test_return_tuple_wrong_length(self):
        src = dedent(
            """
            def f(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                return (vec3(1.0, 0.0, 0.0), vec3(0.0, 1.0, 0.0))
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "f", {})
        self.assertIn("exactly 3", str(ctx.exception))

    def test_return_third_slot_must_be_int(self):
        src = dedent(
            """
            def f(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                return (vec3(1.0, 0.0, 0.0), vec3(0.0, 1.0, 0.0), 1.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "f", {})
        msg = str(ctx.exception)
        self.assertIn("vec3", msg)
        self.assertIn("int", msg)

    def test_vec3_return_annotation_rejected(self):
        src = dedent(
            """
            def f(tt_FragCoord: vec2) -> vec3:
                v: vec3 = vec3(1.0, 0.0, 0.0)
                return (v, v, 0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "f", {})
        self.assertIn("tuple[vec3, vec3, int]", str(ctx.exception))


class Test_tt_texture_frontend(unittest.TestCase):
    def test_tt_texture_compiles_full_pipeline(self):
        src = dedent(
            """
            def shade(tt_TexCoord0: vec2) -> tuple[vec3, vec3, int]:
                sample: vec4 = tt_texture(0, tt_TexCoord0)
                rgb: vec3 = vec3(sample.x, sample.y, sample.z)
                return (rgb, rgb, 0)
            """
        )
        bytecode, _ = all_passes_compilation(src, "shade", {})
        self.assertIsInstance(bytecode, bytes)
        self.assertGreater(len(bytecode), 0)


class Test_RegisterSettings_fork_and_depth_kwargs(unittest.TestCase):
    def test_fork_is_independent_for_user_uniform(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                return (u_tint, vec3(0.0, 0.0, 0.0), 0)
            """
        )
        _, template = all_passes_compilation(src, "shade", {"u_tint": glm.vec3})

        a = template.fork()
        b = template.fork()
        a.set_variable("u_tint", glm.vec3(1.0, 0.0, 0.0))
        b.set_variable("u_tint", glm.vec3(0.0, 0.0, 1.0))

        ty, rid = template.var_name_to_registers["u_tint"]
        self.assertAlmostEqual(a.regs[ty][rid].x, 1.0)
        self.assertAlmostEqual(b.regs[ty][rid].z, 1.0)
        self.assertAlmostEqual(b.regs[ty][rid].x, 0.0)

    def test_shader_py_frag_depth_clip_kwargs_matches_manual_registers(self):
        src = dedent(
            """
            def depth_tone(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                z_n: float = 2.0 * tt_FragDepth - 1.0
                d: float = (2.0 * tt_Near * tt_Far) / (tt_Far + tt_Near - z_n * (tt_Far - tt_Near))
                return (vec3(d, d, d), vec3(0.0, 0.0, 0.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(
            src,
            "depth_tone",
            {GLOBAL_VAR_TT_NEAR: float, GLOBAL_VAR_TT_FAR: float},
        )
        kw = shader_py_frag_depth_clip_kwargs(reg_settings)
        fd = reg_settings.var_name_to_registers[PIXELVAR_TT_FRAG_DEPTH][1]
        near_r = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_NEAR][1]
        far_r = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_FAR][1]
        self.assertEqual(
            kw,
            {
                "frag_depth_f32_reg": fd,
                "near_f32_reg": near_r,
                "far_f32_reg": far_r,
            },
        )

    def test_shader_py_frag_depth_clip_kwargs_raises_without_clip_globals(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
                return (vec3(tt_FragDepth, 0.0, 0.0), vec3(0.0, 0.0, 0.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        with self.assertRaises(ValueError) as ctx:
            shader_py_frag_depth_clip_kwargs(reg_settings)
        self.assertIn(GLOBAL_VAR_TT_NEAR, str(ctx.exception))
        self.assertIn(GLOBAL_VAR_TT_FAR, str(ctx.exception))
