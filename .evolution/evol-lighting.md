# Evolution: Lighting — LightBuffer, accessor opcodes, and reference shader

```yaml
id: evol-lighting
status: draft
created: 2026-05-11
authors: []
supersedes: []
superseded-by: ""
related:
  - .evolution/evol-shader-math-normal.md  # Prerequisite: tt_Normal, tt_ViewPos, smooth normals, math primitives
  - source/ttsl.md                         # TTSL built-in variables and primitives
  - source/low_level_api.rst               # Pipeline, buffers, material modes
  - source/high_level_api.rst              # User-facing API surface
```

## Summary

Add real light capability to the tt3de engine. Introduce a **LightBuffer** — a new engine-level buffer holding a fixed-capacity set of typed light sources (ambient, directional, point) — and TTSL **accessor opcodes** that let shaders query individual light properties by index. The LightBuffer stores light data in **world space** (user-friendly); the engine **auto-transforms** positions and directions to **view space** each frame before material application, following the OpenGL `glLightfv` convention. Provide a **reference TTSL shader** demonstrating ambient illumination, Lambert diffuse from a directional light, and point-light distance attenuation — all computed in view space using `tt_Normal`, `tt_ViewPos`, and the light accessors. Spot lights, shadows, and specular effects are explicitly excluded from this first iteration.

## Motivation and context

**Current behavior** — tt3de renders all surfaces with flat color driven by material modes (StaticColor, BaseTexture, Textured) or arbitrary TTSL shader logic. There is no concept of light sources anywhere in the engine: no light storage, no light uniforms, no shading model. Every surface receives identical illumination regardless of orientation or position.

The `evol-shader-math-normal` prerequisite wires `tt_Normal` (view-space interpolated normal), `tt_ViewPos` (view-space fragment position), smooth per-vertex normals, and the essential math primitives (`dot`, `normalize`, `length`, `max`, `clamp`) into TTSL. What's missing is the **data delivery mechanism** — a way to define lights in Python and access their properties from TTSL.

**Reference comparison** — In classic OpenGL, `glLightfv(GL_LIGHT0, GL_POSITION, pos)` transformed the light position by the current modelview matrix, placing it in eye (view) space automatically. Fragment shaders then received view-space light data alongside view-space normals and positions. tt3de follows this convention: the user specifies lights in world space, the engine transforms them to view space, and TTSL shaders compute lighting in view space.

**Why a buffer, not plain uniforms** — User uniforms (like `u_albedo` in the fog demo) work for single-value parameters but become unwieldy for N lights: each light has 5+ properties, and the number of lights varies. A `LightBuffer` indexed by `tt_lightColor(i)` etc. scales cleanly without exploding the uniform count, mirrors how `TextureBuffer` + `tt_texture(slot, uv)` already works, and keeps the light data in one cache-friendly Rust structure rather than scattered across register seeds.

## Goals

- **LightBuffer**: A new Rust buffer type holding up to N light definitions (N = 16 default capacity), exposed to Python via `LightBufferPy`.
- **Light types**: Ambient (color only), Directional (color + direction), Point (color + position + attenuation).
- **World-to-view auto-transform**: Users set lights in world space. Each frame before material application, the engine transforms directions and positions to view space using the current `view_matrix_3d`. TTSL accessors return view-space values. This mirrors the OpenGL `glLightfv` convention.
- **TTSL accessor opcodes**: `tt_lightCount`, `tt_lightType`, `tt_lightColor`, `tt_lightDirection`, `tt_lightPosition`, `tt_lightAttenuation` — each an opcode reading from the view-space-transformed LightBuffer by integer index.
- **Engine integration**: LightBuffer passed to the shader VM alongside TextureBuffer during material application.
- **Python API**: `LightBufferPy` with methods to set/clear individual light slots and query count.
- **Reference shader**: A complete TTSL shader demonstrating ambient + Lambert diffuse + point-light distance attenuation in view space.
- **Demo**: At least one demo scene using the reference shader to visually validate the lighting pipeline.

## Non-goals

- **Spot lights**: Excluded from first iteration. The LightBuffer can reserve a type enum value for future addition.
- **Shadows**: No shadow mapping, shadow volumes, or occlusion. Pure direct illumination.
- **Specular / Phong / Blinn-Phong highlights**: No shiny effects. Lambert diffuse only for the reference shader (users can implement specular in custom TTSL shaders using `tt_ViewPos` for view direction).
- **Automatic lighting in non-shader materials**: StaticColor, BaseTexture, Textured modes are unaffected. Lighting is a shader-level concern.
- **Tangent-space normals or normal mapping**.
- **Light animation helpers**: No built-in light orbiting, flickering, or color cycling. Users animate via `LightBufferPy` calls in `update_step`.

