.. tt3de documentation master file

tt3de documentation
===================

TT3DE is a 3D engine built on top of the Textual library, designed to provide a simple and efficient way to render 3D graphics in Python applications.
It is particularly well-suited for creating interactive 3D visualizations and games running in a terminal environment.
The engine is designed to be easy to use and integrate into existing Textual applications,
allowing developers to create rich 3D experiences with minimal effort.

Engine Status & Roadmap Overview
======================================


This project is a deliberately CPU-only, software-based 3D rendering engine designed around a classical rasterization pipeline.
Its current architecture is built on triangle-based geometry,
with the additional constraint that total scene complexity remains intentionally small—typically dozens of triangles per object,
and a modest number of objects.


How to use the engine
=====================

User can load and build the scene using specific python class and methods.
Those classes will take care of the buffer management and the rendering process.

The application is built using the Textual library, so the 3D engine is integrated into a Textual application as a widget.


Simple example on how to use the engine:


.. code-block:: python


    from tt3de.asset_fastloader import MaterialPerfab
    from tt3de.prefab3d import Prefab3D
    from tt3de.textual_widget import StandAloneTT3DView

    class GLMTester(StandAloneTT3DView):

        def initialize(self):
            # prepare a bunch of material
            self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
            # create a root 3D node that will contain all the 3D objects
            self.root3Dnode = TT3DNode()

            # load a cube object from a .obj file
            cube = fast_load("models/cube.obj")
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
        app.run()




.. toctree::
   :maxdepth: 3
   :caption: Contents:
   :hidden:

   high_level_api
   low_level_api
   ttsl
