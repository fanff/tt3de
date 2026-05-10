---
name: ttsl-implementation
description: Implements or changes Tiny Tiny Shader Language (TTSL) shaders, compiler, VM opcodes, or TTSL-related docs in tt3de. Use when writing TTSL source, editing python/tt3de/ttsl/, Rust TTSL VM/material paths, or when the user mentions TTSL, shader materials, bytecode, builtins (tt_FragCoord, tt_Time), or all_passes_compilation.
disable-model-invocation: true
---

# TTSL implementation

## Documentation map

Read these before changing behavior; they are the contract:

| Topic | File |
|-------|------|
| Builtins, uniforms, texture ABI, material bridge | [source/ttsl.md](../../../source/ttsl.md) |
| Compiler API, `globals_dict`, supported syntax | [source/ttsl_compiler.md](../../../source/ttsl_compiler.md) |
| Opcode numbers and operand types (generated) | [source/opcode_reference.md](../../../source/opcode_reference.md) |

## Authoring shader source

- **Return type**: `(front, back, glyph)` as `(vec3, vec3, int)`, matching VM `OP_RET`. Annotate `tuple[vec3, vec3, int]` (or `typing.Tuple[...]`) when typing the entry function.
- **Per-cell builtins** (`tt_FragCoord`, `tt_FragPos`, `tt_TexCoord0`, `tt_TexCoord1`, `tt_FrontFacing`, `tt_PrimitiveID`): known to the compiler; see `ttsl_compiler.md` for parameter declarations vs implicit slots.
- **Engine uniforms** (`tt_Time`, `tt_DeltaTime`, `tt_Frame`, `tt_Resolution`): include in `globals_dict` with the types documented in `ttsl.md` / `ttsl_compiler.md`; wire runtime setters and `ShaderPy.*_reg` to match `RegisterSettings` after `all_passes_compilation`.
- **Naming**: `tt_` + CamelCase, analogous to GLSL `gl_`.
- **Sampling**: only `tt_texture(index: int, coord: vec2) -> vec4` (and `tt_texelFetch` when implemented end-to-end—confirm opcode + compiler + tests). Use `tt_TexCoord*` for interpolated coords. Standalone Python `ttsl_run` does not bind textures; expect black or engine-defined fallback unless exercising through `Shader` + `TextureBuffer`.
- **Python next to shaders**: `from pyglm import glm` (same prelude convention as AGENTS.md).

## Compiler and bytecode

- **Pipeline entry**: `all_passes_compilation(src, func_name, globals_dict)` in `python/tt3de/ttsl/compiler.py`.
- **ISA / opcode definition changes**: edit `python/tt3de/ttsl/ttisa/low_level_def.py`, then run `make gen-opcodes` or `bash scripts/gen_opcodes.sh` (PowerShell script on Windows). That refreshes Rust opcodes, Python opcode tables, and `source/opcode_reference.md`.
- **Lowering gaps**: consult `source/ttsl_compiler.md` (supported features, typability in `type_of`, notes like partially wired helpers). Do not assume a name in `ttsl.md` primitives table compiles until verified in the compiler and tests.

## Key architecture: what is generated vs manual

**`src/ttsl/opcodes.rs` is fully auto-generated** by `low_level_def.py` via `gen-opcodes`. Never hand-edit it. The generator builds the entire Rust `exec_opcode` match block from Python `Form` definitions, including `unsafe` register access. For standard math operations the Rust VM implementation requires zero manual Rust coding.

**`PassToByteCode.find_form` is generic.** It matches IR instructions to bytecode forms by checking `instr.op.name in form["name"]` (substring) and comparing type tuples. New opcodes that follow existing patterns (unary same-type, binary same-type) need **no back-end changes** — the generic matcher handles them automatically.

**Opcode index assignment is sequential** across all `CategoryGroup`s in `generate_all_forms()`. Adding forms anywhere shifts downstream indices. Always regenerate after ISA edits; never hand-edit `ttisa_opcodes.py` or `opcodes.rs`.

## Adding a new builtin (end-to-end)

Determine the **shape** of the new builtin first — this determines which pattern to follow:

### Pattern A: Unary math (like `sin`, `abs`, `floor`, `ceil`, `fract`)

Signature: `func(x) -> T` where input and output share the same type (F32, V2, V3, V4).

**Files to edit (in order):**

1. **`python/tt3de/ttsl/ttsl_assembly.py`** — Add `MYOP = "myop"` to the `OpCodes` enum.

2. **`python/tt3de/ttsl/ttisa/low_level_def.py`** — Three changes:
   - Add `OpCodes.MYOP` to both `MATH_FUNCTION_NATIVE_TYPES` (F32 method syntax: `"{a}.myop()"`) and `MATH_FUNCTION_VEC_TYPES` (nalgebra_glm free function: `"myop(&{a})"`).
   - Add `OpCodes.MYOP` to the unary ops list inside the `"Unary Math"` `CategoryGroup` in `generate_all_forms()`.
   - Add the nalgebra_glm symbol to the `use nalgebra_glm::{...}` line in `RUST_OPCODE_FILE_PRELUDE` inside `main()`.

