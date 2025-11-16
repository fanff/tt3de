# -*- coding: utf-8 -*-
import math
import unittest

from pyglm import glm

from tests.tt3de.test_utils import perspective_divide
from tt3de.prefab3d import Prefab3D
from tt3de.tt3de import GeometryBufferPy
from tt3de.tt3de import DrawingBufferPy
from tt3de.tt3de import MaterialBufferPy
from tt3de.tt3de import TextureBufferPy
from tt3de.tt3de import VertexBufferPy, TransformPackPy
from tt3de.tt3de import PrimitiveBufferPy

from tt3de.tt3de import raster_all_py, build_primitives_py, apply_material_py

import random

from tt3de.glm_camera import GLMCamera
from tt3de.points import Point3D


class TestMVP_Projection(unittest.TestCase):

    def test_simple_central_points(self):

        transform_buffer = TransformPackPy(64)

        transform_buffer.set_projection_matrix(
            glm.perspectiveZO(glm.radians(90), 800 / 600, 1.0, 10.0)
        )
        transform_buffer.set_view_matrix_3d(
            glm.lookAt(glm.vec3(0, 0, 3), glm.vec3(0, 0, -3), glm.vec3(0, 1, 0))
        )

        vertex_buffer = VertexBufferPy(128,128,128)
        self.assertEqual(vertex_buffer.get_3d_len(), 0)

        vertices = [
            Point3D(
                0, 0, 1.0
            ),  # this point is in the middle of the screen, far enough from the camera
            Point3D(
                0.0, 0.0, 1.8
            ),  # this point is closer to the camera ; still in the frustum
            Point3D(
                0.0, 0.0, 2.9
            ),  # this is the point just in front of it the camera; not is the frustum, too close
            Point3D(
                0.0, 0.0, 5.0
            ),  # this is the point far in the back; not in the frustum
        ]
        for pidx, p3d in enumerate(vertices):
            self.assertEqual(vertex_buffer.add_3d_vertex(p3d.x, p3d.y, p3d.z), pidx)
            self.assertEqual(vertex_buffer.get_3d_len(), pidx + 1)

        self.assertEqual(vertex_buffer.get_3d_len(), 4)

        node_id = transform_buffer.add_node_transform(glm.mat4(1.0))

        vertex_buffer.apply_mvp(transform_buffer, node_id=node_id, start=0, end=4)

        pa = glm.vec4(vertex_buffer.get_3d_calculated_tuple(0))
        pb = glm.vec4(vertex_buffer.get_3d_calculated_tuple(1))
        pc = glm.vec4(vertex_buffer.get_3d_calculated_tuple(2))
        pd = glm.vec4(vertex_buffer.get_3d_calculated_tuple(3))

        pa_ndc = perspective_divide(pa)
        pb_ndc = perspective_divide(pb)
        pc_ndc = perspective_divide(pc)
        pd_ndc = perspective_divide(pd)

        # camera is located at 0, 0, 3; looking at 0,0,0
        # so the first vertex should be at 0,0  and z like positive, in front of us
        self.assertEqual(pa_ndc.x, 0.0)
        self.assertEqual(pa_ndc.y, 0.0)
        self.assertGreaterEqual(pa_ndc.z, 0.0)
        self.assertLessEqual(pa_ndc.z, 1.0)

        # second vertext is closer to the camera, so it should be lower in the z
        self.assertEqual(pb_ndc.x, 0.0)
        self.assertEqual(pb_ndc.y, 0.0)
        self.assertGreaterEqual(pb_ndc.z, 0.0)
        self.assertLessEqual(pa_ndc.z, 1.0)
        self.assertLessEqual(pb_ndc.z, pa_ndc.z)

        # third vertex is even closer to the camera, but not inside the frustum
        self.assertEqual(pc_ndc.x, 0.0)
        self.assertEqual(pc_ndc.y, 0.0)
        self.assertLessEqual(pc_ndc.z, 0.0)  # lower than zero
        self.assertLessEqual(pc_ndc.z, pb_ndc.z)

        # last vertex is  behind the camera
        self.assertEqual(pd_ndc.x, 0.0)
        self.assertEqual(pd_ndc.y, 0.0)
        self.assertGreaterEqual(pd_ndc.z, 1.0)  # this is behind the far plane

    def test_simple_central_points_2(self):

        transform_buffer = TransformPackPy(64)

        transform_buffer.set_projection_matrix(
            glm.perspectiveFovLH_ZO(glm.radians(90), 800, 600, 1.0, 10.0)
        )

        camera_pos = glm.vec3(
            random.randint(-100, 100),
            random.randint(-100, 100),
            random.randint(-100, 100),
        )
        yaw = math.radians(random.randint(-100, 100))
        pitch = math.radians(random.randint(-100, 100))

        camera = GLMCamera(camera_pos)
        camera.set_yaw_pitch(yaw, pitch)

        # create a view matrix from yaw and pitch and position
        transform_buffer.set_view_matrix_3d(camera.view_matrix_3D())

        vertex_buffer = VertexBufferPy(128,128,128)
        self.assertEqual(vertex_buffer.get_3d_len(), 0)

        vertices = [
            camera_pos
            + (
                camera.direction_vector() * 3
            )  # this point is in the middle, far enough from the camera; inside frustrum
        ]
        for pidx, p3d in enumerate(vertices):
            self.assertEqual(vertex_buffer.add_3d_vertex(p3d.x, p3d.y, p3d.z), pidx)

        node_id = transform_buffer.add_node_transform(glm.mat4(1.0))

        vertex_buffer.apply_mvp(transform_buffer, node_id=node_id, start=0, end=len(vertices))

        pa = glm.vec4(vertex_buffer.get_3d_calculated_tuple(0))
        pa_ndc = perspective_divide(pa)
        self.assertAlmostEqual(pa_ndc.x, 0.0, 4)
        self.assertAlmostEqual(pa_ndc.y, 0.0, 4)
        self.assertGreaterEqual(pa_ndc.z, 0.0)
        self.assertLessEqual(pa_ndc.z, 1.0)

    def test_simple_one_point_with_glm_camera(self):
        transform_buffer = TransformPackPy(64)

        transform_buffer.set_projection_matrix(
            glm.perspectiveFovLH_ZO(glm.radians(90), 800, 600, 1.0, 10.0)
        )

        camera_pos = glm.vec3(
            random.randint(-100, 100),
            random.randint(-100, 100),
            random.randint(-100, 100),
        )
        camera = GLMCamera(camera_pos)
        yaw = math.radians(random.randint(-360, 360))
        pitch = math.radians(random.randint(-30, 30))
        camera.set_yaw_pitch(yaw, pitch)

        transform_buffer.set_view_matrix_3d(camera.view_matrix_3D())

        vertex_buffer = VertexBufferPy(128,128,128)
        self.assertEqual(vertex_buffer.get_3d_len(), 0)

        # adding one point in front of the camera inside the frustum
        vertices = [
            camera_pos
            + (
                camera.direction_vector() * 3
            )  # this point is in the middle, far enough from the camera; inside frustrum
        ]
        for pidx, p3d in enumerate(vertices):
            self.assertEqual(vertex_buffer.add_3d_vertex(p3d.x, p3d.y, p3d.z), pidx)

        node_id = transform_buffer.add_node_transform(glm.mat4(1.0))

        vertex_buffer.apply_mvp(transform_buffer, node_id=node_id, start=0, end=len(vertices))

        pa = glm.vec4(vertex_buffer.get_3d_calculated_tuple(0))
        pa_ndc = perspective_divide(pa)
        self.assertAlmostEqual(pa_ndc.x, 0.0, 4)
        self.assertAlmostEqual(pa_ndc.y, 0.0, 4)
        self.assertGreaterEqual(pa_ndc.z, 0.0)
        self.assertLessEqual(pa_ndc.z, 1.0)

    def test_many_points_with_glm_camera(self):
        transform_buffer = TransformPackPy(64)

        transform_buffer.set_projection_matrix(
            glm.perspectiveZO(glm.radians(90), 800 / 600, 1.0, 100.0)
        )

        # camera is randomly placed and pointed
        camera_pos = glm.vec3(
            random.randint(-100, 100),
            random.randint(-100, 100),
            random.randint(-100, 100),
        )
        camera = GLMCamera(camera_pos)
        yaw = math.radians(random.randint(-100, 100))
        pitch = math.radians(random.randint(-100, 100))
        camera.set_yaw_pitch(yaw, pitch)

        transform_buffer.set_view_matrix_3d(camera.view_matrix_3D())

        vertex_buffer = VertexBufferPy(128,128,128)
        self.assertEqual(vertex_buffer.get_3d_len(), 0)

        point_inside_frustrum = camera_pos - (camera.direction_vector() * 5)

        # adding one point in front of the camera inside the frustum
        vertices = [
            point_inside_frustrum + (camera.right_vector() * (-0.3)),
            point_inside_frustrum + (camera.right_vector() * (-0.1)),
            point_inside_frustrum + (camera.right_vector() * (0.1)),
            point_inside_frustrum + (camera.right_vector() * (0.3)),  #
        ]
        for pidx, p3d in enumerate(vertices):
            self.assertEqual(vertex_buffer.add_3d_vertex(p3d.x, p3d.y, p3d.z), pidx)

        node_id = transform_buffer.add_node_transform(glm.mat4(1.0))

        vertex_buffer.apply_mvp(transform_buffer, node_id=node_id, start=0, end=4)

        # extract first 4 points
        pa = glm.vec4(vertex_buffer.get_3d_calculated_tuple(0))
        pb = glm.vec4(vertex_buffer.get_3d_calculated_tuple(1))
        pc = glm.vec4(vertex_buffer.get_3d_calculated_tuple(2))
        pd = glm.vec4(vertex_buffer.get_3d_calculated_tuple(3))

        pa_ndc = perspective_divide(pa)
        pb_ndc = perspective_divide(pb)
        pc_ndc = perspective_divide(pc)
        pd_ndc = perspective_divide(pd)

        self.assertGreaterEqual(pa_ndc.x, -1.0)
        self.assertAlmostEqual(pa_ndc.y, 0.0, 4)
        self.assertGreaterEqual(pa_ndc.z, 0.0)
        self.assertLessEqual(pa_ndc.z, 1.0)
