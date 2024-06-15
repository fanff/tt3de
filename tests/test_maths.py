import math
import unittest


from tt3de.tt3de import (
    Camera,
    FPSCamera,
    Mesh3D,
    Point3D,
    PointElem,
    Quaternion,
    Triangle3D,
)


def assertAlmostEqualP3D(a: Point3D, b: Point3D, limit=0.00001):
    assert (a - b).magnitude() < limit, f"a = {a},b = {b} "


class TestQuad(unittest.TestCase):

    def test_0(self):

        q = Quaternion.from_euler(0, 0, 0)
        r = q.rotate_point(Point3D(1, 0, 0))

        print(r)

    def test_Yrot(self):
        point = Point3D(1, 0, 0)
        q = Quaternion.from_euler(0, math.pi / 2, 0)
        r = q.inverse().rotate_point(point)
        print(r)

        r = Quaternion.from_euler(0, math.pi, 0).rotate_point(point)
        print(r)

        r = Quaternion.from_euler(0, 3 * math.pi / 2, 0).rotate_point(point)
        print(r)


class TestTriangle(unittest.TestCase):

    def test_0(self):
        a, b, c = Point3D(0, 0, 0), Point3D(0, 0, 1), Point3D(1, 0, 1)

        assertAlmostEqualP3D(Triangle3D(a, b, c).normal, Triangle3D(b, c, a).normal)
        assertAlmostEqualP3D(Triangle3D(a, b, c).normal, Triangle3D(c, a, b).normal)
        assertAlmostEqualP3D(Triangle3D(a, b, c).normal, Point3D(0, 1, 0))

        t = Triangle3D(c, b, a)

        assertAlmostEqualP3D(Triangle3D(c, b, a).normal, Triangle3D(a, c, b).normal)
        assertAlmostEqualP3D(Triangle3D(c, b, a).normal, Triangle3D(b, a, c).normal)
        assertAlmostEqualP3D(Triangle3D(c, b, a).normal, Point3D(0, -1, 0))


import random
import math
import unittest


from tt3de.glm.c_math import c_floor_f, c_ceil_f, c_round_f, c_clamp_and_round_f


class Test_c_custom_math_func(unittest.TestCase):

    def test_custom_math_artihmetic(self):

        numberlist = [-12, -2.1, -1.9, 2.3, 1.1, 2.9, 101221.2]

        for n in numberlist:
            self.assertEqual(math.floor(n), c_floor_f(n))
            self.assertEqual(math.ceil(n), c_ceil_f(n))
            self.assertEqual(round(n), c_round_f(n))

        for i in range(1000):
            n = random.normalvariate(0, 10033)
            self.assertEqual(math.floor(n), c_floor_f(n), f"floor issue with {n}")
            self.assertEqual(math.ceil(n), c_ceil_f(n), f"ceil issue with {n}")
            self.assertEqual(round(n), c_round_f(n), f"round issue with {n}")

            self.assertEqual(
                min(4000, max(round(n), 0)),
                c_clamp_and_round_f(n, 4000),
                f"clamp_and_round issue with {n}",
            )


if __name__ == "__main__":
    unittest.main()
