import array
import random
from textwrap import dedent
import timeit

import math
import glm

from tt3de.glm.pyglmtexture import yvalue_from_adjoint_unprotected
from tt3de.glm.triangle_raster import (
    generate_random_triangle,
    triangle_raster_v1,
    triangle_raster_v2,
)
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem


from glm import ivec2, vec2, vec3, mat3
import unittest

from fractions import Fraction


def topiliimage(coordinates, imgname):
    from PIL import Image

    # Extract the min and max values for x and y
    min_x = min(coordinates, key=lambda t: t[0])[0]
    max_x = max(coordinates, key=lambda t: t[0])[0]
    min_y = min(coordinates, key=lambda t: t[1])[1]
    max_y = max(coordinates, key=lambda t: t[1])[1]

    # Calculate canvas size with extra 10 pixels on each side
    width = (max_x - min_x) + 20
    height = (max_y - min_y) + 20

    # Create a blank white canvas
    canvas = Image.new("RGB", (width, height), "white")

    # Adjust coordinates to account for the offset
    adjusted_coordinates = [(x - min_x + 10, y - min_y + 10) for x, y in coordinates]

    # Plot each point on the canvas
    for x, y in adjusted_coordinates:
        canvas.putpixel((x, y), (0, 0, 0))  # Black pixel
    canvas.save(imgname)


def line_nofloat(pa, pb):
    "Bresenham's line algorithm without using float (because the float curse)"
    (y0, x0), (y1, x1) = pa, pb
    rev = reversed
    if abs(y1 - y0) <= abs(x1 - x0):
        x0, y0, x1, y1 = y0, x0, y1, x1
        rev = lambda x: x
    if x1 < x0:
        x0, y0, x1, y1 = x1, y1, x0, y0
    leny = abs(y1 - y0)
    for i in range(leny + 1):
        xi, yi = rev(
            (round(Fraction(i, leny) * (x1 - x0)) + x0, (1 if y1 > y0 else -1) * i + y0)
        )

        yield (xi, yi)


def line_float(pa, pb):
    "Bresenham's line algorithm using float"
    (x0, y0), (x1, y1) = pa, pb
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            yield x, y
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            yield x, y
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    yield x, y


def line_float_prot(pa, pb, maxx, maxy):
    "Bresenham's line algorithm with float values, protecting the top/bottom values within screen"
    (x0, y0), (x1, y1) = pa, pb
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            if x < maxx and x >= 0 and y < maxy and y >= 0:
                yield x, y
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            if x < maxx and x >= 0 and y < maxy and y >= 0:
                yield x, y
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    if x < maxx and x >= 0 and y < maxy and y >= 0:
        yield x, y


def iter_rect_full(p1, p2):
    paxi, payi = p1
    pbxi, pbyi = p2
    for xi in range(paxi, pbxi + 1):
        for yi in range(payi, pbyi + 1):
            yield xi, yi


def iter_vertical_line(p1, count):
    xi, ystart = p1
    for yi in range(ystart, ystart + count):
        yield xi, yi


def iter_horizontal_line(p1, count):
    xstart, yi = p1
    for xi in range(xstart, xstart + count):
        yield xi, yi


def iter_rect_diagonal_full(p1, p2):

    paxi, payi = p1
    pbxi, pbyi = p2

    diffx = pbxi - paxi
    diffy = pbyi - payi

    match diffx:
        case 0:

            match diffy:
                case 0:
                    yield paxi, payi
                    return
                case _:
                    yield from iter_vertical_line(p1, diffy + 1)
                    return
        case _:
            match diffy:
                case 0:
                    yield from iter_horizontal_line(p1, diffx + 1)
                    return

    jump_step = float(pbxi - paxi) / (pbyi - payi)
    if jump_step <= 1.0:

        yi = payi

        jumpx = 0.0
        for xi in range(paxi, pbxi):
            while jumpx < 1.0:
                yield xi, yi

                jumpx += jump_step
                yi += 1
            if jumpx >= 1.0:
                jumpx = jumpx - math.floor(jumpx)
        yield pbxi, pbyi
    else:
        yi = payi
        jumpx = 0.0
        for xi in range(paxi, pbxi + 1):
            yield xi, yi

            jumpx += 1.0

            if jumpx >= jump_step:
                yi += 1

                jumpx = jumpx - jump_step


