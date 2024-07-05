
import unittest
from rtt3de import GeometryBufferPy
from rtt3de import AbigDrawing
from rtt3de import MaterialBufferPy
from rtt3de import TextureBufferPy
from rtt3de import VertexBufferPy,TransformPackPy
from rtt3de import PrimitiveBufferPy

from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture

from rtt3de import raster_all_py,build_primitives_py,apply_material_py


class Test_Stages(unittest.TestCase):
    def test_simple_fullrun(self):
        transform_pack = TransformPackPy(64)
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
        
        
        node_id = 3
        material_id = 1
        geometry_buffer.add_polygon(0, 1, node_id, material_id,0)

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(10)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        # build the primitives
        build_primitives_py(geometry_buffer,vertex_buffer,transform_pack,drawing_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        raster_all_py(primitive_buffer, drawing_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 1)
        apply_material_py(material_buffer,texture_buffer,vertex_buffer,primitive_buffer,drawing_buffer)

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

        build_primitives_py(geometry_buffer,vertex_buffer,transform_pack,drawing_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

    def test_one_default(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)
        vertex_buffer = VertexBufferPy()
        geometry_buffer = GeometryBufferPy(256)
        transform_pack = TransformPackPy(64)


        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(0,  node_id=0, material_id=0) ## this is the geomid default and MUST be the background. 
        self.assertEqual(geometry_buffer.geometry_count(), 1)

        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)

        build_primitives_py(geometry_buffer,vertex_buffer,transform_pack,drawing_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 0)



    def test_simple_one_triangle(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)
        
        transform_pack = TransformPackPy(64)
        vertex_buffer = VertexBufferPy()
        self.assertEqual(vertex_buffer.add_vertex(0.0,0.0,0.5),0)
        self.assertEqual(vertex_buffer.add_vertex(0.0,0.5,0.5),1)
        self.assertEqual(vertex_buffer.add_vertex(0.5,0.5,0.5),2)

        self.assertEqual(vertex_buffer.add_vertex(0.5,0.0,0.5),3)



        geometry_buffer = GeometryBufferPy(256)
        self.assertEqual(geometry_buffer.geometry_count(), 0)
        geometry_buffer.add_point(0,  node_id=0, material_id=0) ## this is the geomid default and MUST be the background. 
            
        node_id = 2
        material_id = 1
        self.assertEqual(geometry_buffer.add_polygon(0, 1, node_id, material_id,0),1)

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)


        # build the primitives
        build_primitives_py(geometry_buffer,vertex_buffer,transform_pack,drawing_buffer, primitive_buffer)

        prim0 = primitive_buffer.get_primitive(0)
        
        self.assertEqual(primitive_buffer.primitive_count(), 1)

        self.assertEqual(prim0,{
            "primitive_id":0,
            "geometry_id":1,
            "node_id":node_id,
            "material_id":material_id,
            'pa': { 'col': 256, 'row': 256, 'depth': 0.5},
            'pb': { 'col': 256, 'row': 384, 'depth': 0.5},
            'pc': { 'col': 384, 'row': 384, 'depth': 0.5},
        })


    def test_simple_two_triangle(self):
        drawing_buffer = AbigDrawing(512, 512)
        drawing_buffer.hard_clear(1000)

        transform_pack = TransformPackPy(64)
        vertex_buffer = VertexBufferPy()
        self.assertEqual(vertex_buffer.add_vertex(0.0,0.0,1.0),0)
        self.assertEqual(vertex_buffer.add_vertex(0.0,1.0,1.0),1)
        self.assertEqual(vertex_buffer.add_vertex(1.0,1.0,1.0),2)
        self.assertEqual(vertex_buffer.add_vertex(1.0,0.0,1.0),3)



        geometry_buffer = GeometryBufferPy(256)
        self.assertEqual(geometry_buffer.geometry_count(), 0)


        geometry_buffer.add_point(0,  node_id=0, material_id=0) ## this is the geomid default and MUST be the background. 
            
        node_id = 3
        material_id = 2
        self.assertEqual(geometry_buffer.add_polygon(0, 2, node_id, material_id,0),1)

        # create a buffer of primitives
        primitive_buffer = PrimitiveBufferPy(256)
        self.assertEqual(primitive_buffer.primitive_count(), 0)


        # build the primitives
        build_primitives_py(geometry_buffer,vertex_buffer,transform_pack,drawing_buffer, primitive_buffer)
        self.assertEqual(primitive_buffer.primitive_count(), 2)

        prim0 = primitive_buffer.get_primitive(0)


        

        self.assertEqual(prim0,{
            "primitive_id":0,
            "geometry_id":1,
            "node_id":node_id,
            "material_id":material_id,
            'pa': { 'col': 256, 'row': 256, 'depth': 1.0},
            'pb': { 'col': 256, 'row': 512, 'depth': 1.0},
            'pc': { 'col': 512, 'row': 512, 'depth': 1.0},
        })


        prim1 = primitive_buffer.get_primitive(1)

        self.assertEqual(prim1,{
            "primitive_id":1,
            "geometry_id":1,
            "node_id":node_id,
            "material_id":material_id,
            'pa': { 'col': 256, 'row': 256, 'depth': 1.0},
            'pb': { 'col': 512, 'row': 512, 'depth': 1.0},
            'pc': { 'col': 512, 'row': 256, 'depth': 1.0},
        })

