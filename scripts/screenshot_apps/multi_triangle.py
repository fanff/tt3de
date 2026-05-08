# -*- coding: utf-8 -*-

from pyglm import glm
from textual.app import App, ComposeResult

from tt3de.prefab3d import Prefab3D
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py
from tt3de.tt_3dnodes import TT3DNode


class MultiTriangleScene(TT3DViewStandAlone):
    """Three flat-shaded triangles, no BMP assets."""

    def initialize(self):
        red = self.rc.material_buffer.add_static(
            (200, 40, 40),
            (80, 80, 80),
            find_glyph_indices_py("R"),
        )
        green = self.rc.material_buffer.add_static(
            (40, 200, 40),
            (80, 80, 80),
            find_glyph_indices_py("G"),
        )
        blue = self.rc.material_buffer.add_static(
            (60, 60, 200),
            (80, 80, 80),
            find_glyph_indices_py("B"),
        )

        root = TT3DNode()

        t1 = Prefab3D.unitary_triangle()
        t1.material_id = red
        t1.local_transform = glm.translate(glm.vec3(-1.15, 0.9, 0.0))

        t2 = Prefab3D.unitary_triangle()
        t2.material_id = green
        t2.local_transform = glm.translate(glm.vec3(0.05, 0.9, 0.0))

        t3 = Prefab3D.unitary_triangle()
        t3.material_id = blue
        t3.local_transform = glm.translate(glm.vec3(1.25, 0.9, 0.0))

        root.add_child(t1)
        root.add_child(t2)
        root.add_child(t3)
        self.rc.append_root(root)

    def update_step(self, delta_time: float):
        pass

    def post_render_step(self):
        pass


class MultiTriangleDemoApp(App):
    DEFAULT_CSS = """
    MultiTriangleDemoApp {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield MultiTriangleScene(target_fps=0)
