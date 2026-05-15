# -*- coding: utf-8 -*-
"""
TTSL variable binding tests (front-end only: `compile_ttsl`).

Always-present inputs match `TTSLCompilerContext.always_present_variables()` (pixel
inputs only). ``tt_Time``, ``tt_DeltaTime``, ``tt_Resolution``, ``tt_Near``, ``tt_Far``,
and other engine uniforms are optional via ``globals_dict``;
see `source/ttsl_compiler.md`. The broader catalog in `source/ttsl.md` includes names
not yet present in the Python compiler; some tests use `@unittest.expectedFailure`
only where noted for constructs still missing from the compiler surface.
"""

from textwrap import dedent
import unittest

from pyglm import glm

from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_DELTA_TIME,
    GLOBAL_VAR_TT_FAR,
    GLOBAL_VAR_TT_FRAME,
    GLOBAL_VAR_TT_NEAR,
    GLOBAL_VAR_TT_RESOLUTION,
    GLOBAL_VAR_TT_TIME,
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_FRAGPOS,
    PIXELVAR_TT_FRAG_DEPTH,
    PIXELVAR_TT_FRONT_FACING,
    PIXELVAR_TT_LINE_COORD,
    PIXELVAR_TT_NORMAL,
    PIXELVAR_TT_POINT_COORD,
    PIXELVAR_TT_PRIMITIVE_ID,
    PIXELVAR_TT_TEXCOORD0,
    PIXELVAR_TT_TEXCOORD1,
    PIXELVAR_TT_VIEW_POS,
    TTSLCompilerContext,
    CompileError,
    all_passes_compilation,
    compile_ttsl,
)
from tt3de.ttsl.ttsl_assembly import IRType

# Always-present pixel/cell inputs (see `TTSLCompilerContext.always_present_variables()`).
ALWAYS_PRESENT_BUILTIN_NAMES = (
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_TEXCOORD0,
    PIXELVAR_TT_TEXCOORD1,
    PIXELVAR_TT_FRAGPOS,
    PIXELVAR_TT_FRONT_FACING,
    PIXELVAR_TT_FRAG_DEPTH,
    PIXELVAR_TT_LINE_COORD,
    PIXELVAR_TT_NORMAL,
    PIXELVAR_TT_POINT_COORD,
    PIXELVAR_TT_PRIMITIVE_ID,
    PIXELVAR_TT_VIEW_POS,
)


