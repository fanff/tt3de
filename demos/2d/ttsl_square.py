# -*- coding: utf-8 -*-
"""End-to-end TTSL pipeline demo.

Compiles a tiny TTSL shader once at startup and, every frame, runs the produced
bytecode with the current `tt_Time` to derive a single RGB color. That color is
written into material slot 0 of the render context, which a centered 2D square
is bound to.

This validates the full path:
    shader source -> IR -> SSA -> bytecode -> ttsl_run -> glm.vec3 -> material -> render

Run:
    uv run python demos/2d/ttsl_square.py
"""

from textwrap import dedent

from pyglm import glm
from textual.app import App, ComposeResult
from textual.widgets import Header

from tt3de.glm_camera import ViewportScaleMode
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py, ttsl_run
from tt3de.tt_2dnodes import TT2DNode, TT2DUnitSquare
from tt3de.ttsl.compiler import GLOBAL_VAR_TT_TIME, all_passes_compilation


SHADER_SRC = dedent(
    """
    def my_shader(tt_FragCoord: vec2) -> vec3:
        pulse: float = abs(glm.sin(tt_Time))
        return vec3(pulse, 0.2, 1.0 - pulse)
    """
)


def _vec3_to_rgb(v: glm.vec3) -> tuple[int, int, int]:
    return (
        max(0, min(255, int(v.x * 255))),
        max(0, min(255, int(v.y * 255))),
        max(0, min(255, int(v.z * 255))),
    )


class TTSLSquareDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self._bytecode, self._reg_settings = all_passes_compilation(
            SHADER_SRC, "my_shader", {}
        )

        self.camera.set_zoom_2D(0.5)
        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)

        self._full_block_glyph = find_glyph_indices_py("█")
        self.rc.material_buffer.add_static(
            (0, 0, 0), (0, 0, 0), self._full_block_glyph
        )

        self.root2Dnode = TT2DNode()
        self.root2Dnode.add_child(
            TT2DUnitSquare(
                transform=glm.scale(glm.vec3(1.5, 1.5, 1.0)),
                material_id=0,
                centered=True,
            )
        )
        self.rc.append_root(self.root2Dnode)

    def update_step(self, delta_time: float) -> None:
        self._reg_settings.set_variable(
            GLOBAL_VAR_TT_TIME, float(self.time_since_start())
        )
        regs = self._reg_settings.get_register_list()

        front, _back, _glyph = ttsl_run(*regs, self._bytecode)

        rgb = _vec3_to_rgb(front)
        # Slot 0 is rebuilt each frame so the existing geometry binding to
        # material_id=0 picks up the latest shader output without re-syncing.
        self.rc.material_buffer.clear()
        self.rc.material_buffer.add_static(rgb, rgb, self._full_block_glyph)

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
