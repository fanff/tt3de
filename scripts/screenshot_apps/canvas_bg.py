# -*- coding: utf-8 -*-
"""The render context keeps a sentinel geometry slot that uses ``material_id == 0``; the
first ``add_static`` in each view therefore must define that slot, or "empty" pixels
pick up the scene's first real color (e.g. red ``R`` everywhere)."""

from __future__ import annotations

from tt3de.tt3de import find_glyph_indices_py


def seed_material0_void(material_buffer) -> None:
    """Reserve index 0 for background / uninitialized samples (near-black, space
    glyph)."""
    material_buffer.add_static(
        (0, 0, 0),
        (0, 0, 0),
        find_glyph_indices_py(" "),
    )
