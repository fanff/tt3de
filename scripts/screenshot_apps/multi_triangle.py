# -*- coding: utf-8 -*-
"""Taxi car 3D model loaded from OBJ + BMP (doc screenshot scene)."""

from pyglm import glm
from textual.app import App, ComposeResult

from tt3de.asset_fastloader import MaterialPerfab, fast_load
from tt3de.prefab3d import Prefab3D
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt_3dnodes import TT3DNode


class TaxiModelScene(TT3DViewStandAlone):
    """Car5_Taxi OBJ with texture and a 3-axis gizmo for spatial context."""

    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

        root = TT3DNode()
        root.add_child(Prefab3D.gizmo_lines())

        taxi = fast_load(
            "models/car/Car5_Taxi.obj", reverse_uv_v=False, flip_triangles=True
        )
        taxi.material_id = 12
        taxi.local_transform = glm.translate(glm.vec3(0, 0, 0))
        root.add_child(taxi)

        self.rc.append_root(root)

        self.camera.move_at(glm.vec3(3.0, 2.5, -4.0))
        self.camera.point_at(glm.vec3(0.0, 0.5, 0.0))

    def update_step(self, delta_time: float):
        pass

    def post_render_step(self):
        pass


class TaxiModelDemoApp(App):
    """Fullscreen taxi model view."""

    DEFAULT_CSS = """
    TaxiModelDemoApp {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield TaxiModelScene(target_fps=0)
