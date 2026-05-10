---
hide-toc: true
---

Tiny Tiny Shader Language (TTSL)
=================================

Built-in variables
------------------

**Implicit inputs (per cell)** — `tt_FragCoord`, `tt_FragPos`, `tt_TexCoord0`, `tt_TexCoord1`, `tt_FrontFacing`, `tt_FragDepth`, `tt_LineCoord`, `tt_PointCoord`, `tt_PrimitiveID` are built into the compiler and filled by the material bridge each shaded cell; they are **not** `globals_dict` keys.

**Engine uniforms** — `tt_Time`, `tt_DeltaTime`, `tt_Frame`, `tt_Resolution`, `tt_Near`, and `tt_Far` are **host uniforms**: for each name the shader references, pass that key in `globals_dict` with the type shown below so compilation allocates the matching register and `ShaderPy` / `MaterialBufferPy` setters stay aligned.

**User-defined uniforms** — Any other global you read in TTSL (for example ``u_color`` as ``glm.vec3``, ``u_uv_bias`` as ``glm.vec2``) must also appear in ``globals_dict`` with the correct **type object**. After ``all_passes_compilation``, call ``RegisterSettings.set_variable(name, value)`` and pass ``register_seed=reg_settings.get_register_list()`` into ``ShaderPy`` so bytecode and the material snapshot use the same register indices. See [TTSL Compiler](ttsl_compiler.md) for a full example and for how this differs from per-frame engine uniform setters.

**Availability** for built-ins is **Shipped** (compiler + material bridge), **Planned** (roadmap intent), or **Missing** (specified below for depth workflows but **not** implemented in the compiler or Rust renderer yet—no registers or setters today).

| Name               | Type  | Range / Units                          | Description | Availability |
|--------------------|-------|----------------------------------------|-------------|--------------|
| tt_FragCoord       | vec2  | x:[0..res.x-1], y:[0..res.y-1]         | Window-space cell coordinate of the current shaded cell. Equivalent to gl_FragCoord.xy (cell-level, integer-like). | Shipped |
| tt_FragPos         | vec2  | [-1..1]                                | Normalized device-space position of the cell center. Equivalent to gl_Position → NDC mapping for fragments. | Shipped |
| tt_Resolution      | vec2  | (width_cells, height_cells)            | Size of the render target in cells. Pass ``'tt_Resolution': glm.vec2`` in ``globals_dict`` when referenced. Compiler seeds ``(1, 1)`` until the host writes via ``register_seed`` / ``ShaderPy.resolution_v2_reg`` or ``MaterialBufferPy.set_shader_resolution``. Non-positive dimensions are clamped to 1 in the Rust setter. On resize, ``tt_FragCoord`` and ``tt_Resolution`` may briefly disagree unless the host refreshes both together. | Shipped |
| tt_PrimitiveID     | int   | [0..N-1]                               | Index of the primitive that generated this cell (depth winner). Mirrors gl_PrimitiveID. | Shipped |
| tt_FrontFacing     | bool  | true / false                           | Front-facing under current winding rules. Mirrors gl_FrontFacing; optional ``ShaderPy.front_facing_bool_reg`` binds the VM bool the runtime fills each pixel. | Shipped |
| tt_TexCoord0       | vec2  | typically [0..1] (convention-defined)  | First interpolated texture coordinate set. Equivalent to a user-defined in vec2 or legacy gl_TexCoord[0]. | Shipped |
| tt_TexCoord1       | vec2  | typically [0..1] (convention-defined)  | Second interpolated texture coordinate set. Equivalent to gl_TexCoord[1] / multi-UV workflows. | Shipped |
| tt_Time            | float | seconds (>= 0)                         | Elapsed engine time. Pass ``'tt_Time': float`` in ``globals_dict`` when referenced; host updates via ``MaterialBufferPy.set_shader_time`` (and ``ShaderPy.time_f32_reg`` from compilation). | Shipped |
| tt_DeltaTime       | float | seconds (>= 0)                         | Frame delta seconds. Pass ``'tt_DeltaTime': float`` when referenced; ``MaterialBufferPy.set_shader_delta_time``. | Shipped |
| tt_Frame           | int   | [0..]                                  | Frame counter. Pass ``'tt_Frame': int`` when referenced. Compiler seeds ``0``; host uses ``MaterialBufferPy.set_shader_frame``; values saturate at ``i32::MAX`` (no wrap). | Shipped |
| tt_FragDepth       | float | engine-defined (depth buffer units)    | Depth value for the shaded depth layer at this cell. Compiler seeds ``0.0``; ``ShaderMaterial`` writes ``ShaderPy.frag_depth_f32_reg`` from that layer each pixel when set (same pattern as ``tt_FrontFacing``). Standalone ``ttsl_run`` keeps the seed unless the host fills the register. | Shipped |
| tt_Near            | float | (> 0), engine clip distance            | **Near clip distance** for the active projection (same units as depth buffering). Pass ``'tt_Near': float`` in ``globals_dict`` when referenced; compiler seeds ``0.1`` until the host writes via ``register_seed`` / ``ShaderPy.near_f32_reg`` or ``MaterialBufferPy.set_shader_near``. Use values consistent with the projection that produces ``tt_FragDepth``. | Shipped |
| tt_Far             | float | (> ``tt_Near``), engine clip distance    | **Far clip distance** for the active projection. Pass ``'tt_Far': float`` when referenced; compiler seeds ``100.0``; ``MaterialBufferPy.set_shader_far`` and ``ShaderPy.far_f32_reg`` mirror ``tt_Near``. Enables portable fog and linear depth without literals when paired with a documented ``tt_FragDepth`` mapping. | Shipped |
| tt_LineCoord       | float | [0..1] along line segments             | Parametric coordinate from the line start toward the end for pixels produced by line rasterization; ``0.0`` for non-line primitives and when not supplied. Compiler seeds ``0.0``; optional ``ShaderPy.line_coord_f32_reg`` matches compilation (same pattern as ``tt_FragDepth``). Hosts may pass an explicit value through ``DrawingBufferPy.set_depth_content(..., line_coord=...)``. | Shipped |
| tt_PointCoord      | vec2  | [0..1] typical                         | Coordinates within a rasterized point sprite. Mirrors ``gl_PointCoord``. Compiler seeds ``(0, 0)``; optional ``ShaderPy.point_coord_v2_reg`` matches compilation. Non-point raster paths and standalone ``ttsl_run`` leave ``(0, 0)`` unless the host sets ``DrawingBufferPy.set_depth_content(..., point_coord=...)``. Point rasterization sets ``(0.5, 0.5)`` for the single-cell path. | Shipped |

