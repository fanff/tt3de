# Evolution: Shader math primitives — dot, normalize, length, max, clamp

```yaml
id: evol-shader-math-normal
status: draft
created: 2026-05-14
authors: []
supersedes: []
superseded-by: ""
related:
  - .evolution/evol-lighting.md                 # Consumer: needs these primitives for the reference shader
  - source/ttsl.md                               # Primitive table — all five are "Planned"
  - source/ttsl_compiler.md                      # Compiler pipeline and extension guide
  - source/opcode_reference.md                   # Generated opcode listing (none of these exist yet)
```

## Summary

Add five vector/scalar math primitives to the TTSL language and VM: **`dot`**, **`normalize`**, **`length`**, **`max`**, and **`clamp`**. These are the minimum set needed for basic Lambertian lighting (the reference shader in `evol-lighting.md`), and they are common GLSL built-ins that every shading language provides. Each primitive is added end-to-end: compiler front-end (type inference + code emission), opcode forms (VM execution), and tests.

## Motivation and context

**Current state** — TTSL ships basic component-wise unary ops (`sin`, `abs`, `floor`, `ceil`, `fract`), binary arithmetic (`+`, `-`, `*`, `/`), and the binary `mod` operator. What it lacks are the **cross-type** and **ternary** operations that shaders need for geometry and lighting math:

| Operation | What it does | Why it's missing from component-wise ops |
|-----------|-------------|------------------------------------------|
| `dot(a, b)` | Scalar result from two vectors | Cross-type: `vecN × vecN → f32`. Not component-wise — returns a single float |
| `normalize(v)` | Unit-length vector | Not component-wise: needs length computation + division of all components |
| `length(v)` | Vector magnitude | Cross-type: `vecN → f32`. Not component-wise |
| `max(a, b)` | Component-wise maximum | Binary same-type, but needs a Rust free function (`f32::max`, `nalgebra_glm::max`) rather than an operator |
| `clamp(x, lo, hi)` | Clamp value into range | Ternary (3 operands): `T × T × T → T`. No existing ternary opcode infrastructure except `MIX` |

**What they enable**:

- **`dot`** — Lambert diffuse lighting, half-vector for specular, projection tests
- **`normalize`** — Unit-length normals and light/view direction vectors for correct dot products
- **`length`** — Point-light distance attenuation, distance-based effects (fog, falloff)
- **`max`** — Clamp dot product to `[0, ∞)` for diffuse, general bounds
- **`clamp`** — Final color clamping to `[0, 1]`, general range restriction

Without these, the lighting evolution's reference shader cannot compile. These are the **shipping dependency** for `evol-lighting.md`.

**Partial infrastructure that already exists**:

| Primitive | Existing partial work |
|-----------|----------------------|
| `dot` | Type signatures defined in `GLM_TOOLS` (compiler.py:109-112) — but `compile_glm_tool_call` only handles `mix`; everything else raises `CompileError` |
| `normalize` | `"norm"` listed in `NATIVE_UNI_OPS_TYPE` (compiler.py:91) for V2/V3/V4 — but no opcode mapping in `opcode_for_uniop`, no codegen path for bare calls |
| `length` | No infrastructure |
| `max` / `clamp` | Listed as "Planned" in `ttsl.md` primitives table — no compiler or VM work |

## Goals

- **5 opcode families** in the VM: `DOT_*`, `NORMALIZE_*`, `LENGTH_*`, `MAX_*`, `CLAMP_*` — each supporting the relevant type variants (V2, V3, V4; plus F32 for `max` and `clamp`)
- **Compiler front-end**: Both bare-call spelling (`dot(a, b)`) and `glm.` spelling (`glm.dot(a, b)`) working for all five
- **Type inference**: Correct return types — `f32` for `dot` and `length`, same type as input for `normalize`/`max`/`clamp`
- **VM execution**: Rust implementations using nalgebra_glm free functions where available, component-wise expansion otherwise
- **Tests**: E2E tests (compile + `ttsl_run`) for every primitive across supported types, including edge cases (zero-length vectors for `normalize`, negative values for `max`, invalid ranges for `clamp`)

