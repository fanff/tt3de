
from textwrap import dedent
import timeit

import math
import glm
from tt3de.glm.pyglmtexture import IVEC3_YES, IVEC3_ZERO, VEC3_YES, VEC3_ZERO, glm_triangle_vertex_pixels, glmtriangle_render
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem


from glm import ivec2, vec2, vec3,mat3
import unittest

from fractions import Fraction

def line_nofloat(pa,pb ):
    "Bresenham's line algorithm"
    (y0, x0), (y1, x1) = pa,pb
    rev = reversed
    if abs(y1 - y0) <= abs(x1 - x0):
        x0, y0, x1, y1 = y0, x0, y1, x1
        rev = lambda x: x
    if x1 < x0:
        x0, y0, x1, y1 = x1, y1, x0, y0
    leny = abs(y1 - y0)
    for i in range(leny + 1):
        xi,yi = rev((round(Fraction(i, leny) * (x1 - x0)) + x0, (1 if y1 > y0 else -1) * i + y0))

        yield(xi,yi)

def line_float(pa,pb ):
    "Bresenham's line algorithm"
    (x0, y0), (x1, y1) = pa,pb
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            yield x,y
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            yield x,y
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy        
    yield x,y

def line_float_prot(pa,pb, maxx,maxy ):
    "Bresenham's line algorithm"
    (x0, y0), (x1, y1) = pa,pb
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            if x<maxx and x>=0 and y<maxy and y>=0:
                yield x,y 
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            if x<maxx and x>=0 and y<maxy and y>=0:
                yield x,y
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy        
    if x<maxx and x>=0 and y<maxy and y>=0:
        yield x,y

def iter_rect_full(p1,p2):
    paxi,payi = p1
    pbxi,pbyi = p2
    for xi in range(paxi,pbxi+1):
        for yi in range(payi,pbyi+1):
            yield xi,yi
def iter_vertical_line(p1,count):
    xi,ystart = p1
    for yi in range(ystart,ystart+count):
        yield xi,yi

def iter_horizontal_line(p1,count):
    xstart,yi = p1
    for xi in range(xstart,xstart+count):
        yield xi,yi

def iter_rect_diagonal_full(p1,p2):

    paxi,payi = p1
    pbxi,pbyi = p2

    diffx = pbxi-paxi
    diffy = pbyi-payi


    match diffx:
        case 0:

            match diffy:
                case 0:
                    yield paxi,payi
                    return
                case _:
                    yield from iter_vertical_line(p1,diffy+1)
                    return
        case _:
            match diffy:
                case 0:
                    yield from iter_horizontal_line(p1,diffx+1)
                    return

        

    jump_step = float(pbxi-paxi)/(pbyi-payi)
    if jump_step<=1.0:

        yi = payi

        jumpx = 0.0
        for xi in range(paxi,pbxi):
            while jumpx<1.0:
                yield xi,yi

                jumpx+=jump_step
                yi+=1
            if jumpx>=1.0:
                jumpx = jumpx-math.floor(jumpx)
        yield pbxi,pbyi
    else:
        yi = payi
        jumpx = 0.0
        for xi in range(paxi,pbxi+1):
            yield xi,yi

            jumpx+=1.0

            if jumpx>=jump_step:
                yi+=1

                jumpx = jumpx-jump_step


def inscreen_iter(p1,p2):
    # TODO Unfinished,
    """draw line pixel on the screen by protecting  the x, and y values."""
    paxi,payi = p1
    pbxi,pbyi = p2


    x_yfact = float(pbxi-paxi)/(pbyi-payi)
    yxfact = 1/x_yfact


    if p1[0]<0:
        start_x = 0
        start_y = yxfact * -p1[0]
    else:
        start_y = p1[1]
        start_x = p1[0]
    
    if start_y < 0:
        start_y = 0
        start_x = x_yfact * (-start_y)

        yield from iter_rect_diagonal_full((start_x,start_y),p2)

    else:
        yield from iter_rect_diagonal_full((start_x,start_y),p2)


