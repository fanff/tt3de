# -*- coding: utf-8 -*-
from textwrap import dedent
import unittest

from tt3de.ttsl.compiler import PassSSARenamer, compile_ttsl
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
