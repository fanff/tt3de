from types import TracebackType
from typing import Any, List, Optional
import glm
from typing_extensions import Self

from tt3de.glm.pyglmtexture import GLMCamera
from tt3de.utils import (
    p2d_uv_tomatrix,
    p3d_tovec3,
    p3d_tovec4,
    p3d_triplet_to_matrix,
    random_node_id,
)


class TT2DNode:
    def __init__(self, name: str = None, transform: Optional[glm.mat3] = None):
        self.name = name if name is not None else random_node_id()
        self.elements: List[TT2DNode] = []
        self.local_transform = transform if transform is not None else glm.mat4(1.0)
        

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


class TT2DMesh(TT2DNode):

    def __init__(
        self, name: str = None, transform: Optional[glm.mat3] = None, material_id=0
    ):
        super().__init__(name=name, transform=transform)
        self.elements = []
        self.uvmap = []
        self.material_id = material_id

    def cache_output(self, segmap):

        self.glm_elements = [
            [p3d_tovec3(a), p3d_tovec3(b), p3d_tovec3(c)]
            for (a, b, c) in (self.elements)
        ]

        self.glm_elements_4 = [
            [p3d_tovec4(a), p3d_tovec4(b), p3d_tovec4(c)]
            for (a, b, c) in (self.elements)
        ]

    def draw(self, camera: GLMCamera, geometry_buffer, model_matrix=None, node_id=0):
        if model_matrix is not None:
            _model_matrix = model_matrix * self.local_transform
        else:
            _model_matrix = self.local_transform
        #screen_scaling_matrix: glm.mat3x3 = camera.view_matrix_2D * _model_matrix


        vpmatrix = camera.update_2d_perspective()
        tr = vpmatrix*_model_matrix

        for faceidx, facepoints in enumerate(self.glm_elements_4):
            a, b, c = facepoints

            a = tr * a
            b = tr * b
            c = tr * c
            deptha = a.z
            depthb = b.z
            depthc = c.z

            #a = a / a.z
            #b = b / b.z
            #c = c / c.z

            a = [a.x, a.y, a.z]
            b = [b.x, b.y, b.z]
            c = [c.x, c.y, c.z]
            uva, uvb, uvc = self.uvmap[faceidx]

            uvs = [uva.x, uva.y, uvb.x, uvb.y, uvc.x, uvc.y] + [0.0] * 42
            geometry_buffer.add_triangle_to_buffer(
                a, b, c, uvs, node_id, self.material_id  # uv list  # node_id
            )

        return     
        for faceidx, trimat in enumerate(self.glm_elements):
            a, b, c = trimat

            a = screen_scaling_matrix * a
            b = screen_scaling_matrix * b
            c = screen_scaling_matrix * c
            deptha = a.z
            depthb = b.z
            depthc = c.z

            #a = a / a.z
            #b = b / b.z
            #c = c / c.z

            a = [a.x, a.y, deptha]
            b = [b.x, b.y, depthb]
            c = [c.x, c.y, depthc]
            uva, uvb, uvc = self.uvmap[faceidx]

            uvs = [uva.x, uva.y, uvb.x, uvb.y, uvc.x, uvc.y] + [0.0] * 42
            geometry_buffer.add_triangle_to_buffer(
                a, b, c, uvs, node_id, self.material_id  # uv list  # node_id
            )
