# -*- coding: utf-8 -*-
import inspect
from tt3de.ttsl.compiler import TTSLCompilerContext, compile_ttsl
from pyglm import glm

# Built-in TTSL variables. Names mirror the OpenGL `gl_<CamelCase>` convention as
# `tt_<CamelCase>`; see `source/ttsl.md` for the canonical spec.

# Global uniform:
tt_Time: float = 0.0  # noqa: N816 — built-in name follows OpenGL `gl_*` convention

# Per-fragment (cell) input variables:
tt_FragCoord: glm.vec2 = glm.vec2(0.0, 0.0)  # noqa: N816
tt_TexCoord0: glm.vec2 = glm.vec2(0.0, 0.0)  # noqa: N816
tt_TexCoord1: glm.vec2 = glm.vec2(0.0, 0.0)  # noqa: N816


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
