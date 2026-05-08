# -*- coding: utf-8 -*-
import ast
from textwrap import dedent
from tt3de.ttsl.compiler import TTSLCompilerContext, CompileError
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
