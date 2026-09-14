# -*- coding: utf-8 -*-
"""Raster font sheet loading, tile slicing, and material lookup."""

from __future__ import annotations

import io
from pathlib import Path

import png
import pytest

from tt3de.asset_load import load_png
from tt3de.raster_font import (
    RasterFont,
    SpriteSheetLayout,
    load_font_sheet,
    sidecar_path_for,
    slice_sprite_tile,
    tile_index_for_char,
)
from tt3de.tt3de import MaterialBufferPy, TextureBufferPy, find_glyph_indices_py

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_FONT = REPO_ROOT / "models" / "fonts" / "default_32px.png"
EXAMPLE_LAYOUT = sidecar_path_for(EXAMPLE_FONT)

BLUE = (0, 0, 255)
RED = (255, 0, 0)


def _rgb_png_bytes(width: int, height: int, rows_rgb: list[list[int]]) -> io.BytesIO:
    buf = io.BytesIO()
    writer = png.Writer(width=width, height=height, greyscale=False, alpha=False)
    writer.write(buf, rows_rgb)
    buf.seek(0)
    return buf


def test_example_layout_grid_matches_sheet_description():
    layout = SpriteSheetLayout.load(EXAMPLE_LAYOUT)
    assert layout.tile_size == 32
    assert layout.columns == 8
    assert layout.rows == 8
    assert layout.transparent_rgb == BLUE
    assert layout.name_to_index["0"] == 0
    assert layout.name_to_index["7"] == 7
    assert layout.name_to_index["8"] == 8
    assert layout.name_to_index["9"] == 9
    assert layout.name_to_index["mouse_pointer_square_04"] == 10
    assert layout.name_to_index["mouse_pointer_square_03"] == 11
    assert layout.name_to_index["mouse_pointer_square_02"] == 12
    assert layout.name_to_index["mouse_pointer_square_01"] == 13
    assert layout.name_to_index["mouse_pointer"] == 14
    assert layout.name_to_index["cross"] == 15
    assert layout.name_to_index["space"] == 16
    assert layout.name_to_index["."] == 17
    assert layout.name_to_index[":"] == 18
    assert layout.char_to_index[" "] == 16
    assert layout.char_to_index[":"] == 18
    assert "mouse_pointer" not in layout.char_to_index
    assert "cross" in layout.comments


def test_tile_index_for_char_digits_colon_and_unknown():
    layout = SpriteSheetLayout.load(EXAMPLE_LAYOUT)
    mapping = layout.char_to_index
    assert tile_index_for_char("0", mapping) == 0
    assert tile_index_for_char("7", mapping) == 7
    assert tile_index_for_char(":", mapping) == 18
    assert tile_index_for_char(".", mapping) == 17
    assert tile_index_for_char(" ", mapping) == 16
    assert tile_index_for_char("A", mapping) == 16
    with pytest.raises(ValueError):
        tile_index_for_char("12", mapping)


def test_custom_char_to_tile_fallback():
    mapping = {"0": 3, " ": 9}
    assert tile_index_for_char("0", mapping) == 3
    assert tile_index_for_char("x", mapping) == 9


