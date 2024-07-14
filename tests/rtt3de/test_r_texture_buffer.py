import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture

from rtt3de import TextureBufferPy


class Test_TextureArray(unittest.TestCase):
    def test_create(self):
        texture_array = TextureBufferPy(12)
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        data = img.chained_data()
        texture_array.add_texture(img.image_width ,img.image_height ,data)
        self.assertEqual(texture_array.size(), 1)
        texture_array.add_texture(img.image_width ,img.image_height ,data)
        self.assertEqual(texture_array.size(), 2)
        texture_array.add_texture(img.image_width ,img.image_height ,data)
        self.assertEqual(texture_array.size(), 3)

        
    def test_create256(self):
        texture_array = TextureBufferPy(12)
        self.assertEqual(texture_array.size(), 0)
        img256: ImageTexture = fast_load("models/test_screen256.bmp")
        sky1: ImageTexture = fast_load("models/sky1.bmp")
        img32: ImageTexture = fast_load("models/test_screen32.bmp")


        texture_array.add_texture(img32.image_width ,img32.image_height ,img32.chained_data())
        self.assertEqual(texture_array.size(), 1)

        self.assertEqual(texture_array.get_wh_of(0), (32,32))

        texture_array.add_texture(img256.image_width ,img256.image_height ,img256.chained_data())
        self.assertEqual(texture_array.size(), 2)
        self.assertEqual(texture_array.get_wh_of(1), (256,256))
        
        texture_array.add_texture(sky1.image_width ,sky1.image_height ,sky1.chained_data())
        self.assertEqual(texture_array.size(), 3)
        self.assertEqual(texture_array.get_wh_of(2), (256,114))

        self.assertEqual(texture_array.get_rgba_at(2,0.0,0.0), (204, 145, 114, 255))
        self.assertEqual(texture_array.get_rgba_at(2,0.1,0.0), (211, 149, 113, 255))
        self.assertEqual(texture_array.get_rgba_at(2,0.1,0.1), (205, 146, 112, 255))



    def test_mapping_repeat(self):
        texture_array = TextureBufferPy(12)
        self.assertEqual(texture_array.size(), 0)
        sky1: ImageTexture = fast_load("models/sky1.bmp")

        texture_array.add_texture(sky1.image_width ,sky1.image_height ,sky1.chained_data())
        self.assertEqual(texture_array.size(), 1)
        self.assertEqual(texture_array.get_wh_of(0), (256,114))

        self.assertEqual( texture_array.get_rgba_at(0,0.0,0.0),
                          texture_array.get_rgba_at(0,1.0,1.0))
        

        # forcing a repeat by asking uv after 1.0
        self.assertEqual( texture_array.get_rgba_at(0,0.1,0.1),
                          texture_array.get_rgba_at(0,1.1,1.1))
        
        self.assertEqual( texture_array.get_rgba_at(0,0.4,0.4),
                          texture_array.get_rgba_at(0,1.4,1.4))