## Non-goals

- **`min`**: Not needed for the lighting reference shader. Can be added in a follow-up if needed (mirroring the `max` pattern).
- **`cross`**: Already in `GLM_TOOLS` but not handled. Useful but not required for lighting.
- **`distance`**: Can be expressed as `length(a - b)`. Deferred.
- **Component-wise `max`/`clamp` for `int`/`bool` types**: Not needed for shader math. F32, V2, V3, V4 only.
- **Optimized SIMD paths**: The nalgebra_glm scalar fallthrough is sufficient for terminal-resolution pixel counts (~12K cells).
- **Compiler error messages for wrong types**: The existing `GLM_TOOLS` type validation is reused; no bespoke error messages.

## User-visible functionality

### TTSL source spellings

All five primitives accept **both bare-call** and `glm.` spellings:

```python
# --- dot: vecN × vecN → float ---
d: float = dot(n, light_dir)
d: float = glm.dot(n, light_dir)

# --- normalize: vecN → vecN ---
n: vec3 = normalize(tt_Normal)
n: vec3 = glm.normalize(tt_Normal)

# --- length: vecN → float ---
dist: float = length(to_light)
dist: float = glm.length(to_light)

# --- max: T × T → T (T = float, vec2, vec3, vec4) ---
diff: float = max(dot_nl, 0.0)
v_max: vec3 = max(vec3(0.0), vec3(1.0))
diff: float = glm.max(dot_nl, 0.0)

# --- clamp: T × T × T → T (T = float, vec2, vec3, vec4) ---
result: vec3 = clamp(color, vec3(0.0, 0.0, 0.0), vec3(1.0, 1.0, 1.0))
result: vec3 = glm.clamp(color, vec3(0.0), vec3(1.0))
```

### Type support matrix

| Primitive | F32 | V2 | V3 | V4 | Return type |
|-----------|-----|----|----|----|-------------|
| `dot(a, b)` | — | ✓ | ✓ | ✓ | `float` |
| `normalize(v)` | — | ✓ | ✓ | ✓ | same as input |
| `length(v)` | — | ✓ | ✓ | ✓ | `float` |
| `max(a, b)` | ✓ | ✓ | ✓ | ✓ | same as inputs |
| `clamp(x, lo, hi)` | ✓ | ✓ | ✓ | ✓ | same as inputs |

### Breaking changes

None. These are additive built-in functions. Existing shaders that do not reference these names are unaffected. The only risk is a name collision if a user already declared a user uniform named `dot` or `max` in `globals_dict` — but `globals_dict` entries take precedence over built-ins, so existing code continues to work (the user uniform shadows the built-in).

## Technical approach

### Phase 1: Opcode forms (low_level_def.py)

#### `DOT_*` (vecN × vecN → f32)

Custom form generator `generate_dot_forms()` producing one form per vector type (V2, V3, V4):

```python
# Rust match code per form:
# input_types = [ir_type, ir_type], output_type = F32
# DOT_V3 => {
#     unsafe {
#         let base_v3 = regs.v3.as_mut_ptr();
#         let base_f32 = regs.f32.as_mut_ptr();
#         let a_val = *base_v3.add(a as usize);
#         let b_val = *base_v3.add(b as usize);
#         *base_f32.add(dst as usize) = nalgebra_glm::dot(&a_val, &b_val);
#     }
#     None
# }
```

#### `NORMALIZE_*` (vecN → vecN)

Unary form for vectors only. The `"norm"` entry already exists in `NATIVE_UNI_OPS_TYPE`. Add to the "Unary Math" `CategoryGroup` in `generate_all_forms()`:

```python
# rust_expr: "nalgebra_glm::normalize(&{a})"
# Same form structure as SIN_V2, SIN_V3, etc., using the nalgebra_glm free function.
```

Add `"norm"` to `opcode_for_uniop` in the compiler, mapping to `OpCodes.NORM` (or a new opcode name like `NORMALIZE`).

