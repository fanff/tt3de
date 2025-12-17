# -*- coding: utf-8 -*-
from typing import List, Optional, Tuple

from pyglm import glm

from tt3de.points import Point2D, Point3D
from tt3de.render_context_rust import RustRenderContext
from tt3de.tt_2dnodes import DirtyProcessor, TreeNode, WithMaterialID
from tt3de.utils import p2d_tovec2, random_node_id


class TT3DNode(TreeNode, DirtyProcessor):
    def __init__(self, name: str | None = None, transform: Optional[glm.mat4] = None):
        if name is None:
            name = f"Node3D_{random_node_id()}"
        super().__init__(name=name)
        self.name = name if name is not None else random_node_id()

        self.local_transform: glm.mat4 = (
            transform if transform is not None else glm.mat4(1.0)
        )
        self.global_transform_dirty: bool = True
        self.global_transform_matrix: glm.mat4 = self.local_transform
        self.node_id = None
        self.elements: List[TT3DNode] = []
        self.parent: TT3DNode = None

    def add_child(self, child: "TT3DNode"):  # type: ignore
        """
        Adds a child element to the list of elements.

        Args:
            child: The child element to be added.
        """
        super().add_child(child)

    def global_transform(self) -> glm.mat4:
        return self.global_transform_matrix

    def to_global_transform(self) -> glm.mat4:
        if self.parent is not None:
            return self.parent.global_transform() * self.local_transform
        else:
            return self.local_transform

    def __recalc_global_transform(self):
        self.global_transform_matrix = self.to_global_transform()

    def set_local_transform(self, transform: glm.mat4):
        self.local_transform = transform
        self.global_transform_dirty = True

    def apply_transform(self, transform: glm.mat4):
        self.local_transform = transform * self.local_transform
        self.global_transform_dirty = True

    def sync_in_context(self, rc: "RustRenderContext"):
        if self.global_transform_dirty:
            assert self.node_id is not None
            self.__recalc_global_transform()
            rc.transform_buffer.set_node_transform(
                self.node_id, self.global_transform_matrix
            )
            self.global_transform_dirty = False
            for child in self.elements:
                child.global_transform_dirty = True

        for child in self.elements:
            child.sync_in_context(rc)

    def insert_in(self, rc: "RustRenderContext"):
        """
        Inserts the node in the render context.

        This function will add the node's transform to the render context's transform
        buffer and recursively insert all child elements. Also setting the node_id
        attribute and rc attribute.
        """
        if self.node_id is not None:
            raise ValueError("Already inserted in context")
        self.rc = rc
        self.node_id = rc.transform_buffer.add_node_transform(
            self.global_transform_matrix
        )
        self.global_transform_dirty = True

        for e in self.elements:
            e.insert_in(rc)


class TT3DPolygonFan(WithMaterialID, TT3DNode):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        material_id=0,
    ):
        if name is None:
            name = f"PolygonFan_{random_node_id()}"
        super().__init__(name=name, transform=transform, material_id=material_id)
        self.vertex_list: List[Point3D] = []
        self.uvmap: List[tuple[Point2D, Point2D, Point2D]] = []
        self.geom_id = None

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)

        start_idx = None
        for p3d in self.vertex_list:
            vertex_idx = rc.vertex_buffer.add_3d_vertex(p3d.x, p3d.y, p3d.z)
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
        self.geom_id = rc.geometry_buffer.add_polygon_3d(
            start_idx,
            len(self.vertex_list) - 2,
            self.node_id,
            self.material_id,
            start_uv,
        )


