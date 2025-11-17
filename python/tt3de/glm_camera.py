# -*- coding: utf-8 -*-
from enum import Enum, auto
import math

from pyglm import glm


class ViewportScaleMode(Enum):
    # Preserve aspect ratio, entire logical 1x1 area visible, may letterbox
    FIT = auto()
    # Preserve aspect ratio, fill screen, logical 1x1 area may be cropped
    FILL = auto()
    # Ignore aspect ratio, logical 1x1 is stretched to screen
    STRETCH = auto()


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
        use_left_hand_perspective=True,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.fov_radians = fov_radians
        self.dist_min = dist_min
        self.dist_max = dist_max
        self.character_factor = character_factor

        # 2D Camera Info
        self.zoom_2D = 1.0
        self.position_2d = glm.vec2(0.0, 0.0)
        self.view_matrix_2D = glm.scale(glm.vec2(self.character_factor, 1.0))
        self.current_method = ViewportScaleMode.STRETCH

        # 3D Camera Info
        self._pos = pos
        self.yaw = 0.0
        self.pitch = 0.0

        self._rot = self.calculate_rotation_matrix()

        self.perspective_matrix: glm.mat4 = glm.mat4(1.0)
        self.use_left_hand_perspective = use_left_hand_perspective
        self.update_perspective()
        self.update_2d_perspective()

    def view_matrix_3D(self):
        """Calculate the view matrix 3D from inner _pos and _rot."""
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

        if self.use_left_hand_perspective:
            self.perspective_matrix = glm.perspectiveFovLH_ZO(
                (self.fov_radians * h) / w, w, h, self.dist_min, self.dist_max
            )
        else:
            self.perspective_matrix = glm.perspectiveFovRH_ZO(
                (self.fov_radians * h) / w, w, h, self.dist_min, self.dist_max
            )

    def get_position_2d(self) -> glm.vec2:
        """Get the camera location in 2D space."""
        return self.position_2d

    def set_position_2d(self, pos: glm.vec2):
        """Set the camera location in 2D space."""
        self.position_2d = pos
        self.update_2d_perspective()

    def set_viewport_scale_mode(self, method: ViewportScaleMode):
        self.current_method = method
        self.update_2d_perspective()

    def get_viewport_scale_mode(self) -> ViewportScaleMode:
        return self.current_method

    def update_2d_perspective(self):
        """
        Update the 2D view matrix that maps a logical 1.0 x 1.0 space to screen.

        - ViewportScaleMode.FIT   : preserve aspect ratio, entire 1x1 visible (letterbox if needed)
        - ViewportScaleMode.FILL  : preserve aspect ratio, screen fully covered (crop if needed)
        - ViewportScaleMode.STRETCH: ignore aspect ratio (distort to fill screen)

        Assumes:
            * Logical space is 1.0 units wide and 1.0 units tall (a square).
            * zoom_2D is an overall scale factor.
        """
        aspect = self.screen_width / (self.screen_height * self.character_factor)

        match self.current_method:
            case ViewportScaleMode.FIT:
                # Entire 1x1 fits on screen, preserve aspect ratio.
                # We shrink the longer dimension so that the shorter fits perfectly.
                if aspect >= 1.0:
                    # Screen is wider than tall -> compress X
                    scale_x = self.zoom_2D / aspect
                    scale_y = self.zoom_2D
                else:
                    # Screen is taller than wide -> compress Y
                    scale_x = self.zoom_2D
                    scale_y = self.zoom_2D * aspect

            case ViewportScaleMode.FILL:
                # Screen fully covered, preserve aspect ratio, crop the 1x1 if needed.
                if aspect >= 1.0:
                    # Screen is wider than tall -> expand Y
                    scale_x = self.zoom_2D
                    scale_y = self.zoom_2D * aspect
                else:
                    # Screen is taller than wide -> expand X
                    scale_x = self.zoom_2D / aspect
                    scale_y = self.zoom_2D

            case ViewportScaleMode.STRETCH:
                # No aspect preservation at all.
                scale_x = self.zoom_2D
                scale_y = self.zoom_2D * self.character_factor

        glm.identity(glm.mat4)
        self.view_matrix_2D = glm.translate(
            glm.vec3(-self.position_2d.x, -self.position_2d.y, 0.0)
        ) * glm.scale(glm.vec3(scale_x, -scale_y, 1.0))

    def set_character_factor(self, character_factor=1.0):
        self.character_factor = character_factor
        self.update_perspective()
        self.update_2d_perspective()

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
        self.move(pos - self._pos)

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
        return glm.column(self._rot, 2).xyz * (
            -1 if not self.use_left_hand_perspective else 1
        )

    def up_vector(self) -> glm.vec3:
        # directional up vector extracted from the matrix
        return glm.column(self._rot, 1).xyz

    def right_vector(self) -> glm.vec3:
        # directional right vector extracted from the matrix
        return glm.column(self._rot, 0).xyz

    def position_vector(self) -> glm.vec3:
        # position vector
        return self._pos

    def __str__(self):
        return f"GLMCamera({self._pos},yaw={self.yaw},pitch={self.pitch})"

    def __repr__(self):
        return str(self)
