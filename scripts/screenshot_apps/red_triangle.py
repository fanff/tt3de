# -*- coding: utf-8 -*-

from pyglm import glm
from textual.app import App, ComposeResult

from tt3de.prefab3d import Prefab3D
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py
from tt3de.tt_3dnodes import TT3DNode


class RedTriangleView(TT3DViewStandAlone):
    """Single unit triangle with a static diffuse-red material (no BMP assets)."""

    def initialize(self):
        red_mat = self.rc.material_buffer.add_static(
            (200, 0, 0),
            (100, 100, 100),
            find_glyph_indices_py("R"),
        )

        root = TT3DNode()
        tri = Prefab3D.unitary_triangle()
        tri.material_id = red_mat
        tri.local_transform = glm.mat4(1.0)
        root.add_child(tri)
        self.rc.append_root(root)

    def update_step(self, delta_time: float):
        pass

    def post_render_step(self):
        pass


class RedTriangleDemoApp(App):
    """Fullscreen 3D view only — minimal chrome."""

    DEFAULT_CSS = """
    RedTriangleDemoApp {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield RedTriangleView(target_fps=0)
