import math
from typing import List
import unittest

import glm

from tt3de.glm.pyglmtexture import barycentric_coordinates
from tt3de.glm.triangle_clipping import (
    PLANE_BOTTOM,
    PLANE_FAR,
    PLANE_LEFT,
    PLANE_NEAR,
    PLANE_RIGHT,
    PLANE_TOP,
    clip_space_reject_test,
    clipping_space_planes,
    clipping_space_planes_NO,
    inside_planes,
    is_front_facing,
)
from tt3de.glm.triangle_clipping import (
    calculate_normal,
    clip_polygon_against_plane,
    clip_triangle_in_planes,
    extract_planes,
    inside,
)


class Test_ClippingTriangleZ(unittest.TestCase):

    def test_triangle_no_clipping_z(self):

        near_plane = 0.1

        # standart view port
        viewport = glm.vec4(0, 0, 1, 1.0)
        # standart perspective with near and far plane
        p = glm.perspectiveFovZO(math.radians(90), 400, 400, near_plane, 100.0)

        m = glm.mat4(1.0)

        v1 = glm.vec4(2, -2, -10.1, 1.0)
        v2 = glm.vec4(-2, -2, -10.1, 1.0)
        v3 = glm.vec4(0.0, -2.0, -8, 1.0)
        nv = calculate_normal([v1, v2, v3])

        planes = extract_planes(p)

        acliped_apoly = clip_polygon_against_plane(planes[PLANE_NEAR], [v1, v2, v3])
        self.assertEqual(len(acliped_apoly), 3)

    def test_triangle_with_clipping_on_z(self):

        near_plane = 0.1
        # standart perspective with near and far plane
        p = glm.perspectiveFovZO(math.radians(90), 400, 400, near_plane, 100.0)

        m = glm.mat4(1.0)

        v1 = glm.vec4(2, -2, -10.1, 1.0)
        v2 = glm.vec4(-2, -2, 10.1, 1.0)
        v3 = glm.vec4(0.0, -2.0, -8, 1.0)
        nv = calculate_normal([v1, v2, v3])

        planes = extract_planes(p)
        acliped_apoly = clip_polygon_against_plane(planes[PLANE_NEAR], [v1, v2, v3])
        self.assertEqual(len(acliped_apoly), 4)


class Test_ExtractPlane(unittest.TestCase):

    def test_triangle_no_clipping_z(self):

        # Generate a perspective projection matrix
        fov = glm.radians(90.0)
        aspect_ratio = 16.0 / 9.0
        near = 0.1
        far = 100.0

        projection_matrix = glm.perspectiveZO(fov, aspect_ratio, near, far)

        # Extract the planes
        planes = extract_planes(projection_matrix)

        # Print the planes for verification
        def print_plane_equation(plane):
            normal = glm.vec3(plane.x, plane.y, plane.z)
            distance = plane.w
            print(f"Normal: {normal}, Distance: {distance}")

        for i, plane in enumerate(planes):
            print(f"Plane {i}: {plane}")

        self.assertEqual(len(planes), 6)


