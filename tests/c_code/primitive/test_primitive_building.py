import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture


from tt3de.glm.primitives.primitives import PrimitivesBuffer
import itertools

from tt3de.glm.geometry.geometry import GeometryBuffer

from tt3de.glm.primitives.primitive_builder import build_primitives


class Test_PrimitiveBuilding(unittest.TestCase):

    def test_with_over_flow(self):
        # create a geometry buffer  of 50
        # create a Primitive buffer  of 10
        # add some geomtry to the buffer, like 20 triangles
        # do the "build primitive" function
        # check that the primitive buffer contains 0 elements

        geom_buffer = GeometryBuffer(50)
        self.assertEqual(geom_buffer.geometry_count(), 0)

        for i in range(20):
            tri_1_point_a = [0, 0, 1]
            tri_1_point_b = [1, 0, 1]
            tri_1_point_c = [0, 1, 1]
            tri_1_uv_array = [0.2] * 48
            tri_1_node_id = 101
            tri_1_material_id = 201
            geom_buffer.add_triangle_to_buffer(
                tri_1_point_a,
                tri_1_point_b,
                tri_1_point_c,
                tri_1_uv_array,
                tri_1_node_id,
                tri_1_material_id,
            )

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)
        build_primitives(geom_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

    def test_create_simple(self):
        # create a geometry buffer

        # create a Primitive buffer

        # add some geomtry to the buffer, like 2 triangles and one point

        # do the "build primitive" function

        # check that the primitive buffer contains 3 elements (2 triangles and one point)

        geom_buffer = GeometryBuffer(10)
        self.assertEqual(geom_buffer.geometry_count(), 0)
        point1_x, point1_y, point1_z = 1.0, 2.0, 3.0
        point1_uv_array = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]*4
        point1_node_id = 100
        point1_material_id = 200
        geom_buffer.add_point_to_buffer(
            point1_x,
            point1_y,
            point1_z,
            point1_uv_array,
            point1_node_id,
            point1_material_id,
        )

        self.assertEqual(geom_buffer.geometry_count(), 1)

        tri_1_point_a = [0, 0, 1]
        tri_1_point_b = [1, 0, 1]
        tri_1_point_c = [0, 1, 1]
        tri_1_uv_array = [0.2] * 48
        tri_1_node_id = 101
        tri_1_material_id = 201
        geom_buffer.add_triangle_to_buffer(
            tri_1_point_a,
            tri_1_point_b,
            tri_1_point_c,
            tri_1_uv_array,
            tri_1_node_id,
            tri_1_material_id,
        )

        tri_2_point_a = [1, 2, 1]
        tri_2_point_b = [3, 4, 1]
        tri_2_point_c = [5, 6, 1]
        tri_2_uv_array = [0.1] * 48
        tri_2_node_id = 102
        tri_2_material_id = 202
        geom_buffer.add_triangle_to_buffer(
            tri_2_point_a,
            tri_2_point_b,
            tri_2_point_c,
            tri_2_uv_array,
            tri_2_node_id,
            tri_2_material_id,
        )

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)
        build_primitives(geom_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 3)

        prim0 = primitive_buffer.get_primitive(0)
        prim1 = primitive_buffer.get_primitive(1)
        prim2 = primitive_buffer.get_primitive(2)

        print(prim0)
        self.assertEqual(prim0["node_id"], point1_node_id)
        self.assertEqual(prim0["material_id"], point1_material_id)
        self.assertEqual(prim0["unique_id"], 0)
        self.assertEqual(prim0["geometry_id"], 0)

        self.assertEqual(prim1["node_id"], tri_1_node_id)
        self.assertEqual(prim1["material_id"], tri_1_material_id)
        self.assertEqual(prim1["unique_id"], 1)
        self.assertEqual(prim1["geometry_id"], 1)

        self.assertEqual(prim2["node_id"], tri_2_node_id)
        self.assertEqual(prim2["material_id"], tri_2_material_id)
        self.assertEqual(prim2["unique_id"], 2)
        self.assertEqual(prim2["geometry_id"], 2)



    def test_create_polygon(self):
        geom_buffer = GeometryBuffer(10)
        self.assertEqual(geom_buffer.geometry_count(), 0)
        self.assertEqual(geom_buffer.element_count(), 0)

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)
        



        poly_point_a = [1, 2, 1]
        poly_point_b = [3, 4, 1]
        poly_point_c = [5, 6, 1]
        poly_point_d = [7, 8, 1]
        face_uv_array = [0.1] * 48

        face_uvs = [face_uv_array,face_uv_array]


        tri_2_node_id = 102
        tri_2_material_id = 202
        geom_buffer.add_polygon_to_buffer(
            [ poly_point_a,poly_point_b,poly_point_c,poly_point_d],
            face_uvs,
            tri_2_node_id,
            tri_2_material_id,
        )


        self.assertEqual(geom_buffer.geometry_count(), 2)
        self.assertEqual(geom_buffer.element_count(), 1)

        build_primitives(geom_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 2)

        prim0 = primitive_buffer.get_primitive(0)
        prim1 = primitive_buffer.get_primitive(1)
        self.assertEqual(prim0["primitive_type_id"],2) # triangle
        self.assertEqual(prim0["geometry_id"],0) 
        self.assertEqual(prim0["material_id"],202) 
        self.assertEqual(prim0["node_id"],102) 


        self.assertEqual(prim1["primitive_type_id"],2) # triangle
        self.assertEqual(prim1["geometry_id"],0) 
        self.assertEqual(prim1["material_id"],202) 
        self.assertEqual(prim1["node_id"],102) 