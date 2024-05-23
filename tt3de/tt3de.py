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
        self.uv:Point2D = None
        self.dotval:float= 0.0

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


class Quaternion:
    def __init__(self, w: float, x: float, y: float, z: float):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"Quaternion(w={self.w}, x={self.x}, y={self.y}, z={self.z})"

    def rotate_point(self, point):
        p = Quaternion(0, point.x, point.y, point.z)
        rotated_p = self * p * self.inverse()
        return Point3D(rotated_p.x, rotated_p.y, rotated_p.z)

    def norm(self):
        return math.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)

    def norm2(self):
        return self.w**2 + self.x**2 + self.y**2 + self.z**2

    def to_rotation_matrix(self):
        # Calculate the rotation matrix from the quaternion
        w, x, y, z = self.w, self.x, self.y, self.z
        return [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]

    def inverse(self):
        norm_sq = self.norm2()
        return Quaternion(
            self.w / norm_sq, -self.x / norm_sq, -self.y / norm_sq, -self.z / norm_sq
        )

    def normalize(self):
        mag = math.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)
        self.w /= mag
        self.x /= mag
        self.y /= mag
        self.z /= mag

    def conjugate(self) -> "Quaternion":
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def __mul__(self, other: "Quaternion") -> "Quaternion":
        return Quaternion(
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
        )

    @staticmethod
    def from_euler(yaw, pitch, roll):
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return Quaternion(w, x, y, z)

    @staticmethod
    def from_axis_angle(axis, angle):
        half_angle = angle / 2
        sin_half_angle = math.sin(half_angle)
        return Quaternion(
            math.cos(half_angle),
            axis[0] * sin_half_angle,
            axis[1] * sin_half_angle,
            axis[2] * sin_half_angle,
        )


class Camera:
    def __init__(self, pos: Point3D, fov_w: float = 90, fov_h: float = 90):
        self.pos = pos
        self.fov_w = fov_w
        self.fov_h = fov_h

    def recalc_fov_h(self, w, h):
        r = (w / h) * 0.5
        self.fov_h = self.fov_w * r


class FPSCamera():

    NO_PROJECT = PPoint2D(0,0,0)
    def __init__(self, pos: Point3D, screen_width: int = 100, screen_height: int = 100, 
                 fov_radians=70, 
                 dist_min=1, 
                 dist_max=100,
                 character_factor=1.8):
        self.pos = pos

        self.screen_width = screen_width
        self.screen_height = screen_height


        self.fov_w = math.radians(fov_radians)
        self.fov_h = math.radians(fov_radians)

        self.dist_min=dist_min
        self.dist_max=dist_max
        self.character_factor = character_factor

        self.pitch = 0
        self.yaw = 0
        self._rotation:Quaternion
        self._rotation_invers:Quaternion

        
        self.worldobj_rotation:Quaternion = Quaternion.from_euler(0,0,0)
        self.update_rotation()
        self.recalc_fov_h(screen_width,screen_height,force_recalc=True)


    def set_projectioninfo(self, fov_radians:float=None, 
                 dist_min:float=None, 
                 dist_max:float=None,
                 character_factor:float=None):
        
        if fov_radians is not None:
            self.fov_w = fov_radians
        if dist_min is not None:
            self.dist_min=dist_min
        if dist_max is not None:
            self.dist_max=dist_max
        if character_factor is not None:
            self.character_factor=character_factor
        self.recalc_fov_h(self.screen_width,self.screen_height,force_recalc=True)


    def recalc_fov_h(self, w, h,force_recalc=False):
        if  force_recalc or self.screen_width!=w or self.screen_height!=h:
            r = (float(h) / w) 
            self.fov_h = self.fov_w * r * self.character_factor

    def rotate_left_right(self, angle: float):
        self.yaw += angle
        self.update_rotation()

    def rotate_up_down(self, angle: float):
        self.pitch = max(min(self.pitch + angle, 80), -80)
        self.update_rotation()

    def set_yaw_pitch(self , yaw,pitch):
        self.yaw = yaw
        self.pitch = pitch
        self.update_rotation()

    def update_rotation(self):
        q_pitch = Quaternion.from_axis_angle((1, 0, 0), (self.pitch))
        q_yaw = Quaternion.from_axis_angle((0, 1, 0), (self.yaw))
        self._rotation = q_yaw * q_pitch
        self._rotation_invers = self._rotation.inverse()

    def move_forward(self, dist: float):
        forward = self.direction_vector()
        delta = Point3D(forward.x * dist, forward.y * dist, forward.z * dist)
        self.move(delta)

    def move_side(self, dist: float):
        forward = self.direction_vector()
        # Right vector is orthogonal to the forward vector, can be calculated using cross product
        right = Point3D(-forward.z, 0, forward.x)  # Assuming Y is up
        delta = Point3D(right.x * dist, right.y * dist, right.z * dist)
        self.move(delta)

    def move(self, delta: Point3D):
        self.pos += delta

    def move_at(self, pos: Point3D):
        self.pos = pos

    def direction_vector(self) -> Point3D:
        # Forward vector should be (0, 0, 1) in camera's local space
        forward = self._rotation.rotate_point(Point3D(0, 0, 1))
        return forward

    def point_at(self, target: Point3D):
        direction = target - self.pos
        self.yaw = math.atan2(direction.x, direction.z)
        self.pitch = math.atan2(-direction.y, math.sqrt(direction.x**2 + direction.z**2))
        self.update_rotation()

    @property
    def rotation(self) -> Quaternion:
        return self._rotation

    def project(self, point: Point3D) -> PPoint2D:


        # Transform the point to camera space
        camera_space_point = self._rotation_invers.rotate_point(point - self.pos)

        # Check if the point is in front of the camera
        if camera_space_point.z <= 0:
            return self.NO_PROJECT  # Point is behind the camera

            return PPoint2D(.2, .5, camera_space_point.z)  # Point is behind the camera

        # Perspective projection onto the screen space (0,1)
        x = (camera_space_point.x / camera_space_point.z) * (
            (math.pi-self.fov_w) / 2
        ) + 0.5
        y = (camera_space_point.y / camera_space_point.z) * (
            (math.pi-self.fov_h) / 2
        ) + 0.5

        # Calculate the distance from the camera to the point
        distance = camera_space_point.magnitude()

        return PPoint2D(x, y, distance)

    def __str__(self):
        return f"Camera({self.pos,self.direction_vector()})"

    def __repr__(self):
        return str(self)