class Test_scanline_iterator(unittest.TestCase):

    def test_rectfull(self):
        points = list(iter_rect_full((3,4),(3,4)))
        self.assertEqual(len(points),1)

        points = list(iter_rect_full((3,4),(4,5)))
        self.assertEqual(len(points),4)

        points = list(iter_rect_full((3,4),(5,6)))
        self.assertEqual(len(points),9)

    def test_rectfulldiagonal(self):
        points = list(iter_rect_diagonal_full((3,4),(4,5)))
        #print(points)
        self.assertEqual(len(points),2)

        points = list(iter_rect_diagonal_full((3,4),(5,6)))
        #print(points)
        self.assertEqual(len(points),3)


        # pure long diagonal
        shift = 140
        points = list(iter_rect_diagonal_full((3,4),(3+shift,4+shift)))
        self.assertEqual(len(points),shift+1)

        pa = (-1,-1)
        shiftx = 3
        shifty = 4
        pb = (3+shiftx,2+shifty)

        points = list(iter_rect_diagonal_full(pa,pb))
        print(points)
        #print(len(points),shiftx+shifty)

        #self.assertEqual(pa,points[0])
        #self.assertEqual(pb,points[-1])
        #self.assertEqual(len(points),3)

        print(list(line_float(pa,pb)))
        
        print(list(line_float_prot(pa,pb,2000,2000)))

        print(list(inscreen_iter(pa,pb)))
        import timeit
        setup=f"pa={(0,0)};pb={(100,90)}"    
        number=100000
        durnat = timeit.timeit("list(iter_rect_diagonal_full(pa,pb))",globals=globals(),setup=setup,number=number)
        dur_in_nat = timeit.timeit("list(inscreen_iter(pa,pb))",globals=globals(),setup=setup,number=number)

        dur_f = timeit.timeit("list(line_float(pa,pb))",globals=globals(),setup=setup,number=number)
        dur_fp = timeit.timeit("list(line_float_prot(pa,pb,2000,2000))",globals=globals(),setup=setup,number=number)

        print(durnat,dur_in_nat,dur_f,dur_fp)
        



orient2d = glm.determinant
def orient2di(a,b,c)->int:
    return (b.x-a.x)*(c.y-a.y) - (b.y-a.y)*(c.x-a.x)


class Test_TriangleScanLine(unittest.TestCase):
    
    def test_one(self):
        a,b,c = vec3(2.0,2.0,1.0), vec3(120,120.0,1.0),  vec3(100.0,40.0,1.0)
        
        screen_width, screen_height = 100,100


        trv1 = list( triangle_raster_v1(b,a,c,screen_width, screen_height) )

        trv2 = list( triangle_raster_v2(b,a,c,screen_width, screen_height) )

        tri = mat3(a,c,b)
        glmtri_rend = list(glmtriangle_render(tri,glm.inverse(tri),screen_width, screen_height))

        trv1 = set(trv1)

        glmtri_rend = set(glmtri_rend)

        inter=trv1.intersection(glmtri_rend)

        print(f"{len(inter)} , inglm:{len(glmtri_rend)} , in trv1:{len(trv1)} , in trv2 : {len(trv2)}")
        #print(f"in glmtri", glmtri_rend.difference(inter))
        #print(f"in trv1", trv1.difference(inter))
    def test_clipfunc(self):

        from random import randint
        max(30,min(randint(0,100),80))
        number = 1000000
        setup=dedent(f"""
        from random import randint
        def clamp(x, minimum, maximum):
            return minimum if x < minimum else (maximum if x > maximum else x)
        """)
        dur_maxmin = timeit.timeit("max(30,min(randint(0,100),80))",setup=setup,number=number)
        print(f"max_min duration: {dur_maxmin:.2f}")


        dur_customclamp = timeit.timeit("x=randint(0,100)\nclamp(x,30,80)",setup=setup,number=number)
        print(f"dur_customclamp duration: {dur_customclamp:.2f}")

        dur_customclamp = timeit.timeit("x=randint(0,100)\n30 if x < 30 else (80 if x > 80 else x)",setup=setup,number=number)
        print(f"dur_inline duration: {dur_customclamp:.2f}")




    def test_bench_big_triangle_raster(self):
        number=5000
        setup_big=dedent(f"""
        a,b,c = vec3(2.0,2.0,1.0), vec3(120,120.0,1.0),  vec3(100.0,40.0,1.0)
        screen_width, screen_height = 100,100
        """)

        setup_small=dedent(f"""
        a,b,c = vec3(2.0,2.0,1.0), vec3(12,12.0,1.0),  vec3(10.0,4.0,1.0)
        screen_width, screen_height = 100,100
        """)

        setups = [("big",setup_big),("small",setup_small)]
        
        rots=[("abc",dedent(f"""
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """)),
        ("bca",dedent(f"""
        a,b,c = b,c,a
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """)),
        ("cab",dedent(f"""
        a,b,c = c,a,b
        tri = mat3(a,c,b)
        tri_i = glm.inverse(tri)
        """))]

        for setupkey , setup in setups:
            for rotinfo , setup_rot in rots:

                print(setupkey,rotinfo)
                durv1 = timeit.timeit("list(triangle_raster_v1(b,a,c,screen_width, screen_height))",globals=globals(),setup=setup,number=number)
                print(durv1)
                durv2 = timeit.timeit("list(triangle_raster_v2(b,a,c,screen_width, screen_height))",globals=globals(),setup=setup,number=number)
                print(durv2)
                durnat = timeit.timeit("list(glmtriangle_render(tri,tri_i,screen_width, screen_height))",globals=globals(),setup=setup+setup_rot,number=number)
                print(durnat)




    def test_bench_pyinstrument(self):
        from pyinstrument import Profiler
        a,b,c = vec3(2.0,2.0,1.0), vec3(120,120.0,1.0),  vec3(100.0,40.0,1.0)
        screen_width, screen_height = 100,100

        tri = mat3(a,c,b)


        profiler = Profiler()
        profiler.start()

        # code you want to profile
        for _ in range(100):
            list(triangle_raster_v2(b,a,c,screen_width, screen_height))
            list(glmtriangle_render(tri,glm.inverse(tri),screen_width, screen_height))


        profiler.stop()

        profiler.print()



