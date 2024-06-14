import math
import unittest
import pytest

from tests.c_code.drawing_buffer.test_draw_buffer import drawbuffer_to_pil
from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de.glm.primitives.primitives import PrimitivesBuffer
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

from tt3de.glm.material.c_material import MaterialBuffer


class Test_RasterPrecalcLine(unittest.TestCase):
    def test_raster_precalc_empty(self):
        drawing_buffer = DrawingBuffer(32, 32)
        primitive_buffer = PrimitivesBuffer(10)

        raster_precalc(primitive_buffer, drawing_buffer)

    def test_raster_precalc_line(self):
        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        line_node_id = 1
        line_geometry_id = 2
        line_material_id = 3
        line_ax = 2.2
        line_ay = 3.2
        line_az = 1.0
        line_bx = 5.6
        line_by = 8.7
        line_bz = 1.0
        primitive_buffer.add_line(
            line_node_id,
            line_geometry_id,
            line_material_id,
            line_ax,
            line_ay,
            line_az,
            line_bx,
            line_by,
            line_bz,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)

        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)
        self.assertEqual(precalculated["ax"], 2)
        self.assertEqual(precalculated["ay"], 3)

        self.assertEqual(precalculated["bx"], 6)
        self.assertEqual(precalculated["by"], 9)

    def test_raster_precalc_line_outbound(self):
        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        line_node_id = 1
        line_geometry_id = 2
        line_material_id = 3
        line_ax = 2.2
        line_ay = 3.2
        line_az = 1.0
        line_bx = -5.6
        line_by = 8.7
        line_bz = 1.0
        primitive_buffer.add_line(
            line_node_id,
            line_geometry_id,
            line_material_id,
            line_ax,
            line_ay,
            line_az,
            line_bx,
            line_by,
            line_bz,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)

        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)
        self.assertEqual(precalculated["ax"], 2)
        self.assertEqual(precalculated["ay"], 3)

        self.assertEqual(precalculated["bx"], 0)
        self.assertEqual(precalculated["by"], 5)


class Test_RasterPrecalcTriangle(unittest.TestCase):

    def test_raster_precalc_triangle(self):
        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)
        primitive_buffer.add_triangle(
            0,
            0,
            0,
            2.2,
            2.2,
            1.0,
            5.5,
            8.8,
            1.0,
            10.0,
            3.0,
            1.0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)

        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)

        self.assertEqual(precalculated["clipped"], 0)

    def test_raster_precalc_triangle_clamp(self):
        drawing_buffer = DrawingBuffer(5, 5)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)
        primitive_buffer.add_triangle(
            0,
            0,
            0,
            2.2,
            2.2,
            1.0,
            5.5,
            8.8,
            1.0,
            10.0,
            3.0,
            1.0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)

        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)
        self.assertEqual(precalculated["clipped"], 0)


class Test_RasterPrecalc_point(unittest.TestCase):
    def test_raster_precacl_point(self):

        drawing_buffer = DrawingBuffer(5, 5)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        xyzfloat_point = 1.0, 2.0, 1.0
        primitive_buffer.add_point(0, 0, 0, *xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        # apply the pre_calculation on the point
        raster_precalc(primitive_buffer, drawing_buffer)

        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)
        self.assertEqual(precalculated["ax"], 1)
        self.assertEqual(precalculated["ay"], 2)
        self.assertEqual(precalculated["clipped"], 0)

    def test_raster_precacl_pointout_bound(self):

        drawing_buffer = DrawingBuffer(5, 5)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        xyzfloat_point = -1.0, -2.0, 1.0
        primitive_buffer.add_point(0, 0, 0, *xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        # apply the pre_calculation on the point
        raster_precalc(primitive_buffer, drawing_buffer)

        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)

        self.assertEqual(
            precalculated["clipped"], 1
        )  # point has been clipped and won't be visible.


