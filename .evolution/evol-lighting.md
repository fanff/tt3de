# Evolution: Lighting — LightBuffer, accessor opcodes, and reference shader

```yaml
id: evol-lighting
status: draft
created: 2026-05-11
authors: []
supersedes: []
superseded-by: ""
related:
  - .evolution/evol-shader-math-normal.md  # Prerequisite: tt_Normal + dot/normalize/length/max/min/clamp
  - source/ttsl.md                         # TTSL built-in variables and primitives
  - source/low_level_api.rst               # Pipeline, buffers, material modes
  - source/high_level_api.rst              # User-facing API surface
```

## Summary

Add real light capability to the tt3de engine. Introduce a **LightBuffer** — a new engine-level buffer holding a fixed-capacity set of typed light sources (ambient, directional, point) — and TTSL **accessor opcodes** that let shaders query individual light properties by index. Provide a **reference TTSL shader** demonstrating ambient illumination, Lambert diffuse from a directional light, and point-light attenuation. Spot lights, shadows, and specular effects are explicitly excluded from this first iteration.

## Motivation and context

**Current behavior** — tt3de renders all surfaces with flat color driven by material modes (StaticColor, BaseTexture, Textured) or arbitrary TTSL shader logic. There is no concept of light sources anywhere in the engine: no light storage, no light uniforms, no shading model. Every surface receives identical illumination regardless of orientation or position.

The rasterizer already interpolates normals per pixel (`PixInfo.normal`) and the TTSL shader system supports per-pixel computation with engine uniforms (`tt_Time`, `tt_Near`, `tt_Far`) and texture sampling (`tt_texture`). The `evol-shader-math-normal` prerequisite wires `tt_Normal` into the VM and ships the math primitives (`dot`, `normalize`, `length`, `max`) needed for lighting calculations. What's missing is the **data delivery mechanism** — a way to define lights in Python and access their properties from TTSL.

**Reference comparison** — In OpenGL, lights are traditionally either built-in uniforms (fixed-function era) or user-defined uniform buffers / SSBOs queried in fragment shaders. tt3de's approach mirrors the modern pattern: a structured buffer on the host side, accessed through typed lookups in the shader, leaving the lighting equation entirely to shader code.

**Why a buffer, not plain uniforms** — User uniforms (like `u_albedo` in the fog demo) work for single-value parameters but become unwieldy for N lights: each light has 5+ properties, and the number of lights varies. A `LightBuffer` indexed by `tt_lightColor(i)` etc. scales cleanly without exploding the uniform count, mirrors how `TextureBuffer` + `tt_texture(slot, uv)` already works, and keeps the light data in one cache-friendly Rust structure rather than scattered across register seeds.

## Goals

- **LightBuffer**: A new Rust buffer type holding up to N light definitions (N = 16 as a reasonable default capacity), exposed to Python via `LightBufferPy`.
- **Light types**: Ambient (color only), Directional (color + direction), Point (color + position + attenuation).
- **TTSL accessor opcodes**: `tt_lightCount`, `tt_lightType`, `tt_lightColor`, `tt_lightDirection`, `tt_lightPosition`, `tt_lightAttenuation` — each an opcode reading from the LightBuffer by integer index.
- **Engine integration**: LightBuffer passed to the shader VM alongside TextureBuffer during material application.
- **Python API**: `LightBufferPy` with methods to set/clear individual light slots and query count.
- **Reference shader**: A complete TTSL shader demonstrating ambient + Lambert diffuse + point-light distance attenuation, usable as a starting point for custom lighting.
- **Demo**: At least one demo scene using the reference shader to visually validate the lighting pipeline.

## Non-goals

- **Spot lights**: Excluded from first iteration. The LightBuffer can reserve a type enum value for future addition.
- **Shadows**: No shadow mapping, shadow volumes, or occlusion. Pure direct illumination.
- **Specular / Phong / Blinn-Phong highlights**: No shiny effects. Lambert diffuse only for the reference shader (users can implement specular in custom TTSL).
- **Automatic lighting in non-shader materials**: StaticColor, BaseTexture, Textured modes are unaffected. Lighting is a shader-level concern.
- **View-space or tangent-space normal transforms**: Normals flow in whatever space `tt_Normal` provides (see `evol-shader-math-normal`); the reference shader assumes world-space conventions.
- **Light animation helpers**: No built-in light orbiting, flickering, or color cycling. Users animate via `LightBufferPy` calls in `update_step`.