class Test_inside_planes(unittest.TestCase):
    def test_unit_cube_in_zo_coordinate(self):

        clipping_space_planes_list = clipping_space_planes()

        apoint_inside_a_clipping_space = glm.vec4(0.5, 0.5, 0.2, 1.0)

        res = inside_planes(clipping_space_planes_list, apoint_inside_a_clipping_space)

        self.assertTrue(all(res))
        import random

        # testing bounds inside
        for i in range(1000):
            xvalue = random.uniform(-1, 1)
            yvalue = random.uniform(-1, 1)
            zvalue = random.uniform(0, 1)

            apoint_inside_a_clipping_space = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            res = inside_planes(
                clipping_space_planes_list, apoint_inside_a_clipping_space
            )

            self.assertTrue(all(res))

        # testing bounds outside X+
        for i in range(1000):
            xvalue = random.uniform(1.01, 10000)
            yvalue = random.uniform(-0.99, 0.99)
            zvalue = random.uniform(0.01, 0.99)

            apoint_inside_a_clipping_space = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(
                clipping_space_planes_list, apoint_inside_a_clipping_space
            )

            self.assertTrue(results[PLANE_FAR])
            self.assertTrue(results[PLANE_TOP])
            self.assertTrue(results[PLANE_NEAR])
            self.assertTrue(results[PLANE_LEFT])
            self.assertFalse(results[PLANE_RIGHT])  # outside here
            self.assertTrue(results[PLANE_BOTTOM])

        # testing bounds outside X-
        for i in range(1000):
            xvalue = random.uniform(-10000, -1.01)
            yvalue = random.uniform(-0.99, 0.99)
            zvalue = random.uniform(0.01, 0.99)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertTrue(results[PLANE_FAR])
            self.assertTrue(results[PLANE_TOP])
            self.assertTrue(results[PLANE_NEAR])
            self.assertFalse(results[PLANE_LEFT])  # outside here
            self.assertTrue(results[PLANE_RIGHT])
            self.assertTrue(results[PLANE_BOTTOM])

        # testing bounds outside Y-
        for i in range(1000):
            xvalue = random.uniform(-0.99, 0.99)
            yvalue = random.uniform(-10000, -1.01)
            zvalue = random.uniform(0.01, 0.99)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertTrue(results[PLANE_FAR])
            self.assertTrue(results[PLANE_TOP])
            self.assertTrue(results[PLANE_NEAR])
            self.assertTrue(results[PLANE_LEFT])
            self.assertTrue(results[PLANE_RIGHT])
            self.assertFalse(results[PLANE_BOTTOM])  # outside here

        # testing bounds outside Y+
        for i in range(1000):
            xvalue = random.uniform(-0.99, 0.99)
            yvalue = random.uniform(1.01, 100000)
            zvalue = random.uniform(0.01, 0.99)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertTrue(results[PLANE_FAR])
            self.assertFalse(results[PLANE_TOP])  # outside here
            self.assertTrue(results[PLANE_NEAR])
            self.assertTrue(results[PLANE_LEFT])
            self.assertTrue(results[PLANE_RIGHT])
            self.assertTrue(results[PLANE_BOTTOM])

        # testing bounds outside Z-
        for i in range(1000):
            xvalue = random.uniform(-0.99, 0.99)
            yvalue = random.uniform(-0.99, 0.99)
            zvalue = random.uniform(-10000, -0.01)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertTrue(results[PLANE_FAR])
            self.assertTrue(results[PLANE_TOP])
            self.assertFalse(results[PLANE_NEAR])  # outside here
            self.assertTrue(results[PLANE_LEFT])
            self.assertTrue(results[PLANE_RIGHT])
            self.assertTrue(results[PLANE_BOTTOM])

        # testing bounds outside Z+
        for i in range(1000):
            xvalue = random.uniform(-0.99, 0.99)
            yvalue = random.uniform(-0.99, 0.99)
            zvalue = random.uniform(1.01, 100000)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertFalse(results[PLANE_FAR])  # outside here
            self.assertTrue(results[PLANE_TOP])
            self.assertTrue(results[PLANE_NEAR])
            self.assertTrue(results[PLANE_LEFT])
            self.assertTrue(results[PLANE_RIGHT])
            self.assertTrue(results[PLANE_BOTTOM])


