# -*- coding: utf-8 -*-
"""TTSL fog with glyph dither: depth bands select shade glyphs.

Same rotating box room as ``ttsl_fog.py``, but the fragment shader maps the fog factor
``t`` (linear depth -> ``1 - d/(d+k)``) into **four density bands** using ``floor()``
for quantization. Each band selects one of four glyph indices passed as **user uniforms**
``u_g0``...``u_g3`` (defaults: the block-density run from ``GLYPH_STATIC_STR`` in
``glyphset.rs``). The room geometry spins over time (``update_step``), so depth bands
shift naturally without any time logic inside the shader itself.

Uses ``ShaderPy`` with ``frag_depth_f32_reg`` / ``near_f32_reg`` / ``far_f32_reg``,
slot 0 static space, and per-wall ``u_albedo`` like the original fog demo.

Run:
    uv run python demos/3d/ttsl_fog_glyph_shadows.py
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
    RegisterSettings,
    all_passes_compilation,
)
from tt3de.ttsl.ttsl_assembly import IRType

CAM_NEAR = 0.1
CAM_FAR = 100.0

ROOM_HALF = 10.0
WALL_H = 3.0
SPIN_SPEED = 0.55  # radians per second

ALBEDO_RED_WALL = glm.vec3(0.92, 0.22, 0.18)
ALBEDO_BLUE_WALL = glm.vec3(0.2, 0.28, 0.92)
ALBEDO_FLOOR = glm.vec3(0.42, 0.36, 0.30)

# Indices into GLYPH_STATIC_STR (see src/drawbuffer/glyphset.rs): light -> full block.
GLYPH_D = find_glyph_indices_py("\u2591")
GLYPH_M2 = find_glyph_indices_py("\u2592")
GLYPH_M3 = find_glyph_indices_py("\u2593")
GLYPH_FULL = find_glyph_indices_py("\u2588")

SHADER_SRC = dedent(
    """
    def depth_fog_glyph(tt_FragCoord: vec2) -> tuple[vec3, vec3, int]:
        z_n: float = 2.0 * tt_FragDepth - 1.0
        d: float = (2.0 * tt_Near * tt_Far) / (tt_Far + tt_Near - z_n * (tt_Far - tt_Near))
        t: float = 1.0 - d / (d + 10.0)
        rgb: vec3 = u_albedo * t
        # Quantize depth factor into 4 fog bands via floor.
        band: float = floor(t * 4.0)
        if band >= 4.0:
            band = 3.0
        blk: vec3 = vec3(0.0, 0.0, 0.0)
        if band >= 3.0:
            return (rgb, blk, u_g3)
        if band >= 2.0:
            return (rgb, blk, u_g2)
        if band >= 1.0:
            return (rgb, blk, u_g1)
        return (rgb, blk, u_g0)
    """
)


def _clone_reg_settings(base: RegisterSettings) -> RegisterSettings:
    out = RegisterSettings(dict(base.var_name_to_registers))
    for ty in IRType:
        out.regs[ty] = dict(base.regs[ty])
    return out


def _add_glyph_fog_material(
    rc,
    *,
    bytecode: bytes,
    reg_template: RegisterSettings,
    u_albedo: glm.vec3,
    full_block: tuple[int, ...],
    glyph_uniforms: tuple[int, int, int, int],
) -> int:
    reg_settings = _clone_reg_settings(reg_template)
    reg_settings.set_variable("u_albedo", u_albedo)
    g0, g1, g2, g3 = glyph_uniforms
    reg_settings.set_variable("u_g0", int(g0))
    reg_settings.set_variable("u_g1", int(g1))
    reg_settings.set_variable("u_g2", int(g2))
    reg_settings.set_variable("u_g3", int(g3))

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


class TTSLFogGlyphShadowsDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)
        self.camera.set_projectioninfo(
            dist_min=CAM_NEAR,
            dist_max=CAM_FAR,
            fov_radians=glm.radians(110.0),
        )
        self.camera.move_at(glm.vec3(5.0, WALL_H * 0.4, 5.0))
        self.camera.point_at(glm.vec3(0.0, WALL_H * 0.5, 1.0))

        self.rc.material_buffer.add_static(
            (0, 0, 0),
            (0, 0, 0),
            find_glyph_indices_py(" "),
        )

        bytecode, reg_template = all_passes_compilation(
            SHADER_SRC,
            "depth_fog_glyph",
            {
                GLOBAL_VAR_TT_NEAR: float,
                GLOBAL_VAR_TT_FAR: float,
                "u_albedo": glm.vec3,
                "u_g0": int,
                "u_g1": int,
                "u_g2": int,
                "u_g3": int,
            },
        )

        glyph_band = (GLYPH_D, GLYPH_M2, GLYPH_M3, GLYPH_FULL)
        full_block = find_glyph_indices_py("\u2588")

        mat_red = _add_glyph_fog_material(
            self.rc,
            bytecode=bytecode,
            reg_template=reg_template,
            u_albedo=ALBEDO_RED_WALL,
            full_block=full_block,
            glyph_uniforms=glyph_band,
        )
        mat_blue = _add_glyph_fog_material(
            self.rc,
            bytecode=bytecode,
            reg_template=reg_template,
            u_albedo=ALBEDO_BLUE_WALL,
            full_block=full_block,
            glyph_uniforms=glyph_band,
        )
        mat_floor = _add_glyph_fog_material(
            self.rc,
            bytecode=bytecode,
            reg_template=reg_template,
            u_albedo=ALBEDO_FLOOR,
            full_block=full_block,
            glyph_uniforms=glyph_band,
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


def _wall_xf(angle_y_deg: float, pos: glm.vec3) -> glm.mat4:
    s = glm.scale(glm.vec3(ROOM_HALF * 2, WALL_H, 1.0))
    r = glm.rotate(glm.mat4(1.0), glm.radians(angle_y_deg), glm.vec3(0.0, 1.0, 0.0))
    tr = glm.translate(pos)
    return tr * r * s


def _floor_xf() -> glm.mat4:
    s = glm.scale(glm.vec3(ROOM_HALF * 2, ROOM_HALF * 2, 1.0))
    rx = glm.rotate(glm.mat4(1.0), glm.radians(90.0), glm.vec3(1.0, 0.0, 0.0))
    tr = glm.translate(glm.vec3(-ROOM_HALF, 0.0, -ROOM_HALF))
    return tr * rx * s


class TTSLFogGlyphShadowsApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TTSLFogGlyphShadowsDemo()


if __name__ == "__main__":
    app = TTSLFogGlyphShadowsApp()
    app._disable_tooltips = True
    app.run()