## User-visible functionality

### Python API

```python
from tt3de.tt3de import LightBufferPy

light_buffer = LightBufferPy(capacity=16)

light_buffer.set_ambient(0, color=(0.15, 0.15, 0.15))

light_buffer.set_directional(1,
    color=(0.8, 0.8, 0.7),
    direction=(0.0, -1.0, -0.5),  # world-space; normalized internally
)

light_buffer.set_point(2,
    color=(1.0, 0.6, 0.3),
    position=(3.0, 2.0, 0.0),    # world-space
    attenuation=(1.0, 0.09, 0.032),  # constant, linear, quadratic
)

light_buffer.clear(2)  # removes light at slot 2

self.rc.light_buffer = light_buffer
# Engine auto-transforms to view space each frame using the active camera's view matrix.
```

### TTSL shader (reference — view-space lighting)

```python
def lit_shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
    n: vec3 = normalize(tt_Normal)           # view-space normal (smooth)
    frag_pos: vec3 = tt_ViewPos              # view-space fragment position
    base_color: vec3 = vec3(0.8, 0.5, 0.3)  # or sample from texture
    result: vec3 = vec3(0.0, 0.0, 0.0)

    # -- ambient contribution --
    amb_color: vec3 = tt_lightColor(0)
    result = result + base_color * amb_color

    # -- directional light (view-space direction from auto-transform) --
    dir_color: vec3 = tt_lightColor(1)
    light_dir: vec3 = tt_lightDirection(1)   # view-space, pre-normalized
    diff: float = max(dot(n, light_dir), 0.0)
    result = result + base_color * dir_color * diff

    # -- point light (view-space position from auto-transform) --
    pt_color: vec3 = tt_lightColor(2)
    pt_pos: vec3 = tt_lightPosition(2)       # view-space
    pt_atten: vec3 = tt_lightAttenuation(2)
    to_light: vec3 = pt_pos - frag_pos       # tt_ViewPos enables this
    dist: float = length(to_light)
    l_dir: vec3 = normalize(to_light)
    pt_diff: float = max(dot(n, l_dir), 0.0)
    atten: float = 1.0 / (pt_atten.x + pt_atten.y * dist + pt_atten.z * dist * dist)
    result = result + base_color * pt_color * pt_diff * atten

    # clamp to [0, 1]
    result = clamp(result, vec3(0.0, 0.0, 0.0), vec3(1.0, 1.0, 1.0))
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
| `TransformPack` | Has unused `environment_light: Vec3` field — placeholder, not wired |

### Phase 1: LightBuffer (Rust)

**New module**: `src/lightbuffer/`

```
src/lightbuffer/
    mod.rs             -- LightBuffer struct, LightSlot, LightType, TtslLightEnv impl
    light_buffer_py.rs -- PyO3 bindings (LightBufferPy)
```

**Data model** per light slot — dual storage for world and view space:

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
    pub color: Vec3,              // RGB intensity [0..1] or HDR
    // World-space (set by user)
    pub world_direction: Vec3,    // normalized; meaningful for Directional
    pub world_position: Vec3,     // meaningful for Point
    pub attenuation: Vec3,        // (constant, linear, quadratic); meaningful for Point
    // View-space (auto-computed each frame)
    pub view_direction: Vec3,
    pub view_position: Vec3,
}
```

**`LightBuffer`**:
```rust
pub struct LightBuffer<const CAPACITY: usize> {
    slots: [LightSlot; CAPACITY],
    count: usize,
}
```

Methods:
- `set_ambient(index, color)`, `set_directional(index, color, direction)`, `set_point(index, color, position, attenuation)`, `clear(index)`, `count() -> usize`
- `update_view_space(view_matrix: &Mat4)` — called once per frame before material application. Transforms `world_direction` and `world_position` to view space for each active slot. For directional lights: `view_dir = (view_matrix * vec4(world_dir, 0.0)).xyz()`. For point lights: `view_pos = (view_matrix * vec4(world_pos, 1.0)).xyz()`. Ambient lights are space-independent (color only).

Direction is normalized on write (`set_directional` normalizes `world_direction` internally).

