from context import tt3de
from pyinstrument import Profiler

from tt3de.richtexture import (
    ImageTexture,
    RenderContext,
    StaticTexture,
    get_cube_vertices,
)
from tt3de.textual_widget import Cwr
from tt3de.tt3de import (
    FPSCamera,
    Line3D,
    Mesh3D,
    Point3D,
    PointElem,
    Triangle3D,
    load_bmp,
)

camera = FPSCamera(pos=Point3D(5, 2, 5))
camera.point_at(Point3D(0, 0, 0))

rc = RenderContext(200, 200)
cwr = Cwr(rc)

m = Mesh3D.from_obj("models/cube.obj")
texture2 = ImageTexture(load_bmp("models/cubetest2.bmp"))


m.set_texture(texture2)
# m.triangles=m.triangles[3:4]
rc.append(m)

profiler = Profiler()
profiler.start()

for i in range(100):
    rc.render(camera)

profiler.stop()

profiler.print(color=True, show_all=True)
