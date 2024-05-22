import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import tt3de

from pyinstrument import Profiler


setup="""
from tt3de.asset_fastloader import fast_load
from tt3de.pyglmtexture import GLMCamera, GLMMesh3D, GLMRenderContext
from tt3de.richtexture import ImageTexture, RenderContext, Segmap, StaticTexture, get_cube_vertices
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Point3D, PointElem, Triangle3D
from glm import vec3
WIDTH = 300
HEIGHT = 90

camera = FPSCamera(pos=Point3D(5, 0, 5), WIDTH, HEIGHT)
glmcam = GLMCamera(camera.pos, WIDTH, HEIGHT)

camera.point_at(Point3D(0, 0, 0))

glmcam.point_at(vec3(0, 0, 0))

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

"""


if __name__ == '__main__':

    itercount = 100
    
    import timeit

    res= timeit.timeit(stmt="(rc.render(camera))", number=itercount,
                       setup=setup)
    print(f"{(res/itercount)*1000:.5f} ms per iteration")
    
    res= timeit.timeit(stmt="(glmrc.render(glmcam))", number=itercount,
                       setup=setup)
    print(f"{(res/itercount)*1000:.5f} ms per iteration")