def triangle_raster_v1(a:vec3,b:vec3,c:vec3,screenWidth,screenHeight):
    v0,v1,v2 = glm.iround(a),glm.iround(b),glm.iround(c)
    #print(" vectors index : ")
    #print(v0,v1,v2)

    minX = glm.iround(glm.min(a.x, b.x, c.x))
    minY = glm.iround(glm.min(a.y, b.y, c.y))
    maxX = glm.iround(glm.max(a.x, b.x, c.x))
    maxY = glm.iround(glm.max(a.y, b.y, c.y))
    minX = max(minX, 0)
    minY = max(minY, 0)
    maxX = min(maxX, screenWidth - 1)
    maxY = min(maxY, screenHeight - 1)

    #print(f"boundingx ",minX,maxX)
    #print(f"boundingy ",minY,maxY)
    A01 = v0.y - v1.y 
    A12 = v1.y - v2.y
    A20 = v2.y - v0.y

    B01 = v1.x - v0.x
    B12 = v2.x - v1.x
    B20 = v0.x - v2.x

    p = glm.ivec3(minX,minY,1)
    w0_row:int = orient2di(v1, v2, p)
    w1_row:int = orient2di(v2, v0, p)
    w2_row:int = orient2di(v0, v1, p)
    #print(w0_row,w1_row,w2_row)
#
    #print("factors A",A01,A12,A20)
    #print("factors B",B01,B12,B20)
    for yi in range(minY,maxY+1):
        # Barycentric coordinates at start of row
        w0 = w0_row
        w1 = w1_row
        w2 = w2_row

        for xi in range(minX,maxX+1):#(p.x = minX; p.x <= maxX; p.x++) {

            #print( w0,w1,w2   )
            #// If p is on or inside all edges, render pixel.
            if (w0 >= 0 and w1 >= 0 and w2 >= 0):
                yield xi,yi
#
            # One step to the right
            w0 += A12
            w1 += A20
            w2 += A01
        # One row step
        w0_row += B12
        w1_row += B20
        w2_row += B01

