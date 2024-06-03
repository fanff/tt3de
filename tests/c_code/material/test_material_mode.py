
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


class Test_Static_Mode(unittest.TestCase):
    def test_mode_2_static_front(self):

        ###### init code
        # create a drawing buffer 
        # create a geometry buffer to hold the point at 0 0 wiht material 1
        # create a buffer of primitives

        drawing_buffer = DrawingBuffer(512 ,512)
        drawing_buffer.hard_clear(1000)

        geometry_buffer = GeometryBuffer(32)
        x, y, z = 0.1, 0.2, 1.0
        uv_array = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
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

        # the 1 material is in mode 2, its a ... static color map
        mat1 = Material(texturemode=2)

        mat1.set_albedo_front(23,45,56)
        mb.add_material(mat1) # 


        #build the primitives
        build_primitives(geometry_buffer,primitive_buffer)
        raster_precalc( primitive_buffer,  drawing_buffer)
        raster_all(primitive_buffer,drawing_buffer)

        
        apply_pixel_shader(primitive_buffer,drawing_buffer,mb,geometry_buffer)
        

        canvas_list = drawing_buffer.canvas_to_list()
        depth_buffer_list = drawing_buffer.drawbuffer_to_list()
        
        
        depthp_pix_0 = depth_buffer_list[0]
        self.assertEqual(depthp_pix_0[0], 1.0) # depth
        self.assertEqual(depthp_pix_0[1], 1.0) # weights to vertice 2D 
        self.assertEqual(depthp_pix_0[2], 0.0) # weights
        self.assertEqual(depthp_pix_0[3], 0.0) # weights


        self.assertEqual(depthp_pix_0[4], 100) # node id
        self.assertEqual(depthp_pix_0[5], 0) #
        self.assertEqual(depthp_pix_0[6], 1) # material_id 
        self.assertEqual(depthp_pix_0[7], 0) # 


        self.assertEqual(canvas_list[0], [23,45,56,0,0,0,0,0]) # because material here is the 1, mode 2 is color bstyatic

        for anypix in canvas_list[1:]:
            self.assertEqual(anypix, [0, 0, 0, 0, 0, 0, 0, 0]) # because material here is the 0, mode 0 is donothing
        
        for anypix in depth_buffer_list[1:]:
            self.assertEqual(anypix, [1000.0, 0.0, 0.0, 0.0, 0, 0, 0, 0]) #because this is the raw canvas here.


    def test_mode_3_static_back_albedo(self):

        ###### init code
        # create a drawing buffer 
        # create a geometry buffer to hold the point at 0 0 wiht material 1
        # create a buffer of primitives

        drawing_buffer = DrawingBuffer(512 ,512)
        drawing_buffer.hard_clear(1000)

        geometry_buffer = GeometryBuffer(32)
        x, y, z = 0.1, 0.2, 1.0
        uv_array = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
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
        settings = {"texturemode":3,
                    "albedo_front_r":1,
                    "albedo_front_g":2,
                    "albedo_front_b":3,
                    "albedo_back_r": 4,
                    "albedo_back_g": 5,
                    "albedo_back_b": 6,
                    "glyph_a" : 7,
                    "glyph_b" : 8,
                    "texture_id_array": [0]*8}
        mb.add_material_ele(settings)


        #build the primitives
        build_primitives(geometry_buffer,primitive_buffer)
        raster_precalc( primitive_buffer,  drawing_buffer)
        raster_all(primitive_buffer,drawing_buffer)

        
        apply_pixel_shader(primitive_buffer,drawing_buffer,mb,geometry_buffer)
        

        canvas_list = drawing_buffer.canvas_to_list()
        depth_buffer_list = drawing_buffer.drawbuffer_to_list()
        
        
        depthp_pix_0 = depth_buffer_list[0]
        self.assertEqual(depthp_pix_0[0], 1.0) # depth
        self.assertEqual(depthp_pix_0[1], 1.0) # weights to vertice 2D 
        self.assertEqual(depthp_pix_0[2], 0.0) # weights
        self.assertEqual(depthp_pix_0[3], 0.0) # weights


        self.assertEqual(depthp_pix_0[4], 100) # node id
        self.assertEqual(depthp_pix_0[5], 0) #
        self.assertEqual(depthp_pix_0[6], 1) # material_id 
        self.assertEqual(depthp_pix_0[7], 0) # 


        self.assertEqual(canvas_list[0], [0,0,0,4,5,6,0,0]) # because material here is the 1, mode 2 is color bstyatic

        for anypix in canvas_list[1:]:
            self.assertEqual(anypix, [0, 0, 0, 0, 0, 0, 0, 0]) # because material here is the 0, mode 0 is donothing
        
        for anypix in depth_buffer_list[1:]:
            self.assertEqual(anypix, [1000.0, 0.0, 0.0, 0.0, 0, 0, 0, 0]) #because this is the raw canvas here.