## User-visible functionality

### Python API

```python
from tt3de.tt3de import LightBufferPy

light_buffer = LightBufferPy(capacity=16)

light_buffer.set_ambient(0, color=(0.15, 0.15, 0.15))

light_buffer.set_directional(1,
    color=(0.8, 0.8, 0.7),
    direction=(0.0, -1.0, -0.5),  # normalized internally
)

light_buffer.set_point(2,
    color=(1.0, 0.6, 0.3),
    position=(3.0, 2.0, 0.0),
    attenuation=(1.0, 0.09, 0.032),  # constant, linear, quadratic
)

light_buffer.clear(2)  # removes light at slot 2

self.rc.light_buffer = light_buffer
```

### TTSL shader

```python
def shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
    n: vec3 = normalize(tt_Normal)
    base_color: vec3 = vec3(0.8, 0.5, 0.3)
    result: vec3 = vec3(0.0, 0.0, 0.0)

    count: int = tt_lightCount()
    i: int = 0
    # note: TTSL for-loops are not yet supported; unroll or use while
    # For the reference shader, a fixed unrolled loop over a small count is acceptable.

    # -- ambient contribution --
    amb_color: vec3 = tt_lightColor(0)
    result = result + base_color * amb_color.x  # uniform ambient factor

    # -- directional light --
    dir_color: vec3 = tt_lightColor(1)
    light_dir: vec3 = tt_lightDirection(1)
    diff: float = max(dot(n, light_dir), 0.0)
    result = result + base_color * dir_color * diff

    # -- point light --
    pt_color: vec3 = tt_lightColor(2)
    pt_pos: vec3 = tt_lightPosition(2)
    # ... distance attenuation ...

    c: vec4 = vec4(result.x, result.y, result.z, 1.0)
    return (c, c, 0)
```

### Breaking changes

None. Existing apps that do not create a `LightBufferPy` are unaffected. The render context defaults to no light buffer (or an empty one); accessor opcodes return zero/default when no buffer is attached.

## Technical approach

### Baseline

| Component | Current state |
|-----------|--------------|
| Light sources | None — no concept in the engine |
| Shader data access | TextureBuffer via `tt_texture(slot, uv)` opcode; user uniforms via register seeds |
| `RustRenderContext` | Holds `transform_buffer`, `geometry_buffer`, `primitive_buffer`, `drawing_buffer`, `texture_buffer`, `material_buffer` |
| `run_ttsl` / `ShaderMaterial::render_mat` | Receives `&TextureBuffer` via `TtslTextureEnv` trait; no light env |

### Phase 1: LightBuffer (Rust)

**New module**: `src/lightbuffer/` (or `src/light/`)

```
src/lightbuffer/
    mod.rs           -- LightBuffer struct + public API
    light_buffer_py.rs -- PyO3 bindings
```

**Data model** per light slot:

```rust
#[derive(Clone, Copy)]
pub enum LightType {
    Empty = 0,
    Ambient = 1,
    Directional = 2,
    Point = 3,
}

#[derive(Clone, Copy)]
pub struct LightSlot {
    pub light_type: LightType,
    pub color: Vec3,       // RGB intensity [0..1] or HDR
    pub direction: Vec3,   // normalized; meaningful for Directional
    pub position: Vec3,    // world-space; meaningful for Point
    pub attenuation: Vec3, // (constant, linear, quadratic); meaningful for Point
}
```

**`LightBuffer`**:
```rust
pub struct LightBuffer<const CAPACITY: usize> {
    slots: [LightSlot; CAPACITY],
    count: usize,  // number of active (non-Empty) slots, or highest used index + 1
}
```

Methods: `set_ambient(index, color)`, `set_directional(index, color, direction)`, `set_point(index, color, position, attenuation)`, `clear(index)`, `get(index) -> &LightSlot`, `count() -> usize`.

