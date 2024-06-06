import math
from typing import List
import unittest

import glm

from context import tt3de

from tt3de.glm.triangle_clipping import calculate_normal, clip_triangle, split_quad_to_triangles
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem


from PIL import Image, ImageDraw


class Test_ClippingTriangle(unittest.TestCase):

    def test_triangle_no_clipping_z(self):
       
        near_plane = 0.01


        #standart view port 
        viewport = glm.vec4(0,0,1,1.0)
        #standart perspective with near and far plane
        p = glm.perspectiveFovZO(math.radians(90),400,400,near_plane,100.0)
        
        m = glm.mat4(1.0)

        v1      = glm.vec3( 2,   -2,   10.1)
        v2      = glm.vec3(-2,   -2,   10.1)
        v3      = glm.vec3( 0.0, -2.0, 8  )
        nv = calculate_normal(v1,v2,v3)


        res= clip_triangle(v1,v2,v3,near_plane, nv)
        
        self.assertEqual(len(res),3)


    def test_triangle_with_clipping_4z(self):
       
        near_plane = 0.01


        #standart view port 
        viewport = glm.vec4(0,0,1,1.0)
        #standart perspective with near and far plane
        p = glm.perspectiveFovZO(math.radians(90),400,400,near_plane,100.0)
        
        m = glm.mat4(1.0)

        v1      = glm.vec3(-2,   -2,   10.1)
        v2      = glm.vec3( 0,   -2,   -8.1)
        v3      = glm.vec3( 20.0, -2.0, 10  )
        nv = calculate_normal(v1,v2,v3)


        res= clip_triangle(v1,v2,v3,near_plane, nv)
        print(res)
        self.assertEqual(len(res),4)    

        sv1,sv2,sv3,sv4 = res
        two_triangles = split_quad_to_triangles(sv1,sv2,sv3,sv4,nv)


        t1 , t2 = two_triangles

        nt1 = calculate_normal(*t1)
        nt2 = calculate_normal(*t2)


        self.assertEqual(nt1,nv)    
        self.assertEqual(nt2,nv)    

    def test_triangle_with_clipping_3z(self):
       
        near_plane = 0.01


        #standart view port 
        viewport = glm.vec4(0,0,1,1.0)
        #standart perspective with near and far plane
        p = glm.perspectiveFovZO(math.radians(90),400,400,near_plane,100.0)
        
        m = glm.mat4(1.0)

        v1      = glm.vec3(-2,    -2,   -8.1  )
        v2      = glm.vec3( 0,    -2,    10.1   )
        v3      = glm.vec3( 2.0, -2.0,  -8.1  )
        nv = calculate_normal(v1,v2,v3)


        res= clip_triangle(v1,v2,v3,near_plane,nv)
        print(res)
        self.assertEqual(len(res),3)    

        sv1,sv2,sv3 = res

        self.assertGreater(glm.dot(calculate_normal(sv1,sv2,sv3),nv),0.8)
        #self.assertEqual(calculate_normal(sv1,sv2,sv3),nv)    


if __name__ == "__main__":
    unittest.main()
