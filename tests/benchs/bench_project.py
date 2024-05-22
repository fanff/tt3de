import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import glm
from pyinstrument import Profiler

from tt3de.asset_fastloader import fast_load
from tt3de.pyglmtexture import GLMCamera, GLMMesh3D
from tt3de.richtexture import ImageTexture, RenderContext, Segmap, StaticTexture, get_cube_vertices
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Point3D, PointElem, Triangle3D
from glm import vec3

WIDTH = 400
HEIGHT = 400


camera = FPSCamera(pos=Point3D(5, 0, 5))
glmcam = GLMCamera(camera.pos, 90, 90)

camera.point_at(Point3D(0, 0, 0))
camera.recalc_fov_h(WIDTH,HEIGHT)

glmcam.point_at(vec3(0, 0, 0))
glmcam.recalc_fov_h(WIDTH,HEIGHT)

glmMesh:GLMMesh3D = fast_load("models/cube.obj",GLMMesh3D)
mesh = fast_load("models/cube.obj",Mesh3D)


texture2 = fast_load("models/cubetest2.bmp")


mesh.set_texture(texture2)
glmMesh.set_texture(texture2)
glmMesh.cache_output(Segmap().init())
#m.triangles=m.triangles[3:4]

perspective_matrix = glm.perspectiveFovZO(math.radians(90), 2, 2, 1,10.0) 

if __name__ == '__main__':

    itercount = 30000
    
    import timeit
    res= timeit.timeit(stmt="list(mesh.proj_vertices(camera,200,200))", number=itercount,setup="from __main__ import mesh,camera")
    print(f"{(res/itercount)*1000:.5f} ms per iteration")
    
    glmMesh.proj_vertices(glmcam,perspective_matrix,200,200)
    res= timeit.timeit(stmt="list(glmMesh.proj_vertices(glmcam,perspective_matrix,200,200))", number=itercount,setup="from __main__ import glmMesh,glmcam,perspective_matrix")
    print(f"{(res/itercount)*1000:.5f} ms per iteration")
