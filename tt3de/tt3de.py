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


class Line2D:
    def __init__(self, p1: PPoint2D, p2: PPoint2D):
        self.p1 = p1
        self.p2 = p2
        self.horizontal_mode = True if self.get_slope() != float("inf") else False

    def __str__(self):
        return f"Line2d({self.p1},{self.p2})"

    def get_slope(self) -> float:
        if self.p2.x == self.p1.x:
            return float("inf")  # Vertical line
        return (self.p2.y - self.p1.y) / (self.p2.x - self.p1.x)

    def get_y_intercept(self) -> float:
        slope = self.get_slope()
        if slope == float("inf"):
            return float("nan")  # Vertical line has no y-intercept
        return self.p1.y - slope * self.p1.x

    def y_given_x(self, x: float) -> float:
        slope = self.get_slope()
        y_intercept = self.get_y_intercept()
        if slope == float("inf"):
            raise ValueError("Line is vertical, cannot calculate y given x")
        return slope * x + y_intercept

    def x_given_y(self, y: float) -> float:
        slope = self.get_slope()
        y_intercept = self.get_y_intercept()
        if slope == 0:
            raise ValueError("Line is horizontal, cannot calculate x given y")
        return (y - y_intercept) / slope

    def angle_to_reference_vector(self) -> float:
        dx, dy = (self.p2.x - self.p1.x, self.p2.y - self.p1.y)
        magnitude_direction = math.sqrt(dx**2 + dy**2)
        cos_theta = dy / (magnitude_direction)
        return math.acos(cos_theta)

    def draw(self, screen_w, screen_h) -> Iterable[PPoint2D]:

        p1i = self.p1.to_screen_space(screen_w, screen_h)
        p2i = self.p2.to_screen_space(screen_w, screen_h)

        d1 = self.p1.depth
        d2 = self.p2.depth

        total_len = (self.p2 - self.p1).magnitude()
        slope = self.get_slope()
        if slope == float("inf"):  # Vertical line
            x = p1i.x
            for j in range(
                max(0, min(p1i.y, p2i.y)), min(screen_h - 1, max(p1i.y, p2i.y))
            ):

                b1 = ((Point2D(x, j) - self.p1).magnitude()) / total_len
                b2 = 1.0 - b1
                dist = d1 * b1 + b2 * d2
                yield PPoint2D(x, j, dist, [b1, b2])

        else:
            y_intercept = self.get_y_intercept()
            if abs(slope) < 1:
                # horizontal parsing
                for i in range(
                    max(0, min(p1i.x, p2i.x)), min(screen_w, max(p1i.x, p2i.x)) + 1
                ):
                    x = i / screen_w
                    y = slope * x + y_intercept
                    j = round(y * screen_h)

                    b1 = ((Point2D(i, j) - self.p1).magnitude()) / total_len
                    b1 = max(0, min(b1, 1.0))
                    b2 = 1.0 - b1
                    dist = d1 * b1 + b2 * d2
                    yield PPoint2D(i, j, dist, [b1, b2])
            else:
                # vertical parsing
                for j in range(
                    max(0, min(p1i.y, p2i.y)), min(screen_h, max(p1i.y, p2i.y)) + 1
                ):
                    y = j / screen_h
                    x = (y - y_intercept) / slope
                    i = round(x * screen_w)

                    b1 = ((Point2D(i, j) - self.p1).magnitude()) / total_len
                    b1 = max(0, min(b1, 1.0))
                    b2 = 1.0 - b1
                    dist = d1 * b1 + b2 * d2
                    yield PPoint2D(i, j, dist, [b1, b2])


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

