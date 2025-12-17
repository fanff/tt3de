# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Union


if TYPE_CHECKING:
    from tt3de.tt_2dnodes import TT2DNode
    from tt3de.tt_3dnodes import TT3DNode

from typing import List

from pyglm import glm
from textual.geometry import Region
from textual.strip import Strip

from tt3de.glm_camera import GLMCamera
from tt3de.tt3de import (
    DrawingBufferPy,
    GeometryBufferPy,
    MaterialBufferPy,
    PrimitiveBufferPy,
    TextureBufferPy,
    TransformPackPy,
    VertexBufferPy,
    apply_material_py_parallel,
    build_primitives_py,
    raster_all_py,
)


class RustRenderContext:
    def __init__(
        self,
        screen_width,
        screen_height,
        vertex_buffer_size=1024,
        uv_buffer_size=1024,
        vertex_2d_buffer_size=1024,
        geometry_buffer_size=256,
        primitive_buffer_size=2048,
        transform_buffer_size=64,
        texture_buffer_size=32,
        material_buffer_size=32,
    ):
        self.width = screen_width
        self.height = screen_height

        self.texture_buffer = TextureBufferPy(texture_buffer_size)
        self.material_buffer = MaterialBufferPy(material_buffer_size)
        self.vertex_buffer = VertexBufferPy(
            vertex_buffer_size, uv_buffer_size, vertex_2d_buffer_size
        )
        self.geometry_buffer: GeometryBufferPy = GeometryBufferPy(geometry_buffer_size)
        self.geometry_buffer.add_point_3d(0, 0, node_id=0, material_id=0)
        self.primitive_buffer = PrimitiveBufferPy(primitive_buffer_size)
        self.transform_buffer = TransformPackPy(transform_buffer_size)
        self.drawing_buffer: DrawingBufferPy = DrawingBufferPy(
            max_row=self.height, max_col=self.width
        )

        self.global_bit_size = 4
        # self.drawing_buffer.set_bit_size_front(self.global_bit_size,self.global_bit_size,self.global_bit_size)
        # self.drawing_buffer.set_bit_size_back(self.global_bit_size,self.global_bit_size,self.global_bit_size)

        self.drawing_buffer.hard_clear(1000.0)
        self.roots_nodes: List[Union["TT3DNode", "TT2DNode"]] = []

    def update_wh(self, w, h):
        if w != self.width or h != self.height:
            self.width, self.height = w, h
            self.drawing_buffer = DrawingBufferPy(
                max_row=self.height, max_col=self.width
            )
            # self.drawing_buffer.set_bit_size_front(self.global_bit_size,self.global_bit_size,self.global_bit_size)
            # self.drawing_buffer.set_bit_size_back(self.global_bit_size,self.global_bit_size,self.global_bit_size)
            self.drawing_buffer.hard_clear(1000.0)

    def clear_canvas(self):
        self.drawing_buffer.hard_clear(1000.0)

    def render(self, camera: GLMCamera):
        self.transform_buffer.set_view_matrix_glm(camera.view_matrix_2D)

        self.transform_buffer.set_view_matrix_3d(
            glm.inverse(camera._rot) * glm.translate(-camera._pos)
        )
        # transform_buffer.set_view_matrix_3d(glm.inverse(camera._rot)) # camera.view_matrix_3D())
        # node_id = transform_buffer.add_node_transform(glm.translate(-camera._pos))#glm.mat4(1.0) )

        self.transform_buffer.set_projection_matrix(camera.perspective_matrix)

        # build the primitives in the primitive buffer using the projected geometry
        self.primitive_buffer.clear()

        self.process_dirty()

        build_primitives_py(
            self.geometry_buffer,
            self.vertex_buffer,
            self.transform_buffer,
            self.drawing_buffer,
            self.primitive_buffer,
        )
        # raster all the primitives in the drawing buffer
        raster_all_py(self.primitive_buffer, self.vertex_buffer, self.drawing_buffer)

        # apply_material_py(
        #     self.material_buffer,
        #     self.texture_buffer,
        #     self.vertex_buffer,
        #     self.primitive_buffer,
        #     self.drawing_buffer,
        # )
        # make a pass to apply the material on the drawing buffer
        apply_material_py_parallel(
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

        return [Strip(line) for line in res]

    def process_dirty(self):
        for elem in self.roots_nodes:
            elem.sync_in_context(self)

    def append_root(self, elem: Union["TT3DNode", "TT2DNode"]):
        """
        Append a 3D node to the render context.

        This will call the "insert_in" method on the object you are appending and
        recursively on all its children.
        """

        self.roots_nodes.append(elem)
        elem.insert_in(self)
