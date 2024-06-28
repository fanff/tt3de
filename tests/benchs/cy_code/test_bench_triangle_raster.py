import math
import pytest


from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de. glm.primitives.primitives import PrimitivesBuffer
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

from tt3de.glm.primitives.primitive_builder import build_primitives

from tt3de.glm.geometry.geometry import GeometryBuffer
from tt3de.glm.material.c_material import MaterialBuffer


def cversion(primitive_buffer, drawing_buffer, material_buffer):
    raster_all(primitive_buffer, drawing_buffer, material_buffer)


sizes = [32, 64,128, 256, 512, 2048, 4096]


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


from rtt3de import PrimitiveBufferPy
from rtt3de import AbigDrawing

from rtt3de import raster_all_py


def rust_version(primitive_buffer, drawing_buffer):
    raster_all_py(primitive_buffer, drawing_buffer)


@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="triangle_raster")
def test_bench_rust_triangle_raster(benchmark, size):

    drawing_buffer = AbigDrawing(256, 256)
    drawing_buffer.hard_clear(1000)

    primitive_buffer = PrimitiveBufferPy(2000)
    
    # create a geometry buffer to hold the initial elemnts
    for i in range(1000):

        primitive_buffer.add_triangle(
            102, # node
            i, # geom
            303,  # material 
            2, # row col
            2,
            1.0,

            5,  # top
            size, # right
            1.0,


            6, # bottom
            size, # left 
            1.0,
        )

    benchmark(rust_version, primitive_buffer, drawing_buffer)



TRI_MODE = ["STACK", "SAME","BELLOW"]
TRI_COUT = [100,1000,10000]

@pytest.mark.parametrize("mode", TRI_MODE)
@pytest.mark.parametrize("tri_count", TRI_COUT)
@pytest.mark.benchmark(group="triangle_rust_raster")
def test_bench_rust_triangle_raster_mode(benchmark,mode,tri_count):
    size = 64
    drawing_buffer = AbigDrawing(256, 256)
    drawing_buffer.hard_clear(10000)

    primitive_buffer = PrimitiveBufferPy(tri_count+1)


    if mode=="STACK":
        # every triangle is "above the previous one"
        for i in range(tri_count):
            depth = float(tri_count-i)
            primitive_buffer.add_triangle(
                102, # node
                i, # geom
                303,  # material 
                2, # row col
                2,
                depth,

                5,  # top
                size, # right
                depth,


                6, # bottom
                size, # left 
                depth,
            )
    elif mode=="SAME":
        #ALL triangles have rigourousely 
        # the same depth
        for i in range(tri_count):

            primitive_buffer.add_triangle(
                102, # node
                i, # geom
                303,  # material 
                2, # row col
                2,
                1.0,

                5,  # top
                size, # right
                1.0,


                6, # bottom
                size, # left 
                1.0,
            )
    elif mode == "BELLOW":
        # every triangle is "bellow the previous one"
        for i in range(tri_count):
            depth = float(i+1)
            primitive_buffer.add_triangle(
                102, # node
                i, # geom
                303,  # material 
                2, # row col
                2,
                depth,

                5,  # top
                size, # right
                depth,


                6, # bottom
                size, # left 
                depth,
            )
    assert (primitive_buffer.primitive_count(), tri_count)
    benchmark(rust_version, primitive_buffer, drawing_buffer)