class TT3DPolygon(WithMaterialID, TT3DNode):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        material_id=0,
    ):
        super().__init__(name=name, transform=transform, material_id=material_id)
        self.vertex_list: List[Point3D] = []
        self.triangles: List[Tuple[int, int, int]] = []
        self.uvmap: List[tuple[Point2D, Point2D, Point2D]] = []
        self.geom_id = None
        self.flipped_normals: bool = False

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)
        if self.geom_id is not None:
            raise ValueError("Already inserted in GeometryBuffer")
        assert rc.geometry_buffer is not None
        assert self.node_id is not None

        # insert all vertices
        vertex_index_list = [
            rc.vertex_buffer.add_3d_vertex(p3d.x, p3d.y, p3d.z)
            for p3d in self.vertex_list
        ]
        start_idx = vertex_index_list[0]

        # insert all triangles
        triangle_count = len(self.triangles)
        assert triangle_count == len(self.uvmap)
        triangle_start = None
        start_uv = None
        for triangle_idx, ((uva, uvb, uvc), (idx_a, idx_b, idx_c)) in enumerate(
            zip(self.uvmap, self.triangles)
        ):
            pa = self.vertex_list[idx_a]
            pb = self.vertex_list[idx_b]
            pc = self.vertex_list[idx_c]
            ab = glm.vec3(pb.x - pa.x, pb.y - pa.y, pb.z - pa.z)
            ac = glm.vec3(pc.x - pa.x, pc.y - pa.y, pc.z - pa.z)
            normal = glm.normalize(glm.cross(ab, ac))
            if self.flipped_normals:
                normal = -normal
            uv_idx, triangle_idx = rc.vertex_buffer.add_3d_triangle(
                vertex_index_list[idx_a],
                vertex_index_list[idx_b],
                vertex_index_list[idx_c],
                p2d_tovec2(uva),
                p2d_tovec2(uvb),
                p2d_tovec2(uvc),
                normal=normal,
            )
            if start_uv is None:
                start_uv = uv_idx
            if triangle_start is None:
                triangle_start = triangle_idx
        assert start_uv is not None
        assert triangle_start is not None
        self.geom_id = rc.geometry_buffer.add_polygon_3d(
            start_idx,
            len(vertex_index_list),
            start_uv,
            triangle_start,
            triangle_count,
            self.node_id,
            self.material_id,
        )


class TT3DPoint(WithMaterialID, TT3DNode):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        material_id=0,
    ):
        super().__init__(name=name, transform=transform, material_id=material_id)
        self.vertex_list: List[Point3D] = []
        self.uvmap: List[tuple[Point2D, Point2D, Point2D]] = []
        self.geom_id = None

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)
        assert self.node_id is not None

        start_idx = None
        for p3d in self.vertex_list:
            vertex_idx = rc.vertex_buffer.add_3d_vertex(p3d.x, p3d.y, p3d.z)
            if start_idx is None:
                start_idx = vertex_idx

        start_uv = None
        for uva, uvb, uvc in self.uvmap:
            idx = rc.vertex_buffer.add_uv(
                p2d_tovec2(uva), p2d_tovec2(uvb), p2d_tovec2(uvc)
            )
            if start_uv is None:
                start_uv = idx
        assert start_idx is not None
        assert start_uv is not None
        self.geom_id = rc.geometry_buffer.add_point_3d(
            start_idx, start_uv, self.node_id, self.material_id
        )


class TT3DLine(WithMaterialID, TT3DNode):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        material_id=0,
    ):
        super().__init__(name=name, transform=transform, material_id=material_id)
        self.vertex_list: List[Point3D] = []
        self.segment_uv: List[Tuple[Point2D, Point2D]] = []
        self.geom_id = None

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)
        self.vertex_indices = [
            rc.vertex_buffer.add_3d_vertex(p3d.x, p3d.y, p3d.z)
            for p3d in self.vertex_list
        ]
        self.segment_idx = [
            rc.vertex_buffer.add_uv(
                glm.vec2(uva.x, uva.y), glm.vec2(uvb.x, uvb.y), glm.vec2(0.0, 0.0)
            )
            for (uva, uvb) in self.segment_uv
        ]
        assert self.node_id is not None
        self.geom_id = rc.geometry_buffer.add_line3d(
            self.vertex_indices[0],
            len(self.vertex_list),
            self.segment_idx[0],
            self.node_id,
            self.material_id,
        )