#### `LENGTH_*` (vecN → f32)

Custom form generator `generate_length_forms()` — same cross-type pattern as `DOT_*`:

```python
# input_types = [ir_type], output_type = F32
# LENGTH_V3 => {
#     unsafe {
#         let base_v3 = regs.v3.as_mut_ptr();
#         let base_f32 = regs.f32.as_mut_ptr();
#         let a_val = *base_v3.add(a as usize);
#         *base_f32.add(dst as usize) = nalgebra_glm::length(&a_val);
#     }
#     None
# }
```

#### `MAX_*` (T × T → T)

Binary same-type form for F32, V2, V3, V4. Follow the `mod` pattern (`generate_binary_unitype_forms` or a custom generator):

```python
# For F32: "{a}.max({b})"  (Rust f32 method)
# For V2/V3/V4: "nalgebra_glm::max(&{a}, &{b})"
```

Since `max` is not a Rust operator, a custom generator (like `generate_mod_forms()`) is needed rather than adding to `generate_binary_unitype_forms` (which uses operators).

#### `CLAMP_*` (T × T × T → T)

Ternary same-type form for F32, V2, V3, V4. Follow the `MIX` pattern:

```python
# For F32:
#     "{a}.clamp({b}, {c})"  (Rust f32::clamp)
# For V2/V3/V4:
#     "nalgebra_glm::clamp(&{a}, &{b}, &{c})"
```

The Rust VM code uses `emit_2` with 3 source operands (same layout as `MIX`). The `find_form` generic matcher will match the 3-input type tuple against `(output_type, input_type, input_type, input_type)`.

### Phase 2: Compiler support

#### `compile_expr` bare-call path

Add `elif` branches for each primitive in `compile_expr` (around line 447):

```python
# dot(a, b) — validate 2 args, same type, vector only
elif func.id == "dot":
    # type checking
    # emit DOT_* opcode  (cross-type: dst in f32 bank)

# normalize(v) — validate 1 arg, vector only
elif func.id == "normalize":
    # handled by existing NATIVE_UNI_OPS_TYPE + opcode_for_uniop

# length(v) — validate 1 arg, vector only
elif func.id == "length":
    # type checking
    # emit LENGTH_* opcode  (cross-type: dst in f32 bank)

# max(a, b) — validate 2 args, same type
elif func.id == "max":
    # type checking, same-type validation
    # emit MAX_* opcode

# clamp(x, lo, hi) — validate 3 args, all same type
elif func.id == "clamp":
    # type checking
    # emit CLAMP_* opcode (3 source operands like MIX)
```

#### `compile_expr` glm-attribute path

The existing `glm` path at line 524 checks `func_name in NATIVE_UNI_OPS_TYPE` and dispatches to `opcode_for_uniop`. For `normalize`, adding `"norm"` to `opcode_for_uniop` makes `glm.normalize(v)` work automatically.

For `glm.dot`, `glm.length`, `glm.max`, `glm.clamp` — these need dedicated branches in the `glm` path (like the existing `glm.mod` branch at line 537).

#### `type_of` additions

All five need entries in `type_of` for bare-call `ast.Name` and `ast.Attribute` nodes:

- `dot` → `IRType.F32` regardless of argument types
- `normalize` → same as argument type
- `length` → `IRType.F32`
- `max` → same as argument types (after validating 2 args of same type)
- `clamp` → same as argument types (after validating 3 args of same type)

For `dot`, `length`, `max`, and `clamp`, `type_of` must accept them even though they don't go through `opcode_for_uniop`. The `dot` case is already partially handled since it's in `GLM_TOOLS`, but `type_of` for bare calls needs explicit handling.

#### `opcode_for_uniop` additions

Add `"norm"` mapping to `OpCodes.NORM` (and wire `NORM` to `NORMALIZE` in the opcode enum — the name `norm` is shorter for the compiler but the opcode should be clearly named `NORMALIZE_*`).

### Phase 3: Rust VM — opcode code generation

All five primitives use nalgebra_glm functions, so the `RUST_OPCODE_FILE_PRELUDE` needs these imports added:

