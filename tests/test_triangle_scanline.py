


import math
from context import tt3de

from tt3de.glm.pyglmtexture import glm_triangle_vertex_pixels, glmtriangle_render
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem


from glm import ivec2, vec2, vec3,mat3
import unittest






import decimal

def drange(x, y, jump):
  # float curse warning
  while x < y:
    yield x
    x += jump



class TestScanLine(unittest.TestCase):

    def test_many(self):
        import glm

        tri = mat3(vec3(0.0,0.0,1.0), vec3(24,0.0,1.0),  vec3(10.0,10.0,1.0))
        st = glm.translate(vec2(-12,-5))
        ss = glm.scale(vec2(1,1)*1.0)
        sr = glm.rotate(math.radians(30))

        st2 = glm.translate(vec2(20,50))

        tri = (st2*sr*ss*st)*tri#glm.translate(vec2(16,6))*sr*st*
        print(tri)
        return        
        screen_min = ivec2(5,5)
        screen_max = ivec2(100,100)
        print(list(glm_triangle_vertex_pixels(tri,screen_min,screen_max)))
        #print(sr*tri)

        #res = list(glmtriangle_render(tri,100,100))
        adjoint = glm.determinant(tri)* glm.inverse(tri)
        for side in range(3):
            a, b, c = glm.row(adjoint,side)
            if b == 0:  # Vertical line case
                return None
            
            print( f"Y= {-a/b} X + {-c/b}")
        return
        adjoint = glm.determinant(tri)* glm.inverseTranspose(tri)


        #glm.clamp(tri[1],vec3(-1.0,-1.0,zvalue),vec3(1,1,zvalue))
        
        print(tri)
        print(adjoint)
        print(glm.column(adjoint,1))
        def line_equation_from_adjoint(adj_matrix:mat3, side, x):
            a, b, c = glm.row(adj_matrix,side)
            if b == 0:  # Vertical line case
                return None
            return -(a * x + c) / b
        print(line_equation_from_adjoint(adjoint, 2,   -0.5))

        print(line_equation_from_adjoint(adjoint, 2,   -0.75))

        print("dfsq")
        xclamped = glm.clamp((tri[0]),-3,3)
        minx = glm.min(xclamped)
        maxx = glm.max(xclamped)
        print(minx,maxx)
        return
        maxx = glm.max(tri[0])

        ax = tri[0][0]

        print((ax))
        for x in drange(minx,maxx,1):
            
            if x<=ax:
                
                miny = line_equation_from_adjoint(adjoint, 0,   x)
                maxy = line_equation_from_adjoint(adjoint, 2,   x)

                print("1",x, miny,maxy)
            else:
                pass
                miny = line_equation_from_adjoint(adjoint, 1,   x)
                maxy = line_equation_from_adjoint(adjoint, 0,   x)
#
                print("2",x, miny,maxy)
        



def print_info_row(c) -> str:
    if c[0] == "b6":
        charuse = "⠿"
    else :
        charuse = "⣿"


    return "\n".join(["".join([charuse for _ in range(c[2])])  for r in range(c[1])])
class TestBraile_scaling(unittest.TestCase):

    def test_bs(self):
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