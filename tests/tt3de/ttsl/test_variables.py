# -*- coding: utf-8 -*-
"""
TTSL variable binding tests (front-end only: `compile_ttsl`).

Always-present inputs match `TTSLCompilerContext.always_present_variables()` (pixel
inputs only). ``tt_Time`` and other engine uniforms are optional via ``globals_dict``;
see `source/ttsl_compiler.md`. The broader catalog in `source/ttsl.md` includes names
not yet present in the Python compiler; some tests use `@unittest.expectedFailure`
to track eventual parity without failing the suite today.

"""

from textwrap import dedent
import unittest

from pyglm import glm

from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_TIME,
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_TEXCOORD0,
    PIXELVAR_TT_TEXCOORD1,
    TTSLCompilerContext,
    CompileError,
    compile_ttsl,
)
from tt3de.ttsl.ttsl_assembly import IRType

# Always-present pixel/cell inputs (see `TTSLCompilerContext.always_present_variables()`).
ALWAYS_PRESENT_BUILTIN_NAMES = (
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_TEXCOORD0,
    PIXELVAR_TT_TEXCOORD1,
)


class Test_VariableContract(unittest.TestCase):
    """Anchors tests to `always_present_variables()` and exported name constants."""

    def test_implemented_builtins_match_always_present(self):
        ref = set(TTSLCompilerContext.always_present_variables().keys())
        self.assertEqual(ref, set(ALWAYS_PRESENT_BUILTIN_NAMES))

    def test_lowercase_time_and_tt_Time_not_registered_by_default(self):
        """No implicit ``time`` or ``tt_Time`` slot — only ``globals_dict`` adds those."""
        src = dedent(
            """
            def simple(tt_FragCoord: vec2) -> vec3:
                return vec3(1.0, 2.0, 3.0)
            """
        )
        cc = compile_ttsl(src, "simple", {})
        self.assertNotIn("time", cc.named_variables)
        self.assertNotIn(GLOBAL_VAR_TT_TIME, cc.named_variables)


class Test_BuiltinsHappyPath(unittest.TestCase):
    def test_pixel_builtins_plus_tt_Time_when_declared_in_globals(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                pulse: float = tt_Time
                u0: vec2 = tt_TexCoord0
                u1: vec2 = tt_TexCoord1
                return vec3(u0.x + u1.x + pulse * 0.0, u0.y, tt_FragCoord.x)
            """
        )
        globs = {GLOBAL_VAR_TT_TIME: float}
        cc = compile_ttsl(src, "shade", globs)
        for name in ALWAYS_PRESENT_BUILTIN_NAMES:
            self.assertIn(name, cc.named_variables)
        self.assertIn(GLOBAL_VAR_TT_TIME, cc.named_variables)
        self.assertEqual(cc.named_variables[GLOBAL_VAR_TT_TIME].ty, IRType.F32)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_FRAGCOORD].ty, IRType.V2)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_TEXCOORD0].ty, IRType.V2)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_TEXCOORD1].ty, IRType.V2)
        self.assertEqual(cc.globals, {GLOBAL_VAR_TT_TIME: IRType.F32})

    def test_tt_Time_requires_globals_dict(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                return vec3(tt_Time, 0.0, 0.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn(GLOBAL_VAR_TT_TIME, msg)
        self.assertIn("Unknown variable", msg)

    def test_empty_globals_dict_builtin_only(self):
        src = dedent(
            """
            def simple(tt_FragCoord: vec2) -> vec3:
                return vec3(1.0, 2.0, 3.0)
            """
        )
        cc = compile_ttsl(src, "simple", {})
        self.assertEqual(cc.globals, {})


class Test_UserGlobalsHappyPath(unittest.TestCase):
    def test_globals_dict_uniforms(self):
        globs = {"time": float, "position": glm.vec3}
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                t: float = time
                p: vec3 = position
                return vec3(t + tt_FragCoord.x * 0.0, p.y, p.z)
            """
        )
        cc = compile_ttsl(src, "shade", globs)
        self.assertEqual(cc.globals, {"time": IRType.F32, "position": IRType.V3})
        self.assertIn("time", cc.named_variables)
        self.assertIn("position", cc.named_variables)


