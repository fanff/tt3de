
Low Level API
==============

Main Buffer Usage
-----------------

This section documents all core buffers used by the 3D engine.
Each buffer has a specific responsibility in the rendering pipeline and interacts
with others as the scene is transformed, rasterized, shaded, and drawn.


Transform Buffer
^^^^^^^^^^^^^^^^
Stores all 3D transformations required for rendering the scene.

This includes:

- Model transforms for every object in the scene
- Camera transformation
- Camera projection parameters (perspective or orthographic)

The transform buffer is consulted during the **Project & Clip** phase to position
all geometry correctly on screen.


Geometry Buffer
^^^^^^^^^^^^^^^
Stores all original 3D geometry data.

Contents typically include:

- Polygon, PolygonFan, Line, and Point primitives
- Vertex attributes such as:

  - Positions
  - Normals (if used)
  - UV texture coordinates
  - Any additional per-vertex metadata

Notes:

- Index **0** of the Geometry Buffer is reserved and intentionally ignored. It is never rendered by the `render_primitive` function.


Primitive Buffer
^^^^^^^^^^^^^^^^

Holds the **2D projected primitives** after transformation from 3D space to
screen space.

This buffer contains:

- Triangles
- Lines
- Points

These primitives are already clipped and ready for rasterization.


Texture Buffer
^^^^^^^^^^^^^^
Stores 2D texture data used by materials when shading pixels.

Textures typically contain:

- Diffuse color information
- Optional patterns or procedural images
- Images mapped via the object’s UV coordinates

Textures are referenced by entries in the **Material Buffer**.


Material Buffer
^^^^^^^^^^^^^^^
Defines how each object should appear when rendered.

Materials may specify:

- Flat colors
- Texture references
- Shading parameters
- Rules controlling how the **Pixel Shader** will interpret per-pixel data

Each geometry instance references a material entry to determine its final
appearance on screen.


Drawing Buffer
^^^^^^^^^^^^^^

Contains all final screen output information, separated into two primary parts:

Canvas:
    A 2D array of "ASCII art pixels", each storing:

    - Foreground color
    - Background color
    - Output glyph

    This represents the final rendered frame.

Depth Buffer:
    A parallel 2D array storing depth values for each pixel.
    Used to ensure correct visibility and occlusion.

Depth layer resolve
^^^^^^^^^^^^^^^^^^^

``DrawingBufferPy`` now supports two rendering models:

- ``legacy_layers=True`` (default): legacy ``DrawBuffer<2, f32>`` K-buffer-like
  resolve behavior for compatibility.
- ``legacy_layers=False``: two-pass model with one depth winner per pass.

New two-pass behavior (``legacy_layers=False``):

1. **Opaque pass** rasterizes non-transparent primitives into ``DrawBuffer<1, f32>``.
2. **Opaque material resolve** writes full ``CanvasCell`` state (front/back/glyph).
3. **Transparent pass** rasterizes transparent primitives into another
   ``DrawBuffer<1, f32>``.
4. **Transparent composite** blends only ``front_color`` onto the opaque canvas.

Blend/composite is centralized through ``BlendMode`` (``replace``,
``alpha_blend``, ``additive``, ``glyph_dither``, ``half_block_composite``),
while glyph behavior in transparent compositing is explicit through
``GlyphPolicy`` (``preserve_existing`` / ``replace_from_shader``).

Depth ordering of overlapping transparent primitives remains raster-order
dependent in this milestone (no transparent sort yet).

For comparison, classic OpenGL normally has one depth value per pixel. A
fragment passes or fails the depth test against that single value; if it passes,
it may blend its color into the framebuffer and update the depth buffer.
Transparent rendering is usually handled separately by drawing opaque geometry
first, then drawing transparent geometry back-to-front with blending enabled
and depth writes disabled, or by using advanced techniques such as depth
peeling, A-buffers, or K-buffers.


Material modes
--------------

Materials are entries in the **Material Buffer** that decide how each shaded
cell is filled. The Rust enum lives in ``src/material/materials.rs`` and is
exposed to Python through ``MaterialBufferPy`` (``src/material/mod.rs`` plus
``src/material/materials_py.rs``).

Most demos start from the bundled bank ``MaterialPerfab.rust_set_0()`` and
then add custom slots on top — that helper pre-populates slots ``0..14`` with
static colors, debug helpers, and textured prefabs (see
``python/tt3de/asset_fastloader.py`` for the exact contents). Custom slots are
appended in the order they are added; each ``add_*`` call returns the slot
index that ``material_id`` references on a node or mesh.

StaticColor
^^^^^^^^^^^

``StaticColor`` writes any subset of front color, back color, and glyph through
booleans:

- ``front``, ``back``, ``glyph`` — per-channel write toggles
- ``front_color``, ``back_color`` — ``(r, g, b, a)`` tuples in ``0..255``
- ``glyph_idx`` — index into the glyph palette (use ``find_glyph_indices_py``)