### Phase 2: TTSL accessor opcodes

**New opcodes** (added to `low_level_def.py`, regenerated):

| TTSL function | Signature | Opcode name | Returns |
|---------------|-----------|-------------|---------|
| `tt_lightCount()` | `() → int` | `TT_LIGHT_COUNT` | Number of active lights |
| `tt_lightType(i: int)` | `(int) → int` | `TT_LIGHT_TYPE` | 0=empty, 1=ambient, 2=directional, 3=point |
| `tt_lightColor(i: int)` | `(int) → vec3` | `TT_LIGHT_COLOR` | RGB color |
| `tt_lightDirection(i: int)` | `(int) → vec3` | `TT_LIGHT_DIRECTION` | **View-space** direction (pre-normalized) |
| `tt_lightPosition(i: int)` | `(int) → vec3` | `TT_LIGHT_POSITION` | **View-space** position |
| `tt_lightAttenuation(i: int)` | `(int) → vec3` | `TT_LIGHT_ATTENUATION` | (constant, linear, quadratic) — space-independent |

**VM execution**: Introduce `TtslLightEnv` trait (mirrors `TtslTextureEnv`):

```rust
pub trait TtslLightEnv {
    fn light_count(&self) -> i32;
    fn light_type(&self, index: i32) -> i32;
    fn light_color(&self, index: i32) -> Vec3;
    fn light_direction(&self, index: i32) -> Vec3;  // returns view_direction
    fn light_position(&self, index: i32) -> Vec3;   // returns view_position
    fn light_attenuation(&self, index: i32) -> Vec3;
}
```

`LightBuffer` implements `TtslLightEnv`, returning view-space values from the `view_direction` / `view_position` fields (populated by `update_view_space`). Out-of-range indices return zero vectors / 0.

The `run_ttsl` function signature gains `Option<&dyn TtslLightEnv>` (defaulting to `None`).

**Opcode code generation**: New `"Light Accessors"` category in `low_level_def.py` with hand-written `rust_match_code` blocks (like `TT_TEXTURE`) that access the `light` env pointer.

### Phase 3: Engine integration

1. **`RustRenderContext`**: Add a `light_buffer` field (defaulting to an empty buffer or `None`).
2. **Per-frame view-space update**: In the render path, after the camera's view matrix is set and before material application, call `light_buffer.update_view_space(&transform_pack.view_matrix_3d)`. This mirrors how `glLightfv` transformed light data by the active modelview matrix.
3. **`ShaderMaterial::render_mat`**: Pass the light buffer reference to `run_ttsl` as `TtslLightEnv`.
4. **`DrawBuffer::apply_material_on`**: Thread the light buffer through to material application (same pattern as `TextureBuffer`).
5. **Python `RustRenderContext`**: Expose `light_buffer` property for assignment.

### Phase 4: Compiler support

1. **New built-in functions**: Register `tt_lightCount`, `tt_lightType`, `tt_lightColor`, `tt_lightDirection`, `tt_lightPosition`, `tt_lightAttenuation` in the compiler.
2. **Type inference**: `tt_lightCount()` → `int`, `tt_lightType(int)` → `int`, others → `vec3`.
3. **Code emission**: Lower each call to its corresponding opcode.
4. These are **not** `globals_dict` entries or implicit pixel vars — they are global callable built-ins (like `tt_texture`).

### Phase 5: Reference shader + demo

1. **Reference shader source**: A TTSL function implementing (see User-visible functionality above):
   - Ambient: `result += albedo * tt_lightColor(i)`
   - Directional (view-space): `L = tt_lightDirection(i)`, `result += albedo * color * max(dot(N, L), 0.0)`
   - Point (view-space): `L = tt_lightPosition(i) - tt_ViewPos`, distance attenuation, `result += albedo * color * max(dot(N, normalize(L)), 0.0) * atten`
2. **Demo app** (`demos/3d/ttsl_lighting.py`): A scene with a textured or colored model (e.g., cube or loaded OBJ), one ambient + one directional + one point light, rotating the object or moving the point light to show dynamic shading.

### Alternatives considered