Direction is normalized on write (`set_directional` normalizes internally) so shaders don't need to re-normalize.

### Phase 2: TTSL accessor opcodes

**New opcodes** (added to `low_level_def.py`, regenerated):

| TTSL function | Signature | Opcode name | Returns |
|---------------|-----------|-------------|---------|
| `tt_lightCount()` | `() → int` | `TT_LIGHT_COUNT` | Number of active lights |
| `tt_lightType(i: int)` | `(int) → int` | `TT_LIGHT_TYPE` | 0=empty, 1=ambient, 2=directional, 3=point |
| `tt_lightColor(i: int)` | `(int) → vec3` | `TT_LIGHT_COLOR` | RGB color of light at slot i |
| `tt_lightDirection(i: int)` | `(int) → vec3` | `TT_LIGHT_DIRECTION` | Direction vector (normalized) |
| `tt_lightPosition(i: int)` | `(int) → vec3` | `TT_LIGHT_POSITION` | World-space position |
| `tt_lightAttenuation(i: int)` | `(int) → vec3` | `TT_LIGHT_ATTENUATION` | (constant, linear, quadratic) |

**VM execution**: Similar to `TT_TEXTURE`, these opcodes access an environment trait. Introduce `TtslLightEnv`:

```rust
pub trait TtslLightEnv {
    fn light_count(&self) -> i32;
    fn light_type(&self, index: i32) -> i32;
    fn light_color(&self, index: i32) -> Vec3;
    fn light_direction(&self, index: i32) -> Vec3;
    fn light_position(&self, index: i32) -> Vec3;
    fn light_attenuation(&self, index: i32) -> Vec3;
}
```

`LightBuffer` implements `TtslLightEnv`. The `run_ttsl` function signature gains an `Option<&dyn TtslLightEnv>` parameter (defaulting to `None` for backward compatibility). Out-of-range indices return zero vectors / 0.

**Opcode code generation**: Add a new category in `low_level_def.py` (`"Light Accessors"`) with hand-written `rust_match_code` blocks (like `TT_TEXTURE`) since they access the `light` env pointer, not register-to-register math.

### Phase 3: Engine integration

1. **`RustRenderContext`**: Add a `light_buffer` field (defaulting to an empty buffer or `None`).
2. **`ShaderMaterial::render_mat`**: Pass the light buffer reference to `run_ttsl` as `TtslLightEnv`.
3. **`DrawBuffer::apply_material_on`**: Thread the light buffer through to material application (same pattern as `TextureBuffer`).
4. **Python `RustRenderContext`**: Expose `light_buffer` property for assignment.

### Phase 4: Compiler support

1. **New built-in functions**: Register `tt_lightCount`, `tt_lightType`, `tt_lightColor`, `tt_lightDirection`, `tt_lightPosition`, `tt_lightAttenuation` in the compiler.
2. **Type inference**: `tt_lightCount()` → `int`, `tt_lightType(int)` → `int`, others → `vec3`.
3. **Code emission**: Lower each call to its corresponding opcode.
4. These are **not** `globals_dict` entries or implicit pixel vars — they are global callable built-ins (like `tt_texture`).

### Phase 5: Reference shader + demo

1. **Reference shader source**: A TTSL function implementing:
   - Iterate over lights (unrolled or bounded loop if TTSL gains `while` support)
   - Ambient: `result += albedo * light_color`
   - Directional: `result += albedo * light_color * max(dot(N, L), 0.0)`
   - Point: compute `L = normalize(light_pos - frag_world_pos)`, distance, attenuation factor `1.0 / (c + l*d + q*d*d)`, then `result += albedo * light_color * max(dot(N, L), 0.0) * atten`
2. **Demo app**: A scene with a textured or colored object, one ambient + one directional + one point light, rotating the object or moving the point light to show dynamic shading. Placed in `demos/3d/`.

### Alternatives considered

