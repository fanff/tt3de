
import math

import glm

from tt3de.tt3de import Point3D


class GLMCamera:
    def __init__(
        self,
        pos: Point3D,
        screen_width: int = 100,
        screen_height: int = 100,
        fov_radians=math.radians(80),
        dist_min=1,
        dist_max=100,
        character_factor=1.8,
    ):
        self.pos = glm.vec3(pos.x, pos.y, pos.z)

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.pitch = 0
        self.yaw = 0

        self.fov_radians = fov_radians
        self.dist_min = dist_min
        self.dist_max = dist_max
        self.character_factor = character_factor

        self.zoom_2D = 1.0

        self.view_matrix_2D = glm.scale(glm.vec2(self.character_factor, 1.0))

        self.perspective: glm.mat4 = glm.mat4(1.0)
        self._rotation: glm.mat4 = glm.mat4(1.0)
        self.update_rotation()
        self.update_perspective()
        self.update_2d_perspective()

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

        self.perspective = glm.perspectiveFovZO(
            (self.fov_radians * h) / w, w, h, self.dist_min, self.dist_max
        )

    def update_2d_perspective(self):
        """ """
        # TODO depending on mode it can be different here.

        # currently we do adjuste to the minimum of the screen width and height
        min_screen_ = min(self.screen_width, self.screen_height) 

        scale_x =  self.character_factor * self.zoom_2D
        scale_y =  self.zoom_2D

        self.view_matrix_2D = glm.scale(glm.vec3(scale_x, scale_y, 1.0))

    def set_zoom_2D(self, zoom=1.0):
        self.zoom_2D = zoom
        self.update_2d_perspective()

    def move(self, delta: glm.vec3):
        self.pos += delta
        self.update_rotation()

    def move_at(self, pos: glm.vec3):
        self.pos = pos
        self.update_rotation()

    def move_side(self, dist: float):
        self.pos += glm.cross(self.direction_vector(), glm.vec3(0, 1, 0)) * dist
        self.update_rotation()

    def move_forward(self, dist: float):
        self.pos -= self.direction_vector() * dist
        self.update_rotation()

    def rotate_left_right(self, angle: float):
        self.yaw -= angle
        self.update_rotation()

    def rotate_up_down(self, angle: float):
        self.pitch = self.pitch + angle
        self.update_rotation()

    def set_yaw_pitch(self, yaw: float, pitch: float):
        self.yaw = yaw
        self.pitch = pitch
        self.update_rotation()

    def update_rotation(self):
        # pitch is around x axis , yaw is around y axis
        self._rotation = glm.rotate(self.yaw, glm.vec3(0, 1, 0)) * glm.rotate(
            self.pitch, glm.vec3(1, 0, 0)
        )

        self.recalc_model_inverse()

    def recalc_model_inverse(self):
        self._model_inverse = glm.inverse(self._rotation) * glm.translate(-self.pos)

    def project(
        self, point: glm.vec3, perspective: glm.mat4x4, screen_info=glm.vec4(0, 0, 1, 1)
    ) -> glm.vec3:

        return glm.projectZO(point, self._model_inverse, perspective, screen_info)

    def point_at(self, target: glm.vec3):
        direction = target - self.pos
        self.yaw = glm.atan(
            direction.x, direction.z
        )  # math.atan2(direction.x, direction.z)
        self.pitch = glm.atan(-direction.y, glm.length(direction.xz))

        self.update_rotation()

    def direction_vector(self) -> glm.vec3:
        # directional vector extracted from the matrix
        return glm.row(self._model_inverse, 2).xyz

    def __str__(self):
        return f"GLMCamera({self.pos,self.direction_vector()},yaw={self.yaw},pitch={self.pitch})"

    def __repr__(self):
        return str(self)

