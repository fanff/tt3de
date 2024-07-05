
from typing import List
from rtt3de import GeometryBufferPy
from rtt3de import AbigDrawing
from rtt3de import MaterialBufferPy
from rtt3de import TextureBufferPy
from rtt3de import VertexBufferPy,TransformPackPy
from rtt3de import PrimitiveBufferPy


from rtt3de import raster_all_py,build_primitives_py,apply_material_py


from textual.strip import Strip
from textual.geometry import Region

from tt3de.glm_camera import GLMCamera
from tt3de.tt3de import Drawable3D


class RustRenderContext():

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height

        self.texture_buffer = TextureBufferPy(32)
        self.material_buffer = MaterialBufferPy()
        self.vertex_buffer = VertexBufferPy()
        self.geometry_buffer = GeometryBufferPy(256)
        self.geometry_buffer.add_point(0,  node_id=0, material_id=0)
        self.primitive_buffer = PrimitiveBufferPy(256)
        self.transform_buffer = TransformPackPy(64)
        self.drawing_buffer = AbigDrawing(max_row=self.height,  max_col=self.width)

        self.drawing_buffer.set_bit_size_front(8,8,8)
        self.drawing_buffer.set_bit_size_back(8,8,8)
        self.drawing_buffer.hard_clear(100.0)    
    def update_wh(self, w, h):
        if w!= self.width or h!= self.height:
            self.width, self.height = w,h
            self.drawing_buffer = AbigDrawing(max_row=self.height,max_col=self.width)
            self.drawing_buffer.set_bit_size_front(8,8,8)
            self.drawing_buffer.set_bit_size_back(8,8,8)
            self.drawing_buffer.hard_clear(100.0) 
    def write_text(self, txt: str, row:0,col:0):
        pass

    def clear_canvas(self):
        self.drawing_buffer.hard_clear(1000)


    def render(self, camera: GLMCamera):
        self.primitive_buffer.clear()

        self.transform_buffer.set_view_matrix_glm(camera.view_matrix_2D)
        # build the primitives
        build_primitives_py(self.geometry_buffer,
                            self.vertex_buffer,
                            self.transform_buffer,
                            self.drawing_buffer,
                            self.primitive_buffer)
        raster_all_py(self.primitive_buffer, self.drawing_buffer)

        apply_material_py(self.material_buffer,
                          self.texture_buffer,
                          self.vertex_buffer,
                          self.primitive_buffer,
                          self.drawing_buffer)

    def to_textual_2(self, region: Region) -> List[Strip]:

        res = self.drawing_buffer.to_textual_2(min_x = region.x,
                                                max_x = region.x+region.width,
                                                min_y = region.y,
                                                max_y = region.y+region.height)
        
        return [Strip(l) for l in res]
        
    def append(self, elem: Drawable3D):
        elem.insert_in(self,None)