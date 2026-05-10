# -*- coding: utf-8 -*-
"""TTSL depth fog: a rotating box room where walls fade with distance.

Four inward-facing quads plus a floor share full-block materials. One TTSL entry
computes linear eye-space depth from ``tt_FragDepth`` with ``tt_Near`` /
``tt_Far`` (matching the camera clip planes), applies ``1 - d/(d+k)`` fog, and
tints with a per-material **user uniform** ``u_albedo`` (``glm.vec3`` in
``globals_dict``) so red, blue, and floor surfaces reuse the same bytecode with
different ``register_seed`` snapshots.

Uses ``ShaderPy`` with ``frag_depth_f32_reg`` / ``near_f32_reg`` / ``far_f32_reg``
from ``all_passes_compilation``. Slot 0 is a static space fill. Camera is offset
from the room center so rotation shows fog sliding over colored walls and a
neutral floor.

Run:
    uv run python demos/3d/ttsl_fog.py
"""

from textwrap import dedent

from pyglm import glm
from textual.app import App, ComposeResult
from textual.widgets import Header

from tt3de.glm_camera import ViewportScaleMode
from tt3de.prefab3d import Prefab3D
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py, materials  # type: ignore[reportMissingImports]
from tt3de.tt_3dnodes import TT3DNode
from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_FAR,
    GLOBAL_VAR_TT_NEAR,
    RegisterSettings,
    all_passes_compilation,
    shader_py_frag_depth_clip_kwargs,
)

CAM_NEAR = 0.1
CAM_FAR = 100.0

ROOM_HALF = 10.0
WALL_H = 3.0
SPIN_SPEED = 0.55  # radians per second

# Base RGB before fog; one bytecode + ``u_albedo`` per material instance (``RegisterSettings.fork``).
ALBEDO_RED_WALL = glm.vec3(0.92, 0.22, 0.18)
ALBEDO_BLUE_WALL = glm.vec3(0.2, 0.28, 0.92)
ALBEDO_FLOOR = glm.vec3(0.42, 0.36, 0.30)

SHADER_SRC = dedent(
    """
    def depth_fog_surface(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
        z_n: float = 2.0 * tt_FragDepth - 1.0
        # linear eye-space depth from NDC z using active clip planes (see ttsl.md)
        d: float = (2.0 * tt_Near * tt_Far) / (tt_Far + tt_Near - z_n * (tt_Far - tt_Near))
        t: float = 1.0 - d / (d + 10.0)
        # per-material tint via user uniform (globals_dict + register_seed)
        rgb: vec3 = u_albedo * t
        return (rgb, vec3(0.0, 0.0, 0.0), 0)
    """
)


def _wall_xf(angle_y_deg: float, pos: glm.vec3) -> glm.mat4:
    """Position a unitary_square as a room wall.

    The unit square (0..1 in XY, z=0) is front-facing from -Z in LH.
    ``angle_y_deg`` rotates around Y so -Z aims inward, then ``pos``
    translates the transformed origin corner into place.
    """
    s = glm.scale(glm.vec3(ROOM_HALF * 2, WALL_H, 1.0))
    r = glm.rotate(glm.mat4(1.0), glm.radians(angle_y_deg), glm.vec3(0.0, 1.0, 0.0))
    t = glm.translate(pos)
    return t * r * s


def _floor_xf() -> glm.mat4:
    """Lay a unitary_square flat in XZ at y=0, visible from above (LH)."""
    s = glm.scale(glm.vec3(ROOM_HALF * 2, ROOM_HALF * 2, 1.0))
    rx = glm.rotate(glm.mat4(1.0), glm.radians(90.0), glm.vec3(1.0, 0.0, 0.0))
    t = glm.translate(glm.vec3(-ROOM_HALF, 0.0, -ROOM_HALF))
    return t * rx * s


