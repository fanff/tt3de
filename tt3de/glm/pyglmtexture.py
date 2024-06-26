import array
import itertools
from math import exp
import math
from typing import Iterable, List, Tuple
from tt3de.asset_load import extract_palette
from tt3de.glm.triangle_clipping import (
    Triangle,
    clip_triangle_in_planes,
    clipping_space_planes,
    extract_planes,
    is_front_facing,
)
from tt3de.richtexture import ImageTexture, Segmap, StaticTexture, TextureAscii
from tt3de.tt3de import (
    Camera,
    Drawable3D,
    FPSCamera,
    Line3D,
    Mesh3D,
    Node3D,
    PPoint2D,
    Point2D,
    Point3D,
    PointElem,
    TextureCoordinate,
    TextureTT3DE,
    Triangle3D,
)
from rich.color import Color
from rich.style import Style
from rich.text import Segment
from textual.strip import Strip

import glm
from glm import array as glma, i32vec2, ivec2, ivec3, mat3, mat4, vec2
from glm import quat
from glm import vec3, vec4

from tt3de.utils import GLMTexturecoord, GLMTriangle


class GLMCamera:
    def __init__(
        self,
        pos: Point3D,
        screen_width: int = 100,
        screen_height: int = 100,
        fov_radians=math.radians(80),
        dist_min=1,
        dist_max=100,
        character_factor=1.8,
    ):
        self.pos = glm.vec3(pos.x, pos.y, pos.z)

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.pitch = 0
        self.yaw = 0

        self.fov_radians = fov_radians
        self.dist_min = dist_min
        self.dist_max = dist_max
        self.character_factor = character_factor

        self.zoom_2D = 1.0

        self.view_matrix_2D = glm.scale(glm.vec2(self.character_factor, 1.0))

        self.perspective: glm.mat4 = glm.mat4(1.0)
        self._rotation: glm.mat4 = glm.mat4(1.0)
        self.update_rotation()
        self.update_perspective()
        self.update_2d_perspective()

    def recalc_fov_h(self, w, h):
        if self.screen_width != w or self.screen_height != h:
            self.screen_width = w
            self.screen_height = h
            self.update_perspective()
            self.update_2d_perspective()

    def set_projectioninfo(
        self,
        fov_radians: float = None,
        dist_min: float = None,
        dist_max: float = None,
        character_factor: float = None,
    ):

        if fov_radians is not None:
            self.fov_radians = fov_radians
        if dist_min is not None:
            self.dist_min = dist_min
        if dist_max is not None:
            self.dist_max = dist_max
        if character_factor is not None:
            self.character_factor = character_factor

        self.update_perspective()
        self.update_2d_perspective()

    def update_perspective(self):

        w, h = self.screen_width, self.screen_height * self.character_factor

        self.perspective = glm.perspectiveFovZO(
            (self.fov_radians * h) / w, w, h, self.dist_min, self.dist_max
        )

    def update_2d_perspective(self):
        """ """
        # TODO depending on mode it can be different here.
        min_screen_ = min(self.screen_width, self.screen_height) * self.zoom_2D

        scale_x = min_screen_ * self.character_factor
        scale_y = min_screen_

        self.view_matrix_2D = glm.translate(
            glm.vec3(self.screen_width / 2, self.screen_height / 2, 0.0)
        ) * glm.scale(glm.vec3(scale_x, scale_y, 1.0))

    def set_zoom_2D(self, zoom=1.0):
        self.zoom_2D = zoom
        self.update_2d_perspective()

    def move(self, delta: glm.vec3):
        self.pos += delta
        self.update_rotation()

    def move_at(self, pos: glm.vec3):
        self.pos = pos
        self.update_rotation()

    def move_side(self, dist: float):
        self.pos += glm.cross(self.direction_vector(), glm.vec3(0, 1, 0)) * dist
        self.update_rotation()

    def move_forward(self, dist: float):
        self.pos -= self.direction_vector() * dist
        self.update_rotation()

    def rotate_left_right(self, angle: float):
        self.yaw -= angle
        self.update_rotation()

    def rotate_up_down(self, angle: float):
        self.pitch = self.pitch + angle
        self.update_rotation()

    def set_yaw_pitch(self, yaw: float, pitch: float):
        self.yaw = yaw
        self.pitch = pitch
        self.update_rotation()

    def update_rotation(self):
        # pitch is around x axis , yaw is around y axis
        self._rotation = glm.rotate(self.yaw, glm.vec3(0, 1, 0)) * glm.rotate(
            self.pitch, glm.vec3(1, 0, 0)
        )

        self.recalc_model_inverse()

    def recalc_model_inverse(self):
        self._model_inverse = glm.inverse(self._rotation) * glm.translate(-self.pos)

    def project(
        self, point: glm.vec3, perspective: glm.mat4x4, screen_info=glm.vec4(0, 0, 1, 1)
    ) -> glm.vec3:

        return glm.projectZO(point, self._model_inverse, perspective, screen_info)

    def point_at(self, target: glm.vec3):
        direction = target - self.pos
        self.yaw = glm.atan(
            direction.x, direction.z
        )  # math.atan2(direction.x, direction.z)
        self.pitch = glm.atan(-direction.y, glm.length(direction.xz))

        self.update_rotation()

    def direction_vector(self) -> glm.vec3:
        # directional vector extracted from the matrix
        return glm.row(self._model_inverse, 2).xyz

    def __str__(self):
        return f"GLMCamera({self.pos,self.direction_vector()},yaw={self.yaw},pitch={self.pitch})"

    def __repr__(self):
        return str(self)


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