def inscreen_iter(p1, p2):
    # TODO Unfinished,
    """draw line pixel on the screen by protecting  the x, and y values."""
    paxi, payi = p1
    pbxi, pbyi = p2

    x_yfact = float(pbxi - paxi) / (pbyi - payi)
    yxfact = 1 / x_yfact

    if p1[0] < 0:
        start_x = 0
        start_y = yxfact * -p1[0]
    else:
        start_y = p1[1]
        start_x = p1[0]

    if start_y < 0:
        start_y = 0
        start_x = x_yfact * (-start_y)

        yield from iter_rect_diagonal_full((start_x, start_y), p2)

    else:
        yield from iter_rect_diagonal_full((start_x, start_y), p2)


class Test_scanline_iterator(unittest.TestCase):

    def test_rectfull(self):
        points = list(iter_rect_full((3, 4), (3, 4)))
        self.assertEqual(len(points), 1)

        points = list(iter_rect_full((3, 4), (4, 5)))
        self.assertEqual(len(points), 4)

        points = list(iter_rect_full((3, 4), (5, 6)))
        self.assertEqual(len(points), 9)

    def test_rectfulldiagonal(self):
        points = list(iter_rect_diagonal_full((3, 4), (4, 5)))
        # print(points)
        self.assertEqual(len(points), 2)

        points = list(iter_rect_diagonal_full((3, 4), (5, 6)))
        # print(points)
        self.assertEqual(len(points), 3)

        # pure long diagonal
        shift = 140
        points = list(iter_rect_diagonal_full((3, 4), (3 + shift, 4 + shift)))
        self.assertEqual(len(points), shift + 1)

        pa = (-1, -1)
        shiftx = 3
        shifty = 4
        pb = (3 + shiftx, 2 + shifty)

        points = list(iter_rect_diagonal_full(pa, pb))
        print(points)
        # print(len(points),shiftx+shifty)

        # self.assertEqual(pa,points[0])
        # self.assertEqual(pb,points[-1])
        # self.assertEqual(len(points),3)

        print(list(line_float(pa, pb)))

        print(list(line_float_prot(pa, pb, 2000, 2000)))

        print(list(inscreen_iter(pa, pb)))
        import timeit

        setup = f"pa={(0,0)};pb={(100,90)}"
        number = 10000
        durnat = timeit.timeit(
            "list(iter_rect_diagonal_full(pa,pb))",
            globals=globals(),
            setup=setup,
            number=number,
        )
        dur_in_nat = timeit.timeit(
            "list(inscreen_iter(pa,pb))", globals=globals(), setup=setup, number=number
        )

        dur_f = timeit.timeit(
            "list(line_float(pa,pb))", globals=globals(), setup=setup, number=number
        )
        dur_fp = timeit.timeit(
            "list(line_float_prot(pa,pb,2000,2000))",
            globals=globals(),
            setup=setup,
            number=number,
        )

        print(durnat, dur_in_nat, dur_f, dur_fp)


from tt3de.glm.c_triangle_raster import c_glm_triangle_render_to_buffer
from tt3de.glm.c_triangle_raster import TrianglesBuffer


