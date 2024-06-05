
import math
import pytest


from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de.glm.primitives.primitives import PrimitivesBuffer    
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

from tt3de.glm.primitives.primitive_builder import build_primitives  

from tt3de.glm.geometry.geometry import GeometryBuffer  

def cversion(primitive_buffer,drawing_buffer):
    raster_all(primitive_buffer,drawing_buffer)

sizes = [32,64,128,256,512,2048,4096]

@pytest.mark.parametrize('size', sizes)
@pytest.mark.benchmark(group="line_raster")
def test_bench_line_raster(benchmark,size):

    drawing_buffer = DrawingBuffer(512 ,512)
    drawing_buffer.hard_clear(1000)
    

    # create a geometry buffer to hold the initial elemnts
    geometry_buffer = GeometryBuffer(2000)



    primitive_buffer = PrimitivesBuffer(2000)

    for i in range(1000):
        ratio = i/float(1000)

        xdiff = size * math.cos( ratio * math.pi * 2)
        ydiff = size * math.sin( ratio * math.pi * 2)

        start = [256, 256, 1.0]
        end = [256+xdiff, 256+ydiff, 1]
        uv_array = [0.1] * 16
        node_id = 101
        material_id = 201
        geometry_buffer.add_line_to_buffer(start, end, uv_array, node_id, material_id)

    #build the primitives
    build_primitives(geometry_buffer,primitive_buffer)
    
    raster_precalc( primitive_buffer,  drawing_buffer)
    
    benchmark(cversion,primitive_buffer,drawing_buffer)