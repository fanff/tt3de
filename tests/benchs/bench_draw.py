import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import tt3de

from pyinstrument import Profiler

from tt3de.asset_fastloader import fast_load
from tt3de.glm.pyglmtexture import GLMCamera, GLMMesh3D
from tt3de.richtexture import ImageTexture, RenderContext, Segmap, StaticTexture, get_cube_vertices
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Point3D, PointElem, Triangle3D
from glm import vec3
WIDTH = 100
HEIGHT = 100


camera = FPSCamera(pos=Point3D(5, 0, 5))
glmcam = GLMCamera(camera.pos, 90, 90)

camera.point_at(Point3D(0, 0, 0))
#camera.recalc_fov_h(WIDTH,HEIGHT)

glmcam.point_at(vec3(0, 0, 0))
#glmcam.recalc_fov_h(WIDTH,HEIGHT)

glmMesh:GLMMesh3D = fast_load("models/cube.obj",GLMMesh3D)
mesh:Mesh3D = fast_load("models/cube.obj",Mesh3D)


texture2 = fast_load("models/cubetest2.bmp")


mesh.set_texture(texture2)
glmMesh.set_texture(texture2)
glmMesh.cache_output(Segmap().init())




if __name__ == '__main__':

    itercount = 200
    
    import timeit
    setupstr = "from __main__ import mesh,camera,glmMesh,glmcam;import collections;\nWIDTH,HEIGHT=200,100"
    nativepy = list(mesh.draw(camera,WIDTH,HEIGHT))
    native_py_duration= timeit.timeit(stmt="collections.deque(mesh.draw(camera, WIDTH,HEIGHT), maxlen=0)", number=itercount,setup=setupstr)
    print(f"{(native_py_duration/itercount)*1000:.5f} ms per iteration")
    
    glmver = list(glmMesh.draw(glmcam,WIDTH,HEIGHT))
    glmduration= timeit.timeit(stmt="collections.deque(glmMesh.draw(glmcam, WIDTH,HEIGHT), maxlen=0)", number=itercount,setup=setupstr)
    print(f"{(glmduration/itercount)*1000:.5f} ms per iteration")

    print(f"perf ratio: {native_py_duration/glmduration:.5f}")

    print(len(nativepy),len(glmver))