class Test_inside_planes(unittest.TestCase):
    def test_unit_cube_in_NOcoordinate(self):

        clipping_space_planes_list = clipping_space_planes_NO()

        apoint_inside_a_clipping_space = glm.vec4(0.5, 0.5, 0.2, 1.0)

        res = inside_planes(clipping_space_planes_list, apoint_inside_a_clipping_space)

        self.assertTrue(all(res))
        import random

        # testing bounds inside
        for i in range(1000):
            xvalue = random.uniform(-1, 1)
            yvalue = random.uniform(-1, 1)
            zvalue = random.uniform(-1, 1)

            apoint_inside_a_clipping_space = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            res = inside_planes(
                clipping_space_planes_list, apoint_inside_a_clipping_space
            )

            self.assertTrue(all(res))

        # testing bounds outside X+
        for i in range(1000):
            xvalue = random.uniform(1.01, 10)
            yvalue = random.uniform(-0.99, 0.99)
            zvalue = random.uniform(0.01, 0.99)

            apoint_inside_a_clipping_space = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(
                clipping_space_planes_list, apoint_inside_a_clipping_space
            )

            self.assertTrue(results[PLANE_FAR])
            self.assertTrue(results[PLANE_TOP])
            self.assertTrue(results[PLANE_NEAR])
            self.assertTrue(results[PLANE_LEFT])
            self.assertFalse(results[PLANE_RIGHT])  # outside here
            self.assertTrue(results[PLANE_BOTTOM])

        # testing bounds outside X-
        for i in range(1000):
            xvalue = random.uniform(-10, -1.01)
            yvalue = random.uniform(-0.99, 0.99)
            zvalue = random.uniform(0.01, 0.99)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertTrue(results[PLANE_FAR])
            self.assertTrue(results[PLANE_TOP])
            self.assertTrue(results[PLANE_NEAR])
            self.assertFalse(results[PLANE_LEFT])  # outside here
            self.assertTrue(results[PLANE_RIGHT])
            self.assertTrue(results[PLANE_BOTTOM])

        # testing bounds outside Y-
        for i in range(1000):
            xvalue = random.uniform(-0.99, 0.99)
            yvalue = random.uniform(-10, -1.01)
            zvalue = random.uniform(0.01, 0.99)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertTrue(results[PLANE_FAR])
            self.assertTrue(results[PLANE_TOP])
            self.assertTrue(results[PLANE_NEAR])
            self.assertTrue(results[PLANE_LEFT])
            self.assertTrue(results[PLANE_RIGHT])
            self.assertFalse(results[PLANE_BOTTOM])  # outside here

        # testing bounds outside Y+
        for i in range(1000):
            xvalue = random.uniform(-0.99, 0.99)
            yvalue = random.uniform(1.01, 10)
            zvalue = random.uniform(0.01, 0.99)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertTrue(results[PLANE_FAR])
            self.assertFalse(results[PLANE_TOP])  # outside here
            self.assertTrue(results[PLANE_NEAR])
            self.assertTrue(results[PLANE_LEFT])
            self.assertTrue(results[PLANE_RIGHT])
            self.assertTrue(results[PLANE_BOTTOM])

        # testing bounds outside Z-
        for i in range(1000):
            xvalue = random.uniform(-0.99, 0.99)
            yvalue = random.uniform(-0.99, 0.99)
            zvalue = random.uniform(-10, -1.01)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertTrue(results[PLANE_FAR])
            self.assertTrue(results[PLANE_TOP])
            self.assertFalse(results[PLANE_NEAR])  # outside here
            self.assertTrue(results[PLANE_LEFT])
            self.assertTrue(results[PLANE_RIGHT])
            self.assertTrue(results[PLANE_BOTTOM])

        # testing bounds outside Z+
        for i in range(1000):
            xvalue = random.uniform(-0.99, 0.99)
            yvalue = random.uniform(-0.99, 0.99)
            zvalue = random.uniform(1.01, 10)

            apoint_ = glm.vec4(xvalue, yvalue, zvalue, 1.0)

            results = inside_planes(clipping_space_planes_list, apoint_)

            self.assertFalse(results[PLANE_FAR])  # outside here
            self.assertTrue(results[PLANE_TOP])
            self.assertTrue(results[PLANE_NEAR])
            self.assertTrue(results[PLANE_LEFT])
            self.assertTrue(results[PLANE_RIGHT])
            self.assertTrue(results[PLANE_BOTTOM])


