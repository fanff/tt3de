# -*- coding: utf-8 -*-
"""Load chroma-keyed sprite-sheet fonts and build per-glyph shader materials.

This is an asset-loading convenience for 2D glyph quads. It does not lay out
text (no kerning, wrapping, baseline, or shaping).

Glyph names and character mapping live in a JSON sidecar next to the sheet
(``sheet.png`` + ``sheet.json``). Edit the JSON grid to add tiles.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Tuple

from tt3de.asset_load import load_bmp, load_png
from tt3de.tt3de import (  # type: ignore[reportMissingImports]
    MaterialBufferPy,
    TextureBufferPy,
    find_glyph_indices_py,
    materials,
)
from tt3de.ttsl.compiler import all_passes_compilation

DEFAULT_TILE_SIZE = 32
DEFAULT_TRANSPARENT_RGB = (0, 0, 255)
SHADER_UNIFORM_TEXIDX = "u_TextureIndex"
DEFAULT_SHADER_ENTRY = "glyph_tex"
SPACE_TILE_NAME = "space"

DEFAULT_GLYPH_SHADER = dedent(
    """
    def glyph_tex(tt_TexCoord0: vec2, tt_TexCoord1: vec2) -> tuple[vec4, vec4, int]:
        sampled_top: vec4 = tt_texture(u_TextureIndex, tt_TexCoord0)
        sampled_bottom: vec4 = tt_texture(u_TextureIndex, tt_TexCoord1)
        # Keyed texels (sheet blue / alpha 0) keep alpha 0 so the transparent
        # pass can show the background. Do not copy key RGB into either half-cell.
        if sampled_top.w < 0.5:
            top_rgb: vec4 = vec4(0.0, 0.0, 0.0, 0.0)
        else:
            if sampled_top.z > 0.8 and sampled_top.x < 0.15 and sampled_top.y < 0.15:
                top_rgb: vec4 = vec4(0.0, 0.0, 0.0, 0.0)
            else:
                top_rgb: vec4 = vec4(sampled_top.x, sampled_top.y, sampled_top.z, 1.0)
        if sampled_bottom.w < 0.5:
            bottom_rgb: vec4 = vec4(0.0, 0.0, 0.0, 0.0)
        else:
            if sampled_bottom.z > 0.8 and sampled_bottom.x < 0.15 and sampled_bottom.y < 0.15:
                bottom_rgb: vec4 = vec4(0.0, 0.0, 0.0, 0.0)
            else:
                bottom_rgb: vec4 = vec4(
                    sampled_bottom.x, sampled_bottom.y, sampled_bottom.z, 1.0
                )
        return (top_rgb, bottom_rgb, 0)
    """
)

Pixel = Tuple[int, int, int, int]
SheetRows = List[List[Pixel]]


def sidecar_path_for(image_path: str | Path) -> Path:
    """JSON layout path beside a glyph sheet image."""
    return Path(image_path).with_suffix(".json")


def char_for_tile_name(name: str) -> str | None:
    """Map a grid cell name to a character, if it is a character glyph."""
    if name == SPACE_TILE_NAME:
        return " "
    if len(name) == 1:
        return name
    return None


def tile_index_for_char(ch: str, char_to_tile: Mapping[str, int]) -> int:
    """Resolve one character to a sprite-sheet tile index.

    Unknown characters fall back to space when that mapping exists.
    """
    if len(ch) != 1:
        raise ValueError(f"expected a single character, got {ch!r}")
    if ch in char_to_tile:
        return char_to_tile[ch]
    if " " in char_to_tile:
        return char_to_tile[" "]
    raise KeyError(f"no tile for character {ch!r} and no space fallback")


@dataclass(frozen=True)
class SpriteSheetLayout:
    """Named tiles for one sprite sheet, loaded from a JSON sidecar."""

    path: Path
    tile_size: int
    columns: int
    rows: int
    transparent_rgb: Tuple[int, int, int]
    fallback_name: str
    comments: Dict[str, str] = field(default_factory=dict)
    name_to_index: Dict[str, int] = field(default_factory=dict)
    char_to_index: Dict[str, int] = field(default_factory=dict)

    @property
    def fallback_index(self) -> int:
        return self.name_to_index[self.fallback_name]

    @classmethod
    def load(cls, path: str | Path) -> SpriteSheetLayout:
        layout_path = Path(path)
        with layout_path.open("r", encoding="utf-8") as fin:
            raw = json.load(fin)
        return cls.from_dict(raw, path=layout_path)

    @classmethod
    def from_dict(
        cls, raw: Mapping[str, Any], *, path: Path
    ) -> SpriteSheetLayout:
        tile_size = int(raw.get("tile_size", DEFAULT_TILE_SIZE))
        if tile_size <= 0:
            raise ValueError(f"{path}: tile_size must be positive")

        grid = raw.get("grid")
        if not isinstance(grid, list) or not grid:
            raise ValueError(f"{path}: grid must be a non-empty list of rows")

        inferred_columns = max(len(row) for row in grid if isinstance(row, list))
        columns = int(raw.get("columns", inferred_columns))
        rows = int(raw.get("rows", len(grid)))
        if columns <= 0 or rows <= 0:
            raise ValueError(f"{path}: columns and rows must be positive")
        if len(grid) > rows:
            raise ValueError(
                f"{path}: grid has {len(grid)} rows but rows is {rows}"
            )

        transparent = raw.get("transparent_rgb", list(DEFAULT_TRANSPARENT_RGB))
        if (
            not isinstance(transparent, list)
            or len(transparent) != 3
            or not all(isinstance(c, int) for c in transparent)
        ):
            raise ValueError(f"{path}: transparent_rgb must be [r, g, b]")
        transparent_rgb = (int(transparent[0]), int(transparent[1]), int(transparent[2]))

        comments_raw = raw.get("comments", {})
        if not isinstance(comments_raw, dict):
            raise ValueError(f"{path}: comments must be an object")
        comments = {str(k): str(v) for k, v in comments_raw.items()}

        fallback_name = str(raw.get("fallback", SPACE_TILE_NAME))
        name_to_index: Dict[str, int] = {}
        char_to_index: Dict[str, int] = {}

        for row_i, row in enumerate(grid):
            if not isinstance(row, list):
                raise ValueError(f"{path}: grid row {row_i} must be a list")
            if len(row) > columns:
                raise ValueError(
                    f"{path}: grid row {row_i} has {len(row)} cells; columns is {columns}"
                )
            for col_i, cell in enumerate(row):
                if cell is None or cell == "":
                    continue
                if not isinstance(cell, str):
                    raise ValueError(
                        f"{path}: grid[{row_i}][{col_i}] must be a string or null"
                    )
                index = row_i * columns + col_i
                if cell in name_to_index:
                    raise ValueError(f"{path}: duplicate tile name {cell!r}")
                name_to_index[cell] = index
                mapped_char = char_for_tile_name(cell)
                if mapped_char is not None:
                    if mapped_char in char_to_index:
                        raise ValueError(
                            f"{path}: duplicate character {mapped_char!r}"
                        )
                    char_to_index[mapped_char] = index

        if fallback_name not in name_to_index:
            raise ValueError(
                f"{path}: fallback {fallback_name!r} is not in the grid"
            )

        return cls(
            path=path,
            tile_size=tile_size,
            columns=columns,
            rows=rows,
            transparent_rgb=transparent_rgb,
            fallback_name=fallback_name,
            comments=comments,
            name_to_index=name_to_index,
            char_to_index=char_to_index,
        )


def load_font_sheet(
    path: str | Path,
    *,
    alpha: int = 255,
    transparent_colors: List[Tuple[int, int, int]] | None = None,
) -> SheetRows:
    """Load a BMP or PNG glyph sheet as bottom-origin RGBA rows."""
    sheet_path = Path(path)
    if transparent_colors is None:
        transparent_colors = [DEFAULT_TRANSPARENT_RGB]
    suffix = sheet_path.suffix.lower()
    with sheet_path.open("rb") as fin:
        if suffix == ".png":
            return load_png(fin, alpha=alpha, transparent_colors=transparent_colors)
        if suffix == ".bmp":
            return load_bmp(fin, alpha=alpha, transparent_colors=transparent_colors)
    raise ValueError(f"Unsupported font sheet format: {sheet_path.suffix!r}")


def slice_sprite_tile(
    img_data: Sequence[Sequence[Pixel]],
    sprite_idx: int,
    tile_size: int = DEFAULT_TILE_SIZE,
) -> Tuple[int, int, List[Pixel]]:
    """Extract one tile as a standalone texture payload.

    ``img_data`` is bottom-origin (row 0 is the visual bottom), matching
    ``load_bmp`` / ``load_png``.
    """
    if tile_size <= 0:
        raise ValueError("tile_size must be positive")
    if not img_data or not img_data[0]:
        raise ValueError("font sheet has no pixels")
    width = len(img_data[0])
    height = len(img_data)
    if width % tile_size != 0 or height % tile_size != 0:
        raise ValueError(
            f"sheet {width}x{height} is not divisible by tile_size {tile_size}"
        )
    cols = width // tile_size
    rows = height // tile_size
    tile_col = sprite_idx % cols
    tile_row = sprite_idx // cols
    if tile_row >= rows:
        raise ValueError(
            f"sprite index {sprite_idx} is out of range for a {cols}x{rows} sheet"
        )
    tile_row_from_bottom = rows - tile_row - 1
    start_x = tile_col * tile_size
    start_y = tile_row_from_bottom * tile_size
    tile_pixels: List[Pixel] = []
    for y in range(start_y, start_y + tile_size):
        row = img_data[y]
        tile_pixels.extend(row[start_x : start_x + tile_size])
    return (tile_size, tile_size, tile_pixels)


class RasterFont:
    """Per-glyph texture and ``ShaderPy`` material ids for a sprite-sheet font."""

    def __init__(
        self,
        *,
        tile_size: int,
        texture_by_tile: Mapping[int, int],
        material_by_tile: Mapping[int, int],
        char_to_tile: Mapping[str, int],
        name_to_tile: Mapping[str, int] | None = None,
        layout: SpriteSheetLayout | None = None,
    ) -> None:
        self.tile_size = tile_size
        self.texture_by_tile = dict(texture_by_tile)
        self.material_by_tile = dict(material_by_tile)
        self.char_to_tile = dict(char_to_tile)
        self.name_to_tile = dict(name_to_tile or {})
        self.layout = layout

    @classmethod
    def load(
        cls,
        texture_buffer: TextureBufferPy,
        material_buffer: MaterialBufferPy,
        path: str | Path,
        *,
        tile_size: int | None = None,
        alpha: int = 255,
        transparent_colors: List[Tuple[int, int, int]] | None = None,
        char_to_tile: Mapping[str, int] | None = None,
        tile_indices: Iterable[int] | None = None,
        layout_path: str | Path | None = None,
        shader_src: str | None = None,
        shader_entry: str = DEFAULT_SHADER_ENTRY,
        texture_uniform: str = SHADER_UNIFORM_TEXIDX,
        default_glyph: int | None = None,
    ) -> RasterFont:
        """Slice a glyph sheet, upload per-tile textures, and add shader materials.

        Callers should keep material slot 0 as a static fill before loading.
        When ``char_to_tile`` is omitted, the JSON sidecar beside ``path`` is used.
        """
        if char_to_tile is not None and not char_to_tile:
            raise ValueError("char_to_tile mapping is empty")

        sheet_path = Path(path)
        sidecar = Path(layout_path) if layout_path is not None else sidecar_path_for(
            sheet_path
        )
        layout: SpriteSheetLayout | None = None
        if sidecar.is_file():
            layout = SpriteSheetLayout.load(sidecar)

        resolved_tile_size = (
            tile_size
            if tile_size is not None
            else (layout.tile_size if layout is not None else DEFAULT_TILE_SIZE)
        )
        if transparent_colors is None:
            if layout is not None:
                transparent_colors = [layout.transparent_rgb]
            else:
                transparent_colors = [DEFAULT_TRANSPARENT_RGB]

        resolved_chars: Dict[str, int]
        name_to_tile: Dict[str, int] = {}
        if char_to_tile is not None:
            resolved_chars = dict(char_to_tile)
        elif layout is not None:
            resolved_chars = dict(layout.char_to_index)
            name_to_tile = dict(layout.name_to_index)
        else:
            raise FileNotFoundError(
                f"no font layout sidecar at {sidecar}; pass char_to_tile or add a JSON grid"
            )

        if tile_indices is None:
            if name_to_tile:
                indices = sorted(set(name_to_tile.values()))
            else:
                indices = sorted(set(resolved_chars.values()))
        else:
            indices = list(tile_indices)
        if not indices:
            raise ValueError("tile_indices is empty")

        img_data = load_font_sheet(
            sheet_path, alpha=alpha, transparent_colors=transparent_colors
        )

        bytecode, reg_settings = all_passes_compilation(
            shader_src if shader_src is not None else DEFAULT_GLYPH_SHADER,
            shader_entry,
            {texture_uniform: int},
        )
        glyph = (
            find_glyph_indices_py("▀") if default_glyph is None else default_glyph
        )

        texture_by_tile: Dict[int, int] = {}
        material_by_tile: Dict[int, int] = {}
        for sprite_idx in indices:
            _w, _h, chained_data = slice_sprite_tile(
                img_data, sprite_idx, resolved_tile_size
            )
            tex_idx = texture_buffer.add_texture(
                resolved_tile_size,
                resolved_tile_size,
                chained_data,
                False,
                False,
                "nearest",
            )
            shader_regs = reg_settings.fork()
            shader_regs.set_variable(texture_uniform, tex_idx)
            mat_idx = material_buffer.add_shader(
                materials.ShaderPy(
                    bytecode,
                    default_glyph=glyph,
                    register_seed=shader_regs.get_register_list(),
                    ssa_json=shader_regs.ssa_json(),
                    blend_mode="alpha_blend",
                    glyph_policy="replace_from_shader",
                )
            )
            texture_by_tile[sprite_idx] = tex_idx
            material_by_tile[sprite_idx] = mat_idx

        return cls(
            tile_size=resolved_tile_size,
            texture_by_tile=texture_by_tile,
            material_by_tile=material_by_tile,
            char_to_tile=resolved_chars,
            name_to_tile=name_to_tile,
            layout=layout,
        )

    def tile_index(self, ch: str) -> int:
        return tile_index_for_char(ch, self.char_to_tile)

    def tile_named(self, name: str) -> int:
        try:
            return self.name_to_tile[name]
        except KeyError as exc:
            raise KeyError(f"no tile named {name!r}") from exc

    def material_id(self, ch: str) -> int:
        tile = self.tile_index(ch)
        try:
            return self.material_by_tile[tile]
        except KeyError as exc:
            raise KeyError(
                f"no material for character {ch!r} (tile {tile})"
            ) from exc

    def material_named(self, name: str) -> int:
        tile = self.tile_named(name)
        try:
            return self.material_by_tile[tile]
        except KeyError as exc:
            raise KeyError(f"no material named {name!r} (tile {tile})") from exc

    def material_ids(self, text: str) -> List[int]:
        return [self.material_id(ch) for ch in text]

    def texture_id(self, ch: str) -> int:
        tile = self.tile_index(ch)
        try:
            return self.texture_by_tile[tile]
        except KeyError as exc:
            raise KeyError(
                f"no texture for character {ch!r} (tile {tile})"
            ) from exc

    def texture_named(self, name: str) -> int:
        tile = self.tile_named(name)
        try:
            return self.texture_by_tile[tile]
        except KeyError as exc:
            raise KeyError(f"no texture named {name!r} (tile {tile})") from exc
