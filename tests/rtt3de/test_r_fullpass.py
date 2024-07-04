
import unittest
from rtt3de import GeometryBufferPy
from rtt3de import AbigDrawing
from rtt3de import MaterialBufferPy
from rtt3de import TextureBufferPy
from rtt3de import VertexBufferPy,TransformPackPy

from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture

from rtt3de import PrimitiveBufferPy
from rtt3de import raster_all_py,build_primitives_py,apply_material_py


class Test_Stages(unittest.TestCase):
    def test_simple_fullrun(self):

        texture_buffer = TextureBufferPy(12)
        img: ImageTexture = fast_load("models/test_screen32.bmp")
        data = img.chained_data()
        texture_buffer.add_texture(img.image_width ,img.image_height ,data)
        self.assertEqual(texture_buffer.size(), 1)



        # create some materials
        material_buffer = MaterialBufferPy()
        self.assertEqual(material_buffer.add_textured(0,1),0)
        self.assertEqual(material_buffer.count(),1)
        self.assertEqual(material_buffer.add_static((255,90,90,255),(5,10,20,255),0) , 1 )
        self.assertEqual(material_buffer.count(),2)


        # create a drawing buffer 
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)

        # create a geometry buffer to hold the initial elemnts
        vertex_buffer = VertexBufferPy()

        self.assertEqual(vertex_buffer.add_vertex(0.0,0.0,1.0),0)
        self.assertEqual(vertex_buffer.add_vertex(0.0,0.5,1.0),1)
        self.assertEqual(vertex_buffer.add_vertex(0.5,0.5,1.0),2)


        geometry_buffer = GeometryBufferPy(32)
        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(0,  node_id=0, material_id=1) ## this is the geomid default and MUST be the background. 
        
        
        node_id = 100
        material_id = 1
        geometry_buffer.add_polygon(0, 3, node_id, material_id,0,0)

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives_py(geometry_buffer,vertex_buffer,drawing_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, drawing_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 1)
        apply_material_py(material_buffer,texture_buffer,drawing_buffer)

        
