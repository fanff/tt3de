from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell



from tt3de.glm.primitives.primitives cimport s_drawing_primitive



from libc.math cimport fabs,sqrt

# Define region codes for the Cohen-Sutherland algorithm
DEF INSIDE = 0  # 0000
DEF LEFT = 1    # 0001
DEF RIGHT = 2   # 0010
DEF BOTTOM = 4  # 0100
DEF TOP = 8     # 1000

cdef int compute_code(float x, float y, int screen_width, int screen_height) noexcept nogil:
    cdef int code = INSIDE

    if x < 0:
        code |= LEFT
    elif x > screen_width:
        code |= RIGHT
    if y < 0:
        code |= BOTTOM
    elif y > screen_height:
        code |= TOP

    return code

# applyed during precalc
cdef int clip_in_screen(float axf, float ayf, float bxf, float byf, int screen_width, int screen_height,
                        float* ax_clipped, float* ay_clipped, float* bx_clipped, float* by_clipped) noexcept nogil :
    cdef int code1, code2, code_out
    cdef float x, y
    cdef int accept = 0

    ax_clipped[0] = axf
    ay_clipped[0] = ayf
    bx_clipped[0] = bxf
    by_clipped[0] = byf

    code1 = compute_code(axf, ayf, screen_width, screen_height)
    code2 = compute_code(bxf, byf, screen_width, screen_height)

    while True:
        if not (code1 | code2):
            accept = 1
            break
        elif code1 & code2:
            break
        else:
            code_out = code1 if code1 else code2

            if code_out & TOP:
                x = axf + (bxf - axf) * (screen_height - ayf) / (byf - ayf)
                y = <float> screen_height
            elif code_out & BOTTOM:
                x = axf + (bxf - axf) * (-ayf) / (byf - ayf)
                y = 0
            elif code_out & RIGHT:
                y = ayf + (byf - ayf) * (screen_width - axf) / (bxf - axf)
                x = <float> screen_width
            elif code_out & LEFT:
                y = ayf + (byf - ayf) * (-axf) / (bxf - axf)
                x = 0

            if code_out == code1:
                ax_clipped[0] = x
                ay_clipped[0] = y
                code1 = compute_code(ax_clipped[0], ay_clipped[0], screen_width, screen_height)
            else:
                bx_clipped[0] = x
                by_clipped[0] = y
                code2 = compute_code(bx_clipped[0], by_clipped[0], screen_width, screen_height)

    if accept:
        if (fabs((ax_clipped[0]) - axf) < 1e-6 and fabs((ay_clipped[0]) - ayf) < 1e-6 and
            fabs((bx_clipped[0]) - bxf) < 1e-6 and fabs((by_clipped[0]) - byf) < 1e-6):
            return 0  # Entire line is within the screen
        else:
            return 1  # Line is partially within the screen
    else:
        return 2  # Line is completely outside the screen



##############

# for the full raster code 
#####


cdef extern from "math.h":
    float sqrt(float)  noexcept nogil
    float abs(float)  noexcept nogil
    int max(int)  noexcept nogil

from tt3de.glm.drawing.c_drawing_buffer cimport set_depth_content

cdef void raster_line(s_drawing_primitive* dprim,
     s_drawbuffer_cell* the_raw_array,
     int raw_array_width) noexcept nogil:


    # lineRasterization(s_drawbuffer_cell* the_raw_array , int raw_array_width ,s_drawing_primitive* dprim, 
    #    float initial_x, float initial_y, float final_x, float final_y,
    #    int x, int y, int x2, int y2)
    cdef float zzp1 = dprim.mat[2][0]
    cdef float zzp2 = dprim.mat[2][1]
    
    cdef float initial_x= dprim.mat[0][0]
    cdef float initial_y= dprim.mat[1][0]

    cdef float final_x = dprim.mat[0][1]
    cdef float final_y = dprim.mat[1][1]


    lineRasterization(the_raw_array , raw_array_width , dprim, 
         initial_x,  initial_y,  zzp1, final_x,  final_y, zzp2,
        dprim.ax, dprim.ay, dprim.bx, dprim.by)


    #_raster_line(  the_raw_array , raw_array_width, dprim,      dprim.ax, dprim.ay,dprim.mat[2][0], dprim.bx, dprim.by,dprim.mat[2][1])




cdef void set_in_depth_buffer(s_drawbuffer_cell* the_raw_array, int raw_array_width,s_drawing_primitive* dprim, int x, int y,float depth,

        float wa,
        ) noexcept nogil:
    set_depth_content(the_raw_array,raw_array_width,x,y,
        depth, wa,0.0,0.0,
        dprim[0].node_id,  # pass node_id
        dprim[0].geometry_id, # pass geom 
        dprim[0].material_id,
        dprim[0].unique_id, # my primitive id 
    )


