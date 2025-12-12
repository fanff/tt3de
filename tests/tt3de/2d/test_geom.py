# -*- coding: utf-8 -*-

import unittest


from tt3de.tt3de import GeometryBufferPy

from tests.tt3de.test_utils import assertPolygon3DEqual


class Test_2DGeometryBuffer(unittest.TestCase):
    def setUp(self):
        # create a default GeometryBufferPy before each test
        self.geom_buffer = GeometryBufferPy(32)

    def test_empty(self):
        geom_buffer = self.geom_buffer
        self.assertEqual(geom_buffer.geometry_count(), 0)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_points_2d(self):
        """Test adding a 2D point and verify its addition to the buffer."""
        geom_buffer = self.geom_buffer

        geom_buffer.clear()

        node_id = 101
        material_id = 201
        uv_idx = 2
        geom_buffer.add_points_2d(
            0,
            5,
            uv_idx,
            node_id,
            material_id,
        )

        self.assertEqual(geom_buffer.geometry_count(), 1)

        added_geometry_dict = geom_buffer.get_element(0)

        self.assertEqual(added_geometry_dict["_type"], "Points2D")
        self.assertEqual(added_geometry_dict["point_start"], 0)
        self.assertEqual(added_geometry_dict["point_count"], 5)
        self.assertEqual(added_geometry_dict["uv_idx"], uv_idx)

        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_polygon2d(self):
        """Test adding a 2D polygon and verify its addition to the buffer."""
        geom_buffer = self.geom_buffer

        geom_buffer.clear()

        node_id = 102
        material_id = 202
        uv_idx = 3
        geom_buffer.add_polygon2d(
            0,
            2,
            node_id,
            material_id,
            uv_idx,
        )

        self.assertEqual(geom_buffer.geometry_count(), 1)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)
