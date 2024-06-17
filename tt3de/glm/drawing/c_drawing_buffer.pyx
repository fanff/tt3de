from libc.string cimport memset
from libc.stdlib cimport malloc, free
import cython


from rich.style import Style
from rich.color import Color
from rich.color_triplet import ColorTriplet



from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell,s_canvas_cell

@cython.boundscheck(False)
@cython.wraparound(False)
cdef class DrawingBuffer:
    

    def __cinit__(self, int width,int height):
        cdef int _size = width*height
        
        self.style_array = [Style() for i in range(width*height)]
        print(type(self.style_array))
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

        #init some bit reduction for caching the output
        self.bit_reductions = [1,1,1,1,1,1]

    cpdef set_bit_reduction(self, list params):
        if len(params)!= 6:
            raise ValueError("bit reduction size must be 6")
        for i in range(6):
            self.bit_reductions[i] = <unsigned char> params[i]
    cpdef int hash_value(self, list value):
        cdef unsigned char [8] v
        for i in range(8):
            v[i] = value[i]
        return hash_function(v,self.bit_reductions)
    cdef unsigned char* aleph(self,int index):
        return &(self.canvas[index].aleph[0])

    cdef s_drawbuffer_cell* get_raw_depth_buffer(self):
        return self._raw_data

    cdef s_canvas_cell* get_raw_canvas_buffer(self):
        return self._raw_canvas



    cdef inline int linear_idx(self,const int xi,const int yi):
        return (yi*self.width)+xi

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
        set_depth_content(self._raw_data,self.width,xi,yi,
        
            depth_value, 
            w1,
            w2,
            w3 ,
            node_id,
            geom_id,
            material_id ,
            primitiv_id ,
        )
    def get_depth_buff_content(self,xi:int,yi:int):
        #lol =  self.canvas[self.linear_idx(xi,yi)]
        athing = self._raw_data[self.linear_idx(xi,yi)]
        return athing


    def get_depth_min_max(self)->tuple[int,int]:

        max_depth:float = -10**8
        min_depth:float = 10**8
        depth_val:float = 0
        for i in range(self.size):
            athing = self._raw_data[i]

            depth_val = athing.depth_value
            if depth_val> max_depth:
                max_depth = depth_val
            if depth_val< min_depth:
                min_depth = depth_val
        return min_depth,max_depth
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
        
        set_canvas_content(self._raw_canvas,    self.width,xi,yi,             fr,fg,fb, br,bg,bb, g1,g2)


    def get_canvas_content(self,xi:int ,yi:int ):
        apix =  self.canvas[self.linear_idx(xi,yi)]
        rlist = [
            <int> apix.aleph[0],
            <int> apix.aleph[1],
            <int> apix.aleph[2],
            <int> apix.aleph[3],
            <int> apix.aleph[4],
            <int> apix.aleph[5],
            <int> apix.aleph[6],
            <int> apix.aleph[7],
        ]
        return rlist

    cpdef list canvas_to_list_ofstyled(self):
        cdef list ret = []

        cdef list row = []
        cdef int idx
        cdef char[8] aaa
        cdef unsigned char b 
        cdef unsigned char gidx 

        for idx in range (self.size):
            
            aaa = (self.canvas[idx]).aleph
            c1 = Color.from_triplet(ColorTriplet(<int>aaa[0],<int>aaa[1],<int>aaa[2]))
            c2 = Color.from_triplet(ColorTriplet(<int>aaa[3],<int>aaa[4],<int>aaa[5]))

            asetyle = self.style_array[idx]
            asetyle._color =c1
            asetyle._bgcolor=c2


            ret.append((asetyle,int(aaa[6]),int(aaa[7])))
        return ret

    cpdef list canvas_to_list(self):

        #cdef unsigned char [6] bit_reductions= [4,5,6,4,5,6]
        cdef list ret = []

        cdef list row = []
        cdef int idx

        cdef unsigned char b 
        cdef unsigned char gidx 

        for idx in range (self.size):
            row = []
            #hash_function(((self.canvas[idx]).aleph) ,bit_reductions)

            for gidx in range(8):
                row.append( ((self.canvas[idx]).aleph)[gidx]      )
            ret.append(row)
        return ret

    
    cpdef list drawbuffer_to_list(self):
        # will return the list of the drawbuffer elements. 
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
    ) noexcept nogil:
    # Set depth content with a testing. assume it is used for simple rendering.

    cdef s_drawbuffer_cell* thecell = &(the_raw_array[(yi*raw_array_width)+xi]) #&self.drawbuffer[self.linear_idx(xi,yi)]
    if depth_value < thecell.depth_value:
        thecell.depth_value = depth_value
        thecell.w1 = w1
        thecell.w2 = w2
        thecell.w3 = w3 

        thecell.w1_alt = 1
        thecell.w2_alt = 1
        thecell.w3_alt = 1

        thecell.primitiv_id = primitiv_id
        thecell.geom_id = geom_id
        thecell.node_id = node_id
        thecell.material_id = material_id



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
    ) noexcept nogil:
    # Set depth content with a testing. assume it is used for double rendering.

    cdef s_drawbuffer_cell* thecell = &(the_raw_array[(yi*raw_array_width)+xi]) #&self.drawbuffer[self.linear_idx(xi,yi)]
    if depth_value < thecell.depth_value:
        thecell.depth_value = depth_value
        thecell.w1 = w1
        thecell.w2 = w2
        thecell.w3 = w3 

        thecell.w1_alt = w1_alt
        thecell.w2_alt = w2_alt
        thecell.w3_alt = w3_alt

        thecell.primitiv_id = primitiv_id
        thecell.geom_id = geom_id
        thecell.node_id = node_id
        thecell.material_id = material_id



cdef void set_canvas_content(s_canvas_cell* the_raw_array,
        const int raw_array_width,
        const int xi,const int yi,
        const unsigned char fr,
        const unsigned char fg,
        const unsigned char fb,
        const unsigned char br,
        const unsigned char bg,
        const unsigned char bb,
        const unsigned char g1, 
        const unsigned char g2, 
    ) noexcept nogil:
    
    cdef s_canvas_cell* thecell = &(the_raw_array[(yi*raw_array_width)+xi]) #&self.drawbuffer[self.linear_idx(xi,yi)]
        
    thecell.aleph[0] = fr
    thecell.aleph[1] = fg
    thecell.aleph[2] = fb
    
    thecell.aleph[3] = br
    thecell.aleph[4] = bg
    thecell.aleph[5] = bb

    thecell.aleph[6] = g1
    thecell.aleph[7] = g2




cdef unsigned int hash_function(unsigned char nums[8], unsigned char bit_reductions[6]):
    """
    :param nums: An array of 8 unsigned char values to be hashed.
    :param bit_reductions: An array of 6 unsigned char values specifying the number of bits to retain for the first 6 elements of nums.
    
    The hashing method is as follows:
    - For the first 6 elements of nums (indices 0 to 5), only the highest bits as specified by bit_reductions are used.
    - The 7th element of nums (index 6) is ignored.
    - The 8th element of nums (index 7) is used without any bit reduction.

    The resulting hash value is a unique positive integer derived from the provided nums and bit_reductions.
    """
    cdef unsigned int hash_value = 0
    cdef int i

    # Iterate over the first 6 elements of nums
    for i in range(6):
        # Use only the highest bits as specified by bit_reductions
        hash_value = (hash_value << bit_reductions[i]) | (nums[i] >> (8 - bit_reductions[i]))
    
    # Use the 8th element of nums (nums[7]) directly
    hash_value = (hash_value << 8) | nums[7]

    return hash_value