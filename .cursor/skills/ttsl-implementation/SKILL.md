---
name: ttsl-implementation
description: >-
  Writes and edits Tiny Tiny Shader Language (TTSL) shader source, and implements
  compiler / ISA / Cranelift-lowering changes when needed. Use for TTSL materials,
  shading logic, all_passes_compilation, ShaderPy, globals_dict, tt_* builtins,
  tt_texture, or extending python/tt3de/ttsl/, low_level_def, gen-opcodes,
  ir_lower.rs, libcalls.rs.
disable-model-invocation: true
---

# TTSL coder

You are the **TTSL language specialist** in tt3de. Default to **authoring correct shader source** that compiles and matches engine semantics. Touch the compiler, ISA, or Cranelift lowerer only when the task is explicitly to add or change language / op behavior.

## Runtime map

| Layer | Where | Role |
|-------|--------|------|
| Compiler | `python/tt3de/ttsl/` | Parse TTSL, SSA snapshot (`ssa_json()`), optional bytecode dump |
| Execute | `crates/tt3de-core/src/ttsl/jit/` | Cranelift compiles SSA; `ShaderMaterial` runs it per cell |
| Bindings | `crates/tt3de-py/` | Thin `ShaderPy` / material buffer; **no** `ttsl_run` |

Bytecode (`PassToByteCode`) is a compiler-explorer / ISA dump only. It is **not** an execute format.

## Documentation map (read first)

These files are the contract; prefer them over memory or GLSL habits:

| Topic | File |
|-------|------|
| Builtins, uniforms, textures, transparency, material bridge | [source/ttsl.md](../../../source/ttsl.md) |
| `globals_dict`, compile API, pipeline overview | [source/ttsl_compiler.md](../../../source/ttsl_compiler.md) |
| Opcode numbers and operand types (generated dump) | [source/opcode_reference.md](../../../source/opcode_reference.md) |

**Shipped vs Planned:** the primitives table in `source/ttsl.md` lists intent. Before using a function name, confirm it compiles (grep `tests/tt3de/ttsl/` or run `all_passes_compilation` on a minimal snippet). **Planned** or **Missing** rows are not safe to use in production shaders unless you are implementing them in the same change.

## Scope and boundaries

| Task | This skill | Hand off |
|------|------------|----------|
| Write / fix shader `SHADER_SRC`, uniforms, sampling, fog, transparency | **Yes** | — |
| Compile, seed registers, `ShaderPy` + `ssa_json` | **Yes** | — |
| Textual demos using `ShaderPy` | **Yes** — all `SHADER_SRC` bodies | [tt3de-demomaker](../tt3de-demomaker/SKILL.md) wires the demo only; it **delegates** shader source here |
| New TTSL builtin needing texture buffer / raster / material bridge in Rust | Compiler + `ir_lower` / `libcalls` here | [tt3de-low](../tt3de-low/SKILL.md) for engine hook |
| Scene graph, prefabs, loaders (no TTSL) | — | [tt3de-high](../tt3de-high/SKILL.md) |

## What TTSL is

TTSL is a **typed, Python-syntax shader subset** compiled to post-SSA IR (Cranelift) plus optional bytecode dumps. It is **not** full Python: no imports inside shader source, no `for` loops, no classes, no lambdas, no list/dict literals as language features. The compiler strips bare `print` and import statements from the parsed function body.

- **Types:** `float`, `int`, `bool`, `vec2`, `vec3`, `vec4` (construct with `vec2(...)` / `glm.vec2(...)`).
- **GLM:** host Python uses `from pyglm import glm`; in shaders prefer **`glm.sin`**, **`glm.vec4`**, etc. when that matches existing demos—many bare names (`sin`, `clamp`, `mod`) also work when listed below.
- **Naming:** engine builtins use `tt_` + CamelCase (GLSL `gl_` analogue), e.g. `tt_FragCoord`, `tt_Time`.

## Shader entry contract

Every entry function must **`return (front, back, glyph)`** with types **`(vec4, vec4, int)`**.

- **`front` / `back`:** RGBA for the terminal cell’s foreground and background halves. Shader materials write these **directly**—there is no post-pass alpha compositing. See **Transparency** below.
- **`glyph`:** glyph index (`int`); `0` is common when color alone drives the look.

Annotate the return type: `-> tuple[vec4, vec4, int]`. List builtins as parameters when you want explicit slots (e.g. `tt_TexCoord0: vec2`); omitting them still works for implicit per-cell inputs.

### Builtins and `globals_dict`

