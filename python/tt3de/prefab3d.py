# -*- coding: utf-8 -*-
import math

from pyglm import glm

from tt3de.points import Point2D, Point3D
from tt3de.tt_3dnodes import TT3DLine, TT3DNode, TT3DPoint, TT3DPolygon


class Prefab3D:
    @staticmethod
    def unitary_triangle() -> TT3DPolygon:
        """Create a triangle with vertices at (0,0,1), (1,0,0), (1,1,0)"""
        vertices = [
            Point3D(0, 0, 0.0),
            Point3D(1.0, 0.0, 0.0),
            Point3D(1.0, 1.0, 0.0),
        ]
        texture_coords = (
            Point2D(0.0, 0),
            Point2D(1.0, 0.0),
            Point2D(1.0, 1.0),
        )

        m = TT3DPolygon()
        m.vertex_list = vertices
        m.triangles = [(0, 1, 2)]
        m.uvmap = [texture_coords]
        return m

    @staticmethod
    def unitary_square() -> TT3DPolygon:
        vertices = [
            Point3D(0, 0, 0.0),
            Point3D(1.0, 0.0, 0.0),
            Point3D(1.0, 1.0, 0.0),
            Point3D(0, 1.0, 0.0),
        ]

        triangles = [
            (0, 1, 2),
            (0, 2, 3),
        ]
        texture_coords = [
            (
                Point2D(0.0, 0),
                Point2D(1.0, 0.0),
                Point2D(1.0, 1.0),
            ),
            (
                Point2D(0.0, 0),
                Point2D(1.0, 1.0),
                Point2D(0.0, 1.0),
            ),
        ]

        m = TT3DPolygon()
        m.vertex_list = vertices
        m.uvmap = texture_coords
        m.triangles = triangles
        return m

    @staticmethod
    def unitary_cube(half_extent: float = 0.5) -> TT3DPolygon:
        """Axis-aligned cube centered at the origin, UV 0–1 on each face (same layout).

        Triangle winding matches ``models/cube.obj`` loaded with ``flip_triangles=True``.
        U is mirrored per face (``u → 1 - u``) so BMP/OBJ-style textures are not shown
        left–right inverted compared to the image file.

        ``half_extent`` is half the edge length (default ``0.5`` → unit cube from -0.5 to 0.5).
        """
        h = half_extent
        # Vertices: front +z, then back -z (same winding reference as ``unitary_square`` XY).
        vertices = [
            Point3D(-h, -h, h),
            Point3D(h, -h, h),
            Point3D(h, h, h),
            Point3D(-h, h, h),
            Point3D(-h, -h, -h),
            Point3D(h, -h, -h),
            Point3D(h, h, -h),
            Point3D(-h, h, -h),
        ]

        # Per-face 0–1 UV square with U mirrored (same corner labels as unmirrored layout).
        u1 = (
            Point2D(1.0, 0.0),
            Point2D(0.0, 0.0),
            Point2D(0.0, 1.0),
        )
        u2 = (
            Point2D(1.0, 0.0),
            Point2D(0.0, 1.0),
            Point2D(1.0, 1.0),
        )

        triangles = []
        uvmap = []

        def add_face(a: int, b: int, c: int, d: int) -> None:
            # Match ``cube.obj`` winding when loaded with ``flip_triangles=True``
            # (swap second/third vertex per triangle; same UV corners).
            triangles.append((a, c, b))
            uvmap.append((u1[0], u1[2], u1[1]))
            triangles.append((a, d, c))
            uvmap.append((u2[0], u2[2], u2[1]))

        # +Z front
        add_face(0, 1, 2, 3)
        # -Z back
        add_face(5, 4, 7, 6)
        # +X right
        add_face(1, 5, 6, 2)
        # -X left
        add_face(4, 0, 3, 7)
        # +Y top
        add_face(3, 2, 6, 7)
        # -Y bottom
        add_face(4, 5, 1, 0)

        m = TT3DPolygon()
        m.vertex_list = vertices
        m.triangles = triangles
        m.uvmap = uvmap
        return m

    @staticmethod
    def latlong_uv_sphere(
        radius: float = 1.0, stacks: int = 4, slices: int = 10
    ) -> TT3DPolygon:
        """Faceted UV-mapped sphere via latitude–longitude tessellation.

        Each triangle carries a single **flat (faceted) normal** — the mesh is
        appropriate for ``tt_Normal`` lighting demos where per-face normals are
        expected, not smooth per-vertex interpolation.

        **Axis convention**: Y-up, poles on ±Y.  **UV range**: [0, 1] on each
        triangle, laid out as a lat-long strip (U wraps horizontally, V from
        bottom to top pole).

        ``stacks`` must be >= 1 and ``slices`` >= 3.

        Returns a ``TT3DPolygon`` with ``(stacks + 1) * (slices + 1)`` vertices
        and ``2 * stacks * slices`` triangles.
        """
        if stacks < 1 or slices < 3:
            raise ValueError("stacks must be >= 1 and slices >= 3")
        verts: list[Point3D] = []
        for stack in range(stacks + 1):
            v = stack / stacks
            theta = v * math.pi
            st = math.sin(theta)
            ct = math.cos(theta)
            for sl in range(slices + 1):
                u = sl / slices
                phi = u * 2.0 * math.pi
                x = radius * st * math.cos(phi)
                y = radius * ct
                z = radius * st * math.sin(phi)
                verts.append(Point3D(x, y, z))

        tris: list[tuple[int, int, int]] = []
        uvs: list[tuple[Point2D, Point2D, Point2D]] = []
        for stack in range(stacks):
            for sl in range(slices):
                i0 = stack * (slices + 1) + sl
                i1 = stack * (slices + 1) + sl + 1
                i2 = (stack + 1) * (slices + 1) + sl
                i3 = (stack + 1) * (slices + 1) + sl + 1
                ua = Point2D(sl / slices, stack / stacks)
                ub = Point2D((sl + 1) / slices, stack / stacks)
                uc = Point2D(sl / slices, (stack + 1) / stacks)
                ud = Point2D((sl + 1) / slices, (stack + 1) / stacks)
                tris.append((i0, i2, i1))
                uvs.append((ua, uc, ub))
                tris.append((i1, i2, i3))
                uvs.append((ub, uc, ud))

        m = TT3DPolygon()
        m.vertex_list = verts
        m.triangles = tris
        m.uvmap = uvs
        return m

    @staticmethod
    def unitary_circle(segment_count=3) -> TT3DPolygon:
        vertices = [Point3D(0.0, 0.0, 0.0)]
        triangles = []
        texture_coords = []
        for i in range(segment_count + 1):
            angle = i * 2 * math.pi / segment_count
            next_angle = (i + 1) * 2 * math.pi / segment_count

            x = math.cos(angle)
            y = math.sin(angle)

            next_x = math.cos(next_angle)
            next_y = math.sin(next_angle)

            vertices.append(Point3D(x * 0.5, y * 0.5, 0.0))
            triangles.append([0, i + 1, ((i + 1) % segment_count) + 1])
            texture_coords.append(
                [
                    Point2D(0.5, 0.5),
                    Point2D(
                        0.5 + x / 2,
                        0.5 + y / 2,
                    ),
                    Point2D(
                        0.5 + next_x / 2,
                        0.5 + next_y / 2,
                    ),
                ]
            )
        m = TT3DPolygon()
        m.triangles = triangles
        m.vertex_list = vertices
        m.uvmap = texture_coords
        return m

    @staticmethod
    def unitary_Point() -> TT3DPoint:
        vertices = [Point3D(0, 0, 0.0)]
        texture_coords = (
            Point2D(0.0, 0),
            Point2D(1, 0),
            Point2D(1, 1),
        )

        m = TT3DPoint()
        m.vertex_list = vertices
        m.uvmap = [texture_coords]
        return m

    @staticmethod
    def gizmo_points():
        """Add a gizmo to the scene made of 4 points."""
        gizmo_node = TT3DNode()
        # center point
        center_point = Prefab3D.unitary_Point()
        center_point.local_transform = glm.translate(glm.vec3(0, 0, 0))
        center_point.material_id = 1
        gizmo_node.add_child(center_point)

        point_x = Prefab3D.unitary_Point()
        point_x.local_transform = glm.translate(glm.vec3(1, 0, 0))
        point_x.material_id = 2
        gizmo_node.add_child(point_x)

        # top point (y)
        point_y = Prefab3D.unitary_Point()
        point_y.local_transform = glm.translate(glm.vec3(0, 1, 0))
        point_y.material_id = 3
        gizmo_node.add_child(point_y)
        # front point (z)
        point_z = Prefab3D.unitary_Point()
        point_z.local_transform = glm.translate(glm.vec3(0, 0, 1))
        point_z.material_id = 4
        gizmo_node.add_child(point_z)
        return gizmo_node

    @staticmethod
    def unitary_line(axis=0) -> TT3DLine:
        vertices = [
            Point3D(0, 0, 0.0),
            Point3D(
                1.0 if axis == 0 else 0.0,
                1.0 if axis == 1 else 0.0,
                1.0 if axis == 2 else 0.0,
            ),
        ]
        texture_coords = [
            (
                Point2D(0.0, 0),
                Point2D(1.0, 1.0),
            )
        ]

        m = TT3DLine()
        m.vertex_list = vertices
        m.segment_uv = texture_coords
        return m

    @staticmethod
    def gizmo_lines():
        """Add a gizmo to the scene made of 3 lines."""
        gizmo_node = TT3DNode()
        # X line
        line_x = Prefab3D.unitary_line(axis=0)
        line_x.material_id = 2
        gizmo_node.add_child(line_x)

        # Y line
        line_y = Prefab3D.unitary_line(axis=1)

        line_y.material_id = 3
        gizmo_node.add_child(line_y)

        # Z line
        line_z = Prefab3D.unitary_line(axis=2)
        line_z.material_id = 4
        gizmo_node.add_child(line_z)
        return gizmo_node