.. code-block:: python

    from tt3de.tt3de import find_glyph_indices_py, materials

    background = self.rc.material_buffer.add_static_color(
        materials.StaticColorPy(
            front=False, back=True, glyph=False,
            front_color=(0, 0, 0, 255),
            back_color=(0, 0, 0, 255),
            glyph_idx=0,
        )
    )

A faster shortcut for opaque ``(rgb, rgb, glyph)`` fills used in
``demos/2d/ttsl_square.py`` and ``demos/2d/bouncing_clock.py`` is
``MaterialBufferPy.add_static(front_rgb, back_rgb, glyph_idx)``.

BaseTexture
^^^^^^^^^^^

``BaseTexture`` is the modern texture-driven mode used by
``demos/3d/some_models.py`` and ``demos/3d/city_01.py`` /
``demos/3d/city_02.py``:

- channel toggles: ``front``, ``back``, ``glyph``
- per-channel UV source: ``front_uv_0``, ``back_uv_0``, ``glyph_uv_0``
  (``True`` picks the rasterizer's primary ``uv``; ``False`` picks ``uv_1`` so
  the back channel can read the second sample on a half-block ``▀`` cell)
- texture references: ``albedo_texture_idx`` (+ ``albedo_texture_subid``)
  for the color sample, ``glyph_texture_idx`` (+ ``glyph_texture_subid``)
  for the glyph-selection sample
- ``glyph_method`` — see `Glyph mapping methods`_ below

.. code-block:: python

    from tt3de.tt3de import find_glyph_indices_py, materials, toglyphmethod

    HALF_BLOCK = find_glyph_indices_py("▀")
    mat_id = self.rc.material_buffer.add_base_texture(
        materials.BaseTexturePy(
            albedo_texture_idx=tex_idx,
            albedo_texture_subid=0,
            glyph_texture_idx=0,
            glyph_texture_subid=0,
            front=True,
            back=True,
            glyph=True,
            glyph_uv_0=True,
            front_uv_0=True,
            back_uv_0=False,
            glyph_method=toglyphmethod.ToGlyphMethodPyStatic(HALF_BLOCK),
        )
    )

Textured (legacy)
^^^^^^^^^^^^^^^^^

``MaterialBufferPy.add_textured(albedo_texture_idx, glyph_idx)`` is the older
fast path: one albedo texture and a fixed glyph index — equivalent to a
``BaseTexture`` with all channel booleans set and ``ToGlyphMethodPyStatic``.
Prefer ``add_base_texture`` for new code so per-channel and per-UV control
stay explicit.

Shader (compiled TTSL)
^^^^^^^^^^^^^^^^^^^^^^

``ShaderPy`` runs compiled TTSL bytecode at material-application time so the
shader's return tuple ``(front: vec3, back: vec3, glyph: int)`` directly drives
the cell. See :doc:`ttsl` for the language surface and built-in / uniform
list.

The pattern used in ``demos/2d/ttsl_square.py``,
``demos/3d/ttsl_texture_cube.py``, ``demos/3d/ttsl_texture_half_block_cube.py``,
and ``demos/3d/ttsl_fog.py`` is:

1. compile once with ``all_passes_compilation(SHADER_SRC, "<entry>", globals_dict)``
2. seed material slot ``0`` with a plain static fill — ``RustRenderContext``
   uses ``material_id=0`` for cleared / sentinel depth samples, so any other
   choice runs the shader across the whole canvas
3. instantiate ``materials.ShaderPy(bytecode, ...)`` and add it via
   ``MaterialBufferPy.add_shader(...)``

.. code-block:: python

    from tt3de.tt3de import find_glyph_indices_py, materials
    from tt3de.ttsl.compiler import GLOBAL_VAR_TT_TIME, all_passes_compilation

    bytecode, reg_settings = all_passes_compilation(
        SHADER_SRC, "my_shader", {GLOBAL_VAR_TT_TIME: float}
    )
    _ty, time_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_TIME]

    # slot-0 sentinel fill (do not run TTSL on cleared cells)
    self.rc.material_buffer.add_static(
        (0, 0, 0), (0, 0, 0), find_glyph_indices_py(" ")
    )

    shader_mat = materials.ShaderPy(
        bytecode,
        time_f32_reg=time_reg,
        default_glyph=find_glyph_indices_py("█"),
        register_seed=reg_settings.get_register_list(),
    )
    self._shader_mat_id = self.rc.material_buffer.add_shader(shader_mat)