cdef void line_vertical(s_drawbuffer_cell* the_raw_array , int raw_array_width ,s_drawing_primitive* dprim, 
    float initial_y,float zzp1, 
    float final_y,float zzp2,
    int x, int y, int y2
    ) noexcept nogil:
    
    cdef float dy = final_y - initial_y

    cdef float line_full_length = abs(dy)
    cdef float in_screen_length = abs(<float>(y2-y))


    cdef float initial_factor = ((<float>y)-initial_y) / line_full_length

    cdef float factor_step = (in_screen_length/line_full_length)/line_full_length


    cdef int y_value = y
    cdef float factor = initial_factor


    cdef float diffzzz = (zzp2-zzp1)
    

    if y2>= y:
        while (y_value<=y2):
            set_in_depth_buffer(the_raw_array, raw_array_width, dprim, x, y_value, zzp1+  diffzzz * factor, factor)
            factor+=factor_step
            y_value+=1
    else:
        while (y_value>=y2):
            set_in_depth_buffer(the_raw_array, raw_array_width, dprim, x, y_value, zzp1+  diffzzz * factor, factor)
            factor+=factor_step
            y_value-=1
    



cdef void lineRasterization(s_drawbuffer_cell* the_raw_array , int raw_array_width ,s_drawing_primitive* dprim, 
        float initial_x, float initial_y,float zzp1, 
        float final_x, float final_y,float zzp2,

        int x, int y, 
        int x2, int y2) noexcept nogil:

    if x == x2:
        line_vertical(the_raw_array , raw_array_width ,dprim, 
            initial_y,zzp1, 
            final_y,  zzp2,
            x,  y,  y2
            ) 
        return
    cdef int absolute_max_y = y if y > y2 else y2
    # Calculate the direction vector of the line segment
    cdef float dx = final_x - initial_x
    cdef float dy = final_y - initial_y
    cdef float diffzzz = (zzp2-zzp1)



    cdef float alpha = dy/dx
    cdef float beta  = initial_y - (alpha * initial_x)


    # Calculate the length of the direction vector
    cdef float line_full_length = abs(dx) + abs(dy) # sqrt(dx * dx + dy * dy)


    # calculate the in screen leng
    cdef int dxinscreen = x2 - x
    cdef int dyinscreen = y2 - y
    cdef float in_screen_length =  abs(<float> dxinscreen)   + abs(<float> dyinscreen)  # sqrt(<float>(dxinscreen*dxinscreen + dyinscreen*dyinscreen))

    # factor step calculation
    cdef float factor_step = (in_screen_length/line_full_length)/line_full_length
    cdef float diff_initial_float_y = (    (<float>y)-initial_y     )     
    cdef float diff_initial_float_x = (    (<float>x)-initial_x     )     

    cdef float initial_factor =( abs(diff_initial_float_x) + abs(diff_initial_float_y))/line_full_length #sqrt(diff_initial_float_y*diff_initial_float_y + diff_initial_float_x*diff_initial_float_x) / line_full_length
    
    cdef float factor = initial_factor
    cdef float y_value_float
    cdef float y_value2_float

    cdef int y_value_int
    cdef int y_value2_int

    # calculate y and y2 for the current x value 
    cdef float x_value_float = <float> x
    cdef int x_value = x

    if x2>= x:
        while x_value <= x2 :

            y_value_float = alpha * x_value_float + beta
            y_value2_float = alpha * (x_value_float+1.0) +beta
            y_value_int   = <int> y_value_float 
            y_value2_int  = <int> y_value2_float

            if y_value2_int>= y_value_int:
                while ((y_value_int <= y_value2_int) ):

                    if (y_value_int>=0) and (y_value_int <= absolute_max_y):
                        
                        set_in_depth_buffer(the_raw_array, raw_array_width, dprim, x_value, y_value_int, zzp1+ diffzzz * factor, factor)
                    factor+=factor_step
                    y_value_int+=1
            else:
                while (y_value_int >= y_value2_int):
                    if (y_value_int>=0) and (y_value_int <= absolute_max_y):
                        set_in_depth_buffer(the_raw_array, raw_array_width, dprim, x_value, y_value_int, zzp1+  diffzzz * factor, factor)
                    factor+=factor_step
                    y_value_int-=1
            x_value += 1
            x_value_float +=1.0
    else:

        while x_value >= x2 :

            y_value_float = alpha * x_value_float + beta
            y_value2_float = alpha * (x_value_float+1.0) +beta

            y_value_int   = <int> y_value_float 
            y_value2_int  = <int> y_value2_float

            if y_value2_int>= y_value_int:
                while (y_value_int <= y_value2_int):
                    if (y_value_int>=0) and (y_value_int <= absolute_max_y):
                        set_in_depth_buffer(the_raw_array, raw_array_width, dprim, x_value, y_value_int, zzp1+diffzzz * factor, factor)
                    factor+=factor_step
                    y_value_int+=1
            else:
                while (y_value_int >= y_value2_int):
                    if (y_value_int>=0) and (y_value_int <= absolute_max_y):
                        set_in_depth_buffer(the_raw_array, raw_array_width, dprim, x_value, y_value_int,zzp1+  diffzzz * factor, factor)
                    factor+=factor_step
                    y_value_int-=1

            x_value = x_value - 1
            x_value_float = x_value_float - 1.0