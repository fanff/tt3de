import math
import random
import unittest
import glm
from rtt3de import GeometryBufferPy
from rtt3de import AbigDrawing
from rtt3de import MaterialBufferPy
from rtt3de import TextureBufferPy
from rtt3de import VertexBufferPy, TransformPackPy
from rtt3de import PrimitiveBufferPy

from tests.tt3de.test_utils import (
    assertLine3DPrimitiveKeyEqual,
    assertPointPrimitiveAlmostEqual,
    assertTriangle3DPrimitiveKeyEqual,
    perspective_divide,
)
from tt3de.asset_fastloader import fast_load
from tt3de.glm_camera import GLMCamera
from tt3de.richtexture import ImageTexture

from rtt3de import raster_all_py, build_primitives_py, apply_material_py


class Test_Stages(unittest.TestCase):
    def test_simple_fullrun(self):
        transform_pack = TransformPackPy(64)
        texture_buffer = TextureBufferPy(12)
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        data = img.chained_data()
        texture_buffer.add_texture(img.image_width, img.image_height, data, True, True)
        self.assertEqual(texture_buffer.size(), 1)

        # create some materials
        material_buffer = MaterialBufferPy()
        self.assertEqual(material_buffer.add_textured(0, 1), 0)
        self.assertEqual(material_buffer.count(), 1)
        self.assertEqual(
            material_buffer.add_static((255, 90, 90, 255), (5, 10, 20, 255), 0), 1
        )
        self.assertEqual(material_buffer.count(), 2)

        # create a drawing buffer
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)

        # create a geometry buffer to hold the initial elemnts
        vertex_buffer = VertexBufferPy()

        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.0, 1.0), 0)
        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.5, 1.0), 1)
        self.assertEqual(vertex_buffer.add_vertex(0.5, 0.5, 1.0), 2)

        geometry_buffer = GeometryBufferPy(32)
        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=1
        )  ## this is the geomid default and MUST be the background.

        node_id = 3
        material_id = 1
        geometry_buffer.add_polygon_3d(0, 1, node_id, material_id, 0)

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_pack,
            drawing_buffer,
            primitive_buffer,
        )
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, vertex_buffer, drawing_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 1)
        apply_material_py(
            material_buffer,
            texture_buffer,
            vertex_buffer,
            primitive_buffer,
            drawing_buffer,
        )


