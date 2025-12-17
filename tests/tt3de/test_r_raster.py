# -*- coding: utf-8 -*-
import math
import unittest
from tt3de.tt3de import PrimitiveBufferPy
from tt3de.tt3de import DrawingBufferPy

from tt3de.tt3de import raster_all_py, VertexBufferPy


class Test_Rust_RasterPoint(unittest.TestCase):
    def test_raster_Oneoint(self):
        drawing_buffer = DrawingBufferPy(32, 32)
        drawing_buffer.hard_clear(10)
        vertex_buffer = VertexBufferPy(32, 32, 32)
        primitive_buffer = PrimitiveBufferPy(10)

        node_id = 1
        geom_id = 2
        material_id = 3
        primitive_buffer.add_point(
            node_id, geom_id, material_id, row=1, col=2, depth=3.0, uv=1
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        point_cell = drawing_buffer.get_depth_buffer_cell(1, 2, 0)

        not_point_cell = drawing_buffer.get_depth_buffer_cell(5, 5, 0)
        self.assertEqual(point_cell["node_id"], node_id)
        self.assertEqual(point_cell["geometry_id"], geom_id)
        self.assertEqual(point_cell["material_id"], material_id)
        self.assertAlmostEqual(point_cell["uv"][0], 1.0)
        self.assertAlmostEqual(point_cell["uv"][0], 1.0)

        self.assertEqual(not_point_cell["node_id"], 0)
        self.assertEqual(not_point_cell["geometry_id"], 0)
        self.assertEqual(not_point_cell["material_id"], 0)
        self.assertAlmostEqual(not_point_cell["uv"][0], 0.0)
        self.assertAlmostEqual(not_point_cell["uv"][0], 0.0)


class Test_Rust_RasterLine(unittest.TestCase):
    def test_raster_OneLine(self):
        drawing_buffer = DrawingBufferPy(32, 32)
        drawing_buffer.hard_clear(10)
        vertex_buffer = VertexBufferPy(32, 32, 32)
        primitive_buffer = PrimitiveBufferPy(10)

        node_id = 1
        geom_id = 2
        material_id = 3

        pa_row = 1
        pa_col = 2
        p_a_depth = 3.0

        pb_row = 5
        pb_col = 8
        p_b_depth = 1.0

        primitive_buffer.add_line(
            node_id,
            geom_id,
            material_id,
            pa_row,
            pa_col,
            p_a_depth,
            pb_row,
            pb_col,
            p_b_depth,
            uv=0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)
        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)

    def test_raster_ManyLines(self):
        for pa_row in range(0, 10):
            for pa_col in range(0, 10):
                for pb_row in range(0, 10):
                    for pb_col in range(0, 10):
                        self._test_raster_line(pa_row, pa_col, pb_row, pb_col)

    def _test_raster_line(self, pa_row, pa_col, pb_row, pb_col):
        drawing_buffer = DrawingBufferPy(10, 10)
        drawing_buffer.hard_clear(10)
        vertex_buffer = VertexBufferPy(32, 32, 32)
        primitive_buffer = PrimitiveBufferPy(10)

        node_id = 1
        geom_id = 2
        material_id = 3

        p_a_depth = 3.0

        p_b_depth = 1.0

        primitive_buffer.add_line(
            node_id,
            geom_id,
            material_id,
            pa_row,
            pa_col,
            p_a_depth,
            pb_row,
            pb_col,
            p_b_depth,
            uv=0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)
        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)

        # get the cell of point a
        point_a_cell = drawing_buffer.get_depth_buffer_cell(pa_row, pa_col, 0)
        self.assertEqual(point_a_cell["node_id"], node_id)
        self.assertEqual(point_a_cell["geometry_id"], geom_id)
        self.assertEqual(point_a_cell["material_id"], material_id)
        # check the uv values
        self.assertAlmostEqual(point_a_cell["uv"][0], 1.0, delta=0.001)
        self.assertAlmostEqual(point_a_cell["uv"][1], 0.0, delta=0.001)

        if not (pa_row == pb_row and pa_col == pb_col):
            # get the cell of point b
            point_b_cell = drawing_buffer.get_depth_buffer_cell(pb_row, pb_col, 0)
            self.assertEqual(point_b_cell["node_id"], node_id)
            self.assertEqual(point_b_cell["geometry_id"], geom_id)
            self.assertEqual(point_b_cell["material_id"], material_id)
            # check the uv values
            self.assertAlmostEqual(point_b_cell["uv"][0], 0.0, delta=0.001)
            self.assertAlmostEqual(point_b_cell["uv"][1], 1.0, delta=0.001)

            ##self.assertGreaterEqual(point_b_cell["w"][0],0.0)

        # iterate over the whole canvas and count pixel that are blit by the line
        litpixcount = 0
        for i in range(10):
            for j in range(10):
                elem = drawing_buffer.get_depth_buffer_cell(i, j, 0)

                if elem["node_id"] != 0:
                    litpixcount += 1

        self.assertGreaterEqual(litpixcount, 1)

        # the line is longter that the longest of the two axis.
        self.assertGreaterEqual(
            litpixcount, max(abs(pa_row - pb_row), abs(pa_col - pb_col))
        )

        # the line is smaller than the length of itself ceilled
        self.assertLessEqual(
            litpixcount, math.sqrt((pa_row - pb_row) ** 2 + (pa_col - pb_col) ** 2) + 1
        )


