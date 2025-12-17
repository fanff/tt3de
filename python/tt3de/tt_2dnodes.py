# -*- coding: utf-8 -*-
import math
from typing import List, Optional, Tuple

from pyglm import glm

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tt3de.render_context_rust import RustRenderContext

from tt3de.points import Point2D, Point3D
from tt3de.utils import (
    p2d_tovec2,
    random_node_id,
)


class TreeNode:
    def __init__(self, name: str | None = None):
        self.name: str = name if name is not None else random_node_id()
        self.elements: List[TreeNode] = []

        # will be set when added to a parent node
        self.parent: TreeNode = None
        self.rc: "RustRenderContext" = None

    def add_child(self, child: "TreeNode"):
        """
        Adds a child element to the list of elements.

        Args:
            child: The child element to be added.
        """
        child.parent = self
        self.elements.append(child)

    def parent_chain_iterator(self):
        current = self.parent
        while current is not None:
            yield current
            current = current.parent


class DirtyProcessor:
    def sync_in_context(self, rc: "RustRenderContext"):
        pass


class Transform2DMixin:
    """
    Mixin that assumes the class has:
        self.local_transform: glm.mat4
    and provides position / rotation / scale properties.

    No extra storage: everything lives in the mat4.
    """

    # --- Position ---------------------------------------------------------
    @property
    def position(self) -> glm.vec3:
        t = self.local_transform
        return glm.vec3(t[3].x, t[3].y, t[3].z)

    @position.setter
    def position(self, value: glm.vec3) -> None:
        t = self.local_transform
        t[3].x = value.x
        t[3].y = value.y
        t[3].z = value.z
        self.local_transform = t
        self.global_transform_dirty = True

    @property
    def scale(self) -> glm.vec2:
        m = self.local_transform
        # lengths of the basis vectors (first two columns)
        sx = glm.length(glm.vec2(m[0].x, m[0].y))
        sy = glm.length(glm.vec2(m[1].x, m[1].y))
        return glm.vec2(sx, sy)

    @scale.setter
    def scale(self, value: glm.vec2) -> None:
        m = self.local_transform
        angle = self.rotation  # keep current rotation
        c, s = math.cos(angle), math.sin(angle)

        # rebuild first two columns from rotation * scale (no shear)
        m[0].x = value.x * c
        m[0].y = value.x * s
        m[1].x = -value.y * s
        m[1].y = value.y * c

        self.local_transform = m
        self.global_transform_dirty = True

    @property
    def rotation(self) -> float:
        """Rotation in Radians."""
        m = self.local_transform
        # assuming no shear; extract angle from first column
        return math.atan2(m[0].y, m[0].x)

    @rotation.setter
    def rotation(self, angle: float) -> None:
        m = self.local_transform
        scale = self.scale  # keep current scale
        c, s = math.cos(angle), math.sin(angle)

        m[0].x = scale.x * c
        m[0].y = scale.x * s
        m[1].x = -scale.y * s
        m[1].y = scale.y * c

        self.local_transform = m
        self.global_transform_dirty = True


class TT2DNode(TreeNode, DirtyProcessor, Transform2DMixin):
    def __init__(self, name: str | None = None, transform: Optional[glm.mat4] = None):
        super().__init__(name=name)

        self.local_transform: glm.mat4 = (
            transform if transform is not None else glm.mat4(1.0)
        )

        self.global_transform_dirty: bool = True
        self.global_transform_matrix: glm.mat4 = self.local_transform

        # will be set when inserted in the render context
        self.node_id: int | None = None
        # will be set when added to a parent node
        # declared here for type checking purposes
        self.elements: List[TT2DNode] = []
        self.parent: TT2DNode = None

    def add_child(self, child: "TT2DNode"):  # type: ignore
        """
        Adds a child element to the list of elements.

        Args:
            child: The child element to be added.
        """
        # call the super add_child to set the parent
        super().add_child(child)
        child.global_transform_dirty = True

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

    def get_position(self) -> glm.vec3:
        pos_vec = self.global_transform_matrix[3]
        return glm.vec3(pos_vec.x, pos_vec.y, pos_vec.z)

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

    def insert_in(
        self,
        rc: "RustRenderContext",
    ):
        self.rc = rc
        self.node_id = rc.transform_buffer.add_node_transform(
            self.global_transform_matrix
        )
        self.global_transform_dirty = True

        for e in self.elements:
            e.insert_in(rc)


class WithMaterialID(DirtyProcessor):
    def __init__(self, material_id=0, **kwargs):
        super().__init__(**kwargs)
        self.material_id = material_id
        self.dirty_material = True
        # will be set when inserted in the render context
        self.geom_id = None

    def sync_in_context(self, rc: "RustRenderContext"):
        assert isinstance(self.geom_id, int)
        if self.dirty_material:
            rc.geometry_buffer.update_geometry_material(
                self.geom_id,
                self.material_id,
            )
            self.dirty_material = False
        super().sync_in_context(rc)

    def set_material_id(self, material_id: int):
        if self.material_id != material_id:
            self.material_id = material_id
            self.dirty_material = True


class TT2DPoints(WithMaterialID, TT2DNode):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        point_list: List[Point3D] | None = None,
        material_id: int = 0,
    ):
        super().__init__(name=name, transform=transform, material_id=material_id)

        self.point_list: List[Point3D] = point_list if point_list is not None else []
        self.dirty_points = False

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)
        assert self.node_id is not None

        self.vert_idx = [
            rc.vertex_buffer.add_2d_vertex(p3d.x, p3d.y, p3d.z)
            for p3d in self.point_list
        ]
        self.allocated_verts = len(self.point_list)

        self.geom_id = rc.geometry_buffer.add_points_2d(
            self.vert_idx[0],
            self.allocated_verts,
            0,
            self.node_id,
            self.material_id,
        )