class Drawable3D:
    texture: "TextureTT3DE"

    def draw(self, camera, screen_width, screen_height) -> Iterable[PPoint2D]: ...
    def cache_output(self,segmap):
        raise NotImplemented("")


    @staticmethod
    def is_in_scree(pp: PPoint2D):
        return pp.depth > 1 and pp.x >= 0 and pp.x < 1 and pp.y >= 0 and pp.y < 1

    def render_point(self,pp: PPoint2D):
        raise NotImplemented("")

    


def is_point_in_triangle(px, py, ax, ay, bx, by, cx, cy, d) -> tuple[float]:
    """
    Barycentric coordinate method
    give d such that d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    """

    if d == 0:
        # If d is zero, the points are collinear or duplicate
        return None

    wa = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d
    wb = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d
    wc = 1 - wa - wb

    if wa >= 0 and wb >= 0 and wc >= 0:
        return wa, wb, wc
    else:
        return None


class PointElem(Drawable3D):
    def __init__(self, p: Point3D, texture: "TextureTT3DE"=None):
        self.p = p
        self.texture: "TextureTT3DE" = texture

    def draw(self, camera: Camera, screen_width, screen_height) -> Iterable[PPoint2D]:
        pp = camera.project(self.p)
        if self.is_in_scree(pp):
            pi: Point2Di = pp.to_screen_space(screen_width, screen_height)
            ppr = PPoint2D(pi.x, pi.y, pp.depth)
            yield ppr

    def proj_vertices(self, camera: Camera, screen_width, screen_height) :
        return camera.project(self.p)
    

