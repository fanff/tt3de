from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell
from tt3de.glm.primitives.primitives cimport s_drawing_primitive

from tt3de.glm.drawing.c_drawing_buffer cimport set_depth_content,set_depth_content_with_alts

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
    
    cdef int px
    cdef int py

    cdef int w0
    cdef int w1    
    cdef int w2


    # Compute triangle bounding box
    cdef int minX 
    cdef int minY 

    cdef int maxX 
    cdef int maxY 

    if axi == bxi and axi == cxi:
        # its a very vertical triangle. 
        return
    elif ayi == byi and ayi == cyi:
        # its a very horizontal triangle
        return 
    minX = min3int(axi, bxi, cxi);
    minY = min3int(ayi, byi, cyi);
    maxX = max3int(axi, bxi, cxi);
    maxY = max3int(ayi, byi, cyi);


    # // Clip against screen bounds
    minX = max3int(minX,minX, 0);
    minY = max3int(minY,minY, 0);
    maxX = min3int(maxX,maxX, screenWidth - 1);
    maxY = min3int(maxY,maxY, screenHeight - 1);


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

cdef void set_pixel_double_weights(s_drawing_primitive* dprim,
    s_drawbuffer_cell* the_raw_array,
    int screenWidth,     int px, int py, float w0,  float w1, float  w2,float w0_alt, float w1_alt,float  w2_alt) noexcept nogil:


    cdef float azi =  dprim.mat[2][0]
    cdef float bzi =  dprim.mat[2][1]
    cdef float czi =  dprim.mat[2][2]
    cdef float sss = w0+w1+w2
    cdef float depth = (azi*w0 + bzi * w1 + czi * w2) / sss

    cdef float sss_alt = w0_alt+w1_alt+w2_alt


    set_depth_content_with_alts(the_raw_array, screenWidth, px,py, 
            depth, 
            w0/ sss,
            w1/ sss,
            w2/ sss,  

            w0_alt/sss_alt,
            w1_alt/sss_alt,
            w2_alt/sss_alt,

            dprim.node_id,  # pass node_id
            dprim.geometry_id, # pass geom 
            dprim.material_id,
            dprim.unique_id, # my primitive id 
             )



cdef float orient2d_bottom( const int ax, const  int ay,const  int bx,  const   int by , const int cx,const int cy) noexcept nogil:
    cdef float cxf = (<float> cx) 
    cdef float cyf = (<float> cy) +.49
    cdef float ayf = <float> ay
    cdef float axf = <float> ax

    return (<float>(bx-ax))*(cyf-ayf) - (<float>((by-ay))*(cxf-axf))





cdef void raster_triangle_double_weights(s_drawing_primitive* dprim,
    s_drawbuffer_cell* the_raw_array,
    int screenWidth,int screenHeight) noexcept nogil:
    # basic version of this  https://fgiesen.wordpress.com/2013/02/08/triangle-rasterization-in-practice/
    # with a dummy version of two pixel at once, 


    cdef int axi = <int> dprim.mat[0][0]
    cdef int ayi = <int> dprim.mat[1][0]
    cdef int bxi = <int> dprim.mat[0][1]
    cdef int byi = <int> dprim.mat[1][1]
    cdef int cxi = <int> dprim.mat[0][2]
    cdef int cyi = <int> dprim.mat[1][2]
    
    cdef int px
    cdef int py

    cdef int w0
    cdef int w1    
    cdef int w2
    

    cdef float w0_alt
    cdef float w1_alt
    cdef float w2_alt


    # Compute triangle bounding box
    cdef int minX 
    cdef int minY 

    cdef int maxX 
    cdef int maxY 

    if axi == bxi and axi == cxi:
        # its a very vertical triangle. 
        return
    elif ayi == byi and ayi == cyi:
        # its a very horizontal triangle
        return 
    minX = min3int(axi, bxi, cxi);
    minY = min3int(ayi, byi, cyi);
    maxX = max3int(axi, bxi, cxi);
    maxY = max3int(ayi, byi, cyi);


    # // Clip against screen bounds
    minX = max3int(minX,minX, 0);
    minY = max3int(minY,minY, 0);
    maxX = min3int(maxX,maxX, screenWidth - 1);
    maxY = min3int(maxY,maxY, screenHeight - 1);


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

            w0_alt = orient2d_bottom(bxi,byi, cxi,cyi, px,py);
            w1_alt = orient2d_bottom(cxi,cyi, axi,ayi, px,py);
            w2_alt = orient2d_bottom(axi,ayi, bxi,byi, px,py);


            # // If p is on or inside all edges, render pixel.
            if (w0 >= 0 and w1 >= 0 and w2 >= 0):
                set_pixel_double_weights(dprim, the_raw_array, screenWidth, px,py, w0, w1, w2,w0_alt, w1_alt, w2_alt,)  
            px += 1       
        py += 1 
 