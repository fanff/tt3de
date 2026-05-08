# -*- coding: utf-8 -*-
"""
3D primitives showcase for high_level_api.rst documentation screenshot.

Demonstrates Prefab3D shapes (triangle, square, circle), gizmo lines, and OBJ model
loading — the core 3D building blocks from the High Level API docs.
"""

import math

from pyglm import glm
from textual.app import App, ComposeResult

from tt3de.asset_fastloader import MaterialPerfab, fast_load
from tt3de.prefab3d import Prefab3D
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt_3dnodes import TT3DNode


class Primitives3DScene(TT3DViewStandAlone):
    """Scene showing Prefab3D primitives, gizmo, and a loaded OBJ model."""

    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

        root = TT3DNode()

        # --- Axis gizmo at origin ---
        root.add_child(Prefab3D.gizmo_lines())

        # --- Unitary triangle (left) ---
        tri = Prefab3D.unitary_triangle()
        tri.material_id = 6
        tri.local_transform = glm.translate(glm.vec3(-3.0, 0.0, 0.0))
        root.add_child(tri)

        # --- Unitary square (center-left) ---
        sq = Prefab3D.unitary_square()
        sq.material_id = 8
        sq.local_transform = glm.translate(glm.vec3(-1.2, 0.0, 0.0)) * glm.rotate(
            math.radians(20), glm.vec3(0, 1, 0)
        )
        root.add_child(sq)

        # --- Circle (center) ---
        circle = Prefab3D.unitary_circle(segment_count=12)
        circle.material_id = 9
        circle.local_transform = glm.translate(glm.vec3(0.8, 0.5, 0.0)) * glm.rotate(
            math.radians(-15), glm.vec3(1, 0, 0)
        )
        root.add_child(circle)

        # --- Loaded OBJ cube (right) ---
        cube = fast_load("models/cube.obj", flip_triangles=True)
        cube.material_id = 11
        cube.local_transform = (
            glm.translate(glm.vec3(3.0, 0.5, 0.0))
            * glm.rotate(math.radians(30), glm.vec3(0, 1, 0))
            * glm.rotate(math.radians(15), glm.vec3(1, 0, 0))
        )
        root.add_child(cube)

        self.rc.append_root(root)

        self.camera.move_at(glm.vec3(0.0, 2.5, -6.0))
        self.camera.point_at(glm.vec3(0.0, 0.3, 0.0))

    def update_step(self, delta_time: float):
        pass

    def post_render_step(self):
        pass


class Primitives3DDemoApp(App):
    """3D primitives documentation screenshot app."""

    TITLE = "TT3DE — 3D Primitives"

    DEFAULT_CSS = """
    Primitives3DDemoApp {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Primitives3DScene(target_fps=0)