class Triangle3D(Drawable3D):
    def __init__(
        self, pos1: Point3D, pos2: Point3D, pos3: Point3D, texture: "TextureTT3DE"=None
    ):
        self.pos1 = pos1
        self.pos2 = pos2
        self.pos3 = pos3
        self.texture: "TextureTT3DE" = texture

        self.uvmap: List[tuple[PPoint2D, PPoint2D, PPoint2D]] = [
            (PPoint2D(0, 0), PPoint2D(0, 0), PPoint2D(0, 0))
        ]
        self.normal = self.normal_vector()


    def __str__(self):
        return f"Triangle3D({self.pos1,self.pos2,self.pos3}, {self.uvmap}, {self.normal})"

    def __repr__(self):
        return str(self)
    

    def uvcalc(self, w1: float, w2: float, w3: float) -> Point2D:
        # Calculate the UV coordinates based on the weights
        r1, r2, r3 = self.uvmap[0]
        u = w1 * r1.x + w2 * r2.x + w3 * r3.x
        v = w1 * r1.y + w2 * r2.y + w3 * r3.y
        return Point2D(u, v)

    def normal_vector(self) -> Point3D:
        # Calculate the normal vector of the triangle using the cross product
        # Vector AB
        ab_x = self.pos2.x - self.pos1.x
        ab_y = self.pos2.y - self.pos1.y
        ab_z = self.pos2.z - self.pos1.z

        # Vector AC
        ac_x = self.pos3.x - self.pos1.x
        ac_y = self.pos3.y - self.pos1.y
        ac_z = self.pos3.z - self.pos1.z

        # Cross product AB x AC
        normal_x = ab_y * ac_z - ab_z * ac_y
        normal_y = ab_z * ac_x - ab_x * ac_z
        normal_z = ab_x * ac_y - ab_y * ac_x

        # Normalize the vector to get the unit normal vector
        norm = math.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        if norm == 0:
            return Point3D(0, 0, 0)
        normal_unit_x = normal_x / norm
        normal_unit_y = normal_y / norm
        normal_unit_z = normal_z / norm

        return Point3D(normal_unit_x, normal_unit_y, normal_unit_z)

    def center_point(self) -> Point3D:
        # Calculate the centroid of the triangle
        cx = (self.pos1.x + self.pos2.x + self.pos3.x) / 3
        cy = (self.pos1.y + self.pos2.y + self.pos3.y) / 3
        cz = (self.pos1.z + self.pos2.z + self.pos3.z) / 3
        return Point3D(cx, cy, cz)

    def draw(self, camera: FPSCamera, screen_width, screen_height) -> Iterable[PPoint2D]:
        # vertex modifier can be applied here.

        # project
        rrp1 = camera.worldobj_rotation.rotate_point(self.pos1)
        rrp2 = camera.worldobj_rotation.rotate_point(self.pos2)
        rrp3 = camera.worldobj_rotation.rotate_point(self.pos3)

        pp1 = camera.project(rrp1)
        pp2 = camera.project(rrp2)
        pp3 = camera.project(rrp3)


        rnormal = camera.worldobj_rotation.rotate_point(self.normal)
        dotp1 = rnormal.dot(rrp1 - camera.pos) 
        dotp2 = rnormal.dot(rrp2 - camera.pos) 
        dotp3 = rnormal.dot(rrp3 - camera.pos) 

        min_depth = camera.dist_min
        
        c = (dotp1>0 or dotp2>0 or dotp3>0) or (
            pp1.depth<min_depth and pp2.depth<min_depth and pp3.depth<min_depth)or (
            pp1.x<=0 and pp2.x <=0 and pp3.x <= 0) or (
            pp1.y<=0 and pp2.y <=0 and pp3.y <= 0) or (
            pp1.x>=1 and pp2.x >=1 and pp3.x >=1) or (
            pp1.y>=1 and pp2.y >=1 and pp3.y >=1) or (
                pp1==camera.NO_PROJECT or pp2 == camera.NO_PROJECT or pp3==camera.NO_PROJECT
            )
        
        if not c:
            return self.draw_inner(camera, 
                                    pp1, pp2, pp3, 
                                    screen_width, screen_height,
                                    rnormal,
                                    rrp1,rrp2,rrp3)
        return []

    def draw_border(
        self, pp1, pp2, pp3, screen_width, screen_height
    ) -> Iterable[PPoint2D]:
        yield from Line2D(pp1, pp2).draw(screen_width, screen_height)
        yield from Line2D(pp2, pp3).draw(screen_width, screen_height)
        yield from Line2D(pp3, pp1).draw(screen_width, screen_height)

    def render_point(self,pp: PPoint2D):
        return self.texture.render_point(pp)
    def cache_output(self,segmap):
        self.texture.cache_output(segmap)

    def draw_inner(
        self,
        camera: Camera,
        pp1: PPoint2D,
        pp2: PPoint2D,
        pp3: PPoint2D,
        screen_width,
        screen_height,
        rnormal:Point3D,
        rrp1,rrp2,rrp3
    ) -> Iterable[PPoint2D]:

        p1i = pp1.to_screen_space(screen_width, screen_height)
        p2i = pp2.to_screen_space(screen_width, screen_height)
        p3i = pp3.to_screen_space(screen_width, screen_height)

        p1fx, p1fy = pp1.to_screen_space_flt(screen_width, screen_height)
        p2fx, p2fy = pp2.to_screen_space_flt(screen_width, screen_height)
        p3fx, p3fy = pp3.to_screen_space_flt(screen_width, screen_height)

        bd = (p2fy - p3fy) * (p1fx - p3fx) + (p3fx - p2fx) * (p1fy - p3fy)
        if -0.00001 < bd < 0.00001:
            return None
        # Bounding box coordinates
        min_x = max(0, min(p1i.x, p2i.x, p3i.x))
        max_x = min(screen_width - 1, max(p1i.x, p2i.x, p3i.x))
        min_y = max(0, min(p1i.y, p2i.y, p3i.y))
        max_y = min(screen_height - 1, max(p1i.y, p2i.y, p3i.y))

        # Check each point in the bounding box
        for px in range(min_x, max_x + 1):
            for py in range(min_y, max_y + 1):

                w1 = ((p2fy - p3fy) * (px - p3fx) + (p3fx - p2fx) * (py - p3fy)) / bd
                w2 = ((p3fy - p1fy) * (px - p3fx) + (p1fx - p3fx) * (py - p3fy)) / bd
                w3 = 1 - w1 - w2

                if w1 > 0 and w2 > 0 and w3 > 0:
                    # this is like the pixel shader. 

                    appxp = rrp1*w1 + rrp2*w2 + rrp3*w3
                    

                    d = (pp1.depth * w1 + pp2.depth * w2 + pp3.depth * w3) 


                    ddot_prod = rnormal.dot(appxp-camera.pos) / d
                    
                    p = PPoint2D(px, py, d)
                    uvpoint = self.uvcalc(w1, w2, w3)
                    p.uv = uvpoint
                    p.dotval = ddot_prod
                    yield p


