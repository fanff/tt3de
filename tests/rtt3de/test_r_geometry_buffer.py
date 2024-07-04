


import unittest



from rtt3de import GeometryBufferPy

class Test_GeometryBuffer(unittest.TestCase):
    def test_empty(self):
        geom_buffer = GeometryBufferPy(32)
        self.assertEqual(geom_buffer.geometry_count(), 0)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_point(self):
        """Test adding a single point and verify buffer contents."""
        geom_buffer = GeometryBufferPy(10)
        self.assertEqual(geom_buffer.geometry_count(), 0)
        pidx = 0
        uv_array = [0.1, 0.2]*16
        node_id = 100
        material_id = 200
        geom_buffer.add_point(pidx, node_id, material_id)

        # Access the raw content if possible to verify or check content_idx increase
        self.assertEqual(geom_buffer.geometry_count(), 1)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_line(self):
        """Test adding a line and check for correct buffer update."""
        geom_buffer = GeometryBufferPy(10)
        geom_buffer.clear()
        start = 0
        end = 1
        uv_array = [0.1] * 16
        node_id = 101
        material_id = 201
        geom_buffer.add_line(start, end, node_id, material_id)

        self.assertEqual(geom_buffer.geometry_count(), 1)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_triangle(self):
        """Test adding a triangle and verify its addition to the buffer."""
        geom_buffer = GeometryBufferPy(10)

        geom_buffer.clear()

        
        
        node_id = 102
        material_id = 202
        geom_buffer.add_polygon(
            0,5,  node_id, material_id, 0,3
        )

        self.assertEqual(geom_buffer.geometry_count(), 1)

        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)


    def test_add_polygon(self):
        """Test adding a triangle and verify its addition to the buffer."""
        geom_buffer = GeometryBufferPy(10)
        geom_buffer.clear()
        point_a = [0, 0, 0]
        point_b = [1, 0, 0]
        point_c = [0, 1, 0]
        point_d = [1, 1, 0]

        uv_array_face1 = [0.1] * 48
        uv_array_face2 = [0.1] * 48

        node_id = 102
        material_id = 202

        vertex = [ point_a, point_b, point_c , point_d]
        uv_array = [uv_array_face1, uv_array_face2]

        geom_buffer.add_polygon(
            0,2, node_id, material_id, 0,3
        )

        self.assertEqual(geom_buffer.geometry_count(), 1)
#
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

        
    def test_buffer_overflow(self):
        """Test it does not crash and ignore stuff"""
        geom_buffer = GeometryBufferPy(
            10
        )  # Start with a small buffer size to test resizing
        for i in range(100):  # Add more items than the initial size
            geom_buffer.add_point(0,  100, 200)

        self.assertEqual(geom_buffer.geometry_count(), 10)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)


