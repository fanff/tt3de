# -*- coding: utf-8 -*-
from textwrap import dedent
import json
import unittest

from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_TIME,
    PIXELVAR_TT_TEXCOORD0,
    PassSSARenamer,
    RegisterAllocatorPass,
    all_passes_compilation_with_state,
    compile_ttsl,
)
from tt3de.ttsl.ssa_dump import dump_ssa_module, snapshot_ssa_cfg
from tt3de.ttsl.ttsl_assembly import build_cfg_from_ir


class TestSsaDump(unittest.TestCase):
    def test_snapshot_after_ssa_has_blocks_and_consts(self):
        src = dedent(
            """
            def shade(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
                x: float = tt_TexCoord0.x + 0.25
                c: vec4 = vec4(x, 0.0, 1.0, 1.0)
                return (c, c, 0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        build_cfg_from_ir(cc)
        PassSSARenamer(cc).run()
        module = snapshot_ssa_cfg(cc)

        self.assertEqual(module["version"], 1)
        self.assertIsInstance(module["entry"], int)
        self.assertTrue(module["blocks"])
        self.assertTrue(any(c["ty"] == "F32" for c in module["consts"]))
        names = {inp["name"] for inp in module["inputs"]}
        self.assertIn(PIXELVAR_TT_TEXCOORD0, names)
        self.assertTrue(all(inp["reg"] is None for inp in module["inputs"]))

        ops = [instr["op"] for block in module["blocks"] for instr in block["instrs"]]
        self.assertIn("load_const", ops)
        self.assertIn("add", ops)
        self.assertIn("ret", ops)
        for block in module["blocks"]:
            self.assertTrue(block["instrs"], msg=block["name"])
            self.assertIn(block["instrs"][-1]["op"], {"jmp", "jmp_if_false", "ret"})
        json.dumps(module)

    def test_full_pipeline_fills_input_registers(self):
        src = dedent(
            """
            def shade() -> tuple[vec4, vec4, int]:
                t: float = tt_Time * 2.0
                c: vec4 = vec4(t, 0.0, 0.0, 1.0)
                return (c, c, 0)
            """
        )
        result = all_passes_compilation_with_state(
            src, "shade", {GLOBAL_VAR_TT_TIME: float}
        )
        self.assertTrue(result.ok, result.traceback_text)
        module = result.ssa_module
        self.assertIsNotNone(module)
        time_in = next(i for i in module["inputs"] if i["name"] == GLOBAL_VAR_TT_TIME)
        self.assertIsInstance(time_in["reg"], int)
        self.assertEqual(time_in["ty"], "F32")
        self.assertIsNotNone(result.register_settings)
        self.assertEqual(result.register_settings.ssa_module, module)

    def test_branch_records_jmp_if_false_and_phis(self):
        src = dedent(
            """
            def shade(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
                g: int = 0
                if tt_TexCoord0.x > 0.5:
                    g = 1
                c: vec4 = vec4(1.0, 0.0, 0.0, 1.0)
                return (c, c, g)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        build_cfg_from_ir(cc)
        PassSSARenamer(cc).run()
        rar = RegisterAllocatorPass(cc).run()
        module = dump_ssa_module(cc, rar)

        ops = [instr["op"] for block in module["blocks"] for instr in block["instrs"]]
        self.assertIn("jmp_if_false", ops)
        self.assertIn("cmp_gt", ops)
        has_phi = any(block["phis"] for block in module["blocks"])
        self.assertTrue(has_phi)
        jmp = next(
            instr
            for block in module["blocks"]
            for instr in block["instrs"]
            if instr["op"] == "jmp_if_false"
        )
        self.assertIn("target", jmp)
        self.assertIn("fallthrough", jmp)
        self.assertNotEqual(jmp["target"], jmp["fallthrough"])