class Test_clip_polygon_against_plane(unittest.TestCase):

    def test_some_cliping(self):
        # Generate a perspective projection matrix
        fov = glm.radians(90.0)
        aspect_ratio = 16.0 / 9.0
        near = 1.0
        far = 100.0

        projection_matrix = glm.perspective(fov, aspect_ratio, near, far)

        # Extract the planes
        planes = extract_planes(projection_matrix)

        poly_p1 = glm.vec4(0, 0, -5, 1.0)  # inside
        poly_p2 = glm.vec4(0, 0, -500, 1.0)  # ouside
        poly_p3 = glm.vec4(0, 500, -5, 1.0)  # outsid completely far on y
        apoly = [poly_p1, poly_p2, poly_p3]
        acliped_apoly = clip_polygon_against_plane(planes[PLANE_FAR], apoly)

        self.assertEqual(len(acliped_apoly), 4)

        # self.assertEqual(acliped_apoly[0],poly_p1 )
        # self.assertEqual(acliped_apoly[1],glm.vec4(0,0,-100,1.0) )

    def test_frustrum_cliping(self):

        fov = glm.radians(90.0)
        aspect_ratio = 16.0 / 9.0
        near = 1.0
        far = 100.0

        projection_matrix = glm.perspective(fov, aspect_ratio, near, far)

        # Extract the planes
        planes = extract_planes(projection_matrix)

        poly_p1 = glm.vec4(0, 0, -5, 1.0)  # inside
        poly_p2 = glm.vec4(0, 0, -500, 1.0)  # ouside
        poly_p3 = glm.vec4(0, 500, -5, 1.0)  # outsid completely far on y
        apoly = [poly_p1, poly_p2, poly_p3]
        acliped_apoly = clip_triangle_in_planes(apoly, planes)

        self.assertEqual(len(acliped_apoly), 2)  # two triangles gets out

    def test_frustrum_cliping_extrem_case(self):

        fov = glm.radians(90.0)
        aspect_ratio = 16.0 / 9.0
        near = 0.1
        far = 10.0

        projection_matrix = glm.perspective(fov, aspect_ratio, near, far)

        # Extract the planes
        planes = extract_planes(projection_matrix)

        # lets have a plane with x+y+z = d
        # z = d -x -y
        # pick some far far outreachable x an y and calculate associated z

        def z_plane(x, y, d):
            return d - x - y

        def calc_z(on_this, given_d):
            return glm.vec4(
                on_this.x, on_this.y, z_plane(on_this.x, on_this.y, given_d), on_this.w
            )

        poly_p1 = glm.vec4(-1000, -1000.0, 1.0, 1.0)  #
        poly_p2 = glm.vec4(1000.0, -1000.0, 1.0, 1.0)  #
        poly_p3 = glm.vec4(0.0, 1000.0, 1.0, 1.0)  #

        #  we gonna slide the plane along the z axis, it gonna cut with projections at some point
        count = 50
        for idx in range(count):

            d = ((float(idx) / count) - 0.5) * 50 * 2

            poly_p1 = calc_z(poly_p1, d)  #
            poly_p2 = calc_z(poly_p2, d)  #
            poly_p3 = calc_z(poly_p3, d)  #

            apoly = [poly_p1, poly_p2, poly_p3]
            acliped_apoly = clip_triangle_in_planes(apoly, planes)

            clip_count = len(acliped_apoly)
            # some clip_count can be 0,3,4,5 etc..
            print(f"d: {d}, -> {len(acliped_apoly)}")


class Test_Insidefunction(unittest.TestCase):

    def test_some_insidez(self):

        # Generate a perspective projection matrix
        fov = glm.radians(70.0)
        aspect_ratio = 16.0 / 9.0
        near = 0.1
        far = 100.0

        projection_matrix = glm.perspectiveZO(fov, aspect_ratio, near, far)

        # Extract the planes
        planes = extract_planes((projection_matrix))

        # all points in front (-z are correctly found within)
        for i in range(10):
            a_test_point = glm.vec4(0.0, 0.0, -5 - i * 5, 1.0)

            results = [inside(plane, a_test_point) for plane in planes]

            self.assertTrue(all(results))

        a_test_point = glm.vec4(0.1, 0.1, -110.0, 1.0)
        results = [inside(plane, a_test_point) for plane in planes]
        self.assertFalse(results[PLANE_FAR])  # it is after the far end

        self.assertTrue(results[PLANE_TOP])
        self.assertTrue(results[PLANE_NEAR])
        self.assertTrue(results[PLANE_LEFT])
        self.assertTrue(results[PLANE_RIGHT])
        self.assertTrue(results[PLANE_BOTTOM])

    def test_some_insideY(self):
        fov = glm.radians(70.0)
        aspect_ratio = 16.0 / 9.0
        near = 1.0
        far = 110.0

        projection_matrix = glm.perspectiveZO(fov, aspect_ratio, near, far)

        # Extract the planes
        planes = extract_planes(projection_matrix)

        # all points in front (-z are correctly found within)
        for i in range(10):
            a_test_point = glm.vec4(0.0, i / 10, -5, 1.0)

            results = [inside(plane, a_test_point) for plane in planes]

            self.assertTrue(all(results))

        a_test_point = glm.vec4(0.1, 100, -5.0, 1.0)
        results = [inside(plane, a_test_point) for plane in planes]

        self.assertFalse(results[PLANE_TOP])  # it is over the top

        self.assertTrue(results[PLANE_FAR])
        self.assertTrue(results[PLANE_NEAR])
        self.assertTrue(results[PLANE_LEFT])
        self.assertTrue(results[PLANE_RIGHT])
        self.assertTrue(results[PLANE_BOTTOM])


