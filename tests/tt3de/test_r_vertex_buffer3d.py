# -*- coding: utf-8 -*-
from typing import Dict
import unittest

from pyglm import glm
from tt3de.tt3de import VertexBufferPy, TransformPackPy


class Test_VertexBuffer(unittest.TestCase):
    def test_create(self):
        abuffer = VertexBufferPy(32,32,323)
        trpack = TransformPackPy(232)
        self.assertEqual(abuffer.get_3d_len(), 0)
        abuffer.add_3d_vertex(1, 2, 3)
        self.assertEqual(abuffer.get_3d_vertex_tuple(0), (1.0, 2.0, 3.0, 1.0))
        self.assertEqual(abuffer.get_3d_len(), 1)
    def test_add_vertex(self):
        abuffer = VertexBufferPy(32,32,32)
        self.assertEqual(abuffer.get_3d_len(), 0)

        self.assertEqual(abuffer.add_3d_vertex(1, 2, 3), 0)
        self.assertEqual(abuffer.add_3d_vertex(12, 22, 32), 1)
        self.assertEqual(abuffer.add_3d_vertex(11, 21, 31), 2)
        self.assertEqual(abuffer.get_3d_len(), 3)

        self.assertEqual(abuffer.get_3d_vertex_tuple(0), (1.0, 2.0, 3.0, 1.0))
        self.assertEqual(abuffer.get_3d_vertex_tuple(1), (12.0, 22.0, 32.0, 1.0))
        self.assertEqual(abuffer.get_3d_vertex_tuple(2), (11.0, 21.0, 31.0, 1.0))

    def test_add_uv(self):
        abuffer = VertexBufferPy(32,32,32)

        self.assertEqual(abuffer.get_uv_size(), 0)

        retidex = abuffer.add_uv(
            glm.vec2(1.0, 1.5), glm.vec2(2.0, 2.5), glm.vec2(3.0, 3.5)
        )
        self.assertEqual(retidex, 0)
        self.assertEqual(abuffer.get_uv_size(), 1)

        ret1 = abuffer.add_uv(
            glm.vec2(1.1, 1.1), glm.vec2(2.1, 2.1), glm.vec2(3.1, 3.1)
        )
        self.assertEqual(ret1, 1)
        self.assertEqual(abuffer.get_uv_size(), 2)

        self.assertEqual(abuffer.get_uv(0), ((1.0, 1.5), (2.0, 2.5), (3.0, 3.5)))
        # self.assertEqual(abuffer.get_uv(1),(
        #     (1.1,1.1),
        #     (2.1,2.1),
        #     (3.1,3.1)
        # )
        #
        # )

    def test_apply_mv_3D(self):
        abuffer = VertexBufferPy(32,32,32)
        trpack = TransformPackPy(23)

        trpack.add_node_transform(glm.translate(glm.vec3(1, 2, 3)))

        trpack.set_view_matrix_glm(glm.identity(glm.mat4))

        for i in range(abuffer.get_3d_capacity()):
            abuffer.add_3d_vertex(1 + i, 2 + i, 3 + i)

        abuffer.apply_mv(trpack, 0, 0, abuffer.get_3d_capacity())

        z = abuffer.get_3d_vertex_tuple(0)
        self.assertEqual(z, (1.0, 2.0, 3.0, 1.0))

        z = abuffer.get_3d_vertex_tuple(1)
        self.assertEqual(z, (2.0, 3.0, 4.0, 1.0))


        z0_mv = abuffer.get_3d_calculated_tuple(0)
        self.assertEqual(z0_mv, (2.0, 4.0, 6.0, 1.0))  # translated
        # check conformal with glm calculation :
        res = glm.translate(glm.vec3(1, 2, 3)) * glm.mat4(1) * glm.vec4(1, 2, 3, 1)
        self.assertEqual(z0_mv, res.to_tuple())
