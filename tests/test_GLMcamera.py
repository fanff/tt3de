
import math
import random
import unittest

from context import tt3de

from tt3de.glm.pyglmtexture import GLMCamera
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem

import glm

from glm import vec3


def assertAlmostEqualGLM(a: glm.vec3, b: glm.vec3, limit=0.00001):
    assert glm.length(a-b) < limit,  f"error equaling : \na = {a}\nb = {b} "
    


class TestCameraInit(unittest.TestCase):


    def test_vector_ref(self):
        c = GLMCamera(Point3D(12, 24, 56))

        c.set_yaw_pitch(.2,1.1)

        dirvec = c._rotation*glm.vec3(0,0,1)
        lrvec = c._rotation*glm.vec3(1,0,0)
        udvec = c._rotation*glm.vec3(0,1,0)
        
        
        
        #print(dirvec)
        #print(lrvec)
        #print(udvec)


        noise_factor = .2
        rpx,rpy,rpz = random.random()-.5, random.random()-.5, random.random()-.5
        
        #print(rpx,rpy,rpz)
        random_noise = noise_factor*(dirvec*rpx+ lrvec*rpy + udvec * rpz)
        
        point_in_front_of_camera_noised = c.pos+c.direction_vector()+random_noise
        point_in_the_camera_coordinate=c._model*point_in_front_of_camera_noised

        #print(point_in_the_camera_coordinate) # this should look like a direction vector
        #print((c._model*glm.array(glm.vec4(point_in_front_of_camera_noised,1.0))))

    def test_projection_distance(self):
        # can't understand what is the z value of the Projectzo stuff


        c = GLMCamera(Point3D(12, 24, 56))

        #c.set_yaw_pitch(.2,1.1)

        dirvec = c._rotation*glm.vec3(0,0,1)
        lrvec = c._rotation*glm.vec3(1,0,0)
        udvec = c._rotation*glm.vec3(0,1,0)


        print(dirvec)
        print(lrvec)
        print(udvec)
        c.perspective

        screeninfo = glm.vec4(0,0,1,1)

        
        p1 = glm.perspectiveFovLH_ZO(math.radians(90), 1, 1, 1, 10)
        p2 = glm.perspectiveFovRH_ZO(math.radians(90), 1, 1, 1, 10)


        for p in [glm.vec3(0,0,-2),glm.vec3(0,0,2),glm.vec3(0,0,5),glm.vec3(0,0,10),glm.vec3(0,0,12)]:

            #p = glm.vec3(0,0,-2)
            print("p:",p)
            for perspective in [p1,p2]:
                projected = glm.projectZO(p,glm.identity(glm.mat4),perspective,screeninfo)
                
                est_dist = math.atan(projected.z)
                print(f"projectedz {projected.z:.2f}  -> {est_dist:.2f}")

    def test_direction_vector(self):
        for i in range(100):
            import random

            c = GLMCamera(Point3D(0, 0, 0))

            rpx,rpy,rpz = random.random(), random.random(), random.random()
            rp = glm.vec3(rpx,rpy,rpz)
            rp = glm.normalize(rp)

            c.point_at(rp)
            dv = c.direction_vector()

            self.assertAlmostEqual(glm.length(dv),1.0,2)
            assertAlmostEqualGLM(rp, dv)


def makeelements_on_x():
    c = GLMCamera(Point3D(0, 0, 0))
    c.point_at(glm.vec3(1, 0, 0))

    assertAlmostEqualGLM(glm.vec3(1, 0, 0), c.direction_vector())
    perspective_matrix = glm.perspectiveFovZO(math.radians(90), 2, 2, 1,10.0) 

    po =glm.vec3(5, 0, 0) 
    p1 =glm.vec3(5, -.1, 0) 
    p2 =glm.vec3(5, .1, 0) 
    p3 =glm.vec3(5, 0, -.1) 
    p4 =glm.vec3(5, 0, .1) 

    return c,perspective_matrix,po,p1,p2,p3,p4



