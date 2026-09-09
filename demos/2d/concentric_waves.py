# -*- coding: utf-8 -*-
"""Concentric water ripples on a 2D square (TTSL + glyph bands).

A compiled TTSL shader paints dark blue rings that emanate from the square center
with ``tt_Time``. Wave height selects one of four glyph uniforms (``.`` ``~`` ``o``
``O``) so motion reads on the terminal grid, not only in color.

Run:
    uv run python demos/2d/concentric_waves.py
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

# Glyph indices must fit ``find_glyph_indices_py`` (``i8``); avoid code points > 127.
GLYPH_TROUGH = find_glyph_indices_py(".")
GLYPH_RIPPLE = find_glyph_indices_py("~")
GLYPH_RING = find_glyph_indices_py("o")
GLYPH_CREST = find_glyph_indices_py("O")

SHADER_SRC = dedent(
    """
    def concentric_waves(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
        # Square center in UV space; rings move outward as tt_Time advances.
        dx: float = tt_TexCoord0.x - 0.5
        dy: float = tt_TexCoord0.y - 0.5
        offset: vec2 = vec2(dx, dy)
        dist: float = length(offset)
        phase: float = dist * 24.0 - tt_Time * 5.0
        wave: float = glm.sin(phase)
        trough: vec3 = vec3(0.02, 0.05, 0.14)
        crest: vec3 = vec3(0.10, 0.20, 0.55)
        t: float = 0.5 + 0.5 * wave
        one_minus_t: float = 1.0 - t
        rgb: vec3 = trough * one_minus_t + crest * t
        rgb4: vec4 = vec4(rgb.x, rgb.y, rgb.z, 1.0)
        band: float = t * 4.0
        if band >= 2.7:
            return (rgb4, rgb4, u_g3)
        if band >= 2.0:
            return (rgb4, rgb4, u_g2)
        if band >= 1.2:
            return (rgb4, rgb4, u_g1)
        return (rgb4, rgb4, u_g0)
    """
)


class ConcentricWavesDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self._bytecode, self._reg_settings = all_passes_compilation(
            SHADER_SRC,
            "concentric_waves",
            {
                GLOBAL_VAR_TT_TIME: float,
                "u_g0": int,
                "u_g1": int,
                "u_g2": int,
                "u_g3": int,
            },
        )
        _time_ty, self._time_reg = self._reg_settings.var_name_to_registers[
            GLOBAL_VAR_TT_TIME
        ]
        self._reg_settings.set_variable("u_g0", int(GLYPH_TROUGH))
        self._reg_settings.set_variable("u_g1", int(GLYPH_RIPPLE))
        self._reg_settings.set_variable("u_g2", int(GLYPH_RING))
        self._reg_settings.set_variable("u_g3", int(GLYPH_CREST))

        self.camera.set_zoom_2D(0.5)
        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)

        # Slot 0: static sentinel so cleared depth samples do not run TTSL everywhere.
        self.rc.material_buffer.add_static(
            (0, 0, 0),
            (0, 0, 0),
            find_glyph_indices_py(" "),
        )

        shader_mat = materials.ShaderPy(
            self._bytecode,
            time_f32_reg=self._time_reg,
            default_glyph=find_glyph_indices_py("."),
            register_seed=self._reg_settings.get_register_list(),
            ssa_json=self._reg_settings.ssa_json(),
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


class ConcentricWavesApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ConcentricWavesDemo()


if __name__ == "__main__":
    app = ConcentricWavesApp()
    app._disable_tooltips = True
    app.run()
