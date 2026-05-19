---
name: ttsl-implementation
description: >-
  Writes and edits Tiny Tiny Shader Language (TTSL) shader source, and implements
  compiler / VM / opcode changes when needed. Use for TTSL materials, shading logic,
  all_passes_compilation, ttsl_run, ShaderPy, globals_dict, tt_* builtins,
  tt_texture, or extending python/tt3de/ttsl/, low_level_def, gen-opcodes.
disable-model-invocation: true
---

# TTSL coder

You are the **TTSL language specialist** in tt3de. Default to **authoring correct shader source** that compiles and matches engine semantics. Touch the compiler, ISA, or Rust VM only when the task is explicitly to add or change language / opcode behavior.

## Documentation map (read first)

These files are the contract; prefer them over memory or GLSL habits:

| Topic | File |
|-------|------|
| Builtins, uniforms, textures, transparency, material bridge | [source/ttsl.md](../../../source/ttsl.md) |
| `globals_dict`, compile API, pipeline overview | [source/ttsl_compiler.md](../../../source/ttsl_compiler.md) |
| Opcode numbers and operand types (generated) | [source/opcode_reference.md](../../../source/opcode_reference.md) |

**Shipped vs Planned:** the primitives table in `source/ttsl.md` lists intent. Before using a function name, confirm it compiles (grep `tests/tt3de/ttsl/` or run `all_passes_compilation` on a minimal snippet). **Planned** or **Missing** rows are not safe to use in production shaders unless you are implementing them in the same change.

## Scope and boundaries

| Task | This skill | Hand off |
|------|------------|----------|
| Write / fix shader `SHADER_SRC`, uniforms, sampling, fog, transparency | **Yes** | — |
| Compile, seed registers, `ttsl_run` smoke tests | **Yes** | — |
| Textual demos using `ShaderPy` | **Yes** — all `SHADER_SRC` bodies | [tt3de-demomaker](../tt3de-demomaker/SKILL.md) wires the demo only; it **delegates** shader source here |
| New TTSL builtin needing texture buffer / raster / material bridge in Rust | Opcode + compiler here | [tt3de-low](../tt3de-low/SKILL.md) for engine hook |
| Scene graph, prefabs, loaders (no TTSL) | — | [tt3de-high](../tt3de-high/SKILL.md) |

## What TTSL is

TTSL is a **typed, Python-syntax shader subset** compiled to tt3de VM bytecode. It is **not** full Python: no imports inside shader source, no `for` loops, no classes, no lambdas, no list/dict literals as language features. The compiler strips bare `print` and import statements from the parsed function body.

- **Types:** `float`, `int`, `bool`, `vec2`, `vec3`, `vec4` (construct with `vec2(...)` / `glm.vec2(...)`).
- **GLM:** host Python uses `from pyglm import glm`; in shaders prefer **`glm.sin`**, **`glm.vec4`**, etc. when that matches existing demos—many bare names (`sin`, `clamp`, `mod`) also work when listed below.
- **Naming:** engine builtins use `tt_` + CamelCase (GLSL `gl_` analogue), e.g. `tt_FragCoord`, `tt_Time`.

## Shader entry contract

Every entry function must **`return (front, back, glyph)`** with types **`(vec4, vec4, int)`** (VM `OP_RET`).

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
- Declare texture index in `globals_dict` as `int` (e.g. `"u_TextureIndex": int`) and `set_variable` before `ttsl_run` or engine draw.
- **`tt_texelFetch`:** specified in `source/ttsl.md` but **not** end-to-end in the compiler yet—do not use until shipped.
- Standalone **`ttsl_run`** has **no** texture binding (typically black). Full sampling needs **`ShaderPy`** + **`TextureBuffer`** in a demo or test harness.

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
| Constructors | `vec2`, `vec3`, `vec4`, `glm.vec2`, `glm.vec3`, `glm.vec4` |
| Swizzles | `.x`, `.y`, `.z`, `.w` on vectors |

**Not supported (do not use in shaders):** `for`, `try`, classes, nested `def`, arbitrary Python calls, `min` (not shipped), `sign`, `pow`, `smoothstep`, most of the **Planned** table in `source/ttsl.md`.

### Pitfalls (common author mistakes)

