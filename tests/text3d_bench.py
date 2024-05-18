
from pyinstrument import Profiler

from context import tt3de 
from tt3de.richtexture import RenderContext, StaticTexture
from tt3de.textual_widget import Cwr
from tt3de.tt3de import FPSCamera, Line3D, Point3D, PointElem,Triangle3D
camera = FPSCamera(pos=Point3D(5, 2, 5))
camera.point_at(Point3D(0,0,0))

rc = RenderContext(200,200)
cwr = Cwr(rc)
triangle = Triangle3D(Point3D(0,0,0),Point3D(0,0,5),Point3D(5,5,0),StaticTexture("L",color="red",bgcolor="red"))
rc.append(triangle)


rc.append(Line3D(Point3D(0.1,0,0),Point3D(0.9,0,0),StaticTexture("x","red")))
rc.append(Line3D(Point3D(0,0.1,0),Point3D(0,0.9,0),StaticTexture("y","blue")))
rc.append(Line3D(Point3D(0,0,0.1),Point3D(0,0,0.9),StaticTexture("z","green")))
rc.append(PointElem(Point3D(0,0,0),StaticTexture("O","white"),))
rc.append(PointElem(Point3D(1,0,0),StaticTexture("X","red")))
rc.append(PointElem(Point3D(0,1,0),StaticTexture("Y","blue")))
rc.append(PointElem(Point3D(0,0,1),StaticTexture("Z","green")))


for i in range(3):
    rc.extend(get_cube_vertices(Point3D(0,i,0),0.7))
rc.extend(get_cube_vertices(Point3D(2,0,0),0.7))
rc.extend(get_cube_vertices(Point3D(3,0,0),0.7))
rc.extend(get_cube_vertices(Point3D(1,0,0),0.7))


profiler = Profiler()
profiler.start()

for i in range(1000):
    rc.render(camera)
    #triangle.draw(camera,100,100)
profiler.stop()

profiler.print(color=True,show_all=True)