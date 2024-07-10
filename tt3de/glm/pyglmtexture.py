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



def yvalue_from_adjoint_unprotected(adj_matrix: glm.mat3, side, x):
    a, b, c = glm.row(adj_matrix, side)
    alpha = -a / b
    intercept = -c / b
    return alpha * x + intercept


def line_equation_from_adjoint(adj_matrix: glm.mat3, side, x):
    a, b, c = glm.row(adj_matrix, side)

    CONST = 0.001
    if abs(b) > CONST:  # Vertical line case
        alpha = -a / b
        intercept = -c / b
        return alpha * x + intercept


def glm_triangle_vertex_pixels(
    tri: GLMTriangle, screen_width, screen_height
) -> Iterable[tuple[int, int]]:
    for i in range(3):
        point2f = glm.column(tri, i).xy
        xi = round(point2f.x)
        yi = round(point2f.y)
        if xi >= 0 and xi < screen_width and yi >= 0 and yi < screen_height:
            yield xi, yi


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

def barycentric_coordinates(
    a: glm.vec3, b: glm.vec3, c: glm.vec3, p: glm.vec3
) -> glm.vec3:
    """
    Calculates the barycentric coordinates of point p with respect to the triangle defined by points a, b, and c.

    Args:
        a (glm.vec3): Vertex A of the triangle.
        b (glm.vec3): Vertex B of the triangle.
        c (glm.vec3): Vertex C of the triangle.
        p (glm.vec3): Point P to calculate the barycentric coordinates for.

    Returns:
        glm.vec3: The barycentric coordinates (u, v, w) of point P.
    """

    v0 = b - a
    v1 = c - a
    v2 = p - a

    d00 = glm.dot(v0, v0)
    d01 = glm.dot(v0, v1)
    d11 = glm.dot(v1, v1)
    d20 = glm.dot(v2, v0)
    d21 = glm.dot(v2, v1)

    denom = d00 * d11 - d01 * d01

    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w

    return glm.vec3(u, v, w)


class GLMNode3D(Drawable3D):
    def __init__(self):
        self.local_translate: vec3 = vec3(0.0, 0.0, 0.0)
        self.local_transform: mat4 = mat4(1.0)
        self.elems: list[GLMMesh3D] = []

    def set_transform(self, t: mat4):
        self.local_transform = t

    def draw(self, camera: GLMCamera, *args) -> Iterable[object]:

        cpos = camera.pos
        cmod = camera.view_matrix_3D

        # move the camera
        camera.view_matrix_3D = camera.view_matrix_3D * self.local_transform

        for element_idx, element in enumerate(self.elems):
            element.draw(camera, *args)
        # reset the camera
        camera.pos = cpos
        camera.view_matrix_3D = cmod

    def render_point(self, some_info):
        (otherinfo, element) = some_info
        return element.render_point(otherinfo)

    def cache_output(self, segmap):
        for e in self.elems:
            e.cache_output(segmap)
