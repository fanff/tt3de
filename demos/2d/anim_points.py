# -*- coding: utf-8 -*-

from pyglm import glm
from textual.widgets import (
    Header,
)
from textual.app import App, ComposeResult
from tt3de.asset_fastloader import MaterialPerfab
from tt3de.points import Point3D
from tt3de.textual.debugged_view import DebuggedView
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt_2dnodes import TT2DNode, TT2DPoints


class DemoContent(TT3DViewStandAlone):
    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

        self.root2Dnode = TT2DNode()
        self.root2Dnode.add_child(
            TT2DPoints(point_list=[Point3D(0.0, 0.0, 0)], material_id=1)
        )
        self.root2Dnode.add_child(
            TT2DPoints(point_list=[Point3D(1, 0.0, 0)], material_id=2)
        )
        self.root2Dnode.add_child(
            TT2DPoints(point_list=[Point3D(0.0, 1, 0)], material_id=3)
        )

        self.moving_point = TT2DPoints(point_list=[Point3D(0.2, 0.1, 0)], material_id=3)
        self.root2Dnode.add_child(self.moving_point)

        self.rc.append_root(self.root2Dnode)

    def update_step(self, delta_time: float):
        t = self.time_since_start() * 2
        x = glm.sin(t * 0.7)
        y = glm.cos(t * 1.3)
        self.moving_point.set_local_transform(glm.translate(glm.vec3(x, y, 0.0)))


class CameraTest2D(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DebuggedView(DemoContent())


if __name__ == "__main__":
    app = CameraTest2D()
    app._disable_tooltips = True
    app.run()
