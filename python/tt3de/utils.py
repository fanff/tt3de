# -*- coding: utf-8 -*-

from pyglm import glm


from tt3de.points import Point2D, Point3D
import random
import string


def p2d_tovec2(p: Point2D) -> glm.vec2:
    return glm.vec2(p.x, p.y)


def vec3_str(v) -> str:
    return f"vec3({v.x:.2f},{v.y:.2f},{v.z:.2f})"


def p3d_tovec3(p: Point3D) -> glm.vec3:
    return glm.vec3(p.x, p.y, p.z)


def p3d_tovec4(p: Point3D) -> glm.vec4:
    return glm.vec4(p.x, p.y, p.z, 1.0)


def p3d_triplet_to_matrix(ps: tuple[Point3D, Point3D, Point3D]) -> glm.mat3:
    a, b, c = ps

    return glm.mat3(p3d_tovec3(a), p3d_tovec3(b), p3d_tovec3(c))


def mat_from_axis_angle(axis, angle):
    return glm.rotate(angle, axis)


def clampi(x, minx, maxx):
    return min(maxx, max(x, minx))


def random_node_id(length=16) -> str:
    """
    Generate a random node ID with the specified length.

    Args:
        length (int): The length of the node ID to generate. Default is 16.

    Returns:
        str: A randomly generated node ID.
    """
    hex_chars = string.hexdigits[:-6]  # '0123456789abcdef'
    return "".join(random.choice(hex_chars) for _ in range(length))