class Test_RasterAll_point(unittest.TestCase):
    def test_raster_all_empty(self):

        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(1000.0)
        primitive_buffer = PrimitivesBuffer(10)

        raster_precalc(primitive_buffer, drawing_buffer)

        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        # tets that teh depth buffer hasn"'t changed
        depth_buffer_list = drawing_buffer.drawbuffer_to_list()

        elem_of_dephtbuffer = depth_buffer_list[0]

        (
            depth,
            wa,
            wb,
            wc,
            node_id_out,
            geom_id_out_out,
            material_id_out,
            primitiv_id,
        ) = elem_of_dephtbuffer
        self.assertEqual(depth, 1000.0)

    def test_raster_one_point(self):

        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)

        xyzfloat_point = 0.0, 0.0, 1.0

        node_id = 2
        geom_id = 3
        material_id = 4

        primitive_buffer.add_point(node_id, geom_id, material_id, *xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)

        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        depth_buffer_list = drawing_buffer.drawbuffer_to_list()

        elem_of_dephtbuffer = depth_buffer_list[0]

        (
            depth,
            wa,
            wb,
            wc,
            node_id_out,
            geom_id_out_out,
            material_id_out,
            primitiv_id,
        ) = elem_of_dephtbuffer
        self.assertEqual(depth, 1.0)  # depth is set correctly; as expected.
        self.assertEqual(wa, 1.0)  # weights is calculated
        self.assertEqual(wb, 0.0)
        self.assertEqual(wc, 0.0)

        self.assertEqual(node_id_out, node_id)
        self.assertEqual(geom_id_out_out, geom_id)
        self.assertEqual(material_id_out, material_id)
        self.assertEqual(primitiv_id, 0)

    def test_raster_one_point_Yside(self):

        drawing_buffer = DrawingBuffer(5, 10)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)

        xyzfloat_point = 0.0, 1.0, 1.0  # point with x = 1  , y = 0
        node_id = 2
        geom_id = 3
        material_id = 4

        primitive_buffer.add_point(node_id, geom_id, material_id, *xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)

        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        elem_of_dephtbuffer = drawing_buffer.get_depth_buff_content(0, 0)
        print(elem_of_dephtbuffer)
        self.assertEqual(
            elem_of_dephtbuffer["depth_value"], 1000.0
        )  # depth is set correctly; as expected.
        self.assertEqual(
            elem_of_dephtbuffer["w1"], 0.0
        )  # weights is zero because not the point.
        self.assertEqual(elem_of_dephtbuffer["w2"], 0.0)
        self.assertEqual(elem_of_dephtbuffer["w3"], 0.0)

        self.assertEqual(elem_of_dephtbuffer["node_id"], 0)
        self.assertEqual(elem_of_dephtbuffer["geom_id"], 0)
        self.assertEqual(elem_of_dephtbuffer["material_id"], 0)
        self.assertEqual(elem_of_dephtbuffer["primitiv_id"], 0)

        # the point on the side
        elem_of_dephtbuffer = drawing_buffer.get_depth_buff_content(0, 1)
        self.assertEqual(
            elem_of_dephtbuffer["depth_value"], 1.0
        )  # depth is set correctly; as expected.
        self.assertEqual(
            elem_of_dephtbuffer["w1"], 1.0
        )  # weights is zero because not the point.
        self.assertEqual(elem_of_dephtbuffer["w2"], 0.0)
        self.assertEqual(elem_of_dephtbuffer["w3"], 0.0)

        self.assertEqual(elem_of_dephtbuffer["node_id"], node_id)
        self.assertEqual(elem_of_dephtbuffer["geom_id"], geom_id)
        self.assertEqual(elem_of_dephtbuffer["material_id"], material_id)
        self.assertEqual(elem_of_dephtbuffer["primitiv_id"], 0)

    def test_raster_one_point_Xside(self):

        drawing_buffer = DrawingBuffer(5, 10)
        drawing_buffer.hard_clear(1000)

        primitive_buffer = PrimitivesBuffer(10)

        xyzfloat_point = 1.0, 0.0, 1.0  # point with x = 1  , y = 0
        node_id = 2
        geom_id = 3
        material_id = 4

        primitive_buffer.add_point(node_id, geom_id, material_id, *xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)

        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        depth_buffer_list = drawing_buffer.drawbuffer_to_list()

        elem_of_dephtbuffer = drawing_buffer.get_depth_buff_content(0, 0)
        print(elem_of_dephtbuffer)
        self.assertEqual(
            elem_of_dephtbuffer["depth_value"], 1000.0
        )  # depth is set correctly; as expected.
        self.assertEqual(
            elem_of_dephtbuffer["w1"], 0.0
        )  # weights is zero because not the point.
        self.assertEqual(elem_of_dephtbuffer["w2"], 0.0)
        self.assertEqual(elem_of_dephtbuffer["w3"], 0.0)

        self.assertEqual(elem_of_dephtbuffer["node_id"], 0)
        self.assertEqual(elem_of_dephtbuffer["geom_id"], 0)
        self.assertEqual(elem_of_dephtbuffer["material_id"], 0)
        self.assertEqual(elem_of_dephtbuffer["primitiv_id"], 0)

        # the point on the side
        elem_of_dephtbuffer = drawing_buffer.get_depth_buff_content(1, 0)
        self.assertEqual(
            elem_of_dephtbuffer["depth_value"], 1.0
        )  # depth is set correctly; as expected.
        self.assertEqual(
            elem_of_dephtbuffer["w1"], 1.0
        )  # weights is zero because not the point.
        self.assertEqual(elem_of_dephtbuffer["w2"], 0.0)
        self.assertEqual(elem_of_dephtbuffer["w3"], 0.0)

        self.assertEqual(elem_of_dephtbuffer["node_id"], node_id)
        self.assertEqual(elem_of_dephtbuffer["geom_id"], geom_id)
        self.assertEqual(elem_of_dephtbuffer["material_id"], material_id)
        self.assertEqual(elem_of_dephtbuffer["primitiv_id"], 0)


