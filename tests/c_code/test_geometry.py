import unittest
import pytest

from tt3de.glm.geometry.geometry import GeometryBuffer


class Test_GeometryBuffer(unittest.TestCase):
    def test_empty(self):
        geom_buffer = GeometryBuffer(32)
        self.assertEqual(geom_buffer.geometry_count(), 0)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_point(self):
        """Test adding a single point and verify buffer contents."""
        geom_buffer = GeometryBuffer(10)
        self.assertEqual(geom_buffer.geometry_count(), 0)
        x, y, z = 1.0, 2.0, 3.0
        uv_array = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        node_id = 100
        material_id = 200
        geom_buffer.add_point_to_buffer(x, y, z, uv_array, node_id, material_id)

        # Access the raw content if possible to verify or check content_idx increase
        self.assertEqual(geom_buffer.geometry_count(), 1)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_line(self):
        """Test adding a line and check for correct buffer update."""
        geom_buffer = GeometryBuffer(10)
        start = [0, 0, 0]
        end = [1, 1, 1]
        uv_array = [0.1] * 16
        node_id = 101
        material_id = 201
        geom_buffer.add_line_to_buffer(start, end, uv_array, node_id, material_id)

        self.assertEqual(geom_buffer.geometry_count(), 1)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_triangle(self):
        """Test adding a triangle and verify its addition to the buffer."""
        geom_buffer = GeometryBuffer(10)
        point_a = [0, 0, 0]
        point_b = [1, 0, 0]
        point_c = [0, 1, 0]
        uv_array = [0.1] * 48
        node_id = 102
        material_id = 202
        geom_buffer.add_triangle_to_buffer(
            point_a, point_b, point_c, uv_array, node_id, material_id
        )

        self.assertEqual(geom_buffer.geometry_count(), 1)

        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_buffer_overflow(self):
        """Test it does not crash and ignore stuff"""
        geom_buffer = GeometryBuffer(
            10
        )  # Start with a small buffer size to test resizing
        for i in range(100):  # Add more items than the initial size
            geom_buffer.add_point_to_buffer(0, 0, 0, [0.1] * 8, 100, 200)

        self.assertEqual(geom_buffer.geometry_count(), 10)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_invalid_input(self):
        """Test the buffer's response to invalid input."""
        geom_buffer = GeometryBuffer(10)
        with self.assertRaises(ValueError):
            geom_buffer.add_point_to_buffer(
                0, 0, 0, [0.1] * 7, 100, 200
            )  # UV array too short
