

import unittest
import pytest

from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all
from tt3de.glm.primitives.primitives import PrimitivesBuffer    
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

class Test_RasterPrecalcLine(unittest.TestCase):
    def test_raster_precalc_empty(self):
        drawing_buffer = DrawingBuffer(32,32)
        primitive_buffer = PrimitivesBuffer(10)



        raster_precalc( primitive_buffer,  drawing_buffer)
    def test_raster_precalc_line(self):
        drawing_buffer = DrawingBuffer(32,32)
        drawing_buffer.hard_clear(1000)


        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)

        line_node_id = 1
        line_geometry_id=2
        line_material_id=3
        line_ax=2.2
        line_ay=3.2
        line_az=1.0
        line_bx=5.6
        line_by=8.7
        line_bz=1.0
        primitive_buffer.add_line(
                            line_node_id,
                            line_geometry_id,
                            line_material_id,
                            line_ax,
                            line_ay,
                            line_az,

                            line_bx,
                            line_by,
                            line_bz)
        



        self.assertEqual(primitive_buffer.primitive_count(),1)

        raster_precalc( primitive_buffer,  drawing_buffer)


        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)
        self.assertEqual(precalculated["ax"] ,2 )
        self.assertEqual(precalculated["ay"] ,3 )
        
        self.assertEqual(precalculated["bx"] ,6 )
        self.assertEqual(precalculated["by"] ,9 )


    def test_raster_precalc_line_outbound(self):
        drawing_buffer = DrawingBuffer(32,32)
        drawing_buffer.hard_clear(1000)


        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)

        line_node_id = 1
        line_geometry_id=2
        line_material_id=3
        line_ax=2.2
        line_ay=3.2
        line_az=1.0
        line_bx=-5.6
        line_by=8.7
        line_bz=1.0
        primitive_buffer.add_line(
                            line_node_id,
                            line_geometry_id,
                            line_material_id,
                            line_ax,
                            line_ay,
                            line_az,

                            line_bx,
                            line_by,
                            line_bz)
        



        self.assertEqual(primitive_buffer.primitive_count(),1)

        raster_precalc( primitive_buffer,  drawing_buffer)


        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)
        self.assertEqual(precalculated["ax"] ,2 )
        self.assertEqual(precalculated["ay"] ,3 )
        
        self.assertEqual(precalculated["bx"] ,0 )
        self.assertEqual(precalculated["by"] ,5 )

class Test_RasterPrecalcTriangle(unittest.TestCase):

    def test_raster_precalc_triangle(self):
        drawing_buffer = DrawingBuffer(32,32)
        drawing_buffer.hard_clear(1000)


        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)
        primitive_buffer.add_triangle(0,0,0,
                                      2.2,2.2,1.0,
                                      5.5,8.8,1.0,
                                      10.0,3.0,1.0,
                                      )
        
        self.assertEqual(primitive_buffer.primitive_count(),1)

        raster_precalc( primitive_buffer,  drawing_buffer)


        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)
        self.assertEqual(precalculated["ax"] ,2 )
        self.assertEqual(precalculated["ay"] ,2 )
        
        self.assertEqual(precalculated["bx"] ,6 )
        self.assertEqual(precalculated["by"] ,9 )

        self.assertEqual(precalculated["cx"] ,10 )
        self.assertEqual(precalculated["cy"] ,3 )

    def test_raster_precalc_triangle_clamp(self):
        drawing_buffer = DrawingBuffer(5,5)
        drawing_buffer.hard_clear(1000)


        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)
        primitive_buffer.add_triangle(0,0,0,
                                      2.2,2.2,1.0,
                                      5.5,8.8,1.0,
                                      10.0,3.0,1.0,
                                      )
        
        self.assertEqual(primitive_buffer.primitive_count(),1)

        raster_precalc( primitive_buffer,  drawing_buffer)


        precalculated = primitive_buffer.get_primitive(0)

        print(precalculated)
        self.assertEqual(precalculated["ax"] ,2 )
        self.assertEqual(precalculated["ay"] ,2 )
        
        self.assertEqual(precalculated["bx"] ,4 )
        self.assertEqual(precalculated["by"] ,4 )

        self.assertEqual(precalculated["cx"] ,4 )
        self.assertEqual(precalculated["cy"] ,3 )



class Test_RasterPrecalc_point(unittest.TestCase):
    def test_raster_precacl_point(self):

        drawing_buffer = DrawingBuffer(5,5)
        drawing_buffer.hard_clear(1000)


        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)


        xyzfloat_point = 1.0,2.0,1.0
        primitive_buffer.add_point(0,0,0,*xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(),1)
        

        # apply the pre_calculation on the point
        raster_precalc( primitive_buffer,  drawing_buffer)

        precalculated = primitive_buffer.get_primitive(0)



        print(precalculated)
        self.assertEqual(precalculated["ax"] ,1 )
        self.assertEqual(precalculated["ay"] ,2 )
        self.assertEqual(precalculated["clipped"] , 0 )


    def test_raster_precacl_pointout_bound(self):

        drawing_buffer = DrawingBuffer(5,5)
        drawing_buffer.hard_clear(1000)


        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)


        xyzfloat_point = -1.0,-2.0,1.0
        primitive_buffer.add_point(0,0,0,*xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(),1)
        

        # apply the pre_calculation on the point
        raster_precalc( primitive_buffer,  drawing_buffer)

        precalculated = primitive_buffer.get_primitive(0)



        print(precalculated)
        
        self.assertEqual(precalculated["clipped"] ,1 ) # point has been clipped and won't be visible.




