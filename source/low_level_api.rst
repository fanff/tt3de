
Low Level API
==============

Main Buffer Usage
=================

This section documents all core buffers used by the 3D engine.
Each buffer has a specific responsibility in the rendering pipeline and interacts
with others as the scene is transformed, rasterized, shaded, and drawn.


Transform Buffer
----------------
Stores all 3D transformations required for rendering the scene.

This includes:

- Model transforms for every object in the scene
- Camera transformation
- Camera projection parameters (perspective or orthographic)

The transform buffer is consulted during the **Project & Clip** phase to position
all geometry correctly on screen.


Geometry Buffer
---------------
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
----------------

Holds the **2D projected primitives** after transformation from 3D space to
screen space.

This buffer contains:

- Triangles
- Lines
- Points

These primitives are already clipped and ready for rasterization.


Texture Buffer
--------------
Stores 2D texture data used by materials when shading pixels.

Textures typically contain:

- Diffuse color information
- Optional patterns or procedural images
- Images mapped via the object’s UV coordinates

Textures are referenced by entries in the **Material Buffer**.


Material Buffer
---------------
Defines how each object should appear when rendered.

Materials may specify:

- Flat colors
- Texture references
- Shading parameters
- Rules controlling how the **Pixel Shader** will interpret per-pixel data

Each geometry instance references a material entry to determine its final
appearance on screen.


Drawing Buffer
--------------

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


Overall Pipeline Flow
=====================

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
--------------

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
------

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
------------

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