class Test_Rust_RasterTriangle(unittest.TestCase):
    def test_raster_empty(self):
        drawing_buffer = DrawingBufferPy(32, 32)
        drawing_buffer.hard_clear(2)
        vertex_buffer = VertexBufferPy(32, 32, 32)
        primitive_buffer = PrimitiveBufferPy(10)

        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)

    def test_raster_one_triangle(self):
        drawing_buffer = DrawingBufferPy(32, 32)
        drawing_buffer.hard_clear(10)
        vertex_buffer = VertexBufferPy(128, 128, 128)
        primitive_buffer = PrimitiveBufferPy(10)

        primitive_buffer.add_triangle(
            1221,  # node
            2323,  # geom
            3232,  # material
            0,  # row col
            0,
            1.0,
            0,  # top
            28,  # right
            1.0,
            24,  # bottom
            0,  # left
            2.0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buffer_cell(1, 1, 0)
        elem_of_dephtbuffer3 = drawing_buffer.get_depth_buffer_cell(6, 6, 0)

        self.assertEqual(elem_of_dephtbuffer1["node_id"], 1221)
        self.assertEqual(elem_of_dephtbuffer1["geometry_id"], 2323)
        self.assertEqual(elem_of_dephtbuffer1["material_id"], 3232)
        # self.assertGreater(elem_of_dephtbuffer1["uv"][0],0.0)
        # self.assertLess(elem_of_dephtbuffer1["uv"][1],0.1)
        # self.assertGreater(elem_of_dephtbuffer1["uv_1"][0],0.1)
        # self.assertLess(elem_of_dephtbuffer1["uv_1"][1],0.1)

        elem_of_dephtbuffer_out = drawing_buffer.get_depth_buffer_cell(31, 31, 0)
        self.assertEqual(elem_of_dephtbuffer_out["node_id"], 0)
        self.assertEqual(elem_of_dephtbuffer_out["geometry_id"], 0)
        self.assertEqual(elem_of_dephtbuffer_out["material_id"], 0)

        litpixcount = 0
        for i in range(32):
            for j in range(32):
                elem = drawing_buffer.get_depth_buffer_cell(i, j, 0)

                if elem["node_id"] != 0:
                    litpixcount += 1

        self.assertGreaterEqual(
            litpixcount, 336
        )  # 336= 24*28/2  is the surface of the triangle
        # we migh have the diagonal ; like ~20 pix, to explaing this gap.

    def test_raster_one_triangle_outbound(self):
        drawing_buffer = DrawingBufferPy(32, 32)
        drawing_buffer.hard_clear(2)

        primitive_buffer = PrimitiveBufferPy(10)
        vertex_buffer = VertexBufferPy(128, 128, 128)
        primitive_buffer.add_triangle(
            12,
            23,
            32,  # nodeid and stuff
            -5,
            -5,
            1.0,
            -5,
            5550,
            1.0,
            3230,
            -5,
            1.0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)
        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buffer_cell(1, 1, 0)

        self.assertEqual(elem_of_dephtbuffer1["node_id"], 12)
        self.assertEqual(elem_of_dephtbuffer1["geometry_id"], 23)
        self.assertEqual(elem_of_dephtbuffer1["material_id"], 32)
        self.assertLess(elem_of_dephtbuffer1["uv"][0], 0.1)
        self.assertLess(elem_of_dephtbuffer1["uv"][1], 0.1)

        litpixcount = 0
        for i in range(32):
            for j in range(32):
                elem = drawing_buffer.get_depth_buffer_cell(i, j, 0)

                if elem["node_id"] != 0:
                    litpixcount += 1

        self.assertGreater(litpixcount, 990)
        # for some reason 1024 is not achieved.
        # probeably because the horizontal lines have weird misses ?

    def test_raster_one_triangle_with_hline(self):
        #    *--------*   <- this border here is flat.
        #     \     /
        #       \*/
        drawing_buffer = DrawingBufferPy(max_row=50, max_col=64)
        drawing_buffer.hard_clear(2)
        vertex_buffer = VertexBufferPy(128, 128, 128)
        primitive_buffer = PrimitiveBufferPy(10)

        primitive_buffer.add_triangle(
            12,
            23,
            32,  # nodeid and stuff
            2,  # row
            2,  # col
            1.0,
            2,  # row
            60,  # col
            1.0,
            40,  # row
            30,  # col
            1.0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)

        elem_of_dephtbuffer0 = drawing_buffer.get_depth_buffer_cell(0, 0, 0)

        def is_in_triangle(cell):
            return cell["node_id"] != 0

        self.assertEqual(elem_of_dephtbuffer0["node_id"], 0)
        self.assertFalse(is_in_triangle(elem_of_dephtbuffer0))

        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buffer_cell(2, 2, 0)

        self.assertEqual(elem_of_dephtbuffer1["node_id"], 12)
        self.assertTrue(is_in_triangle(elem_of_dephtbuffer1))

        # test the line above
        for i in range(0, 64):
            elem = drawing_buffer.get_depth_buffer_cell(1, i, 0)
            self.assertEqual(elem["node_id"], 0)
            self.assertFalse(is_in_triangle(elem))

        # test the row 2 ; that contains the line
        inside = []
        outside = []
        for i in range(2, 60):
            if is_in_triangle(drawing_buffer.get_depth_buffer_cell(2, i, 0)):
                inside.append(i)
            else:
                outside.append(i)

        self.assertEqual(len(outside), 0)

        # test the rest of the line
        for i in range(60, 64):
            elem = drawing_buffer.get_depth_buffer_cell(2, i, 0)
            self.assertEqual(elem["node_id"], 0)
            self.assertFalse(is_in_triangle(elem))

    def test_raster_ManyTriangles(self):
        for pa_row in range(0, 8):
            for pa_col in range(0, 10):
                for pb_row in range(0, 8):
                    for pb_col in range(0, 10):
                        for pc_row in range(0, 8):
                            for pc_col in range(0, 10):
                                self._test_raster_triangle(
                                    pa_row, pa_col, pb_row, pb_col, pc_row, pc_col
                                )

    def _test_raster_triangle(self, pa_row, pa_col, pb_row, pb_col, pc_row, pc_col):
        drawing_buffer = DrawingBufferPy(8, 10)
        drawing_buffer.hard_clear(10)
        vertex_buffer = VertexBufferPy(128, 128, 128)
        primitive_buffer = PrimitiveBufferPy(10)

        node_id = 1
        geom_id = 2
        material_id = 3

        p_a_depth = 3.0
        p_b_depth = 1.0
        p_c_depth = 2.0

        primitive_buffer.add_triangle(
            node_id,
            geom_id,
            material_id,
            pa_row,
            pa_col,
            p_a_depth,
            pb_row,
            pb_col,
            p_b_depth,
            pc_row,
            pc_col,
            p_c_depth,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)
        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)

        # estimate the surface of the triangle
        surf = 0.5 * abs(
            pa_row * (pb_col - pc_col)
            + pb_row * (pc_col - pa_col)
            + pc_row * (pa_col - pb_col)
        )

        # iterate over the whole canvas and count pixel that are blit by the line
        litpixcount = 0
        for row in range(8):
            for col in range(10):
                elem = drawing_buffer.get_depth_buffer_cell(row, col, 0)

                if elem["node_id"] != 0:
                    litpixcount += 1

        if surf > 2.0:
            if surf < litpixcount:
                pass
            else:
                pass
