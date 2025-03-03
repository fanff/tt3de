# -*- coding: utf-8 -*-
from time import time
import glm

from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
)

from tt3de.asset_fastloader import MaterialPerfab


from tt3de.prefab3d import Prefab3D
from tt3de.textual_widget import TT3DView

from tt3de.tt_3dnodes import TT3DNode


class GLMTester(TT3DView):
    def __init__(self):
        super().__init__()

    def initialize(self):
        # prepare a bunch of material
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        # create a root 3D node
        self.root3Dnode = TT3DNode()

        tri = Prefab3D.unitary_square()
        tri.material_id = 8
        tri.local_transform = glm.translate(glm.vec3(-1.1, 1, 0))
        self.root3Dnode.add_child(tri)

        poly = Prefab3D.unitary_circle(5)
        poly.material_id = 8
        poly.local_transform = glm.translate(glm.vec3(1.1, 0, 0))
        self.root3Dnode.add_child(poly)

        poly = Prefab3D.unitary_circle(12)
        poly.material_id = 8
        poly.local_transform = glm.translate(glm.vec3(1.1, 1.1, 0))
        self.root3Dnode.add_child(poly)

        poly = Prefab3D.unitary_circle(24)
        poly.material_id = 8
        poly.local_transform = glm.translate(glm.vec3(1.1, 2.1, 0))
        self.root3Dnode.add_child(poly)

        # final append
        self.rc.append(self.root3Dnode)

        # setup a time reference, to avoid trigonometry issues
        self.reftime = time()

    def update_step(self, timediff):
        pass

    def post_render_step(self):
        pass


class Demo3dView(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield GLMTester()


if __name__ == "__main__":
    app = Demo3dView()
    app._disable_tooltips = True
    app.run()
