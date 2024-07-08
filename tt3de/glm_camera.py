
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
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.fov_radians = fov_radians
        self.dist_min = dist_min
        self.dist_max = dist_max
        self.character_factor = character_factor

        self.zoom_2D = 1.0

        self.view_matrix_2D = glm.scale(glm.vec2(self.character_factor, 1.0))
        self.view_matrix_3D: glm.mat4 = glm.lookAt(glm.vec3(pos.x, pos.y, pos.z), glm.vec3(pos.x, pos.y, pos.z) + glm.vec3(0, 0, 1), glm.vec3(0, -1, 0))
        self.perspective_matrix: glm.mat4 = glm.mat4(1.0)
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

        self.perspective_matrix = glm.perspectiveFovZO(
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
        self.view_matrix_3D = glm.translate(delta) * self.view_matrix_3D


    def move_at(self, pos: glm.vec3):
        self.move(pos - self.pos)

    def move_side(self, dist: float):
        self.view_matrix_3D = glm.translate(self.right_vector() * dist) * self.view_matrix_3D

    def move_forward(self, dist: float):
        self.view_matrix_3D = glm.translate(self.direction_vector() * dist) * self.view_matrix_3D

    def rotate_left_right(self, angle: float):
        
        self.view_matrix_3D = glm.rotate(angle, glm.vec3(0, 1, 0)) * self.view_matrix_3D

    def rotate_up_down(self, angle: float):
        self.view_matrix_3D = glm.rotate(angle, self.right_vector()) * self.view_matrix_3D


    def set_yaw_pitch(self, yaw: float, pitch: float):
        """Set the yaw and pitch of the camera. 
        The yaw is the rotation around the y-axis and the pitch is the rotation around the x-axis.
        To calculate the view matrix we proceed as follow :
        1. Separate the rotation from the translation in the view matrix
        2. Apply the yaw and pitch rotations
        3. Apply the translation

        """
        self.yaw = yaw
        self.pitch = pitch

        # 1. Separate the rotation from the translation in the view matrix

        

    def point_at(self, target: glm.vec3):
        # calculate the right vector using the up vector
        right = glm.cross(glm.vec3(0, 1, 0), target - self.position_vector())
        # calculate the up vector
        up = glm.cross(target - self.position_vector(), right)


        self.view_matrix_3D = glm.lookAt(self.position_vector(), target, up)

    def direction_vector(self) -> glm.vec3:
        # directional vector extracted from the matrix
        return -glm.row(self.view_matrix_3D, 2).xyz
    def up_vector(self) -> glm.vec3:
        # directional up vector extracted from the matrix
        return glm.row(self.view_matrix_3D, 1).xyz
    def right_vector(self) -> glm.vec3:
        # directional right vector extracted from the matrix
        return glm.row(self.view_matrix_3D, 0).xyz
    def position_vector(self)-> glm.vec3:
        # position vector extracted from the matrix
        return glm.row(self.view_matrix_3D, 3).xyz
    def __str__(self):
        return f"GLMCamera({self.pos,self.direction_vector()},yaw={self.yaw},pitch={self.pitch})"

    def __repr__(self):
        return str(self)