3. **`python/tt3de/ttsl/compiler.py`** — Five touch points:
   - `NATIVE_UNI_OPS_TYPE` dict — add `"myop": (IRType.F32, IRType.V2, IRType.V3, IRType.V4)`.
   - `compile_expr` bare-call list — add `"myop"` to the `func.id in ("sin", "abs", "cos", ...)` tuple (around line 444). The `glm.myop(...)` path is handled automatically by the existing `NATIVE_UNI_OPS_TYPE` check.
   - `type_of` for `ast.Name` — add `"myop"` to the `node.id in ("abs", "sin", "cos", ...)` tuple.
   - `type_of` for `ast.Attribute` — add `"myop"` to the `node.attr in ("sin", "cos", ...)` tuple.
   - `opcode_for_uniop` — add `"myop": OpCodes.MYOP` to the `name_to_op` dict.

4. **Regenerate and rebuild** — `bash scripts/gen_opcodes.sh && cargo check --all-targets && uv run maturin develop`.

5. **Tests** — Add e2e tests in `tests/tt3de/ttsl/test_e2e.py` using `all_passes_compilation` + `ttsl_run`. Cover: constant input, negative/edge cases, runtime variable input, and `glm.myop(...)` spelling. The `all_passes_compilation` + `ttsl_run` pattern exercises the full pipeline (front end → IR → SSA → bytecode → VM) in one test.

6. **Documentation** — Update the primitives table in `source/ttsl.md`: change row from **Planned** to **Shipped** with notes on supported spellings.

### Pattern B: Binary same-type math (like `mod`)

Signature: `func(x, y) -> T` where both inputs and output share the same type.

If the operation maps to a simple Rust operator (`+`, `-`, `*`, `/`), add it to `generate_binary_unitype_forms`. Otherwise, write a **custom form generator** (see `generate_mod_forms()` for the pattern — it builds `Form` dicts with hand-written `rust_match_code` per type).

**Files to edit:**

1. **`python/tt3de/ttsl/ttsl_assembly.py`** — Add `MYOP = "myop"` to `OpCodes`.

2. **`python/tt3de/ttsl/ttisa/low_level_def.py`** — Write a generator function (or extend an existing one) that produces `Form` dicts for each type variant. Add a `CategoryGroup` to `generate_all_forms()`. For vector variants that need component-wise expansion (no nalgebra_glm free function), generate explicit `VecN::new(a.x op b.x, a.y op b.y, ...)` Rust code. Update `RUST_OPCODE_FILE_PRELUDE` imports if needed.

3. **`python/tt3de/ttsl/compiler.py`** — Handle both bare `myop(x, y)` and `glm.myop(x, y)`:
   - `compile_expr` bare call: add an `elif func.id == "myop"` block that validates 2 args, checks same type, compiles both, and calls `self.emit_2(OpCodes.MYOP, ...)`.
   - `compile_expr` glm attribute: add `elif func_name == "myop"` in the `glm` branch with the same logic.
   - `type_of` for `ast.Name`: add `elif node.id == "myop"` returning `type_args[0]` after validating 2 same-type args.
   - `type_of` for `ast.Attribute`: add `elif node.attr == "myop"` with same validation.

4. **Regenerate, rebuild, test, document** — same as Pattern A steps 4–6.

### Pattern C: Special / cross-type operations (like `tt_texture`, `mix`)

Operations with mixed input types, engine hooks (texture buffer, etc.), or non-register data need custom handling. See `generate_tt_texture_form()` and `generate_glm_tool_mix_forms()` for examples. **Before coding, confirm with the user** the intended strategy when execution needs data beyond VM registers.

## Rust expression patterns in `low_level_def.py`

| Type | Unary template style | Binary template style |
|------|---------------------|----------------------|
| F32 | `"{a}.sin()"` (method on `f32`) | `"{a} + {b}"` (Rust operator) |
| V2/V3/V4 | `"sin(&{a})"` (nalgebra_glm free fn) | `"{a} + {b}"` (nalgebra operator overload) |

For operations without a nalgebra_glm free function on vectors, use component-wise expansion: `VecN::new(a_val.x.op(), a_val.y.op(), ...)` — see `_mod_rust_body_vec` for the pattern.

## Back end: why no changes are usually needed

`PassToByteCode.find_form` matches IR instructions to bytecode forms generically:
- It iterates all forms from `generate_all_forms()`.
- For non-control-flow ops, it checks `instr.op.name in form["name"]` (e.g. `"FLOOR"` is in `"FLOOR_F32"`).
- It then compares the full type tuple `(dst_ty, src1_ty, ...)` against `(form output_type, form input_types)`.
- `transform_instr_to_bytecode` encodes each instruction as `[opcode_index, dst_reg, a_reg, b_reg, c_reg, d_reg]`.

New opcodes that follow the unary (`emit_1`) or binary (`emit_2`) pattern are matched automatically. You only need to touch `PassToByteCode` for operations with unusual operand layouts (e.g. `TT_TEXTURE` uses `emit(...)` with explicit 4 sources, `MIX` uses 3 sources across different type banks).

## Tests and doc updates

- **E2E tests** in `tests/tt3de/ttsl/test_e2e.py` are the primary validation: compile + `ttsl_run` exercises the entire pipeline. Cover constant inputs, edge cases (negatives, zero), runtime variable inputs, and both bare and `glm.` spellings.
- **Compiler-only tests** in `tests/tt3de/ttsl/test_compiler.py` for error cases (wrong arg count, type mismatches).
- Rust-side tests in `src/ttsl/mod.rs` (`#[cfg(test)]`) are only needed for ops that interact with engine surfaces (textures, etc.); pure math ops are fully exercised by the Python e2e path.
- Run `PYTHONPATH=. uv run pytest tests/tt3de/ -v` to validate (skip `tests/benchs/` which are slow).
- Update `source/ttsl.md` primitives table in the same change: **Planned** → **Shipped** with notes.
