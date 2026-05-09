# -*- coding: utf-8 -*-
"""TTSL ``tt_FragDepth`` and ``tt_PrimitiveID`` on three U-shaped planes.

All walls share one ``ShaderPy``. **Depth** modulates brightness via ``d / (d + k)``. **Color**
comes from ``tt_PrimitiveID``: each ``Prefab3D.unitary_square()`` submits two triangles, and we
append **back → left → right → floor**, so IDs ``0–1`` red, ``2–3`` green, ``4–5`` blue,
``6–7`` earth-tone floor (see shader; blue is gated to ``4 ≤ pid < 6``).

``frag_depth_f32_reg`` must match ``PIXELVAR_TT_FRAG_DEPTH``. ``tt_PrimitiveID`` is pinned to the
default i32 register (no extra ``ShaderPy`` field).

Side walls use negative X scale so inward-facing triangles pass ``triangle_3d`` back-face culling.

The scene root spins around **world Y** through a pivot near the U’s centroid (not the world origin),
otherwise the opening sweeps in a huge orbit and usually only one wall stays in frame.

A large **floor** quad sits ``FLOOR_BELOW_CAMERA`` units below ``CAMERA_EYE_Y`` (2 world units by default).

Run:
    uv run python demos/3d/ttsl_frag_depth_u_planes.py
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
    PIXELVAR_TT_FRAG_DEPTH,
    all_passes_compilation,
)

# Vertical planes (world Y-up): opening toward -Z; camera looks toward +Z into the U.
PLANE_H = 4.0
BACK_W = 8.0
SIDE_W = 7.0
SIDE_X = 3.4
BACK_Z = 10.5
Z_LEG_CENTER = BACK_Z * 0.42
CAMERA_EYE_Y = PLANE_H * 0.38
FLOOR_BELOW_CAMERA = 2.0
FLOOR_WORLD_Y = CAMERA_EYE_Y - FLOOR_BELOW_CAMERA
# Horizontal quad in XZ, spans roughly under the U (world units).
FLOOR_HALF_EXTENT_X = 14.0
FLOOR_HALF_EXTENT_Z = 14.0
# Radians per second — ``translate(p) * R_y * translate(-p)`` so the U turns in place.
ROOT_SPIN_Y_RAD_S = 0.55
# Rough center between back wall (``z ≈ BACK_Z``) and side legs (``z ≈ Z_LEG_CENTER``).
U_SPIN_PIVOT = glm.vec3(
    0.0,
    PLANE_H * 0.5,
    (BACK_Z + Z_LEG_CENTER) * 0.5,
)

SHADER_SRC = dedent(
    """
    def depth_showcase(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
        # Depth → luminance scale (hyperbolic, avoids blowing out terminal colors).
        d: float = tt_FragDepth
        t: float = d / (d + 0.42)
        # Two tris per mesh; order: back, left, right (0–5), floor (6–7).
        br: float = 0.35
        bg: float = 0.35
        bb: float = 0.35
        if tt_PrimitiveID > 5:
            br = 0.42
            bg = 0.36
            bb = 0.30
        if tt_PrimitiveID < 2:
            br = 0.92
            bg = 0.22
            bb = 0.18
        if tt_PrimitiveID > 1:
            if tt_PrimitiveID < 4:
                br = 0.18
                bg = 0.88
                bb = 0.22
        if tt_PrimitiveID > 3:
            if tt_PrimitiveID < 6:
                br = 0.2
                bg = 0.28
                bb = 0.92
        rgb: vec3 = vec3(br * t, bg * t, bb * t)
        return (rgb, vec3(0.0, 0.0, 0.0), 0)
    """
)


def _xf_back_wall() -> glm.mat4:
    s = glm.scale(glm.vec3(BACK_W, PLANE_H, 1.0))
    t = glm.translate(glm.vec3(-BACK_W * 0.5, 0.0, BACK_Z))
    return t * s


def _xf_floor() -> glm.mat4:
    # Lay the square in XZ (Rx(90°): mesh +Z → −Y). Local Z scale +1 vs −1 chooses which face passes
    # ``triangle_3d`` back-face culling from above — flipped relative to the previous −1 default.
    s = glm.scale(
        glm.vec3(FLOOR_HALF_EXTENT_X * 2.0, FLOOR_HALF_EXTENT_Z * 2.0, 1.0)
    )
    rx = glm.rotate(glm.mat4(1.0), glm.radians(90.0), glm.vec3(1.0, 0.0, 0.0))
    # Corner-down placement then lift to ``FLOOR_WORLD_Y``; centers on origin X and spin pivot Z.
    t = glm.translate(
        glm.vec3(
            -FLOOR_HALF_EXTENT_X,
            FLOOR_WORLD_Y,
            -FLOOR_HALF_EXTENT_Z + U_SPIN_PIVOT.z,
        )
    )
    return t * rx * s


def _xf_side_wall(
    *,
    degrees_y: float,
    center_x: float,
    z_center: float,
    mirror_local_x: bool = False,
) -> glm.mat4:
    # Negative X scale flips winding so inward faces survive back-face culling.
    s = glm.scale(glm.vec3(-SIDE_W, PLANE_H, 1.0))
    r = glm.rotate(glm.mat4(1.0), glm.radians(degrees_y), glm.vec3(0.0, 1.0, 0.0))
    if degrees_y > 0.0:
        tz = z_center - SIDE_W * 0.5
    else:
        tz = z_center + SIDE_W * 0.5
    tr = glm.translate(glm.vec3(center_x, 0.0, tz))
    m = tr * r * s
    if mirror_local_x:
        m = m * glm.scale(glm.vec3(-1.0, 1.0, 1.0))
    return m


def _spin_world_y_about_pivot(angle: float, pivot: glm.vec3) -> glm.mat4:
    return glm.translate(pivot) * glm.rotate(
        glm.mat4(1.0), angle, glm.vec3(0.0, 1.0, 0.0)
    ) * glm.translate(-pivot)


class TTSLFragDepthUDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self._bytecode, self._reg_settings = all_passes_compilation(
            SHADER_SRC, "depth_showcase", {}
        )
        _ty, fd_reg = self._reg_settings.var_name_to_registers[PIXELVAR_TT_FRAG_DEPTH]

        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)
        self.camera.move_at(glm.vec3(0.0, CAMERA_EYE_Y, -1.25))
        self.camera.point_at(glm.vec3(0.0, PLANE_H * 0.5, BACK_Z * 0.72))

        self.rc.material_buffer.add_static(
            (0, 0, 0),
            (0, 0, 0),
            find_glyph_indices_py(" "),
        )

        full_block = find_glyph_indices_py("█")
        shader_mat = materials.ShaderPy(
            self._bytecode,
            default_glyph=full_block,
            register_seed=self._reg_settings.get_register_list(),
            frag_depth_f32_reg=fd_reg,
        )
        mat_depth = self.rc.material_buffer.add_shader(shader_mat)

        self.root3Dnode = TT3DNode()
        # Primitive IDs follow ``add_child`` order — must match ``depth_showcase`` bands.
        back = Prefab3D.unitary_square()
        back.material_id = mat_depth
        back.local_transform = _xf_back_wall()
        self.root3Dnode.add_child(back)

        left = Prefab3D.unitary_square()
        left.material_id = mat_depth
        left.local_transform = _xf_side_wall(
            degrees_y=90.0,
            center_x=-SIDE_X,
            z_center=Z_LEG_CENTER,
        )
        self.root3Dnode.add_child(left)

        right = Prefab3D.unitary_square()
        right.material_id = mat_depth
        right.local_transform = _xf_side_wall(
            degrees_y=-90.0,
            center_x=SIDE_X,
            z_center=Z_LEG_CENTER,
            mirror_local_x=True,
        )
        self.root3Dnode.add_child(right)

        floor = Prefab3D.unitary_square()
        floor.material_id = mat_depth
        floor.local_transform = _xf_floor()
        self.root3Dnode.add_child(floor)

        self.rc.append_root(self.root3Dnode)

    def update_step(self, delta_time: float) -> None:
        angle = self.time_since_start() * ROOT_SPIN_Y_RAD_S
        self.root3Dnode.set_local_transform(
            _spin_world_y_about_pivot(angle, U_SPIN_PIVOT)
        )

    def before_render_step(self) -> None:
        pass

    def post_render_step(self) -> None:
        pass


class TTSLFragDepthUApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TTSLFragDepthUDemo()


if __name__ == "__main__":
    app = TTSLFragDepthUApp()
    app._disable_tooltips = True
    app.run()
