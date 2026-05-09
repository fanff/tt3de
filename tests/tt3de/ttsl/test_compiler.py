# -*- coding: utf-8 -*-
import ast
from textwrap import dedent
from unittest.mock import patch

from tt3de.ttsl.compiler import (
    CompileError,
    TTSLCompilerContext,
    all_passes_compilation_with_state,
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
        source = dedent(
            """
            def my_shader(tt_FragCoord: vec2) -> vec3:
                uv: vec2 = tt_TexCoord0
                pulse: float = abs(sin(tt_Time))
                return vec3(uv.x, uv.y, pulse)
            """
        )
        result = all_passes_compilation_with_state(
            source, "my_shader", {"time": float}
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
        source = dedent(
            """
            def my_shader(tt_FragCoord: vec2) -> vec3:
                uv: vec2 = tt_TexCoord0
                pulse: float = abs(sin(tt_Time))
                return vec3(uv.x, uv.y, pulse)
            """
        )

        with patch(
            "tt3de.ttsl.compiler.PassToByteCode.run",
            side_effect=RuntimeError("forced bytecode failure"),
        ):
            result = all_passes_compilation_with_state(
                source, "my_shader", {"time": float}
            )

        self.assertFalse(result.ok)
        self.assertEqual(result.last_completed_stage, "normalize_terms")
        self.assertIsNotNone(result.ast_module)
        self.assertIsNotNone(result.context)
        self.assertIsNotNone(result.register_allocation)
        self.assertIsNone(result.final_byte_code)
        self.assertIsNone(result.byte_array)
        self.assertIn("forced bytecode failure", result.traceback_text)
