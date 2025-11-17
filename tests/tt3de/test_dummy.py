# -*- coding: utf-8 -*-


from pyglm import glm
def test_matrix_content():

    a = glm.identity(glm.mat4)
    b = glm.translate(glm.vec3(0.0, 0.0, 0.0))
    c = glm.scale(glm.vec3(1.0, 1.0, 1.0))

    assert a == b
    assert a == c
    assert b == c