class TT2DLines(TT2DNode):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        point_list: List[Point3D] | None = None,
        segment_uv: List[Tuple[Point2D, Point2D]] | None = None,
        material_id=0,
    ):
        super().__init__(name=name, transform=transform)
        self.point_list: List[Point3D] = point_list if point_list is not None else []
        self.segment_uv: List[Tuple[Point2D, Point2D]] = (
            segment_uv
            if segment_uv is not None
            else [
                (Point2D(0.0, 0.0), Point2D(1.0, 1.0))
                for _ in range(len(self.point_list) - 1)
            ]
        )
        self.material_id = material_id

        # will be set when inserted in the render context
        self.geom_id = None
        self.vertex_indices: List[int] = []

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)
        assert self.node_id is not None
        # insert all points as vertices
        self.vertex_indices = [
            rc.vertex_buffer.add_2d_vertex(p3d.x, p3d.y, p3d.z)
            for p3d in self.point_list
        ]
        self.segment_idx = [
            rc.vertex_buffer.add_uv(
                glm.vec2(uva.x, uva.y), glm.vec2(uvb.x, uvb.y), glm.vec2(0.0, 0.0)
            )
            for (uva, uvb) in self.segment_uv
        ]

        self.geom_id = rc.geometry_buffer.add_line2d(
            self.vertex_indices[0],
            len(self.point_list),
            self.segment_idx[0],
            self.node_id,
            self.material_id,
        )


class TT2DPolygon(WithMaterialID, TT2DNode):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        point_list: List[Point3D] | None = None,
        triangles: List[Tuple[int, int, int]] | None = None,
        uvmap: List[Tuple[Point2D, Point2D, Point2D]] | None = None,
        material_id=0,
    ):
        super().__init__(name=name, transform=transform, material_id=material_id)

        self.vertex_list: List[Point3D] = point_list if point_list is not None else []
        self.triangles: List[Tuple[int, int, int]] = (
            triangles if triangles is not None else []
        )
        self.uvmap: List[Tuple[Point2D, Point2D, Point2D]] = (
            uvmap if uvmap is not None else []
        )
        # will be set when inserted in the render context
        self.geom_id = None

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)
        assert self.node_id is not None

        # add all points as vertices
        self.vertex_indices = [
            rc.vertex_buffer.add_2d_vertex(p3d.x, p3d.y, p3d.z)
            for p3d in self.vertex_list
        ]

        # insert all triangles
        triangle_count = len(self.triangles)
        assert triangle_count == len(self.uvmap)
        start_uv = None
        triangle_start = None
        for triangle_idx, ((uva, uvb, uvc), (idx_a, idx_b, idx_c)) in enumerate(
            zip(self.uvmap, self.triangles)
        ):
            normal = glm.vec3(0, 0, 1)
            uv_idx, triangle_idx = rc.vertex_buffer.add_3d_triangle(
                self.vertex_indices[idx_a],
                self.vertex_indices[idx_b],
                self.vertex_indices[idx_c],
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

        self.geom_id = rc.geometry_buffer.add_polygon2d(
            self.vertex_indices[0],
            len(self.vertex_indices),
            start_uv,
            triangle_start,
            triangle_count,
            self.node_id,
            self.material_id,
        )


class TT2DUnitSquare(TT2DPolygon):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        material_id=0,
        centered: bool = False,
    ):
        shift = Point3D(-0.5, -0.5, 0.0) if centered else Point3D(0.0, 0.0, 0.0)
        super().__init__(
            name=name,
            transform=transform,
            point_list=[
                Point3D(0.0, 0.0, 0.0) + shift,
                Point3D(1.0, 0.0, 0.0) + shift,
                Point3D(1.0, 1.0, 0.0) + shift,
                Point3D(0.0, 1.0, 0.0) + shift,
            ],
            triangles=[(0, 1, 2), (2, 3, 0)],
            uvmap=[
                (Point2D(0.0, 0.0), Point2D(1.0, 0.0), Point2D(1.0, 1.0)),
                (Point2D(1.0, 1.0), Point2D(0.0, 1.0), Point2D(0.0, 0.0)),
            ],
            material_id=material_id,
        )


class TT2DRect(TT2DNode):
    def __init__(
        self,
        name: str | None = None,
        transform: Optional[glm.mat4] = None,
        width: float = 1.0,
        height: float = 1.0,
        material_id=0,
    ):
        super().__init__(name=name, transform=transform)

        self.width = width
        self.height = height
        self.material_id = material_id

        # will be set when inserted in the render context
        self.geom_id = None
        self.vertex_indices: List[int] = []

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)
        assert self.node_id is not None
        # add rectangle vertices
        self.vertex_indices = []
        for x, y in [(0, 0), (self.width, self.height)]:
            vertex_idx = rc.vertex_buffer.add_2d_vertex(x, y, 0.0)
            self.vertex_indices.append(vertex_idx)

        uv_start_index = rc.vertex_buffer.add_uv(
            glm.vec2(0, 0), glm.vec2(1, 1), glm.vec2(0.0, 0.0)
        )

        self.geom_id = rc.geometry_buffer.add_rect2d(
            self.vertex_indices[0],
            uv_start_index,
            self.node_id,
            self.material_id,
        )
