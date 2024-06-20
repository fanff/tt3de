import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture

from tt3de.glm.c_texture import Texture2D, TextureArray


class Test_TextureArray(unittest.TestCase):
    def test_create(self):
        texture_array = TextureArray()
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        texture_array.load_texture256_from_list(img.img_data)
        self.assertEqual(texture_array.size(), 1)
        texture_array.load_texture256_from_list(img.img_data)
        self.assertEqual(texture_array.size(), 2)
        texture_array.load_texture256_from_list(img.img_data)
        self.assertEqual(texture_array.size(), 3)
    def test_create256(self):
        texture_array = TextureArray()
        self.assertEqual(texture_array.size(), 0)
        img256: ImageTexture = fast_load("models/test_screen256.bmp")
        sky1: ImageTexture = fast_load("models/sky1.bmp")
        img32: ImageTexture = fast_load("models/test_screen32.bmp")


        texture_array.load_texture256_from_list(img32.img_data)
        self.assertEqual(texture_array.size(), 1)

        self.assertEqual(texture_array.get_wh_of(0), [32,32])


        texture_array.load_texture256_from_list(img256.img_data)
        self.assertEqual(texture_array.size(), 2)
        self.assertEqual(texture_array.get_wh_of(1), [256,256])
        
        texture_array.load_texture256_from_list(sky1.img_data)
        self.assertEqual(texture_array.size(), 3)
        self.assertEqual(texture_array.get_wh_of(2), [256,114])

        self.assertEqual(texture_array.get_pixel_of(2,0.0,0.0), [204, 145, 114])
        self.assertEqual(texture_array.get_pixel_of(2,0.1,0.0), [211, 149, 113])
        self.assertEqual(texture_array.get_pixel_of(2,0.1,0.1), [205, 146, 112])
        
        hyp = [0]*64
        hyp[0] =1
        hyp[1] =1
        hyp[2] =1  
        self.assertEqual(texture_array.get_inner_map(), hyp)



    def test_mapping_repeat(self):
        texture_array = TextureArray()
        self.assertEqual(texture_array.size(), 0)
        sky1: ImageTexture = fast_load("models/sky1.bmp")

        texture_array.load_texture256_from_list(sky1.img_data)
        self.assertEqual(texture_array.size(), 1)
        self.assertEqual(texture_array.get_wh_of(1), [256,114])

        self.assertEqual(texture_array.get_pixel_of(1,0.0,0.0,repeat=False), [204, 145, 114])
        self.assertEqual(texture_array.get_pixel_of(1,0.1,0.0,repeat=False), [211, 149, 113])
        self.assertEqual(texture_array.get_pixel_of(1,0.1,0.1,repeat=False), [205, 146, 112])


        self.assertEqual(texture_array.get_pixel_of(1,0.0,0.0,repeat=True), [204, 145, 114])
        self.assertEqual(texture_array.get_pixel_of(1,0.1,0.0,repeat=True), [211, 149, 113])
        self.assertEqual(texture_array.get_pixel_of(1,0.1,0.1,repeat=True), [205, 146, 112])


        # forcing a repeat by asking uv after 1.0
        self.assertEqual(texture_array.get_pixel_of(1,1.0,1.0,repeat=True), [204, 145, 114])
        self.assertEqual(texture_array.get_pixel_of(1,1.1,1.0,repeat=True), [211, 149, 113])
        self.assertEqual(texture_array.get_pixel_of(1,1.1,1.1,repeat=True), [205, 146, 112])
        # forcing a repeat by asking uv after 5.0
        self.assertEqual(texture_array.get_pixel_of(1,5.0,5.0,repeat=True), [204, 145, 114])
        self.assertEqual(texture_array.get_pixel_of(1,5.1,5.0,repeat=True), [211, 149, 113])
        self.assertEqual(texture_array.get_pixel_of(1,5.1,5.1,repeat=True), [205, 146, 112])


    def test_mapping_transp(self):
        texture_array = TextureArray()
        self.assertEqual(texture_array.size(), 0)
        texture_array.load_texture256_from_list(
            fast_load("models/numbersheet.bmp").img_data,
            0,0,255 #this is the transparent color
        )
        self.assertEqual(texture_array.get_pixel_of(0,0.0,0.0,repeat=False,
                                                    transp=False), [0, 0, 255])
        
        self.assertEqual(texture_array.get_pixel_of(0,0.0,0.0,repeat=False,
                                                    transp=True), [0, 0, 0])
        
        self.assertEqual(texture_array.get_pixel_of(0,0.5,0.5,repeat=False,
                                                    transp=True), [0, 0, 0])
        

        self.assertEqual(texture_array.size(), 1)

    def test_mapping_transp2(self):
        texture_array = TextureArray()
        self.assertEqual(texture_array.size(), 0)
        texture_array.load_texture256_from_list(
            fast_load("models/numbersheet.bmp").img_data,
            0,0,222 # this is not the transparent color
        )
        self.assertEqual(texture_array.get_pixel_of(0,0.0,0.0,repeat=False,
                                                    transp=False), [0, 0, 255])
        
        self.assertEqual(texture_array.get_pixel_of(0,0.0,0.0,repeat=False,
                                                    transp=True), [0, 0, 255])
        self.assertEqual(texture_array.size(), 1)



class Test_UV_calc(unittest.TestCase):

    def test_calculate_uv(self):
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        atexture = Texture2D(img.image_width, img.image_height)
        atexture.load_from_list(img.img_data)

        c = atexture.get_pixel_uv(0, 0)

        self.assertEqual((0, 0, 0), c)

        c = atexture.get_pixel_uv(0.5, 0.5)

        self.assertEqual((0, 0, 0), c)

        c = atexture.get_pixel_uv(1.0, 1.0)
        self.assertEqual((0, 0, 0), c)
        c = atexture.get_pixel_uv(1.1, 1.1)
        self.assertEqual((0, 0, 0), c)

        c = atexture.get_pixel_uv(1.0 - 1.0 / 64, 1.0 - 1.0 / 64)
        self.assertEqual((255, 255, 255), c)
