

import math
import unittest

from context import tt3de
import glm
from tt3de.asset_fastloader import fast_load
from tt3de.glm.pyglmtexture import GLMCamera, GLMMesh3D
from tt3de.richtexture import Segmap
from tt3de.tt3de import Camera, FPSCamera, Mesh3D, Point3D, PointElem, Quaternion, Triangle3D
from glm import vec3
import glm

class TestCameraInit(unittest.TestCase):

    def test_simplepoint(self):
        WIDTH = 400
        HEIGHT = 400

        dist = 10

        camera = FPSCamera(pos=Point3D(0, 0, dist))
        glmcam = GLMCamera(camera.pos, 90, 90)

        camera.point_at(Point3D(0, 0, 0))
        glmcam.point_at(vec3(0, 0, 0))

        point = Point3D(1,0,0)
        native_py = camera.project(point)

        glmpoint = vec3(1,0,0)
        perspective_matrix = glm.perspectiveFovZO(math.radians(50), float(WIDTH),float(HEIGHT), 1,100.0) 
        glmp = glmcam.project(glmpoint,perspective_matrix)


        print(native_py)
        print(glmp)

    def test_meshproj(self):

        WIDTH = 400
        HEIGHT = 400

        camera = FPSCamera(pos=Point3D(5, 0, 5))
        glmcam = GLMCamera(camera.pos, 90, 90)

        camera.point_at(Point3D(0, 0, 0))
        glmcam.point_at(vec3(0, 0, 0))

        glmMesh:GLMMesh3D = fast_load("models/cube.obj",GLMMesh3D)
        mesh:Mesh3D = fast_load("models/cube.obj",Mesh3D)


        texture2 = fast_load("models/cubetest2.bmp")


        mesh.set_texture(texture2)
        glmMesh.set_texture(texture2)
        glmMesh.cache_output(Segmap().init())

    
        perspective_matrix = glm.perspectiveFovZO(math.radians(40), (WIDTH),(HEIGHT), 1.0,1000.0) 

        glmproj = glmMesh.proj_vertices(glmcam,perspective_matrix,200,200)

        native_proj = mesh.proj_vertices(camera,200,200)

        for glmmat,nav in zip(glmproj,native_proj):
            print(glmmat,nav)

if __name__ == "__main__":  
    unittest.main()