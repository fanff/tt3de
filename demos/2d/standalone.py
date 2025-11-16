# -*- coding: utf-8 -*-

from textual.widgets import (
    Header,
)
from textual.app import App, ComposeResult
from tt3de.asset_fastloader import MaterialPerfab
from tt3de.points import Point3D
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

        self.rc.append_root(self.root2Dnode)


class StandAloneDemo(App):
    DEFAULT_CSS = """

    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield DemoContent()


if __name__ == "__main__":
    app = StandAloneDemo()
    app._disable_tooltips = True
    app.run()
