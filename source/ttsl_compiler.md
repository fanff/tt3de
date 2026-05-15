# TTSL Compiler

This project contains a full compiler pipeline for Tiny Tiny Shader Language (TTSL).
The main implementation is in `python/tt3de/ttsl/compiler.py`, and the IR/CFG data model is in `python/tt3de/ttsl/ttsl_assembly.py`.

## Example TTSL source

Built-in names follow the OpenGL/GLSL `gl_<CamelCase>` convention as `tt_<CamelCase>`
(see [TTSL spec](ttsl.md), including **Shipped** vs **Planned** rows).

### `globals_dict`: what goes in it

`globals_dict` is the **compile-time declaration map** for **host uniforms**: keys are identifier strings, and each value must be a supported **Python type** object (`float`, `int`, `bool`, `glm.vec2`, `glm.vec3`, `glm.vec4`, …—the compiler rejects any other mapping target). The compiler uses those entries only for typing and register allocation; it does **not** accept arbitrary literal initializer values in this dict. `all_passes_compilation` returns `RegisterSettings` after seeding documented defaults (`apply_engine_uniform_register_defaults`); the engine then overwrites registers each frame or each shaded cell via `ShaderPy.*_reg` and the material bridge.

**Implicit per-cell inputs** — **omit from `globals_dict`**. The compiler already knows these names and types; the material bridge fills them **per shaded cell** (not as globals):

- `tt_FragCoord`, `tt_FragPos`, `tt_TexCoord0`, `tt_TexCoord1` (`vec2`)
- `tt_ViewPos` (`vec3`)
- `tt_FrontFacing` (`bool`)
- `tt_FragDepth` (`float`)
- `tt_LineCoord` (`float`)
- `tt_PointCoord` (`vec2`)
- `tt_PrimitiveID` (`int`)

The shader entry function may still list `tt_FragCoord` (or other builtins above) as parameters; that pins them to explicit parameter slots instead of the default implicit mapping.

**Engine uniforms** — **include in `globals_dict` for each name the shader reads**. If the source references `tt_Time` but `globals_dict` omits `tt_Time`, compilation does not treat it as a declared uniform. When present, the entry maps the name to the host type and ties bytecode to the runtime hooks below:

| Name | `globals_dict` value (type) | Runtime update / register |
|------|----------------------------|---------------------------|
| `tt_Time` | `float` | `MaterialBufferPy.set_shader_time`, `ShaderPy.time_f32_reg` |
| `tt_DeltaTime` | `float` | `set_shader_delta_time`, `delta_time_f32_reg` |
| `tt_Frame` | `int` | compiler seeds `0`; `set_shader_frame`, `frame_i32_reg` (saturates at `i32::MAX`) |
| `tt_Resolution` | `glm.vec2` | seeds `(1, 1)`; `set_shader_resolution`, `resolution_v2_reg` |
| `tt_Near` | `float` | seeds `0.1`; `set_shader_near`, `near_f32_reg` |
| `tt_Far` | `float` | seeds `100.0`; `set_shader_far`, `far_f32_reg` |

**User uniforms** — any other name referenced from shader code is declared the same way (string key → type in `globals_dict`). They use the **same register banks** as engine uniforms; the compiler picks concrete indices, and you must **seed** those slots before running bytecode.

**Wiring user uniforms after `all_passes_compilation`**

1. Put each uniform name and its **type object** in `globals_dict` (for example `{"u_color": glm.vec3, "u_uv_bias": glm.vec2}`).
2. Call `reg_settings.set_variable("u_color", glm.vec3(0.2, 0.4, 0.6))` (and likewise for every uniform register you care about). Uniforms you never seed read as **numeric zero** / **false** in the VM (Rust register banks start cleared).
3. Pass the snapshot into the renderer: `register_seed=reg_settings.get_register_list()` on `ShaderPy`, or the same six dicts plus `bytecode` into `ttsl_run`.
4. Optional **engine** uniforms (`tt_Time`, …) still use `ShaderPy.time_f32_reg` (etc.) and `MaterialBufferPy.set_shader_time` so values can change every frame **without** rebuilding the material. User uniforms have **no** `MaterialBufferPy` setters today: `add_shader` copies the seed banks once, so changing a user uniform means rebuilding `ShaderPy` / re-`add_shader` (or adding a host API later).

```python
from pyglm import glm
from tt3de.tt3de import ttsl_run
from tt3de.ttsl.compiler import all_passes_compilation

SRC = """
def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
    # u_color / u_uv_bias are ordinary globals — declare types in globals_dict
    c: vec4 = vec4(u_color.x + u_uv_bias.x, u_color.y + u_uv_bias.y, u_color.z, 1.0)
    return (c, c, 0)
"""

bytecode, reg_settings = all_passes_compilation(
    SRC,
    "shade",
    globals_dict={
        "u_color": glm.vec3,
        "u_uv_bias": glm.vec2,
    },
)
reg_settings.set_variable("u_color", glm.vec3(0.1, 0.2, 0.3))
reg_settings.set_variable("u_uv_bias", glm.vec2(0.25, 0.5))

front, back, glyph = ttsl_run(*reg_settings.get_register_list(), bytecode)
assert glyph == 0

# Full renderer: pass the same seed list into ShaderPy(..., register_seed=reg_settings.get_register_list()).
```

