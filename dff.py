# -*- coding: utf-8 -*-

from tt3de.ttsl.compiler import (
    CFGSimplifyPass,
    PassPhiNodeLowering,
    PassSSARenamer,
    PassToByteCode,
    RegisterAllocatorPass,
    TTSLCompilerContext,
)
from pyglm import glm

from tt3de.ttsl.decorator import ttsl, ttsl_time, ttsl_uv0, ttsl_uv1
from tt3de.ttsl.enrich import (
    PassPrintConsole,
)
from tt3de.ttsl.ttsl_assembly import (
    build_cfg_from_ir,
)
from rich.console import Console

console = Console()


@ttsl(globals={"time": float, "position": glm.vec3})
def my_shader(pos: glm.vec2) -> glm.vec3:
    # accessing variables coming from the fragment:
    uv0: glm.vec2 = ttsl_uv0
    uv1: glm.vec2 = ttsl_uv1  # noqa

    if uv0.x < 0.5:
        return glm.vec3(1.0, -2.0, 0.0)
    else:
        return glm.vec3(
            abs(glm.sin(pos.x * 10.0 + ttsl_time / 2.0)),
            abs(glm.sin(pos.y * 10.0 + ttsl_time / 2.0)),
            0.5,
        )


@ttsl(globals={"time": float, "position": glm.vec3})
def my_shader(pos: glm.vec2) -> glm.vec3:  # noqa: F811
    # accessing variables coming from the fragment:
    c: float = 0.0  # noqa

    if ttsl_uv0.x < 0.5:
        # c: float = 2.0
        a: float = 2.0  # noqa
        b: float = 1.0
    else:
        a: float = 3.0  # noqa
        b: float = 1.0

    return glm.vec3(
        abs(glm.sin(ttsl_time / b)),
        abs(glm.sin(ttsl_time / b)),
        0.5,
    )


# compile_ttsl(shader)  # Ensure it's pre-compiled
ttsl_cc: TTSLCompilerContext = my_shader.compile()

cfg = build_cfg_from_ir(ttsl_cc)
PassSSARenamer(ttsl_cc).run()

PassPrintConsole(ttsl_cc).run()


PassPhiNodeLowering(ttsl_cc).run()

quit()
CFGSimplifyPass(ttsl_cc).run()
RegisterAllocatorPass(ttsl_cc).run()
PassToByteCode(ttsl_cc).run()
