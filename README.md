

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

## Known issues 


* [ ] the line distance calculation is buggy for pure vertical lines
* [ ] triangle selection when drawing is too restrictive.
* [ ] triangle front/back culling 
* [ ] shading based on normal to surface
