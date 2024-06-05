from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell
from tt3de.glm.primitives.primitives cimport s_drawing_primitive

from tt3de.glm.drawing.c_drawing_buffer cimport set_depth_content

from libc.math cimport fabs,sqrt


cdef int min3int(int a, int b, int c) noexcept nogil:
    cdef int min_val = a
    if b < min_val:
        min_val = b
    if c < min_val:
        min_val = c
    return min_val

cdef int max3int(int a, int b, int c) noexcept nogil:
    cdef int max_val = a
    if b > max_val:
        max_val = b
    if c > max_val:
        max_val = c
    return max_val



cdef int orient2di( const int ax, const  int ay,const  int bx,  const   int by , const int cx,const int cy) noexcept nogil:
    return (bx-ax)*(cy-ay) - (by-ay)*(cx-ax)


cdef void set_pixel(s_drawing_primitive* dprim,
    s_drawbuffer_cell* the_raw_array,
    int screenWidth,     int px, int py, float w0,  float w1, float  w2) noexcept nogil:
    cdef float azi =  dprim.mat[2][0]
    cdef float bzi =  dprim.mat[2][1]
    cdef float czi =  dprim.mat[2][2]
    cdef float sss = w0+w1+w2
    cdef float depth = (azi*w0 + bzi * w1 + czi * w2) / sss

    set_depth_content(the_raw_array, screenWidth, px,py, 
            depth, w0/ sss,w1/ sss,w2/ sss,  
            dprim.node_id,  # pass node_id
            dprim.geometry_id, # pass geom 
            dprim.material_id,
            dprim.unique_id, # my primitive id 
             )


cdef void raster_triangle(s_drawing_primitive* dprim,
    s_drawbuffer_cell* the_raw_array,
    int screenWidth,int screenHeight) noexcept nogil:
    # basic version of this  https://fgiesen.wordpress.com/2013/02/08/triangle-rasterization-in-practice/


    cdef int axi = <int> dprim.mat[0][0]
    cdef int ayi = <int> dprim.mat[1][0]
    
    cdef int bxi = <int> dprim.mat[0][1]
    cdef int byi = <int> dprim.mat[1][1]
    
    cdef int cxi = <int> dprim.mat[0][2]
    cdef int cyi = <int> dprim.mat[1][2]
    


    # Compute triangle bounding box
    cdef int minX = min3int(axi, bxi, cxi);
    cdef int minY = min3int(ayi, byi, cyi);

    cdef int maxX = max3int(axi, bxi, cxi);
    cdef int maxY = max3int(ayi, byi, cyi);


    cdef int px
    cdef int py

    cdef int w0
    cdef int w1    
    cdef int w2


    # // Clip against screen bounds
    minX = max(minX, 0);
    minY = max(minY, 0);
    maxX = min(maxX, screenWidth - 1);
    maxY = min(maxY, screenHeight - 1);


    # // Rasterize
    #for (py = minY; py <= maxY; py++) {
    py = minY
    while py<=maxY:
        px = minX
        while px<=maxX:
        # for (px = minX; px <= maxX; px++) {
            #// Determine barycentric coordinates
            w0 = orient2di(bxi,byi, cxi,cyi, px,py);
            w1 = orient2di(cxi,cyi, axi,ayi, px,py);
            w2 = orient2di(axi,ayi, bxi,byi, px,py);

            # // If p is on or inside all edges, render pixel.
            if (w0 >= 0 and w1 >= 0 and w2 >= 0):
                set_pixel(dprim, the_raw_array, screenWidth, px,py, w0, w1, w2)  
            px += 1       
        py += 1 