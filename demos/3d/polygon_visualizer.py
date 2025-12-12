# -*- coding: utf-8 -*-
from time import time
from pyglm import glm

from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
)

from tt3de.asset_fastloader import MaterialPerfab


from tt3de.prefab3d import Prefab3D
from tt3de.textual.debugged_view import DebuggedView
from tt3de.textual_standalone import TT3DViewStandAlone

from tt3de.tt_3dnodes import TT3DNode


class PolygonVisualizer(TT3DViewStandAlone):
    def initialize(self):
        # prepare a bunch of material
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        # create a root 3D node
        self.root3Dnode = TT3DNode()
        gizmo = Prefab3D.gizmo_lines()
        self.root3Dnode.add_child(gizmo)

        gizmo_points = Prefab3D.gizmo_points()
        self.root3Dnode.add_child(gizmo_points)

        tri = Prefab3D.unitary_square()
        tri.material_id = 8
        tri.local_transform = glm.translate(glm.vec3(0.0, 1, 0))
        self.root3Dnode.add_child(tri)

        poly = Prefab3D.unitary_circle(5)
        poly.material_id = 8
        poly.local_transform = glm.translate(glm.vec3(1.1, 0, 0))
        self.root3Dnode.add_child(poly)
        #
        # poly = Prefab3D.unitary_circle(12)
        # poly.material_id = 8
        # poly.local_transform = glm.translate(glm.vec3(1.1, 1.1, 0))
        # self.root3Dnode.add_child(poly)
        #
        # poly = Prefab3D.unitary_circle(24)
        # poly.material_id = 8
        # poly.local_transform = glm.translate(glm.vec3(1.1, 2.1, 0))
        # self.root3Dnode.add_child(poly)

        # final append
        self.rc.append_root(self.root3Dnode)

        # setup a time reference, to avoid trigonometry issues
        self.reftime = time()


class Demo3dView(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DebuggedView(PolygonVisualizer())


if __name__ == "__main__":
    app = Demo3dView()
    app._disable_tooltips = True
    app.run()