| Category | Names | `globals_dict` |
|----------|-------|----------------|
| **Per-cell inputs** | `tt_FragCoord`, `tt_FragPos`, `tt_Normal`, `tt_ViewPos`, `tt_TexCoord0`, `tt_TexCoord1`, `tt_FrontFacing`, `tt_FragDepth`, `tt_LineCoord`, `tt_PointCoord`, `tt_PrimitiveID` | **Do not** list—compiler + material bridge fill each pixel |
| **Engine uniforms** | `tt_Time`, `tt_DeltaTime`, `tt_Frame`, `tt_Resolution`, `tt_Near`, `tt_Far` | **Include** each name the shader reads, mapped to `float`, `int`, or `glm.vec2` **type objects** (not runtime values) |
| **User uniforms** | e.g. `u_color`, `u_TextureIndex` | Same: name → type; after compile use `RegisterSettings.set_variable` and `register_seed=reg_settings.get_register_list()` on `ShaderPy` |

`globals_dict` values are **types only**. Runtime values go through `set_variable`, `ShaderPy.*_reg`, and `MaterialBufferPy.set_shader_*` for engine uniforms. Details and examples: `source/ttsl_compiler.md`.

Use `GLOBAL_VAR_TT_TIME` from `tt3de.ttsl.compiler` in host Python when wiring `tt_Time` (matches demos).

### Textures

- **`tt_texture(texture_index: int, coord: vec2) -> vec4`** — filtered sample; pair with **`tt_TexCoord0`** / **`tt_TexCoord1`** or other `vec2` UVs.
- Declare texture index in `globals_dict` as `int` (e.g. `"u_TextureIndex": int`) and `set_variable` before engine draw.
- **`tt_texelFetch`:** specified in `source/ttsl.md` but **not** end-to-end in the compiler yet—do not use until shipped.
- Sampling needs **`ShaderPy`** + **`TextureBuffer`** in a demo or test harness.

### Transparency (critical)

When texels can be transparent, **mask in the shader**—return black (or your clear color) for both `front` and `back` where alpha is low. For **two UV sets** (`tt_TexCoord0` and `tt_TexCoord1`), mask **each half independently** to avoid key-color fringes. Copy patterns from `source/ttsl.md` (single-path and double-raster examples).

## Language surface (authoring)

Use this when writing shaders today. If something fails with `CompileError` or `NotImplementedError`, check **Pitfalls** before “fixing” the compiler.

**Statements:** annotated assignment (`x: float = ...`), plain assignment, `if` / `else`, `while`, `return` (triple only).

**Operators:** `+ - * /` on scalars and vectors; comparisons `> >= < <=`; boolean `and` / `or` (operands must be `bool`—use comparisons, not `if x:` on floats).

**Calls — prefer these (bare and/or `glm.*` where noted):**

| Category | Names |
|----------|--------|
| Unary math | `sin`, `abs`, `floor`, `ceil`, `fract`, `normalize` |
| Binary / n-ary | `mod`, `dot`, `length`, `max`, `clamp` (3 args) |
| GLM tools | **`glm.mix(a, b, t)`** — `vec2/3/4` × same × `float` `t`; bare `mix(...)` is **not** wired |
| Texture | `tt_texture` |
| Lights | `tt_lightCount`, `tt_lightType`, `tt_lightColor`, `tt_lightDirection`, `tt_lightPosition`, `tt_lightAttenuation` |
| Constructors | `vec2`, `vec3`, `vec4`, `glm.vec2`, `glm.vec3`, `glm.vec4` |
| Swizzles | `.x`, `.y`, `.z`, `.w` on vectors |

**Not supported (do not use in shaders):** `for`, `try`, classes, nested `def`, arbitrary Python calls, `min` (not shipped), `sign`, `pow`, `smoothstep`, most of the **Planned** table in `source/ttsl.md`.

### Pitfalls (common author mistakes)

| Looks valid | Actually |
|-------------|----------|
| `cos` / `tan` | Parsed on some paths; `opcode_for_uniop` only maps `sin`/`abs`/… — Cranelift can lower SSA `cos` if emitted |
| `min` | **Not shipped** — use `max` on negated values or compare via `if` |
| `mix(a,b,t)` without `glm.` | **Not wired** — use **`glm.mix`** |
| `tt_texelFetch` | **Not end-to-end** |
| Name in `ttsl.md` **Planned** | Verify compile + test before relying on it |
| `globals_dict` with `tt_FragCoord` | Wrong layer—per-cell builtins are implicit |
| Expect alpha compositing after return | **Must** zero/mask colors in shader |
| New op only in Python ISA | Cranelift will fail at compile (`UnsupportedIr`) until `ir_lower.rs` / `libcalls.rs` handle it |

