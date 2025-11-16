# -*- coding: utf-8 -*-
from typing import Dict
import unittest

from pyglm import glm
from tt3de.tt3de import VertexBufferPy, TransformPackPy


class Test_VertexBuffer2D(unittest.TestCase):

    def setUp(self):
        self.abuffer = VertexBufferPy(32,32,32)
    def test_create(self):
        abuffer = self.abuffer
        trpack = TransformPackPy(232)
        self.assertEqual(abuffer.get_2d_len(), 0)
        abuffer.add_2d_vertex(1, 2, 3)
        self.assertEqual(abuffer.get_2d_vertex_tuple(0), (1.0, 2.0, 3.0, 1.0))
        self.assertEqual(abuffer.get_2d_len(), 1)
    def test_add_vertex(self):
        abuffer = self.abuffer
        self.assertEqual(abuffer.get_2d_len(), 0)

        self.assertEqual(abuffer.add_2d_vertex(1, 2, 3), 0)
        self.assertEqual(abuffer.add_2d_vertex(12, 22, 32), 1)
        self.assertEqual(abuffer.add_2d_vertex(11, 21, 31), 2)
        self.assertEqual(abuffer.get_2d_len(), 3)

        self.assertEqual(abuffer.get_2d_vertex_tuple(0), (1.0, 2.0, 3.0, 1.0))
        self.assertEqual(abuffer.get_2d_vertex_tuple(1), (12.0, 22.0, 32.0, 1.0))
        self.assertEqual(abuffer.get_2d_vertex_tuple(2), (11.0, 21.0, 31.0, 1.0))



    def test_apply_mv(self):
        abuffer = self.abuffer
        trpack = TransformPackPy(23)

        node_id = trpack.add_node_transform(glm.translate(glm.vec3(1, 2, 3)))

        trpack.set_view_matrix_glm(glm.identity(glm.mat4))

        for i in range(abuffer.get_2d_capacity()):
            abuffer.add_2d_vertex(1 + i, 2 + i, 3 + i)

        abuffer.apply_2d_mv(trpack, node_id, 0, abuffer.get_2d_len())

        z = abuffer.get_2d_vertex_tuple(0)
        self.assertEqual(z, (1.0, 2.0, 3.0, 1.0))

        z = abuffer.get_2d_vertex_tuple(1)
        self.assertEqual(z, (2.0, 3.0, 4.0, 1.0))


        z0_mv = abuffer.get_2d_calculated_tuple(0)
        self.assertEqual(z0_mv, (2.0, 4.0, 6.0, 1.0))  # translated
        # check conformal with glm calculation :
        res = glm.translate(glm.vec3(1, 2, 3)) * glm.mat4(1) * glm.vec4(1, 2, 3, 1)
        self.assertEqual(z0_mv, res.to_tuple())
