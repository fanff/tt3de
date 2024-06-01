

import unittest
import pytest

from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.primitives.primitives import PrimitivesBuffer    
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

class Test_RasterPrecalc(unittest.TestCase):
    def test_raster_precalc_empty(self):
        drawing_buffer = DrawingBuffer(32,32)
        primitive_buffer = PrimitivesBuffer(10)



        raster_precalc( primitive_buffer,  drawing_buffer)



    def test_raster_precalc_triangle(self):
        drawing_buffer = DrawingBuffer(32,32)
        drawing_buffer.hard_clear(1000)


        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)
        primitive_buffer.add_triangle(0,0,0,0,
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
        primitive_buffer.add_triangle(0,0,0,0,
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