**Minimal compile example** (per-cell builtins need no `globals_dict` entry; only `tt_Time` is declared because the shader reads it):

```python
from pyglm import glm
from tt3de.ttsl.compiler import all_passes_compilation

SRC = """
def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
    # tt_FragCoord: implicit — do not put in globals_dict
    c: vec4 = glm.vec4(tt_Time, tt_FragCoord.x * 0.01, 0.5, 1.0)
    return (c, c, 0)
"""

bytecode, reg_settings = all_passes_compilation(
    SRC,
    "shade",
    globals_dict={
        "tt_Time": float,
        # "tt_Resolution": glm.vec2,  # add only if the shader references tt_Resolution
        # "u_gain": float,             # user uniform: same pattern (name → type)
    },
)
# reg_settings holds register ids + defaults; pass into ShaderPy / ttsl_run as elsewhere in the docs
```

Per-pixel depth: `tt_FragDepth` is always predeclared as `float`. After compilation, set `ShaderPy.frag_depth_f32_reg` from `RegisterSettings` so `ShaderMaterial` writes the active depth layer’s stored depth into that register each pixel (see [TTSL](ttsl.md) builtins table).

Line interpolation: `tt_LineCoord` is always predeclared as `float` (compiler seeds `0.0`). Set `ShaderPy.line_coord_f32_reg` from `RegisterSettings` so `ShaderMaterial` writes `PixInfo.line_coord` each pixel (line rasterization fills `0.0`…`1.0` along the segment; see `DrawingBufferPy.set_depth_content(..., line_coord=...)`).

Point sprites: `tt_PointCoord` is always predeclared as `vec2` (compiler seeds `(0, 0)`). Set `ShaderPy.point_coord_v2_reg` from `RegisterSettings` so `ShaderMaterial` writes `PixInfo.point_coord` each pixel (point rasterization sets `(0.5, 0.5)` for the single-cell path; see `DrawingBufferPy.set_depth_content(..., point_coord=...)`).

Shader functions must **return a 3-tuple** `(front, back, glyph)` with types `(vec4, vec4, int)`:
front/back are RGBA vectors (or any per-channel `vec4` payload); `glyph` is a glyph index carried as a 32-bit integer in the VM (non-negative by convention). If you annotate the function’s return type, use `tuple[vec4, vec4, int]` or `typing.Tuple[vec4, vec4, int]`.

```python
def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
    pulse: float = sin(tt_Time)
    color: vec4 = glm.vec4(tt_TexCoord0.x, tt_TexCoord0.y, pulse, 1.0)
    if tt_TexCoord0.x > tt_TexCoord0.y:
        return (color, color, 0)
    else:
        dark: vec4 = glm.vec4(color.x * 0.75, color.y * 0.75, color.z * 0.75, 1.0)
        return (dark, dark, 0)
```

Compile it with the same `globals_dict={"tt_Time": float}` shape as the minimal example (no alternate `"time"` key).

**Texture sampling:** `tt_texture(tex_index: int, coord: vec2) -> vec4` is lowered to opcode `TT_TEXTURE`. In `Shader` materials the Rust runtime passes the live `TextureBuffer` into the VM; standalone `ttsl_run` from Python has no texture binding (samples behave as opaque black per spec). `tt_texelFetch` is not implemented yet.

Note: `glm.mix` is not yet typable in `type_of(...)`, so prefer arithmetic or other supported ops until mix is wired end-to-end.

## Where compilation starts

The public entry point is:

- `all_passes_compilation(src, func_name, globals_dict)`

This function runs the whole pipeline and returns:

- compiled bytecode as `bytes`
- `RegisterSettings` preloaded with variable/register mapping and constants

## High-level pipeline

The compiler transforms Python-like TTSL source in several stages:

1. Parse source to Python AST
2. Compile AST nodes into typed IR instructions (`IRProgram`)
3. Build a Control Flow Graph (CFG)
4. Convert named variables to SSA form (`PassSSARenamer`)
5. Lower phi nodes into explicit copies (`PassPhiNodeLowering`)
6. Allocate typed virtual-machine registers (`RegisterAllocatorPass`)
7. Normalize terminators / block layout
8. Encode IR into final bytecode (`PassToByteCode`)

## Stage-to-source references

