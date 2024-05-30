


from array import array
import math
import random
import unittest
import glm

from glm import vec3,mat3
from c_triangle_raster import TrianglesBuffer,make_per_pixel_index_buffer,make_per_pixel_data_buffer
from tt3de.glm.triangle_raster import generate_random_triangle

def pix_buff_to_string(pixel_buffer,w,h,index_shift=1):
    """
    
    index_shift = 
    0 # triangle idx
    1 # for material_id
    """
    lines = []
    for yi in range(h):
        ontheline = []
        for xi in range(w):
            index = (((h) * xi) + yi)*2   #  because that is its size 
            matid = str(pixel_buffer[index+index_shift])
            ontheline.append(matid[:1])

        lines.append("".join(ontheline))
    return "\n".join(lines)


class Test_CalcInternals(unittest.TestCase):
    def test_calculate_variation(self):
        
        # lets create a triangle clock wise
        triangle1 = mat3(vec3(1.2,3.4,   1.0),
                 vec3(5.2,5.4   ,1.0),
                 vec3(8.2,2.4   ,1.0))
        
        # the same triangle with various Z
        triangle2 = mat3(vec3(1.2,3.4,   -2321.5),
                 vec3(5.2,5.4   ,-100.1),
                 vec3(8.2,2.4   ,-123.6))


        # calculate internal for triangle 1
        m1 = TrianglesBuffer(30)
        m1.add_triangle_info(triangle1,1)
        m1.calculate_internal(10,10)
        self.assertEqual( len(m1.as_pylist()),1  )
        thetricalculated = m1.as_pylist()[0]

        tri1_adjoint = thetricalculated["adjoint"]
        tri1_coefs = thetricalculated["coefs"]
        tri1_flatdete = thetricalculated["flat_determinant"]


        # calculate internal for triangle 1
        m2 = TrianglesBuffer(30)
        m2.add_triangle_info(triangle2,1)
        m2.calculate_internal(10,10)
        self.assertEqual( len(m2.as_pylist()),1  )
        thetri2calculated = m2.as_pylist()[0]

        tri2_adjoint = thetri2calculated["adjoint"]
        tri2_coefs = thetri2calculated["coefs"]
        tri2_flatdete = thetri2calculated["flat_determinant"]
        


        #print(tri1_flatdete,tri2_flatdete)
        self.assertEqual( tri1_flatdete,tri2_flatdete  )


        print(tri1_coefs,"\n",tri2_coefs)

        for edge in range(3):
            self.assertEqual(tri1_coefs[edge]["alpha"],tri2_coefs[edge]["alpha"])
            self.assertEqual(tri1_coefs[edge]["beta"],tri2_coefs[edge]["beta"])

        for i in range(3):
            for j in range(3):
                self.assertEqual(tri1_adjoint[i][j],tri2_adjoint[i][j])

        self.assertEqual(thetricalculated["ax"],thetri2calculated["ax"])
        self.assertEqual(thetricalculated["ay"],thetri2calculated["ay"])
        self.assertEqual(thetricalculated["bx"],thetri2calculated["bx"])
        self.assertEqual(thetricalculated["by"],thetri2calculated["by"])
        self.assertEqual(thetricalculated["cx"],thetri2calculated["cx"])
        self.assertEqual(thetricalculated["cy"],thetri2calculated["cy"])


        ### now we can test that the raster is exactly the same 

        pixel_buff_1 = make_per_pixel_index_buffer(10,10)
        data_buff_1 = make_per_pixel_data_buffer(10,10,float("inf"))
        m1.raster_to_buffer(data_buff_1,pixel_buff_1)

        pixel_buff_2 = make_per_pixel_index_buffer(10,10)
        data_buff_2 = make_per_pixel_data_buffer(10,10,float("inf"))
        m2.raster_to_buffer(data_buff_2,pixel_buff_2)

        # now we can compare the two pixel buffer, should be the same 
        self.assertEqual(pix_buff_to_string(pixel_buff_1,10,10,index_shift=1),
                        pix_buff_to_string(pixel_buff_2,10,10,index_shift=1))
        



class Test_TrianglesBuffer(unittest.TestCase):

    def test_creation(self):
        m = TrianglesBuffer(10)

        print(m.count())

        print(type(m))

        print(m==m)

        print(dir(m))

        
        self.assertEqual( len(m.as_pylist()),  0 )

        self.assertEqual( m.count(),  0 )
        
        m.clear()
        self.assertEqual( len(m.as_pylist()),  0 )
        self.assertEqual( m.count(),  0 )


    def test_adding_triangle(self):

        m = TrianglesBuffer(10)
        self.assertEqual( m.count(),  0 )
        self.assertEqual( len(m.as_pylist()),  0 )

        a,b,c = generate_random_triangle()
        tri = glm.mat3(a,b,c)
        m.add_triangle_info(tri)
        self.assertEqual( m.count(),  1 )   
        self.assertEqual( len(m.as_pylist()),  1 )

        print(m.as_pylist())

        
        a,b,c = generate_random_triangle()
        tri = glm.mat3(a,b,c)

        uvmap = (1.0,2.0,3.0,4.0,5.0,6.0)
        m.add_triangle_info(tri,material_id=2,uvmap=uvmap)

        self.assertEqual( m.count(),  2 )   
        self.assertEqual( len(m.as_pylist()),  2 )


        m.clear()

        self.assertEqual( m.count(),  0 )
        self.assertEqual( len(m.as_pylist()),  0 )


        #testing memory limit
        for i in range(12):
            a,b,c = generate_random_triangle()
            tri = glm.mat3(a,b,c)
            m.add_triangle_info(tri)


        self.assertEqual( m.count(),  10 )
        self.assertEqual( len(m.as_pylist()), 10 )
    def test_adding_many_triangle(self):

        m = TrianglesBuffer(30)


        manytri = [glm.mat3(*generate_random_triangle())for i in range(12)]

        m.add_many_triangles(manytri)

        self.assertEqual( m.count(),  12 )
        self.assertEqual( len(m.as_pylist()), 12 )

        m.add_many_triangles(manytri)

        self.assertEqual( m.count(),  24 )
        self.assertEqual( len(m.as_pylist()), 24 )


        m.add_many_triangles(manytri)

        self.assertEqual( m.count(),  30 )
        self.assertEqual( len(m.as_pylist()), 30 )


            
    def test_calculate_internals(self):
        m = TrianglesBuffer(30)
        m.calculate_internal(10,10)

        manytri = [glm.mat3(*generate_random_triangle()) for i in range(40)]

        m.add_many_triangles(manytri)
        m.calculate_internal(10,10)
        print(m.as_pylist())

    def test_raster_triangle(self):
        m = TrianglesBuffer(100000)
        m.calculate_internal(10,10)
        print(f"done instancing TrianglesBuffer")

        tricount = 10000
        manytri = [glm.mat3(*generate_random_triangle(CW_option=False)) 
                   for i in range(tricount)]
        print(f"done making {tricount} triangles")
        m.add_many_triangles(manytri)
        scw,sch = 100,100
        m.calculate_internal(scw,sch)

        # prepare the buffer to hold the projection data.
        index_buffer = make_per_pixel_index_buffer(scw,sch)
        depth_buffer = make_per_pixel_data_buffer(scw,sch)
        print(f"done making outputbuffer")
        import time 

        strt = time.time()
        m.raster_to_buffer(depth_buffer,index_buffer)
        duration = time.time()-strt

        if duration != 0.0:
            print(f"duration baking {duration*1000:.2f} ms ({tricount/duration} tri/sec)")
        print(depth_buffer[:10])