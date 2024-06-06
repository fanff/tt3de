

# TinyTiny 3d Engine 

A minimalistic 3D engine implemented entirely in Python, designed to render 3D objects using ASCII art.

# Features

* **Pure Python Implementation**: No external dependencies, making it easy to understand and extend.
* **Rendering Primitives**: Supports points, lines, and triangles.
* **ASCII Output**: Renders the 3D scenes in a charming ASCII art style.
* **Color Shading support**: Render with RGB colors and Shading level.

# Usage

Here’s a basic example to get you started:

```python


class MyView(TT3DView):
    def __init__(self):
        super().__init__()

    def initialize(self):
        self.rc.extend(build_arrows(Point3D(0, 0, 0)))
        for i in range(3):
            self.rc.extend(get_cube_vertices(Point3D(0, i, 0), 0.7,DistGradBGShade))
        self.rc.extend(get_cube_vertices(Point3D(2, 0, 0), 0.7,  DistGradBGShade))
        self.rc.extend(get_cube_vertices(Point3D(3, 0, 0), 0.7,  DistGradBGShade))
        self.rc.extend(get_cube_vertices(Point3D(1, 0, 0), 0.7,  DistGradBGShade))


        self.write_debug_inside=True
    def update_step(self,timediff):
        ts = monotonic()
        amp = 4
        tf = 0.8
        c1 = math.cos(tf * ts) * amp
        c2 = math.sin(tf * ts) * amp
        self.camera.move_at(Point3D(c1, 1 + math.cos(tf * ts / 2) * 3, c2))
        self.camera.point_at(Point3D(0.0, 0, 0))
        self.camera.recalc_fov_h(self.size.width, self.size.height)
        self.rc.update_wh(self.size.width, self.size.height)
    def post_render_step(self):


        spark:Sparkline = self.parent.query_one(".tsrender_dur")
        spark.data = spark.data[1:] + [self.last_frame_data_info.get("tsrender_dur",0)]
        l:Label = self.parent.query_one(".frame_idx")
        l.update(f"Frame: {self.frame_idx}")


        l:Label = self.parent.query_one(".render_label")
        l.update(f"Render: {(1000*mean(spark.data)):.2f} ms")
        #.update(str(self.last_frame_data_info))

    async def on_event(self,event:events.Event):
        # await super().on_event(event)
        info_box:Static= self.parent.query_one(".lastevent")
        info_box.update(str(event))
        
```


## C Engine structure 

The Cython engine uses 5 elementary buffers to work:

* Drawing: Store the depth buffer & the canvas buffer. 
* Geometry: store a geometry to draw, Point/line/triangle obviously, but could be a Sphere, Cube, Ribon ... 
* Primitives: store an atomic element for drawing. here, only point/line/triangle.
* Material: Store how your geometry is painted. Can be static color / texture application, or combo of it.   
* Textures: Store basically the array of pixels of a 2D texture. Its an image, basically. 

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


