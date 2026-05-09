# -*- coding: utf-8 -*-
import ast
from textwrap import dedent
from unittest.mock import patch

from tt3de.ttsl.compiler import (
    CompileError,
    TTSLCompilerContext,
    all_passes_compilation_with_state,
    compile_ttsl,
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