### Texture sampling (`tt_texture`, `tt_texelFetch`)

GLSL selects a bound sampler and passes normalized **fragment coordinates** into **`texture`**:

```glsl
vec4 texture(sampler2D sampler, vec2 P);
```

TTSL names kernel operations with the **`tt_`** prefix (same convention as `tt_FragCoord`, `tt_TexCoord0`). There are no separate sampler objects on the surface—you pick a **texture slot** with an integer index, in the same spirit as binding `sampler2D` units on the host. TTSL does not expose **`textureLod`** / explicit mip selection; sampling uses the engine’s single resolved image for that slot.

**Tests** follows the same rule as built-ins: **yes** if pytest under `tests/` exercises the TTSL call or opcode path.

| TTSL (specified) | OpenGL / GLSL analogue | Result | Tests |
|------------------|------------------------|--------|-------|
| `tt_texture(texture_index: int, coord: vec2) -> vec4` | `texture(sampler2D, vec2 P)` | Filtered RGBA sample at **normalized** `coord` (typically \([0,1]^2\); behavior outside the volume is engine-defined: clamp, repeat, or border). | yes |
| `tt_texelFetch(texture_index: int, texel: vec2) -> vec4` | `texelFetch(gsampler2D, ivec2 P, int lod)` with **fixed lod** | **Unfiltered** lookup at integer texel coordinates \((x, y)\) passed as `texel` (integral values in a `vec2` carrier), always at the texture’s **base mip** (same idea as GLSL `texelFetch` with `lod == 0`; TTSL has no lod argument). | no |

**Semantics**

- **`texture_index`**: unsigned logical slot into the engine texture store (the same indexing family used when materials reference `albedo_texture_idx` / texture ids on the host). Out-of-range indices yield an engine-defined color (often opaque black).
- **Combining with varyings**: Using `tt_texture(albedo_ix, tt_TexCoord0)` is the direct analogue of sampling in a fragment shader with an interpolated `in vec2 texcoord` and a bound `sampler2D`.
- **Channels**: Return type is **`vec4`** with RGBA in **linear** float components.

## Primitives

The table below is the intended GLSL-style surface for math and utilities. **Texture lookups use TTSL-prefixed names** (`tt_texture`, `tt_texelFetch`) even though most scalar/vector helpers mirror bare GLSL (`mix`, `clamp`, …). See [TTSL Compiler](ttsl_compiler.md) for what actually compiles and [Opcode Reference](opcode_reference.md) for VM operations.

