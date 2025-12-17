# -*- coding: utf-8 -*-
from tt3de.ttsl.ttisa.ttisa_opcodes import (
    ADD_F32,
    OP_RET,
    STORE_F32,
    STORE_V2,
    STORE_V3,
    STORE_V4,
)
from tt3de.ttsl.ttsl_assembly import IRType
from typing import Dict, Any, List
from tt3de.ttsl.compiler import (
    all_passes_compilation,
    PIXELVAR_TTSL_UV0,
    RegisterSettings,
)
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
    c:vec3 = a + b
    c:vec3 = a + b
    c:vec3 = a + b
    c:vec3 = a + b
    c:vec3 = a + b
    c:vec3 = a + b
    c:vec3 = a + b
    c:vec3 = a + b
    return vec3(ttsl_uv0.x, ttsl_uv0.y, 0.0)
"""


all_codes = [SHADER_CODE, SHADER_CODE2]
sizes = list(range(len(all_codes)))


class CustomBenchmark:
    def __init__(self):
        self.context_info: Dict[str, Any] = {}

    def run(self, fn, *args, **kwargs):
        import time

        start = time.time()
        for i in range(10):
            fn(*args, **kwargs)
        end = time.time()
        atomic_time_sec = max((end - start) / 10.0, 1e-5)

        max_duration_sec = self.context_info.get("max_duration_sec", 1)  # in seconds
        # calculate how many iterations we can do in max_time
        iterations = max(1, int(max_duration_sec / atomic_time_sec))

        start = time.time()
        for _i in range(iterations):
            fn(*args, **kwargs)
        end = time.time()

        self.context_info["total_time_sec"] = float(end - start)
        self.context_info["iterations"] = iterations


def test_compiled(benchmark: CustomBenchmark, shader_codeidx):
    # compile the shader first
    bytecode, reg_settings = all_passes_compilation(
        all_codes[shader_codeidx], "frag", {}
    )
    reg_settings.set_variable(PIXELVAR_TTSL_UV0, glm.vec2(0.5, 0.5))
    benchmark.context_info["bytecode_size"] = len(bytecode) / 6
    benchmark.run(rversion, reg_settings.get_register_list(), bytecode)

    print("Done benchmark for shader code idx:", benchmark.context_info)


def bench_raw_code(
    benchmark: CustomBenchmark, bytecode: bytes, reg_settings: RegisterSettings
):

    # compile the shader first
    reg_settings.set_variable(PIXELVAR_TTSL_UV0, glm.vec2(0.5, 0.5))
    benchmark.context_info["bytecode_size"] = len(bytecode) / 6
    benchmark.run(rversion, reg_settings.get_register_list(), bytecode)


def test_empty_code(benchmark: CustomBenchmark):
    reg_settings = RegisterSettings(RegisterSettings.default_vars_to_registers())
    bench_raw_code(benchmark, bytes([]), reg_settings)


def test_ret_code(benchmark: CustomBenchmark):
    reg_settings = RegisterSettings(RegisterSettings.default_vars_to_registers())
    bench_raw_code(benchmark, bytes([OP_RET, 0, 0, 0, 0, 0]), reg_settings)


def test_store_ty(benchmark: CustomBenchmark, ty: IRType):
    reg_settings = RegisterSettings(RegisterSettings.default_vars_to_registers())
    benchmark.context_info["ty"] = ty.name
    ret0 = [OP_RET, 0, 0, 0, 0, 0]
    opfrom_ty = {
        IRType.F32: STORE_F32,
        IRType.V2: STORE_V2,
        IRType.V3: STORE_V3,
        IRType.V4: STORE_V4,
    }
    op_code_tested = opfrom_ty[ty]
    dastore = [op_code_tested, 1, 0, 0, 0, 0] * 200  # store to reg 1, from reg 0
    linear_count = {op_code_tested: 200}
    benchmark.context_info["linear_count"] = linear_count
    bench_raw_code(benchmark, bytes(dastore + ret0), reg_settings)


def test_repetitive_operation(benchmark: CustomBenchmark, op_code: int):
    reg_settings = RegisterSettings(RegisterSettings.default_vars_to_registers())
    dastore = []
    for _ in range(100):
        dastore += [
            op_code,
            2,
            0,
            1,
            0,
            0,
        ]  # reg2 = reg0 + reg1
    dastore += [OP_RET, 0, 0, 0, 0, 0]
    benchmark.context_info["linear_count"] = {op_code: 100}
    bench_raw_code(benchmark, bytes(dastore), reg_settings)


bytecode = bytes([])

if __name__ == "__main__":
    all_benchs: List[CustomBenchmark] = []
    for idx in sizes:
        b = CustomBenchmark()
        test_compiled(b, idx)
        all_benchs.append(b)

    # test empty code
    b = CustomBenchmark()
    test_empty_code(b)
    all_benchs.append(b)

    # test store for different types
    for ty in [
        IRType.F32,
        IRType.V2,
        IRType.V3,
        IRType.V4,
    ]:
        b = CustomBenchmark()
        test_store_ty(b, ty)
        all_benchs.append(b)

    for b in all_benchs:
        b.context_info["ops_per_sec"] = (
            b.context_info["bytecode_size"] * b.context_info["iterations"]
        ) / b.context_info["total_time_sec"]

    for b in all_benchs:
        print(b.context_info)
