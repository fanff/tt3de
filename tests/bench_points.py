import math
import timeit
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
    PPoint2D,
    Point3D,
    PointElem,
    Triangle3D,
    load_bmp,
)


import random


def proc_point2d():
    p = PPoint2D(0.0, 1.0)
    p2 = PPoint2D(1.0, 0.0)
    p3 = random.random() * p + random.random() * p2
    p3.magnitude()


class CPPoint2D(complex):

    depth: float
    uv: "CPPoint2D"
    dotval: float


def cproc_point2d():
    p = CPPoint2D(0.0, 1.0)
    p2 = CPPoint2D(1.0, 0.0)
    p3 = random.random() * p + random.random() * p2

    abs(p3)


def normalize(v: "Point3D"):
    n2 = v.x**2 + v.y**2 + v.z**2
    norm = math.sqrt(n2)
    if norm == 0:
        norm = 1e-6
    return Point3D(v.x / norm, v.y / norm, v.z / norm)


def proc_point3d():
    p1 = Point3D(1.0, 0.0, 0.0)
    p2 = Point3D(0.0, 1.0, 0.0)
    p3 = Point3D(0.0, 0.0, 1.0)
    fd = random.random() * p1 + random.random() * p2 + random.random() * p3

    fd.magnitude()

    normalize(fd)


def c3dmagnitude(self):
    return (self.real.real**2 + self.real.imag**2 + self.imag**2) ** 0.5


def c3normalize(v: "CPPoint3D"):
    n2 = v.real.real**2 + v.real.imag**2 + v.imag**2
    norm = math.sqrt(n2)
    if norm == 0:
        norm = 1e-6
    return v / norm


def proc_cpoint3d():
    p1 = complex(complex(1.0, 0.0), 0.0)
    p2 = complex(complex(0.0, 1.0), 0.0)
    p3 = complex(complex(0.0, 0.0), 1.0)
    fd = random.random() * p1 + random.random() * p2 + random.random() * p3

    c3dmagnitude(fd)

    c3normalize(fd)


if __name__ == "__main__":
    import timeit

    stm = """
proc_point2d()
    """
    res = timeit.timeit(
        stmt=stm, number=100000, setup="from __main__ import proc_point2d"
    )
    print(res)

    stm = """
cproc_point2d()
    """
    res = timeit.timeit(
        stmt=stm, number=100000, setup="from __main__ import cproc_point2d"
    )
    print(res)

    stm = """
proc_point3d()
    """
    res = timeit.timeit(
        stmt=stm, number=100000, setup="from __main__ import proc_point3d"
    )
    print(res)

    stm = """
proc_cpoint3d()
    """
    res = timeit.timeit(
        stmt=stm, number=100000, setup="from __main__ import proc_cpoint3d"
    )
    print(res)