class Test_Front_back_facing(unittest.TestCase):
    def test_some_cases(self):
        front_facing_triangle = [
            glm.vec4(-0.5, -0.5, 0.0, 1.0),
            glm.vec4(0.5, -0.5, 0.0, 1.0),
            glm.vec4(0.0, 0.5, 0.0, 1.0),
        ]
        self.assertTrue(is_front_facing(front_facing_triangle))

        back_facing_triangle = [
            glm.vec4(0.5, -0.5, 0.0, 1.0),
            glm.vec4(-0.5, -0.5, 0.0, 1.0),
            glm.vec4(0.0, 0.5, 0.0, 1.0),
        ]
        self.assertFalse(is_front_facing(back_facing_triangle))


class Test_Clip_unproject(unittest.TestCase):
    def test_clipping_unprojection(self):
        """testing if it is possible to unproject the vertice back,
        because it is super usefull for the uv mapping stage
        """

        # we take a front facing triangle
        front_facing_triangle = [
            glm.vec4(-0.5, -0.5, 0.1, 1.0),
            glm.vec4(0.5, -0.5, 0.1, 1.0),
            glm.vec4(0.0, 0.5, 0.1, 1.0),
        ]

        # and stuff to make projection tp screen
        fov = glm.radians(70.0)
        aspect_ratio = 16.0 / 9.0
        near = 1
        far = 100.0
        view_matrix = glm.lookAt(
            glm.vec3(0.1, 0.1, 5.1), glm.vec3(-0.2, -0.1, 0.1), glm.vec3(0, 1, 0)
        )
        projection_matrix = glm.perspectiveZO(fov, aspect_ratio, near, far)

        model_matrix = glm.scale(glm.vec3(1, 1, 1.0))
        # Step 1: Vertex Shader
        # put vertices in view_space; in anycase it is usefull.
        view_space_vertices = [
            (view_matrix * model_matrix) * vertex for vertex in front_facing_triangle
        ]

        # then in clip space
        triangle_in_clip_space = [
            projection_matrix * vertex for vertex in view_space_vertices
        ]
        if clip_space_reject_test(triangle_in_clip_space):
            self.assertFalse(True)
        else:
            # then I do the perspective divide
            triangle_in_clip_space_divided = [
                vertex / vertex.w for vertex in triangle_in_clip_space
            ]

            # and now lets clip the triangle
            plane_of_the_clip_space = clipping_space_planes()

            # and now I clip.
            triangles_in_clip_space_divided_and_clipped = clip_triangle_in_planes(
                triangle_in_clip_space_divided, plane_of_the_clip_space
            )

            # points of the first triangle
            p1, p2, p3 = triangles_in_clip_space_divided_and_clipped[0]

            p1_view_space = (
                glm.inverse(projection_matrix * view_matrix * model_matrix) * p1
            )
            p2_view_space = (
                glm.inverse(projection_matrix * view_matrix * model_matrix) * p2
            )
            p3_view_space = (
                glm.inverse(projection_matrix * view_matrix * model_matrix) * p3
            )

            p1_view_space = p1_view_space / p1_view_space.w
            p2_view_space = p2_view_space / p2_view_space.w
            p3_view_space = p3_view_space / p3_view_space.w

            # we can test the revers transformation of the projected point fits well with
            # the original triangle points
            self.assertLessEqual(
                glm_vec3_dist(p1_view_space, front_facing_triangle[0]), 0.001
            )
            self.assertLessEqual(
                glm_vec3_dist(p2_view_space, front_facing_triangle[1]), 0.001
            )
            self.assertLessEqual(
                glm_vec3_dist(p3_view_space, front_facing_triangle[2]), 0.001
            )

            # also testing the barycentric_coordinates
            original_point_1, original_point_2, original_point_3 = front_facing_triangle
            bar_point_p1 = barycentric_coordinates(
                original_point_1, original_point_2, original_point_3, p1_view_space
            )
            bar_point_p2 = barycentric_coordinates(
                original_point_1, original_point_2, original_point_3, p2_view_space
            )
            bar_point_p3 = barycentric_coordinates(
                original_point_1, original_point_2, original_point_3, p3_view_space
            )

            self.assertAlmostEqual(bar_point_p1[0], 1, 3)
            self.assertAlmostEqual(bar_point_p1[1], 0, 3)
            self.assertAlmostEqual(bar_point_p1[2], 0, 3)

            self.assertAlmostEqual(bar_point_p2[0], 0, 3)
            self.assertAlmostEqual(bar_point_p2[1], 1, 3)
            self.assertAlmostEqual(bar_point_p2[2], 0, 3)

            self.assertAlmostEqual(bar_point_p3[0], 0, 3)
            self.assertAlmostEqual(bar_point_p3[1], 0, 3)
            self.assertAlmostEqual(bar_point_p3[2], 1, 3)


