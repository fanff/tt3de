import math
import pytest


from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de.glm.primitives.primitives import PrimitivesBuffer
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

from tt3de.glm.primitives.primitive_builder import build_primitives

from tt3de.glm.geometry.geometry import GeometryBuffer
from tt3de.glm.material.c_material import MaterialBuffer
from tt3de.render_context_cy import CyRenderContext
from textual.geometry import Region


def version1(rc,size):
    rc.to_textual_(Region(0,0,size,size))

def version2(rc,size):
    rc.to_textual_2(Region(0,0,size,size))


sizes = [128, 256, 512, 768]


@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="to_textual")
def test_method1(benchmark, size):
    rc = CyRenderContext(size,size)

    benchmark(version1, rc,size)

@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="to_textual")
def test_method2(benchmark, size):
    rc = CyRenderContext(size,size)
    benchmark(version2, rc,size)




def canvas_to_list_hashed(rc,size):
    rc.drawing_buffer.canvas_to_list_hashed(0,0,size,size,rc.auto_buffer,rc.allchars)

@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="canvas_to_list_hashed")
def test_to_list_hashed(benchmark, size):
    rc = CyRenderContext(size,size)
    benchmark(canvas_to_list_hashed, rc,size)
