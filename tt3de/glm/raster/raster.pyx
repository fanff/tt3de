

from tt3de.glm.c_math cimport round_in_screen
from tt3de.glm.c_math cimport flat_determinant_g

from tt3de.glm.c_buffer cimport s_buffer


from tt3de.glm.primitives.primitives cimport PrimitivesBuffer,s_drawing_primitive

from tt3de.glm.drawing.c_drawing_buffer cimport DrawingBuffer

from tt3de.glm.raster.c_raster_point cimport raster_point
from tt3de.glm.raster.c_raster_point import raster_on_stuff
from tt3de.glm.raster.c_raster_line cimport clip_in_screen,raster_line



DEF PRIMITIVE_TYPE_POINT=0
DEF PRIMITIVE_TYPE_LINE=1
DEF PRIMITIVE_TYPE_TRIANGLE=2



cpdef void raster_precalc(PrimitivesBuffer primitive_buffer, 
        DrawingBuffer drawing_buffer):
    cdef unsigned int idx_limit = primitive_buffer.primitive_count()
    cdef s_buffer* buff  =  primitive_buffer.rawaccess_array()

    _precalc(buff,idx_limit,drawing_buffer.get_width(),drawing_buffer.get_height())


cdef void _precalc(s_buffer* primitive_array,unsigned int idx_limit,

    unsigned int screen_width,
    unsigned int screen_height):


    cdef s_drawing_primitive* tr

    cdef unsigned int scw_1 = screen_width-1
    cdef unsigned int sch_1 = screen_height-1

    # Elements of the input matrix
    cdef float axf 
    cdef float ayf 
    cdef float bxf 
    cdef float byf 
    cdef float cxf 
    cdef float cyf 

    # some clipped values scratch pad 
    cdef int clipping_result 
    cdef float axf_clipped = 0.0
    cdef float ayf_clipped = 0.0
    cdef float bxf_clipped = 0.0
    cdef float byf_clipped = 0.0



    cdef size_t side;

    cdef size_t i;
    for i in range(idx_limit):

        tr=<s_drawing_primitive* > ((<char*> ((primitive_array).data)) + sizeof(s_drawing_primitive) * i )

        if tr.primitive_type_id == PRIMITIVE_TYPE_POINT:
            
            axf = tr.mat[0][0]
            ayf = tr.mat[1][0]

            if (axf < 0.0) or (axf >= scw_1) or (ayf < 0.0) or (ayf >= scw_1):
                tr.clipped=1
            else:
                tr.clipped=0
                tr.ax = round_in_screen(axf, scw_1)
                tr.ay = round_in_screen(ayf, sch_1)

        elif tr.primitive_type_id == PRIMITIVE_TYPE_LINE:
            axf = tr.mat[0][0]
            ayf = tr.mat[1][0]

            bxf = tr.mat[0][1]
            byf = tr.mat[1][1]



           
            
            clipping_result = clip_in_screen(axf,ayf,bxf,byf,screen_width,screen_height,
            &axf_clipped,
            &ayf_clipped,
            &bxf_clipped,
            &byf_clipped,
            
            )
            # if line full clipped  
            if clipping_result == 2:
                tr.clipped=1
            else:
                tr.clipped=0
                # we can precalc this
                tr.adjoint[0][2] = ayf - byf
                tr.adjoint[1][2] = bxf - axf
                tr.adjoint[2][2] = axf*byf - bxf*ayf
                
                # 
                # that will be clipped to screen
                # clipped coordinate to draw the line to/from.
                tr.ax = round_in_screen(axf_clipped, scw_1)
                tr.ay = round_in_screen(ayf_clipped, sch_1)

                tr.bx = round_in_screen(bxf_clipped, scw_1)
                tr.by = round_in_screen(byf_clipped, sch_1)


        elif tr.primitive_type_id == PRIMITIVE_TYPE_TRIANGLE:
            tr.clipped=1
            #tr = &(primitiv[i])
            tr[0].flat_determinant = flat_determinant_g(tr.mat)
            
            axf = tr.mat[0][0]
            ayf = tr.mat[1][0]
            bxf = tr.mat[0][1]
            byf = tr.mat[1][1]
            cxf = tr.mat[0][2]
            cyf = tr.mat[1][2]

            # getting the rounded values of the corners; 
            # clamped into the screen
            tr.ax = round_in_screen(axf, scw_1)
            tr.ay = round_in_screen(ayf, sch_1)
            tr.bx = round_in_screen(bxf, scw_1)
            tr.by = round_in_screen(byf, sch_1)
            tr.cx = round_in_screen(cxf, scw_1)
            tr.cy = round_in_screen(cyf, sch_1)
            

            # Calculate the cofactors (with assumption that last row is [1, 1, 1])
            tr.adjoint[0][0] = byf - cyf  #diff y 
            tr.adjoint[0][1] = cyf - ayf
            tr.adjoint[0][2] = ayf - byf
            tr.adjoint[1][0] = cxf - bxf  # diff x 
            tr.adjoint[1][1] = axf - cxf
            tr.adjoint[1][2] = bxf - axf
            tr.adjoint[2][0] = bxf*cyf - cxf*byf
            tr.adjoint[2][1] = cxf*ayf - axf*cyf
            tr.adjoint[2][2] = axf*byf - bxf*ayf
            #  C
            # A  B
            # some extra values could be calculated :
            # segment index 
            # 0: CB
            # 1: AC
            # 2: BA
            
            side=0
            if tr.cx!=tr.bx:
                tr.coefs[side].alpha = (-tr.adjoint[0][side])/tr.adjoint[1][side]
                tr.coefs[side].beta = (-tr.adjoint[2][side])/tr.adjoint[1][side]

            side=1
            if tr.ax!=tr.cx:
                tr.coefs[side].alpha = (-tr.adjoint[0][side])/tr.adjoint[1][side]
                tr.coefs[side].beta = (-tr.adjoint[2][side])/tr.adjoint[1][side]
            side=2
            if tr.ax!=tr.bx:
                tr.coefs[side].alpha = (-tr.adjoint[0][side])/tr.adjoint[1][side]
                tr.coefs[side].beta = (-tr.adjoint[2][side])/tr.adjoint[1][side]







cpdef void raster_all(PrimitivesBuffer primitive_buffer, 
                DrawingBuffer drawing_buffer):
    cdef unsigned int idx_limit = primitive_buffer.primitive_count()
    cdef s_buffer* primitive_array  =  primitive_buffer.rawaccess_array()
    _raster_all(primitive_array,
                idx_limit,
                drawing_buffer.get_width(),
                drawing_buffer.get_height(),
                drawing_buffer)

cdef void _raster_all(s_buffer* primitive_array,
                    unsigned int idx_limit,
                    unsigned int screen_width,
                    unsigned int screen_height,
                    DrawingBuffer drawing_buffer):
    cdef size_t i;
    cdef s_drawing_primitive* buff
    for i in range(idx_limit):

        buff= <s_drawing_primitive* > ((<char*> ((primitive_array).data)) + sizeof(s_drawing_primitive) * i )


        if buff.primitive_type_id == PRIMITIVE_TYPE_POINT:
            raster_point(buff,drawing_buffer)
        elif buff.primitive_type_id == PRIMITIVE_TYPE_LINE:
            raster_line(buff,drawing_buffer)