import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture


from tt3de.glm.c_texture import Texture2D


from tt3de.glm.material.c_material import apply_pixel_shader
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

from tt3de.glm.primitives.primitives import PrimitivesBuffer


from tt3de.glm.raster.raster import raster_precalc
from tt3de.glm.raster.raster import raster_all


from tt3de.glm.material.c_material import Material
from tt3de.glm.material.c_material import MaterialBuffer

from tt3de.glm.primitives.primitive_builder import build_primitives

from tt3de.glm.geometry.geometry import GeometryBuffer


class Test_Material(unittest.TestCase):
    def test_create(self):
        amaterial = Material()

        print(amaterial)
        # print(amaterial.dostuff())


class Test_MaterialBuffer(unittest.TestCase):
    def test_create(self):

        img: ImageTexture = fast_load("models/test_screen32.bmp")
        atexture = Texture2D(img.image_width, img.image_height)
        atexture.load_from_list(img.img_data)

        mb = MaterialBuffer()

        # mb.add_material(Material())
        settings = {
            "texturemode": 1,
            "albedo_front_r": 1,
            "albedo_front_g": 2,
            "albedo_front_b": 3,
            "albedo_back_r": 4,
            "albedo_back_g": 5,
            "albedo_back_b": 6,
            "glyph_a": 7,
            "glyph_b": 8,
            "texture_id_array": [0] * 8,
        }
        mb.add_material_ele(settings)

        materialretrieved = mb.get_material(0)

        self.assertDictEqual(settings, materialretrieved)

        settings2 = {
            "texturemode": 3,
            "albedo_front_r": 11,
            "albedo_front_g": 12,
            "albedo_front_b": 13,
            "albedo_back_r": 14,
            "albedo_back_g": 15,
            "albedo_back_b": 16,
            "glyph_a": 17,
            "glyph_b": 18,
            "texture_id_array": [0] * 8,
        }
        mb.add_material_ele(settings2)

        materialretrieved = mb.get_material(0)
        self.assertDictEqual(settings, materialretrieved)

        materialretrieved = mb.get_material(1)
        self.assertDictEqual(settings2, materialretrieved)

    def test_create_fullcolored(self):
        mb = MaterialBuffer()

        # mb.add_material(Material())
        settings = {
            "texturemode": 1,
            "albedo_front_r": 1,
            "albedo_front_g": 2,
            "albedo_front_b": 3,
            "albedo_back_r": 4,
            "albedo_back_g": 5,
            "albedo_back_b": 6,
            "glyph_a": 7,
            "glyph_b": 8,
            "texture_id_array": [0] * 8,
        }
        mb.add_material_ele(settings)

        materialretrieved = mb.get_material(0)
        self.assertDictEqual(materialretrieved, settings)


class Test_ApplyMaterialMethod(unittest.TestCase):
    def test_this(self):

        # create some material on one side
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        atexture = Texture2D(img.image_width, img.image_height)
        atexture.load_from_list(img.img_data)

        mat = Material(texturemode=0)
        mat.add_texture(atexture)

        mb = MaterialBuffer()
        mb.add_material(mat)

        mat2 = Material(texturemode=1)
        mb.add_material(
            mat2
        )  # add a second material to check that there is a correct mapping

        # create a drawing buffer on the other side
        drawing_buffer = DrawingBuffer(512, 512)
        drawing_buffer.hard_clear(1000)

        # create a geometry buffer to hold the initial elemnts
        geometry_buffer = GeometryBuffer(32)
        self.assertEqual(geometry_buffer.geometry_count(), 0)

        x, y, z = 0.1, 0.2, 1.0
        uv_array = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        node_id = 100
        material_id = 1
        geometry_buffer.add_point_to_buffer(x, y, z, uv_array, node_id, material_id)

        # create a buffer of primitives
        primitive_buffer = PrimitivesBuffer(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives(geometry_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_precalc(primitive_buffer, drawing_buffer)

        raster_all(primitive_buffer, drawing_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        apply_pixel_shader(primitive_buffer, drawing_buffer, mb, geometry_buffer)

        canvas_list = drawing_buffer.canvas_to_list()
        depth_buffer_list = drawing_buffer.drawbuffer_to_list()

        depthp_pix_0 = depth_buffer_list[0]
        self.assertEqual(depthp_pix_0[0], 1.0)  # depth
        self.assertEqual(depthp_pix_0[1], 1.0)  # weights to vertice 2D
        self.assertEqual(depthp_pix_0[2], 0.0)  # weights
        self.assertEqual(depthp_pix_0[3], 0.0)  # weights

        self.assertEqual(depthp_pix_0[4], 100)  # node id
        self.assertEqual(depthp_pix_0[5], 0)  #
        self.assertEqual(depthp_pix_0[6], 1)  # material_id
        self.assertEqual(depthp_pix_0[7], 0)  #

        self.assertEqual(
            canvas_list[0], list(range(8))
        )  # because material here is the 1, mode 1 is debug

        for anypix in canvas_list[1:]:
            self.assertEqual(
                anypix, [0, 0, 0, 0, 0, 0, 0, 0]
            )  # because material here is the 0, mode 0 is donothing

        for anypix in depth_buffer_list[1:]:
            self.assertEqual(
                anypix, [1000.0, 0.0, 0.0, 0.0, 0, 0, 0, 0]
            )  # because this is the raw canvas here.
