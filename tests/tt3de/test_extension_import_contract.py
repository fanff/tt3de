import importlib

import pytest


TOP_LEVEL_EXPORTS = (
    "TextureBufferPy",
    "MaterialBufferPy",
    "GeometryBufferPy",
    "DrawingBufferPy",
    "VertexBufferPy",
    "TransformPackPy",
    "PrimitiveBufferPy",
    "build_primitives_py",
    "raster_all_py",
    "apply_material_py",
    "apply_material_py_parallel",
    "find_glyph_indices_py",
    "get_glyph_set",
    "materials",
    "toglyphmethod",
)

MATERIAL_EXPORTS = (
    "MaterialPy",
    "BaseTexturePy",
    "ShaderPy",
    "StaticColorPy",
    "StaticGlyphPy",
)

TO_GLYPH_METHOD_EXPORTS = (
    "ToGlyphMethodPy",
    "ToGlyphMethodPyMap4Luminance",
    "ToGlyphMethodPyStatic",
)


@pytest.mark.parametrize("name", TOP_LEVEL_EXPORTS)
def test_extension_top_level_export_is_importable(name):
    extension = importlib.import_module("tt3de.tt3de")

    assert getattr(extension, name) is not None


@pytest.mark.parametrize(
    ("module_name", "exports"),
    (
        ("materials", MATERIAL_EXPORTS),
        ("toglyphmethod", TO_GLYPH_METHOD_EXPORTS),
    ),
)
def test_extension_submodule_exports_are_importable(module_name, exports):
    extension = importlib.import_module("tt3de.tt3de")
    submodule = importlib.import_module(f"tt3de.tt3de.{module_name}")

    assert getattr(extension, module_name) is submodule
    for name in exports:
        assert getattr(submodule, name) is not None
