import pytest


from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de.glm.primitives.primitives import PrimitivesBuffer
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer
from tt3de.glm.c_texture import TextureArray


from tt3de.glm.material.c_material import apply_pixel_shader


from tt3de.glm.material.c_material import Material
from tt3de.glm.material.c_material import MaterialBuffer

from tt3de.glm.primitives.primitive_builder import build_primitives

from tt3de.glm.geometry.geometry import GeometryBuffer

LOOP_COUNT = 1000


def rversion(gb):
    gb.apply_material()


sizes = [16,32, 64, 128, 256,512]


@pytest.mark.parametrize("n", sizes)
@pytest.mark.benchmark(group="pix_shader_loop")
def test_bench_full_pass(benchmark, n):

    from rtt3de import AbigDrawing

    gb = AbigDrawing(n,n)
    gb.hard_clear(100.0)

    
    benchmark(rversion,gb)
