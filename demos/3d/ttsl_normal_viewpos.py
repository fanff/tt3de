# -*- coding: utf-8 -*-
"""TTSL view-space varyings: ``tt_Normal`` and ``tt_ViewPos``.

Two **low-poly spheres**: the left uses smooth Lambert + rim color. The right
uses the same varyings but the **glyph** shader (``sphere_glyphs``) — a
**diffuse-biased** scalar (``diff`` plus a little rim) maps to ``#``, ``+``, ``*``,
``.`` (glyph uniforms ``u_g_hash`` … ``u_g_dot``; bullet ``•`` is index ``> 127``
so ``find_glyph_indices_py`` ``i8`` would mis-encode it). Background is flat
``u_albedo``; **front** (ink) color is ``u_albedo * ink_w`` with ``ink_w`` from
``shade`` (see ``demos/3d/ttsl_fog_glyph_shadows.py`` for glyph index returns).


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

# Glyph-band characters (darkest → lightest): #, +, *, . — indices < 128 for
# ``find_glyph_indices_py`` (``i8``); bullet ``•`` is index 241.
GLYPH_HASH = find_glyph_indices_py("#")
GLYPH_PLUS = find_glyph_indices_py("+")
GLYPH_STAR = find_glyph_indices_py("*")
GLYPH_DOT = find_glyph_indices_py(".")

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
        # Band on diffuse (+ rim); ``shade`` also scales ink for front color depth.
        shade: float = glm.clamp(diff + rim * 0.42, 0.0, 1.0)
        ink_w: float = glm.clamp(0.12 + 0.88 * shade, 0.0, 1.0)
        ink: vec3 = u_albedo * ink_w
        fr: vec4 = vec4(ink.x, ink.y, ink.z, 1.0)
        bg: vec4 = vec4(u_albedo.x, u_albedo.y, u_albedo.z, 1.0)
        if shade >= 0.74:
            return (fr, bg, u_g_dot)
        if shade >= 0.48:
            return (fr, bg, u_g_star)
        if shade >= 0.22:
            return (fr, bg, u_g_plus)
        return (fr, bg, u_g_hash)
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
    reg_settings.set_variable("u_g_hash", int(GLYPH_HASH))
    reg_settings.set_variable("u_g_plus", int(GLYPH_PLUS))
    reg_settings.set_variable("u_g_star", int(GLYPH_STAR))
    reg_settings.set_variable("u_g_dot", int(GLYPH_DOT))
    shader_mat = materials.ShaderPy(
        bytecode,
        default_glyph=default_glyph,
        register_seed=reg_settings.get_register_list(),
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
        self.camera.move_at(glm.vec3(0.0, 0.85, -4.6))
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
            {
                "u_albedo": glm.vec3,
                "u_g_hash": int,
                "u_g_plus": int,
                "u_g_star": int,
                "u_g_dot": int,
            },
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
            default_glyph=int(GLYPH_HASH),
        )

        self.spin_root = TT3DNode()

        sphere = Prefab3D.latlong_uv_sphere(0.42, stacks=4, slices=10)
        sphere.material_id = mat_sphere
        sphere.local_transform = glm.translate(glm.vec3(-1.05, 0.0, 0.0))
        self.spin_root.add_child(sphere)

        # Second mesh: same low-poly sphere with ``sphere_glyphs`` TTSL.
        glyph_sphere = Prefab3D.latlong_uv_sphere(0.5, stacks=6, slices=12)
        glyph_sphere.material_id = mat_glyphs
        glyph_sphere.local_transform = glm.translate(glm.vec3(1.05, 0.0, 0.0))
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
