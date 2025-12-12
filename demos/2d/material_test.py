# -*- coding: utf-8 -*-

from pyglm import glm
from textual.widgets import (
    Header,
)
from textual.app import App, ComposeResult
from tt3de.asset_fastloader import MaterialPerfab
from tt3de.points import Point2D, Point3D
from tt3de.textual.debugged_view import DebuggedView
from tt3de.textual_standalone import TT3DViewStandAlone

from tt3de.tt3de import find_glyph_indices_py, materials
from tt3de.tt3de.materials import ComboMaterialPy
from tt3de.tt_2dnodes import TT2DLines, TT2DNode, TT2DPolygon, TT2DUnitSquare


class DemoContent(TT3DViewStandAlone):
    def initialize(self):
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        self.root2Dnode = TT2DNode()

        matidx_front_tex0 = self.rc.material_buffer.add_base_texture(
            materials.BaseTexturePy(0)
        )
        matix_back_static_black = self.rc.material_buffer.add_static_color(
            materials.StaticColorPy(
                False, True, False, (0, 0, 0, 255), (0, 0, 0, 255), 0
            )
        )
        glyph = self.rc.material_buffer.add_static_color(
            materials.StaticColorPy(
                False,
                False,
                True,
                (0, 0, 0, 255),
                (0, 0, 0, 255),
                find_glyph_indices_py("#"),
            )
        )

        mat_idx = self.rc.material_buffer.add_combo_material(
            ComboMaterialPy.from_list(
                [glyph, matix_back_static_black, matidx_front_tex0]
            )
        )

        # adding line
        self.lines = TT2DLines(
            transform=glm.translate(glm.vec3(-0.5, -0.5, 0.0)),
            point_list=[Point3D(0, 0, 0), Point3D(1, 1, 0)],
            material_id=mat_idx,
        )
        self.root2Dnode.add_child(self.lines)
        self.lines = TT2DLines(
            transform=glm.translate(glm.vec3(-0.5, -0.5, 0.0)),
            point_list=[Point3D(0, 1, 0), Point3D(1, 0, 0)],
            material_id=mat_idx,
        )
        self.root2Dnode.add_child(self.lines)

        # adding a triangle
        self.triangle = TT2DPolygon(
            transform=glm.translate(glm.vec3(0.0, -1.0, -1.0)),
            point_list=[
                Point3D(-0.5, -0.5, 0),
                Point3D(0.0, 0.5, 0),
                Point3D(0.5, -0.5, 0),
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
        self.root2Dnode.add_child(self.triangle)

        self.unit_square = TT2DUnitSquare(
            transform=glm.translate(glm.vec3(0.0, 1.0, 0.0))
            * glm.scale(glm.vec3(0.8, 0.8, 1.0)),
            centered=True,
            material_id=7,
        )
        self.root2Dnode.add_child(self.unit_square)

        self.unit_square = TT2DUnitSquare(
            transform=glm.translate(glm.vec3(1.0, 1.0, 0.0))
            * glm.scale(glm.vec3(0.8, 0.8, 1.0)),
            centered=True,
            material_id=8,
        )
        self.root2Dnode.add_child(self.unit_square)

        self.unit_square = TT2DUnitSquare(
            transform=glm.translate(glm.vec3(2.0, 1.0, 0.0))
            * glm.scale(glm.vec3(0.8, 0.8, 1.0)),
            centered=True,
            material_id=10,
        )
        self.root2Dnode.add_child(self.unit_square)

        self.unit_square = TT2DUnitSquare(
            transform=glm.translate(glm.vec3(1.0, 0.0, 0.0))
            * glm.scale(glm.vec3(0.8, 0.8, 1.0)),
            centered=True,
            material_id=13,
        )
        self.root2Dnode.add_child(self.unit_square)

        self.unit_square = TT2DUnitSquare(
            transform=glm.translate(glm.vec3(2.0, 0.0, 0.0))
            * glm.scale(glm.vec3(0.8, 0.8, 1.0)),
            centered=True,
            material_id=14,
        )
        self.root2Dnode.add_child(self.unit_square)

        self.atlas_square = TT2DUnitSquare(
            transform=glm.translate(glm.vec3(3.0, 0.0, 0.0))
            * glm.scale(glm.vec3(0.8, 0.8, 1.0)),
            centered=True,
            material_id=24,
        )
        self.root2Dnode.add_child(self.atlas_square)

        self.rc.append_root(self.root2Dnode)

    def update_step(self, delta_time: float):
        self.unit_square.set_material_id(14 + (self.frame_idx // 30) % 10)
        self.atlas_square.set_material_id(24 + (self.frame_idx // 30) % 10)


class Material_Test(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DebuggedView(DemoContent())


if __name__ == "__main__":
    app = Material_Test()
    app._disable_tooltips = True
    app.run()
