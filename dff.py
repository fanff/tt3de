# -*- coding: utf-8 -*-

from tt3de.ttsl.compiler import (
    CFGSimplifyPass,
    PassPhiNodeLowering,
    PassSSARenamer,
    PassToByteCode,
    RegisterAllocatorPass,
    TTSLCompilerContext,
    PassNormalizeTerminators,
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


@ttsl(globals={})
def my_shader(pos: glm.vec2) -> glm.vec3:  # noqa: F811
    # calculate a skybox background based on pos (from -1 to 1)
    color_sky: glm.vec3 = glm.vec3(0.2, 0.4, 0.8)
    color_horizon: glm.vec3 = glm.vec3(0.8, 0.9, 1.0)
    t: float = (pos.y + 1.0) / 2.0
    mixed: glm.vec3 = glm.mix(color_sky, color_horizon, t)  # noqa

    return mixed


# compile_ttsl(shader)  # Ensure it's pre-compiled
ttsl_cc: TTSLCompilerContext = my_shader.compile()

cfg = build_cfg_from_ir(ttsl_cc)
PassPrintConsole(ttsl_cc).run()

PassSSARenamer(ttsl_cc).run()
PassPrintConsole(ttsl_cc).run()


PassPhiNodeLowering(ttsl_cc).run()
PassPrintConsole(ttsl_cc).run()
CFGSimplifyPass(ttsl_cc).run()
rar = RegisterAllocatorPass(ttsl_cc).run()


PassNormalizeTerminators(ttsl_cc).run()
PassPrintConsole(ttsl_cc).run()
final_byte_code = PassToByteCode(ttsl_cc).run(rar)

print("FINAL BYTECODE:")
all_bytecode_instrs = []
for bytecode_instr in final_byte_code:
    print(bytecode_instr)
    all_bytecode_instrs.extend(bytecode_instr)
# convert the bytecode to a bytes array
byte_array = bytearray(all_bytecode_instrs)
print("FINAL BYTECODE AS BYTES:")
# print as base16
print(byte_array.hex())

# PassPrintConsole(ttsl_cc).run()
quit()
