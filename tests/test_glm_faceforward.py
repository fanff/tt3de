import math
from typing import List
import unittest

import glm

from context import tt3de

from tt3de.glm.triangle_clipping import calculate_normal
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem


from PIL import Image, ImageDraw


class TestFaceforward(unittest.TestCase):

    def test_many(self):

        n = glm.vec3(1.1, 2.2, 3.3)

        for i in range(100):
            import random

            Nref = glm.vec3(0, 0, 1)
            n = glm.vec3(
                random.random() - 0.5, random.random() - 0.5, random.random() - 0.5
            )
            # Ivec = glm.vec3(random.random()-.5,random.random()-.5,random.random()-.5)
            Ivec = glm.vec3(0.4, -0.5, 0.5)

            result = glm.faceforward(n, Ivec, Nref)

            # print(n,result)

    def test_matrix_triangle(self):
        # https://computergraphics.stackexchange.com/questions/9537/how-does-graphics-api-like-opengl-determine-which-triangle-is-back-face-to-cull

        mat = glm.mat3(1, 2, 3, 4, 5, 6, 7, 8, 9)
        print(mat)

        mat = glm.mat3(glm.vec3(0.5, 0, 78), glm.vec3(-1, 1, 100), glm.vec3(1, 1, 111))
        print(mat)
        mat_det = glm.determinant(mat)
        print(mat_det)

    def test_project_inf_perspective(self):

        viewport = glm.vec4(0, 0, 1, 1.0)
        v = glm.lookAt(glm.vec3(0, 0, 0), glm.vec3(0, 0, 1), glm.vec3(0, 1, 0))

        p = glm.infinitePerspective(math.radians(60), 16.0 / 9.0, 1.0)
        m = glm.mat4(1.0)

        apoint4 = glm.vec4(0, 0, 5, 1)

        for pz in [-40, -20, -5, -2, -1, 1, 2, 5, 20, 40]:
            apoint3 = glm.vec3(0, 1.0, pz)
            apoint4 = glm.vec4(0, 0, pz, 1.0)
            pp3 = glm.project(apoint3, m * v, p, viewport)
            # afaik https://github.com/g-truc/glm/blob/master/glm/ext/matrix_projection.inl
            # the glm project function are doing the /wi  internally.

            print(f"{apoint3} -> {pp3}")
            # pp4=m*v*p*apoint4
            # print(pp4)


if __name__ == "__main__":
    unittest.main()
