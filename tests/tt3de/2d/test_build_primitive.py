# -*- coding: utf-8 -*-

import unittest

from pyglm import glm

from tt3de.tt3de import GeometryBufferPy, PrimitiveBufferPy,build_primitives_py,TransformPackPy,DrawingBufferPy,VertexBufferPy



class Test_2DBuildPrimitives(unittest.TestCase):
    def setUp(self):
        # create a default GeometryBufferPy before each test
        self.geom_buffer = GeometryBufferPy(32)
        self.vertex_buffer = VertexBufferPy(32,32,32)
        self.transform_buffer =  TransformPackPy(32)
        self.drawing_buffer= DrawingBufferPy(32, 32)
        self.primitive_buffer= PrimitiveBufferPy(32)

    def test_empty(self):
        build_primitives_py(
            self.geom_buffer,
            self.vertex_buffer,
            self.transform_buffer,
            self.drawing_buffer,
            self.primitive_buffer
        )
        self.assertEqual(self.primitive_buffer.primitive_count(), 0)
    def test_points2d(self):
        geom_buffer = self.geom_buffer
        geom_buffer.add_point(0,0,node_id=0,material_id=0)
        vertex_buffer = self.vertex_buffer
        transform_buffer = self.transform_buffer
        drawing_buffer = self.drawing_buffer
        primitive_buffer = self.primitive_buffer


        primitive_buffer.clear()
        node_id =transform_buffer.add_node_transform(glm.translate(glm.vec3(0.0,0.0,0.0)))
        transform_buffer.set_view_matrix_glm(glm.scale(glm.vec3(0.1,0.1,1.0)))
        # add some vertices
        for i in range(5):
            vertex_buffer.add_2d_vertex(float(i), float(i*2), 0.1)
        self.assertEqual(vertex_buffer.get_2d_len(), 5)
        material_id = 0
        uv_idx = 0
        geom_buffer.add_points_2d(
            0,
            5,
            uv_idx,
            node_id,
            material_id,
        )

        self.assertEqual(geom_buffer.geometry_count(), 2)
        elemnt_in_geom = geom_buffer.get_element(1)
        build_primitives_py(
            geom_buffer,
            vertex_buffer,
            transform_buffer,
            drawing_buffer,
            primitive_buffer
        )


        all_inputs = [vertex_buffer.get_2d_vertex_tuple(i) for i in range(5)]
        all_calcs = [vertex_buffer.get_2d_calculated_tuple(i) for i in range(5)]

        self.assertEqual(primitive_buffer.primitive_count(), 5)


    def test_rect2d(self):
        geom_buffer = self.geom_buffer
        geom_buffer.add_point(0,0,node_id=0,material_id=0)
        vertex_buffer = self.vertex_buffer
        transform_buffer = self.transform_buffer
        drawing_buffer = self.drawing_buffer
        primitive_buffer = self.primitive_buffer


        primitive_buffer.clear()
        node_id =transform_buffer.add_node_transform(glm.translate(glm.vec3(0.0,0.0,0.0)))
        transform_buffer.set_view_matrix_glm(glm.scale(glm.vec3(0.1,0.1,1.0)))
        # add two vertices for the rect (top-left and bottom-right)
        top_left_idx = vertex_buffer.add_2d_vertex(0.0, 0.0, 0.0)  # top-left
        bottom_right_idx = vertex_buffer.add_2d_vertex(8.0, 5.0, 0.0)  # bottom-right
        self.assertEqual(vertex_buffer.get_2d_len(), 2)
        material_id = 0

        uv_idx =vertex_buffer.add_uv(glm.vec2(0,0),glm.vec2(1,1),glm.vec2(0.0,0.0))
        geom_buffer.add_rect2d(
            top_left_idx,
            uv_idx,
            node_id,
            material_id,
        )

        self.assertEqual(geom_buffer.geometry_count(), 2)
        elemnt_in_geom = geom_buffer.get_element(1)
        build_primitives_py(
            geom_buffer,
            vertex_buffer,
            transform_buffer,
            drawing_buffer,
            primitive_buffer
        )


        all_inputs = [vertex_buffer.get_2d_vertex_tuple(i) for i in range(2)]
        all_calcs = [vertex_buffer.get_2d_calculated_tuple(i) for i in range(2)]

        self.assertEqual(primitive_buffer.primitive_count(), 1)
        rect_prim = primitive_buffer.get_primitive(0)
        self.assertEqual(rect_prim["_type"], "rect")