def _add_depth_fog_material(
    rc,
    *,
    bytecode: bytes,
    reg_template: RegisterSettings,
    u_albedo: glm.vec3,
    full_block: tuple[int, ...],
) -> int:
    reg_settings = reg_template.fork()
    reg_settings.set_variable("u_albedo", u_albedo)

    shader_mat = materials.ShaderPy(
        bytecode,
        default_glyph=full_block,
        register_seed=reg_settings.get_register_list(),
        **shader_py_frag_depth_clip_kwargs(reg_settings),
    )
    mat_id = rc.material_buffer.add_shader(shader_mat)
    rc.material_buffer.set_shader_near(mat_id, CAM_NEAR)
    rc.material_buffer.set_shader_far(mat_id, CAM_FAR)
    return mat_id


class TTSLFogRoomDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)
        self.camera.set_projectioninfo(
            dist_min=CAM_NEAR,
            dist_max=CAM_FAR,
            fov_radians=glm.radians(110.0),
        )
        # camera is shifted away from the room to apreciate distance better
        self.camera.move_at(glm.vec3(5.0, WALL_H * 0.4, 5.0))
        self.camera.point_at(glm.vec3(0.0, WALL_H * 0.5, 1.0))

        # the is the background color
        self.rc.material_buffer.add_static(
            (0, 0, 0),
            (0, 0, 0),
            find_glyph_indices_py(" "),
        )

        bytecode, reg_template = all_passes_compilation(
            SHADER_SRC,
            "depth_fog_surface",
            {
                GLOBAL_VAR_TT_NEAR: float,
                GLOBAL_VAR_TT_FAR: float,
                "u_albedo": glm.vec3,
            },
        )

        full_block = find_glyph_indices_py("█")
        mat_red = _add_depth_fog_material(
            self.rc,
            bytecode=bytecode,
            reg_template=reg_template,
            u_albedo=ALBEDO_RED_WALL,
            full_block=full_block,
        )
        mat_blue = _add_depth_fog_material(
            self.rc,
            bytecode=bytecode,
            reg_template=reg_template,
            u_albedo=ALBEDO_BLUE_WALL,
            full_block=full_block,
        )
        mat_floor = _add_depth_fog_material(
            self.rc,
            bytecode=bytecode,
            reg_template=reg_template,
            u_albedo=ALBEDO_FLOOR,
            full_block=full_block,
        )

        self.room = TT3DNode()

        south = Prefab3D.unitary_square()
        south.material_id = mat_red
        south.local_transform = _wall_xf(180.0, glm.vec3(ROOM_HALF, 0.0, -ROOM_HALF))
        self.room.add_child(south)

        north = Prefab3D.unitary_square()
        north.material_id = mat_red
        north.local_transform = _wall_xf(0.0, glm.vec3(-ROOM_HALF, 0.0, ROOM_HALF))
        self.room.add_child(north)

        east = Prefab3D.unitary_square()
        east.material_id = mat_blue
        east.local_transform = _wall_xf(90.0, glm.vec3(ROOM_HALF, 0.0, ROOM_HALF))
        self.room.add_child(east)

        west = Prefab3D.unitary_square()
        west.material_id = mat_blue
        west.local_transform = _wall_xf(-90.0, glm.vec3(-ROOM_HALF, 0.0, -ROOM_HALF))
        self.room.add_child(west)

        floor_quad = Prefab3D.unitary_square()
        floor_quad.material_id = mat_floor
        floor_quad.local_transform = _floor_xf()
        self.room.add_child(floor_quad)

        self.rc.append_root(self.room)

    def update_step(self, delta_time: float) -> None:
        angle = self.time_since_start() * SPIN_SPEED
        self.room.set_local_transform(
            glm.rotate(glm.mat4(1.0), angle, glm.vec3(0.0, 1.0, 0.0))
        )

    def before_render_step(self) -> None:
        pass

    def post_render_step(self) -> None:
        pass


class TTSLFogRoomApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TTSLFogRoomDemo()


if __name__ == "__main__":
    app = TTSLFogRoomApp()
    app._disable_tooltips = True
    app.run()
