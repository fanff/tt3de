





import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture





from tt3de.glm.raster.c_raster_point import raster_on_stuff

from tt3de.glm.primitives.primitives import make_point_primitive    
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

class Test_RasterPoint(unittest.TestCase):
    def test_rasterpoint0(self):


        node_id = 1
        geometry_id = 2
        material_id = 3
        unique_id = 32
        p = make_point_primitive(node_id,geometry_id,material_id,unique_id,
                                 
                                 0,0,
                                 
                                 
                                 1.0)
        

        d = DrawingBuffer(32,20)
        d.hard_clear(1000.0)

        #do the crazy raster function
        raster_on_stuff(p,d)


        depthbuff_list = d.drawbuffer_to_list()


        in_depthbuff = depthbuff_list[0]
        #node_id,geom_id,material_id,primitiv_id
        self.assertEqual(in_depthbuff,[1.0, # depth is 1.0 from primitiv
                                       1.0,0.0,0.0, # weights of point is always like this I guess
                                       node_id,geometry_id,material_id,unique_id])
        