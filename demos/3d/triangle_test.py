# -*- coding: utf-8 -*-

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


class GLMTester(TT3DViewStandAlone):
    def initialize(self):
        # prepare a bunch of material
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        # create a root 3D node
        self.root3Dnode = TT3DNode()

        self.root3Dnode.add_child(Prefab3D.gizmo_points())

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 5
        tri.local_transform = glm.translate(glm.vec3(-1.1, 1, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 6
        tri.local_transform = glm.translate(glm.vec3(0, 1, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 7
        tri.local_transform = glm.translate(glm.vec3(1.1, 1, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 8
        tri.local_transform = glm.translate(glm.vec3(0, 2, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 9
        tri.local_transform = glm.translate(glm.vec3(1.1, 2, 0))
        self.root3Dnode.add_child(tri)

        tri = Prefab3D.unitary_triangle()
        tri.material_id = 10
        tri.local_transform = glm.translate(glm.vec3(-1.1, 2, 0))
        self.root3Dnode.add_child(tri)

        # final append
        self.rc.append_root(self.root3Dnode)


class Demo3dView(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DebuggedView(GLMTester())


if __name__ == "__main__":
    app = Demo3dView()
    app._disable_tooltips = True
    app.run()
