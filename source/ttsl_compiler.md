# TTSL Compiler

This project contains a full compiler pipeline for Tiny Tiny Shader Language (TTSL).
The main implementation is in `python/tt3de/ttsl/compiler.py`, and the IR/CFG data model is in `python/tt3de/ttsl/ttsl_assembly.py`.

## Example TTSL source

Built-in names follow the OpenGL/GLSL `gl_<CamelCase>` convention as `tt_<CamelCase>`
(see [TTSL spec](ttsl.md), including **Shipped** vs **Planned** rows).

**Always predeclared** (per-cell inputs; do not list in `globals_dict`):

- `tt_FragCoord`, `tt_FragPos`, `tt_TexCoord0`, `tt_TexCoord1` (`vec2`)
- `tt_FrontFacing` (`bool`)
- `tt_PrimitiveID` (`int`)

The shader entry function may still declare `tt_FragCoord` (or other builtins) as parameters;
that replaces the default slot for those names in the register map.

**Engine uniforms** — only bound when passed in `globals_dict` if the shader references them:

- `tt_Time` → `globals_dict={"tt_Time": float}`; runtime: `MaterialBufferPy.set_shader_time`, `ShaderPy.time_f32_reg`
- `tt_DeltaTime` → `{"tt_DeltaTime": float}`; `set_shader_delta_time`, `delta_time_f32_reg`
- `tt_Frame` → `{"tt_Frame": int}`; compiler seeds `0`; `set_shader_frame`, `frame_i32_reg` (saturates at `i32::MAX`)
- `tt_Resolution` → `{"tt_Resolution": glm.vec2}`; seeds `(1, 1)`; `set_shader_resolution`, `resolution_v2_reg`

User uniforms (any other name, e.g. `"position"`) are also declared only through `globals_dict`.

Shader functions must **return a 3-tuple** `(front, back, glyph)` with types `(vec3, vec3, int)`:
front/back are RGB triples (or any per-channel `vec3` payload); `glyph` is a glyph index carried as a 32-bit integer in the VM (non-negative by convention). If you annotate the function’s return type, use `tuple[vec3, vec3, int]` or `typing.Tuple[vec3, vec3, int]`.

```python
def shade(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
    pulse: float = sin(tt_Time)
    color: vec3 = glm.vec3(tt_TexCoord0.x, tt_TexCoord0.y, pulse)
    if tt_TexCoord0.x > tt_TexCoord0.y:
        return (color, color, 0)
    else:
        dark: vec3 = glm.vec3(color.x * 0.75, color.y * 0.75, color.z * 0.75)
        return (dark, dark, 0)
```

Compile the above with `globals_dict={"tt_Time": float}` (and no extra implicit `"time"` uniform).

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
- returns (must be a 3-tuple `(vec3, vec3, int)`; see example above)
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
