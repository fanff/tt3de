

import pytest


from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de.glm.primitives.primitives import PrimitivesBuffer    
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer


from tt3de.glm.material.c_material import apply_pixel_shader


from tt3de.glm.material.c_material import Material
from tt3de.glm.material.c_material import MaterialBuffer

from tt3de.glm.primitives.primitive_builder import build_primitives  

from tt3de.glm.geometry.geometry import GeometryBuffer  

LOOP_COUNT = 1000
def cversion(primitive_buffer,drawing_buffer,mb,geometry_buffer):
    #for i in range(LOOP_COUNT):
    apply_pixel_shader(primitive_buffer,drawing_buffer,mb,geometry_buffer)

sizes = [32,64,128,256]
mode = [0,1,2]

@pytest.mark.parametrize('n', sizes)
@pytest.mark.parametrize('texture_mode', mode)
@pytest.mark.benchmark(group="pix_shader_loop")
def test_bench_full_pass_512(benchmark,n,texture_mode):

    mat = Material(texturemode=texture_mode)
    mat.set_albedo_front(1,2,3)
    mb = MaterialBuffer()   
    mb.add_material(mat)

    drawing_buffer = DrawingBuffer(n ,n)
    drawing_buffer.hard_clear(1000)
    

    # create a geometry buffer to hold the initial elemnts
    geometry_buffer = GeometryBuffer(1)


    
    primitive_buffer = PrimitivesBuffer(1)


    #build the primitives
    build_primitives(geometry_buffer,primitive_buffer)
    
    raster_precalc( primitive_buffer,  drawing_buffer)

    raster_all(primitive_buffer,drawing_buffer)
    
    benchmark(cversion,primitive_buffer,drawing_buffer,mb,geometry_buffer)

