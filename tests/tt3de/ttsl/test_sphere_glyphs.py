# -*- coding: utf-8 -*-
"""Compile and execute the ``sphere_glyphs`` demo shader (10-step ASCII ramp)."""

from __future__ import annotations

import importlib.util
import math
import unittest
from pathlib import Path

from pyglm import glm

from tests.tt3de.ttsl.shade import shade
from tt3de.ttsl.compiler import (
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_NORMAL,
    PIXELVAR_TT_VIEW_POS,
    all_passes_compilation,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_PATH = REPO_ROOT / "demos" / "3d" / "ttsl_normal_viewpos.py"


def _load_demo():
    spec = importlib.util.spec_from_file_location("ttsl_normal_viewpos_demo", DEMO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _python_reference(
    normal: glm.vec3,
    view_pos: glm.vec3,
    albedo: glm.vec3,
    glyphs: tuple[int, ...],
) -> tuple[glm.vec4, glm.vec4, int]:
    n = glm.normalize(normal)
    vdir = glm.normalize(-view_pos)
    ldir = glm.normalize(glm.vec3(0.35, 0.72, 0.48))
    diff = max(0.0, float(glm.dot(n, ldir)))
    edge = min(1.0, max(0.0, 1.0 - max(0.0, float(glm.dot(n, vdir)))))
    rim = edge * edge
    shade_v = min(1.0, max(0.0, diff + rim * 0.42))
    ink_w = min(1.0, max(0.0, 0.12 + 0.88 * shade_v))
    ink = albedo * ink_w
    fr = glm.vec4(ink.x, ink.y, ink.z, 1.0)
    bg = glm.vec4(albedo.x, albedo.y, albedo.z, 1.0)
    inv = min(0.999, max(0.0, 1.0 - shade_v))
    band = int(math.floor(inv * 10.0))
    band = min(9, max(0, band))
    return (fr, bg, glyphs[band])


class TestSphereGlyphsRamp(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.demo = _load_demo()
        cls.bytecode, cls.reg_settings = all_passes_compilation(
            cls.demo.SHADER_SPHERE_GLYPHS_SRC,
            "sphere_glyphs",
            {"u_albedo": glm.vec3, **cls.demo.GLYPH_GLOBALS},
        )
        cls.albedo = cls.demo.ALBEDO_GLYPH_SPHERE
        cls.glyphs = tuple(int(g) for g in cls.demo.GLYPH_RAMP)
        cls.reg_settings.set_variable("u_albedo", cls.albedo)
        for name, glyph in zip(cls.demo.GLYPH_UNIFORM_NAMES, cls.glyphs, strict=True):
            cls.reg_settings.set_variable(name, glyph)
        cls.reg_settings.set_variable(PIXELVAR_TT_FRAGCOORD, glm.vec2(0.37, 0.61))

    def test_ramp_is_ten_distinct_ascii_glyphs(self) -> None:
        self.assertEqual(self.demo.GLYPH_RAMP_CHARS, " .:-=+*#%@")
        self.assertEqual(len(self.glyphs), 10)
        self.assertEqual(len(set(self.glyphs)), 10)
        self.assertTrue(all(0 <= g < 128 for g in self.glyphs))

    def test_vm_matches_python_reference_across_bands(self) -> None:
        # Facet normals that sweep lit → shadowed so several ramp steps fire.
        samples = (
            glm.vec3(0.35, 0.72, 0.48),
            glm.vec3(0.31, 0.62, -0.72),
            glm.vec3(0.0, 1.0, 0.0),
            glm.vec3(0.0, 0.2, -1.0),
            glm.vec3(-0.4, -0.3, -0.85),
            glm.vec3(-0.8, -0.5, -0.2),
            glm.vec3(0.1, -0.9, 0.2),
        )
        view_pos = glm.vec3(0.44, 0.18, 3.10)
        seen: set[int] = set()
        for normal in samples:
            self.reg_settings.set_variable(PIXELVAR_TT_NORMAL, normal)
            self.reg_settings.set_variable(PIXELVAR_TT_VIEW_POS, view_pos)
            front, back, glyph = shade(self.reg_settings)
            exp_front, exp_back, exp_glyph = _python_reference(
                normal, view_pos, self.albedo, self.glyphs
            )
            self.assertEqual(glyph, exp_glyph)
            self.assertEqual(back, exp_back)
            self.assertAlmostEqual(front.x, exp_front.x, places=4)
            self.assertAlmostEqual(front.y, exp_front.y, places=4)
            self.assertAlmostEqual(front.z, exp_front.z, places=4)
            seen.add(int(glyph))
        self.assertGreaterEqual(len(seen), 3)
