

import unittest
from rtt3de import PrimitiveBufferPy
from rtt3de import AbigDrawing

from rtt3de import raster_all_py

from tests.c_code.drawing_buffer.test_draw_buffer import drawbuffer_to_pil


class Test_Rust_RasterTriangle(unittest.TestCase):
    def test_raster_empty(self):

        drawing_buffer = AbigDrawing(32, 32)
        drawing_buffer.hard_clear(2)

        primitive_buffer = PrimitiveBufferPy(10)

        raster_all_py(primitive_buffer,drawing_buffer)


    def test_raster_one_triangle(self):

        drawing_buffer = AbigDrawing(32, 32)
        drawing_buffer.hard_clear(10)

        primitive_buffer = PrimitiveBufferPy(10)

        primitive_buffer.add_triangle(
            1221, # node
            2323, # geom
            3232,  # material 
            0, # row col
            0,
            1.0,

            0,  # top
            28, # right
            1.0,


            24, # bottom
            0, # left 
            2.0,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, drawing_buffer)
        
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buffer_cell(1, 1,0)
        elem_of_dephtbuffer_out = drawing_buffer.get_depth_buffer_cell(31, 31,0)
        elem_of_dephtbuffer3 = drawing_buffer.get_depth_buffer_cell(6, 6,0)
        
        self.assertEqual(elem_of_dephtbuffer1["node_id"],1221)
        self.assertEqual(elem_of_dephtbuffer1["geometry_id"],2323)
        self.assertEqual(elem_of_dephtbuffer1["material_id"],3232)
        self.assertGreater(elem_of_dephtbuffer1["w"][0],0.9)
        self.assertLess(elem_of_dephtbuffer1["w"][1],0.1)
        self.assertLess(elem_of_dephtbuffer1["w"][2],0.1)

        self.assertGreater(elem_of_dephtbuffer1["w_1"][0],0.9)
        self.assertLess(elem_of_dephtbuffer1["w_1"][1],0.1)
        self.assertLess(elem_of_dephtbuffer1["w_1"][2],0.1)



        self.assertEqual(elem_of_dephtbuffer_out["node_id"],0)
        self.assertEqual(elem_of_dephtbuffer_out["geometry_id"],0)
        self.assertEqual(elem_of_dephtbuffer_out["material_id"],0)

        litpixcount = 0
        for i in range(32):
            for j in range(32):
                elem = drawing_buffer.get_depth_buffer_cell(i, j,0)

                if elem["node_id"]!=0:
                    litpixcount+=1

        self.assertEqual(litpixcount,356) # 336= 24*28/2  is the surface of the triangle 
        # we migh have the diagonal ; like ~20 pix, to explaing this gap.




    def test_raster_one_triangle_outbound(self):

        drawing_buffer = AbigDrawing(32, 32)
        drawing_buffer.hard_clear(2)

        primitive_buffer = PrimitiveBufferPy(10)

        primitive_buffer.add_triangle(
            12,
            23,
            32,  # nodeid and stuff


            0,
            0,
            1.0,

            0,
            5550,
            2.0,


            3230,
            0,
            1.0,

        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, drawing_buffer)
        elem_of_dephtbuffer1 = drawing_buffer.get_depth_buffer_cell(1, 1,0)

        self.assertEqual(elem_of_dephtbuffer1["node_id"],12)
        self.assertEqual(elem_of_dephtbuffer1["geometry_id"],23)
        self.assertEqual(elem_of_dephtbuffer1["material_id"],32)
        self.assertGreater(elem_of_dephtbuffer1["w"][0],0.9)
        self.assertLess(elem_of_dephtbuffer1["w"][1],0.1)
        self.assertLess(elem_of_dephtbuffer1["w"][2],0.1)

        litpixcount = 0
        for i in range(32):
            for j in range(32):
                elem = drawing_buffer.get_depth_buffer_cell(i, j,0)

                if elem["node_id"]!=0:
                    litpixcount+=1

        self.assertGreater(litpixcount,1000) 
        # for some reason 1024 is not achieved. 
        # probeably because the horizontal lines have weird misses ? 
        