```python
# Already imported (check existing):
use nalgebra_glm::{...existing...};
# Add:
# nalgebra_glm::dot, nalgebra_glm::normalize, nalgebra_glm::length,
# nalgebra_glm::max, nalgebra_glm::clamp
```

For `NORMALIZE` on V2/V3/V4, the `MATH_FUNCTION_NATIVE_TYPES` and `MATH_FUNCTION_VEC_TYPES` pattern already supports adding new unary functions through the standard codegen. Add the opcode name `OpCodes.NORM` to `MATH_FUNCTION_VEC_TYPES` as `"normalize(&{a})"` (no F32 variant since normalizing a scalar makes no sense).

For `MAX` on F32, use `f32::max({a}, {b})`. For vectors, `nalgebra_glm::max(&{a}, &{b})`.

For `CLAMP` on F32, use `{a}.clamp({b}, {c})`. For vectors, `nalgebra_glm::clamp(&{a}, &{b}, &{c})`.

### Phase 4: E2E tests

Each primitive gets at least:

1. **Happy path**: Compile + `ttsl_run` with constant inputs. Assert numeric output matches expected value.
2. **Runtime inputs**: Same computation with variables instead of literals.
3. **Edge cases**: Zero-length vector for `normalize`, negative values in `max`, tight ranges in `clamp`.
4. **GLM spelling**: Same tests using `glm.dot(...)`, `glm.normalize(...)`, etc.

Example test structure (from `tests/tt3de/ttsl/test_e2e.py`):

```python
def test_dot_v3(self):
    src = """
def shader() -> tuple[vec4, vec4, int]:
    a: vec3 = vec3(1.0, 0.0, 0.0)
    b: vec3 = vec3(0.0, 1.0, 0.0)
    d: float = dot(a, b)  # should be 0.0
    return (vec4(d, 0.0, 0.0, 1.0), vec4(0.0), 0)
"""
    bytecode, regs = all_passes_compilation(src, "shader", {})
    front, back, glyph = ttsl_run(*regs.get_register_list(), bytecode)
    assert front.x == pytest.approx(0.0)
```

### Alternatives considered

- **Decompose `clamp` into `max(lo, min(x, hi))`**: Rejected — two opcodes per call instead of one, harder to debug, and the VM already has ternary opcode support (`MIX`).
- **Decompose `normalize` into `v / length(v)`**: Rejected — `length` is also missing, and this would require two opcodes + a division per normalization.
- **Component-wise expansion in the compiler instead of VM**: Rejected — the compiler would emit multiple instructions for what should be one VM operation, bloating bytecode and register pressure.
- **Add `min` alongside `max`**: Deferred — not needed for the lighting reference shader. Follow-up evolution if needed.

### Files likely touched

- `python/tt3de/ttsl/ttsl_assembly.py` — new `OpCodes` entries (`DOT`, `NORMALIZE`, `LENGTH`, `MAX`, `CLAMP`)
- `python/tt3de/ttsl/ttisa/low_level_def.py` — form generators for all 5 opcode families; add to `generate_all_forms()`; update `RUST_OPCODE_FILE_PRELUDE` imports
- `python/tt3de/ttsl/compiler.py` — `type_of` additions, `compile_expr` bare-call branches for all 5, `glm`-attribute branches for `dot`/`length`/`max`/`clamp`, `opcode_for_uniop` addition for `norm`
- `src/ttsl/opcodes.rs` — auto-generated (regenerate after low_level_def.py changes)
- `python/tt3de/ttsl/ttisa/ttisa_opcodes.py` — auto-generated
- `source/opcode_reference.md` — auto-generated
- `source/ttsl.md` — change `dot`, `normalize`, `length`, `min / max`, `clamp` from **Planned** to **Shipped** in the primitives table
- `tests/tt3de/ttsl/test_e2e.py` — e2e tests for all 5 primitives across supported types

### Implementation order

