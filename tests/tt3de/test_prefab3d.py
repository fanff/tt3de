# -*- coding: utf-8 -*-
"""Unit tests for ``Prefab3D`` factory methods."""

import math
import unittest

from tt3de.prefab3d import Prefab3D


class TestLatLongUVSphere(unittest.TestCase):
    def test_default_radius_is_one(self):
        sphere = Prefab3D.latlong_uv_sphere()
        for v in sphere.vertex_list:
            dist = math.sqrt(v.x**2 + v.y**2 + v.z**2)
            self.assertAlmostEqual(dist, 1.0, places=6)

    def test_custom_radius(self):
        sphere = Prefab3D.latlong_uv_sphere(radius=2.5, stacks=3, slices=5)
        for v in sphere.vertex_list:
            dist = math.sqrt(v.x**2 + v.y**2 + v.z**2)
            self.assertAlmostEqual(dist, 2.5, places=6)

    def test_vertex_count(self):
        sphere = Prefab3D.latlong_uv_sphere(stacks=4, slices=10)
        expected = (4 + 1) * (10 + 1)
        self.assertEqual(len(sphere.vertex_list), expected)

    def test_triangle_count(self):
        sphere = Prefab3D.latlong_uv_sphere(stacks=4, slices=10)
        expected = 2 * 4 * 10
        self.assertEqual(len(sphere.triangles), expected)

    def test_uvmap_matches_triangles(self):
        sphere = Prefab3D.latlong_uv_sphere(stacks=3, slices=6)
        self.assertEqual(len(sphere.uvmap), len(sphere.triangles))

    def test_poles_are_single_points(self):
        """Top and bottom rings should degenerate to single points at ±Y."""
        sphere = Prefab3D.latlong_uv_sphere(radius=1.0, stacks=4, slices=8)
        verts = sphere.vertex_list
        slices_plus_one = 8 + 1
        # Top ring (stack 0): all vertices should be at (0, radius, 0)
        top_ring = verts[:slices_plus_one]
        for v in top_ring:
            self.assertAlmostEqual(v.x, 0.0, places=10)
            self.assertAlmostEqual(v.y, 1.0, places=10)
            self.assertAlmostEqual(v.z, 0.0, places=10)
        # Bottom ring (last stack): all vertices should be at (0, -radius, 0)
        bottom_ring = verts[-slices_plus_one:]
        for v in bottom_ring:
            self.assertAlmostEqual(v.x, 0.0, places=10)
            self.assertAlmostEqual(v.y, -1.0, places=10)
            self.assertAlmostEqual(v.z, 0.0, places=10)

    def test_minimal_stacks_and_slices(self):
        sphere = Prefab3D.latlong_uv_sphere(stacks=1, slices=3)
        self.assertEqual(len(sphere.vertex_list), (1 + 1) * (3 + 1))
        self.assertEqual(len(sphere.triangles), 2 * 1 * 3)

    def test_stacks_too_low_raises(self):
        with self.assertRaises(ValueError):
            Prefab3D.latlong_uv_sphere(stacks=0, slices=3)

    def test_slices_too_low_raises(self):
        with self.assertRaises(ValueError):
            Prefab3D.latlong_uv_sphere(stacks=1, slices=2)

    def test_uv_range(self):
        """All UV coordinates should be in [0, 1]."""
        sphere = Prefab3D.latlong_uv_sphere(stacks=5, slices=12)
        for uva, uvb, uvc in sphere.uvmap:
            for uv in (uva, uvb, uvc):
                self.assertGreaterEqual(uv.x, 0.0)
                self.assertLessEqual(uv.x, 1.0)
                self.assertGreaterEqual(uv.y, 0.0)
                self.assertLessEqual(uv.y, 1.0)

    def test_triangle_indices_in_range(self):
        sphere = Prefab3D.latlong_uv_sphere(stacks=4, slices=10)
        n_verts = len(sphere.vertex_list)
        for a, b, c in sphere.triangles:
            self.assertLess(a, n_verts)
            self.assertLess(b, n_verts)
            self.assertLess(c, n_verts)
            self.assertGreaterEqual(a, 0)
            self.assertGreaterEqual(b, 0)
            self.assertGreaterEqual(c, 0)


if __name__ == "__main__":
    unittest.main()