**Availability** is **Shipped**, **Planned**, or **Missing** on the TTSL compiler surface. **Shipped** means at least one spelling in the row is accepted by `all_passes_compilation` today (see **Notes / ranges** for the subset). **Planned** names may still have VM opcodes reserved—check the opcode reference—but they are not wired through this language surface yet. **Missing** rows describe intended builtins that are **not** parsed, lowered, or opcode-backed yet (often paired with engine work in Rust).

| Availability | Function (GLSL-style) | Typical signatures (examples) | What it’s for | Notes / ranges |
|---|---|---|---|---|
| Shipped | tt_texture | `tt_texture(tex_index: int, coord: vec2) -> vec4` | 2D texture sample (filtered) | OpenGL **`texture(sampler2D, vec2)`**; pair `coord` with **`tt_TexCoord0`** / **`tt_TexCoord1`** like a varying |
| Planned | tt_texelFetch | `tt_texelFetch(tex_index: int, texel: vec2) -> vec4` | Integer texel read (base mip) | Same role as **`texelFetch(..., ivec2 P, 0)`**; no lod parameter in TTSL; not implemented end-to-end in the compiler yet |
| Planned | mix | mix(a, b, t) -> T | Linear interpolation (lerp) | `t` usually [0..1], works on float/vec2/vec3/vec4 in GLSL; TTSL does not expose bare **`mix`** yet (`glm.mix` is not typable in `type_of` either—see compiler docs) |
| Planned | clamp | clamp(x, lo, hi) -> T | Clamp into a range | Great for keeping colors in [0..1] |
| Planned | min / max | min(a,b)->T, max(a,b)->T | Bounds / compare | Works component-wise on vectors |
| Planned | smoothstep | smoothstep(e0, e1, x) -> T | Smooth threshold | Hermite curve; output in [0..1] when e0<e1 |
| Planned | step | step(edge, x) -> T | Hard threshold | Returns 0 or 1 (component-wise) |
| Shipped | abs / sign | abs(x)->T, sign(x)->T | Magnitude / sign | TTSL: **`abs`** only (unary opcode lowering). **`sign`** not implemented; GLSL defines `sign(0)=0` |
| Shipped | floor / ceil / fract | floor(x)->T, ceil(x)->T, fract(x)->T | Tiling, patterns, quantization | Bare **`floor`** / **`ceil`** / **`fract`** and **`glm.floor`** / **`glm.ceil`** / **`glm.fract`**; works on float/vec2/vec3/vec4. `fract(x)=x-floor(x)` in [0..1) |
| Shipped | mod | mod(x, y) -> T | Periodic wrap | Bare **`mod`** and **`glm.mod`**; GLSL-style `x - y * floor(x/y)` for float/vec2/vec3/vec4 (component-wise on vectors) |
| Planned | pow | pow(x, y) -> T | Curves / gamma-like shaping | Be careful with negative bases |
| Planned | sqrt / inversesqrt | sqrt(x)->T, inversesqrt(x)->T | Lengths, normalization helpers | `x` should be >= 0 for real sqrt |
| Planned | exp / log | exp(x)->T, log(x)->T | Exponential / logarithmic shaping | Useful for tone mapping-ish curves |
| Shipped | sin / cos / tan | sin(x)->T, cos(x)->T, tan(x)->T | Oscillation / waves | TTSL: **`sin`** only (bare **`sin`** and **`glm.sin`**); input in radians. **`cos`** / **`tan`** are parsed on some paths but do not codegen yet |
| Planned | asin / acos / atan | asin(x)->T, acos(x)->T, atan(y,x)->T | Angles from values | `asin/acos` domain [-1..1] |
| Planned | radians / degrees | radians(deg)->T, degrees(rad)->T | Unit conversion | Convenience |
| Planned | dot | dot(a,b)->float | Lighting, projections | For vec2/vec3/vec4 |
| Planned | cross | cross(a,b)->vec3 | Perpendicular vector | Only vec3 |
| Planned | length | length(v)->float | Vector magnitude | |
| Planned | distance | distance(a,b)->float | Metric distance | |
| Planned | normalize | normalize(v)->T | Unit-length vector | Undefined for zero-length vectors (decide your behavior) |
| Missing | tt_linear_depth | ``tt_linear_depth(z: float) -> float`` | Linear eye-space / clip-distance factor for fog and depth grading | Intended to convert a **stored depth** (e.g. ``tt_FragDepth`` or a reconstructed linear depth in engine units) into a stable **[0..1]** scalar using the active **``tt_Near``** / **``tt_Far``** uniforms supplied by Rust—so shaders avoid ad‑hoc formulas that duplicate projection constants. Exact mapping (hyperbolic vs linear clip space) will match whatever the renderer documents for ``tt_FragDepth`` once ``tt_Near`` / ``tt_Far`` ship; until then demos keep manual math. Not in the compiler or VM. |
| Planned | reflect | reflect(I, N)->T | Reflection vector | `N` should be normalized |
| Planned | refract | refract(I, N, eta)->T | Refraction vector | `eta` is n1/n2; returns 0-vector on total internal reflection (GLSL behavior) |
| Planned | faceforward | faceforward(N, I, Nref)->T | Choose normal orientation | Helps ensure N faces viewer/light |
| Planned | any / all | any(bvec)->bool, all(bvec)->bool | Boolean reductions | For vector bools if you have them (or emulate) |
| Planned | lessThan / greaterThan / equal / notEqual | lessThan(a,b)->bvec, equal(a,b)->bvec | Vector comparisons | If you don’t have bvec types, you can omit or return bool via `all()` patterns |
| Planned | isnan / isinf | isnan(x)->bvec/bool, isinf(x)->bvec/bool | Robustness / debugging | Optional but handy in shader languages |
| Planned | fma | fma(a,b,c)->T | Fused multiply-add | If available, improves precision/perf |
| Planned | dFdx / dFdy | dFdx(x)->T, dFdy(x)->T | Screen-space derivatives | Niche but powerful; needs neighbor access (per 2x2 quad concept) |
| Planned | fwidth | fwidth(x)->T | `abs(dFdx)+abs(dFdy)` | Great for anti-aliased lines/signed-distance fields (SDF) style edges |
| Planned | round / trunc | round(x)->T, trunc(x)->T | Quantization | Optional; useful for glyph selection / palette quantization |
| Planned | frexp / ldexp | frexp(x, out exp)->T, ldexp(x, exp)->T | Mantissa/exponent ops | Very niche; can skip unless you want full GLSL parity |
| Planned | bitwise (int) | & \| ^ ~ << >> | Masks, packing, hashing | If your “int” is real int, these are very useful for RNG/patterns |


