# -*- coding: utf-8 -*-
from typing import List, Optional

from pyglm import glm

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tt3de.render_context_rust import RustRenderContext

from tt3de.points import Point3D
from tt3de.utils import (
    random_node_id,
)


class TreeNode:
    def __init__(self, name: str = None):
        self.name = name if name is not None else random_node_id()
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


class TT2DNode(TreeNode):
    def __init__(self, name: str = None, transform: Optional[glm.mat4] = None):
        super().__init__(name=name)

        self.local_transform: glm.mat4 = (
            transform if transform is not None else glm.mat4(1.0)
        )
        self.global_transform_dirty: bool = True
        self.global_transform_matrix: glm.mat4 = self.local_transform

        # will be set when inserted in the render context
        self.node_id = None
        # will be set when added to a parent node
        # declared here for type checking purposes
        self.elements: List[TT2DNode] = []
        self.parent: TT2DNode = None

    def add_child(self, child: "TT2DNode"):
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

    def sync_in_context(self, rc: "RustRenderContext"):
        if self.global_transform_dirty:
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


class TT2DPoints(TT2DNode):
    def __init__(
        self,
        name: str = None,
        transform: Optional[glm.mat4] = None,
        point_list: List[Point3D] = None,
        material_id=0,
    ):
        super().__init__(name=name, transform=transform)

        self.point_list: List[Point3D] = point_list if point_list is not None else []
        self.material_id = material_id

        # will be set when inserted in the render context
        self.geom_id = None

    def insert_in(self, rc: "RustRenderContext"):
        super().insert_in(rc)

        p_start = None
        for p3d in self.point_list:
            vertex_idx = rc.vertex_buffer.add_2d_vertex(p3d.x, p3d.y, p3d.z)
            if p_start is None:
                p_start = vertex_idx

        self.geom_id = rc.geometry_buffer.add_points_2d(
            p_start,
            len(self.point_list),
            0,
            self.node_id,
            self.material_id,
        )


class TT2DRect(TT2DNode):
    def __init__(
        self,
        name: str = None,
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