def exp_grad(maxv, alpha=0.1, minv=0):
    def f(x):
        if x < minv:
            return 0
        else:
            return round(maxv * (1 - math.exp(-alpha * x)))

    return f


class TextureTT3DE:
    def render_point(self, p: PPoint2D) -> int:
        pass


class Line3D(Drawable3D):
    def __init__(self, pos1: Point3D, pos2: Point3D, texture: "TextureTT3DE"):
        self.pos1 = pos1
        self.pos2 = pos2
        self.texture: "TextureTT3DE" = texture

    def draw(self, camera: Camera, screen_width, screen_height) -> Iterable[PPoint2D]:
        pp1 = camera.project(self.pos1)
        pp2 = camera.project(self.pos2)
        if self.is_in_scree(pp1) or self.is_in_scree(pp1):
            l2d = Line2D(pp1, pp2)
            lpoint2D = l2d.draw(screen_width, screen_height)
            return lpoint2D
        return []
class TextureCoordinate(Point2D):
    pass

class Mesh3D(Drawable3D):
    def __init__(self):
        self.vertices: List[Point3D] = []
        self.texture_coords: List[List[TextureCoordinate]] = [[] for _ in range(8)]
        self.normals: List[Point3D] = []
        self.triangles: List[Triangle3D] = []

        self.triangles_vindex: List[Tuple[int,int,int]] = []


        self.texture:TextureTT3DE=None

    def proj_vertices(self, camera: Camera, screen_width, screen_height) :

        for t in self.triangles:
            #rrp1 = camera.worldobj_rotation.rotate_point(t.pos1)
            #rrp2 = camera.worldobj_rotation.rotate_point(t.pos2)
            #rrp3 = camera.worldobj_rotation.rotate_point(t.pos3)

            pp1 = camera.project(t.pos1)
            pp2 = camera.project(t.pos2)
            pp3 = camera.project(t.pos3)
            yield [pp1, pp2, pp3]

    def draw(self, camera, screen_width, screen_height) -> Iterable[PPoint2D]:
        for t in self.triangles:
            yield from t.draw(camera, screen_width, screen_height)


    def cache_output(self,segmap):
        self.texture.cache_output(segmap)


    def render_point(self,pp: PPoint2D):
        return self.texture.render_point(pp)

    def set_texture(self,t):
        self.texture=t
        for t in self.triangles:
            t.texture = t

    @classmethod
    def from_square(cls,p1:Point3D):
        t1 = Triangle3D( p1 , p1+Point3D(1,0,0), p1+Point3D(1,0,1))
        t2 = Triangle3D( p1 , p1+Point3D(0,0,1), p1+Point3D(1,0,1))

        t1.uvmap = [(TextureCoordinate(0,0),TextureCoordinate(1,0),TextureCoordinate(1,1))]
        t2.uvmap = [(TextureCoordinate(0,0),TextureCoordinate(0,1),TextureCoordinate(1,1))]
        s = cls()
        s.triangles=[t1,t2]

class Node3D(Drawable3D):
    def __init__(self):
        
        self.translation = Point3D(0,0,0)
        self.rotation = Quaternion.from_euler(0,0,0)
        self.elems:list[Drawable3D] = []


    def set_translation(self,translation:Point3D):
        self.translation = translation

    def draw(self, camera:FPSCamera, screen_width, screen_height) -> Iterable[PPoint2D]:
        p = camera.pos
        prev_rot = camera.worldobj_rotation
        camera.move(self.translation * (-1))
        camera.worldobj_rotation = camera.worldobj_rotation*self.rotation
        for elemidx,t in enumerate(self.elems):
            yield from t.draw(camera, screen_width, screen_height)

        camera.move_at(p)
        camera.worldobj_rotation = prev_rot


    def render_point(self,pp: PPoint2D):
        idx=0
        return self.elems[idx].render_point(pp)
    
    def cache_output(self,segmap):
        for e in self.elems:
            e.cache_output(segmap)


