from enum import Enum
from glm import ivec2, mat3, quat, vec2, vec3, vec4
import glm

from tt3de.tt3de import Point2D, Point3D


def p2d_tovec2(p: Point2D) -> vec2:
    return vec2(p.x, p.y)


def p2d_uv_tomatrix(ps: tuple[Point2D, Point2D, Point2D]) -> glm.mat3x2:
    return glm.mat3x2(p2d_tovec2(ps[0]), p2d_tovec2(ps[1]), p2d_tovec2(ps[2]))


def vec3_str(v) -> str:
    return f"vec3({v.x:.2f},{v.y:.2f},{v.z:.2f})"


def p3d_tovec3(p: Point3D) -> vec3:
    return vec3(p.x, p.y, p.z)


def p3d_tovec4(p: Point3D) -> vec4:
    return vec4(p.x, p.y, p.z, 1.0)


def p3d_triplet_to_matrix(ps: tuple[Point3D, Point3D, Point3D]) -> mat3:
    a, b, c = ps

    return mat3(p3d_tovec3(a), p3d_tovec3(b), p3d_tovec3(c))


def mat_from_axis_angle(axis, angle):
    return glm.rotate(angle, axis)


def clampi(x, minx, maxx):
    return min(maxx, max(x, minx))


GLMTexturecoord = glm.vec2
GLMTriangle = glm.mat3
IVEC2_YES = ivec2(1, 1)
VEC3_YES = vec3(1.0, 1.0, 1.0)
VEC3_ZERO = vec3(0.0, 0.0, 0.0)


class TT3DEMaterialMode(Enum):
    DO_NOTHING = 0
    DEBUG = 1
    STATIC_FRONT_ALBEDO = 2
    STATIC_BACK_ALBEDO = 3
    STATIC_GLYPH = 4
    STATIC_ALL = 5
    DEBUG_WEIGHTS = 6
    DEBUG_DEPTH_BUFFER = 7
    BACK_DEPTH_SHADING = 8
    UV_MAPPING_DEBUG = 9
    UV_MAPPING_TEXT1 = 10
    DEBUG_DOUBLE_WEIGHTS = 11
    DEBUG_DOUBLE_UV = 12
    DOUBLE_UV_MAPPING_TEXT1 = 13
    DOUBLE_PERLIN_NOISE = 14

class TT3DEMaterialTextureMappingOptions:
    def __init__(self):
        self._bits = 0

    def _set_bit(self, position, value):
        if value:
            self._bits |= (1 << position)
        else:
            self._bits &= ~(1 << position)

    def _get_bit(self, position):
        return (self._bits >> position) & 1

    @property
    def texture_mapping_repetition(self):
        return self._get_bit(0)

    @texture_mapping_repetition.setter
    def texture_mapping_repetition(self, value):
        self._set_bit(0, value)

    @property
    def texture_transparency_mode(self):
        return self._get_bit(1)

    @texture_transparency_mode.setter
    def texture_transparency_mode(self, value):
        self._set_bit(1, value)

    @property
    def specular_reflection(self):
        return self._get_bit(2)

    @specular_reflection.setter
    def specular_reflection(self, value):
        self._set_bit(2, value)

    @property
    def normal_mapping(self):
        return self._get_bit(3)

    @normal_mapping.setter
    def normal_mapping(self, value):
        self._set_bit(3, value)

    @property
    def emission(self):
        return self._get_bit(4)

    @emission.setter
    def emission(self, value):
        self._set_bit(4, value)

    @property
    def double_sided_rendering(self):
        return self._get_bit(5)

    @double_sided_rendering.setter
    def double_sided_rendering(self, value):
        self._set_bit(5, value)

    @property
    def alpha_blending(self):
        return self._get_bit(6)

    @alpha_blending.setter
    def alpha_blending(self, value):
        self._set_bit(6, value)

    @property
    def ambient_occlusion(self):
        return self._get_bit(7)

    @ambient_occlusion.setter
    def ambient_occlusion(self, value):
        self._set_bit(7, value)

    def get_value(self):
        return self._bits

import random
import string


def random_node_id(length=16) -> str:
    """Generate a random node ID with the specified length.

    Args:
        length (int): The length of the node ID to generate. Default is 16.

    Returns:
        str: A randomly generated node ID.
    """
    hex_chars = string.hexdigits[:-6]  # '0123456789abcdef'
    return "".join(random.choice(hex_chars) for _ in range(length))
