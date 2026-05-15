# -*- coding: utf-8 -*-
import inspect
from tt3de.ttsl.compiler import TTSLCompilerContext, compile_ttsl
from pyglm import glm

# Built-in TTSL variables. Names mirror the OpenGL `gl_<CamelCase>` convention as
# `tt_<CamelCase>`; see `source/ttsl.md` for the canonical spec.

# Global uniforms (declare in ``globals_dict`` / ``ShaderDescriptor.globals`` when used):
tt_Time: float = 0.0  # noqa: N816 — built-in name follows OpenGL `gl_*` convention
tt_DeltaTime: float = 0.0  # noqa: N816 — frame delta seconds; host updates via material API
tt_Frame: int = 0  # noqa: N816 — non-negative frame counter
tt_Resolution: glm.vec2 = glm.vec2(1.0, 1.0)  # noqa: N816 — width_cells, height_cells
tt_Near: float = 0.1  # noqa: N816 — near clip distance; compiler seeds until host writes
tt_Far: float = 100.0  # noqa: N816 — far clip distance; must exceed near in real scenes

# Per-fragment (cell) input variables:
tt_FragCoord: glm.vec2 = glm.vec2(0.0, 0.0)  # noqa: N816
tt_FragPos: glm.vec2 = glm.vec2(0.0, 0.0)  # noqa: N816
tt_ViewPos: glm.vec3 = glm.vec3(0.0, 0.0, 0.0)  # noqa: N816 — view-space fragment position; see PixInfo / ShaderMaterial
tt_Normal: glm.vec3 = glm.vec3(0.0, 0.0, 1.0)  # noqa: N816 — view-space interpolated normal; see PixInfo / ShaderMaterial
tt_TexCoord0: glm.vec2 = glm.vec2(0.0, 0.0)  # noqa: N816
tt_TexCoord1: glm.vec2 = glm.vec2(0.0, 0.0)  # noqa: N816
tt_FrontFacing: bool = True  # noqa: N816
tt_FragDepth: float = 0.0  # noqa: N816 — depth for the shaded layer; engine fills via ShaderPy
tt_LineCoord: float = 0.0  # noqa: N816 — parametric coord along rasterized lines; see PixInfo / ShaderPy
tt_PointCoord: glm.vec2 = glm.vec2(0.0, 0.0)  # noqa: N816 — point sprite coords; see PixInfo / ShaderPy
tt_PrimitiveID: int = 0  # noqa: N816 — per-pixel index of depth-winning primitive


class ShaderDescriptor:
    def __init__(self, fn, globals):
        self.fn = fn
        self.globals = globals
        self._compiled: TTSLCompilerContext | None = None

    def compile(self) -> TTSLCompilerContext:
        if self._compiled is None:
            src = inspect.getsource(self.fn)
            self._compiled = compile_ttsl(src, self.fn.__name__, self.globals)
        return self._compiled


def ttsl(globals=None):
    globals = globals or {}

    def decorator(fn):
        return ShaderDescriptor(fn, globals)

    return decorator
