import math
import unittest

from context import tt3de

from tt3de.richtexture import RenderContext
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem


def assertAlmostEqualP3D(a: Point3D, b: Point3D, limit=0.00001):
    assert (a - b).magnitude() < limit, f"a = {a},b = {b} "


class TestCameraInit(unittest.TestCase):

    def test_many(self):
        for i in range(100):
            import random

            c = FPSCamera(Point3D(0, 0, 0))

            rp = Point3D(random.random(), random.random(), random.random())
            rp = rp.normalize()

            c.point_at(rp)
            dv = c.direction_vector()
            assertAlmostEqualP3D(rp, dv)

    def test_rottop(self):
        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(1, 0, 0))
        dX = c.direction_vector()
        assertAlmostEqualP3D(dX, Point3D(1, 0, 0))

        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(-1, 0, 0))
        dmX = c.direction_vector()
        assertAlmostEqualP3D(dmX, Point3D(-1, 0, 0))

        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(0, 0, 1))
        dZ = c.direction_vector()
        assertAlmostEqualP3D(dZ, Point3D(0, 0, 1))

        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(0, 0, -10))
        dmZ = c.direction_vector()
        assertAlmostEqualP3D(dmZ, Point3D(0, 0, -1))


class TestPJ(unittest.TestCase):
    def test_projx(self):
        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(1, 0, 0))

        assertAlmostEqualP3D(Point3D(1, 0, 0), c.direction_vector())

        projected_point = c.project(Point3D(5, 0, 0))
        self.assertGreater(projected_point.depth, 0)

        projected_6point = c.project(Point3D(6, 0, 0))
        self.assertGreater(projected_6point.depth, 0)
        self.assertGreater(projected_6point.depth, projected_point.depth)

        projected_point = c.project(Point3D(-5, 0, 0))
        self.assertEqual(projected_point.depth, 0)

    def test_projx2(self):
        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(1, 0, 0))

        rc = RenderContext(100, 100)
        rc.append(PointElem(Point3D(5, 0, 0)))

        rc.render(c)


if __name__ == "__main__":
    unittest.main()
