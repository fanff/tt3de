# -*- coding: utf-8 -*-
"""
2D primitives showcase for high_level_api.rst documentation screenshot.

Demonstrates TT2DPoints, TT2DLines, TT2DPolygon, and TT2DUnitSquare — the core 2D
building blocks described in the High Level API docs.
"""

from pyglm import glm
from textual.app import App, ComposeResult

from tt3de.asset_fastloader import MaterialPerfab
from tt3de.points import Point2D, Point3D
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt_2dnodes import (
    TT2DLines,
    TT2DNode,
    TT2DPoints,
    TT2DPolygon,
    TT2DUnitSquare,
)


class Primitives2DScene(TT3DViewStandAlone):
    """Scene showing all four 2D primitive types side by side."""

    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()

        root = TT2DNode()

        # --- Points cluster (left) ---
        for i, (x, y, mat) in enumerate(
            [
                (0.0, 0.0, 1),
                (0.3, 0.2, 2),
                (-0.3, 0.2, 3),
                (0.0, -0.3, 4),
                (0.15, 0.4, 2),
                (-0.15, -0.1, 3),
            ]
        ):
            root.add_child(
                TT2DPoints(
                    point_list=[Point3D(x - 2.5, y, 0.0)],
                    material_id=mat,
                )
            )

        # --- Line segments (center-left) ---
        root.add_child(
            TT2DLines(
                point_list=[Point3D(-1.2, -0.5, 0.0), Point3D(-0.5, 0.5, 0.0)],
                material_id=2,
            )
        )
        root.add_child(
            TT2DLines(
                point_list=[Point3D(-0.5, -0.5, 0.0), Point3D(-1.2, 0.5, 0.0)],
                material_id=3,
            )
        )
        root.add_child(
            TT2DLines(
                point_list=[Point3D(-1.2, 0.0, 0.0), Point3D(-0.5, 0.0, 0.0)],
                material_id=4,
            )
        )

        # --- Polygon / triangle (center-right) ---
        root.add_child(
            TT2DPolygon(
                point_list=[
                    Point3D(0.3, -0.5, 0.0),
                    Point3D(1.0, 0.5, 0.0),
                    Point3D(1.7, -0.5, 0.0),
                ],
                triangles=[(0, 1, 2)],
                uvmap=[
                    (
                        Point2D(0.0, 0.0),
                        Point2D(0.5, 1.0),
                        Point2D(1.0, 0.0),
                    )
                ],
                material_id=7,
            )
        )

        # --- Unit squares with different materials (right) ---
        for i, mat in enumerate([8, 9, 10]):
            root.add_child(
                TT2DUnitSquare(
                    transform=glm.translate(glm.vec3(2.2 + i * 0.9, -0.1, 0.0))
                    * glm.scale(glm.vec3(0.75, 0.75, 1.0)),
                    centered=True,
                    material_id=mat,
                )
            )

        self.rc.append_root(root)

    def update_step(self, delta_time: float):
        pass

    def post_render_step(self):
        pass


class Primitives2DDemoApp(App):
    """2D primitives documentation screenshot app."""

    TITLE = "TT3DE — 2D Primitives"

    DEFAULT_CSS = """
    Primitives2DDemoApp {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Primitives2DScene(target_fps=0)