class Test_PrimitivBuilding(unittest.TestCase):

    def test_empty_build(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)
        vertex_buffer = VertexBufferPy()
        geometry_buffer = GeometryBufferPy(256)

        transform_pack = TransformPackPy(64)
        self.assertEqual(geometry_buffer.geometry_count(), 0)

        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_pack,
            drawing_buffer,
            primitive_buffer,
        )
        self.assertEqual(primitive_buffer.primitive_count(), 0)

    def test_one_default(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)
        vertex_buffer = VertexBufferPy()
        geometry_buffer = GeometryBufferPy(256)
        transform_pack = TransformPackPy(64)

        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  ## this is the geomid default and MUST be the background.
        self.assertEqual(geometry_buffer.geometry_count(), 1)

        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_pack,
            drawing_buffer,
            primitive_buffer,
        )
        self.assertEqual(primitive_buffer.primitive_count(), 0)

    def test_one_line3D_inside_frustrum(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)

        transform_pack = TransformPackPy(64)
        vertex_buffer = VertexBufferPy()
        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.0, 0.0), 0)
        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.5, 3.0), 1)

        geometry_buffer = GeometryBufferPy(256)
        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  ## this is the geomid default and MUST be the background.

        # now add the line
        node_id = transform_pack.add_node_transform(glm.mat4(1.0))
        material_id = 1
        self.assertEqual(geometry_buffer.add_line3d(0, node_id, material_id, 0), 1)

        # make a glm camera
        camera = GLMCamera(glm.vec3(0, 0, -5))
        camera.set_yaw_pitch(0, 0)
        transform_pack.set_projection_matrix(
            glm.perspectiveFovLH_ZO(glm.radians(90), 512, 512, 1.0, 10.0)
        )
        transform_pack.set_view_matrix_3d(camera.view_matrix_3D())

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_pack,
            drawing_buffer,
            primitive_buffer,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)
        prim0 = primitive_buffer.get_primitive(0)
        assertLine3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": node_id,
                "material_id": material_id,
            },
        )

        self.assertEqual(prim0["pa"]["row"], 256)
        self.assertEqual(prim0["pa"]["col"], 256)

        # self.assertEqual(prim0["pb"]["row"], ~270) # pb is a bit shifted to the bottom because it has y positive
        self.assertEqual(prim0["pb"]["col"], 256)

        self.assertGreater(
            prim0["pb"]["depth"], prim0["pa"]["depth"]
        )  # pb is after pa; clearly

    def test_one_line3D_cutting_backplane(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)

        transform_pack = TransformPackPy(64)
        vertex_buffer = VertexBufferPy()
        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.0, 0.0), 0)

        # setup a point away from the camera; controlling clipping
        self.assertEqual(
            vertex_buffer.add_vertex(0.0, 0.5, 100.0), 1
        )  # too far away from the back of the frustrum plane; will be clipped.

        geometry_buffer = GeometryBufferPy(256)
        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  ## this is the geomid default and MUST be the background.

        # now add the line
        node_id = transform_pack.add_node_transform(glm.mat4(1.0))
        material_id = 1
        self.assertEqual(geometry_buffer.add_line3d(0, node_id, material_id, 0), 1)

        # make a glm camera
        camera = GLMCamera(glm.vec3(0, 0, -5))
        camera.set_yaw_pitch(0, 0)
        transform_pack.set_projection_matrix(
            glm.perspectiveFovLH_ZO(glm.radians(90), 512, 512, 1.0, 10.0)
        )
        transform_pack.set_view_matrix_3d(camera.view_matrix_3D())

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_pack,
            drawing_buffer,
            primitive_buffer,
        )

        self.assertEqual(primitive_buffer.primitive_count(), 1)
        prim0 = primitive_buffer.get_primitive(0)
        assertLine3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": node_id,
                "material_id": material_id,
            },
        )

        self.assertEqual(prim0["pa"]["row"], 256)
        self.assertEqual(prim0["pa"]["col"], 256)

        # self.assertEqual(prim0["pb"]["row"], ~270) # pb is a bit shifted to the bottom because it has y positive
        self.assertEqual(prim0["pb"]["col"], 256)

        self.assertGreater(
            prim0["pb"]["depth"], prim0["pa"]["depth"]
        )  # pb is after pa; clearly
        self.assertAlmostEqual(
            prim0["pb"]["depth"], 1.0
        )  # pb is the clipped point. at the back of the frustum

    def test_simple_one_triangle(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)

        transform_pack = TransformPackPy(64)
        vertex_buffer = VertexBufferPy()
        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.0, 0.5), 0)
        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.5, 0.5), 1)
        self.assertEqual(vertex_buffer.add_vertex(0.5, 0.5, 0.5), 2)
        self.assertEqual(vertex_buffer.add_vertex(0.5, 0.0, 0.5), 3)

        # add some uv coordinates 0 , 1 for nothing
        vertex_buffer.add_uv(glm.vec2(0.0, 0.0), glm.vec2(0.0, 0.0), glm.vec2(0.0, 0.0))
        vertex_buffer.add_uv(glm.vec2(0.0, 0.0), glm.vec2(0.0, 0.0), glm.vec2(0.0, 0.0))
        # this one is used
        vertex_buffer.add_uv(glm.vec2(0.0, 0.0), glm.vec2(0.0, 1.0), glm.vec2(1.0, 1.0))

        geometry_buffer = GeometryBufferPy(256)
        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  ## this is the geomid default and MUST be the background.

        node_id = 2
        material_id = 1
        uv_index = 2
        self.assertEqual(
            geometry_buffer.add_polygon_3d(0, 1, node_id, material_id, uv_index), 1
        )

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_pack,
            drawing_buffer,
            primitive_buffer,
        )

        prim0 = primitive_buffer.get_primitive(0)

        self.assertEqual(primitive_buffer.primitive_count(), 1)
        assertTriangle3DPrimitiveKeyEqual(
            prim0,
            {
                "_type": "triangle",
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": node_id,
                "material_id": material_id,
            },
        )

    def test_simple_two_triangle(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)

        transform_pack = TransformPackPy(64)
        vertex_buffer = VertexBufferPy()
        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.0, 1.0), 0)
        self.assertEqual(vertex_buffer.add_vertex(0.0, 1.0, 1.0), 1)
        self.assertEqual(vertex_buffer.add_vertex(1.0, 1.0, 1.0), 2)
        self.assertEqual(vertex_buffer.add_vertex(1.0, 0.0, 1.0), 3)

        # add some uv coordinates 0 , 1 for nothing
        vertex_buffer.add_uv(glm.vec2(0.0, 0.0), glm.vec2(0.0, 0.0), glm.vec2(0.0, 0.0))
        vertex_buffer.add_uv(glm.vec2(0.0, 0.0), glm.vec2(0.0, 0.0), glm.vec2(0.0, 0.0))

        # this one is used by the first triangles
        vertex_buffer.add_uv(glm.vec2(0.0, 0.0), glm.vec2(0.0, 1.0), glm.vec2(1.0, 1.0))
        # this one is used by the second triangles
        vertex_buffer.add_uv(glm.vec2(0.0, 0.0), glm.vec2(1.0, 1.0), glm.vec2(1.0, 0.0))

        geometry_buffer = GeometryBufferPy(256)
        self.assertEqual(geometry_buffer.geometry_count(), 0)

        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  ## this is the geomid default and MUST be the background.

        node_id = 3
        material_id = 2
        # adding two triangles ; with uv ccorrdinate 2
        self.assertEqual(
            geometry_buffer.add_polygon_fan_3d(0, 2, node_id, material_id, 2), 1
        )

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_pack,
            drawing_buffer,
            primitive_buffer,
        )
        # the two triangles gets out
        self.assertEqual(primitive_buffer.primitive_count(), 2)

        # the first triangles
        prim0 = primitive_buffer.get_primitive(0)

        assertTriangle3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "_type": "triangle",
                "node_id": node_id,
                "material_id": material_id,
            },
        )

        prim1 = primitive_buffer.get_primitive(1)

        assertTriangle3DPrimitiveKeyEqual(
            prim1,
            {
                "_type": "triangle",
                "primitive_id": 1,
                "geometry_id": 1,
                "node_id": node_id,
                "material_id": material_id,
            },
        )

    def test_one_point_inside_raw_config(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)

        transform_pack = TransformPackPy(64)
        vertex_buffer = VertexBufferPy()
        self.assertEqual(vertex_buffer.add_vertex(0.0, 0.0, 1.0), 0)
        self.assertEqual(vertex_buffer.add_vertex(0.0, 1.0, 1.0), 1)
        self.assertEqual(vertex_buffer.add_vertex(1.0, 1.0, 1.0), 2)
        self.assertEqual(vertex_buffer.add_vertex(1.0, 0.0, 1.0), 3)

        geometry_buffer = GeometryBufferPy(256)
        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  ## this is the geomid default and MUST be the background.

        node_id = 3
        material_id = 2
        self.assertEqual(
            geometry_buffer.add_point(
                0,
                2,
                node_id,
                material_id,
            ),
            1,
        )

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_pack,
            drawing_buffer,
            primitive_buffer,
        )
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        prim0 = primitive_buffer.get_primitive(0)

        self.assertEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": node_id,
                "material_id": material_id,
                "row": 256,
                "col": 256,
                "depth": 1.0,
            },
        )

    def test_points_with_camera_left_right(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)
        transform_buffer = TransformPackPy(64)
        primitive_buffer = PrimitiveBufferPy(256)
        vertex_buffer = VertexBufferPy()
        geometry_buffer = GeometryBufferPy(256)
        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  ## this is the geomid default and MUST be the background.

        # camera is randomly placed and pointed
        camera_pos = glm.vec3(
            random.randint(-100, 100),
            random.randint(-100, 100),
            random.randint(-100, 100),
        )
        camera = GLMCamera(camera_pos, fov_radians=math.radians(50))
        yaw = math.radians(random.randint(-100, 100))
        pitch = math.radians(random.randint(-100, 100))
        camera.set_yaw_pitch(yaw, pitch)

        transform_buffer.set_projection_matrix(camera.perspective_matrix)
        transform_buffer.set_view_matrix_3d(camera.view_matrix_3D())
        node_id = transform_buffer.add_node_transform(glm.mat4(1.0))

        point_inside_frustrum = camera_pos + (camera.direction_vector() * 6)

        # adding one point in front of the camera inside the frustum
        vertices = [
            point_inside_frustrum,
            point_inside_frustrum + (camera.right_vector() * (-0.3)),
            point_inside_frustrum + (camera.right_vector() * (-0.1)),
            point_inside_frustrum + (camera.right_vector() * (0.1)),
            point_inside_frustrum + (camera.right_vector() * (0.3)),  #
        ]
        for pidx, p3d in enumerate(vertices):
            self.assertEqual(vertex_buffer.add_vertex(p3d.x, p3d.y, p3d.z), pidx)
            geometry_buffer.add_point(pidx, 0, node_id=node_id, material_id=23)

        self.assertEqual(geometry_buffer.geometry_count(), len(vertices) + 1)

        vertex_buffer.apply_mvp(
            transform_buffer, node_id=node_id, start=0, end=len(vertices)
        )

        # extract first 4 points
        pa = glm.vec4(vertex_buffer.get_clip_space_vertex(0))
        pb = glm.vec4(vertex_buffer.get_clip_space_vertex(1))
        pc = glm.vec4(vertex_buffer.get_clip_space_vertex(2))
        pd = glm.vec4(vertex_buffer.get_clip_space_vertex(3))

        for p in [pa, pb, pc, pd]:
            p_ndc = perspective_divide(p)
            self.assertGreaterEqual(p_ndc.x, -1.0)
            self.assertLessEqual(p_ndc.x, 1.0)
            self.assertAlmostEqual(p_ndc.y, 0.0, 4)
            self.assertGreaterEqual(p_ndc.z, 0.01)
            self.assertLessEqual(p_ndc.z, 1.0)

        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_buffer,
            drawing_buffer,
            primitive_buffer,
        )
        self.assertEqual(primitive_buffer.primitive_count(), len(vertices))

        prim0 = primitive_buffer.get_primitive(0)

        assertPointPrimitiveAlmostEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": node_id,
                "material_id": 23,
                "row": 256,
                "col": 256,
                "depth": 0.8417510,
            },
        )

        prim1 = primitive_buffer.get_primitive(1)
        assertPointPrimitiveAlmostEqual(
            prim1,
            {
                "primitive_id": 1,
                "geometry_id": 2,
                "node_id": node_id,
                "material_id": 23,
                "row": 256,
                "col": 233,
                "depth": 0.8417510,
            },
        )

        prim2 = primitive_buffer.get_primitive(2)

        assertPointPrimitiveAlmostEqual(
            prim2,
            {
                "primitive_id": 2,
                "geometry_id": 3,
                "node_id": node_id,
                "material_id": 23,
                "row": 256,
                "col": 248,
                "depth": 0.8417510,
            },
        )

        ##prim3 = primitive_buffer.get_primitive(3)
        ##assertPointPrimitiveAlmostEqual(prim3,{
        ##    "primitive_id":3,
        ##    "geometry_id":4,
        ##    "node_id":node_id,
        ##    "material_id":23,
        ##    'row': 256,
        ##    'col': 259,
        ##    'depth': 0.8417510
        ##})
        ##prim4 = primitive_buffer.get_primitive(4)
        ##assertPointPrimitiveAlmostEqual(prim4,{
        ##    "primitive_id":4,
        ##    "geometry_id":5,
        ##    "node_id":node_id,
        ##    "material_id":23,
        ##    'row': 256,
        ##    'col': 266,
        ##    'depth': 0.8417510
        ##})

    def test_points_with_camera_top_down(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)
        transform_buffer = TransformPackPy(64)
        primitive_buffer = PrimitiveBufferPy(256)
        vertex_buffer = VertexBufferPy()
        geometry_buffer = GeometryBufferPy(256)
        geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  ## this is the geomid default and MUST be the background.

        # camera is randomly placed and pointed
        camera_pos = glm.vec3(
            random.randint(-100, 100),
            random.randint(-100, 100),
            random.randint(-100, 100),
        )
        camera = GLMCamera(camera_pos, fov_radians=math.radians(50))
        yaw = math.radians(random.randint(-100, 100))
        pitch = math.radians(random.randint(-100, 100))
        camera.set_yaw_pitch(yaw, pitch)

        transform_buffer.set_projection_matrix(camera.perspective_matrix)
        transform_buffer.set_view_matrix_3d(camera.view_matrix_3D())
        node_id = transform_buffer.add_node_transform(glm.mat4(1.0))

        point_inside_frustrum = camera_pos + (camera.direction_vector() * 6)

        # adding one point in front of the camera inside the frustum
        vertices = [
            point_inside_frustrum,
            point_inside_frustrum + (camera.up_vector() * (-0.3)),
            point_inside_frustrum + (camera.up_vector() * (-0.1)),
            point_inside_frustrum + (camera.up_vector() * (0.1)),
            point_inside_frustrum + (camera.up_vector() * (0.3)),  #
        ]

        for pidx, p3d in enumerate(vertices):
            self.assertEqual(vertex_buffer.add_vertex(p3d.x, p3d.y, p3d.z), pidx)
            geometry_buffer.add_point(pidx, 0, node_id=node_id, material_id=23)

        self.assertEqual(geometry_buffer.geometry_count(), len(vertices) + 1)

        vertex_buffer.apply_mvp(
            transform_buffer, node_id=node_id, start=0, end=len(vertices)
        )

        # extract first 4 points
        pa = glm.vec4(vertex_buffer.get_clip_space_vertex(0))
        pb = glm.vec4(vertex_buffer.get_clip_space_vertex(1))
        pc = glm.vec4(vertex_buffer.get_clip_space_vertex(2))
        pd = glm.vec4(vertex_buffer.get_clip_space_vertex(3))

        for p in [pa, pb, pc, pd]:
            p_ndc = perspective_divide(p)
            self.assertAlmostEqual(p_ndc.x, 0.0, 4)
            self.assertGreaterEqual(p_ndc.y, -1.0)
            self.assertLessEqual(p_ndc.y, 1.0)
            self.assertGreaterEqual(p_ndc.z, 0.01)
            self.assertLessEqual(p_ndc.z, 1.0)

        build_primitives_py(
            geometry_buffer,
            vertex_buffer,
            transform_buffer,
            drawing_buffer,
            primitive_buffer,
        )
        self.assertEqual(primitive_buffer.primitive_count(), len(vertices))

        prim0 = primitive_buffer.get_primitive(0)

        assertPointPrimitiveAlmostEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": node_id,
                "material_id": 23,
                "row": 256,
                "col": 256,
                "depth": 0.84175,
            },
        )

        prim1 = primitive_buffer.get_primitive(1)
        assertPointPrimitiveAlmostEqual(
            prim1,
            {
                "primitive_id": 1,
                "geometry_id": 2,
                "node_id": node_id,
                "material_id": 23,
                "row": 269,
                "col": 256,
                "depth": 0.84175,
            },
        )

        # prim2 = primitive_buffer.get_primitive(2)
        # assertPointPrimitiveAlmostEqual(prim2,{
        #     "primitive_id":2,
        #     "geometry_id":3,
        #     "node_id":node_id,
        #     "material_id":23,
        #     'row': 252,
        #     'col': 256,
        #     'depth': 0.8417510
        # })
        # prim3 = primitive_buffer.get_primitive(3)
        # assertPointPrimitiveAlmostEqual(prim3,{
        #     "primitive_id":3,
        #     "geometry_id":4,
        #     "node_id":node_id,
        #     "material_id":23,
        #     'row': 260,
        #     'col': 256,
        #     'depth': 0.8417510
        # })

        prim4 = primitive_buffer.get_primitive(4)
        assertPointPrimitiveAlmostEqual(
            prim4,
            {
                "primitive_id": 4,
                "geometry_id": 5,
                "node_id": node_id,
                "material_id": 23,
                "row": 243,
                "col": 256,
                "depth": 0.8417510,
            },
        )


