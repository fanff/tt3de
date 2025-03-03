from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tt3de.tt_3dnodes import TT3DNode
from typing import List
import glm
from tt3de.tt3de import GeometryBufferPy
from tt3de.tt3de import AbigDrawing
from tt3de.tt3de import MaterialBufferPy
from tt3de.tt3de import TextureBufferPy
from tt3de.tt3de import VertexBufferPy, TransformPackPy
from tt3de.tt3de import PrimitiveBufferPy
from tt3de.tt3de import raster_all_py, build_primitives_py, apply_material_py

from textual.strip import Strip
from textual.geometry import Region

from tt3de.glm_camera import GLMCamera


class RustRenderContext:

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height

        self.texture_buffer = TextureBufferPy(32)
        self.material_buffer = MaterialBufferPy()
        self.vertex_buffer = VertexBufferPy(2048)
        self.geometry_buffer = GeometryBufferPy(256)
        self.geometry_buffer.add_point(0, 0, node_id=0, material_id=0)
        self.primitive_buffer = PrimitiveBufferPy(512)
        self.transform_buffer = TransformPackPy(64)
        self.drawing_buffer = AbigDrawing(max_row=self.height, max_col=self.width)

        self.global_bit_size = 4
        # self.drawing_buffer.set_bit_size_front(self.global_bit_size,self.global_bit_size,self.global_bit_size)
        # self.drawing_buffer.set_bit_size_back(self.global_bit_size,self.global_bit_size,self.global_bit_size)

        self.drawing_buffer.hard_clear(100.0)

    def update_wh(self, w, h):
        if w != self.width or h != self.height:
            self.width, self.height = w, h
            self.drawing_buffer = AbigDrawing(max_row=self.height, max_col=self.width)
            # self.drawing_buffer.set_bit_size_front(self.global_bit_size,self.global_bit_size,self.global_bit_size)
            # self.drawing_buffer.set_bit_size_back(self.global_bit_size,self.global_bit_size,self.global_bit_size)
            self.drawing_buffer.hard_clear(100.0)

    def write_text(self, txt: str, row: 0, col: 0):
        pass

    def clear_canvas(self):
        self.drawing_buffer.hard_clear(1000)

    def render(self, camera: GLMCamera):
        self.primitive_buffer.clear()

        self.transform_buffer.set_view_matrix_glm(camera.view_matrix_2D)

        self.transform_buffer.set_view_matrix_3d(
            glm.inverse(camera._rot) * glm.translate(-camera._pos)
        )
        # transform_buffer.set_view_matrix_3d(glm.inverse(camera._rot)) # camera.view_matrix_3D())
        # node_id = transform_buffer.add_node_transform(glm.translate(-camera._pos))#glm.mat4(1.0) )

        self.transform_buffer.set_projection_matrix(camera.perspective_matrix)

        # build the primitives
        build_primitives_py(
            self.geometry_buffer,
            self.vertex_buffer,
            self.transform_buffer,
            self.drawing_buffer,
            self.primitive_buffer,
        )

        raster_all_py(self.primitive_buffer, self.vertex_buffer, self.drawing_buffer)

        apply_material_py(
            self.material_buffer,
            self.texture_buffer,
            self.vertex_buffer,
            self.primitive_buffer,
            self.drawing_buffer,
        )

    def to_textual_2(self, region: Region) -> List[Strip]:

        res = self.drawing_buffer.to_textual_2(
            min_x=region.x,
            max_x=region.x + region.width,
            min_y=region.y,
            max_y=region.y + region.height,
        )

        return [Strip(l) for l in res]

    def append(self, elem: "TT3DNode"):
        """Append a 3D node to the render context.
        This will call the "insert_in" method on the object you are appending and recursively on all its children.
        """
        elem.insert_in(self, None)
