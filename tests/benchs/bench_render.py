
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import tt3de

from pyinstrument import Profiler



from tt3de.asset_fastloader import fast_load
from tt3de.glm.pyglmtexture import GLMCamera, GLMMesh3D, GLMRenderContext
from tt3de.richtexture import ImageTexture, RenderContext, Segmap, StaticTexture, get_cube_vertices
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Point3D, PointElem, Triangle3D
from glm import vec3

import math
WIDTH = 300
HEIGHT = 80

camera = FPSCamera(Point3D(0, 0, -3), WIDTH, HEIGHT)
camera.set_yaw_pitch(0.0,0.0)
camera.set_projectioninfo(math.radians(80),1.0,100.0,1.8)

glmcam = GLMCamera(Point3D(0, 0, 2.1), WIDTH, HEIGHT,fov_radians=math.radians(70))

glmcam.set_yaw_pitch(0.0,0.0)
camera.set_projectioninfo(math.radians(68),0.1,100.0,2.5)

glmMesh:GLMMesh3D = fast_load("models/cube.obj",GLMMesh3D)
mesh:Mesh3D = fast_load("models/cube.obj",Mesh3D)


texture2 = fast_load("models/cubetest2.bmp")


mesh.set_texture(texture2)
glmMesh.set_texture(texture2)
glmMesh.cache_output(Segmap().init())


rc= RenderContext(WIDTH,HEIGHT)
rc.append(mesh)
glmrc = GLMRenderContext(WIDTH,HEIGHT)
glmrc.append(glmMesh)
setup="""
from __main__ import rc,camera,glmrc,glmcam
"""


if __name__ == '__main__':

    itercount = 50
    
    import timeit

    durpy= timeit.timeit(stmt="(rc.render(camera))", number=itercount,
                       setup=setup)
    print(f"{(durpy/itercount)*1000:.5f} ms per iteration")
    
    durglm= timeit.timeit(stmt="(glmrc.render(glmcam))", number=itercount,
                       setup=setup)
    print(f"{(durglm/itercount)*1000:.5f} ms per iteration")


    print(f"factor : {(durpy/durglm):.2f}")