


import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture


from tt3de.glm.primitives.primitives import make_point_primitive    
from tt3de.glm.primitives.primitives import PrimitivesBuffer  

class Test_Primitive(unittest.TestCase):
    def test_createPoint(self):
        apoint = make_point_primitive(0,0,0,0 , # ids
                                
                                0,0, #xiyi
                                0.0) # depth
        
        apoint




class Test_PrimitivesBuffer(unittest.TestCase):
    def test_addTriangle(self):
        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)

        primitive_buffer.add_triangle(1,2,3,4,
                                      2.2,2.2,1.0,
                                      5.5,8.8,1.0,
                                      10.0,3.0,1.0,
                                      )
        
        self.assertEqual(primitive_buffer.primitive_count(),1)

        not_precalculated = primitive_buffer.get_primitive(0)


        self.assertEqual(not_precalculated["node_id"],1)
        self.assertEqual(not_precalculated["geometry_id"],2)
        self.assertEqual(not_precalculated["material_id"],3)
        self.assertEqual(not_precalculated["unique_id"],4)

        import itertools

        xxxyyyzzz = list(itertools.chain(*(not_precalculated["mat"])))
        def compare(a,b):
            self.assertEqual(len(a),len(b))
            for i,z in zip(a,b):
                self.assertAlmostEqual(i,z,3)
        compare(xxxyyyzzz[:3],[2.2,5.5,10.0])
        compare(xxxyyyzzz[-3:],[1.0,1.0,1.0])



    def test_createPoint(self):
        apoint = make_point_primitive(0,0,0,0 , # ids
                                
                                0,0, #xiyi
                                0.0) # depth
        
        apoint

        pb = PrimitivesBuffer(3)

        self.assertEqual(pb.primitive_count(),0)

        xyzfloat_point = 1.0,1.0,1.0
        pb.add_point(0,0,0,0,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),1)


        pb.add_point(0,0,0,0,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),2)


        pb.add_point(0,0,0,0,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),3)


        pb.add_point(0,0,0,0,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),3)
        pb.add_point(0,0,0,0,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),3)