def test_layout_rejects_duplicate_names(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text(
        '{"tile_size": 32, "columns": 2, "rows": 1, "grid": [["0", "0"]]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        SpriteSheetLayout.load(path)


def test_load_png_chroma_key_and_bottom_origin():
    # Visual top row is red, red, visual bottom row is blue, green.
    rows = [
        [*RED, *RED],
        [*BLUE, 0, 255, 0],
    ]
    img = load_png(_rgb_png_bytes(2, 2, rows), transparent_colors=[BLUE])
    assert len(img) == 2
    assert img[0][0] == (*BLUE, 0)
    assert img[0][1] == (0, 255, 0, 255)
    assert img[1][0] == (*RED, 255)
    assert img[1][1] == (*RED, 255)


def test_slice_sprite_tile_top_left_is_index_zero():
    blue = (*BLUE, 0)
    red = (*RED, 255)
    # 64x64, 2x2 tiles of 32px, bottom-origin rows.
    img = []
    for y in range(64):
        visual_y_from_top = 63 - y
        tile_row = visual_y_from_top // 32
        row = []
        for x in range(64):
            tile_col = x // 32
            row.append(red if tile_row == 0 and tile_col == 0 else blue)
        img.append(row)

    w, h, pixels = slice_sprite_tile(img, 0, 32)
    assert (w, h) == (32, 32)
    assert len(pixels) == 32 * 32
    assert all(p == red for p in pixels)

    _, _, other = slice_sprite_tile(img, 1, 32)
    assert all(p == blue for p in other)


def test_example_font_sheet_is_8x8_of_32px_with_blue_key():
    assert EXAMPLE_FONT.is_file()
    img = load_font_sheet(EXAMPLE_FONT)
    assert len(img) == 256
    assert len(img[0]) == 256
    # Visual top-left of the sheet (digit 0 tile) lives in the last 32 bottom-origin rows.
    w, h, tile0 = slice_sprite_tile(img, 0, 32)
    assert (w, h) == (32, 32)
    assert any(px[3] == 0 and px[:3] == BLUE for px in tile0)
    assert any(px[3] == 255 for px in tile0)


def test_raster_font_load_assigns_stable_materials():
    layout = SpriteSheetLayout.load(EXAMPLE_LAYOUT)
    tb = TextureBufferPy(32)
    mb = MaterialBufferPy()
    mb.add_static((0, 0, 0), (0, 0, 0), find_glyph_indices_py(" "))
    font = RasterFont.load(tb, mb, EXAMPLE_FONT)

    ids = font.material_ids("12:34:56")
    assert len(ids) == 8
    assert ids[0] == font.material_id("1")
    assert ids[2] == font.material_id(":")
    assert font.material_id("1") != font.material_id("2")
    assert font.material_id(":") != font.material_id("1")
    assert font.tile_index("0") == 0
    assert font.texture_id("0") != font.texture_id("1")
    assert font.material_named("mouse_pointer") == font.material_by_tile[14]
    assert font.material_named("cross") == font.material_by_tile[15]
    assert font.tile_named("mouse_pointer_square_04") == 10
    # Slot 0 stays the static fill; glyph shaders are appended after it.
    assert min(font.material_by_tile.values()) >= 1
    assert tb.size() == len(layout.name_to_index)
    assert mb.count() == 1 + len(layout.name_to_index)


def test_space_tile_is_chroma_keyed_nearest():
    tb = TextureBufferPy(32)
    mb = MaterialBufferPy()
    mb.add_static((0, 0, 0), (0, 0, 0), find_glyph_indices_py(" "))
    font = RasterFont.load(tb, mb, EXAMPLE_FONT)
    tex = font.texture_named("space")
    rgba = tb.get_rgba_at(tex, 0.5, 0.5)
    assert rgba[3] == 0
    # Key RGB can remain in the texel; alpha 0 is what the compositor uses.
    assert rgba[2] == 255


def test_raster_font_custom_mapping_only_materializes_requested_tiles():
    tb = TextureBufferPy(8)
    mb = MaterialBufferPy()
    mb.add_static((0, 0, 0), (0, 0, 0), find_glyph_indices_py(" "))
    mapping = {"A": 0, "B": 1, " ": 16}
    font = RasterFont.load(
        tb,
        mb,
        EXAMPLE_FONT,
        char_to_tile=mapping,
    )
    assert font.material_id("A") == font.material_by_tile[0]
    assert font.material_id("B") == font.material_by_tile[1]
    assert font.material_id("z") == font.material_id(" ")
    assert set(font.material_by_tile) == {0, 1, 16}
    with pytest.raises(ValueError):
        RasterFont.load(tb, mb, EXAMPLE_FONT, char_to_tile={})
