

High Level API
==============


Loading Materials
-----------------

Default Materials
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python


    from tt3de.asset_fastloader import MaterialPerfab
    from tt3de.textual_widget import StandAloneTT3DView

    class GLMTester(StandAloneTT3DView):

        def initialize(self):
            # prepare a bunch of material
            self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

            ... # Use the materials in your 3D scene by referencing their IDS


2D world
----------------

Adding Polygons
^^^^^^^^^^^^^^^^^^^^^

Adding Points
^^^^^^^^^^^^^^^^^^^^^

Adding Lines
^^^^^^^^^^^^^^^^^^^^^




3D world
----------------

Adding Polygons Mesh
^^^^^^^^^^^^^^^^^^^^^^^^^

Adding Points Cloud
^^^^^^^^^^^^^^^^^^^^^^^^^


Adding Lines
^^^^^^^^^^^^^^^^^^^^^^^^^

Loading 3D models
^^^^^^^^^^^^^^^^^^^^^^^^^
