# -*- coding: utf-8 -*-
"""TTSL lighting: LightBuffer + view-space Lambert / point attenuation.

One low-poly sphere uses ``tt_Normal`` and ``tt_ViewPos`` with host lights:
ambient, a key directional, and a moving point light. Lights are authored in
world space; ``RustRenderContext.render`` transforms them to view space each
frame. Slot 0 is a static space fill.

Run:
    uv run python demos/3d/ttsl_lighting.py
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
SPIN_SPEED = 0.45
POINT_ORBIT = 1.15

ALBEDO = glm.vec3(0.82, 0.52, 0.34)

SHADER_SRC = dedent(
    """
    def lit_shade(tt_FragCoord: vec2) -> tuple[vec4, vec4, int]:
        n: vec3 = normalize(tt_Normal)
        frag_pos: vec3 = tt_ViewPos
        amb: vec3 = tt_lightColor(0)
        lit: vec3 = vec3(u_albedo.x * amb.x, u_albedo.y * amb.y, u_albedo.z * amb.z)

        light_dir: vec3 = tt_lightDirection(1)
        diff: float = max(dot(n, light_dir), 0.0)
        dir_c: vec3 = tt_lightColor(1)
        lit = lit + vec3(
            u_albedo.x * dir_c.x * diff,
            u_albedo.y * dir_c.y * diff,
            u_albedo.z * dir_c.z * diff,
        )

        to_light: vec3 = tt_lightPosition(2) - frag_pos
        dist: float = length(to_light)
        l_dir: vec3 = normalize(to_light)
        pt_diff: float = max(dot(n, l_dir), 0.0)
        att: vec3 = tt_lightAttenuation(2)
        atten: float = 1.0 / (att.x + att.y * dist + att.z * dist * dist)
        pt_c: vec3 = tt_lightColor(2)
        k: float = pt_diff * atten
        lit = lit + vec3(u_albedo.x * pt_c.x * k, u_albedo.y * pt_c.y * k, u_albedo.z * pt_c.z * k)

        lit = clamp(lit, vec3(0.0, 0.0, 0.0), vec3(1.0, 1.0, 1.0))
        c: vec4 = vec4(lit.x, lit.y, lit.z, 1.0)
        return (c, c, 0)
    """
)


def _add_lit_material(
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


class TTSLLightingDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)
        self.camera.set_projectioninfo(
            dist_min=CAM_NEAR,
            dist_max=CAM_FAR,
            fov_radians=glm.radians(72.0),
        )
        self.camera.move_at(glm.vec3(0.0, 0.55, -3.6))
        self.camera.point_at(glm.vec3(0.0, 0.0, 0.0))

        self.rc.material_buffer.add_static(
            (0, 0, 0),
            (0, 0, 0),
            find_glyph_indices_py(" "),
        )

        bytecode, reg_template = all_passes_compilation(
            SHADER_SRC,
            "lit_shade",
            {"u_albedo": glm.vec3},
        )
        mat_id = _add_lit_material(
            self.rc,
            bytecode=bytecode,
            reg_template=reg_template,
            u_albedo=ALBEDO,
            default_glyph=find_glyph_indices_py("█"),
        )

        lights = self.rc.light_buffer
        lights.set_ambient(0, color=(0.16, 0.16, 0.18))
        lights.set_directional(
            1,
            color=(0.78, 0.76, 0.68),
            direction=(0.35, 0.72, 0.48),
        )
        lights.set_point(
            2,
            color=(1.0, 0.45, 0.22),
            position=(1.4, 0.6, 0.2),
            attenuation=(1.0, 0.22, 0.08),
        )

        self.spin_root = TT3DNode()
        sphere = Prefab3D.latlong_uv_sphere(0.55, stacks=6, slices=12)
        sphere.material_id = mat_id
        self.spin_root.add_child(sphere)
        self.rc.append_root(self.spin_root)

    def update_step(self, delta_time: float) -> None:
        t = self.time_since_start()
        self.spin_root.set_local_transform(
            glm.rotate(glm.mat4(1.0), t * SPIN_SPEED, glm.vec3(0.0, 1.0, 0.0))
        )
        orbit = glm.vec3(
            glm.cos(t * POINT_ORBIT) * 1.5,
            0.55 + 0.25 * glm.sin(t * 0.7),
            glm.sin(t * POINT_ORBIT) * 1.5,
        )
        self.rc.light_buffer.set_point(
            2,
            color=(1.0, 0.45, 0.22),
            position=orbit,
            attenuation=(1.0, 0.22, 0.08),
        )

    def before_render_step(self) -> None:
        pass

    def post_render_step(self) -> None:
        pass


class TTSLLightingApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TTSLLightingDemo()


if __name__ == "__main__":
    app = TTSLLightingApp()
    app._disable_tooltips = True
    app.run()
