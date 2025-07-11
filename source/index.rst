.. tt3de documentation master file

tt3de documentation
===================

TT3DE is a 3D engine built on top of the Textual library, designed to provide a simple and efficient way to render 3D graphics in Python applications.
It is particularly well-suited for creating interactive 3D visualizations and games running in a terminal environment.
The engine is designed to be easy to use and integrate into existing Textual applications, allowing developers to create rich 3D experiences with minimal effort.


How to use the engine
=====================

User can load and build the scene using specific python class and methods.
Those classes will take care of the buffer management and the rendering process.

The application is built using the Textual library, so the 3D engine is integrated into a Textual application as a widget.
The main class to use is the TT3DView, which is a subclass of Textual's Widget class.

Simple example on how to use the engine:

```python

from tt3de.asset_fastloader import MaterialPerfab
from tt3de.prefab3d import Prefab3D
from tt3de.textual_widget import TT3DView

class GLMTester(TT3DView):

    def initialize(self):
        # prepare a bunch of material
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        # create a root 3D node that will contain all the 3D objects
        self.root3Dnode = TT3DNode()

        # load a cube object from a .obj file
        cube = fast_load("models/cube.obj", reverse_uv_v=True)
        cube.material_id = 11
        cube.local_transform = glm.translate(glm.vec3(-4.1, 0, 0))
        # attach the cube to the root 3D node
        self.root3Dnode.add_child(cube)

    def update_step(self, timediff):
        ... # function executed every frame before rendering

    def post_render_step(self):
        ... # function executed after the rendering step

    async def on_event(self, event: events.Event):
        await super().on_event(event)

        ... # global event management

# define the Textual main application
class Demo3dView(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield GLMTester()

if __name__ == "__main__":
    app = Demo3dView()
    app._disable_tooltips = True
    app.run()

```


Main Buffer usage
=================

Here are the details on every buffer used in the 3D engine :

Transform Buffer : store the 3D transformation for every every objects in the scene as well as the Camera perspective & transformation

Gometry buffer : store the 3D geometry objects (Polygon, PolygonFan, Line, Point, etc.) vertex and attributes like uv coordinates.

Primitive Buffer : store the 2D objects primitive after the projection onto the screen (Triangle, Line, Point)


Texture Buffer : store the 2D texture to map onto the 3D geometry objects

Material Buffer : store the material information, this define how the 3D geometry objects will be rendered (flat color, texture, etc.)





.. toctree::
   :maxdepth: 2
   :caption: Contents:
