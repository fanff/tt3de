---
hide-toc: true
---

Tiny Tiny Shader Language (TTSL)
=================================


Variables list [TODO]
---------------------


| Name               | Type  | Range / Units                          | Description |
|--------------------|-------|----------------------------------------|-------------|
| tt_FragCoord       | vec2  | x:[0..res.x-1], y:[0..res.y-1]         | Window-space cell coordinate of the current shaded cell. Equivalent to gl_FragCoord.xy (cell-level, integer-like). |
| tt_FragPos         | vec2  | [-1..1]                                | Normalized device-space position of the cell center. Equivalent to gl_Position → NDC mapping for fragments. |
| tt_Resolution      | vec2  | (width_cells, height_cells)            | Size of the render target in cells. Analogous to framebuffer resolution queries. |
| tt_PrimitiveID     | int   | [0..N-1]                               | ID of the primitive that generated this cell. Mirrors gl_PrimitiveID. |
| tt_FrontFacing     | bool  | true / false                           | True if the primitive is front-facing under current winding rules. Mirrors gl_FrontFacing. |
| tt_TexCoord0       | vec2  | typically [0..1] (convention-defined)  | First interpolated texture coordinate set. Equivalent to a user-defined in vec2 or legacy gl_TexCoord[0]. |
| tt_TexCoord1       | vec2  | typically [0..1] (convention-defined)  | Second interpolated texture coordinate set. Equivalent to gl_TexCoord[1] / multi-UV workflows. |
| tt_Time            | float | seconds (>= 0)                         | Elapsed time since start. Common engine uniform, analogous to user-defined time uniforms in GLSL. |
| tt_DeltaTime       | float | seconds (>= 0)                         | Time between frames. Not a GLSL built-in, but standard real-time shader uniform. |
| tt_Frame           | int   | [0..]                                  | Frame counter. Analogous to application-provided frame index uniforms. |
| tt_PointCoord      | vec2  | [0..1]                                 | Coordinates within a rasterized point sprite. Mirrors gl_PointCoord. Only valid for point primitives. |
| tt_LineCoord       | float | [0..1]                                 | Parametric coordinate along a rasterized line. GLSL-adjacent (no direct built-in), but follows naming conventions. |
| tt_FragDepth       | float | [0..1] or [-1..1] (engine-defined)     | Depth value of the current cell. Mirrors gl_FragDepth semantics (read-only unless you allow writes). |


## Primitives


| Function (GLSL-style) | Typical signatures (examples) | What it’s for | Notes / ranges |
|---|---|---|---|
| mix | mix(a, b, t) -> T | Linear interpolation (lerp) | `t` usually [0..1], works on float/vec2/vec3/vec4 |
| clamp | clamp(x, lo, hi) -> T | Clamp into a range | Great for keeping colors in [0..1] |
| min / max | min(a,b)->T, max(a,b)->T | Bounds / compare | Works component-wise on vectors |
| smoothstep | smoothstep(e0, e1, x) -> T | Smooth threshold | Hermite curve; output in [0..1] when e0<e1 |
| step | step(edge, x) -> T | Hard threshold | Returns 0 or 1 (component-wise) |
| abs / sign | abs(x)->T, sign(x)->T | Magnitude / sign | `sign(0)=0` |
| floor / ceil / fract | floor(x)->T, ceil(x)->T, fract(x)->T | Tiling, patterns, quantization | `fract(x)=x-floor(x)` in [0..1) |
| mod | mod(x, y) -> T | Periodic wrap | For floats (GLSL-style); component-wise |
| pow | pow(x, y) -> T | Curves / gamma-like shaping | Be careful with negative bases |
| sqrt / inversesqrt | sqrt(x)->T, inversesqrt(x)->T | Lengths, normalization helpers | `x` should be >= 0 for real sqrt |
| exp / log | exp(x)->T, log(x)->T | Exponential / logarithmic shaping | Useful for tone mapping-ish curves |
| sin / cos / tan | sin(x)->T, cos(x)->T, tan(x)->T | Oscillation / waves | Input in radians |
| asin / acos / atan | asin(x)->T, acos(x)->T, atan(y,x)->T | Angles from values | `asin/acos` domain [-1..1] |
| radians / degrees | radians(deg)->T, degrees(rad)->T | Unit conversion | Convenience |
| dot | dot(a,b)->float | Lighting, projections | For vec2/vec3/vec4 |
| cross | cross(a,b)->vec3 | Perpendicular vector | Only vec3 |
| length | length(v)->float | Vector magnitude | |
| distance | distance(a,b)->float | Metric distance | |
| normalize | normalize(v)->T | Unit-length vector | Undefined for zero-length vectors (decide your behavior) |
| reflect | reflect(I, N)->T | Reflection vector | `N` should be normalized |
| refract | refract(I, N, eta)->T | Refraction vector | `eta` is n1/n2; returns 0-vector on total internal reflection (GLSL behavior) |
| faceforward | faceforward(N, I, Nref)->T | Choose normal orientation | Helps ensure N faces viewer/light |
| any / all | any(bvec)->bool, all(bvec)->bool | Boolean reductions | For vector bools if you have them (or emulate) |
| lessThan / greaterThan / equal / notEqual | lessThan(a,b)->bvec, equal(a,b)->bvec | Vector comparisons | If you don’t have bvec types, you can omit or return bool via `all()` patterns |
| isnan / isinf | isnan(x)->bvec/bool, isinf(x)->bvec/bool | Robustness / debugging | Optional but handy in shader languages |
| fma | fma(a,b,c)->T | Fused multiply-add | If available, improves precision/perf |
| dFdx / dFdy | dFdx(x)->T, dFdy(x)->T | Screen-space derivatives | Niche but powerful; needs neighbor access (per 2x2 quad concept) |
| fwidth | fwidth(x)->T | `abs(dFdx)+abs(dFdy)` | Great for anti-aliased lines/signed-distance fields (SDF) style edges |
| round / trunc | round(x)->T, trunc(x)->T | Quantization | Optional; useful for glyph selection / palette quantization |
| frexp / ldexp | frexp(x, out exp)->T, ldexp(x, exp)->T | Mantissa/exponent ops | Very niche; can skip unless you want full GLSL parity |
| bitwise (int) | & \| ^ ~ << >> | Masks, packing, hashing | If your “int” is real int, these are very useful for RNG/patterns |
