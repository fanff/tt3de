
import random
from glm import vec3,iround,ivec3
from glm import determinant as orient2d
import glm

IVEC3_ZERO = ivec3(0)
IVEC3_YES = ivec3(1)

def orient2di(a,b,c)->int:
    return (b.x-a.x)*(c.y-a.y) - (b.y-a.y)*(c.x-a.x)

def triangle_raster_v1(a:vec3,b:vec3,c:vec3,screenWidth,screenHeight):
    """using https://fgiesen.wordpress.com/2013/02/10/optimizing-the-basic-rasterizer/
    as inspiration source. 

    most of the loop run in actual pure python
    """
    v0,v1,v2 = iround(a),iround(b),iround(c)
    #print(" vectors index : ")
    #print(v0,v1,v2)

    minX = iround(glm.min(a.x, b.x, c.x))
    minY = iround(glm.min(a.y, b.y, c.y))
    maxX = iround(glm.max(a.x, b.x, c.x))
    maxY = iround(glm.max(a.y, b.y, c.y))
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

    p = ivec3(minX,minY,1)
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
    """
    same as v1

    most of the loop run will use a glm.ivec3 to sum the weights. 
    this should use SIMD in glm, but it actually do not because
    the code runs at the exact same speed. (a bit lower actually)

    Could this be because the glm lib has a "type" check feature enabled ? 
    
    
    """
    v0,v1,v2 = iround(a),iround(b),iround(c)
    #print(" vectors index : ")
    #print(v0,v1,v2)

    minX = iround(glm.min(a.x, b.x, c.x))
    minY = iround(glm.min(a.y, b.y, c.y))
    maxX = iround(glm.max(a.x, b.x, c.x))
    maxY = iround(glm.max(a.y, b.y, c.y))
    minX = max(minX, 0)
    minY = max(minY, 0)
    maxX = min(maxX, screenWidth - 1)
    maxY = min(maxY, screenHeight - 1)

    #print(f"boundingx ",minX,maxX)
    #print(f"boundingy ",minY,maxY)
    a01 = v0.y - v1.y 
    a12 = v1.y - v2.y
    a20 = v2.y - v0.y

    b01 = v1.x - v0.x
    b12 = v2.x - v1.x
    b20 = v0.x - v2.x
    avec = ivec3(a12,a20,a01)
    bvec = ivec3(b12,b20,b01)
    p = ivec3(minX,minY,1)
    #w0_row:int = orient2di(v1, v2, p)
    #w1_row:int = orient2di(v2, v0, p)
    #w2_row:int = orient2di(v0, v1, p)

    w_row = ivec3(orient2di(v1, v2, p) , orient2di(v2, v0, p) , orient2di(v0, v1, p) )

    w = ivec3(0)
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





def generate_random_triangle(CW_option=True):
    # Generate random coordinates for the triangle vertices
    a = vec3(random.uniform(2, 5), random.uniform(3, 5), 1.0)
    b = vec3(random.uniform(10, 12), random.uniform(10, 12), 1.0)
    c = vec3(random.uniform(15, 20), random.uniform(2, 8), 1.0)
    
    # Function to calculate the signed area of the triangle
    def signed_area(a, b, c):
        return 0.5 * ((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y))

    # Ensure the triangle has the desired orientation
    if CW_option:
        if signed_area(a, b, c) > 0:
            a, b = b, a  # Swap to make it clockwise
    else:
        if signed_area(a, b, c) < 0:
            a, b = b, a  # Swap to make it counter-clockwise

    return a, b, c