class Test_ParameterVsBuiltinFragCoord(unittest.TestCase):
    def test_uv_parameter_distinct_from_tt_FragCoord_builtin(self):
        src = dedent(
            """
            def shade(uv: vec2) -> vec3:
                return vec3(uv.x + tt_FragCoord.x, uv.y + tt_FragCoord.y, 0.0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertIn("uv", cc.named_variables)
        self.assertIn(PIXELVAR_TT_FRAGCOORD, cc.named_variables)
        self.assertIsNot(
            cc.named_variables["uv"].id,
            cc.named_variables[PIXELVAR_TT_FRAGCOORD].id,
        )


class Test_ShadowBuiltinViaGlobalsDict(unittest.TestCase):
    def test_tt_Time_shadowed_by_int_global_still_compiles(self):
        """globals_dict chooses the IR type for ``tt_Time`` (here ``int`` vs default ``float``)."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                tick: int = tt_Time
                return vec3(1.0, 2.0, 3.0)
            """
        )
        cc = compile_ttsl(src, "shade", {GLOBAL_VAR_TT_TIME: int})
        self.assertEqual(cc.named_variables[GLOBAL_VAR_TT_TIME].ty, IRType.I32)

    def test_tt_Time_shadowed_as_int_breaks_float_vec3_mixing(self):
        """sin(tt_Time) is I32; vec3(...) requires f32 components — CompileError."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                return vec3(sin(tt_Time), 0.0, 0.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {GLOBAL_VAR_TT_TIME: int})
        msg = str(ctx.exception)
        # Root cause: globals_dict shadowed tt_Time as int, so sin(...) is I32 inside vec3(...)
        self.assertIn("vec3", msg)
        self.assertIn("f32", msg)
        self.assertIn("I32", msg)


class Test_VariableFailures(unittest.TestCase):
    def test_doc_catalog_tt_FragPos_not_implemented(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                p: vec2 = tt_FragPos
                return vec3(p.x, p.y, 0.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn("tt_FragPos", msg)
        self.assertIn("Unknown variable", msg)

    def test_doc_catalog_tt_DeltaTime_not_implemented(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                d: float = tt_DeltaTime
                return vec3(d, 0.0, 0.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn("tt_DeltaTime", msg)
        self.assertIn("Unknown variable", msg)

    def test_typo_tt_Tim(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                return vec3(tt_Tim, 0.0, 0.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn("tt_Tim", msg)
        self.assertIn("Unknown variable", msg)

    def test_typo_tt_fragcoord_case(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                return vec3(tt_fragcoord.x, 0.0, 0.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn("tt_fragcoord", msg)
        self.assertIn("Unknown variable", msg)

    def test_undeclared_user_global(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                return vec3(mystery_uniform, 0.0, 0.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn("mystery_uniform", msg)
        self.assertIn("Unknown variable", msg)

    def test_unsupported_global_type_in_globals_dict(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                return vec3(1.0, 2.0, 3.0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {"bad": str})
        msg = str(ctx.exception)
        self.assertIn("bad", msg)
        self.assertIn("Unsupported global variable type", msg)


class Test_DocParityExpectedFailures(unittest.TestCase):
    """When these builtins exist in the compiler, remove @unittest.expectedFailure."""

    @unittest.expectedFailure
    def test_doc_tt_FragPos_vec2_builtin_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                p: vec2 = tt_FragPos
                return vec3(p.x, p.y, 0.0)
            """
        )
        compile_ttsl(src, "shade", {})

    @unittest.expectedFailure
    def test_doc_tt_DeltaTime_float_builtin_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> vec3:
                d: float = tt_DeltaTime
                return vec3(d, 0.0, 0.0)
            """
        )
        compile_ttsl(src, "shade", {})


if __name__ == "__main__":
    unittest.main()