- **Engine-level `tt_*` uniforms** (fixed `tt_AmbientColor`, `tt_DirLightDir` etc.): Rejected — doesn't scale to N lights; forces a fixed light layout into every shader's register seed.
- **Pure user uniforms per shader**: Rejected — too manual; every shader must wire its own light data; no reuse.
- **New Rust `LitMaterial` mode**: Deferred — could be a convenience wrapper that internally uses a compiled TTSL shader + LightBuffer, added later. The reference shader approach proves the pipeline first.

### Files likely touched

- `src/lightbuffer/mod.rs` (new) — `LightBuffer`, `LightSlot`, `LightType`
- `src/lightbuffer/light_buffer_py.rs` (new) — PyO3 `LightBufferPy`
- `src/ttsl/mod.rs` — `TtslLightEnv` trait, `run_ttsl` signature update
- `src/ttsl/opcodes.rs` — auto-generated (new light opcodes)
- `src/material/shader_material.rs` — pass light env to `run_ttsl`
- `src/drawbuffer/drawbuffer.rs` — thread light buffer through `apply_material_on`
- `src/lib.rs` — expose `LightBufferPy`, register `lightbuffer` module
- `python/tt3de/ttsl/ttisa/low_level_def.py` — new opcode generators for light accessors
- `python/tt3de/ttsl/ttsl_assembly.py` — new `OpCodes` members
- `python/tt3de/ttsl/compiler.py` — light accessor built-in functions
- `python/tt3de/ttsl/ttisa/ttisa_opcodes.py` — auto-generated
- `source/opcode_reference.md` — auto-generated
- `source/ttsl.md` — new built-in functions section for light accessors
- `source/low_level_api.rst` — new LightBuffer section
- `demos/3d/` — new lighting demo

## Usability and documentation

- **`source/low_level_api.rst`**: Add a "LightBuffer" section (parallel to Texture Buffer / Material Buffer) describing the slot data model, capacity, and how it feeds into the shader path.
- **`source/ttsl.md`**: Add light accessor functions to the primitives table; add a "Lighting" section or subsection explaining the accessor pattern and linking to the reference shader.
- **`source/high_level_api.rst`**: Brief note in the "Loading materials" or a new "Lighting" section showing how to create and assign a `LightBufferPy`.
- **Reference shader**: Ship as a documented example (in `source/ttsl.md` or a dedicated `source/lighting.md`) with inline comments explaining each lighting term. This becomes the canonical "how to light things in tt3de" resource.
- **Demo**: `demos/3d/ttsl_lighting.py` (or similar name) — minimal, runnable, shows all three light types.

## Testability

- **LightBuffer unit tests** (Rust): Create, set slots, read back values, clear, verify count. Edge cases: out-of-range index, overwrite existing slot, clear already-empty slot.
- **Opcode unit tests** (Rust): Verify each `TT_LIGHT_*` opcode reads correct data from a mock `TtslLightEnv`. Test out-of-range index returns defaults.
- **Compiler tests** (Python): Compile shaders using `tt_lightCount()`, `tt_lightColor(0)`, etc. Verify bytecode generation succeeds and opcodes are correct.
- **E2E tests** (Python): A shader that reads light properties and returns them as pixel colors; verify output matches the configured LightBuffer. Extend `tests/tt3de/ttsl/test_e2e.py`.
- **Integration test**: Full render pipeline with a LightBuffer attached; verify that a triangle facing the directional light is brighter than one facing away (coarse pixel color comparison, not pixel-perfect).
- **Regression**: All existing tests pass. Shaders that don't use light accessors must be unaffected.

## Complexity and scope

| Phase | Size | Risk | Can ship independently? |
|-------|------|------|------------------------|
| Phase 1: LightBuffer (Rust) | M | Low — new module, no existing code touched | Yes (inert until opcodes exist) |
| Phase 2: Accessor opcodes | M | Medium — `run_ttsl` signature change propagates | Yes, with Phase 1 |
| Phase 3: Engine integration | S | Low — follows TextureBuffer pattern | Requires Phase 1+2 |
| Phase 4: Compiler support | M | Medium — new built-in function category | Requires Phase 2 |
| Phase 5: Reference shader + demo | S | Low — pure TTSL + Python | Requires all above |

