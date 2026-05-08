High Level API
==============

This page documents the "day-to-day" Python API used in the demos.
The intended workflow is:

1. create a ``TT3DViewStandAlone`` (or ``TT3DFpsView``) widget
2. initialize materials/textures and build a scene graph
3. append one or more root nodes to the render context
4. animate with ``update_step(delta_time)``
5. embed the view in a Textual ``App``


Minimal app structure
---------------------

.. code-block:: python

    from textual.app import App, ComposeResult
    from textual.widgets import Header
    from tt3de.textual_standalone import TT3DViewStandAlone

    class DemoView(TT3DViewStandAlone):
        def initialize(self):
            pass

        def update_step(self, delta_time: float):
            pass

    class DemoApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield DemoView()


Loading materials
-----------------

Default materials
^^^^^^^^^^^^^^^^^

Most demos start by loading a default texture/material set:

.. code-block:: python

    from tt3de.asset_fastloader import MaterialPerfab

    self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

Then assign ``material_id`` on each node/mesh.


Custom materials
^^^^^^^^^^^^^^^^

You can create material entries dynamically via ``material_buffer``:

.. code-block:: python

    from tt3de.tt3de import materials, find_glyph_indices_py

    half_block = find_glyph_indices_py("▀")
    mat_id = self.rc.material_buffer.add_base_texture(
        materials.BaseTexturePy(
            albedo_texture_idx=texture_idx,
            albedo_texture_subid=0,
            glyph_texture_idx=0,
            glyph_texture_subid=0,
            front=True,
            back=True,
            glyph=True,
            glyph_uv_0=True,
            front_uv_0=True,
            back_uv_0=False,
            glyph_method=...,
        )
    )


2D world
--------

Core classes
^^^^^^^^^^^^

- ``TT2DNode``: scene graph container node
- ``TT2DPoints``: points
- ``TT2DLines``: line segments
- ``TT2DPolygon``: polygon mesh + triangle index list
- ``TT2DUnitSquare``: utility quad primitive

Adding points and lines
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from tt3de.points import Point3D
    from tt3de.tt_2dnodes import TT2DNode, TT2DPoints, TT2DLines

    root = TT2DNode()
    root.add_child(TT2DPoints(point_list=[Point3D(0.0, 0.0, 0.0)], material_id=1))
    root.add_child(
        TT2DLines(
            point_list=[Point3D(-0.5, -0.5, 0.0), Point3D(0.5, 0.5, 0.0)],
            material_id=2,
        )
    )
    self.rc.append_root(root)

Adding polygons
^^^^^^^^^^^^^^^

``TT2DPolygon`` expects vertices, triangle indices, and optionally UVs:

.. code-block:: python

    from tt3de.points import Point2D, Point3D
    from tt3de.tt_2dnodes import TT2DPolygon

    poly = TT2DPolygon(
        point_list=[
            Point3D(-0.5, -0.5, 0.0),
            Point3D(0.0, 0.5, 0.0),
            Point3D(0.5, -0.5, 0.0),
        ],
        triangles=[(0, 1, 2)],
        uvmap=[(Point2D(0.0, 0.0), Point2D(0.5, 1.0), Point2D(1.0, 0.0))],
        material_id=7,
    )

Animating 2D nodes
^^^^^^^^^^^^^^^^^^

Use ``update_step`` to update transform/materials each frame:

.. code-block:: python

    from pyglm import glm

    def update_step(self, delta_time: float):
        t = self.time_since_start()
        x = glm.sin(t)
        y = glm.cos(t)
        self.some_node.set_local_transform(glm.translate(glm.vec3(x, y, 0.0)))


3D world
--------

Core classes
^^^^^^^^^^^^

- ``TT3DNode``: 3D scene graph container
- ``Prefab3D``: helper constructors for test geometry (triangle, square, gizmos, circle)
- ``fast_load(...)``: loads meshes/textures from files

Adding primitive meshes
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pyglm import glm
    from tt3de.prefab3d import Prefab3D
    from tt3de.tt_3dnodes import TT3DNode

    root = TT3DNode()
    tri = Prefab3D.unitary_triangle()
    tri.material_id = 6
    tri.local_transform = glm.translate(glm.vec3(0.0, 1.0, 0.0))
    root.add_child(tri)
    self.rc.append_root(root)

Loading models
^^^^^^^^^^^^^^

.. code-block:: python

    from tt3de.asset_fastloader import fast_load

    mesh = fast_load("models/cube.obj", reverse_uv_v=False, flip_triangles=True)
    mesh.material_id = 11
    self.root3Dnode.add_child(mesh)

Animating 3D nodes
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pyglm import glm

    def update_step(self, delta_time: float):
        self.cube.apply_transform(glm.rotate(delta_time, glm.vec3(0, 1, 0)))


Camera, debug view, and events
------------------------------

- ``DebuggedView(...)`` wraps a view and displays useful debug state.
- ``TT3DFpsView`` provides FPS-like navigation behavior.
- You can override ``on_event`` in your view for keyboard/mouse interactions.


Recommended reading order
-------------------------

1. ``demos/2d/standalone.py`` (smallest setup)
2. ``demos/2d/material_test.py`` (materials and geometry variety)
3. ``demos/3d/triangle_test.py`` (basic 3D primitives)
4. ``demos/3d/some_models.py`` (assets, texture materials, interaction)
