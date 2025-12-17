# -*- coding: utf-8 -*-
import math

from pyglm import glm

from textual import events
from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Static,
)
from textual.css.query import NoMatches

from tt3de.asset_fastloader import MaterialPerfab, fast_load


from tt3de.prefab3d import Prefab3D
from tt3de.richtexture import ImageTexture
from tt3de.textual.debugged_view import DebuggedView
from tt3de.textual_standalone import TT3DViewStandAlone

from tt3de.tt3de import find_glyph_indices_py, materials
from tt3de.tt_3dnodes import TT3DNode
from tt3de.tt3de import toglyphmethod


class GLMTester(TT3DViewStandAlone):
    use_native_python = False

    def __init__(self):
        super().__init__(
            vertex_buffer_size=8192,
            use_left_hand_perspective=False,
        )

    def initialize(self):
        # prepare a bunch of material
        self.rc.texture_buffer, self.rc.material_buffer = MaterialPerfab.rust_set_0()
        # create a root 3D node
        self.root3Dnode = TT3DNode()

        self.root3Dnode.add_child(Prefab3D.gizmo_lines())
        self.cube1 = fast_load(
            "models/cube.obj", reverse_uv_v=False, flip_triangles=True
        )
        self.cube1.material_id = 11
        self.cube1.local_transform = glm.translate(glm.vec3(-1.1, 0, 0)) * glm.rotate(
            math.radians(180), glm.vec3(0, 1, 0)
        )
        self.root3Dnode.add_child(self.cube1)

        # loading a second cube with a bitmap texture
        img: ImageTexture = fast_load("models/cube_texture.bmp")
        cube2_texture_index = self.rc.texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )
        HALF_BLOCK = find_glyph_indices_py("▀")
        cube2_material_idx = self.rc.material_buffer.add_base_texture(
            materials.BaseTexturePy(
                albedo_texture_idx=cube2_texture_index,
                albedo_texture_subid=0,
                glyph_texture_idx=0,
                glyph_texture_subid=0,
                front=True,
                back=True,
                glyph=True,
                glyph_uv_0=True,
                front_uv_0=True,
                back_uv_0=False,
                glyph_method=toglyphmethod.ToGlyphMethodPyStatic(HALF_BLOCK),
            )
        )

        self.cube2 = fast_load(
            "models/cube.obj", reverse_uv_v=False, flip_triangles=True
        )
        self.cube2.material_id = cube2_material_idx
        self.cube2.local_transform = glm.rotate(math.radians(180), glm.vec3(0, 1, 0))

        self.cube2slot = TT3DNode(transform=glm.translate(glm.vec3(1.5, 0, 0)))
        self.cube2slot.add_child(self.cube2)
        self.root3Dnode.add_child(self.cube2slot)

        self.car_taxi = fast_load(
            "models/car/Car5_Taxi.obj", reverse_uv_v=False, flip_triangles=True
        )
        self.car_taxi.material_id = 12
        self.car_taxi.local_transform = glm.translate(glm.vec3(4, 0, 0))
        self.root3Dnode.add_child(self.car_taxi)
        #
        # self.car_taxi2 = fast_load(
        #    "models/car/Car5_Taxi.obj", reverse_uv_v=False, flip_triangles=True
        # )
        # self.car_taxi2.material_id = 12
        # self.car_taxi2.local_transform = glm.translate(glm.vec3(4, 2, 0))
        # self.root3Dnode.add_child(self.car_taxi2)

        # final append
        self.rc.append_root(self.root3Dnode)

    def update_step(self, _timediff):
        self.cube2.apply_transform(
            glm.rotate(_timediff / 2, glm.vec3(0, 1, 0))
            * glm.rotate(_timediff / 4, glm.vec3(1, 0, 0))
        )

    async def on_event(self, event: events.Event):
        await super().on_event(event)

        match event.__class__:
            case events.Leave:
                pass
                # info_box: Static = self.parent.query_one(".lastevent")
                # info_box.update(f"leaving!")

            case events.Key:
                event: events.Key = event
                match event.key:
                    case "a":
                        pass
            case events.MouseDown:
                event: events.MouseDown = event
                match event.button:
                    case 1:
                        screen_click_position = glm.vec3(
                            float(event.x), float(event.y), 0.0
                        )
                        # convert to screen to clip space
                        clip_click_position = glm.vec3(
                            screen_click_position.x / self.size.width * 2 - 1,
                            1 - screen_click_position.y / self.size.height * 2,
                            0.0,
                        )

                        # convert to world space using the view matrix
                        world_click_position = (
                            glm.inverse(self.camera.view_matrix_2D)
                            * clip_click_position
                        )

                        self.camera.view_matrix_2D
                        # self.root2Dnode.local_transform = glm.translate(small_tr_vector)*self.root2Dnode.local_transform
                        # self.parent.query_one("EngineLog").add_line(
                        #    f"click ! {str(world_click_position)}"
                        # )

            case events.MouseScrollDown:
                self.camera.set_zoom_2D(self.camera.zoom_2D * 0.9)
            case events.MouseScrollUp:
                self.camera.set_zoom_2D(self.camera.zoom_2D * 1.1)
            case _:
                try:
                    info_box: Static = self.parent.query_one(".lastevent")
                    info_box.update(f"{event.__class__}: \n{str(event)}")
                except NoMatches:
                    pass


class Some3DModels(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DebuggedView(GLMTester())


if __name__ == "__main__":
    app = Some3DModels()
    app._disable_tooltips = True
    app.run()
