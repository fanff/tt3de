# -*- coding: utf-8 -*-
import pytest

from tt3de.render_context_rust import RustRenderContext
from tt3de.tt3de import (
    DrawingBufferPy,
    MaterialBufferPy,
    PrimitiveBufferPy,
    TextureBufferPy,
    VertexBufferPy,
    apply_material_py_parallel,
)


def test_drawing_buffer_default_parallel_threads_is_eight():
    db = DrawingBufferPy(4, 4)
    assert db.material_parallel_threads == 8


def test_drawing_buffer_serial_has_no_pool():
    db = DrawingBufferPy(4, 4, material_parallel_threads=0)
    assert db.material_parallel_threads is None


def test_apply_material_parallel_errors_without_pool():
    db = DrawingBufferPy(2, 2, material_parallel_threads=0)
    mb = MaterialBufferPy(4)
    tb = TextureBufferPy(4)
    vb = VertexBufferPy(4, 4, 4)
    pb = PrimitiveBufferPy(4)
    with pytest.raises(ValueError, match="no material thread pool"):
        apply_material_py_parallel(mb, tb, vb, pb, db)


def test_rust_render_context_serial_has_no_parallel_threads_attr():
    rc = RustRenderContext(16, 16, material_parallel_threads=None)
    assert rc._material_parallel_threads is None
    assert rc.drawing_buffer.material_parallel_threads is None


def test_rust_render_context_default_parallel_threads_eight():
    rc = RustRenderContext(16, 16)
    assert rc._material_parallel_threads == 8
    assert rc.drawing_buffer.material_parallel_threads == 8