- **Engine-level `tt_*` uniforms** (fixed `tt_AmbientColor`, `tt_DirLightDir` etc.): Rejected — doesn't scale to N lights; forces a fixed light layout into every shader's register seed.
- **Pure user uniforms per shader**: Rejected — too manual; every shader must wire its own light data; no reuse.
- **New Rust `LitMaterial` mode**: Deferred — could be a convenience wrapper that internally uses a compiled TTSL shader + LightBuffer.
- **World-space accessors (no auto-transform)**: Rejected — forces every shader to transform lights manually; inconsistent with the OpenGL convention where `glLightfv` handled the transform. The engine should do it once per frame.
- **Store only view-space in LightBuffer**: Rejected — users would need to re-transform lights every frame themselves. Storing world-space and auto-transforming is cleaner.

### Files likely touched

- `src/lightbuffer/mod.rs` (new) — `LightBuffer`, `LightSlot`, `LightType`, `update_view_space`, `TtslLightEnv` impl
- `src/lightbuffer/light_buffer_py.rs` (new) — PyO3 `LightBufferPy`
- `src/ttsl/mod.rs` — `TtslLightEnv` trait, `run_ttsl` signature update
- `src/ttsl/opcodes.rs` — auto-generated (new light opcodes)
- `src/material/shader_material.rs` — pass light env to `run_ttsl`
- `src/material/mod.rs` — `apply_material` gains light env parameter
- `src/drawbuffer/drawbuffer.rs` — thread light buffer through `apply_material_on`
- `src/lib.rs` — expose `LightBufferPy`, register `lightbuffer` module
- `python/tt3de/render_context_rust.py` — call `update_view_space` in render path, expose `light_buffer`
- `python/tt3de/ttsl/ttisa/low_level_def.py` — new opcode generators for light accessors
- `python/tt3de/ttsl/ttsl_assembly.py` — new `OpCodes` members
- `python/tt3de/ttsl/compiler.py` — light accessor built-in functions
- `python/tt3de/ttsl/ttisa/ttisa_opcodes.py` — auto-generated
- `source/opcode_reference.md` — auto-generated
- `source/ttsl.md` — new built-in functions section for light accessors
- `source/low_level_api.rst` — new LightBuffer section
- `source/high_level_api.rst` — brief lighting setup section
- `demos/3d/ttsl_lighting.py` (new) — lighting demo

## Usability and documentation

- **`source/low_level_api.rst`**: Add a "LightBuffer" section describing the slot data model, capacity, world-to-view auto-transform, and how it feeds into the shader path.
- **`source/ttsl.md`**: Add light accessor functions to the primitives table. Add a "Lighting" section explaining:
  - The view-space convention (matching `tt_Normal` and `tt_ViewPos`)
  - The `glLightfv`-style auto-transform (user sets world-space, shader reads view-space)
  - How to use accessors in a shader loop
  - Link to the reference shader
- **`source/high_level_api.rst`**: New "Lighting" subsection showing `LightBufferPy` setup.
- **Reference shader**: Documented example with inline comments explaining ambient, Lambert diffuse, and distance attenuation terms. Canonical "how to light things in tt3de" resource.
- **Demo**: `demos/3d/ttsl_lighting.py` — minimal, runnable, shows all three light types.

## Testability

- **LightBuffer unit tests** (Rust): Create, set slots, read back values, clear, verify count. Test `update_view_space` with a known view matrix (identity, 90° rotation, translation) and verify `view_direction` / `view_position` values.
- **Opcode unit tests** (Rust): Verify each `TT_LIGHT_*` opcode reads correct data from a mock `TtslLightEnv`. Test out-of-range index returns defaults.
- **View-space transform**: Unit test that `set_directional(_, _, world_dir=(0,0,-1))` with a 90° Y-rotation view matrix produces `view_direction = (-1, 0, 0)` (or equivalent).
- **Compiler tests** (Python): Compile shaders using `tt_lightCount()`, `tt_lightColor(0)`, etc. Verify bytecode generation succeeds.
- **E2E tests** (Python): A shader that reads light properties and returns them as pixel colors; verify output matches the configured LightBuffer after view-space transform.
- **Integration test**: Full render pipeline with a LightBuffer attached; verify that a triangle facing the directional light is brighter than one facing away.
- **Regression**: All existing tests pass. Shaders that don't use light accessors must be unaffected.

## Complexity and scope

| Phase | Size | Risk | Ships independently? |
|-------|------|------|---------------------|
| Phase 1: LightBuffer (Rust) | M | Low — new module, no existing code touched | Yes (inert until opcodes exist) |
| Phase 2: Accessor opcodes | M | Medium — `run_ttsl` signature change propagates | Yes, with Phase 1 |
| Phase 3: Engine integration | M | Medium — view-space auto-transform in render path, threading through apply_material | Requires Phase 1+2 |
| Phase 4: Compiler support | M | Medium — new built-in function category | Requires Phase 2 |
| Phase 5: Reference shader + demo | S | Low — pure TTSL + Python | Requires all above |

