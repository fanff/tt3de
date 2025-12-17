# -*- coding: utf-8 -*-
import inspect
from tt3de.ttsl.compiler import TTSLCompilerContext, compile_ttsl
from pyglm import glm

# Constant accessible in the global uniforms:
ttsl_time: float = 0.0

# Pixel input variables:
ttsl_uv0: glm.vec2 = glm.vec2(0.0, 0.0)
ttsl_uv1: glm.vec2 = glm.vec2(0.0, 0.0)
screen_pos: glm.vec2 = glm.vec2(0.0, 0.0)


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
