import math

import glm

from tt3de.points import Point3D


class GLMCamera:
    def __init__(
        self,
        pos: glm.vec3,
        screen_width: int = 100,
        screen_height: int = 100,
        fov_radians=math.radians(80),
        dist_min=1,
        dist_max=100,
        character_factor=1.8,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.fov_radians = fov_radians
        self.dist_min = dist_min
        self.dist_max = dist_max
        self.character_factor = character_factor

        self.zoom_2D = 1.0

        self.view_matrix_2D = glm.scale(glm.vec2(self.character_factor, 1.0))

        self._pos = pos
        self.yaw = 0.0
        self.pitch = 0.0

        self._rot = self.calculate_rotation_matrix()

        self.perspective_matrix: glm.mat4 = glm.mat4(1.0)
        self.update_perspective()
        self.update_2d_perspective()

    def view_matrix_3D(self):
        """calculate the view matrix 3D from inner _pos and _rot"""
        return glm.inverse(self._rot) * glm.translate(-self._pos)

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

        self.perspective_matrix = glm.perspectiveFovLH_ZO(
            (self.fov_radians * h) / w, w, h, self.dist_min, self.dist_max
        )

    def update_2d_perspective(self):
        """ """
        # TODO depending on mode it can be different here.

        # currently we do adjuste to the minimum of the screen width and height
        min_screen_ = min(self.screen_width, self.screen_height)

        scale_x = self.character_factor * self.zoom_2D
        scale_y = self.zoom_2D

        self.view_matrix_2D = glm.scale(glm.vec3(scale_x, scale_y, 1.0))

    def set_zoom_2D(self, zoom=1.0):
        self.zoom_2D = zoom
        self.update_2d_perspective()

    def point_at(self, pos: glm.vec3):
        """Point the camera at a position in 3D space."""
        # Calculate the direction the camera is pointing
        direction = pos - self._pos

        # Calculate the pitch and yaw angles from the direction
        self.pitch = math.asin(-direction.y)
        self.yaw = math.atan2(direction.x, direction.z)

        self.set_yaw_pitch(self.yaw, self.pitch)

    def move(self, delta: glm.vec3):
        self._pos = self._pos + delta

    def move_at(self, pos: glm.vec3):
        self.move(pos - self.pos)

    def move_side(self, dist: float):
        self.move(self.right_vector() * dist)

    def move_forward(self, dist: float):
        self.move(self.direction_vector() * dist)

    def calculate_rotation_matrix(self):
        """Calculate the rotation matrix from yaw and pitch angles."""
        # Create a rotation matrix from yaw and pitch
        yaw_matrix = glm.rotate(
            glm.mat4(1.0), self.yaw, glm.vec3(0, 1, 0)
        )  # Rotation around the Y axis
        pitch_matrix = glm.rotate(
            glm.mat4(1.0), self.pitch, glm.vec3(1, 0, 0)
        )  # Rotation around the X axis

        # Combine yaw and pitch rotations
        return yaw_matrix * pitch_matrix

    def rotate_left_right(self, angle: float):
        self.yaw += angle
        self._rot = self.calculate_rotation_matrix()

    def rotate_up_down(self, angle: float):
        self.pitch += angle
        self._rot = self.calculate_rotation_matrix()

    def set_yaw_pitch(self, yaw: float, pitch: float):
        """Set the yaw and pitch of the camera."""
        self.yaw = yaw
        self.pitch = pitch
        new_rot = self.calculate_rotation_matrix()
        self._rot = new_rot

    def direction_vector(self) -> glm.vec3:
        # directional vector extracted from the matrix
        return glm.column(self._rot, 2).xyz

    def up_vector(self) -> glm.vec3:
        # directional up vector extracted from the matrix
        return glm.column(self._rot, 1).xyz

    def right_vector(self) -> glm.vec3:
        # directional right vector extracted from the matrix
        return glm.column(self._rot, 0).xyz

    def position_vector(self) -> glm.vec3:
        # position vector extracted from the matrix
        return self._pos

    def __str__(self):
        return f"GLMCamera({self._pos},yaw={self.yaw},pitch={self.pitch})"

    def __repr__(self):
        return str(self)
