# -*- coding: utf-8 -*-
import unittest
from typing import Dict
import unittest

from pyglm import glm
from tt3de.tt3de import VertexBufferPy, TransformPackPy


class Test_TransformationPack(unittest.TestCase):
    def test_create(self):
        trpack = TransformPackPy(23)

    def test_add_node(self):

        transform_buffer = TransformPackPy(128)

        m4 = glm.translate(glm.vec3(1, 2, 3))

        self.assertEqual(transform_buffer.node_count(), 0)
        self.assertEqual(transform_buffer.add_node_transform(m4), 0)
        self.assertEqual(transform_buffer.node_count(), 1)

        self.assertEqual(transform_buffer.add_node_transform(m4), 1)
        self.assertEqual(transform_buffer.node_count(), 2)
        transform_buffer.clear()
        self.assertEqual(transform_buffer.node_count(), 0)

    def test_set_view(self):
        trpack = TransformPackPy(12)
        trpack.set_view_matrix_glm(glm.translate(glm.vec3(1, 2, 3)))

        m4out = trpack.get_view_matrix()
        self.assertEqual(m4out, glm.translate(glm.vec3(1, 2, 3)))

    def test_apply_mv(self):

        abuffer = VertexBufferPy(32,32,32)
        trpack = TransformPackPy(12)

        trpack.set_view_matrix_glm(glm.translate(glm.vec3(1, 2, 3)))

        for i in range(abuffer.get_3d_capacity()):
            abuffer.add_3d_vertex(1 + i, 2 + i, 3 + i)

        abuffer.apply_mv(trpack, node_id=0, start=0, end=32)