def triangle_raster_v2(a:vec3,b:vec3,c:vec3,screenWidth,screenHeight):
    v0,v1,v2 = glm.iround(a),glm.iround(b),glm.iround(c)
    #print(" vectors index : ")
    #print(v0,v1,v2)

    minX = glm.iround(glm.min(a.x, b.x, c.x))
    minY = glm.iround(glm.min(a.y, b.y, c.y))
    maxX = glm.iround(glm.max(a.x, b.x, c.x))
    maxY = glm.iround(glm.max(a.y, b.y, c.y))
    minX = max(minX, 0)
    minY = max(minY, 0)
    maxX = min(maxX, screenWidth - 1)
    maxY = min(maxY, screenHeight - 1)

    #print(f"boundingx ",minX,maxX)
    #print(f"boundingy ",minY,maxY)
    A01 = v0.y - v1.y 
    A12 = v1.y - v2.y
    A20 = v2.y - v0.y

    B01 = v1.x - v0.x
    B12 = v2.x - v1.x
    B20 = v0.x - v2.x
    avec = glm.ivec3(A12,A20,A01)
    bvec = glm.ivec3(B12,B20,B01)
    p = glm.ivec3(minX,minY,1)
    #w0_row:int = orient2di(v1, v2, p)
    #w1_row:int = orient2di(v2, v0, p)
    #w2_row:int = orient2di(v0, v1, p)

    w_row = glm.ivec3(orient2di(v1, v2, p) , orient2di(v2, v0, p) , orient2di(v0, v1, p) )

    w = glm.ivec3(0)
    #print(w0_row,w1_row,w2_row)
    

    #print("factors A",A01,A12,A20)
    #print("factors B",B01,B12,B20)
    for yi in range(minY,maxY+1):
        # Barycentric coordinates at start of row
        w=glm.ivec3(w_row)
        for xi in range(minX,maxX+1):#(p.x = minX; p.x <= maxX; p.x++) {

            #print( w0,w1,w2   )
            #// If p is on or inside all edges, render pixel.
            
            #if (w0 >= 0 and w1 >= 0 and w2 >= 0):
            #glm.all(glm.greaterThanEqual(w,IVEC3_ZERO)) -> this is slower here. probeably because function call?
            # (w>=IVEC3_ZERO)==IVEC3_YES: -> faster version 
            if (w>=IVEC3_ZERO)==IVEC3_YES:
                yield xi,yi
#
            # One step to the right
            # w0 += A12
            # w1 += A20
            # w2 += A01

            w = w+ avec
        # One row step
        #w0_row += B12
        #w1_row += B20
        #w2_row += B01
        w_row = w_row+ bvec

def print_info_row(c) -> str:
    if c[0] == "b6":
        charuse = "⠿"
    else :
        charuse = "⣿"


    return "\n".join(["".join([charuse for _ in range(c[2])])  for r in range(c[1])])
class TestBraile_scaling(unittest.TestCase):

    def ____fdfd_bs(self):
        return
        info = []
        rowcount = 30
        for line_count in range(1,rowcount):
            for char_count in range(1,rowcount*5):
                interlinefactor = 0.22


                b6_h = line_count*3 + ((line_count-1)*interlinefactor)
                b6_w = char_count*2 

                b8_h = line_count*4 + ((line_count-1)*interlinefactor)
                
                b6ratio = (b6_w/(b6_h))
                
                info.append(("b6",line_count,char_count,b6_w,b6_h,b6ratio))

                if line_count>0:
                    b8ratio = (b6_w/b8_h)
                    info.append(("b8l1",line_count,char_count,b6_w,b8_h,b8ratio))
                b8ratio = (b6_w/b8_h)
                info.append(("b8",line_count,char_count,b6_w,b8_h,b8ratio))

        target_ratio= 1.0

        print(target_ratio)
        for row in range(1,20):
            
            closest = sorted(filter(lambda x:(x[1] == row ) and x[0]=="b8",info),key=lambda x:  abs(target_ratio-x[-1]))
            print( print_info_row(closest[0]) ) 
            print()
        #for c in closest[:10]:
        #    print(c)
        #    if c[0] == "b6":
        #        charuse = "⠿"
        #    else :
        #        charuse = "⣿"
#
        #    for r in range(c[1]):
        #        line = "".join([charuse for c in range(c[2])])
        #        print(line)


if __name__ == "__main__":
    unittest.main()
#⠀⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯⠰⠱⠲⠳⠴⠵⠶⠷⠸⠹⠺⠻⠼⠽⠾⠿