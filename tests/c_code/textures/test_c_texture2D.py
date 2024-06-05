
import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture

from tt3de.glm.c_texture import Texture2D,TextureArray


class Test_TextureArray(unittest.TestCase):
    def test_create(self):
        texture_array = TextureArray()
        img:ImageTexture = fast_load("models/test_screen32.bmp")
        texture_array.load_texture32_from_list(img.img_data)
        self.assertEqual(texture_array.size(),1)


class Test_UV_calc(unittest.TestCase):
    
    def test_calculate_uv(self):
        img:ImageTexture = fast_load("models/test_screen32.bmp")
        atexture = Texture2D(img.image_width,img.image_height)
        atexture.load_from_list(img.img_data)


        c = atexture.get_pixel_uv(0,0)

        self.assertEqual((0,0,0),c)


        c = atexture.get_pixel_uv(.5,.5)

        self.assertEqual((0,0,0),c)

        c = atexture.get_pixel_uv(1.0,1.0)
        self.assertEqual((0,0,0),c)
        c = atexture.get_pixel_uv(1.1,1.1)
        self.assertEqual((0,0,0),c)


        c = atexture.get_pixel_uv(1.0-1.0/64,1.0-1.0/64)
        self.assertEqual((255,255,255),c)


