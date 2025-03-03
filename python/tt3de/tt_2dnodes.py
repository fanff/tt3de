import itertools
from types import TracebackType
from typing import Any, List, Optional

import glm
from typing_extensions import Self

from tt3de.glm_camera import GLMCamera
from tt3de.points import Point2D, Point3D
from tt3de.render_context_rust import RustRenderContext
from tt3de.utils import (
    p2d_tovec2,
    p2d_uv_tomatrix,
    p3d_tovec3,
    p3d_tovec4,
    p3d_triplet_to_matrix,
    random_node_id,
)


class TT2DNode:
    def __init__(self, name: str = None, transform: Optional[glm.mat4] = None):
        self.name = name if name is not None else random_node_id()
        self.elements: List[TT2DNode] = []
        self.local_transform: glm.mat4 = (
            transform if transform is not None else glm.mat4(1.0)
        )
        self.node_id = None

    def cache_output(self, segmap):
        for e in self.elements:
            e.cache_output(segmap)

    def draw(self, camera: GLMCamera, geometry_buffer, model_matrix=None):
        if model_matrix is not None:
            _model_matrix = model_matrix * self.local_transform
        else:
            _model_matrix = self.local_transform
        for elem in self.elements:
            elem.draw(camera, geometry_buffer, _model_matrix)

    def add_child(self, child: "TT2DNode"):
        """Adds a child element to the list of elements.

        Args:
            child: The child element to be added.
        """
        self.elements.append(child)

    def insert_in(self, rc: "RustRenderContext", parent_transform: Optional[glm.mat4]):
        # self.node_id = rc.transform_buffer.add_node_transform(self.local_transform)
        if parent_transform:
            fff = parent_transform * self.local_transform
        else:
            fff = self.local_transform
        for e in self.elements:
            e.insert_in(rc, fff)


class TT2DMesh(TT2DNode):
    def __init__(
        self, name: str = None, transform: Optional[glm.mat3] = None, material_id=0
    ):
        super().__init__(name=name, transform=transform)
        self.elements = []
        self.uvmap: List[tuple[Point2D, Point2D, Point2D]] = []
        self.material_id = material_id
        self.node_id = None

    def cache_output(self, segmap):
        self.glm_elements = [
            [p3d_tovec3(a), p3d_tovec3(b), p3d_tovec3(c)]
            for (a, b, c) in (self.elements)
        ]

        self.glm_elements_4 = [
            [p3d_tovec4(a), p3d_tovec4(b), p3d_tovec4(c)]
            for (a, b, c) in (self.elements)
        ]

        import itertools

        self.uvmap_prepared = itertools.chain(
            [
                [pa.x, pa.y, pb.x, pb.y, pc.x, pc.y]
                for face_idx, (pa, pb, pc) in enumerate(self.uvmap)
            ]
        )

    def draw(self, camera: GLMCamera, geometry_buffer, model_matrix=None, node_id=0):
        if model_matrix is not None:
            _model_matrix = model_matrix * self.local_transform
        else:
            _model_matrix = self.local_transform
        tr = camera.view_matrix_2D * _model_matrix

        for faceidx, facepoints in enumerate(self.glm_elements_4):
            a, b, c = facepoints

            a = tr * a
            b = tr * b
            c = tr * c

            a = [a.x, a.y, a.z]
            b = [b.x, b.y, b.z]
            c = [c.x, c.y, c.z]
            uva, uvb, uvc = self.uvmap[faceidx]

            face_uv = [uva.x, uva.y, uvb.x, uvb.y, uvc.x, uvc.y] + [0.0] * 42
            geometry_buffer.add_triangle_to_buffer(
                a,
                b,
                c,
                face_uv,
                node_id,
                self.material_id,  # uv list  # node_id
            )


class TT2Polygon(TT2DNode):
    def __init__(
        self, name: str = None, transform: Optional[glm.mat3] = None, material_id=0
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

        rc.geometry_buffer.add_polygon(
            start_idx,
            len(self.vertex_list) - 2,
            self.node_id,
            self.material_id,
            start_uv,
        )

    def cache_output(self, segmap):
        self.uvmap_prepared = [
            [pa.x, pa.y, pb.x, pb.y, pc.x, pc.y] * 8
            for face_idx, (pa, pb, pc) in enumerate(self.uvmap)
        ]

        self.glm_elements_4 = [p3d_tovec4(v) for v in (self.vertex_list)]

    def draw(self, camera: GLMCamera, geometry_buffer, model_matrix=None, node_id=0):
        if model_matrix is not None:
            _model_matrix = model_matrix * self.local_transform
        else:
            _model_matrix = self.local_transform
        tr = camera.view_matrix_2D * _model_matrix

        transformed_vertex = (tr * vertex for vertex in (self.glm_elements_4))
        transformed_vertex = [
            [vertex.x, vertex.y, vertex.z] for vertex in transformed_vertex
        ]

        geometry_buffer.add_polygon_to_buffer(
            transformed_vertex,
            self.uvmap_prepared,
            node_id,
            self.material_id,  # uv list  # node_id
        )
