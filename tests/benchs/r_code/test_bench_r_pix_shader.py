import pytest
from rtt3de import AbigDrawing
from rtt3de import apply_material_py
from rtt3de import MaterialBufferPy
from rtt3de import TextureBufferPy,VertexBufferPy,PrimitiveBufferPy


def rversion(material_buffer,texture_buffer,vertex_buffer,primitive_buffer,drawing_buffer):
    apply_material_py(material_buffer,texture_buffer,vertex_buffer,primitive_buffer,drawing_buffer)


sizes = [16,32, 64, 128, 256,512]


@pytest.mark.parametrize("n", sizes)
@pytest.mark.benchmark(group="pix_shader_loop")
def test_bench_full_pass(benchmark, n):

    texture_buffer = TextureBufferPy(12)

    material_buffer = MaterialBufferPy()
    material_buffer.add_static((255,90,90,255),(5,10,20,255),0) 


    drawing_buffer = AbigDrawing(n,n)
    drawing_buffer.hard_clear(100.0)
    vertex_buffer = VertexBufferPy()
    primitive_buffer = PrimitiveBufferPy(3)
    
    benchmark(rversion,material_buffer,texture_buffer,vertex_buffer,primitive_buffer,drawing_buffer)
