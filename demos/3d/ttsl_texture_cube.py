# -*- coding: utf-8 -*-
"""TTSL texture sampling on a centered rotating cube (full block ``█``).

Uses ``tt_texture(0, tt_TexCoord0)`` with ``ShaderPy``. Texture:
``models/test_screen32.bmp``.

For dual-sample / ``▀`` half-block detail see ``ttsl_texture_half_block_cube.py``.

Run:
    uv run python demos/3d/ttsl_texture_cube.py
"""

from pathlib import Path
from textwrap import dedent

from pyglm import glm
from textual.app import App, ComposeResult
from textual.widgets import Header

from tt3de.asset_fastloader import fast_load
from tt3de.glm_camera import ViewportScaleMode
from tt3de.prefab3d import Prefab3D
from tt3de.richtexture import ImageTexture
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py, materials  # type: ignore[reportMissingImports]
from tt3de.tt_3dnodes import TT3DNode
from tt3de.ttsl.compiler import all_passes_compilation

CUBE_SCALE = 2.0

SHADER_SRC = dedent(
    """
    def texshade(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
        s: vec4 = tt_texture(0, tt_TexCoord0)
        rgb: vec4 = vec4(s.x, s.y, s.z, 1.0)
        return (rgb, rgb, 0)
    """
)


class TTSLTextureCubeDemo(TT3DViewStandAlone):
    def initialize(self) -> None:
        self._bytecode, self._reg_settings = all_passes_compilation(
            SHADER_SRC, "texshade", {}
        )

        self.camera.set_viewport_scale_mode(ViewportScaleMode.FIT)
        self.camera.point_at(glm.vec3(0.0, 0.0, 0.0))

        self.rc.material_buffer.add_static(
            (0, 0, 0),
            (0, 0, 0),
            find_glyph_indices_py(" "),
        )

        bmp_path = Path(__file__).resolve().parents[2] / "models" / "test_screen32.bmp"
        img: ImageTexture = fast_load(str(bmp_path))
        self.rc.texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )

        full_block_glyph = find_glyph_indices_py("█")
        shader_mat = materials.ShaderPy(
            self._bytecode,
            default_glyph=full_block_glyph,
            register_seed=self._reg_settings.get_register_list(),
        )
        self._shader_mat_id = self.rc.material_buffer.add_shader(shader_mat)

        s = CUBE_SCALE
        self._cube_scale = glm.scale(glm.vec3(s, s, s))

        self.root3Dnode = TT3DNode()
        self._cube = Prefab3D.unitary_cube()
        self._cube.material_id = self._shader_mat_id
        self._cube.local_transform = self._cube_scale
        self.root3Dnode.add_child(self._cube)
        self.rc.append_root(self.root3Dnode)

    def update_step(self, delta_time: float) -> None:
        angle = self.time_since_start() * 0.9
        rot = glm.rotate(angle, glm.vec3(0.0, 1.0, 0.0))
        self._cube.set_local_transform(rot * self._cube_scale)

    def before_render_step(self) -> None:
        pass

    def post_render_step(self) -> None:
        pass


class TTSLTextureCubeApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TTSLTextureCubeDemo()


if __name__ == "__main__":
    app = TTSLTextureCubeApp()
    app._disable_tooltips = True
    app.run()
