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
from tt3de.glm.c_texture import TextureArray

from tt3de.glm.primitives.primitive_builder import build_primitives

from tt3de.glm.geometry.geometry import GeometryBuffer
from tt3de.utils import TT3DEMaterialMode, TT3DEMaterialTextureMappingOptions


class Test_Static_Mode(unittest.TestCase):
    def test_mode_2_static_front(self):

        ###### init code
        # create a drawing buffer
        # create a geometry buffer to hold the point at 0 0 wiht material 1
        # create a buffer of primitives

        drawing_buffer = DrawingBuffer(512, 512)
        drawing_buffer.hard_clear(1000)

        geometry_buffer = GeometryBuffer(32)
        x, y, z = 0.1, 0.2, 1.0
        uv_array = [0.1, 0.1]* 16
        node_id = 100
        material_id = 1
        geometry_buffer.add_point_to_buffer(x, y, z, uv_array, node_id, material_id)

        primitive_buffer = PrimitivesBuffer(10)
        ####### start of the test

        ###

        texture_array_object = TextureArray()

        mb = MaterialBuffer()
        self.assertEqual(mb.size(), 0)
        # the 0 material
        mat0 = Material(texturemode=0)
        mb.add_material(mat0)
        self.assertEqual(mb.size(), 1)
        # the 1 material is in mode 2, its a ... static color map
        mat1 = Material(texturemode=2)

        mat1.set_albedo_front(23, 45, 56)
        mb.add_material(mat1)  #

        self.assertEqual(mb.size(), 2)
        # build the primitives
        build_primitives(geometry_buffer, primitive_buffer)
        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, mb)

        apply_pixel_shader(
            primitive_buffer, drawing_buffer, mb, geometry_buffer, texture_array_object
        )

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
            canvas_list[0], [23, 45, 56, 0, 0, 0, 0, 0]
        )  # because material here is the 1, mode 2 is color bstyatic

        for anypix in canvas_list[1:]:
            self.assertEqual(
                anypix, [0, 0, 0, 0, 0, 0, 0, 0]
            )  # because material here is the 0, mode 0 is donothing

        for anypix in depth_buffer_list[1:]:
            self.assertEqual(
                anypix, [1000.0, 0.0, 0.0, 0.0, 0, 0, 0, 0]
            )  # because this is the raw canvas here.

    def test_mode_3_static_back_albedo(self):

        ###### init code
        # create a drawing buffer
        # create a geometry buffer to hold the point at 0 0 wiht material 1
        # create a buffer of primitives

        drawing_buffer = DrawingBuffer(512, 512)
        drawing_buffer.hard_clear(1000)

        geometry_buffer = GeometryBuffer(32)
        x, y, z = 0.1, 0.2, 1.0
        uv_array = [0.1, 0.1]* 16
        node_id = 100
        material_id = 1
        geometry_buffer.add_point_to_buffer(x, y, z, uv_array, node_id, material_id)

        primitive_buffer = PrimitivesBuffer(10)
        ####### start of the test

        ###
        mb = MaterialBuffer()

        # the 0 material
        mat0 = Material(texturemode=0)
        mb.add_material(mat0)

        # the 1 material is in mode 3, its a ... static color map back albedo
        settings = {
            "texturemode": 3,
            "texture_mapping_options": 0,
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

        # build the primitives
        build_primitives(geometry_buffer, primitive_buffer)
        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, mb)

        texture_array_object = TextureArray()
        apply_pixel_shader(
            primitive_buffer, drawing_buffer, mb, geometry_buffer, texture_array_object
        )

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
            canvas_list[0], [0, 0, 0, 4, 5, 6, 0, 0]
        )  # because material here is the 1, mode 2 is color bstyatic

        for anypix in canvas_list[1:]:
            self.assertEqual(
                anypix, [0, 0, 0, 0, 0, 0, 0, 0]
            )  # because material here is the 0, mode 0 is donothing

        for anypix in depth_buffer_list[1:]:
            self.assertEqual(
                anypix, [1000.0, 0.0, 0.0, 0.0, 0, 0, 0, 0]
            )  # because this is the raw canvas here.



    def test_mode_double_raster_full_transp(self):

        ###### init code
        # create a drawing buffer
        # create a geometry buffer to hold the point at 0 0 wiht material 1
        # create a buffer of primitives

        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(1000)

        geometry_buffer = GeometryBuffer(32)
        

        primitive_buffer = PrimitivesBuffer(10)
        

        texture_array_object = TextureArray()
        texture_array_object.load_texture256_from_list(
            fast_load("models/numbersheet.bmp").img_data,
            0,0,255
        )
        mb = MaterialBuffer()

        # the 0 material
        mat0 = Material(texturemode=TT3DEMaterialMode.STATIC_ALL.value)
        mat0.set_albedo_back(200, 0, 0)
        mat0.set_albedo_front(0, 200, 0)
        mb.add_material(mat0)

        
        mat1 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat1.set_albedo_front(0, 200, 150)
        mat1.set_albedo_back(200, 0, 0)
        mat1.set_glyph(0, 157)
        mat1.set_texture_ids([0, -1, -1])
        mops = TT3DEMaterialTextureMappingOptions()
        mops.texture_mapping_repetition = 0
        mops.texture_transparency_mode = 1
        mat1.set_texture_mapping_options(mops.get_value())
        mb.add_material(mat1)

        ####### start of the test

        ###
        x, y, z = 0.1, 0.2, 1.0
        uv_array = [0.0, 0.0]* 16
        node_id = 100
        material_id = 1
        geometry_buffer.add_point_to_buffer(x, y, z, uv_array, node_id, material_id)



        # build the primitives
        build_primitives(geometry_buffer, primitive_buffer)
        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, mb)

        elem_of_dephtbuffer_0 = drawing_buffer.get_depth_buff_content(0, 0 , layer=0)
        elem_of_dephtbuffer_1 = drawing_buffer.get_depth_buff_content(0, 0 , layer=1)
        self.assertEqual(elem_of_dephtbuffer_0, {
                "depth_value": 1.0,
                "w1": 1.0,
                "w2": 0.0,
                "w3": 0.0,
                "w1_alt": 0.5,
                "w2_alt": 0.5,
                "w3_alt": 0.0,
                "primitiv_id": 0,
                "geom_id": 0,
                "node_id": node_id,
                "material_id": material_id,
            })  # the point is located at 0,0, with correct depth
        self.assertEqual(elem_of_dephtbuffer_1, {
                "depth_value": 1000.0,
                "w1": 0.0,
                "w2": 0.0,
                "w3": 0.0,
                "w1_alt": 0.0,
                "w2_alt": 0.0,
                "w3_alt": 0.0,
                "primitiv_id": 0,
                "geom_id": 0,
                "node_id": 0,
                "material_id": 0,
            })  # the layer on the back is untouched
        


        apply_pixel_shader(
            primitive_buffer, drawing_buffer, mb, geometry_buffer, texture_array_object
        )

        canvas_list = drawing_buffer.canvas_to_list()


        self.assertEqual(
            canvas_list[0], [0, 200, 0, 200, 0, 0, 0, 0]
        )  # firt corlor is the green, because mat 0 colorized
        # second color (background) is blit because mat0 applyed
        # glyph is 0 0 , because  the transparency applied



    def test_mode_double_raster_transp_blit(self):

        ###### init code
        # create a drawing buffer
        # create a geometry buffer to hold the point at 0 0 wiht material 1
        # create a buffer of primitives

        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(1000)

        geometry_buffer = GeometryBuffer(32)
        

        primitive_buffer = PrimitivesBuffer(10)
        

        texture_array_object = TextureArray()
        texture_array_object.load_texture256_from_list(
            fast_load("models/numbersheet.bmp").img_data,
            0,0,255
        )
        mb = MaterialBuffer()

        # the 0 material
        mat0 = Material(texturemode=TT3DEMaterialMode.STATIC_ALL.value)
        mat0.set_albedo_back(200, 0, 0)
        mat0.set_albedo_front(0, 200, 0)
        mb.add_material(mat0)

        
        mat1 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat1.set_albedo_front(0, 200, 150)
        mat1.set_albedo_back(200, 0, 0)
        mat1.set_glyph(0, 157)
        mat1.set_texture_ids([0, -1, -1])
        mops = TT3DEMaterialTextureMappingOptions()
        mops.texture_mapping_repetition = 0
        mops.texture_transparency_mode = 1
        mat1.set_texture_mapping_options(mops.get_value())
        mb.add_material(mat1)

        ####### start of the test

        ### UV is targeting a point that we know is not transparent 
        x, y, z = 0.1, 0.2, 1.0
        uv_array = [18.0/256, 18.0/256] * 16
        node_id = 100
        material_id = 1
        geometry_buffer.add_point_to_buffer(x, y, z, uv_array, node_id, material_id)



        # build the primitives
        build_primitives(geometry_buffer, primitive_buffer)
        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, mb)

        elem_of_dephtbuffer_0 = drawing_buffer.get_depth_buff_content(0, 0 , layer=0)
        elem_of_dephtbuffer_1 = drawing_buffer.get_depth_buff_content(0, 0 , layer=1)
        self.assertEqual(elem_of_dephtbuffer_0, {
                "depth_value": 1.0,
                "w1": 1.0,
                "w2": 0.0,
                "w3": 0.0,
                "w1_alt": 0.5,
                "w2_alt": 0.5,
                "w3_alt": 0.0,
                "primitiv_id": 0,
                "geom_id": 0,
                "node_id": node_id,
                "material_id": material_id,
            })  # the point is located at 0,0, with correct depth
        self.assertEqual(elem_of_dephtbuffer_1, {
                "depth_value": 1000.0,
                "w1": 0.0,
                "w2": 0.0,
                "w3": 0.0,
                "w1_alt": 0.0,
                "w2_alt": 0.0,
                "w3_alt": 0.0,
                "primitiv_id": 0,
                "geom_id": 0,
                "node_id": 0,
                "material_id": 0,
            })  # the layer on the back is untouched
        


        apply_pixel_shader(
            primitive_buffer, drawing_buffer, mb, geometry_buffer, texture_array_object
        )

        canvas_list = drawing_buffer.canvas_to_list()


        self.assertEqual(
            canvas_list[0], [160, 160, 164, 160, 160, 164, 0, 157]
        )  # firt corlor is the White, because mat 1 colorized
        # second color (background) is White because mat1 applyed
        # glyph is 0 157 , because  the transparency applied


    def test_mode_double_raster_half_blit(self):

        ###### init code
        # create a drawing buffer
        # create a geometry buffer to hold the point at 0 0 wiht material 1
        # create a buffer of primitives

        drawing_buffer = DrawingBuffer(32, 32)
        drawing_buffer.hard_clear(1000)

        geometry_buffer = GeometryBuffer(32)
        

        primitive_buffer = PrimitivesBuffer(10)
        

        texture_array_object = TextureArray()
        texture_array_object.load_texture256_from_list(
            fast_load("models/numbersheet.bmp").img_data,
            0,0,255
        )
        mb = MaterialBuffer()

        # the 0 material
        mat0 = Material(texturemode=TT3DEMaterialMode.STATIC_ALL.value)
        mat0.set_albedo_back(200, 0, 0)
        mat0.set_albedo_front(0, 200, 0)
        mb.add_material(mat0)

        
        mat1 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat1.set_albedo_front(0, 200, 150)
        mat1.set_albedo_back(200, 0, 0)
        mat1.set_glyph(0, 157)
        mat1.set_texture_ids([0, -1, -1])
        mops = TT3DEMaterialTextureMappingOptions()
        mops.texture_mapping_repetition = 0
        mops.texture_transparency_mode = 1
        mat1.set_texture_mapping_options(mops.get_value())
        mb.add_material(mat1)

        ####### start of the test

        ### UV is targeting a point that we know is not transparent 
        x, y, z = 0.1, 0.2, 1.0

        # the uv_array_will use a from too pattern, 
        uv_array = [ 18.5/256,    2.5/256 , 19.5/256,    3.5/256   ] * 8
        node_id = 100
        material_id = 1
        geometry_buffer.add_point_to_buffer(x, y, z, uv_array, node_id, material_id)



        # build the primitives
        build_primitives(geometry_buffer, primitive_buffer)
        raster_precalc(primitive_buffer, drawing_buffer)
        raster_all(primitive_buffer, drawing_buffer, mb)

        elem_of_dephtbuffer_0 = drawing_buffer.get_depth_buff_content(0, 0 , layer=0)
        elem_of_dephtbuffer_1 = drawing_buffer.get_depth_buff_content(0, 0 , layer=1)
        self.assertEqual(elem_of_dephtbuffer_0, {
                "depth_value": 1.0,
                "w1": 1.0,
                "w2": 0.0,
                "w3": 0.0,
                "w1_alt": 0.5,
                "w2_alt": 0.5,
                "w3_alt": 0.0,
                "primitiv_id": 0,
                "geom_id": 0,
                "node_id": node_id,
                "material_id": material_id,
            })  # the point is located at 0,0, with correct depth
        self.assertEqual(elem_of_dephtbuffer_1, {
                "depth_value": 1000.0,
                "w1": 0.0,
                "w2": 0.0,
                "w3": 0.0,
                "w1_alt": 0.0,
                "w2_alt": 0.0,
                "w3_alt": 0.0,
                "primitiv_id": 0,
                "geom_id": 0,
                "node_id": 0,
                "material_id": 0,
            })  # the layer on the back is untouched
        


        apply_pixel_shader(
            primitive_buffer, drawing_buffer, mb, geometry_buffer, texture_array_object
        )

        canvas_list = drawing_buffer.canvas_to_list()


        self.assertEqual(
            canvas_list[0], [0,0,0, 197, 197, 198, 0, 157]
        )  # firt corlor is the black, because the texture has a blac line on top of the number
        # second color is White because mat1 applyed; just bellow the
        # glyph is 0 157 , because the double blit
