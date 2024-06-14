import math
import pytest


from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de.glm.primitives.primitives import PrimitivesBuffer
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

from tt3de.glm.primitives.primitive_builder import build_primitives

from tt3de.glm.geometry.geometry import GeometryBuffer
from tt3de.glm.material.c_material import MaterialBuffer


def cversion(primitive_buffer, drawing_buffer, material_buffer):
    raster_all(primitive_buffer, drawing_buffer, material_buffer)


sizes = [32, 64, 128, 256, 512, 2048, 4096]


@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="triangle_raster")
def test_bench_triangle_raster(benchmark, size):

    drawing_buffer = DrawingBuffer(256, 256)
    drawing_buffer.hard_clear(1000)

    # create a geometry buffer to hold the initial elemnts
    geometry_buffer = GeometryBuffer(2000)

    primitive_buffer = PrimitivesBuffer(2000)

    for i in range(1000):

        point_a = [2, 2, 1]
        point_b = [size, 5, 1]
        point_c = [5, size, 1]
        uv_array = [0.1] * 48
        node_id = 102
        material_id = 202
        geometry_buffer.add_triangle_to_buffer(
            point_a, point_b, point_c, uv_array, node_id, material_id
        )

    # build the primitives
    build_primitives(geometry_buffer, primitive_buffer)

    raster_precalc(primitive_buffer, drawing_buffer)

    benchmark(cversion, primitive_buffer, drawing_buffer, MaterialBuffer())
