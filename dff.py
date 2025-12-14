# -*- coding: utf-8 -*-

from tt3de.ttsl.compiler import PassSSARenamer, TTSLCompilerContext
from pyglm import glm

from tt3de.ttsl.decorator import ttsl, ttsl_time, ttsl_uv0, ttsl_uv1
from tt3de.ttsl.enrich import (
    cfg_to_rich,
    env_table_to_rich,
    const_pool_to_rich,
    instr_list_to_rich,
)
from tt3de.ttsl.ttsl_assembly import (
    CFG,
    build_cfg_from_ir,
)
from rich.console import Console


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
        a: float = 2.0
        b: float = 1.0
    else:
        a: float = 3.0
        b: float = 1.0

    return a + b


console = Console()


def print_ttsl_compiler(ttsl_compiler: TTSLCompilerContext) -> None:
    cfg: CFG = ttsl_compiler.cfg

    tinstrs = instr_list_to_rich(cfg.to_irprog())

    tenv = env_table_to_rich(ttsl_compiler.named_variables)
    tconst_pool = const_pool_to_rich(ttsl_compiler.const_pool)
    t_cfg = cfg_to_rich(cfg)

    all_ = [tinstrs, tenv, tconst_pool, t_cfg]
    for item in all_:
        console.print(item)


# compile_ttsl(shader)  # Ensure it's pre-compiled
ttsl_cc: TTSLCompilerContext = my_shader.compile()

cfg = build_cfg_from_ir(ttsl_cc)
PassSSARenamer(ttsl_cc).run()
print_ttsl_compiler(ttsl_cc)


# variables_defs: Dict[SSAVarID, Set[NodeID]] = {}
# cfg.variables_definitions() -> Dict[SSAVarID, Set[NodeID]]
# for node_idx, node in cfg.node_items():
#     for instr in node.instrs():
#         if isinstance(instr.dst, Temp):
#             # find variable name
#             filt = [
#                 name
#                 for name, temp in ttsl_compiler.named_variables.items()
#                 if temp.id == instr.dst.id
#             ]
#             if not filt:
#                 continue
#             var_name = filt[0]
#
#             if var_name not in variables_defs:
#                 variables_defs[var_name] = set()
#             variables_defs[var_name].add(node_idx)

# console.print("Node writting variables:", variables_defs)

# console.print(*compiler_to_rich(ttsl_compiler), sep="\n")
