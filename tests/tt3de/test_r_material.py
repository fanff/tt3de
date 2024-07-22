import unittest

from rtt3de import MaterialBufferPy,TextureBufferPy

from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture

class Test_MaterialBufferPy(unittest.TestCase):
    def test_create(self):
        mb = MaterialBufferPy()

        self.assertEqual(mb.count(),0)

        self.assertEqual(mb.add_static((255,90,90,255),(5,10,20,255),0) , 0 )

        self.assertEqual(mb.count(),1)
        self.assertEqual(mb.add_static((255,90,90,255),(5,10,20,255),2), 1 ) 
        self.assertEqual(mb.count(),2)


    def test_add_texture(self):
        texture_array = TextureBufferPy(12)
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        data = img.chained_data()
        texture_array.add_texture(img.image_width ,img.image_height ,data,repeat_width=True,repeat_height=True)
        self.assertEqual(texture_array.size(), 1)


        
        mb = MaterialBufferPy()
        self.assertEqual(mb.add_textured(0,1),0)
        self.assertEqual(mb.count(),1)
        
