from tt3de.glm.drawing.c_drawing_buffer cimport DrawingBuffer
from tt3de.glm.primitives.primitives cimport s_drawing_primitive




from libc.math cimport fabs,sqrt

# Define region codes for the Cohen-Sutherland algorithm
DEF INSIDE = 0  # 0000
DEF LEFT = 1    # 0001
DEF RIGHT = 2   # 0010
DEF BOTTOM = 4  # 0100
DEF TOP = 8     # 1000

cdef int compute_code(float x, float y, int screen_width, int screen_height):
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
                        float* ax_clipped, float* ay_clipped, float* bx_clipped, float* by_clipped):
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
                y = screen_height
            elif code_out & BOTTOM:
                x = axf + (bxf - axf) * (-ayf) / (byf - ayf)
                y = 0
            elif code_out & RIGHT:
                y = ayf + (byf - ayf) * (screen_width - axf) / (bxf - axf)
                x = screen_width
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






cdef void raster_line(s_drawing_primitive* dprim,
    DrawingBuffer drawing_buffer):

    _raster_line( drawing_buffer,dprim, dprim.ax, dprim.ay,dprim.mat[2][0], dprim.bx, dprim.by,dprim.mat[2][1])




cdef void set_in_depth_buffer(DrawingBuffer drawing_buffer,s_drawing_primitive* dprim, int x, int y,float depth,

        float wa,
        ):
    drawing_buffer.set_depth_content(x,y, 
            depth, wa,0.0,0.0,  
            dprim.node_id,  # pass node_id
            dprim.geometry_id, # pass geom 
            dprim.material_id,
            dprim.unique_id, # my primitive id 
             )



cdef void _raster_line(DrawingBuffer drawing_buffer,s_drawing_primitive* dprim, int x, int y, float z, int x2, int y2, float z2):
    cdef:
        bint yLonger = False
        int incrementVal, endVal
        int shortLen = y2 - y
        int longLen = x2 - x
        double decInc, j = 0.0
        float depth = 1.0
        float ratioptop = 0.0
        float zzp1 = dprim.mat[2][0]
        float zzp2 = dprim.mat[2][1]

        float line_full_length = sqrt ((dprim.adjoint[1][2])**2 + (dprim.adjoint[0][2])**2)
        float initial_x= dprim.mat[0][0]
        float initial_y= dprim.mat[1][0]

        float final_x = dprim.mat[0][1]
        float final_y = dprim.mat[1][1]


        int x_set
        int y_set

    if abs(shortLen) > abs(longLen):
        # swap shortLen and longLen
        shortLen, longLen = longLen, shortLen
        yLonger = True

    endVal = longLen
    if longLen < 0:
        incrementVal = -1
        longLen = -longLen
        zzp1,zzp2 = zzp2,zzp1

    else:

        incrementVal = 1
        #zzp1,zzp2 = z,z2


    if longLen == 0:
        decInc = float(shortLen)
    else:
        decInc = float(shortLen) / float(longLen)

    if yLonger:
        for i in range(0, endVal, incrementVal):
            x_set = x + int(j)
            y_set = y + i

            
            ratioptop = sqrt((x_set-initial_x)**2 + (y_set-initial_y)**2)/line_full_length
            
            depth = zzp1  + ((zzp2-zzp1)*ratioptop)

            set_in_depth_buffer(drawing_buffer,dprim, x_set, y_set, depth,ratioptop)
            j += decInc
    else:
        for i in range(0, endVal, incrementVal):
            x_set = x + i
            y_set = y + int(j)        
            ratioptop = sqrt(float(x_set-initial_x)**2 + float(y_set-initial_y)**2)/line_full_length

            depth = zzp1 + ((zzp2-zzp1)*ratioptop)
            set_in_depth_buffer(drawing_buffer,dprim, x_set, y_set, depth,ratioptop)
            j += decInc