ABI: Opcode Reference
---------------------

The TTSL virtual machine uses a fixed set of typed opcodes that form its ABI.
The full list of opcodes with their numeric values, types, and input signatures
is maintained in the [Opcode Reference](opcode_reference.md).

This reference is auto-generated from the opcode definitions in
`python/tt3de/ttsl/ttisa/low_level_def.py` by running `bash scripts/gen_opcodes.sh`
(or `powershell -ExecutionPolicy Bypass -File scripts/gen_opcodes.ps1` on Windows).

Low-Level Runtime/Material Bridge
---------------------------------

This section documents how TTSL VM output is consumed by the Rust renderer.

### VM return contract (`OP_RET`)

At bytecode level, `OP_RET` returns **three values**:

- `front: vec4`
- `back: vec4`
- `glyph: i32`

The Rust VM implementation (`src/ttsl/opcodes.rs`) reads these from register files
as `v4[a]`, `v4[b]`, and `i32[c]`, and `ttsl_run(...)` exposes them to Python as:

```python
front_vec4, back_vec4, glyph_idx = ttsl_run(*regs, bytecode)
```

In practice today, most demos use `front_vec4` as the generated color and then
write a material (often static color) into `MaterialBufferPy` each frame.

### How rendering applies materials

Material application happens after rasterization:

1. raster stage writes per-pixel `PixInfo` (`uv`, `uv_1`, normal, `material_id`, etc.)
2. draw stage resolves each pixel layer and calls `apply_material(...)`
3. material writes `CanvasCell` output (`front_color`, `back_color`, `glyph`)

The final terminal cell is produced by material logic. In particular, when the
material mode is `Shader`, the material owns compiled TTSL bytecode and executes
it during material application so shader output directly drives final cell
channels (`front_color`, `back_color`, `glyph`).

### TTSL Python compiler surface syntax

The TTSL compiler requires the shader to ``return`` a 3-tuple ``(front, back, glyph)``
with types ``(vec4, vec4, int)``, matching ``OP_RET`` above. Annotate as
``tuple[vec4, vec4, int]`` (or ``typing.Tuple[...]``). See the [TTSL Compiler](ttsl_compiler.md) example.
