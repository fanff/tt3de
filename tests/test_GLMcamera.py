import math
import random
import unittest

import random
from tt3de.glm.pyglmtexture import GLMCamera
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem

import glm

from glm import vec3


def assertAlmostEqualvec3(a: glm.vec3, b: glm.vec3, limit=0.00001):
    assert glm.length(a - b) < limit, f"error equaling : \na = {a}\nb = {b} "


class TestCameraInit(unittest.TestCase):

    def test_vector_ref(self):
        c = GLMCamera(Point3D(12, 24, 56))

        c.set_yaw_pitch(0.2, 1.1)

        dirvec = c._rotation * glm.vec3(0, 0, 1)
        lrvec = c._rotation * glm.vec3(1, 0, 0)
        udvec = c._rotation * glm.vec3(0, 1, 0)

        print(dirvec, lrvec, udvec)

        dirvec = glm.row(c.view_matrix_3D, 2).xyz
        udvec = glm.row(c.view_matrix_3D, 1).xyz
        lrvec = glm.row(c.view_matrix_3D, 0).xyz

        print(dirvec, lrvec, udvec)
        # print(dirvec)
        # print(lrvec)
        # print(udvec)

        noise_factor = 0.2
        rpx, rpy, rpz = (
            random.random() - 0.5,
            random.random() - 0.5,
            random.random() - 0.5,
        )

        # print(rpx,rpy,rpz)
        random_noise = noise_factor * (dirvec * rpx + lrvec * rpy + udvec * rpz)

        point_in_front_of_camera_noised = c.pos + c.direction_vector() + random_noise
        point_in_the_camera_coordinate = (
            c.view_matrix_3D * point_in_front_of_camera_noised
        )

        # print(point_in_the_camera_coordinate) # this should look like a direction vector
        # print((c._model*glm.array(glm.vec4(point_in_front_of_camera_noised,1.0))))

    def test_point_at(self):
        for i in range(100):

            c = GLMCamera(Point3D(0, 0, 0))

            rpx, rpy, rpz = random.random(), random.random(), random.random()
            rp = glm.vec3(rpx, rpy, rpz)
            rp = glm.normalize(rp)

            c.point_at(rp)
            dv = c.direction_vector()

            self.assertAlmostEqual(glm.length(dv), 1.0, 4)
            assertAlmostEqualvec3(rp, dv)

    def test_camera_reference(self):
        """verify camera is right handed"""
        for i in range(100):

            init_pos = glm.vec3(random.random(), random.random(), random.random())
            c = GLMCamera(init_pos)


            c.point_at(init_pos+glm.vec3(0, 0, 1))

            assertAlmostEqualvec3(c.direction_vector(),glm.vec3(0, 0, 1))
            assertAlmostEqualvec3(c.right_vector(),glm.vec3(-1, 0, 0))
            assertAlmostEqualvec3(c.up_vector(),glm.vec3(0, 1, 0))


class TestCameraRotate(unittest.TestCase):

    def test_camera_rotate_0(self):
        """verify camera is right handed"""
        for i in range(100):

            init_pos = glm.vec3(random.random(), random.random(), random.random())
            c = GLMCamera(init_pos)


            c.point_at(init_pos+glm.vec3(0, 0, 1))


            assertAlmostEqualvec3(c.direction_vector(),glm.vec3(0, 0, 1))
            assertAlmostEqualvec3(c.right_vector(),glm.vec3(-1, 0, 0))
            assertAlmostEqualvec3(c.up_vector(),glm.vec3(0, 1, 0))


            c.rotate_left_right(math.radians(0))

            assertAlmostEqualvec3(c.direction_vector(),glm.vec3(0, 0, 1))
            assertAlmostEqualvec3(c.right_vector(),glm.vec3(-1, 0, 0))
            assertAlmostEqualvec3(c.up_vector(),glm.vec3(0, 1, 0))


        

def makeelements_on_x():
    c = GLMCamera(Point3D(0, 0, 0))
    c.point_at(glm.vec3(1, 0, 0))

    assertAlmostEqualvec3(glm.vec3(1, 0, 0), c.direction_vector())
    perspective_matrix = glm.perspectiveFovZO(math.radians(90), 2, 2, 1, 10.0)

    po = glm.vec3(5, 0, 0)
    p1 = glm.vec3(5, -0.1, 0)
    p2 = glm.vec3(5, 0.1, 0)
    p3 = glm.vec3(5, 0, -0.1)
    p4 = glm.vec3(5, 0, 0.1)

    return c, perspective_matrix, po, p1, p2, p3, p4

if __name__ == "__main__":
    unittest.main()