**Dependency**: This evolution depends on `evol-shader-math-normal` (`tt_Normal`, `dot`, `normalize`, `length`, `max`) being shipped first.

**Rollback**: LightBuffer is additive. If it lands behind a feature flag or simply unused, existing behavior is unchanged. Removing it later means deleting the module + opcodes and bumping the opcode table (breaking bytecode compatibility, but tt3de doesn't promise bytecode stability today).

## A priori performance analysis

**Hot paths**:

- **Light accessor opcodes** execute during material application, once per pixel per light query. For a reference shader with 3 lights and ~5 accessors per light, that's ~15 opcode dispatches per pixel. Each accessor is a bounds-checked array index + field read — comparable cost to `READ_AXIS_*` opcodes. For a 200x60 cell grid = 12,000 cells, that's ~180,000 accessor calls per frame. On modern CPUs this is sub-millisecond.
- **LightBuffer memory**: 16 slots × ~80 bytes per slot ≈ 1.3 KB. Fits in L1 cache. No allocation per frame.
- **`run_ttsl` signature change**: Adding `Option<&dyn TtslLightEnv>` is a pointer-sized argument. When `None`, light opcodes return defaults (one branch per call). When `Some`, trait dispatch is a single vtable indirection.

**Relative cost ranking** (cheapest → expensive):

1. Scene with no light buffer attached — zero overhead (accessor opcodes never called)
2. Scene with 1–3 lights, reference shader — ~15 extra opcode dispatches per pixel; dominated by existing raster + shade cost
3. Scene with 16 lights, complex custom shader — ~80 extra dispatches per pixel; likely still not the bottleneck vs triangle rasterization

**Validation**: Time `apply_material_on` with and without light accessors on a stress scene (full-screen quad, 16 lights). Compare to baseline (no-light shader).

## Risks and open questions

- **`run_ttsl` signature change**: Adding a second `Option<&dyn Trait>` parameter touches every call site. Mitigate by using a combined environment struct or by bundling both textures and lights into a single `TtslEnv` trait.
- **TTSL loop support**: The reference shader needs to iterate over lights. If TTSL doesn't support `while` or `for` loops yet, the reference shader must unroll the loop manually for a fixed number of lights. Document this limitation. Loop support could be a separate evolution.
- **World-space assumption**: The reference shader assumes `tt_Normal` and light positions/directions are in the same coordinate space (world). If models use different conventions, results will be wrong. Document the assumption clearly.
- **HDR and clamping**: Light color × albedo can exceed 1.0. The reference shader should clamp the final result to [0, 1] before output. Or allow HDR and let the material bridge clamp — document the convention.
- **Point light fragment position**: Computing distance from fragment to light requires the fragment's world-space position, which is not currently a TTSL built-in. `tt_FragPos` is NDC-space. Options: (a) add `tt_WorldPos` as a new per-pixel built-in (requires storing world-space position in PixInfo, which is not done today), (b) use `tt_FragDepth` + projection inverse to reconstruct position (complex, fragile), (c) defer point lights to a later phase until `tt_WorldPos` is available. **This is the biggest open question** — it may scope-reduce the first iteration to ambient + directional only, with point lights requiring a `tt_WorldPos` prerequisite.
- **Opcode numbering stability**: Adding opcodes shifts all subsequent indices. Not a problem today (no bytecode persistence), but worth noting if bytecode caching is ever considered.

## Decision record

- **Status**: draft
- **Resolution**: *(to be filled when closing)*

## References

- `.evolution/evol-shader-math-normal.md` — Prerequisite: `tt_Normal`, `dot`, `normalize`, `length`, `max`
- `source/ttsl.md` — TTSL built-in variables and primitives
- `source/low_level_api.rst` — Pipeline overview, buffer descriptions, material modes
- `source/ttsl_compiler.md` — Compiler pipeline and extension guide
- `src/ttsl/mod.rs` — `TtslTextureEnv` trait (pattern for `TtslLightEnv`)
- `src/material/shader_material.rs` — Where `run_ttsl` is called with texture env
- `demos/3d/ttsl_fog.py` — Closest existing precedent (per-pixel shader with uniforms)