def glm_vec3_dist(v1, v2):
    return glm.length(v1 - v2)


class Test_Clip_in_clip_space(unittest.TestCase):

    def test_clipping_output_(self):
        """testing if the output of cliped triangle always lies withing the frustrum"""

        # we take a front facing triangle
        front_facing_triangle = [
            glm.vec4(-0.5, -0.5, 0.1, 1.0),
            glm.vec4(0.5, -0.5, 0.1, 1.0),
            glm.vec4(0.0, 0.5, 0.1, 1.0),
        ]

        # and stuff to make projection tp screen
        fov = glm.radians(70.0)
        aspect_ratio = 16.0 / 9.0
        near = 0.1
        far = 100.0
        view_matrix = glm.lookAt(
            glm.vec3(0, 0, 5), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0)
        )
        projection_matrix = glm.perspectiveZO(fov, aspect_ratio, near, far)

        # I gonna change the shape of the triangle a little bit.
        for scale_x in (0, 100):
            for scale_y in (0, 100):
                scale_x = ((scale_x / 100) - 0.5) * 28
                scale_y = ((scale_y / 100) - 0.5) * 28

                # it is facing front I gonna scale the triangle in the Y coordinate and X coordinate.
                model_matrix = glm.scale(glm.vec3(scale_x, scale_y, 1.0))
                #

                # Step 1: Vertex Shader
                # put vertices in view_space; in anycase it is usefull.
                view_space_vertices = [
                    (view_matrix * model_matrix) * vertex
                    for vertex in front_facing_triangle
                ]

                # then in clip space
                triangle_in_clip_space = [
                    projection_matrix * vertex for vertex in view_space_vertices
                ]
                if clip_space_reject_test(triangle_in_clip_space):
                    self.assertFalse(True)
                else:
                    # then I do the perspective divide
                    triangle_in_clip_space_divided = [
                        vertex / vertex.w for vertex in triangle_in_clip_space
                    ]

                    # and now lets clip the triangle
                    plane_of_the_clip_space = clipping_space_planes()

                    # and now I clip.
                    triangles_in_clip_space_divided_and_clipped = (
                        clip_triangle_in_planes(
                            triangle_in_clip_space_divided, plane_of_the_clip_space
                        )
                    )
                    self.assertGreaterEqual(
                        len(triangles_in_clip_space_divided_and_clipped), 1
                    )
                    for subtriangle in triangles_in_clip_space_divided_and_clipped:
                        for p1 in subtriangle:
                            self.assertGreaterEqual(p1.x, -1)
                            self.assertLessEqual(p1.x, 1)

                            self.assertGreaterEqual(p1.y, -1)
                            self.assertLessEqual(p1.y, 1)

                            self.assertGreaterEqual(p1.z, 0)
                            self.assertLessEqual(p1.z, 1)

                    if len(triangles_in_clip_space_divided_and_clipped) > 3:
                        pass

    def test_some_insidez(self):
        front_facing_triangle = [
            glm.vec4(-0.5, -0.5, 0.0, 1.0),
            glm.vec4(0.5, -0.5, 0.0, 1.0),
            glm.vec4(0.0, 0.5, 0.0, 1.0),
        ]
        self.assertTrue(is_front_facing(front_facing_triangle))

        back_facing_triangle = [
            glm.vec4(0.5, -0.5, 0.0, 1.0),
            glm.vec4(-0.5, -0.5, 0.0, 1.0),
            glm.vec4(0.0, 0.5, 0.0, 1.0),
        ]
        self.assertFalse(is_front_facing(back_facing_triangle))

        # Generate a perspective projection matrix
        fov = glm.radians(70.0)
        aspect_ratio = 16.0 / 9.0
        near = 0.1
        far = 100.0
        model_matrix = glm.mat4(1.0)  # Identity matrix for simplicity
        view_matrix = glm.lookAt(
            glm.vec3(0, 0, 5), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0)
        )
        projection_matrix = glm.perspectiveZO(fov, aspect_ratio, near, far)

        model_matrix = glm.scale(glm.vec3(100.0, 10.0, 1.0))

        vertices_to_use_inthe_calculation = front_facing_triangle

        # Step 1: Vertex Shader
        # put vertices in view_space; in anycase it is usefull.
        view_space_vertices = [
            (view_matrix * model_matrix) * vertex
            for vertex in vertices_to_use_inthe_calculation
        ]

        ## METHOD 1 do the clip in the view space

        # Step 2: clipping, like the "cutting the triangle withing the visible space. "
        # use the planes of the projection
        planes = extract_planes(projection_matrix)
        # and do some cliping, inside the view space coordinates .
        clipped_triangles = clip_triangle_in_planes(view_space_vertices, planes)
        # this shows one triangle, as expected

        print(clipped_triangles)
        # finally, I can project stuff that were clipped inside the frustrum already.
        clipped_triangle_after_projection = [
            projection_matrix * vertex for vertex in clipped_triangles[0]
        ]
        clipped_triangle_after_projection_divided = [
            vertex / vertex.w for vertex in clipped_triangle_after_projection
        ]

        # METHOD 2: dot the clip in the clip space AFTER the /W

        # to compare the previous results, I will use the clipspace coordinates
        # so I first convert from view space to into the clip space using the projection.
        triangle_in_clip_space = [
            projection_matrix * vertex for vertex in view_space_vertices
        ]

        # then I do the perspective divide
        triangle_in_clip_space_divided = [
            vertex / vertex.w for vertex in triangle_in_clip_space
        ]

        # those are the side of a cube, -1,1 on x, -1,1 on y, 0,1 on z, because we used a ZO perspective. Rigth ?
        plane_of_the_clip_space = clipping_space_planes()

        # and now I clip.
        triangles_in_clip_space_divided_and_clipped = clip_triangle_in_planes(
            triangle_in_clip_space_divided, plane_of_the_clip_space
        )

        triangle_in_clip_space_divided_and_clipped = (
            triangles_in_clip_space_divided_and_clipped[0]
        )
        # this shows the sames as "clipped_triangle_after_project_divided"
        print(triangle_in_clip_space_divided_and_clipped)

        # checking it is roughly ok.
        almostEqualVec4(
            clipped_triangle_after_projection_divided[0],
            triangle_in_clip_space_divided_and_clipped[0],
        )
        almostEqualVec4(
            clipped_triangle_after_projection_divided[1],
            triangle_in_clip_space_divided_and_clipped[1],
        )
        almostEqualVec4(
            clipped_triangle_after_projection_divided[2],
            triangle_in_clip_space_divided_and_clipped[2],
        )

        # METHOD 3: do the clip in the clip space BEFORE THE /W
        # DONT WORK! JUST DEAL WITH ZERO DIVISION FOR EVERY TEST

    def test_weirdbug_onthe_side(self):

        def full_transform_method2(
            atriangle,
            arotation_for_the_view=0.0,
            hypothesis_of_is_inside_the_frustum=True,
        ):
            # Generate a perspective projection matrix to look at it
            fov = glm.radians(70.0)
            aspect_ratio = 1.0
            near = 0.3
            far = 100.0

            model_matrix = glm.mat4(1.0)

            view_matrix = glm.rotate(
                arotation_for_the_view, glm.vec3(0, 1, 0)
            ) * glm.lookAt(glm.vec3(0, 0, 5), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))

            projection_matrix = glm.perspective(fov, aspect_ratio, near, far)

            # do go into the view space
            view_space_vertices = [
                (view_matrix * model_matrix) * vertex for vertex in atriangle
            ]

            # go into the clip space; WITHOUT dividing yet.
            triangle_in_clip_space = [
                projection_matrix * vertex for vertex in view_space_vertices
            ]

            # triangles on the strict 90° anle are alike jumping around the clip space.
            # https://www.reddit.com/r/GraphicsProgramming/comments/14uffh2/clipping_a_triangle_inside_clip_space/
            a_clip_space_test = []
            for vertice_in_clip_space in triangle_in_clip_space:
                sometest = [
                    -vertice_in_clip_space.w < vertice_in_clip_space.x,
                    vertice_in_clip_space.x < vertice_in_clip_space.w,
                    -vertice_in_clip_space.w < vertice_in_clip_space.y,
                    vertice_in_clip_space.y < vertice_in_clip_space.w,
                    -vertice_in_clip_space.w < vertice_in_clip_space.z,
                    vertice_in_clip_space.z < vertice_in_clip_space.w,
                ]

                a_clip_space_test.append(sometest)
            clipe_space_rejection = [
                not (a_clip_space_test[0][plane_idx])
                and not (a_clip_space_test[1][plane_idx])
                and not (a_clip_space_test[2][plane_idx])
                for plane_idx in range(6)
            ]
            self.assertEqual(
                any(clipe_space_rejection), not hypothesis_of_is_inside_the_frustum
            )
            # if any of the clip_space_rejection is True, it means that ALL vertices of the triangles are on the outside of this plane.
            if any(clipe_space_rejection):
                return []

            # then I do the perspective divide
            triangle_in_clip_space_divided = [
                vertex / vertex.w for vertex in triangle_in_clip_space
            ]

            # those are the side of a cube, -1,1 on x, -1,1 on y, 0,1 on z, because we used a ZO perspective. Rigth ?
            plane_of_the_clip_space = clipping_space_planes_NO()

            if hypothesis_of_is_inside_the_frustum:
                pass
            else:
                pass
            # and now I clip.
            triangles_in_clip_space_divided_and_clipped = clip_triangle_in_planes(
                triangle_in_clip_space_divided, plane_of_the_clip_space
            )
            return triangles_in_clip_space_divided_and_clipped

        # lets have a triangle is the middle of the scene
        front_facing_triangle = [
            glm.vec4(-0.5, -0.5, 0.0, 1.0),
            glm.vec4(0.5, -0.5, 0.0, 1.0),
            glm.vec4(0.0, 0.5, 0.0, 1.0),
        ]

        for i in range(100):
            import random

            alittle_rot_on_the_camera = math.radians(random.uniform(-10, 10))
            triangles_in_clip_space_divided_and_clipped = full_transform_method2(
                front_facing_triangle,
                alittle_rot_on_the_camera,
                hypothesis_of_is_inside_the_frustum=True,
            )
            # outcome is one triangle.
            triangle_in_clip_space_divided_and_clipped = (
                triangles_in_clip_space_divided_and_clipped[0]
            )
            # this shows the sames as "clipped_triangle_after_project_divided"
            print(triangle_in_clip_space_divided_and_clipped)
            self.assertEqual(len(triangles_in_clip_space_divided_and_clipped), 1)

        import random

        results = []
        for i in range(100):
            alittle_rot_on_the_camera = math.radians(
                random.uniform(80, 100)
            )  # look at the side ~90°
            triangles_in_clip_space_divided_and_clipped = full_transform_method2(
                front_facing_triangle,
                alittle_rot_on_the_camera,
                hypothesis_of_is_inside_the_frustum=False,
            )
            counting = len(triangles_in_clip_space_divided_and_clipped)
            results.append(counting)

            if counting != 0:
                pass
                print("eroror! ")
                triangles_in_clip_space_divided_and_clipped = full_transform_method2(
                    front_facing_triangle,
                    alittle_rot_on_the_camera,
                    hypothesis_of_is_inside_the_frustum=False,
                )

        for r in results:
            self.assertEqual(r, 0)

        for i in range(100):
            alittle_rot_on_the_camera = math.radians(
                random.uniform(-80, -100)
            )  # look at the side  ~ -90°
            triangles_in_clip_space_divided_and_clipped = full_transform_method2(
                front_facing_triangle,
                alittle_rot_on_the_camera,
                hypothesis_of_is_inside_the_frustum=False,
            )
            self.assertEqual(len(triangles_in_clip_space_divided_and_clipped), 0)


def almostEqualVec4(v1, v2, tol=0.01):
    assert glm.length(v1 - v2) < tol