Optional ``ShaderPy`` keyword fields mirror the TTSL uniforms / per-pixel
inputs they feed: ``time_f32_reg``, ``delta_time_f32_reg``, ``frame_i32_reg``,
``resolution_v2_reg``, ``near_f32_reg``, ``far_f32_reg``,
``front_facing_bool_reg``, ``frag_depth_f32_reg``, ``line_coord_f32_reg``,
``point_coord_v2_reg``. Each register index comes from
``reg_settings.var_name_to_registers[<name>]`` after compilation.

In-place uniform updates avoid rebuilding the material:

.. code-block:: python

    def before_render_step(self):
        self.rc.material_buffer.set_shader_time(
            self._shader_mat_id, float(self.time_since_start())
        )

Matching helpers: ``set_shader_time``, ``set_shader_delta_time``,
``set_shader_frame``, ``set_shader_resolution``, ``set_shader_near``,
``set_shader_far``. These update **seed / uniform** registers only —
per-pixel inputs such as ``tt_FragCoord`` are written by the runtime each
shaded cell.

User-defined uniforms (any name other than the ``tt_*`` engine list) flow
through the ``register_seed`` snapshot. ``demos/3d/ttsl_fog.py`` reuses one
bytecode across three materials by cloning ``RegisterSettings``, calling
``set_variable("u_albedo", glm.vec3(...))`` on each clone, and reading
``get_register_list()`` for the matching ``ShaderPy``. Re-add (or rebuild) the
shader material when those values must change at runtime — there are no
``set_shader_*`` helpers for custom uniform names.

Debug helpers
^^^^^^^^^^^^^

``MaterialBufferPy.add_debug_depth(glyph_idx)`` and
``MaterialBufferPy.add_debug_uv(glyph_idx)`` expose visualization materials
backed by ``DebugDepth`` / ``DebugUV`` in Rust. Useful when inspecting
rasterizer output during pipeline debugging.

The Rust enum also defines ``Noise``, ``StaticGlyph``, and ``Custom`` variants
that are not fully surfaced in the Python wrapper today.

Glyph mapping methods
^^^^^^^^^^^^^^^^^^^^^

``BaseTexturePy.glyph_method`` controls how the glyph index is derived from the
glyph-source sample. The Python wrapper currently exposes:

- ``toglyphmethod.ToGlyphMethodPyStatic(glyph_idx)`` — always emit the same
  glyph (the common path; used by ``demos/3d/some_models.py``,
  ``demos/3d/city_01.py``, ``demos/3d/city_02.py``).
- ``toglyphmethod.ToGlyphMethodPyMap4Luminance((g0, g1, g2, g3))`` — sample
  the glyph texture, compute luminance, and map to one of four buckets.

The Rust side defines additional ``ToGlyphMethod`` variants (``FromAlpha``,
``Map4Color``) that are not yet bound from Python.


Overall Pipeline Flow
---------------------

When rendering a 3D scene, the engine processes data through a sequence of
operations. Each stage consumes one or more buffers and produces new data for
the next stage in the pipeline.

Conceptually:

- **Nodes (transform buffer)** define where things are positioned in 3D space.
- **Geometry + vertex data (geometry buffer)** define what the objects look like.
- **Project & Clip** transforms them into screen-space primitives.
- **Raster** converts primitives into pixel-level information.
- **Pixel Shader** applies textures and materials to produce final colors.
- The **Drawing Buffer** holds the completed frame.


Project & Clip
^^^^^^^^^^^^^^

Inputs:

- Node transforms (model, view, projection)
- Vertex data
- Geometry instances

Actions:

- Apply model, view, and projection matrices to all vertices
- Clip geometry against near/far planes and screen boundaries
- Produce 2D screen-space primitives (triangles, lines, points)
- Emit the results into the **Primitive Buffer**

Output:

- Filled Primitive Buffer with ready-to-rasterize primitives


Raster
^^^^^^

Inputs:

- Primitive Buffer

Actions:

- Convert primitives into pixel coverage by rasterization.
- Compute per-pixel attributes such as:

  - Depth
  - Barycentric coordinates
  - Interpolated normals
  - Interpolated UVs

- Store all per-pixel metadata in the **PixInfo** structure of the Drawing Buffer

Output:

- PixInfo buffer containing detailed per-pixel attributes


Pixel Shader
^^^^^^^^^^^^

Inputs:

- PixInfo buffer
- Material Buffer
- Texture Buffer

Actions:

- Determine which material applies to the pixel
- Sample textures when required by the material
- Compute the final shaded color
- Write the color (and glyph) to the Drawing Buffer’s **Canvas**

Output:

- Fully shaded Canvas representing the final frame


Where to see this in demos
--------------------------

- ``demos/2d/material_test.py``: material switching and glyph/textured output
- ``demos/3d/triangle_test.py``: primitive generation and simple material assignment
- ``demos/3d/some_models.py``: textured materials, model loading, and per-frame transforms
- ``demos/3d/city_01.py`` / ``demos/3d/city_02.py``: larger mesh workloads and camera movement context
