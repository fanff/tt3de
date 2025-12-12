class MaterialPy: ...

class ComboMaterialPy(MaterialPy):
    count: int
    idx0: int
    idx1: int
    idx2: int
    idx3: int
    idx4: int

    def __init__(self) -> "ComboMaterialPy": ...
    def from_list(lst: list[int]) -> "ComboMaterialPy": ...

class StaticColorPy(MaterialPy):
    front: bool
    back: bool
    glyph: bool
    front_color: tuple[int, int, int, int]
    back_color: tuple[int, int, int, int]
    glyph_idx: int
    def __init__(
        self,
        front: bool,
        back: bool,
        glyph: bool,
        front_color: tuple[int, int, int, int],
        back_color: tuple[int, int, int, int],
        glyph_idx: int,
    ) -> "StaticColorPy":
        """
        Initialize a StaticColorPy material.
        """
        ...

class ToGlyphMethodPy:
    pass

class ToGlyphMethodPyStatic(ToGlyphMethodPy):
    glyph_idx: int

    def __init__(self, glyph_idx: int) -> "ToGlyphMethodPyStatic": ...

class ToGlyphMethodPyMap4Luminance(ToGlyphMethodPy):
    glyph_idx: tuple[int, int, int, int]
    # glyph_set: (u8, u8, u8, u8)
    def __init__(
        self, glyph_set: tuple[int, int, int, int]
    ) -> "ToGlyphMethodPyMap4Luminance": ...

class BaseTexturePy(MaterialPy):
    albedo_texture_idx: int
    albedo_texture_subid: int
    glyph_texture_idx: int
    glyph_texture_subid: int

    front: bool
    back: bool
    glyph: bool
    glyph_uv_0: bool

    front_uv_0: bool
    back_uv_0: bool
    glyph_method: "ToGlyphMethodPy"

    def __init__(
        self,
        albedo_texture_idx: int,
        albedo_texture_subid: int = 0,
        glyph_texture_idx: int = 0,
        glyph_texture_subid: int = 0,
        front: bool = True,
        back: bool = False,
        glyph: bool = False,
        glyph_uv_0: bool = True,
        front_uv_0: bool = True,
        back_uv_0: bool = True,
        glyph_method: "ToGlyphMethodPy" = ...,
    ) -> "BaseTexturePy": ...
