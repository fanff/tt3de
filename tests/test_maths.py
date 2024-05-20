

import math
import unittest

from context import tt3de

from tt3de.tt3de import Camera, FPSCamera, Mesh3D, Point3D, PointElem, Quaternion, Triangle3D, extract_palette, load_bmp, round_to_palette


def assertAlmostEqualP3D(a: Point3D, b: Point3D, limit=0.00001):
    assert (a - b).magnitude() < limit, f"a = {a},b = {b} "



class TestQuad(unittest.TestCase):


    def test_0(self):

        q = Quaternion.from_euler(0,0,0)
        r = q.rotate_point(Point3D(1,0,0))


        print(r)


    def test_Yrot(self):
        point = Point3D(1,0,0)
        q = Quaternion.from_euler(0,math.pi/2,0)
        r = q.inverse().rotate_point(point)
        print(r)

        r = Quaternion.from_euler(0,math.pi,0).rotate_point(point)
        print(r)

        r = Quaternion.from_euler(0,3*math.pi/2,0).rotate_point(point)
        print(r)

class TestTriangle(unittest.TestCase):


    def test_0(self):
        a,b,c = Point3D(0,0,0),Point3D(0,0,1),Point3D(1,0,1)

        assertAlmostEqualP3D( Triangle3D(a,b,c ).normal, Triangle3D(b,c,a ).normal)
        assertAlmostEqualP3D( Triangle3D(a,b,c ).normal, Triangle3D(c,a,b ).normal)
        assertAlmostEqualP3D( Triangle3D(a,b,c ).normal, Point3D(0,1,0))



        t = Triangle3D(c,b,a)

        assertAlmostEqualP3D( Triangle3D(c,b,a ).normal, Triangle3D(a,c,b ).normal)
        assertAlmostEqualP3D( Triangle3D(c,b,a ).normal, Triangle3D(b,a,c ).normal)
        assertAlmostEqualP3D( Triangle3D(c,b,a ).normal, Point3D(0,-1,0))


        

if __name__ == "__main__":  
    unittest.main()