class Test3DLineClippingCases(unittest.TestCase):

    def setUp(self):
        # Setup the environment for the tests
        self.drawing_buffer = AbigDrawing(512, 512)
        self.drawing_buffer.hard_clear(1000)

        self.transform_pack = TransformPackPy(64)
        self.vertex_buffer = VertexBufferPy()
        self.geometry_buffer = GeometryBufferPy(256)
        self.camera = GLMCamera(glm.vec3(0, 0, -5))
        self.primitive_buffer = PrimitiveBufferPy(256)

        # setup camera and transform
        self.camera.set_yaw_pitch(0, 0)
        self.transform_pack.set_projection_matrix(self.camera.perspective_matrix)
        self.transform_pack.set_view_matrix_3d(self.camera.view_matrix_3D())

        self.vertex_buffer.add_vertex(0.0, 0.0, 0.0)
        self.geometry_buffer.add_point(
            0, 0, node_id=0, material_id=0
        )  # this is the geomid default and MUST be the background.
        self.node_id = self.transform_pack.add_node_transform(glm.mat4(1.0))

    def tearDown(self):
        # Cleanup if needed
        pass

    def test_one_line3D_clipping_backplane(self):

        # setup a point away from the camera; controlling clipping
        self.vertex_buffer.add_vertex(
            0.0, 0.5, 100.0
        )  # too far away from the back of the frustrum plane; will be clipped.

        # now add the line
        node_id = 0
        material_id = 1
        self.assertEqual(self.geometry_buffer.add_line3d(0, node_id, material_id, 0), 1)

        self.assertEqual(self.primitive_buffer.primitive_count(), 0)
        build_primitives_py(
            self.geometry_buffer,
            self.vertex_buffer,
            self.transform_pack,
            self.drawing_buffer,
            self.primitive_buffer,
        )
        self.assertEqual(self.primitive_buffer.primitive_count(), 1)

        prim0 = self.primitive_buffer.get_primitive(0)
        assertLine3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": node_id,
                "material_id": material_id,
            },
        )

        self.assertEqual(prim0["pa"]["row"], 256)
        self.assertEqual(prim0["pa"]["col"], 256)
        self.assertEqual(prim0["pb"]["col"], 256)
        self.assertGreater(
            prim0["pb"]["depth"], prim0["pa"]["depth"]
        )  # pb is after pa; clearly
        self.assertAlmostEqual(
            prim0["pb"]["depth"], 1.0
        )  # pb is the clipped point. at the back of the frustum

    def test_one_line3D_clipping_nearplane(self):
        # setup a point near to the camera; controlling clipping
        self.vertex_buffer.add_vertex(
            0.0, 0.5, -4.1
        )  # too close to the near plane; will be clipped.

        # now add the line
        material_id = 1
        self.assertEqual(
            self.geometry_buffer.add_line3d(0, self.node_id, material_id, 0), 1
        )

        self.assertEqual(self.primitive_buffer.primitive_count(), 0)
        build_primitives_py(
            self.geometry_buffer,
            self.vertex_buffer,
            self.transform_pack,
            self.drawing_buffer,
            self.primitive_buffer,
        )
        clippa = self.vertex_buffer.get_clip_space_vertex(0)
        clippb = self.vertex_buffer.get_clip_space_vertex(1)
        self.assertEqual(self.primitive_buffer.primitive_count(), 1)

        prim0 = self.primitive_buffer.get_primitive(0)
        assertLine3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": self.node_id,
                "material_id": material_id,
            },
        )

        self.assertEqual(prim0["pa"]["row"], 256)
        self.assertEqual(prim0["pa"]["col"], 256)
        self.assertLess(prim0["pa"]["depth"], 1.0)  #
        self.assertGreater(prim0["pa"]["col"], 0.0)  #

        self.assertAlmostEqual(prim0["pb"]["depth"], 0.0)

    def test_one_line3D_clipping_leftplane(self):
        # setup a point to the left of the camera; controlling clipping
        self.vertex_buffer.add_vertex(
            -100.0, 0.5, 5.0
        )  # too far to the left of the frustum plane; will be clipped.

        # now add the line
        material_id = 1
        self.assertEqual(
            self.geometry_buffer.add_line3d(0, self.node_id, material_id, 0), 1
        )

        self.assertEqual(self.primitive_buffer.primitive_count(), 0)
        build_primitives_py(
            self.geometry_buffer,
            self.vertex_buffer,
            self.transform_pack,
            self.drawing_buffer,
            self.primitive_buffer,
        )

        clippa = self.vertex_buffer.get_clip_space_vertex(0)
        clippb = self.vertex_buffer.get_clip_space_vertex(1)
        self.assertEqual(self.primitive_buffer.primitive_count(), 1)

        prim0 = self.primitive_buffer.get_primitive(0)
        assertLine3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": self.node_id,
                "material_id": material_id,
            },
        )
        clippa = self.vertex_buffer.get_clip_space_vertex(0)
        clippb = self.vertex_buffer.get_clip_space_vertex(1)
        self.assertEqual(prim0["pa"]["row"], 256)
        self.assertEqual(prim0["pa"]["col"], 256)
        self.assertLess(prim0["pa"]["depth"], 1.0)  #
        self.assertGreater(prim0["pa"]["col"], 0.0)  #

        self.assertLessEqual(
            prim0["pb"]["row"], 256
        )  # is a little bellow pa; because y is positive
        self.assertEqual(prim0["pb"]["col"], 0)  # pb is at the left frustum plane

    def test_one_line3D_clipping_rightplane(self):
        # setup a point to the right of the camera; controlling clipping
        self.vertex_buffer.add_vertex(
            100.0, 0.5, 5.0
        )  # too far to the right of the frustum plane; will be clipped.

        # now add the line
        material_id = 1
        self.assertEqual(
            self.geometry_buffer.add_line3d(0, self.node_id, material_id, 0), 1
        )

        self.assertEqual(self.primitive_buffer.primitive_count(), 0)
        build_primitives_py(
            self.geometry_buffer,
            self.vertex_buffer,
            self.transform_pack,
            self.drawing_buffer,
            self.primitive_buffer,
        )
        self.assertEqual(self.primitive_buffer.primitive_count(), 1)

        prim0 = self.primitive_buffer.get_primitive(0)
        assertLine3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": self.node_id,
                "material_id": material_id,
            },
        )

        self.assertEqual(prim0["pa"]["row"], 256)
        self.assertEqual(prim0["pa"]["col"], 256)
        self.assertLess(prim0["pa"]["depth"], 1.0)  #
        self.assertGreater(prim0["pa"]["col"], 0.0)  #

        self.assertEqual(
            prim0["pb"]["col"], 511
        )  # pb is at the Right of the frustum plane
        self.assertLess(prim0["pb"]["depth"], 1.0)  #
        self.assertGreater(prim0["pb"]["col"], 0.0)  #

    def test_one_line3D_clipping_topplane(self):
        # setup a point above the camera; controlling clipping
        self.vertex_buffer.add_vertex(
            0.0, -100.0, 5.0
        )  # too far above the frustum plane; will be clipped.

        # now add the line
        material_id = 1
        self.assertEqual(
            self.geometry_buffer.add_line3d(0, self.node_id, material_id, 0), 1
        )

        self.assertEqual(self.primitive_buffer.primitive_count(), 0)
        build_primitives_py(
            self.geometry_buffer,
            self.vertex_buffer,
            self.transform_pack,
            self.drawing_buffer,
            self.primitive_buffer,
        )
        self.assertEqual(self.primitive_buffer.primitive_count(), 1)

        prim0 = self.primitive_buffer.get_primitive(0)
        assertLine3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": self.node_id,
                "material_id": material_id,
            },
        )

        clippa = self.vertex_buffer.get_clip_space_vertex(0)
        clippb = self.vertex_buffer.get_clip_space_vertex(1)
        self.assertEqual(prim0["pa"]["row"], 256)
        self.assertEqual(prim0["pa"]["col"], 256)
        self.assertLess(prim0["pa"]["depth"], 1.0)  #
        self.assertGreater(prim0["pa"]["col"], 0.0)  #

        self.assertEqual(
            prim0["pb"]["row"], 511
        )  # pb the is at the top of the frustum plane
        self.assertEqual(prim0["pb"]["col"], 256)  # in the middle from left right
        self.assertLess(prim0["pb"]["depth"], 1.0)  #
        self.assertGreater(prim0["pb"]["col"], 0.0)  #

    def test_one_line3D_clipping_bottomplane(self):
        # setup a point below the camera; controlling clipping
        self.vertex_buffer.add_vertex(
            0.0, 100.0, 5.0
        )  # too far below the frustum plane; will be clipped.

        # now add the line
        material_id = 1
        self.assertEqual(
            self.geometry_buffer.add_line3d(0, self.node_id, material_id, 0), 1
        )

        self.assertEqual(self.primitive_buffer.primitive_count(), 0)
        build_primitives_py(
            self.geometry_buffer,
            self.vertex_buffer,
            self.transform_pack,
            self.drawing_buffer,
            self.primitive_buffer,
        )
        self.assertEqual(self.primitive_buffer.primitive_count(), 1)

        prim0 = self.primitive_buffer.get_primitive(0)
        assertLine3DPrimitiveKeyEqual(
            prim0,
            {
                "primitive_id": 0,
                "geometry_id": 1,
                "node_id": self.node_id,
                "material_id": material_id,
            },
        )

        clippa = self.vertex_buffer.get_clip_space_vertex(0)
        clippb = self.vertex_buffer.get_clip_space_vertex(1)
        self.assertEqual(prim0["pa"]["row"], 256)
        self.assertEqual(prim0["pa"]["col"], 256)
        self.assertLess(prim0["pa"]["depth"], 1.0)  #
        self.assertGreater(prim0["pa"]["col"], 0.0)  #

        self.assertEqual(
            prim0["pb"]["row"], 0
        )  # pb the is at the bottom of the frustum plane
        self.assertEqual(prim0["pb"]["col"], 256)  # in the middle from left right
        self.assertLess(prim0["pb"]["depth"], 1.0)  #
        self.assertGreater(prim0["pb"]["col"], 0.0)  #