class Test_TriangleScanLine(unittest.TestCase):

    def test_one(self):
        a, b, c = vec3(2.0, 2.0, 1.0), vec3(120, 120.0, 1.0), vec3(100.0, 40.0, 1.0)

        screen_width, screen_height = 100, 100

        trv1 = list(triangle_raster_v1(b, a, c, screen_width, screen_height))

        trv2 = list(triangle_raster_v2(b, a, c, screen_width, screen_height))

        tri = mat3(a, c, b)
        glmtri_rend = list(
            glmtriangle_render(tri, glm.inverse(tri), screen_width, screen_height)
        )

        trv1 = set(trv1)

        glmtri_rend = set(glmtri_rend)

        inter = trv1.intersection(glmtri_rend)

        print(
            f"{len(inter)} , inglm:{len(glmtri_rend)} , in trv1:{len(trv1)} , in trv2 : {len(trv2)}"
        )
        # print(f"in glmtri", glmtri_rend.difference(inter))
        # print(f"in trv1", trv1.difference(inter))

    def test_clipfunc(self):

        from random import randint

        max(30, min(randint(0, 100), 80))
        number = 1000000
        setup = dedent(
            f"""
        from random import randint
        def clamp(x, minimum, maximum):
            return minimum if x < minimum else (maximum if x > maximum else x)
        """
        )
        dur_maxmin = timeit.timeit(
            "max(30,min(randint(0,100),80))", setup=setup, number=number
        )
        print(f"max_min duration: {dur_maxmin:.2f}")

        dur_customclamp = timeit.timeit(
            "x=randint(0,100)\nclamp(x,30,80)", setup=setup, number=number
        )
        print(f"dur_customclamp duration: {dur_customclamp:.2f}")

        dur_customclamp = timeit.timeit(
            "x=randint(0,100)\n30 if x < 30 else (80 if x > 80 else x)",
            setup=setup,
            number=number,
        )
        print(f"dur_inline duration: {dur_customclamp:.2f}")

    def test_bench_triangle_raster(self):
        number = 100
        setup_big = dedent(
            f"""
        a,b,c = vec3(2.0,2.0,1.0), vec3(120,120.0,1.0),  vec3(100.0,40.0,1.0)
        screen_width, screen_height = 100,100
        """
        )

        setup_small = dedent(
            f"""
        a,b,c = vec3(2.0,2.0,1.0), vec3(12,12.0,1.0),  vec3(10.0,4.0,1.0)
        screen_width, screen_height = 100,100
        """
        )

        setups = [("big", setup_big), ("small", setup_small)]

        rots = [
            (
                "abc",
                dedent(
                    f"""
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """
                ),
            ),
            (
                "bca",
                dedent(
                    f"""
        a,b,c = b,c,a
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """
                ),
            ),
            (
                "cab",
                dedent(
                    f"""
        a,b,c = c,a,b
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """
                ),
            ),
        ]

        for setupkey, setup in setups:
            for rotinfo, setup_rot in rots:

                print(setupkey, rotinfo)
                durv1 = timeit.timeit(
                    "list(triangle_raster_v1(b,a,c,screen_width, screen_height))",
                    globals=globals(),
                    setup=setup,
                    number=number,
                )
                print(durv1)
                durv2 = timeit.timeit(
                    "list(triangle_raster_v2(b,a,c,screen_width, screen_height))",
                    globals=globals(),
                    setup=setup,
                    number=number,
                )
                print(durv2)
                durnat = timeit.timeit(
                    "list(glmtriangle_render(tri,tri_i,screen_width, screen_height))",
                    globals=globals(),
                    setup=setup + setup_rot,
                    number=number,
                )
                print(durnat)

    def test_bench_c_triangle_raster(self):
        number = 100
        setup_big = dedent(
            f"""
        import array
        output_array = array.array('I', [0]*100000)
        a,b,c = vec3(2.0,2.0,1.0), vec3(120,120.0,1.0),  vec3(100.0,40.0,1.0)
        screen_width, screen_height = 100,100
        """
        )
        setup_small = dedent(
            f"""
                           
        import array
        output_array = array.array('I', [0]*100000)
        a,b,c = vec3(2.0,2.0,1.0), vec3(12,12.0,1.0),  vec3(10.0,4.0,1.0)
        screen_width, screen_height = 100,100
        """
        )
        setups = [("big", setup_big), ("small", setup_small)]

        rots = [
            (
                "abc",
                dedent(
                    f"""
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """
                ),
            ),
            (
                "bca",
                dedent(
                    f"""
        a,b,c = b,c,a
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """
                ),
            ),
            (
                "cab",
                dedent(
                    f"""
        a,b,c = c,a,b
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """
                ),
            ),
        ]

        for setupkey, setup in setups:
            for rotinfo, setup_rot in rots:
                print(setupkey, rotinfo)
                durpy = timeit.timeit(
                    "list(glmtriangle_render(tri,tri_i,screen_width, screen_height))",
                    globals=globals(),
                    setup=setup + setup_rot,
                    number=number,
                )

                dur_cython_buffer = timeit.timeit(
                    "iterate_pixel_buffer(output_array,c_glm_triangle_render_to_buffer(tri,screen_width, screen_height,output_array))",
                    globals=globals(),
                    setup=setup + setup_rot,
                    number=number,
                )

                print(durpy, dur_cython_buffer)

    def test_c_triangle_raster(self):
        a, b, c = vec3(2.0, 2.0, 1.0), vec3(12, 12.0, 1.0), vec3(10, 4.0, 1.0)

        screen_width, screen_height = 100, 100
        tri = mat3(a, c, b)
        tri_inverse = glm.inverse(tri)

        glmtri_rend = list(
            glmtriangle_render(tri, tri_inverse, screen_width, screen_height)
        )
        print(glmtri_rend[:10])
        print(len(glmtri_rend))

        output_array = array.array("I", [0] * 100000)
        r = c_glm_triangle_render_to_buffer(
            tri, screen_width, screen_height, output_array
        )
        print(output_array[:10])
        print(r // 2)

    def test_random_triangle(self):
        screen_width, screen_height = 100, 100

        a, b, c = generate_random_triangle()
        tri = mat3(a, c, b)
        tri_inverse = glm.inverse(tri)

        glmtri_rend = list(
            glmtriangle_render(tri, tri_inverse, screen_width, screen_height)
        )
        print(glmtri_rend)
        print(f"in normal impl : {len(glmtri_rend)}")

        output_array = array.array("I", [0] * 100000)

        r = c_glm_triangle_render_to_buffer(
            tri, screen_width, screen_height, output_array
        )
        print(output_array[:10])
        cversion_match = [
            (output_array[i], output_array[i + 1]) for i in range(0, r, 2)
        ]
        print(cversion_match)
        print(f"in c impl : {len(cversion_match)}")

        topiliimage(glmtri_rend, "glmtri.png")
        topiliimage(cversion_match, "glm_cversion.png")

        m = TrianglesBuffer(100000)
        m.add_triangle_info(mat3(a, c, b))
        m.calculate_internal(screen_width, screen_height)
        index_buffer = array.array("I", [45] * 32000000)
        depth_buffer = array.array("d", [1000.0] * 32000000)
        m.raster_to_buffer(depth_buffer, index_buffer)

        def make_list():
            for xi in range(screen_width):
                for yi in range(screen_height):
                    index = ((screen_height) * xi) + yi
                    index_d = index * 4
                    if depth_buffer[index_d] < 1000:
                        yield (xi, yi)

        blitedinpureC = list(make_list())
        print("in pure_c ", len(blitedinpureC))
        topiliimage(blitedinpureC, "pure_c_version.png")

    def test_bench_pyinstrument(self):
        from pyinstrument import Profiler

        a, b, c = vec3(2.0, 2.0, 1.0), vec3(120, 120.0, 1.0), vec3(100.0, 40.0, 1.0)
        screen_width, screen_height = 100, 100

        tri = mat3(a, c, b)

        profiler = Profiler()
        profiler.start()

        # code you want to profile
        for _ in range(100):
            list(triangle_raster_v2(b, a, c, screen_width, screen_height))
            list(glmtriangle_render(tri, glm.inverse(tri), screen_width, screen_height))

        profiler.stop()

        profiler.print()


def print_info_row(c) -> str:
    if c[0] == "b6":
        charuse = "⠿"
    else:
        charuse = "⣿"

    return "\n".join(["".join([charuse for _ in range(c[2])]) for r in range(c[1])])


class TestBraile_scaling(unittest.TestCase):

    def ____fdfd_bs(self):
        return
        info = []
        rowcount = 30
        for line_count in range(1, rowcount):
            for char_count in range(1, rowcount * 5):
                interlinefactor = 0.22

                b6_h = line_count * 3 + ((line_count - 1) * interlinefactor)
                b6_w = char_count * 2

                b8_h = line_count * 4 + ((line_count - 1) * interlinefactor)

                b6ratio = b6_w / (b6_h)

                info.append(("b6", line_count, char_count, b6_w, b6_h, b6ratio))

                if line_count > 0:
                    b8ratio = b6_w / b8_h
                    info.append(("b8l1", line_count, char_count, b6_w, b8_h, b8ratio))
                b8ratio = b6_w / b8_h
                info.append(("b8", line_count, char_count, b6_w, b8_h, b8ratio))

        target_ratio = 1.0

        print(target_ratio)
        for row in range(1, 20):

            closest = sorted(
                filter(lambda x: (x[1] == row) and x[0] == "b8", info),
                key=lambda x: abs(target_ratio - x[-1]),
            )
            print(print_info_row(closest[0]))
            print()
        # for c in closest[:10]:
        #    print(c)
        #    if c[0] == "b6":
        #        charuse = "⠿"
        #    else :
        #        charuse = "⣿"


#
#    for r in range(c[1]):
#        line = "".join([charuse for c in range(c[2])])
#        print(line)

from tt3de.glm.c_math import c_floor_f, c_ceil_f, c_round_f, c_clamp_and_round_f
from tt3de.glm.c_triangle_raster import (
    mat3cast_f,
    ut_adjoint_calculation,
    ut_yvalue_calculation,
    ut_factors_calculation,
)
from tt3de.glm.c_triangle_raster import ut_output_array_set
from tt3de.glm.c_triangle_raster import iterate_pixel_buffer


class Test_c_custom_math_func(unittest.TestCase):

    def test_custom_math_artihmetic(self):
        import math

        numberlist = [-12, -2.1, -1.9, 2.3, 1.1, 2.9, 101221.2]

        for n in numberlist:
            self.assertEqual(math.floor(n), c_floor_f(n))
            self.assertEqual(math.ceil(n), c_ceil_f(n))
            self.assertEqual(round(n), c_round_f(n))
        import random

        for i in range(1000):
            n = random.normalvariate(0, 10033)
            self.assertEqual(math.floor(n), c_floor_f(n), f"floor issue with {n}")
            self.assertEqual(math.ceil(n), c_ceil_f(n), f"ceil issue with {n}")
            self.assertEqual(round(n), c_round_f(n), f"round issue with {n}")

            self.assertEqual(
                min(4000, max(round(n), 0)),
                c_clamp_and_round_f(n, 4000),
                f"clamp_and_round issue with {n}",
            )

    def test_custom_c_mat_cast(self):
        m = mat3(vec3(1.2, 3.4, 1.4), vec3(2.2, 34.4, 3.4), vec3(3.2, 6.4, 8.4))

        casted = mat3cast_f(m)
        # self.assertListEqual(casted[0],list(m[0]))
        # self.assertListEqual(casted[1],list(m[1]))
        # self.assertListEqual(casted[2],list(m[2]))

        self.assertListEqual(casted[0], list(glm.row(m, 0)))
        self.assertListEqual(casted[1], list(glm.row(m, 1)))
        self.assertListEqual(casted[2], list(glm.row(m, 2)))

    def test_yvalue_cal(self):

        m = mat3(vec3(1.2, 3.4, 1.0), vec3(2.2, 34.4, 1.0), vec3(3.2, 6.4, 1.0))
        glmadj = glm.determinant(m) * glm.inverse(m)

        glmpy_y = yvalue_from_adjoint_unprotected(glmadj, 1, 2)

        purec_y = ut_yvalue_calculation(m, 1, 2)
        print(glmpy_y, purec_y)

        self.assertAlmostEqual(glmpy_y, purec_y, 5)

    def test_yvalue_calculation_random_triangles(self):

        # generating not CCW triangles
        m = mat3(*generate_random_triangle(False))

        glmadj = glm.determinant(m) * glm.inverse(m)

        for side in range(3):
            for x in range(1, 20):
                glmpy_y = yvalue_from_adjoint_unprotected(glmadj, side, 2)

                purec_y = ut_yvalue_calculation(m, side, 2)

                self.assertAlmostEqual(glmpy_y, purec_y, 5)

    def test_adjoint_matrix(self):
        m = mat3(vec3(1.2, 3.4, 1.0), vec3(2.2, 34.4, 1.0), vec3(3.2, 6.4, 1.0))

        detm = glm.determinant(m)
        glmadj = glm.determinant(m) * glm.inverse(m)

        glmadj_det = glm.determinant(glmadj)

        cadjmatrix, cmat_determinant = ut_adjoint_calculation(m)

        self.assertAlmostEqual(detm, cmat_determinant, 4)
        # self.assertListEqual(cadjmatrix[0],list(glm.column(glmadj,0)))
        # self.assertListEqual(cadjmatrix[1],list(glm.column(glmadj,1)))
        # self.assertListEqual(cadjmatrix[2],list(glm.column(glmadj,2)))

    def test_factor_calculation(self):

        screen_width = 11
        screen_height = 11

        for i in range(100):
            tri = mat3(*generate_random_triangle())
            ax, bx, cx = glm.iround(
                glm.clamp(glm.row(tri, 0), 0.0, screen_width - 1)
            )  # round(xclamped.x),round(xclamped.y),round(xclamped.z)
            ay, by, cy = glm.iround(glm.clamp(glm.row(tri, 1), 0.0, screen_height - 1))

            factors_glm_version = (ax, ay, bx, by, cx, cy)

            factors = ut_factors_calculation(tri, screen_width - 1, screen_height - 1)

            self.assertEqual(factors_glm_version, factors)

    def test_setstuff_inside_array(self):
        output_array = array.array("I", [0] * 100000)
        ut_output_array_set(output_array, 0, 1, 2)
        ut_output_array_set(output_array, 2, 3, 4)

        a = output_array[:6]
        print(a[::2])
        print(a[1::2])
        iterated = list(iterate_pixel_buffer(output_array, 6))
        self.assertEqual(iterated[0], (1, 2))
        self.assertEqual(iterated[1], (3, 4))
        self.assertEqual(iterated[2], (0, 0))
        self.assertEqual(len(iterated), 3)


if __name__ == "__main__":
    unittest.main()
# ⠀⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯⠰⠱⠲⠳⠴⠵⠶⠷⠸⠹⠺⠻⠼⠽⠾⠿