| Looks valid | Actually |
|-------------|----------|
| `cos`, `tan` (bare or `glm.cos`) | Often **type-check** but **`opcode_for_uniop` has no `cos`** — use **`sin`** / phase tricks or implement cos in the same change |
| `min` | **Not shipped** — use `max` on negated values or compare via `if` |
| `mix(a,b,t)` without `glm.` | **Not wired** — use **`glm.mix`** |
| `tt_texelFetch` | **Not end-to-end** |
| Name in `ttsl.md` **Planned** | Verify compile + test before relying on it |
| `globals_dict` with `tt_FragCoord` | Wrong layer—per-cell builtins are implicit |
| Expect alpha compositing after return | **Must** zero/mask colors in shader |
| `ttsl_run` for textured effects | No texture buffer—use engine path or tests that bind textures |

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

4. **Smoke-test** when logic is non-trivial:

```python
from tt3de.tt3de import ttsl_run
from tt3de.ttsl.compiler import PIXELVAR_TT_TEXCOORD0

reg_settings.set_variable(GLOBAL_VAR_TT_TIME, 1.0)
reg_settings.set_variable(PIXELVAR_TT_TEXCOORD0, glm.vec2(0.5, 0.5))
front, back, glyph = ttsl_run(*reg_settings.get_register_list(), bytecode)
```

5. **Integrate** into a demo/app: `materials.ShaderPy(..., register_seed=reg_settings.get_register_list())`, material slot 0 static sentinel, `set_shader_time` in `before_render_step`—see [demos-standards](../../../.cursor/rules/demos-standards.mdc) and `demos/2d/ttsl_square.py`.

6. **Mirror** non-obvious behavior in `tests/tt3de/ttsl/test_e2e.py` when fixing a regression.

Do **not** jump to `low_level_def.py` or opcode work when the user only asked for a shader effect solvable with the shipped surface.

## Compiler and bytecode (when extending the language)

**Pipeline entry:** `all_passes_compilation(src, func_name, globals_dict)` in `python/tt3de/ttsl/compiler.py`.

**ISA changes:** edit `python/tt3de/ttsl/ttisa/low_level_def.py`, then `make gen-opcodes` or `bash scripts/gen_opcodes.sh` (PowerShell on Windows). Regenerates Rust opcodes, Python tables, and `source/opcode_reference.md`.

### Generated vs manual

- **`src/ttsl/opcodes.rs` is fully auto-generated** — never hand-edit.
- **`PassToByteCode.find_form`** matches unary/binary same-type ops generically; unusual layouts (`TT_TEXTURE`, `MIX`, `CLAMP`) need explicit `emit` paths in `compiler.py`.
- Opcode indices are **sequential** across `generate_all_forms()` — always regenerate after ISA edits; never hand-edit `ttisa_opcodes.py`.

### Adding a new operation (summary)

Pick a pattern by shape; full file-level steps apply when implementing:

| Pattern | Examples | Main touch points |
|---------|----------|-------------------|
| **A — Unary same-type** | `sin`, `floor`, `abs` | `ttsl_assembly.py`, `low_level_def.py`, `compiler.py` (`NATIVE_UNI_OPS_TYPE`, bare/`glm` lists, `opcode_for_uniop`), gen-opcodes |
| **B — Binary same-type** | `mod`, `max` | Same + custom `Form` generator if not a Rust operator |
| **C — Special** | `tt_texture`, `glm.mix` | Custom `Form` + `compile_expr` / `compile_glm_tool_call`; confirm Rust bridge with user if data leaves VM registers |

After implementation: `bash scripts/gen_opcodes.sh && cargo check --all-targets && uv run maturin develop`, e2e tests in `tests/tt3de/ttsl/test_e2e.py`, compiler errors in `test_compiler.py`, update **`source/ttsl.md`** row **Planned → Shipped**.

**Rust VM tests** (`src/ttsl/mod.rs`) only for engine-coupled ops; pure math is covered by Python e2e.

Run: `PYTHONPATH=. uv run pytest tests/tt3de/ttsl/ -v` (skip `tests/benchs/` unless needed).

## Verification checklist

**Shader-only change**

- [ ] Uses only shipped calls (see **Language surface** / **Pitfalls**)
- [ ] Correct `globals_dict` (types only; per-cell builtins omitted)
- [ ] Returns `(vec4, vec4, int)`; transparency handled in-shader if needed
- [ ] `all_passes_compilation` succeeds; `ttsl_run` or demo path exercised when non-trivial

**Compiler / opcode change**

- [ ] `gen-opcodes` run; no hand-edited `opcodes.rs` / `ttisa_opcodes.py`
- [ ] `cargo check --all-targets` clean; `uv run pytest tests/tt3de/ttsl/`
- [ ] `source/ttsl.md` (+ opcode reference via generator) updated
