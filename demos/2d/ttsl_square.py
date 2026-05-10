# -*- coding: utf-8 -*-
"""End-to-end real pixel-shader demo.

Compiles a TTSL shader once at startup, installs it as a Rust Shader material,
and renders a UV + time animated pattern directly in the material pass.

This validates the full path:
    shader source -> bytecode -> Shader material -> per-pixel run_ttsl -> final cell

Run:
    uv run python demos/2d/ttsl_square.py
"""

from textwrap import dedent

from pyglm import glm
from textual.app import App, ComposeResult
from textual.widgets import Header

from tt3de.glm_camera import ViewportScaleMode
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py, materials  # type: ignore[reportMissingImports]
from tt3de.tt_2dnodes import TT2DNode, TT2DUnitSquare
from tt3de.ttsl.compiler import GLOBAL_VAR_TT_TIME, all_passes_compilation


SHADER_SRC = dedent(
    """
    def my_shader(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
        # Make motion clearly visible at terminal framerate.
        phase: float = tt_Time * 4.0
        wave_x: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.x * 18.0) + phase)
        wave_y: float = 0.5 + 0.5 * glm.sin((tt_TexCoord0.y * 14.0) - phase * 1.2)
        blue: float = 0.5 + 0.5 * glm.sin(phase * 0.7 + (tt_TexCoord0.x + tt_TexCoord0.y) * 8.0)
        rgb: vec4 = vec4(wave_x, wave_y, blue, 1.0)
        return (rgb, rgb, 0)
    """
)


class TTSLSquareDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self._bytecode, self._reg_settings = all_passes_compilation(
            SHADER_SRC, "my_shader", {GLOBAL_VAR_TT_TIME: float}
        )
        _time_ty, self._time_reg = self._reg_settings.var_name_to_registers[GLOBAL_VAR_TT_TIME]

        self.camera.set_zoom_2D(0.5)
        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)

        # `RustRenderContext` seeds geometry slot 0 with a sentinel point at the origin
        # using `node_id=0` and `material_id=0`. Cleared / empty depth samples reference
        # that geometry, so material index 0 must be a plain static fill — not the
        # shader — or the whole canvas runs TTSL (alternating blues from animated UVs).
        self.rc.material_buffer.add_static(
            (0, 0, 0),
            (0, 0, 0),
            find_glyph_indices_py(" "),
        )

        full_block_glyph = find_glyph_indices_py("█")
        shader_mat = materials.ShaderPy(
            self._bytecode,
            time_f32_reg=self._time_reg,
            default_glyph=full_block_glyph,
            register_seed=self._reg_settings.get_register_list(),
        )
        self._shader_mat_id = self.rc.material_buffer.add_shader(shader_mat)

        self.root2Dnode = TT2DNode()
        self.root2Dnode.add_child(
            TT2DUnitSquare(
                transform=glm.scale(glm.vec3(1.5, 1.5, 1.0)),
                material_id=self._shader_mat_id,
                centered=True,
            )
        )
        self.rc.append_root(self.root2Dnode)

    def update_step(self, delta_time: float) -> None:
        pass

    def before_render_step(self) -> None:
        self.rc.material_buffer.set_shader_time(
            self._shader_mat_id, float(self.time_since_start())
        )

    def post_render_step(self) -> None:
        pass


class TTSLSquareApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TTSLSquareDemo()


if __name__ == "__main__":
    app = TTSLSquareApp()
    app._disable_tooltips = True
    app.run()