1. Opcode forms in `low_level_def.py` + regenerate (`make gen-opcodes`)
2. Python compiler built-in registration (`compiler.py` changes)
3. `cargo check --all-targets` (verify Rust VM code compiles)
4. E2E tests (compile + `ttsl_run`)
5. Update `source/ttsl.md` primitives table

## Usability and documentation

- **`source/ttsl.md`**: Change 5 primitives table rows from **Planned** → **Shipped** with "Bare and `glm.` spelling; works on V2/V3/V4 (and F32 for `max`/`clamp`)"
- **Compiler error messages**: Type mismatches (e.g., `dot(a: vec3, b: vec2)`) produce existing `CompileError` messages. No new error messages needed.
- **Zero-length `normalize`**: Document that `normalize(zero_vec)` returns a zero vector (matching nalgebra_glm behavior). Users should guard against this in shaders if needed.

## Testability

Each primitive has Rust-side unit tests (opcode execution) and Python e2e tests (full compile + run):

### Rust tests (`#[cfg(test)]` in `src/ttsl/mod.rs`)

- Direct opcode dispatch test for each type variant: set up registers, execute the opcode, read result
- `DOT`: orthogonal vectors → 0, parallel → product of lengths, one zero vector → 0
- `NORMALIZE`: unit vector unchanged, non-unit vector → unit length, zero vector → zero (defined behavior)
- `LENGTH`: unit vector → 1, zero vector → 0, arbitrary → √(x²+y²+…)
- `MAX`: same value unchanged, negative vs positive → positive, vector component-wise
- `CLAMP`: within range unchanged, below lo → lo, above hi → hi, vector component-wise

### Python e2e tests (`tests/tt3de/ttsl/test_e2e.py`)

- All happy paths with constant inputs
- All happy paths with runtime variable inputs
- All `glm.` spellings
- `clamp` with inverted range (`lo > hi`) — defined behavior: returns `max(lo, min(x, hi))` from nalgebra_glm
- `normalize` of a zero vector — returns zero vector (defined)
- `dot` with mismatched types — should raise `CompileError`
- `max` with mismatched types — should raise `CompileError`

### Regression

- All existing e2e tests pass (no behavior change for existing shaders)
- Existing unit tests for existing unary ops still pass (no opcode renumbering — new opcodes are appended)

## Complexity and scope

| Phase | Size | Risk | Ships independently? |
|-------|------|------|---------------------|
| Phase 1: Opcode forms | S | Low — follows existing MIX/MOD patterns | Yes (opcodes are inert without compiler) |
| Phase 2: Compiler support | M | Medium — 5 new builtins, 3 different patterns (unary, binary, ternary, cross-type) | Requires Phase 1 |
| Phase 3: Rust VM codegen | S | Low — all use nalgebra_glm, auto-generated via low_level_def.py | Part of Phase 1 |
| Phase 4: E2E tests | S | Low — pure Python, exercises full pipeline | Requires all above |

**Dependency**: This evolution is the **shipping prerequisite** for `evol-lighting.md`. The lighting reference shader cannot compile without these five primitives.

**Rollback**: Fully additive. Remove the opcode forms + compiler branches and existing shaders are unaffected. Opcode indices shift on regenerate but there's no bytecode persistence.

## A priori performance analysis

**Hot paths** — All five primitives are called per-pixel in the lighting reference shader:

| Primitive | Calls per pixel (lighting shader, 3 lights) | Cost |
|-----------|---------------------------------------------|------|
| `normalize` | 2 (once for N, once per-light direction) | ~1 nalgebra_glm `length` + 3 divisions |
| `dot` | 2 per light = 6 (diffuse for directional + point × 3 lights) | 3 mul + 2 add |
| `length` | 1 per point light = 1 | 3 mul + 2 add + 1 sqrt |
| `max` | 1 per diffuse light = 2 | 1 compare + 1 select |
| `clamp` | 1 (final color clamp) | 2 compares + 2 selects |

**Total per-pixel cost**: ~12 math ops + 3 sqrt calls (roughly equivalent to a handful of existing `sin` evaluations). At 12K cells, this is sub-100μs.