class Test_RasterAll_point(unittest.TestCase):
    def test_raster_all_empty(self):

        drawing_buffer = DrawingBuffer(32,32)
        drawing_buffer.hard_clear(1000.0)
        primitive_buffer = PrimitivesBuffer(10)

        raster_precalc( primitive_buffer,  drawing_buffer)

        raster_all(primitive_buffer,drawing_buffer)


        #tets that teh depth buffer hasn"'t changed 
        depth_buffer_list = drawing_buffer.drawbuffer_to_list()

        elem_of_dephtbuffer = depth_buffer_list[0]

        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer
        self.assertEqual(depth,1000.0)


    
    def test_raster_one_point(self):

        drawing_buffer = DrawingBuffer(32,32)
        drawing_buffer.hard_clear(1000)
        
        primitive_buffer = PrimitivesBuffer(10)
        
        xyzfloat_point = 0.0,0.0,1.0
        
        
        node_id = 2
        geom_id = 3
        material_id = 4

        primitive_buffer.add_point(node_id,geom_id,material_id,*xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(),1)
        

        raster_precalc( primitive_buffer,  drawing_buffer)

        raster_all(primitive_buffer,drawing_buffer)

        depth_buffer_list = drawing_buffer.drawbuffer_to_list()


        elem_of_dephtbuffer = depth_buffer_list[0]




        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer
        self.assertEqual(depth ,1.0) # depth is set correctly; as expected. 
        self.assertEqual(wa ,1.0)  # weights is calculated
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,node_id)
        self.assertEqual(geom_id_out_out  ,geom_id)
        self.assertEqual(material_id_out  ,material_id)
        self.assertEqual(primitiv_id  ,0)

    def test_raster_one_point_Yside(self):

        drawing_buffer = DrawingBuffer(5,10)
        drawing_buffer.hard_clear(1000)
        
        primitive_buffer = PrimitivesBuffer(10)
        
        xyzfloat_point = 0.0,1.0,1.0  # point with x = 1  , y = 0
        node_id = 2
        geom_id = 3
        material_id = 4

        primitive_buffer.add_point(node_id,geom_id,material_id,*xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(),1)
        

        raster_precalc( primitive_buffer,  drawing_buffer)

        raster_all(primitive_buffer,drawing_buffer)

        depth_buffer_list = drawing_buffer.drawbuffer_to_list()


        elem_of_dephtbuffer = depth_buffer_list[0]
        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer
        self.assertEqual(depth ,1000.0) # depth is set correctly; as expected. 
        self.assertEqual(wa ,0.0)  # weights is zero because not the point.
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,0)
        self.assertEqual(geom_id_out_out  ,0)
        self.assertEqual(material_id_out  ,0)
        self.assertEqual(primitiv_id  ,0)


        # the point on the side 
        elem_of_dephtbuffer = depth_buffer_list[1]
        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer
        self.assertEqual(depth ,1.0) # depth is set correctly; as expected. 
        self.assertEqual(wa ,1.0)  # weights is zero because not the point.
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,node_id)
        self.assertEqual(geom_id_out_out  ,geom_id)
        self.assertEqual(material_id_out  ,material_id)
        self.assertEqual(primitiv_id  ,0)

    def test_raster_one_point_Xside(self):

        drawing_buffer = DrawingBuffer(5,10)
        drawing_buffer.hard_clear(1000)
        
        primitive_buffer = PrimitivesBuffer(10)
        
        xyzfloat_point = 1.0,0.0,1.0  # point with x = 1  , y = 0
        node_id = 2
        geom_id = 3
        material_id = 4

        primitive_buffer.add_point(node_id,geom_id,material_id,*xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(),1)
        

        raster_precalc( primitive_buffer,  drawing_buffer)

        raster_all(primitive_buffer,drawing_buffer)

        depth_buffer_list = drawing_buffer.drawbuffer_to_list()


        elem_of_dephtbuffer = depth_buffer_list[0]
        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer
        self.assertEqual(depth ,1000.0) # depth is set correctly; as expected. 
        self.assertEqual(wa ,0.0)  # weights is zero because not the point.
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,0)
        self.assertEqual(geom_id_out_out  ,0)
        self.assertEqual(material_id_out  ,0)
        self.assertEqual(primitiv_id  ,0)


        # the point on the side 
        elem_of_dephtbuffer = depth_buffer_list[10]   # this is the height
        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer
        self.assertEqual(depth ,1.0) # depth is set correctly; as expected. 
        self.assertEqual(wa ,1.0)  # weights is zero because not the point.
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,node_id)
        self.assertEqual(geom_id_out_out  ,geom_id)
        self.assertEqual(material_id_out  ,material_id)
        self.assertEqual(primitiv_id  ,0)


