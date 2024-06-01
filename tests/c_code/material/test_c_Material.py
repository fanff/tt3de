
import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture

from tt3de.glm.material.c_material import Material
from tt3de.glm.material.c_material import MaterialBuffer
from tt3de.glm.c_texture import Texture2D


from tt3de.glm.material.c_material import apply_pixel_shader
from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer



class Test_Material(unittest.TestCase):
    def test_create(self):
        amaterial = Material()


        print(amaterial)
        #print(amaterial.dostuff())
    def test_blit(self):
        
        img:ImageTexture = fast_load("models/test_screen32.bmp")
        atexture = Texture2D(img.image_width,img.image_height)
        atexture.load_from_list(img.img_data)

        amaterial = Material()
        amaterial.add_texture(atexture)
        amaterial.add_texture(atexture)
        amaterial.add_texture(atexture)

        from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

        drawbuffer = DrawingBuffer(512 ,512)
        amaterial.test_blit(0,0,drawbuffer)

class Test_MaterialBuffer(unittest.TestCase):
    def test_create(self):
        

        img:ImageTexture = fast_load("models/test_screen32.bmp")
        atexture = Texture2D(img.image_width,img.image_height)
        atexture.load_from_list(img.img_data)

        mb = MaterialBuffer()

        mat = Material()

        mat.add_texture(atexture)

        mb = MaterialBuffer()   

        mb.add_material(mat)



class Test_ApplyMaterialMethod(unittest.TestCase):
    def test_this(self):
        
        # create some material on one side 
        img:ImageTexture = fast_load("models/test_screen32.bmp")
        atexture = Texture2D(img.image_width,img.image_height)
        atexture.load_from_list(img.img_data)

        mat = Material()
        mat.add_texture(atexture)

        mb = MaterialBuffer()   
        mb.add_material(mat)


        # create a drawing buffer on the other side
        drawbuffer = DrawingBuffer(512 ,512)
        drawbuffer.hard_clear(1000)

        apply_pixel_shader(drawbuffer,mb)