- Pipeline orchestrator: `python/tt3de/ttsl/compiler.py` (`all_passes_compilation(...)`)
- Front-end parsing/AST cleanup and IR generation:
  - `python/tt3de/ttsl/compiler.py` (`compile_ttsl(...)`, `compile_ttsl_function(...)`)
  - `python/tt3de/ttsl/compiler.py` (`CleanPythonTreePass`, `TTSLCompilerContext.compile_stmt(...)`, `TTSLCompilerContext.compile_expr(...)`, `TTSLCompilerContext.type_of(...)`)
- CFG construction:
  - `python/tt3de/ttsl/ttsl_assembly.py` (`build_cfg_from_ir(...)`)
- SSA conversion:
  - `python/tt3de/ttsl/compiler.py` (`PassSSARenamer`, `SSARenamer`)
- Phi lowering:
  - `python/tt3de/ttsl/compiler.py` (`PassPhiNodeLowering`)
- Register allocation:
  - `python/tt3de/ttsl/compiler.py` (`RegisterAllocatorPass`)
- Terminator normalization:
  - `python/tt3de/ttsl/compiler.py` (`PassNormalizeTerminators`)
- Bytecode lowering:
  - `python/tt3de/ttsl/compiler.py` (`PassToByteCode`)

## Front-end: AST to IR

`TTSLCompilerContext` is the core front-end object.

It tracks:

- the IR program (`code`)
- known variables and their types (`named_variables`)
- temporary values (`Temp`)
- constants (`const_pool`)

Important methods:

- `compile_stmt(...)`: compiles statements (`Assign`, `AnnAssign`, `If`, `Return`, etc.)
- `compile_expr(...)`: compiles expressions (`BinOp`, `Call`, `Compare`, vector member access, ...)
- `type_of(...)`: enforces type rules and resolves expression result types

The compiler is strongly typed at IR level (`IRType`): `F32`, `I32`, `BOOL`, `V2`, `V3`, `V4`.

## Supported language features (current code)

The current implementation supports a focused shader-style subset:

- scalar and vector arithmetic (`+`, `-`, `*`, `/`)
- comparisons (`>`, `>=`, `<`, `<=`)
- conditionals (`if` / `else`)
- returns (must be a 3-tuple `(vec4, vec4, int)`; see example above)
- vector constructors (`vec2`, `vec3`, `vec4`, including `glm.vec*`)
- unary `-` on numeric / vector types
- math calls: bare `sin`, `abs`; `glm.sin` (VM `SIN_*` / `ABS_*`). Bare `cos` / `glm.cos` fail at codegen today (`opcode_for_uniop` only maps `sin` and `abs`), though unary `COS_*` opcodes exist in the VM.
- vector component reads (`.x`, `.y`, `.z`, `.w`)

`compile_glm_tool_call` can lower `glm.mix` to `MIX_*`, but `glm.mix(...)` does not type-check yet because `type_of` does not handle the `mix` attribute path—use other expressions until that is fixed.

When unsupported syntax is encountered, the compiler raises `CompileError` or `NotImplementedError`.

## Middle-end: CFG and SSA

After front-end IR generation:

- `build_cfg_from_ir(...)` creates basic blocks and control-flow arcs
- variable definition sites are collected
- dominance analysis is run on CFG
- phi nodes are inserted using a Cytron-style algorithm
- `SSARenamer` rewrites variable uses/defs into SSA temps

This gives a cleaner representation for optimization/lowering and for deterministic register assignment.

## Phi lowering and register allocation

`PassPhiNodeLowering` removes SSA phi instructions by inserting edge copies.
It handles critical edges by splitting them when needed.

`RegisterAllocatorPass` then maps each typed temp to the VM’s typed register banks
(`[T; 256]` per kind in Rust; the allocator walks indices `1..255` and reserves slots that
must not alias material-bridge inputs such as default UV extrusion `v3` indices).

Constants are also assigned registers, because final opcodes carry register ids rather than literal payloads.

## Back-end: bytecode emission

`PassToByteCode` converts each typed IR instruction to a concrete VM opcode form:

- picks an opcode form from `ttisa.low_level_def.generate_all_forms()`
- rewrites operands from temps to register ids
- resolves block labels to instruction addresses for jumps
- outputs fixed-width instruction words (6 integers each)

Finally, instructions are flattened and packed into a `bytes` object.

## Key files

- `python/tt3de/ttsl/compiler.py`: pipeline passes and orchestration
- `python/tt3de/ttsl/ttsl_assembly.py`: IR types, instructions, CFG, analysis helpers
- `tests/tt3de/ttsl/test_compiler.py`: tests for compiler behavior

## Quick extension guide

To add a new language/operator feature:

1. Add type inference support in `type_of(...)`
2. Add IR emission in `compile_expr(...)` or `compile_stmt(...)`
3. Ensure opcode mapping exists (or add one)
4. Ensure bytecode form exists in low-level op definitions
5. Add tests in `tests/tt3de/ttsl/test_compiler.py`

This order keeps front-end typing, IR generation, and back-end encoding consistent.