class Test_VariableContract(unittest.TestCase):
    """Anchors tests to `always_present_variables()` and exported name constants."""

    def test_implemented_builtins_match_always_present(self):
        ref = set(TTSLCompilerContext.always_present_variables().keys())
        self.assertEqual(ref, set(ALWAYS_PRESENT_BUILTIN_NAMES))

    def test_lowercase_time_and_tt_Time_not_registered_by_default(self):
        """No implicit ``time`` or ``tt_Time`` slot — only ``globals_dict`` adds
        those."""
        src = dedent(
            """
            def simple(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(1.0, 2.0, 3.0, 1.0), vec4(1.0, 2.0, 3.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "simple", {})
        self.assertNotIn("time", cc.named_variables)
        self.assertNotIn(GLOBAL_VAR_TT_TIME, cc.named_variables)
        self.assertNotIn(GLOBAL_VAR_TT_DELTA_TIME, cc.named_variables)


class Test_BuiltinsHappyPath(unittest.TestCase):
    def test_pixel_builtins_plus_tt_Time_when_declared_in_globals(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                pulse: float = tt_Time
                u0: vec2 = tt_TexCoord0
                u1: vec2 = tt_TexCoord1
                return (
                    vec4(u0.x + u1.x + pulse * 0.0, u0.y, tt_FragCoord.x, 1.0),
                    vec4(u0.x + u1.x + pulse * 0.0, u0.y, tt_FragCoord.x, 1.0),
                    0,
                )
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
        self.assertEqual(cc.named_variables[PIXELVAR_TT_FRAGPOS].ty, IRType.V2)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_FRONT_FACING].ty, IRType.BOOL)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_FRAG_DEPTH].ty, IRType.F32)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_LINE_COORD].ty, IRType.F32)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_PRIMITIVE_ID].ty, IRType.I32)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_NORMAL].ty, IRType.V3)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_VIEW_POS].ty, IRType.V3)
        self.assertEqual(cc.globals, {GLOBAL_VAR_TT_TIME: IRType.F32})

    def test_pixel_builtins_plus_tt_DeltaTime_when_declared_in_globals(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                dt: float = tt_DeltaTime
                u0: vec2 = tt_TexCoord0
                return (
                    vec4(u0.x + dt * 0.0, u0.y, tt_FragCoord.x, 1.0),
                    vec4(u0.x + dt * 0.0, u0.y, tt_FragCoord.x, 1.0),
                    0,
                )
            """
        )
        globs = {GLOBAL_VAR_TT_DELTA_TIME: float}
        cc = compile_ttsl(src, "shade", globs)
        self.assertIn(GLOBAL_VAR_TT_DELTA_TIME, cc.named_variables)
        self.assertEqual(cc.named_variables[GLOBAL_VAR_TT_DELTA_TIME].ty, IRType.F32)
        self.assertEqual(cc.globals, {GLOBAL_VAR_TT_DELTA_TIME: IRType.F32})

    def test_tt_Resolution_when_declared_in_globals_is_vec2_uniform(self):
        globs = {GLOBAL_VAR_TT_RESOLUTION: glm.vec2}
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                r: vec2 = tt_Resolution
                return (vec4(r.x * 0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", globs)
        self.assertIn(GLOBAL_VAR_TT_RESOLUTION, cc.named_variables)
        self.assertEqual(cc.named_variables[GLOBAL_VAR_TT_RESOLUTION].ty, IRType.V2)
        self.assertEqual(cc.globals, {GLOBAL_VAR_TT_RESOLUTION: IRType.V2})

    def test_tt_Frame_when_declared_in_globals_is_i32_uniform(self):
        globs = {GLOBAL_VAR_TT_FRAME: int}
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                frame: int = tt_Frame
                return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), frame)
            """
        )
        cc = compile_ttsl(src, "shade", globs)
        self.assertIn(GLOBAL_VAR_TT_FRAME, cc.named_variables)
        self.assertEqual(cc.named_variables[GLOBAL_VAR_TT_FRAME].ty, IRType.I32)
        self.assertEqual(cc.globals, {GLOBAL_VAR_TT_FRAME: IRType.I32})

    def test_tt_FragPos_used_in_shader_body_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                p: vec2 = tt_FragPos
                return (vec4(p.x, p.y, 0.0, 1.0), vec4(p.x, p.y, 0.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertIn(PIXELVAR_TT_FRAGPOS, cc.named_variables)

    def test_tt_ViewPos_used_in_shader_body_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                p: vec3 = tt_ViewPos
                return (vec4(p.x, p.y, p.z, 1.0), vec4(p.x, p.y, p.z, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertIn(PIXELVAR_TT_VIEW_POS, cc.named_variables)

    def test_tt_Normal_used_in_shader_body_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                n: vec3 = tt_Normal
                return (vec4(n.x, n.y, n.z, 1.0), vec4(n.x, n.y, n.z, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertIn(PIXELVAR_TT_NORMAL, cc.named_variables)

    def test_tt_Normal_register_allocation_pins_v3_slot_2(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_Normal.x, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_NORMAL]
        self.assertEqual(ty, IRType.V3)
        self.assertEqual(reg_id, 2)

    def test_tt_Normal_register_seed_defaults_match_pixinfo_normal(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_Normal.x, tt_Normal.y, tt_Normal.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_NORMAL]
        self.assertEqual(ty, IRType.V3)
        self.assertEqual(reg_id, 2)
        v = reg_settings.regs[IRType.V3][reg_id]
        self.assertAlmostEqual(v.x, 0.0)
        self.assertAlmostEqual(v.y, 0.0)
        self.assertAlmostEqual(v.z, 1.0)

    def test_user_vec3_global_does_not_alias_reserved_tt_normal_tt_view_pos_slots(self):
        globs = {"u_tint": glm.vec3}
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                t: vec3 = u_tint
                return (
                    vec4(tt_Normal.x + t.x * 0.0, tt_ViewPos.x, 0.0, 1.0),
                    vec4(0.0, 0.0, 0.0, 1.0),
                    0,
                )
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", globs)
        _, n_reg = reg_settings.var_name_to_registers[PIXELVAR_TT_NORMAL]
        _, vp_reg = reg_settings.var_name_to_registers[PIXELVAR_TT_VIEW_POS]
        _, u_reg = reg_settings.var_name_to_registers["u_tint"]
        self.assertEqual(n_reg, 2)
        self.assertEqual(vp_reg, 3)
        self.assertGreaterEqual(u_reg, 4)

    def test_tt_ViewPos_register_allocation_pins_v3_slot_3(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_ViewPos.x, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_VIEW_POS]
        self.assertEqual(ty, IRType.V3)
        self.assertEqual(reg_id, 3)

    def test_tt_ViewPos_register_seed_defaults_zero_vec3(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_ViewPos.x, tt_ViewPos.y, tt_ViewPos.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_VIEW_POS]
        self.assertEqual(ty, IRType.V3)
        self.assertEqual(reg_id, 3)
        v = reg_settings.regs[IRType.V3][reg_id]
        self.assertAlmostEqual(v.x, 0.0)
        self.assertAlmostEqual(v.y, 0.0)
        self.assertAlmostEqual(v.z, 0.0)

    def test_tt_FrontFacing_branching_shader_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                if tt_FrontFacing:
                    return (vec4(1.0, 0.0, 0.0, 1.0), vec4(1.0, 0.0, 0.0, 1.0), 0)
                return (vec4(0.0, 1.0, 0.0, 1.0), vec4(0.0, 1.0, 0.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertEqual(cc.named_variables[PIXELVAR_TT_FRONT_FACING].ty, IRType.BOOL)

    def test_tt_PrimitiveID_is_always_present_i32_pixel_input(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                pid: int = tt_PrimitiveID
                return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), pid)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertIn(PIXELVAR_TT_PRIMITIVE_ID, cc.named_variables)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_PRIMITIVE_ID].ty, IRType.I32)

    def test_tt_PrimitiveID_register_seed_defaults_zero(self):
        """Compiler seeds ``tt_PrimitiveID`` to ``0`` (matches ``PixInfo::primitive_id`` init)
        so VM-only harnesses (no ``ShaderMaterial`` per-pixel write) get a deterministic value.
        """
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), tt_PrimitiveID)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_PRIMITIVE_ID]
        self.assertEqual(ty, IRType.I32)
        # Allocator special-cases ``tt_PrimitiveID`` to i32 reg 0 — pinned so
        # ``ShaderInputBinding::primitive_id_i32_reg`` (defaults to 0) keeps matching.
        self.assertEqual(reg_id, 0)
        self.assertEqual(reg_settings.regs[IRType.I32][reg_id], 0)

    def test_tt_PrimitiveID_wrong_annotation_raises(self):
        """``tt_PrimitiveID`` is ``int`` (i32); annotating the receiving variable as
        float fails."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                pid: float = tt_PrimitiveID
                return (vec4(pid, 0.0, 0.0, 1.0), vec4(pid, 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError):
            compile_ttsl(src, "shade", {})

    def test_tt_FrontFacing_register_seed_defaults_true(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                if tt_FrontFacing:
                    return (vec4(1.0, 0.0, 0.0, 1.0), vec4(1.0, 0.0, 0.0, 1.0), 0)
                return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_FRONT_FACING]
        self.assertEqual(ty, IRType.BOOL)
        self.assertEqual(reg_settings.regs[IRType.BOOL][reg_id], True)

    def test_tt_FragDepth_always_present_f32_pixel_input(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                d: float = tt_FragDepth
                return (vec4(d, 0.0, 0.0, 1.0), vec4(d, 0.0, 0.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertIn(PIXELVAR_TT_FRAG_DEPTH, cc.named_variables)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_FRAG_DEPTH].ty, IRType.F32)

    def test_tt_FragDepth_register_seed_defaults_zero(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_FragDepth, 0.0, 0.0, 1.0), vec4(tt_FragDepth, 0.0, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_FRAG_DEPTH]
        self.assertEqual(ty, IRType.F32)
        self.assertEqual(reg_settings.regs[IRType.F32][reg_id], 0.0)

    def test_tt_FragDepth_wrong_annotation_raises(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                bad: vec2 = tt_FragDepth
                return (vec4(bad.x, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError):
            compile_ttsl(src, "shade", {})

    def test_tt_LineCoord_always_present_f32_pixel_input(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                t: float = tt_LineCoord
                return (vec4(t, 0.0, 0.0, 1.0), vec4(t, 0.0, 0.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertIn(PIXELVAR_TT_LINE_COORD, cc.named_variables)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_LINE_COORD].ty, IRType.F32)

    def test_tt_LineCoord_register_seed_defaults_zero(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_LineCoord, 0.0, 0.0, 1.0), vec4(tt_LineCoord, 0.0, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_LINE_COORD]
        self.assertEqual(ty, IRType.F32)
        self.assertEqual(reg_settings.regs[IRType.F32][reg_id], 0.0)

    def test_tt_LineCoord_wrong_annotation_raises(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                bad: vec2 = tt_LineCoord
                return (vec4(bad.x, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError):
            compile_ttsl(src, "shade", {})

    def test_tt_PointCoord_always_present_v2_pixel_input(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                p: vec2 = tt_PointCoord
                return (vec4(p.x, p.y, 0.0, 1.0), vec4(p.x, p.y, 0.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {})
        self.assertIn(PIXELVAR_TT_POINT_COORD, cc.named_variables)
        self.assertEqual(cc.named_variables[PIXELVAR_TT_POINT_COORD].ty, IRType.V2)

    def test_tt_PointCoord_register_seed_defaults_zero_vec2(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_PointCoord.x, tt_PointCoord.y, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(src, "shade", {})
        ty, reg_id = reg_settings.var_name_to_registers[PIXELVAR_TT_POINT_COORD]
        self.assertEqual(ty, IRType.V2)
        self.assertEqual(reg_settings.regs[IRType.V2][reg_id], glm.vec2(0.0, 0.0))

    def test_tt_PointCoord_wrong_annotation_raises(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                bad: float = tt_PointCoord
                return (vec4(bad, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError):
            compile_ttsl(src, "shade", {})

    def test_tt_Time_requires_globals_dict(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_Time, 0.0, 0.0, 1.0), vec4(tt_Time, 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn(GLOBAL_VAR_TT_TIME, msg)
        self.assertIn("Unknown variable", msg)

    def test_tt_DeltaTime_requires_globals_dict(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_DeltaTime, 0.0, 0.0, 1.0), vec4(tt_DeltaTime, 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn(GLOBAL_VAR_TT_DELTA_TIME, msg)
        self.assertIn("Unknown variable", msg)

    def test_tt_Resolution_requires_globals_dict(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                r: vec2 = tt_Resolution
                return (vec4(r.x, r.y, 0.0, 1.0), vec4(r.x, r.y, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn(GLOBAL_VAR_TT_RESOLUTION, msg)
        self.assertIn("Unknown variable", msg)

    def test_tt_Frame_requires_globals_dict(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), tt_Frame)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn(GLOBAL_VAR_TT_FRAME, msg)
        self.assertIn("Unknown variable", msg)

    def test_tt_Near_requires_globals_dict(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_Near, 0.0, 0.0, 1.0), vec4(tt_Near, 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn(GLOBAL_VAR_TT_NEAR, msg)
        self.assertIn("Unknown variable", msg)

    def test_tt_Far_requires_globals_dict(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_Far, 0.0, 0.0, 1.0), vec4(tt_Far, 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {})
        msg = str(ctx.exception)
        self.assertIn(GLOBAL_VAR_TT_FAR, msg)
        self.assertIn("Unknown variable", msg)

    def test_tt_Near_tt_Far_globals_dict_seeded_defaults(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_Near, tt_Far, 0.0, 1.0), vec4(tt_Near, tt_Far, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(
            src,
            "shade",
            {GLOBAL_VAR_TT_NEAR: float, GLOBAL_VAR_TT_FAR: float},
        )
        _, near_id = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_NEAR]
        _, far_id = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_FAR]
        self.assertEqual(reg_settings.regs[IRType.F32][near_id], 0.1)
        self.assertEqual(reg_settings.regs[IRType.F32][far_id], 100.0)

    def test_tt_Resolution_globals_dict_seeded_to_one_by_default(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                r: vec2 = tt_Resolution
                return (vec4(r.x, r.y, 0.0, 1.0), vec4(r.x, r.y, 0.0, 1.0), 0)
            """
        )
        _, reg_settings = all_passes_compilation(
            src, "shade", {GLOBAL_VAR_TT_RESOLUTION: glm.vec2}
        )
        self.assertIn(GLOBAL_VAR_TT_RESOLUTION, reg_settings.var_name_to_registers)
        ty, reg_id = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_RESOLUTION]
        self.assertEqual(ty, IRType.V2)
        self.assertEqual(reg_settings.regs[IRType.V2][reg_id], glm.vec2(1.0, 1.0))

    def test_tt_Frame_globals_dict_seeded_to_zero_by_default(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), tt_Frame)
            """
        )
        _, reg_settings = all_passes_compilation(
            src, "shade", {GLOBAL_VAR_TT_FRAME: int}
        )
        self.assertIn(GLOBAL_VAR_TT_FRAME, reg_settings.var_name_to_registers)
        ty, reg_id = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_FRAME]
        self.assertEqual(ty, IRType.I32)
        self.assertEqual(reg_settings.regs[IRType.I32][reg_id], 0)

    def test_empty_globals_dict_builtin_only(self):
        src = dedent(
            """
            def simple(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(1.0, 2.0, 3.0, 1.0), vec4(1.0, 2.0, 3.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "simple", {})
        self.assertEqual(cc.globals, {})


class Test_UserGlobalsHappyPath(unittest.TestCase):
    def test_globals_dict_uniforms(self):
        globs = {"time": float, "position": glm.vec3}
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                t: float = time
                p: vec3 = position
                return (
                    vec4(t + tt_FragCoord.x * 0.0, p.y, p.z, 1.0),
                    vec4(t + tt_FragCoord.x * 0.0, p.y, p.z, 1.0),
                    0,
                )
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
            def shade(uv: vec2) -> tuple[vec4, vec4, int]:
                return (
                    vec4(uv.x + tt_FragCoord.x, uv.y + tt_FragCoord.y, 0.0, 1.0),
                    vec4(uv.x + tt_FragCoord.x, uv.y + tt_FragCoord.y, 0.0, 1.0),
                    0,
                )
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
        """globals_dict chooses the IR type for ``tt_Time`` (here ``int`` vs default
        ``float``)."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                tick: int = tt_Time
                return (vec4(1.0, 2.0, 3.0, 1.0), vec4(1.0, 2.0, 3.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {GLOBAL_VAR_TT_TIME: int})
        self.assertEqual(cc.named_variables[GLOBAL_VAR_TT_TIME].ty, IRType.I32)

    def test_tt_Time_shadowed_as_int_breaks_float_vec4_mixing(self):
        """sin(tt_Time) is I32; vec4(...) requires f32 components — CompileError."""
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(sin(tt_Time), 0.0, 0.0, 1.0), vec4(sin(tt_Time), 0.0, 0.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {GLOBAL_VAR_TT_TIME: int})
        msg = str(ctx.exception)
        # Root cause: globals_dict shadowed tt_Time as int, so sin(...) is I32 inside vec4(...)
        self.assertIn("vec4", msg)
        self.assertIn("f32", msg)
        self.assertIn("I32", msg)

    def test_tt_DeltaTime_shadowed_by_int_global_still_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                tick: int = tt_DeltaTime
                return (vec4(1.0, 2.0, 3.0, 1.0), vec4(1.0, 2.0, 3.0, 1.0), 0)
            """
        )
        cc = compile_ttsl(src, "shade", {GLOBAL_VAR_TT_DELTA_TIME: int})
        self.assertEqual(cc.named_variables[GLOBAL_VAR_TT_DELTA_TIME].ty, IRType.I32)


class Test_VariableFailures(unittest.TestCase):
    def test_typo_tt_Tim(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(tt_Tim, 0.0, 0.0, 1.0), vec4(tt_Tim, 0.0, 0.0, 1.0), 0)
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
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (
                    vec4(tt_fragcoord.x, 0.0, 0.0, 1.0),
                    vec4(tt_fragcoord.x, 0.0, 0.0, 1.0),
                    0,
                )
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
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (
                    vec4(mystery_uniform, 0.0, 0.0, 1.0),
                    vec4(mystery_uniform, 0.0, 0.0, 1.0),
                    0,
                )
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
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                return (vec4(1.0, 2.0, 3.0, 1.0), vec4(1.0, 2.0, 3.0, 1.0), 0)
            """
        )
        with self.assertRaises(CompileError) as ctx:
            compile_ttsl(src, "shade", {"bad": str})
        msg = str(ctx.exception)
        self.assertIn("bad", msg)
        self.assertIn("Unsupported global variable type", msg)


class Test_DocParityBuiltins(unittest.TestCase):
    """Anchors ``source/ttsl.md`` variable rows to ``compile_ttsl`` success paths."""

    def test_doc_tt_FragPos_vec2_builtin_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                p: vec2 = tt_FragPos
                return (vec4(p.x, p.y, 0.0, 1.0), vec4(p.x, p.y, 0.0, 1.0), 0)
            """
        )
        compile_ttsl(src, "shade", {})


class Test_TtDeltaTimeCompiles(unittest.TestCase):
    def test_tt_DeltaTime_float_with_globals_dict_compiles(self):
        src = dedent(
            """
            def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
                d: float = tt_DeltaTime
                return (vec4(d, 0.0, 0.0, 1.0), vec4(d, 0.0, 0.0, 1.0), 0)
            """
        )
        compile_ttsl(src, "shade", {GLOBAL_VAR_TT_DELTA_TIME: float})


if __name__ == "__main__":
    unittest.main()