class Test_RasterAll_line(unittest.TestCase):

    def test_raster_one_line(self):
        "along the x axis"

        mb_ = MaterialBuffer()
        drawing_buffer = DrawingBuffer(64, 32)
        drawing_buffer.hard_clear(3)

        primitive_buffer = PrimitivesBuffer(10)

        line_node_id = 1
        line_geometry_id = 2
        line_material_id = 3
        line_ax = 3.2
        line_ay = 3.2
        line_az = 1.0
        line_bx = 60.3
        line_by = 3.2
        line_bz = 2.0
        primitive_buffer.add_line(
            line_node_id,
            line_geometry_id,
            line_material_id,
            line_ax,
            line_ay,
            line_az,
            line_bx,
            line_by,
            line_bz,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)
        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, mb_)

        # should be a horizontal line, top left of the screen
        drawbuffer_to_pil(
            drawing_buffer, img_name="test_raster_one_line.png", layer="depth"
        )

        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buff_content(3, 3)

        self.assertAlmostEqual(
            elem_of_dephtbuffer1["depth_value"], 1.05, 0
        )  # depth is set correctly; as expected.
        self.assertAlmostEqual(
            elem_of_dephtbuffer1["w1"], 0.05, 0
        )  # weights is calculated to zero; because it is the start point , almost zero because line drawing
        self.assertEqual(elem_of_dephtbuffer1["w2"], 0.0)
        self.assertEqual(elem_of_dephtbuffer1["w3"], 0.0)

        self.assertEqual(elem_of_dephtbuffer1["node_id"], line_node_id)
        self.assertEqual(elem_of_dephtbuffer1["geom_id"], line_geometry_id)
        self.assertEqual(elem_of_dephtbuffer1["material_id"], line_material_id)
        self.assertEqual(
            elem_of_dephtbuffer1["primitiv_id"], 0
        )  # because this is the first primitive we added.

        elem_of_dephtbuffer2 = drawing_buffer.get_depth_buff_content(58, 3)

        self.assertAlmostEqual(
            elem_of_dephtbuffer2["w1"], 1.00, 1
        )  # weights is calculated to 1; because it is the end point
        self.assertAlmostEqual(
            elem_of_dephtbuffer2["depth_value"], 2.0, 1
        )  # depth is set correctly; as expected.
        self.assertEqual(elem_of_dephtbuffer2["w2"], 0.0)
        self.assertEqual(elem_of_dephtbuffer2["w3"], 0.0)
        self.assertEqual(elem_of_dephtbuffer2["node_id"], line_node_id)
        self.assertEqual(elem_of_dephtbuffer2["geom_id"], line_geometry_id)
        self.assertEqual(elem_of_dephtbuffer2["material_id"], line_material_id)
        self.assertEqual(
            elem_of_dephtbuffer2["primitiv_id"], 0
        )  # because this is the first primitive we added.

        mind, maxd = drawing_buffer.get_depth_min_max()
        self.assertGreaterEqual(mind, 1.0)

        self.assertLessEqual(maxd, 3.0)

    def test_raster_many_line(self):
        "along the x axis"
        drawing_buffer = DrawingBuffer(64, 32)
        drawing_buffer.hard_clear(3)

        primitive_buffer = PrimitivesBuffer(101)

        for i in range(10):

            line_node_id = 1
            line_geometry_id = 2
            line_material_id = 3
            line_ax = 2
            line_ay = (2 * i) + 1
            line_az = 1.0
            line_bx = 60.3
            line_by = (2 * i) + 1
            line_bz = 2 * i
            primitive_buffer.add_line(
                line_node_id,
                line_geometry_id,
                line_material_id,
                line_ax,
                line_ay,
                line_az,
                line_bx,
                line_by,
                line_bz,
            )
        self.assertEqual(primitive_buffer.primitive_count(), 10)
        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        # should be a horizontal line, top left of the screen
        drawbuffer_to_pil(
            drawing_buffer, img_name="test_raster_many_line.png", layer="depth"
        )

    def test_rasterall_line_outbound(self):
        #
        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(3)

        primitive_buffer = PrimitivesBuffer(10)

        line_node_id = 1
        line_geometry_id = 2
        line_material_id = 3
        line_ax = -5.2
        line_ay = -5.2
        line_az = 1.0
        line_bx = 45.1
        line_by = 45.1
        line_bz = 2.0
        primitive_buffer.add_line(
            line_node_id,
            line_geometry_id,
            line_material_id,
            line_ax,
            line_ay,
            line_az,
            line_bx,
            line_by,
            line_bz,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        # should be a horizontal line, top left of the screen
        drawbuffer_to_pil(
            drawing_buffer, img_name="test_raster_outbound_diag_line.png", layer="depth"
        )

        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buff_content(0, 0)

        self.assertAlmostEqual(
            elem_of_dephtbuffer1["depth_value"], 1.05, 0
        )  # depth is set correctly; as expected.
        self.assertAlmostEqual(
            elem_of_dephtbuffer1["w1"], 0.05, 0
        )  # weights is calculated to zero; because it is the start point , almost zero because line drawing
        self.assertEqual(elem_of_dephtbuffer1["w2"], 0.0)
        self.assertEqual(elem_of_dephtbuffer1["w3"], 0.0)

        self.assertEqual(elem_of_dephtbuffer1["node_id"], line_node_id)
        self.assertEqual(elem_of_dephtbuffer1["geom_id"], line_geometry_id)
        self.assertEqual(elem_of_dephtbuffer1["material_id"], line_material_id)
        self.assertEqual(
            elem_of_dephtbuffer1["primitiv_id"], 0
        )  # because this is the first primitive we added.

    def test_raster_line_instar(self):
        #
        drawing_buffer = DrawingBuffer(64, 64)
        drawing_buffer.hard_clear(2.2)

        primitive_buffer = PrimitivesBuffer(1000)

        branch_count = 16
        for i in range(branch_count):
            endx = 24 * math.cos((i / (branch_count)) * math.pi * 2)
            endy = 24 * math.sin((i / (branch_count)) * math.pi * 2)

            line_node_id = 1
            line_geometry_id = i
            line_material_id = 3
            line_ax = 32
            line_ay = 32
            line_az = 1.0
            line_bx = line_ax + endx
            line_by = line_ay + endy
            line_bz = 2.0
            primitive_buffer.add_line(
                line_node_id,
                line_geometry_id,
                line_material_id,
                line_ax,
                line_ay,
                line_az,
                line_bx,
                line_by,
                line_bz,
            )

        self.assertEqual(primitive_buffer.primitive_count(), branch_count)

        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        # should be a horizontal line, top left of the screen
        drawbuffer_to_pil(
            drawing_buffer, img_name="test_raster_line_instar.png", layer="depth"
        )

    def test_raster_line_instar_outbound(self):
        #
        drawing_buffer = DrawingBuffer(64, 64)
        drawing_buffer.hard_clear(2.2)

        primitive_buffer = PrimitivesBuffer(1000)

        branch_count = 16
        for i in range(branch_count):
            endx = 34 * math.cos((i / (branch_count)) * math.pi * 2)
            endy = 34 * math.sin((i / (branch_count)) * math.pi * 2)

            line_node_id = 1
            line_geometry_id = i
            line_material_id = 3
            line_ax = 32
            line_ay = 32
            line_az = 1.0
            line_bx = line_ax + endx
            line_by = line_ay + endy
            line_bz = 2.0
            primitive_buffer.add_line(
                line_node_id,
                line_geometry_id,
                line_material_id,
                line_ax,
                line_ay,
                line_az,
                line_bx,
                line_by,
                line_bz,
            )

        self.assertEqual(primitive_buffer.primitive_count(), branch_count)

        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        # should be a horizontal line, top left of the screen
        drawbuffer_to_pil(
            drawing_buffer,
            img_name="test_raster_line_instar_outbound.png",
            layer="depth",
        )


class Test_RasterAll_Triangle(unittest.TestCase):

    def test_raster_one_triangle(self):

        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(2)

        primitive_buffer = PrimitivesBuffer(10)

        primitive_buffer.add_triangle(
            0,
            0,
            0,  # nodeid and stuff
            2.5,
            2.2,
            1.0,
            24.0,
            7.0,
            2.0,
            5.5,
            28.8,
            1.0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        drawbuffer_to_pil(
            drawing_buffer, img_name="test_raster_one_triangle.png", layer="depth"
        )

        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buff_content(4, 4)
        elem_of_dephtbuffer2 = drawing_buffer.get_depth_buff_content(5, 5)
        elem_of_dephtbuffer3 = drawing_buffer.get_depth_buff_content(6, 6)

    def test_raster_one_triangle_outbound(self):

        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(2)

        primitive_buffer = PrimitivesBuffer(10)

        primitive_buffer.add_triangle(
            0,
            0,
            0,  # nodeid and stuff
            -12.2,
            -12.2,
            1.0,
            24.0,
            4.0,
            2.0,
            5.5,
            24.8,
            1.0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, MaterialBuffer())

        drawbuffer_to_pil(
            drawing_buffer,
            img_name="test_raster_one_triangle_outbound.png",
            layer="depth",
        )

        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buff_content(4, 4)
        elem_of_dephtbuffer2 = drawing_buffer.get_depth_buff_content(5, 5)
        elem_of_dephtbuffer3 = drawing_buffer.get_depth_buff_content(6, 6)
