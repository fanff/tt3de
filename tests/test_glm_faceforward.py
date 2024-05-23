import math
import unittest

import glm

from context import tt3de

from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem





class TestFaceforward(unittest.TestCase):

    def test_many(self):
        
        n = glm.vec3(1.1,2.2,3.3)

        for i in range(100):
            import random
            Nref = glm.vec3(0,0,1) 
            n = glm.vec3(random.random()-.5,random.random()-.5,random.random()-.5)
            #Ivec = glm.vec3(random.random()-.5,random.random()-.5,random.random()-.5)
            Ivec = glm.vec3(.4,-.5,.5)

            result = glm.faceforward(n,Ivec,Nref)

            #print(n,result)
    def test_matrix_triangle(self):
        #https://computergraphics.stackexchange.com/questions/9537/how-does-graphics-api-like-opengl-determine-which-triangle-is-back-face-to-cull


        mat = glm.mat3(1,2,3,4,5,6,7,8,9)
        print(mat)

        mat = glm.mat3(glm.vec3(.5,0,78),glm.vec3(-1,1,100),glm.vec3(1,1,111))
        print(mat)
        mat_det = glm.determinant(mat)
        print(mat_det)


if __name__ == "__main__":
    unittest.main()
