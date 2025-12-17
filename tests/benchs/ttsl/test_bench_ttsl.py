# -*- coding: utf-8 -*-
from tt3de.ttsl.compiler import all_passes_compilation, PIXELVAR_TTSL_UV0
import pytest

from tt3de.tt3de import ttsl_run
from pyglm import glm


def rversion(regs, bytecode: bytes):
    ttsl_run(*regs, bytecode)


SHADER_CODE = """
def frag(pos: vec2) -> vec3:
    return vec3(ttsl_uv0.x, ttsl_uv0.y, 0.0)
"""

SHADER_CODE2 = """
def frag(pos: vec2) -> vec3:
    a:vec3 = vec3(1.0, 2.0, 3.0)
    b:vec3 = vec3(4.0, 5.0, 6.0)
    c:vec3 = a + b + a + b + a + b + a + b + a + b
    return vec3(ttsl_uv0.x, ttsl_uv0.y, 0.0)
"""


all_codes = [SHADER_CODE, SHADER_CODE2]
sizes = list(range(len(all_codes)))


@pytest.mark.parametrize("shader_codeidx", sizes)
@pytest.mark.benchmark(group="ttsl_run")
def test_simple(benchmark, shader_codeidx):
    # compile the shader first
    bytecode, reg_settings = all_passes_compilation(
        all_codes[shader_codeidx], "frag", {}
    )
    # reg_settings.set_variable(GLOBAL_VAR_TTSL_TIME, 1221.1)
    reg_settings.set_variable(PIXELVAR_TTSL_UV0, glm.vec2(0.5, 0.5))
    # reg_settings.set_variable(PIXELVAR_TTSL_UV1, glm.vec2(0.5, 0.5))
    # reg_settings.set_variable(ON_SCREEN_POSITION_VAR_NAME, glm.vec2(0.5, 0.5))
    len(bytecode)
    # from the rar, prepare the registers
    regs = reg_settings.get_register_list()
    benchmark.extra_info["bytecode_size"] = len(bytecode)
    benchmark(rversion, regs, bytecode)

    print("Done benchmark for shader code idx:", benchmark)
