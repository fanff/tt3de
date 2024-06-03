


import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture


from tt3de.glm.primitives.primitives import make_point_primitive    
from tt3de.glm.primitives.primitives import PrimitivesBuffer  
import itertools



class Test_Primitive(unittest.TestCase):
    def test_createPoint(self):
        apoint = make_point_primitive(0,0,0,0 , # ids
                                
                                0,0, #xiyi
                                0.0) # depth
        
        apoint




class Test_PrimitivesBuffer(unittest.TestCase):

    def assert_comparelist(self,a,b):
            self.assertEqual(len(a),len(b))
            for i,z in zip(a,b):
                self.assertAlmostEqual(i,z,3)
    def test_create_10(self):
        primitive_buffer = PrimitivesBuffer(10)
    def test_create_100(self):
        primitive_buffer = PrimitivesBuffer(100)
    def test_addLine(self):
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
        
        not_precalculated = primitive_buffer.get_primitive(0)


        self.assertEqual(not_precalculated["node_id"],line_node_id)
        self.assertEqual(not_precalculated["geometry_id"],line_geometry_id)
        self.assertEqual(not_precalculated["material_id"],line_material_id)
        self.assertEqual(not_precalculated["unique_id"],0)



    def test_addTriangle(self):
        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)

        primitive_buffer.add_triangle(1,2,3,
                                      2.2,2.2,1.0,
                                      5.5,8.8,1.0,
                                      10.0,3.0,1.0,
                                      )
        
        self.assertEqual(primitive_buffer.primitive_count(),1)

        not_precalculated = primitive_buffer.get_primitive(0)


        self.assertEqual(not_precalculated["node_id"],1)
        self.assertEqual(not_precalculated["geometry_id"],2)
        self.assertEqual(not_precalculated["material_id"],3)
        self.assertEqual(not_precalculated["unique_id"],0)

        

        xxxyyyzzz = list(itertools.chain(*(not_precalculated["mat"])))
        
        self.assert_comparelist(xxxyyyzzz[:3],[2.2,5.5,10.0])


        self.assert_comparelist(xxxyyyzzz[-3:],[1.0,1.0,1.0])
    def test_add_point_overflow(self):
        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(),0)

        for i in range(100):
            xyzfloat_point = 1.0,2.0,3.0
            node_id = 1
            geom_id = 2
            material_id = 3
            primitive_buffer.add_point(node_id,geom_id,material_id,*xyzfloat_point)
        self.assertEqual(primitive_buffer.primitive_count(),10)

    def test_add_point(self):
        apoint = make_point_primitive(0,0,0,0 , # ids
                                
                                0,0, #xiyi
                                0.0) # depth
        
        pb = PrimitivesBuffer(3)

        self.assertEqual(pb.primitive_count(),0)

        xyzfloat_point = 1.0,2.0,3.0
        node_id = 1
        geom_id = 2
        material_id = 3
        pb.add_point(node_id,geom_id,material_id,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),1)


        not_precalculated = pb.get_primitive(0)

        print(not_precalculated)

        self.assertEqual(not_precalculated["node_id"],node_id)
        self.assertEqual(not_precalculated["geometry_id"],geom_id)
        self.assertEqual(not_precalculated["material_id"],material_id)
        self.assertEqual(not_precalculated["unique_id"],0) # should be the primitive id itself


        xxxyyyzzz = list(itertools.chain(*(not_precalculated["mat"])))
        self.assertAlmostEqual(xxxyyyzzz[0],1.0,5)
        self.assertAlmostEqual(xxxyyyzzz[3],2.0,5)
        self.assertAlmostEqual(xxxyyyzzz[6],3.0,5)


        # adding a second point
        pb.add_point(5,6,7,*xyzfloat_point)

        # checking the second point is correct
        self.assertEqual(pb.primitive_count(),2)

        point_1 = pb.get_primitive(1)

        self.assertEqual(point_1["node_id"],5)
        self.assertEqual(point_1["geometry_id"],6)
        self.assertEqual(point_1["material_id"],7)
        self.assertEqual(point_1["unique_id"],1) # should be the primitive id itself

        # checking the first point is still correct
        point_0 = pb.get_primitive(0)

        print(not_precalculated)

        self.assertEqual(point_0["node_id"],node_id)
        self.assertEqual(point_0["geometry_id"],geom_id)
        self.assertEqual(point_0["material_id"],material_id)
        self.assertEqual(point_0["unique_id"],0) # should be the primitive id itself







        pb.add_point(0,0,0,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),3)


        pb.add_point(0,0,0,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),3)
        pb.add_point(0,0,0,*xyzfloat_point)
        self.assertEqual(pb.primitive_count(),3)