class Test_RasterAll_line(unittest.TestCase):

    def test_raster_one_line(self):

        drawing_buffer = DrawingBuffer(64,32)
        drawing_buffer.hard_clear(1000)
        
        primitive_buffer = PrimitivesBuffer(10)

        
        line_node_id = 1
        line_geometry_id=2
        line_material_id=3
        line_ax=0.2
        line_ay=0.2
        line_az=1.0
        line_bx=5.1
        line_by=0.1
        line_bz=2.0
        primitive_buffer.add_line(
                            line_node_id,
                            line_geometry_id,
                            line_material_id,
                            line_ax,
                            line_ay,
                            line_az,

                            line_bx,
                            line_by,
                            line_bz)
        



        self.assertEqual(primitive_buffer.primitive_count(),1)



        raster_precalc( primitive_buffer,  drawing_buffer)
        raster_all(primitive_buffer,drawing_buffer)

        depth_buffer_list = drawing_buffer.drawbuffer_to_list()


        elem_of_dephtbuffer1 = depth_buffer_list[0] # this point is the one with the start point of the line.


        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer1
        self.assertAlmostEqual(depth ,1.05,1) # depth is set correctly; as expected. 
        self.assertAlmostEqual(wa ,0.05,1)  # weights is calculated to zero; because it is the start point , almost zero because line drawing
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,line_node_id)
        self.assertEqual(geom_id_out_out  ,line_geometry_id)
        self.assertEqual(material_id_out  ,line_material_id)
        self.assertEqual(primitiv_id  ,0)  # because this is the first primitive we added.



        elem_of_dephtbuffer2 = depth_buffer_list[5*32] # this point is the one with the other end of the line


        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer2
        self.assertAlmostEqual(depth ,1.2,3) # depth is set correctly; as expected. 
        self.assertAlmostEqual(wa , 0.2 , 3)  # weights is calculated along the line
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,line_node_id)
        self.assertEqual(geom_id_out_out  ,line_geometry_id)
        self.assertEqual(material_id_out  ,line_material_id)
        self.assertEqual(primitiv_id  ,0)  # because this is the first primitive we added.



    def test_rasterall_line_outbound(self):

        drawing_buffer = DrawingBuffer(32,32)
        drawing_buffer.hard_clear(1000)
        
        primitive_buffer = PrimitivesBuffer(10)

        
        line_node_id = 1
        line_geometry_id=2
        line_material_id=3
        line_ax=-5.2
        line_ay=-5.2
        line_az=1.0
        line_bx=45.1
        line_by=45.1
        line_bz=2.0
        primitive_buffer.add_line(
                            line_node_id,
                            line_geometry_id,
                            line_material_id,
                            line_ax,
                            line_ay,
                            line_az,

                            line_bx,
                            line_by,
                            line_bz)
        



        self.assertEqual(primitive_buffer.primitive_count(),1)



        raster_precalc( primitive_buffer,  drawing_buffer)
        raster_all(primitive_buffer,drawing_buffer)

        depth_buffer_list = drawing_buffer.drawbuffer_to_list()


        elem_of_dephtbuffer1 = depth_buffer_list[0] # this point is the one the line should go throu


        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer1
        self.assertEqual(depth ,1.0) # depth is set bythe weith 
        self.assertAlmostEqual(wa ,0.1)  # weights clip is considered 
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,line_node_id)
        self.assertEqual(geom_id_out_out  ,line_geometry_id)
        self.assertEqual(material_id_out  ,line_material_id)
        self.assertEqual(primitiv_id  ,0)  # because this is the first primitive we added.



        elem_of_dephtbuffer2 = depth_buffer_list[-1] # this point is the other corners the line should go throu


        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer2
        self.assertAlmostEqual(depth ,1.2,3) # depth is set correctly; as expected. 
        self.assertAlmostEqual(wa , 0.2 , 3)  # weights is calculated along the line
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,line_node_id)
        self.assertEqual(geom_id_out_out  ,line_geometry_id)
        self.assertEqual(material_id_out  ,line_material_id)
        self.assertEqual(primitiv_id  ,0)  # because this is the first primitive we added.



class Test_RasterAll_Triangle(unittest.TestCase):

    def test_raster_one_triangle(self):

        drawing_buffer = DrawingBuffer(32,32)
        drawing_buffer.hard_clear(1000)
        
        primitive_buffer = PrimitivesBuffer(10)
        depth,wa,wb,wc,node_id_out,geom_id_out_out,material_id_out,primitiv_id = elem_of_dephtbuffer
        self.assertEqual(depth ,1.0) # depth is set correctly; as expected. 
        self.assertEqual(wa ,1.0)  # weights is calculated
        self.assertEqual(wb ,0.0)
        self.assertEqual(wc  ,0.0)

        self.assertEqual(node_id_out  ,node_id)
        self.assertEqual(geom_id_out_out  ,geom_id)
        self.assertEqual(material_id_out  ,material_id)
        self.assertEqual(primitiv_id  ,0)