class TestCameraPJ(unittest.TestCase):


    def test_proj_indirection(self):
        c = GLMCamera(Point3D(12, 1, 3))

        p = glm.vec3(.5, -.5, .5)

        c.point_at(p)
        assertAlmostEqualGLM(glm.normalize(p-c.pos), c.direction_vector())

        perspectivematrix = glm.perspectiveFovZO(math.radians(90), 1, 1, 1.0,10.0)

        print("amplitude check")
        for amp in [-.5,-.1,.1,.5,0.9,1.1,1.2, 1.8,  1.9,2.0 , 2.2,9,9.7,11,30]:

            centerp = c.project(c.pos+(c.direction_vector()*amp),perspectivematrix)
            #print(f"amp = {amp} centerp = {centerp}")
        #assertAlmostEqualGLM(centerp, vec3(.5,.5,1.0))

    def test_projx(self):
        c = GLMCamera(Point3D(0, 0, 0))
        c.point_at(glm.vec3(1, 0, 0))
        assertAlmostEqualGLM(glm.vec3(1, 0, 0), c.direction_vector())
        perspective_matrix = glm.perspectiveFovZO(math.radians(90), 2, 2, 1,10.0) 


        projected_point = c.project(glm.vec3(5, 0, 0) , perspective_matrix)
        self.assertGreater(projected_point.z , 0)
        self.assertAlmostEqual(projected_point.x,.5,2)
        self.assertAlmostEqual(projected_point.y,.5,2)
        zclos = projected_point.z

        projected_point = c.project(glm.vec3(10, 0, 0), perspective_matrix)
        self.assertGreater(projected_point.z , 0)
        self.assertAlmostEqual(projected_point.x,.5,2)
        self.assertAlmostEqual(projected_point.y,.5,2)

        self.assertLess(projected_point.z , zclos)

        projected_point = c.project(glm.vec3(-5, 0, 0), perspective_matrix)
        self.assertAlmostEqual(projected_point.x,.5,2)
        self.assertAlmostEqual(projected_point.y,.5,2)
        self.assertGreater(projected_point.z , 0)

    def test_projx2(self):
        c,perspective_matrix,po,p1,p2,p3,p4 = makeelements_on_x()
        
        
        ppo = c.project(po , perspective_matrix)
        pp1 = c.project(p1 , perspective_matrix)
        pp2 = c.project(p2 , perspective_matrix)
        pp3 = c.project(p3 , perspective_matrix)
        pp4 = c.project(p4 , perspective_matrix)

        # TODO check
        self.assertprojection_correct(ppo,pp1,pp2,pp3,pp4)
    def assertprojection_correct(self,ppo,pp1,pp2,pp3,pp4):
        # p1 and p2 moved along Y axis
        # so they should have the same x value
        self.assertAlmostEqual(pp1.x,ppo.x,2)
        self.assertAlmostEqual(pp2.x,ppo.x,2)


        # also p1 should left to p2
        self.assertGreater(pp1.y,pp2.y)

        # p3 and p4 moved along Z axis
        # so they should have the same y value
        self.assertAlmostEqual(pp3.y,ppo.y,2)
        self.assertAlmostEqual(pp4.y,ppo.y,2)
        
        # also p3 should be below p4
        self.assertLess(pp3.x,pp4.x)

    def test_proj_rotatedY(self):

        for i in range(100):
            c,perspective_matrix,po,p1,p2,p3,p4 = makeelements_on_x()
            
            # rotate the camera to the right
            c.rotate_left_right(-i)

            # rotate every point to the right 
            po = glm.rotateY(po,i)
            p1 = glm.rotateY(p1,i)
            p2 = glm.rotateY(p2,i)
            p3 = glm.rotateY(p3,i)
            p4 = glm.rotateY(p4,i)
            
            ppo = c.project(po , perspective_matrix)
            pp1 = c.project(p1 , perspective_matrix)
            pp2 = c.project(p2 , perspective_matrix)
            pp3 = c.project(p3 , perspective_matrix)
            pp4 = c.project(p4 , perspective_matrix)

            self.assertprojection_correct(ppo,pp1,pp2,pp3,pp4)

    def test_proj_rotatepitch(self):

        c,perspective_matrix,po,p1,p2,p3,p4 = makeelements_on_x()

        for angledeg in range(0,400):
            rotationpitch=math.radians(angledeg)
            # rotate the camera up/down
            c.rotate_up_down(-rotationpitch)

            # rotate every point to the right 
            arot = glm.rotate(rotationpitch,vec3(0,0,1))

            po = arot*po
            p1 = arot*p1
            p2 = arot*p2
            p3 = arot*p3
            p4 = arot*p4

            ppo = c.project(po , perspective_matrix)
            pp1 = c.project(p1 , perspective_matrix)
            pp2 = c.project(p2 , perspective_matrix)
            pp3 = c.project(p3 , perspective_matrix)
            pp4 = c.project(p4 , perspective_matrix)

            self.assertprojection_correct(ppo,pp1,pp2,pp3,pp4)
        


if __name__ == "__main__":
    unittest.main()