class GLMMesh3D(Mesh3D):
    def __init__(self):
        self.vertices: List[Point3D] = []
        self.texture_coords: List[List[GLMTexturecoord]] = [[] for _ in range(8)]
        self.normals: List[Point3D] = []
        self.triangles: List[Triangle3D] = []
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

    def proj_vertices(
        self, camera: GLMCamera, perspective_matrix, screen_width, screen_height
    ):
        screeninfo = glm.vec4(0, 0, 1, 1)

        proj_vertices = [
            glm.projectZO(v, camera._model_inverse, perspective_matrix, screeninfo)
            for v in self.glm_vertices
        ]

        vert_camera = self.glm_vertices - camera.pos
        vert_camera_dist = vert_camera.map(glm.length)

        # vert_camera_dist = [0]*len(self.glm_vertices)
        for pa, pb, pc in self.triangles_vindex:
            rp1 = proj_vertices[pa]
            rp2 = proj_vertices[pb]
            rp3 = proj_vertices[pc]

            dist1 = vert_camera_dist[pa]
            dist2 = vert_camera_dist[pb]
            dist3 = vert_camera_dist[pc]

            # yield ((rp1,vec4(0.0,0.0,0.0,dist1)),
            #       (rp2,vec4(0.0,0.0,0.0,dist2)),
            #       (rp3,vec4(0.0,0.0,0.0,dist3)))
            yield ((rp1, (dist1)), (rp2, (dist2)), (rp3, (dist3)))

    def draw(self, camera: GLMCamera, geometry_buffer, node_id=0):

        screen_width, screen_height = camera.screen_width, camera.screen_height
        perspective_matrix = camera.perspective

        view_port_matrix = glm.scale(
            vec3(float(screen_width) / 2.0, float(screen_height) / 2.0, 1.0)
        ) * glm.translate(vec3(1, 1, 0.0))
        # in_view_space = [camera._model_inverse * glm.vec4(vertex, 1.0) for vertex in self.glm_vertices]
        view_space_vertices = [
            (camera._model_inverse) * vertex for vertex in self.glm_vertices_4
        ]

        triangle_in_clip_space = [
            perspective_matrix * vertex for vertex in view_space_vertices
        ]

        triangle_in_clip_space_divided = [
            vertex / vertex.w for vertex in triangle_in_clip_space
        ]

        # keep an inversion for the whole transform :
        inverse_perspective = glm.inverse(perspective_matrix * camera._model_inverse)
        plane_of_the_clip_space = clipping_space_planes()

        for triangle_idx, (v_idx1, v_idx2, v_idx3) in enumerate(self.triangles_vindex):
            v_in_clip_space1 = triangle_in_clip_space_divided[v_idx1]
            v_in_clip_space2 = triangle_in_clip_space_divided[v_idx2]
            v_in_clip_space3 = triangle_in_clip_space_divided[v_idx3]

            v_in_view_space1 = view_space_vertices[v_idx1]
            v_in_view_space2 = view_space_vertices[v_idx2]
            v_in_view_space3 = view_space_vertices[v_idx3]

            v_in_clip_space_undiv_1 = triangle_in_clip_space[v_idx1]
            v_in_clip_space_undiv_2 = triangle_in_clip_space[v_idx2]
            v_in_clip_space_undiv_3 = triangle_in_clip_space[v_idx3]

            # perform a rejection test, if the triangle is like "all outside of the same plane. "
            a_triangle_in_clip_spance_not_divided = [
                v_in_clip_space_undiv_1,
                v_in_clip_space_undiv_2,
                v_in_clip_space_undiv_3,
            ]
            a_clip_space_test = []
            for vertice_in_clip_space in a_triangle_in_clip_spance_not_divided:
                sometest = [
                    -vertice_in_clip_space.w < vertice_in_clip_space.x,
                    vertice_in_clip_space.x < vertice_in_clip_space.w,
                    -vertice_in_clip_space.w < vertice_in_clip_space.y,
                    vertice_in_clip_space.y < vertice_in_clip_space.w,
                    -vertice_in_clip_space.w < vertice_in_clip_space.z,
                    vertice_in_clip_space.z < vertice_in_clip_space.w,
                ]

                a_clip_space_test.append(sometest)
            clipe_space_rejection = [
                not (a_clip_space_test[0][plane_idx])
                and not (a_clip_space_test[1][plane_idx])
                and not (a_clip_space_test[2][plane_idx])
                for plane_idx in range(6)
            ]
            # if any of the clip_space_rejection is True, it means that ALL vertices of the triangles are on the outside of this plane.
            if any(clipe_space_rejection):
                continue

            triangle: Triangle = [v_in_clip_space1, v_in_clip_space2, v_in_clip_space3]

            clipped_triangles = clip_triangle_in_planes(
                triangle, plane_of_the_clip_space
            )
            for sub_triangle in clipped_triangles:

                # lend in pixel coord
                pixwin_coord = [view_port_matrix * (vertex) for vertex in sub_triangle]

                if is_front_facing(pixwin_coord):
                    a, b, c = pixwin_coord
                else:
                    a, c, b = pixwin_coord

                min_window_space = vec3(0, 0, -float("infinity"))
                max_window_space = vec3(
                    screen_width - 1, screen_height - 1, float("infinity")
                )

                a = glm.clamp(vec3(a.xyz), min_window_space, max_window_space)
                b = glm.clamp(vec3(b.xyz), min_window_space, max_window_space)
                c = glm.clamp(vec3(c.xyz), min_window_space, max_window_space)
                a = [a.x, a.y, a.z]
                b = [b.x, b.y, b.z]
                c = [c.x, c.y, c.z]

                geometry_buffer.add_triangle_to_buffer(
                    a, b, c, [0.0] * 48, node_id, self.material_id  # uv list  # node_id
                )  # material_id


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
        cmod = camera._model_inverse

        # move the camera
        camera._model_inverse = camera._model_inverse * self.local_transform

        for element_idx, element in enumerate(self.elems):
            element.draw(camera, *args)
        # reset the camera
        camera.pos = cpos
        camera._model_inverse = cmod

    def render_point(self, some_info):
        (otherinfo, element) = some_info
        return element.render_point(otherinfo)

    def cache_output(self, segmap):
        for e in self.elems:
            e.cache_output(segmap)
