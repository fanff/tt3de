from libc.string cimport memset
from libc.stdlib cimport malloc, free
import cython


from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell,s_canvas_cell

@cython.boundscheck(False)
@cython.wraparound(False)
cdef class DrawingBuffer:
    

    def __cinit__(self, int width,int height):
        cdef int _size = width*height
        
        
        self._raw_data = <s_drawbuffer_cell*>malloc(_size * sizeof(s_drawbuffer_cell))
        if not self._raw_data:
            raise MemoryError("Failed to allocate depth buffer.")


        self._raw_canvas = <s_canvas_cell*>malloc(_size * sizeof(s_canvas_cell))
        if not self._raw_canvas:
            free(self._raw_data)
            raise MemoryError("Failed to allocate canvas buffer.")
        self.size = _size
        self.width = width
        self.height =height

        self.drawbuffer = <s_drawbuffer_cell[:_size]> self._raw_data
        self.canvas = <s_canvas_cell[:_size]> self._raw_canvas

    cdef unsigned char* aleph(self,int index):
        return &(self.canvas[index].aleph[0])



    cdef inline int linear_idx(self,const int xi,const int yi):
        return (xi*self.height)+yi

    def __dealloc__(self):
        free(self._raw_data)
        free(self._raw_canvas)

    cpdef tuple shape(self):
        return (self.width,self.height)

        
    cdef unsigned int get_width(self):
        return <unsigned int> self.width


    cdef unsigned int get_height(self):
        return <unsigned int> self.height



    cpdef void hard_clear(self,float init_depth):
        cdef int idx
        for idx in range(self.size):
            
            # clear canvas
            #((self.canvas[idx]).aleph) = [0,0,0, 0,0,0, 0,0]
            memset(self.aleph(idx), 0, 8*sizeof(unsigned char))
            # clear depth buffer 
            init_s_drawbuffer_cell(& (self.drawbuffer[idx]),init_depth)

    cpdef void set_depth_content(self,const int xi,const int yi,
                                float depth_value, 
                                float w1,
                                float w2,
                                float w3 ,
                                int   node_id,
                                int   geom_id,
                                int   material_id ,
                                int   primitiv_id ,
    ):

        cdef s_drawbuffer_cell* thecell = &self.drawbuffer[self.linear_idx(xi,yi)]
        
        thecell.depth_value = depth_value
        thecell.w1 = w1
        thecell.w2 = w2
        thecell.w3 = w3 
        thecell.primitiv_id = primitiv_id
        thecell.geom_id = geom_id
        thecell.node_id = node_id
        thecell.material_id = material_id

    cpdef void apply_material(self,int xi,int yi):
        cdef int lin_idx = self.linear_idx(xi,yi)



        cdef s_drawbuffer_cell* thecell = &self.drawbuffer[lin_idx]

        cdef unsigned char *aleph = self.aleph(lin_idx)
        
        

        # thecell.material_id 
        # material. 
        # blit


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
        unsigned char g2,):
        
        self.canvas[self.linear_idx(xi,yi)].aleph = [fr,fg,fb, br,bg,bb, g1,g2]



    cpdef list canvas_to_list(self):
        cdef list ret = []

        cdef list row = []
        cdef int idx

        cdef unsigned char b 
        cdef unsigned char gidx 

        for idx in range (self.size):
            row = []
            for gidx in range(8):
                row.append( ((self.canvas[idx]).aleph)[gidx]      )
            ret.append(row)
        return ret

    
    cpdef list drawbuffer_to_list(self):

        cdef list ret = []
        cdef int idx = 0
        cdef s_drawbuffer_cell acell
        cdef list row = []

        

        for idx in range (self.size):
            acell = self.drawbuffer[idx]
            row = [
                acell.depth_value,
                acell.w1,
                acell.w2,
                acell.w3 ,
                acell.node_id,
                acell.geom_id,
                acell.material_id,
                acell.primitiv_id ,
                ]
            ret.append(row)
        return ret




cdef void init_s_drawbuffer_cell(s_drawbuffer_cell* x, const float depth):
    memset(x, 0, sizeof(s_drawbuffer_cell))
    x[0].depth_value = depth






    