**VM dispatch**: 12 extra opcode dispatches per pixel (vs the current non-lighting shader path). Each is a match arm + register reads/write. Negligible.

**Relative cost ranking** (cheapest → expensive):

1. `max` — single compare + select
2. `dot` — a few multiply-adds
3. `clamp` — two compares
4. `length` — dot + sqrt
5. `normalize` — length + reciprocal + 3 multiplies

**Validation**: Include a benchmark test (`tests/benchs/r_code/`) that times a shader using all 5 primitives vs an arithmetic-only baseline.

## Risks and open questions

- **Opcode enumeration naming**: `NORM` vs `NORMALIZE` — the compiler's `NATIVE_UNI_OPS_TYPE` uses `"norm"` as the key. The opcode and Rust match arm should use the descriptive `NORMALIZE_V2`/`NORMALIZE_V3`/`NORMALIZE_V4` name (consistent with `SIN_V2`, `FLOOR_V3`, etc.). The `opcode_for_uniop` mapping bridges the short key `"norm"` → opcode `OpCodes.NORMALIZE`.
- **Zero-vector `normalize`**: nalgebra_glm divides by zero for a zero-length vector, producing NaN or inf. The evolution should decide: (a) match nalgebra_glm behavior (NaN), (b) guard with `if length == 0 { return zero }`. Option (b) is safer for shaders. If the VM guard adds branch overhead, document the trade-off. **Decision**: guard in the Rust VM: `if length_squared == 0.0 { return Vec3::zeros() }`. This matches GLSL `normalize` behavior for zero vectors (undefined, but engines typically return zero).
- **`dot` on mismatched types**: The compiler raises `CompileError` (existing `GLM_TOOLS` validation).
- **`clamp` with inverted lo/hi**: nalgebra_glm's `clamp` clamps to `[lo, hi]` regardless of order (it uses `max(lo, min(x, hi))` internally). This matches GLSL behavior. No special handling needed.
- **Type inference for `dot` and `length`**: These return `F32` even when inputs are vectors. The existing type inference in `type_of` needs new branches (no existing opcode returns a different type than its input). Risk: a typo in `type_of` could produce type mismatches downstream. Mitigate with e2e tests that exercise the full compile+run path.

## Decision record

- **Status**: draft
- **Five primitives**: `dot`, `normalize`, `length`, `max`, `clamp` — the minimum set for the lighting reference shader.
- **Both spellings**: Bare-call and `glm.` prefix for all five.
- **Type coverage**: V2/V3/V4 for all five; F32 for `max` and `clamp` only (dot/length/normalize on scalars are meaningless).
- **Zero-vector normalize**: Returns zero vector (guarded in Rust VM, not NaN).
- **Opcode generation**: Three distinct patterns — unary (normalize), binary cross-type (dot, length), binary same-type (max), ternary same-type (clamp). Each maps cleanly to nalgebra_glm functions.
- **`min` deferred**: Not required for lighting. Can mirror `max` in a follow-up.
- **Resolution**: *(to be filled when closing)*

## References

- `.evolution/evol-lighting.md` — Consumer evolution: lighting reference shader depends on these primitives
- `source/ttsl.md` — Primitive table (all five currently **Planned**)
- `source/ttsl_compiler.md` — Compiler extension guide
- `source/opcode_reference.md` — Auto-generated opcode listing
- `python/tt3de/ttsl/compiler.py` — `NATIVE_UNI_OPS_TYPE` (line 82), `GLM_TOOLS` (line 94), `opcode_for_uniop` (line 1044), `compile_glm_tool_call` (line 665), bare-call dispatch (line 447), glm-path dispatch (line 515)
- `python/tt3de/ttsl/ttisa/low_level_def.py` — Form generators: `generate_glm_tool_mix_forms` (line 584), `generate_mod_forms` (reference for binary same-type), `MATH_FUNCTION_VEC_TYPES` (unary codegen)
- `python/tt3de/ttsl/ttsl_assembly.py` — `OpCodes` enum
- `tests/tt3de/ttsl/test_e2e.py` — Existing e2e test patterns
