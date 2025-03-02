import math

import glm
from tt3de.points import Point2D, Point3D
from tt3de.tt_3dnodes import TT3DPoint, TT3DPolygon, TT3DPolygonFan


class Prefab3D:
    @staticmethod
    def unitary_triangle() -> TT3DPolygonFan:
        vertices = [
            Point3D(0, 0, 1.0),
            Point3D(1.0, 0.0, 1.0),
            Point3D(1.0, 1.0, 1.0),
        ]
        texture_coords = [
            Point2D(0.0, 0),
            Point2D(1.0, 0.0),
            Point2D(1.0, 1.0),
        ]

        m = TT3DPolygonFan()
        m.vertex_list = vertices
        m.uvmap = [texture_coords]
        return m

    @staticmethod
    def unitary_square() -> TT3DPolygonFan:
        vertices = [
            Point3D(0, 0, 1.0),
            Point3D(1.0, 0.0, 1.0),
            Point3D(1.0, 1.0, 1.0),
            Point3D(0, 1.0, 1.0),
        ]
        texture_coords = [
            [
                Point2D(0.0, 0),
                Point2D(1.0, 0.0),
                Point2D(1.0, 1.0),
            ],
            [
                Point2D(0.0, 0),
                Point2D(1.0, 1.0),
                Point2D(0.0, 1.0),
            ],
        ]

        m = TT3DPolygonFan()
        m.vertex_list = vertices
        m.uvmap = texture_coords
        return m

    @staticmethod
    def unitary_circle(point_count=3) -> TT3DPolygonFan:
        vertices = [Point3D(0.0, 0.0, 1.0)]
        texture_coords = []
        for i in range(point_count + 1):
            angle = i * 2 * math.pi / point_count
            next_angle = (i + 1) * 2 * math.pi / point_count

            x = math.cos(angle)
            y = math.sin(angle)

            next_x = math.cos(next_angle)
            next_y = math.sin(next_angle)

            vertices.append(Point3D(x * 0.5, y * 0.5, 1.0))
            texture_coords.append(
                [
                    Point2D(0.5, 0.5),
                    Point2D(0.5 + x / 2, 0.5 + y / 2),
                    Point2D(0.5 + next_x / 2, 0.5 + next_y / 2),
                ]
            )

        m = TT3DPolygonFan()
        m.vertex_list = vertices
        m.uvmap = texture_coords
        return m

    @staticmethod
    def unitary_Point() -> TT3DPoint:
        vertices = [Point3D(0, 0, 1.0)]
        texture_coords = [
            Point2D(0.0, 0),
            Point2D(1, 0),
            Point2D(1, 1),
        ]

        m = TT3DPoint()
        m.vertex_list = vertices
        m.uvmap = [texture_coords]
        return m
    def gizmo_points():
        # center point
        center_point = Prefab3D.unitary_Point()
        center_point.local_transform = glm.translate(
            glm.vec3(0,0,-1)
        )
        center_point.material_id = 1
        point_x = Prefab3D.unitary_Point()
        point_x.local_transform = glm.translate(
            glm.vec3(1,0,-1)
        )
        point_x.material_id = 2

        # top point (y)
        point_y = Prefab3D.unitary_Point()
        point_y.local_transform = glm.translate(
            glm.vec3(0,1,-1)
        )
        point_y.material_id = 3

        # front point (z)
        point_z = Prefab3D.unitary_Point()
        point_z.local_transform = glm.translate(
            glm.vec3(0,0,0)
        )
        point_z.material_id = 4
        return center_point, point_x, point_y, point_z