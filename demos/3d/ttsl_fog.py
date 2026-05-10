# -*- coding: utf-8 -*-
"""TTSL depth fog: a rotating box room where walls fade with distance.

Four inward-facing quads plus a floor share full-block materials. Each TTSL
fragment reads ``tt_FragDepth``, reconstructs linear eye-space depth with
``tt_Near`` / ``tt_Far`` (matching the camera clip planes), and scales color with
``1 - d/(d+k)`` so nearby surfaces read bright and far ones sink into
black—classic distance fog without a separate pass.

Uses ``ShaderPy`` with ``frag_depth_f32_reg`` tied to ``PIXELVAR_TT_FRAG_DEPTH``
and ``near_f32_reg`` / ``far_f32_reg`` for ``tt_Near`` / ``tt_Far`` from
``all_passes_compilation``. Slot 0 is a static space fill. Camera is offset
from the room center so rotation shows the fog sliding over red (north/south),
blue (east/west), and neutral floor tints.

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
    PIXELVAR_TT_FRAG_DEPTH,
    all_passes_compilation,
)

CAM_NEAR = 0.1
CAM_FAR = 100.0

ROOM_HALF = 10.0
WALL_H = 3.0
SPIN_SPEED = 0.55  # radians per second

SHADER_SRC_RED_WALL = dedent(
    """
    def depth_red_wall(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
        z_n: float = 2.0 * tt_FragDepth - 1.0
        # linear eye-space depth from NDC z using active clip planes (see ttsl.md)
        d: float = (2.0 * tt_Near * tt_Far) / (tt_Far + tt_Near - z_n * (tt_Far - tt_Near))
        t: float = 1.0 - d / (d + 10.0)
        rgb: vec3 = vec3(0.92 * t, 0.22 * t, 0.18 * t)
        return (rgb, vec3(0.0, 0.0, 0.0), 0)
    """
)

SHADER_SRC_BLUE_WALL = dedent(
    """
    def depth_blue_wall(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
        z_n: float = 2.0 * tt_FragDepth - 1.0
        d: float = (2.0 * tt_Near * tt_Far) / (tt_Far + tt_Near - z_n * (tt_Far - tt_Near))
        t: float = 1.0 - d / (d + 10.0)
        rgb: vec3 = vec3(0.2 * t, 0.28 * t, 0.92 * t)
        return (rgb, vec3(0.0, 0.0, 0.0), 0)
    """
)

SHADER_SRC_FLOOR = dedent(
    """
    def depth_floor(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
        z_n: float = 2.0 * tt_FragDepth - 1.0
        d: float = (2.0 * tt_Near * tt_Far) / (tt_Far + tt_Near - z_n * (tt_Far - tt_Near))
        t: float = 1.0 - d / (d + 10.0)
        rgb: vec3 = vec3(0.42 * t, 0.36 * t, 0.30 * t)
        return (rgb, vec3(0.0, 0.0, 0.0), 0)
    """
)


def _add_depth_shader_material(
    rc,
    *,
    shader_src: str,
    entry: str,
    full_block: tuple[int, ...],
) -> int:
    globals_dict = {
        GLOBAL_VAR_TT_NEAR: float,
        GLOBAL_VAR_TT_FAR: float,
    }
    bytecode, reg_settings = all_passes_compilation(shader_src, entry, globals_dict)
    _ty, fd_reg = reg_settings.var_name_to_registers[PIXELVAR_TT_FRAG_DEPTH]
    _, near_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_NEAR]
    _, far_reg = reg_settings.var_name_to_registers[GLOBAL_VAR_TT_FAR]
    shader_mat = materials.ShaderPy(
        bytecode,
        default_glyph=full_block,
        register_seed=reg_settings.get_register_list(),
        frag_depth_f32_reg=fd_reg,
        near_f32_reg=near_reg,
        far_f32_reg=far_reg,
    )
    mat_id = rc.material_buffer.add_shader(shader_mat)
    rc.material_buffer.set_shader_near(mat_id, CAM_NEAR)
    rc.material_buffer.set_shader_far(mat_id, CAM_FAR)
    return mat_id


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

        full_block = find_glyph_indices_py("█")
        mat_red = _add_depth_shader_material(
            self.rc,
            shader_src=SHADER_SRC_RED_WALL,
            entry="depth_red_wall",
            full_block=full_block,
        )
        mat_blue = _add_depth_shader_material(
            self.rc,
            shader_src=SHADER_SRC_BLUE_WALL,
            entry="depth_blue_wall",
            full_block=full_block,
        )
        mat_floor = _add_depth_shader_material(
            self.rc,
            shader_src=SHADER_SRC_FLOOR,
            entry="depth_floor",
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
