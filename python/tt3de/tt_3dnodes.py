# -*- coding: utf-8 -*-
from typing import List, Optional

import glm

from tt3de.points import Point2D, Point3D
from tt3de.render_context_rust import RustRenderContext
from tt3de.utils import p2d_tovec2, random_node_id


class TT3DNode:
    def __init__(self, name: str = None, transform: Optional[glm.mat4] = None):
        self.name = name if name is not None else random_node_id()
        self.elements: List[TT3DNode] = []
        self.local_transform: glm.mat4 = (
            transform if transform is not None else glm.mat4(1.0)
        )
        self.node_id = None

    def add_child(self, child: "TT3DNode"):
        """
        Adds a child element to the list of elements.

        Args:
            child: The child element to be added.
        """
        self.elements.append(child)

    def insert_in(self, rc: "RustRenderContext", parent_transform: Optional[glm.mat4]):
        """
        Inserts the node in the render context.

        Function called
        """
        if parent_transform:
            fff = parent_transform * self.local_transform
        else:
            fff = self.local_transform
        for e in self.elements:
            e.insert_in(rc, fff)


class TT3DPolygonFan(TT3DNode):
    def __init__(
        self, name: str = None, transform: Optional[glm.mat4] = None, material_id=0
    ):
        super().__init__(name=name, transform=transform)
        self.vertex_list: List[Point3D] = []
        self.uvmap: List[tuple[Point2D, Point2D, Point2D]] = []
        self.material_id = material_id

        self.node_id = None

    def insert_in(self, rc: "RustRenderContext", parent_transform: glm.mat4):
        self.node_id = rc.transform_buffer.add_node_transform(
            parent_transform * self.local_transform
        )

        start_idx = None
        for p3d in self.vertex_list:
            vertex_idx = rc.vertex_buffer.add_vertex(p3d.x, p3d.y, p3d.z)
            if start_idx is None:
                start_idx = vertex_idx

        start_uv = None
        for uva, uvb, uvc in self.uvmap:
            idx = rc.vertex_buffer.add_uv(
                p2d_tovec2(uva), p2d_tovec2(uvb), p2d_tovec2(uvc)
            )
            if start_uv is None:
                start_uv = idx

        # rc.geometry_buffer.add_line3d(start_idx, self.node_id, self.material_id, 0)
        # rc.geometry_buffer.add_line3d(start_idx+1, self.node_id, self.material_id, 0)
        rc.geometry_buffer.add_polygon_fan_3d(
            start_idx,
            len(self.vertex_list) - 2,
            self.node_id,
            self.material_id,
            start_uv,
        )


class TT3DPolygon(TT3DNode):
    def __init__(
        self, name: str = None, transform: Optional[glm.mat4] = None, material_id=0
    ):
        super().__init__(name=name, transform=transform)
        self.vertex_list: List[Point3D] = []
        self.uvmap: List[tuple[Point2D, Point2D, Point2D]] = []
        self.material_id = material_id

        self.node_id = None

    def set_transform(self, rc, transform: glm.mat4):
        self.local_transform = transform
        rc.transform_buffer.set_node_transform(self.node_id, transform)

    def insert_in(self, rc: "RustRenderContext", parent_transform: glm.mat4):
        self.node_id = rc.transform_buffer.add_node_transform(
            parent_transform * self.local_transform
        )

        start_idx = None
        for p3d in self.vertex_list:
            vertex_idx = rc.vertex_buffer.add_vertex(p3d.x, p3d.y, p3d.z)
            if start_idx is None:
                start_idx = vertex_idx

        start_uv = None
        for uva, uvb, uvc in self.uvmap:
            idx = rc.vertex_buffer.add_uv(
                p2d_tovec2(uva), p2d_tovec2(uvb), p2d_tovec2(uvc)
            )
            if start_uv is None:
                start_uv = idx

        # rc.geometry_buffer.add_line3d(start_idx, self.node_id, self.material_id, 0)
        # rc.geometry_buffer.add_line3d(start_idx+1, self.node_id, self.material_id, 0)
        rc.geometry_buffer.add_polygon_3d(
            start_idx,
            len(self.vertex_list) // 3,
            self.node_id,
            self.material_id,
            start_uv,
        )


class TT3DPoint(TT3DNode):
    def __init__(
        self, name: str = None, transform: Optional[glm.mat4] = None, material_id=0
    ):
        super().__init__(name=name, transform=transform)
        self.vertex_list: List[Point3D] = []
        self.uvmap: List[tuple[Point2D, Point2D, Point2D]] = []
        self.material_id = material_id

        self.node_id = None

    def insert_in(self, rc: "RustRenderContext", parent_transform: glm.mat4):
        self.node_id = rc.transform_buffer.add_node_transform(
            parent_transform * self.local_transform
        )

        start_idx = None
        for p3d in self.vertex_list:
            vertex_idx = rc.vertex_buffer.add_vertex(p3d.x, p3d.y, p3d.z)
            if start_idx is None:
                start_idx = vertex_idx

        start_uv = None
        for uva, uvb, uvc in self.uvmap:
            idx = rc.vertex_buffer.add_uv(
                p2d_tovec2(uva), p2d_tovec2(uvb), p2d_tovec2(uvc)
            )
            if start_uv is None:
                start_uv = idx

        rc.geometry_buffer.add_point(
            start_idx, start_uv, self.node_id, self.material_id
        )
