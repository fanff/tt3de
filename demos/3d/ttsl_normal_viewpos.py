# -*- coding: utf-8 -*-
"""TTSL view-space varyings: ``tt_Normal`` and ``tt_ViewPos``.

Two **low-poly spheres**: the left uses smooth Lambert + rim color. The right
uses the same varyings but the **glyph** shader (``sphere_glyphs``) — a
**diffuse-biased** scalar (``diff`` plus rim), contrast-stretched so mid-tones
snap toward the ends of a 10-step ASCII density ramp `` .:-=+*#%@``
(space = no shading, ``@`` = heaviest).
Glyph uniforms are ``u_g0`` … ``u_g9``; all characters are ASCII so
``find_glyph_indices_py`` ``i8`` stays valid (bullet ``•`` is index ``> 127``
and would mis-encode). Background is flat ``u_albedo``; **front** (ink) color
is ``u_albedo * ink_w`` with ``ink_w`` from ``shade`` (see
``demos/3d/ttsl_fog_glyph_shadows.py`` for glyph index returns).


Run:
    uv run python demos/3d/ttsl_normal_viewpos.py
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
from tt3de.ttsl.compiler import RegisterSettings, all_passes_compilation

CAM_NEAR = 0.1
CAM_FAR = 100.0
SPIN_SPEED = 0.5  # radians per second

ALBEDO_SPHERE = glm.vec3(0.55, 0.72, 0.95)
ALBEDO_GLYPH_SPHERE = glm.vec3(0.95, 0.62, 0.38)

# Lightest (no shading) → darkest. Classic 10-level ASCII density; all < 128.
GLYPH_RAMP_CHARS = " .:-=+*#%@"
GLYPH_G0 = find_glyph_indices_py(" ")
GLYPH_G1 = find_glyph_indices_py(".")
GLYPH_G2 = find_glyph_indices_py(":")
GLYPH_G3 = find_glyph_indices_py("-")
GLYPH_G4 = find_glyph_indices_py("=")
GLYPH_G5 = find_glyph_indices_py("+")
GLYPH_G6 = find_glyph_indices_py("*")
GLYPH_G7 = find_glyph_indices_py("#")
GLYPH_G8 = find_glyph_indices_py("%")
GLYPH_G9 = find_glyph_indices_py("@")
GLYPH_RAMP = (
    GLYPH_G0,
    GLYPH_G1,
    GLYPH_G2,
    GLYPH_G3,
    GLYPH_G4,
    GLYPH_G5,
    GLYPH_G6,
    GLYPH_G7,
    GLYPH_G8,
    GLYPH_G9,
)
GLYPH_UNIFORM_NAMES = tuple(f"u_g{i}" for i in range(len(GLYPH_RAMP)))
GLYPH_GLOBALS = {name: int for name in GLYPH_UNIFORM_NAMES}

SHADER_SPHERE_SRC = dedent(
    """
    def lit_rim(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
        # Per-fragment interpolated normal in view space (see ``source/ttsl.md``).
        n: vec3 = normalize(tt_Normal)
        # View-space surface point; eye at origin → direction to camera is ``-P``.
        vdir: vec3 = normalize(-tt_ViewPos)
        # Fixed "key" light direction in view space (not a builtin).
        ldir: vec3 = normalize(vec3(0.35, 0.72, 0.48))
        diff: float = glm.max(0.0, glm.dot(n, ldir))
        # Squared falloff (``glm.pow`` is not a TTSL surface); keeps edges bright.
        edge: float = glm.clamp(1.0 - glm.max(0.0, glm.dot(n, vdir)), 0.0, 1.0)
        rim: float = edge * edge
        amb: float = 0.14
        rgb: vec3 = u_albedo * (amb + 0.86 * diff) + vec3(1.0, 1.0, 1.0) * rim * 0.38
        return (vec4(rgb.x, rgb.y, rgb.z, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 0)
    """
)

SHADER_SPHERE_GLYPHS_SRC = dedent(
    """
    def sphere_glyphs(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
        # Same view-space varyings as the sphere; ``fr`` = glyph front (ink).
        n: vec3 = normalize(tt_Normal)
        vdir: vec3 = normalize(-tt_ViewPos)
        ldir: vec3 = normalize(vec3(0.35, 0.72, 0.48))
        diff: float = glm.max(0.0, glm.dot(n, ldir))
        edge: float = glm.clamp(1.0 - glm.max(0.0, glm.dot(n, vdir)), 0.0, 1.0)
        rim: float = edge * edge
        # Band on diffuse (+ rim); ``amp`` also scales ink for front color depth.
        shade: float = glm.clamp(diff + rim * 0.55, 0.0, 1.0)
        # Contrast stretch so mid-tones snap toward space / ``@``.
        amp: float = glm.clamp(0.5 + (shade - 0.5) * 1.7, 0.0, 1.0)
        ink_w: float = glm.clamp(0.05 + 0.95 * amp, 0.0, 1.0)
        ink: vec3 = u_albedo * ink_w
        fr: vec4 = vec4(ink.x, ink.y, ink.z, 1.0)
        bg: vec4 = vec4(u_albedo.x, u_albedo.y, u_albedo.z, 1.0)
        # 10 even bands; lit (high amp) → space, shadowed → ``@``.
        inv: float = glm.clamp(1.0 - amp, 0.0, 0.999)
        band: float = floor(inv * 10.0)
        if band >= 9.0:
            return (fr, bg, u_g9)
        if band >= 8.0:
            return (fr, bg, u_g8)
        if band >= 7.0:
            return (fr, bg, u_g7)
        if band >= 6.0:
            return (fr, bg, u_g6)
        if band >= 5.0:
            return (fr, bg, u_g5)
        if band >= 4.0:
            return (fr, bg, u_g4)
        if band >= 3.0:
            return (fr, bg, u_g3)
        if band >= 2.0:
            return (fr, bg, u_g2)
        if band >= 1.0:
            return (fr, bg, u_g1)
        return (fr, bg, u_g0)
    """
)


def _add_sphere_material(
    rc,
    *,
    bytecode: bytes,
    reg_template: RegisterSettings,
    u_albedo: glm.vec3,
    default_glyph: int,
) -> int:
    reg_settings = reg_template.fork()
    reg_settings.set_variable("u_albedo", u_albedo)
    shader_mat = materials.ShaderPy(
        bytecode,
        default_glyph=default_glyph,
        register_seed=reg_settings.get_register_list(),
        ssa_json=reg_settings.ssa_json(),
    )
    return rc.material_buffer.add_shader(shader_mat)


def _add_sphere_glyphs_material(
    rc,
    *,
    bytecode: bytes,
    reg_template: RegisterSettings,
    u_albedo: glm.vec3,
    default_glyph: int,
) -> int:
    reg_settings = reg_template.fork()
    reg_settings.set_variable("u_albedo", u_albedo)
    for name, glyph in zip(GLYPH_UNIFORM_NAMES, GLYPH_RAMP, strict=True):
        reg_settings.set_variable(name, int(glyph))
    shader_mat = materials.ShaderPy(
        bytecode,
        default_glyph=default_glyph,
        register_seed=reg_settings.get_register_list(),
        ssa_json=reg_settings.ssa_json(),
    )
    return rc.material_buffer.add_shader(shader_mat)


class TTSLNormalViewPosDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)
        self.camera.set_projectioninfo(
            dist_min=CAM_NEAR,
            dist_max=CAM_FAR,
            fov_radians=glm.radians(72.0),
        )
        self.camera.move_at(glm.vec3(0.0, 0.55, -5.2))
        self.camera.point_at(glm.vec3(0.0, 0.05, 0.0))

        self.rc.material_buffer.add_static(
            (0, 0, 0),
            (0, 0, 0),
            find_glyph_indices_py(" "),
        )

        sphere_bc, sphere_reg = all_passes_compilation(
            SHADER_SPHERE_SRC,
            "lit_rim",
            {"u_albedo": glm.vec3},
        )
        sphere_glyphs_bc, sphere_glyphs_reg = all_passes_compilation(
            SHADER_SPHERE_GLYPHS_SRC,
            "sphere_glyphs",
            {"u_albedo": glm.vec3, **GLYPH_GLOBALS},
        )
        full_block = find_glyph_indices_py("█")
        mat_sphere = _add_sphere_material(
            self.rc,
            bytecode=sphere_bc,
            reg_template=sphere_reg,
            u_albedo=ALBEDO_SPHERE,
            default_glyph=full_block,
        )
        mat_glyphs = _add_sphere_glyphs_material(
            self.rc,
            bytecode=sphere_glyphs_bc,
            reg_template=sphere_glyphs_reg,
            u_albedo=ALBEDO_GLYPH_SPHERE,
            default_glyph=int(GLYPH_G9),
        )

        self.spin_root = TT3DNode()

        sphere = Prefab3D.latlong_uv_sphere(0.75, stacks=5, slices=12)
        sphere.material_id = mat_sphere
        sphere.local_transform = glm.translate(glm.vec3(-1.85, 0.0, 0.0))
        self.spin_root.add_child(sphere)

        # Denser tessellation so the 10-step ramp can show mid-tones.
        glyph_sphere = Prefab3D.latlong_uv_sphere(0.90, stacks=10, slices=20)
        glyph_sphere.material_id = mat_glyphs
        glyph_sphere.local_transform = glm.translate(glm.vec3(1.85, 0.0, 0.0))
        self.spin_root.add_child(glyph_sphere)

        self.rc.append_root(self.spin_root)

    def update_step(self, delta_time: float) -> None:
        angle = self.time_since_start() * SPIN_SPEED
        self.spin_root.set_local_transform(
            glm.rotate(glm.mat4(1.0), angle, glm.vec3(0.0, 1.0, 0.0))
        )

    def before_render_step(self) -> None:
        pass

    def post_render_step(self) -> None:
        pass


class TTSLNormalViewPosApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TTSLNormalViewPosDemo()


if __name__ == "__main__":
    app = TTSLNormalViewPosApp()
    app._disable_tooltips = True
    app.run()
