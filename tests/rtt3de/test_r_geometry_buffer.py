


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
        uv_idx = 0
        node_id = 100
        material_id = 200
        geom_buffer.add_point(pidx,uv_idx, node_id, material_id)

        # Access the raw content if possible to verify or check content_idx increase
        self.assertEqual(geom_buffer.geometry_count(), 1)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_add_line(self):
        """Test adding a line and check for correct buffer update."""
        geom_buffer = GeometryBufferPy(10)
        geom_buffer.clear()
        
        
        start_vertext_idx = 0
        uv_start=0
        node_id = 101
        material_id = 201
        geom_buffer.add_line3d(start_vertext_idx, node_id, material_id, uv_start )

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
            0,1,  node_id, material_id, 0
        )

        self.assertEqual(geom_buffer.geometry_count(), 1)

        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)


    def test_add_polygon(self):
        """Test adding a triangle and verify its addition to the buffer."""
        geom_buffer = GeometryBufferPy(10)
        geom_buffer.clear()


        node_id = 102
        material_id = 202

        geom_buffer.add_polygon(
            2,23, node_id, material_id, 32
        )

        self.assertEqual(geom_buffer.geometry_count(), 1)
        elem0 = geom_buffer.get_element(0)
        self.assertEqual(elem0,{'p_start': 2, 'triangle_count': 23, 'uv_start': 32} )

#
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)

    def test_buffer_overflow(self):
        """Test it does not crash and ignore stuff"""
        geom_buffer = GeometryBufferPy(
            10
        )  # Start with a small buffer size to test resizing
        for i in range(100):  # Add more items than the initial size
            geom_buffer.add_point(0, 0, 100, 200)

        self.assertEqual(geom_buffer.geometry_count(), 10)
        geom_buffer.clear()
        self.assertEqual(geom_buffer.geometry_count(), 0)