## Workflow: write or change a shader

1. **Read** the relevant sections of `source/ttsl.md` (builtins + primitives + transparency).
2. **Draft** the entry function: typed locals, explicit `return (front, back, glyph)`.
3. **Compile** from host Python:

```python
from pyglm import glm
from tt3de.ttsl.compiler import GLOBAL_VAR_TT_TIME, all_passes_compilation

bytecode, reg_settings = all_passes_compilation(
    SHADER_SRC,
    "entry_fn_name",
    globals_dict={GLOBAL_VAR_TT_TIME: float, "u_MyUniform": glm.vec3},  # only names you read
)
```

4. **Integrate** into a demo/app:

```python
from tt3de.tt3de import find_glyph_indices_py, materials

shader = materials.ShaderPy(
    bytecode,
    default_glyph=find_glyph_indices_py("█"),
    register_seed=reg_settings.get_register_list(),
    ssa_json=reg_settings.ssa_json(),
)
```

Material slot 0 static sentinel, `set_shader_time` in `before_render_step`—see [demos-standards](../../../.cursor/rules/demos-standards.mdc) and `demos/2d/ttsl_square.py`.

5. **Mirror** non-obvious behavior in `tests/tt3de/ttsl/test_e2e.py` when fixing a regression.

Do **not** jump to `low_level_def.py` or opcode work when the user only asked for a shader effect solvable with the shipped surface.

## Compiler and Cranelift (when extending the language)

**Pipeline entry:** `all_passes_compilation(src, func_name, globals_dict)` in `python/tt3de/ttsl/compiler.py`.

**ISA dump changes:** edit `python/tt3de/ttsl/ttisa/low_level_def.py`, then `make gen-opcodes` or `bash scripts/gen_opcodes.sh` (PowerShell on Windows). Regenerates Python tables and `source/opcode_reference.md` only (no Rust VM).

**Execute path:** add the op to SSA emission in `compiler.py`, then lower it in [`crates/tt3de-core/src/ttsl/jit/ir_lower.rs`](../../../crates/tt3de-core/src/ttsl/jit/ir_lower.rs) and [`libcalls.rs`](../../../crates/tt3de-core/src/ttsl/jit/libcalls.rs) if it needs a C helper. An opcode that only exists in the dump will compile in the explorer and **fail at Cranelift**.

### Adding a new operation (summary)

| Pattern | Examples | Main touch points |
|---------|----------|-------------------|
| **A — Unary same-type** | `sin`, `floor`, `abs` | `ttsl_assembly.py`, `low_level_def.py`, `compiler.py`, `ir_lower.rs` / libcalls, gen-opcodes |
| **B — Binary same-type** | `mod`, `max` | Same + custom `Form` generator if not a Rust operator |
| **C — Special** | `tt_texture`, `tt_light*`, `glm.mix` | Custom `Form` + `compile_expr`; confirm Rust bridge with [tt3de-low](../tt3de-low/SKILL.md) if data leaves registers |

After implementation: `bash scripts/gen_opcodes.sh && cargo check --workspace --all-targets && cargo test -p tt3de-core && uv run maturin develop --uv`, e2e tests in `tests/tt3de/ttsl/test_e2e.py`, compiler errors in `test_compiler.py`, update **`source/ttsl.md`** row **Planned → Shipped**.

Run: `PYTHONPATH=. uv run pytest tests/tt3de/ttsl/ -v` (skip `tests/benchs/` unless needed).

## Verification checklist

**Shader-only change**

- [ ] Uses only shipped calls (see **Language surface** / **Pitfalls**)
- [ ] Correct `globals_dict` (types only; per-cell builtins omitted)
- [ ] Returns `(vec4, vec4, int)`; transparency handled in-shader if needed
- [ ] `all_passes_compilation` succeeds; `ShaderPy` + `ssa_json` or demo path exercised when non-trivial

**Compiler / lowering change**

- [ ] `gen-opcodes` run if ISA dump tables changed; no hand-edited `ttisa_opcodes.py`
- [ ] Cranelift `ir_lower` / `libcalls` updated for any new SSA op
- [ ] `cargo check --workspace --all-targets` and `cargo test -p tt3de-core` clean; `uv run pytest tests/tt3de/ttsl/`
- [ ] `source/ttsl.md` (+ opcode reference via generator) updated