**Dependency**: This evolution depends on `evol-shader-math-normal` (`tt_Normal`, `tt_ViewPos`, smooth normals, `dot`, `normalize`, `length`, `max`, `clamp`) being shipped first.

**Rollback**: LightBuffer is additive. If it lands behind a feature flag or simply unused, existing behavior is unchanged.

## A priori performance analysis

**Hot paths**:

- **Light accessor opcodes**: For a reference shader with 3 lights and ~5 accessors per light = ~15 opcode dispatches per pixel. Each is a bounds-checked array index + field read. For 12K cells × 15 = ~180K accessor calls/frame. Sub-millisecond on modern CPUs.
- **Per-frame view-space update** (`update_view_space`): 16 lights × 2 matrix-vector multiplies (direction + position) = 32 operations per frame. Negligible.
- **LightBuffer memory**: 16 slots × ~120 bytes (world + view fields) ≈ 1.9 KB. L1 cache.
- **`run_ttsl` signature**: One extra `Option<&dyn Trait>` pointer-sized argument.

**Relative cost ranking** (cheapest → expensive):

1. Scene with no light buffer — zero overhead
2. Scene with 1–3 lights, reference shader — dominated by existing raster + shade
3. Scene with 16 lights, complex shader — ~80 extra dispatches per pixel; likely still not the bottleneck vs 1K–2K triangle rasterization at terminal resolution

**Validation**: Time `apply_material_on` with and without light accessors on a stress scene.

## Risks and open questions

- **`run_ttsl` signature change**: Adding `Option<&dyn TtslLightEnv>` touches every call site. Mitigate by bundling textures and lights into a single `TtslEnv` struct or trait.
- **TTSL loop support**: The reference shader needs to iterate over lights. If TTSL doesn't support `while` or `for` loops yet, the reference shader must unroll manually for a fixed count. Document this limitation. Loop support could be a separate evolution.
- **HDR and clamping**: Light color × albedo can exceed 1.0. The reference shader clamps to [0, 1] before output. The convention is: shaders are responsible for tone mapping / clamping.
- **Directional light direction convention**: In OpenGL, `GL_POSITION` with `w=0` is a direction *toward* the light (not from the light). The reference shader should document whether `tt_lightDirection` is "toward light" or "from light" — suggest "toward light" (positive dot product with N means lit).
- **Opcode numbering stability**: Adding opcodes shifts subsequent indices. Not a problem today (no bytecode persistence).
- **`TransformPack.environment_light`**: Existing unused field. Consider removing or repurposing it now that a proper LightBuffer exists, to avoid confusion.

## Decision record

- **Status**: draft
- **Coordinate space**: View space for shader computation. LightBuffer stores world-space data; engine auto-transforms to view space each frame using `view_matrix_3d`, following the OpenGL `glLightfv` convention.
- **Light delivery**: LightBuffer with per-property accessor opcodes (not plain uniforms).
- **Lighting model**: Reference TTSL shader, not a Rust `LitMaterial` mode.
- **Point lights enabled**: `tt_ViewPos` from prerequisite evolution provides the fragment position needed for distance/direction computation.
- **Direction convention**: `tt_lightDirection` returns the direction **toward** the light source (positive `dot(N, L)` = lit surface).
- **Resolution**: *(to be filled when closing)*

## References

- `.evolution/evol-shader-math-normal.md` — Prerequisite: `tt_Normal`, `tt_ViewPos`, smooth normals, `dot`, `normalize`, `length`, `max`, `clamp`
- `source/ttsl.md` — TTSL built-in variables and primitives
- `source/low_level_api.rst` — Pipeline overview, buffer descriptions, material modes
- `source/ttsl_compiler.md` — Compiler pipeline and extension guide
- `src/ttsl/mod.rs` — `TtslTextureEnv` trait (pattern for `TtslLightEnv`)
- `src/material/shader_material.rs` — Where `run_ttsl` is called with texture env
- `src/vertexbuffer/transform_pack.rs` — `TransformPack` with `view_matrix_3d` and unused `environment_light`
- `demos/3d/ttsl_fog.py` — Closest existing precedent (per-pixel shader with uniforms)
