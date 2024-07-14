import math
from math import radians
from typing import Iterable, List, Tuple


class Point2Di:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point2Di({self.x},{self.y})"

    def __repr__(self):
        return f"Point2Di({self.x},{self.y})"


class Point2D:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def to_screen_space(self, screen_width: float, screen_height: float) -> "Point2Di":
        new_x = self.x * screen_width
        new_y = self.y * screen_height
        return Point2Di(round(new_x), round(new_y))

    def to_screen_space_flt(
        self, screen_width: float, screen_height: float
    ) -> "Point2D":
        new_x = self.x * screen_width
        new_y = self.y * screen_height
        return new_x, new_y

    def magnitude(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5

    def __add__(self, other: "Point2D") -> "Point2D":
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point2D") -> "Point2D":
        return Point2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Point2D":
        return Point2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Point2D":
        return self.__mul__(scalar)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"Point2D({self.x:.2f},{self.y:.2f})"


class PPoint2D(Point2D):
    def __init__(self, x: float, y: float, depth: float = -1):
        self.x = x
        self.y = y
        self.depth = depth
        self.uv: Point2D = None
        self.dotval: float = 0.0

    def __add__(self, other: "Point2D") -> "PPoint2D":
        return PPoint2D(self.x + other.x, self.y + other.y, self.depth)

    def __sub__(self, other: "Point2D") -> "PPoint2D":
        return PPoint2D(self.x - other.x, self.y - other.y, self.depth)

    def __mul__(self, scalar: float) -> "PPoint2D":
        return PPoint2D(self.x * scalar, self.y * scalar, self.depth)

    def __rmul__(self, scalar: float) -> "PPoint2D":
        return self.__mul__(scalar)

    def __str__(self):
        return f"PPoint2D({self.x},{self.y},{self.depth:.1f}; uv:{self.uv})"

    def __repr__(self):
        return str(self)


class Point3D:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other: "Point3D") -> "Point3D":
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Point3D") -> "Point3D":
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Point3D":
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Point3D":
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __repr__(self):
        return f"Point3D({self.x:.2f},{self.y:.2f},{self.z:.2f})"

    def magnitude(self) -> float:
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def normalize(self) -> "Point3D":
        return normalize(self)

    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Point3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )


def normalize(v: "Point3D"):
    n2 = v.x**2 + v.y**2 + v.z**2

    norm = math.sqrt(n2)
    if norm == 0:
        norm = 1e-6
    return Point3D(v.x / norm, v.y / norm, v.z / norm)

class Drawable3D:
    texture: "TextureTT3DE"

    def draw(self, camera, screen_width, screen_height) -> Iterable[PPoint2D]:
        raise NotImplemented("")

    def cache_output(self, segmap):
        raise NotImplemented("")

    @staticmethod
    def is_in_scree(pp: PPoint2D):
        return pp.depth > 1 and pp.x >= 0 and pp.x < 1 and pp.y >= 0 and pp.y < 1

    def render_point(self, pp: PPoint2D):
        raise NotImplemented("")

