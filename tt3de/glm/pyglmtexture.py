import array
import itertools
from math import exp
import math
from typing import Iterable, List, Tuple

from tt3de.tt3de import (
    
    Drawable3D,
    
    Point3D,
)
import glm
from glm import array as glma, i32vec2, ivec2, ivec3, mat3, mat4, vec2
from glm import vec3, vec4

from tt3de.utils import GLMTexturecoord, GLMTriangle
from tt3de.glm_camera import GLMCamera



def glmtriangle_as_square(
    tri: glm.mat3, screen_width, screen_height
) -> Iterable[tuple[int, int]]:
    adjoint = glm.determinant(tri) * glm.inverse(tri)

    xclamped = glm.clamp(glm.row(tri, 0), 0, screen_width)
    yclamped = glm.clamp(glm.row(tri, 1), 0, screen_height)
    minx = glm.min(xclamped)
    maxx = glm.max(xclamped)

    miny = glm.min(yclamped)
    maxy = glm.max(yclamped)
    minyi, maxyi = round(miny), round(maxy)

    maxxi = round(maxx)
    minxi = round(minx)
    for xi in range(minxi, maxxi + 1):
        if xi == minxi or xi == maxxi:
            for yi in range(minyi, maxyi + 1):
                yield (xi, yi)
        else:
            yield (xi, minyi)
            yield (xi, maxyi)


class GLMMesh3D():
    def __init__(self):
        self.vertices: List[Point3D] = []
        self.texture_coords: List[List[GLMTexturecoord]] = [[] for _ in range(8)]
        self.normals: List[Point3D] = []
        self.triangles: List[Point3D] = []
        self.material_id: int = 0

    def cache_output(self, segmap):

        self.glm_vertices_4: glm.array[vec4] = glma(
            [vec4(p.x, p.y, p.z, 1.0) for p in self.vertices]
        )

        self.glm_vertices = glma([vec3(p.x, p.y, p.z) for p in self.vertices])
        self.glm_normals = glma(
            [vec3(t.normal.x, t.normal.y, t.normal.z) for t in self.triangles]
        )

        uvfiller = [0.0] * 42
        self.c_code_uvmap = [
            [
                list(itertools.chain(*[(1.0 - uv.y, uv.x) for uv in uvlayer]))
                + uvfiller
                for uvlayer in t.uvmap
            ]
            for t in self.triangles
        ]
        # self.glm_uvmap = [[[glm.vec2(uv.x,uv.y) for uv in uvlayer] for uvlayer in t.uvmap] ]
