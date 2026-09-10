# -*- coding: utf-8 -*-
import unittest

from pyglm import glm

from tt3de.tt3de import LightBufferPy


class TestLightBufferPy(unittest.TestCase):
    def test_set_clear_and_count(self):
        buf = LightBufferPy(capacity=8)
        self.assertEqual(buf.capacity, 8)
        self.assertEqual(buf.count(), 0)
        buf.set_ambient(0, color=(0.1, 0.2, 0.3))
        buf.set_directional(2, color=(1.0, 1.0, 1.0), direction=(0.0, 0.0, -2.0))
        self.assertEqual(buf.count(), 3)
        self.assertEqual(buf.light_type(0), 1)
        self.assertEqual(buf.light_type(1), 0)
        self.assertEqual(buf.light_type(2), 2)
        color = buf.light_color(0)
        self.assertAlmostEqual(color.x, 0.1, places=5)
        direction = buf.light_direction(2)
        self.assertAlmostEqual(direction.z, -1.0, places=5)
        buf.clear(2)
        self.assertEqual(buf.count(), 1)

    def test_capacity_errors(self):
        with self.assertRaises(ValueError):
            LightBufferPy(capacity=64)
        buf = LightBufferPy(capacity=2)
        with self.assertRaises(ValueError):
            buf.set_ambient(2, color=(1.0, 0.0, 0.0))

    def test_accepts_glm_vec3(self):
        buf = LightBufferPy()
        buf.set_point(
            0,
            color=glm.vec3(1.0, 0.5, 0.25),
            position=glm.vec3(2.0, 3.0, 4.0),
            attenuation=glm.vec3(1.0, 0.1, 0.01),
        )
        pos = buf.light_position(0)
        self.assertAlmostEqual(pos.y, 3.0, places=5)


if __name__ == "__main__":
    unittest.main()
