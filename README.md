

# TinyTiny 3d Engine 

A minimalistic 2D/3D engine implemented in Python/Cython, designed to render 3D objects using ASCII art.

# Features

* **Rendering Primitives**: Supports points, lines, and triangles in 2D & 3D Context.
* **ASCII Output**: Renders the 3D scenes in a charming ASCII art style.
* **Color Shading support**: Render with RGB colors and Shading level.
* **Materials**: Support 14 Materials including :
    * **Texture Mapping**: Support 32x32 texture bmp & 8 UV layers per faces. 
    * **Double Raster**: Allow to use 2 colors per ascii character (back & front)
    * **PerlinNoise**: Basic Perlin Noise mapped texture




Magic command to build the cython code locally : 

```bash 
python setup.py build_ext --inplace
```


## testing *

```bash 
poetry run python demos\2d\texture_tests.py

```



### trick for pythonpath 


on windows

```bat
set PYTHONPATH=%CD%;%PYTHONPATH%
```

on vscode  launch.josn

```
"env": {"PYTHONPATH":"${workspaceFolder}"}
```



## C Engine structure 

The Cython engine uses 5 elementary buffers to work:

* DrawingBuffer: Store the depth buffer & the canvas buffer. 
* GeometryBuffer: store a geometry to draw, Point/line/triangle obviously, but could be a Sphere, Cube, Ribon ... 
* PrimitivesBuffer: store an atomic element for drawing. here, only point/line/triangle.
* MaterialBuffer: Store how your geometry is painted. Can be static color / texture application, or combo of it.   
* TextureBuffer: Store basically the array of pixels of a 2D texture. Its an image, basically with rgb value 

The rendering process goes as follow:

1. The Geometry buffer is filled after the projection stage. 
2. [PrimitiveAssembly] : every geometry goes from GeometryBuff into Primitives. There a filter can apply to clip the primitive in screen. One Geometry can generate any number of Primitives.
3. [Rasterization] : Find what pixel to light for every primitive. It goes from the Primitive buffer into the depth buffer.
4. [MaterialApplication] : For every painted pixel in the depth buffer, the associated material is called to define and put the color is the canvas buffer.


## DrawingBuffer

Is constituted of two buffer, each with the screen [width x height]  dimension

1. [CanvasBuffer] : store the ascii pixel information in 8 bytes:
    * 3 bytes for the front color
    * 3 bytes for the back color
    * 1 bytes for the "glyph"     (the actual visible character on the screen)
    * 1 bytes for the "glyph mode"   (bold , italic, underline etc.. )

2. [DepthBuffer] : store per pixel information
    * 1 float for the depth
    * 3 float to hold per pixel informations
    * 4 int  , referencing the node_id, geometry_id, primitive_id, material_id.  




The depth buffer is cleaned at each frame.
The rasterizer will fill the DepthBuffer while parsing the primitives
The MaterialApplication parse the DepthBuffer and fill the CanvasBuffer. 





## Status of the full process :

Not covered in C , its python :



[Vertex Shader]: This stage processes each vertex individually. It transforms the vertices from model space to world space, and then to view space (camera space).

[Clipping]: After the vertices have been transformed by the vertex shader, they are in view space. Clipping is performed to ensure that only the parts of the geometry that are within the view frustum (the visible region of the 3D space) are processed further. This includes clipping against the near and far planes, as well as the sides of the view frustum.

[Projection]: Once clipping is done, the vertices are projected from 3D view space to 2D screen space. This involves applying the perspective or orthographic projection matrix, which converts the 3D coordinates into normalized device coordinates (NDC).

This is in Cython.


[PrimitiveAssembly] : The clipped and projected vertices are then assembled into geometric primitives (triangles, lines, points) that can be rasterized. there the face culling happen.

[Rasterization] : The primitives are then converted into fragments (potential pixels), which are processed by the fragment shader.

[MaterialApplication] : This stage processes each fragment to determine its final color and other attributes.



## Rust version test. 

How to setup 

* git clone this repo somewhere 
* if you have poetry just run `poetry install`
* if you don't have poetry 

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install poetry 
poetry install 
```

* Now compile the Rust stuff with `maturin develop` 
* The unit test of the rtt3de should work


### Ideas 


**Static Immediate Render**

* This is a mode within the "PrimitiveBuffer". 
* It accept one single number from 0..1024. + Row & Column for locating + a "material" ; wich will provide the coloring we want. 
* Each number correspond to a cell in the `models\sprite_sheet_8px.bmp`. (the sheet it 256x256 pix;  each cell is 8x8 , there is 32 row, 32 cols =1024 cell with small sprite in it.)

*at compile time*

* Each cell is converted to severals static functions, containing the minimal code to raster the cell, (all pixel that are not black basically). 
* the function should accept parameter; like the color we pick. 

* Because we render in ascii mode, several mode of raster can be picked; 
  * 1:1 mode:    consider the ascii pixel as one full pixel. we replace in the canvas the full block. (more detail bellow)

  * 1:2 mode (or double raster mode) : consider the ascii pixel as 2 full pixel. the canvas will contains the "half-block UPPer"; the back and front color make the bottom/top color respectivelly. 
  In this mode; the tricky part is when it is necessary to change only half of the ascii char.  Depending on where you blit (top/bottom) the other one might need to be updated as well. 

   
Extra for the 1:1 Mode: 

* In this mode we "redraw" the whole ascii char; there we can take some flexibility to have a specific "glyph" or set of glyph. 
* For instance; consider drawing a square of  3px X 3px , the middle pix beeing transparent. 
    * It can be raster with blocks brackets '┌' "┑" etc ..  ; 
    * or other blocks  like : "▛▀▜" etc.. 

* being able to swith mode quickly is key; because it allows some kind of animation; keeping the same "sprite" ; just changing its "way of prining". 





Usage of this mode: 

The user can instanciate (in py) a special "2DNode" that represent sprites we want to render with this mode. Typical targets are: 

* UI text subject to change; but forcibly readable. Think about a hud in flying sim; or the "gold level" in Warcraft 1 ; 
* Mouse Cursor; always over everything





The user set the material, and list of glyph and a vertexidx we want to blit on. All Cached in the MaterialBuffer, & VertexBuffer & Geometry buffer. Just like normal object. 

when the render goes; 
* Geometry makes primitive; (and apply necessary clipping)
* Primitive are rasterized (but not the Static one yet; they are kept for later)
* Pixel shader apply (all the rest is colorized correctly)
* StaticPrimitive apply : -> now the Static apply kickin. 


