




import pytest

import glm

def rversion(abuffer, trpack):
    abuffer.apply_mv(trpack,0,128)

@pytest.mark.benchmark(group="matrix_mult")
def test_r_mmulti(benchmark):

    from rtt3de import VertexBufferPy,TransformPackPy
    abuffer = VertexBufferPy()
    trpack = TransformPackPy()

    trpack.set_model_matrix_glm(glm.translate(glm.vec3(1,2,3)))
    trpack.set_view_matrix_glm(glm.translate(glm.vec3(1,2,3)))

    for i in range(abuffer.get_max_content()):
        abuffer.set_v3(1+i,2+i,3+i,i)
        
    benchmark(rversion,abuffer,trpack)
