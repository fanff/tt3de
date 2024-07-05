




import pytest

import glm

def rversion(abuffer, trpack):
    abuffer.apply_mv(trpack,0,128)

@pytest.mark.benchmark(group="matrix_mult")
def test_r_mmulti(benchmark):

    from rtt3de import VertexBufferPy,TransformPackPy
    abuffer = VertexBufferPy()
    trpack = TransformPackPy(12)

    trpack.set_view_matrix_glm(glm.translate(glm.vec3(1,2,3)))

    for i in range(abuffer.get_max_content()):
        abuffer.add_vertex(1+i,2+i,3+i)
        
    benchmark(rversion,abuffer,trpack)
