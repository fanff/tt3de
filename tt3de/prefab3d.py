

from tt3de.tt3de import Point2D, Point3D
from tt3de.tt_3dnodes import TT3DPoint, TT3DPolygon


class Prefab3D:
    @staticmethod
    def unitary_triangle() -> TT3DPolygon:
        vertices = [
            Point3D(0, 0, 1.0),
            Point3D(1.0, 0.0, 1.0),
            Point3D(1.0, 1.0, 1.0),
        ]
        texture_coords = [
            Point2D(0.0, 0),
            Point2D(1.0,0.0 ),
            Point2D(1.0, 1.0),
        ]

        m = TT3DPolygon()
        m.vertex_list = vertices
        m.uvmap = [texture_coords]
        return m
    
    @staticmethod
    def unitary_Point() -> TT3DPoint:
        vertices = [
            Point3D(0, 0, 1.0)
        ]
        texture_coords = [
            Point2D(0.0, 0),
            Point2D(1, 0),
            Point2D(1, 1),
        ]

        m = TT3DPoint()
        m.vertex_list = vertices
        m.uvmap = [texture_coords]
        return m