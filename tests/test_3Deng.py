import math
import unittest

from context import tt3de 
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem, RenderContext


def assertAlmostEqualP3D(a:Point3D,b:Point3D, limit=0.00001):
    assert (a-b).magnitude() < limit, f"a = {a},b = {b} "
    
class TestCameraInit(unittest.TestCase):

    def test_many(self):
        for i in range(100):
            import random
            
            c = FPSCamera(Point3D(0,0,0))


            rp = Point3D(random.random(), random.random(), random.random())
            rp=rp.normalize()


            c.point_at(rp)
            dv = c.direction_vector()
            assertAlmostEqualP3D(rp,dv)

    def test_rottop(self):
        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(1,0,0))
        dX = c.direction_vector()
        assertAlmostEqualP3D(dX,Point3D(1,0,0))


        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(-1,0,0))
        dmX = c.direction_vector()
        assertAlmostEqualP3D(dmX,Point3D(-1,0,0))


        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(0,0,1))
        dZ = c.direction_vector()
        assertAlmostEqualP3D(dZ,Point3D(0,0,1))


        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(0,0,-10))
        dmZ = c.direction_vector()
        assertAlmostEqualP3D(dmZ,Point3D(0,0,-1))

        

class TestPJ(unittest.TestCase):
    def test_projx(self):
        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(1,0,0))
        
        assertAlmostEqualP3D(Point3D(1,0,0),c.direction_vector())

        projected_point = c.project(Point3D(5,0,0))
        self.assertTrue(projected_point.depth>0)
        projected_point = c.project(Point3D(-5,0,0))
        self.assertTrue(projected_point.depth==-1)

    def test_projx2(self):
        c = FPSCamera(Point3D(0, 0, 0))
        c.point_at(Point3D(1,0,0))

        rc = RenderContext(100, 100)
        rc.append(PointElem(Point3D(5, 0, 0)))
        
        res = rc.render(c)

        self.assertEqual(len(res[0]),1,f"{str(res)}")
        p = res[0][0]
        self.assertEqual(p.x, 50)
        self.assertEqual(p.y, 50)
        self.assertEqual(p.depth, 5)

    

class TestCameraUpDown(unittest.TestCase):

    def setUp(self) -> None:
        self.rc = RenderContext(100, 100)
        self.rc.append(PointElem(Point3D(0, -1,0)))
        self.rc.append(PointElem(Point3D(0, 0 ,0)))
        self.rc.append(PointElem(Point3D(0, 2 ,0)))
        
    def tearDown(self) -> None:
        pass
    
    def test_point_X(self):


        c = FPSCamera(Point3D(5, 0, 0))
        c.point_at(Point3D(0,0,0))

        res = self.rc.render(c)
        self.run_ss(res)



    def test_point_Z(self):
        #rotated_camera a bit to the x axis
        c = FPSCamera(Point3D(0, 0, 5))
        c.point_at(Point3D(0,0,0))

        res = self.rc.render(c)
        self.run_ss(res)


    def test_point_xxx(self):
        #rotated_camera a bit to the x axis
        c = FPSCamera(Point3D(0, 0, -5))
        c.point_at(Point3D(0,0,0))
        res = self.rc.render(c)
        self.run_ss(res)


    def test_rotating_camera(self):
        for _ in range(100):
            # calc camera position 

            amp = 7
            tf = 6.0/100
            c1 = math.cos(tf*_)*amp
            c2 = math.sin(tf*_)*amp

            
            c = FPSCamera(Point3D(c1, 0, c2))
            c.point_at(Point3D(0,0,0))

            res = self.rc.render(c)
            self.run_ss(res)

    def run_ss(self,res):
        ll = res[0][0]
        c = res[1][0]
        r = res[2][0]
       
        self.assertLess(ll.y,c.y)
        self.assertLess(c.y,r.y)

        self.assertAlmostEqual(ll.x,c.x,1)
        self.assertAlmostEqual(r.x,c.x,1)

if __name__ == '__main__':
    unittest.main()


