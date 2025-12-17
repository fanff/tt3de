# -*- coding: utf-8 -*-
import math
import random
import unittest

import random

from tt3de.glm_camera import GLMCamera
from tt3de.points import Point3D

from pyglm import glm


def assertAlmostEqualvec3(a: glm.vec3, b: glm.vec3, limit=0.00001):
    assert glm.length(a - b) < limit, f"error equaling : \na = {a}\nb = {b} "


class TestGLMLOOK(unittest.TestCase):
    def test_point_at(self):
        init_pos = glm.vec3(random.random(), random.random(), random.random())

        m = glm.lookAt(init_pos, init_pos + glm.vec3(0, 0, -1), glm.vec3(0, 1, 0))

        astring = [str(glm.row(m, rowidx)) for rowidx in range(4)]

        pass
        print(astring)


class TestPointAt(unittest.TestCase):
    def test_point_at_intheplane(self):
        for i in range(100):
            c = GLMCamera(glm.vec3(0, 0, 0))

            rp = glm.normalize(glm.vec3(random.random(), 0, random.random()))

            c.point_at(rp)
            dv = c.direction_vector()
            uv = c.up_vector()
            rv = c.right_vector()

            self.assertAlmostEqual(glm.length(dv), 1.0, 4)
            assertAlmostEqualvec3(rp, dv)

            # check up vector is always cross value of direction and right
            assertAlmostEqualvec3(uv, glm.normalize(glm.cross(dv, rv)))

    def test_point_random(self):
        for i in range(100):
            c = GLMCamera(glm.vec3(0, 0, 0))

            rp = glm.normalize(
                glm.vec3(random.random(), random.random(), random.random())
            )

            c.point_at(rp)
            dv = c.direction_vector()
            uv = c.up_vector()
            rv = c.right_vector()

            self.assertAlmostEqual(glm.length(dv), 1.0, 4)
            assertAlmostEqualvec3(rp, dv)

            # check up vector is always cross value of direction and right
            assertAlmostEqualvec3(uv, glm.normalize(glm.cross(dv, rv)))


class TestCamera_INIT(unittest.TestCase):
    def test_init_directions(self):
        c = GLMCamera(glm.vec3(0, 0, 0))
        dv = c.direction_vector()
        rv = c.right_vector()
        uv = c.up_vector()
        assertAlmostEqualvec3(dv, glm.vec3(0, 0, 1))
        assertAlmostEqualvec3(rv, glm.vec3(1, 0, 0))
        assertAlmostEqualvec3(uv, glm.vec3(0, 1, 0))

    def test_init_position(self):
        init_pos = glm.vec3(random.random(), random.random(), random.random())
        c = GLMCamera(init_pos)
        assertAlmostEqualvec3(c.position_vector(), init_pos)


class TestCamera_SetYawPitch(unittest.TestCase):
    def test_yaw(self):
        c = GLMCamera(glm.vec3(0, 0, 0))

        # checking status at init
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0, 0, 1))
        assertAlmostEqualvec3(c.right_vector(), glm.vec3(1, 0, 0))
        assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 1, 0))

        # cheching status at NO move
        c.set_yaw_pitch(math.radians(0), 0)
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0, 0, 1))
        assertAlmostEqualvec3(c.right_vector(), glm.vec3(1, 0, 0))
        assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 1, 0))

        # cheching status at 45° rotation
        c.set_yaw_pitch(math.radians(45), 0)
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0.7071, 0, 0.7071))
        assertAlmostEqualvec3(c.right_vector(), glm.vec3(0.7071, 0, -0.7071))
        assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 1, 0))

        # cheching status at 90° move
        c.set_yaw_pitch(math.radians(90), 0)
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(1, 0, 0))
        assertAlmostEqualvec3(c.right_vector(), glm.vec3(0, 0, -1))
        assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 1, 0))

    def test_pitch(self):
        init_pos = glm.vec3(random.random(), random.random(), random.random())
        c = GLMCamera(init_pos)
        # checking status at init
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0, 0, 1))
        assertAlmostEqualvec3(c.right_vector(), glm.vec3(1, 0, 0))
        assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 1, 0))

        # cheching status at NO pitch
        c.set_yaw_pitch(0, math.radians(0))
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0, 0, 1))
        assertAlmostEqualvec3(c.right_vector(), glm.vec3(1, 0, 0))
        assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 1, 0))

        # cheching status at 45° pitch
        c.set_yaw_pitch(0, math.radians(45))
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0, -0.7071, 0.7071))
        assertAlmostEqualvec3(c.right_vector(), glm.vec3(1, 0, 0))
        assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 0.707107, 0.707107))

    def test_combined_yaw_pitch(self):
        init_pos = glm.vec3(random.random(), random.random(), random.random())
        c = GLMCamera(init_pos)
        # checking status at init
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0, 0, 1))

        c.set_yaw_pitch(math.radians(45), 0)
        assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0.7071, 0, 0.7071))

        c.set_yaw_pitch(math.radians(45), math.radians(10))
        assertAlmostEqualvec3(
            c.direction_vector(), glm.vec3(0.696364, -0.173648, 0.696364)
        )


class TestCameraMove(unittest.TestCase):
    def test_camera_position_init(self):
        """Verify camera is right handed."""
        for i in range(100):
            init_pos = glm.vec3(random.random(), random.random(), random.random())
            c = GLMCamera(init_pos)
            # c.point_at(init_pos+glm.vec3(0, 0, 1))

            assertAlmostEqualvec3(c.position_vector(), init_pos)

    def test_camera_move(self):
        """Verify camera is right handed."""
        for i in range(100):
            init_pos = glm.vec3(random.random(), random.random(), random.random())
            c = GLMCamera(init_pos)
            assertAlmostEqualvec3(c.position_vector(), init_pos)
            c.move_forward(1)
            assertAlmostEqualvec3(c.position_vector(), init_pos + c.direction_vector())


class TestCameraRotate(unittest.TestCase):
    def test_camera_rotate_0(self):
        """Verify camera is right handed."""
        for i in range(100):
            init_pos = glm.vec3(random.random(), random.random(), random.random())
            c = GLMCamera(init_pos)

            assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0, 0, 1))
            assertAlmostEqualvec3(c.right_vector(), glm.vec3(1, 0, 0))
            assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 1, 0))

            c.rotate_left_right(math.radians(0))

            assertAlmostEqualvec3(c.direction_vector(), glm.vec3(0, 0, 1))
            assertAlmostEqualvec3(c.right_vector(), glm.vec3(1, 0, 0))
            assertAlmostEqualvec3(c.up_vector(), glm.vec3(0, 1, 0))


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
