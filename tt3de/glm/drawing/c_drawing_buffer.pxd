
ctypedef packed struct s_canvas_cell:
    unsigned char[8] aleph

ctypedef packed struct s_drawbuffer_cell:
    float depth_value

    # weights for drawing.
    float w1
    float w2
    float w3 

    float w1_alt
    float w2_alt
    float w3_alt 


    int   primitiv_id 
    int   geom_id
    int   node_id
    int   material_id

cdef class DrawingBuffer:
    cdef s_canvas_cell[:] canvas
    cdef s_canvas_cell* _raw_canvas
    cdef list style_array

    cdef s_drawbuffer_cell[:] drawbuffer
    cdef s_drawbuffer_cell* _raw_data
    cdef int size
    cdef int width
    cdef int height


    cdef unsigned char [6] bit_reductions


    cdef s_drawbuffer_cell* get_raw_depth_buffer(self)
    cdef s_canvas_cell* get_raw_canvas_buffer(self)
    cdef inline int linear_idx(self,int xi,int yi)
    
    cpdef set_bit_reduction(self, list params)
    cpdef int hash_value(self, list value)

    
    cdef unsigned int get_width(self)
    cdef unsigned int get_height(self)
    cpdef tuple shape(self)
    cpdef void hard_clear(self,float init_depth)
    
    cpdef void set_depth_content(self,const int xi,const int yi,
                                float depth_value, 
                                float w1,
                                float w2,
                                float w3 ,
                                int   node_id,
                                int   geom_id,
                                int   material_id ,
                                int   primitiv_id ,
    )

    cpdef void set_canvas_content(self,
        int xi,
        int yi,
        unsigned char fr,
        unsigned char fg,
        unsigned char fb,
        unsigned char br,
        unsigned char bg,
        unsigned char bb,
        unsigned char g1,
        unsigned char g2)
    
    cdef unsigned char* aleph(self,int index)
    

    cpdef list canvas_to_list(self)
    cpdef list canvas_to_list_ofstyled(self)
    cpdef list drawbuffer_to_list(self)



cdef void set_depth_content(s_drawbuffer_cell* the_raw_array,
        const int raw_array_width,
        const int xi,const int yi,
        const float depth_value, 
        const float w1 ,
        const float w2 ,
        const float w3 ,
        const int   node_id,
        const int   geom_id,
        const int   material_id ,
        const int   primitiv_id ,
    ) noexcept nogil


cdef void set_depth_content_with_alts(s_drawbuffer_cell* the_raw_array,
        const int raw_array_width,
        const int xi,const int yi,
        const float depth_value, 
        const float w1 ,
        const float w2 ,
        const float w3 ,
        const float w1_alt ,
        const float w2_alt ,
        const float w3_alt ,
        const int   node_id,
        const int   geom_id,
        const int   material_id ,
        const int   primitiv_id ,
    ) noexcept nogil