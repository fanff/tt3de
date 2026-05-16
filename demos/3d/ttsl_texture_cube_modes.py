# -*- coding: utf-8 -*-
"""Combined TTSL texture cube: single vs dual vertical sample and texture filter.

Rotating cube on ``models/test_screen32.bmp``. Four **material** presets (all
built at init): ``█`` full-block with one UV vs ``▀`` half-block with
``tt_TexCoord0`` / ``tt_TexCoord1``, crossed with **nearest** vs **bilinear**
texture filtering (two texture buffer entries, ``u_TextureIndex`` in TTSL).
A **Textual** ``RadioSet`` sits in a dedicated top row; the 3D view fills the
rest (vertical split so controls stay visible).

See also: ``ttsl_texture_cube.py`` (simple + default bilinear),
``ttsl_texture_half_block_cube.py`` (double-sample).

Run:
    uv run python demos/3d/ttsl_texture_cube_modes.py
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from pyglm import glm
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, RadioButton, RadioSet

from tt3de.asset_fastloader import fast_load
from tt3de.glm_camera import ViewportScaleMode
from tt3de.prefab3d import Prefab3D
from tt3de.richtexture import ImageTexture
from tt3de.textual_standalone import TT3DViewStandAlone
from tt3de.tt3de import find_glyph_indices_py, materials  # type: ignore[reportMissingImports]
from tt3de.tt_3dnodes import TT3DNode
from tt3de.ttsl.compiler import all_passes_compilation

CUBE_SCALE = 3.05
SHADER_UNIFORM_TEXIDX = "u_TextureIndex"

SHADER_SIMPLE = dedent(
    """
    def texshade_simple(tt_TexCoord0: vec2) -> tuple[vec4, vec4, int]:
        s: vec4 = tt_texture(u_TextureIndex, tt_TexCoord0)
        rgb: vec4 = vec4(s.x, s.y, s.z, 1.0)
        return (rgb, rgb, 0)
    """
)

SHADER_DOUBLE = dedent(
    """
    def texshade_double(
        tt_TexCoord0: vec2,
        tt_TexCoord1: vec2,
    ) -> tuple[vec4, vec4, int]:
        upper: vec4 = tt_texture(u_TextureIndex, tt_TexCoord0)
        lower: vec4 = tt_texture(u_TextureIndex, tt_TexCoord1)
        top_rgb: vec4 = vec4(upper.x, upper.y, upper.z, 1.0)
        bot_rgb: vec4 = vec4(lower.x, lower.y, lower.z, 1.0)
        return (top_rgb, bot_rgb, 0)
    """
)

_GD_TEX = {SHADER_UNIFORM_TEXIDX: int}


class TTSLTextureCubeModesDemo(TT3DViewStandAlone):
    """3D view with four prebuilt shader materials; use ``set_sampling_mode``."""

    def initialize(self) -> None:
        simple_bc, simple_rs = all_passes_compilation(
            SHADER_SIMPLE, "texshade_simple", _GD_TEX
        )
        double_bc, double_rs = all_passes_compilation(
            SHADER_DOUBLE, "texshade_double", _GD_TEX
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
        w, h = img.image_width, img.image_height
        data = img.chained_data()
        tex_nearest = self.rc.texture_buffer.add_texture(
            w, h, data, True, True, filter_mode="nearest"
        )
        tex_bilinear = self.rc.texture_buffer.add_texture(
            w, h, data, True, True, filter_mode="bilinear"
        )

        full_block = find_glyph_indices_py("█")
        half_block = find_glyph_indices_py("▀")

        mats: list[int] = []
        for tex_idx in (tex_nearest, tex_bilinear):
            regs = simple_rs.fork()
            regs.set_variable(SHADER_UNIFORM_TEXIDX, tex_idx)
            mats.append(
                self.rc.material_buffer.add_shader(
                    materials.ShaderPy(
                        simple_bc,
                        default_glyph=full_block,
                        register_seed=regs.get_register_list(),
                    )
                )
            )
        for tex_idx in (tex_nearest, tex_bilinear):
            regs = double_rs.fork()
            regs.set_variable(SHADER_UNIFORM_TEXIDX, tex_idx)
            mats.append(
                self.rc.material_buffer.add_shader(
                    materials.ShaderPy(
                        double_bc,
                        default_glyph=half_block,
                        register_seed=regs.get_register_list(),
                    )
                )
            )

        self._material_ids = tuple(mats)

        s = CUBE_SCALE
        self._cube_scale = glm.scale(glm.vec3(s, s, s))

        self.root3Dnode = TT3DNode()
        self._cube = Prefab3D.unitary_cube()
        self._cube.material_id = self._material_ids[0]
        self._cube.local_transform = self._cube_scale
        self.root3Dnode.add_child(self._cube)
        self.rc.append_root(self.root3Dnode)

    def set_sampling_mode(self, index: int) -> None:
        if 0 <= index < len(self._material_ids):
            self._cube.set_material_id(self._material_ids[index])

    def update_step(self, delta_time: float) -> None:
        angle = self.time_since_start() * 0.9
        rot = glm.rotate(angle, glm.vec3(0.0, 1.0, 0.0))
        self._cube.set_local_transform(rot * self._cube_scale)

    def before_render_step(self) -> None:
        pass

    def post_render_step(self) -> None:
        pass


class TextureCubeModesPane(Container):
    """Radio strip above a full-size 3D view (vertical split; reliable on Textual
    8+)."""

    DEFAULT_CSS = """
    TextureCubeModesPane {
        height: 1fr;
        width: 100%;
        layout: vertical;
    }
    #mode-radios {
        height: auto;
        width: 100%;
        min-height: 3;
        margin: 2 0 0 0;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    #view-slot {
        height: 1fr;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield RadioSet(
            RadioButton("simple, nearest", value=True),
            RadioButton("simple, bilinear"),
            RadioButton("double, nearest"),
            RadioButton("double, bilinear"),
            id="mode-radios",
        )
        yield Container(id="view-slot")

    async def on_mount(self) -> None:
        slot = self.query_one("#view-slot", Container)
        demo = TTSLTextureCubeModesDemo()
        await slot.mount(demo)
        demo.focus()
        rs = self.query_one("#mode-radios", RadioSet)
        idx = rs.pressed_index
        if idx < 0:
            idx = 0
        demo.set_sampling_mode(idx)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id != "mode-radios":
            return
        idx = event.radio_set.pressed_index
        if idx < 0:
            return
        self.query_one(TTSLTextureCubeModesDemo).set_sampling_mode(idx)


class TTSLTextureCubeModesApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TextureCubeModesPane()


def build_demo_widget() -> Container:
    """Launcher hook used by ``demos/all.py`` to mount composite demo UIs."""
    return TextureCubeModesPane()


if __name__ == "__main__":
    app = TTSLTextureCubeModesApp()
    app._disable_tooltips = True
    app.run()
