from libc.string cimport memset
from libc.stdlib cimport malloc, free
import cython

from textual.strip import Strip

from rich.style import Style
from rich.color import Color
from rich.text import Segment

from rich.color_triplet import ColorTriplet



from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell,s_canvas_cell


DEF DEPTH_BUFFER_COUNT = 2


@cython.boundscheck(False)
@cython.wraparound(False)
cdef class DrawingBuffer:
    

    def __cinit__(self, int width,int height):
        cdef int _size = width*height
        
        self._raw_data = <s_drawbuffer_cell*>malloc( DEPTH_BUFFER_COUNT * _size * sizeof(s_drawbuffer_cell))
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



    cpdef long hash_value(self, list value):
        cdef unsigned char [8] v
        for i in range(8):
            v[i] = value[i]
        return <long> hash_function(v,self.bit_reductions)
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
        cdef int layer_idx
        for idx in range(self.size):
            # clear canvas
            #((self.canvas[idx]).aleph) = [0,0,0, 0,0,0, 0,0]
            memset(self.aleph(idx), 0, 8*sizeof(unsigned char))
            for layer_idx in range(DEPTH_BUFFER_COUNT):
                # clear depth buffer 
                init_s_drawbuffer_cell(& (self.drawbuffer[(DEPTH_BUFFER_COUNT*idx)+layer_idx]),init_depth)

    cpdef void set_depth_content(self,const int xi,const int yi,
                                float depth_value, 
                                float w1,
                                float w2,
                                float w3 ,

                                float w1_alt,
                                float w2_alt,
                                float w3_alt ,

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
            w1_alt,
            w2_alt,
            w3_alt,
            node_id,
            geom_id,
            material_id ,
            primitiv_id ,
        )
    def get_depth_buff_content(self,xi:int,yi:int, layer:int = 0):
        #lol =  self.canvas[self.linear_idx(xi,yi)]
        athing = self._raw_data[(self.linear_idx(xi,yi)*DEPTH_BUFFER_COUNT)+layer]
        return athing

    def get_depth_buff_contents(self,xi:int,yi:int):
        res = []
        for layer in range(DEPTH_BUFFER_COUNT):

            res.append( self._raw_data[(self.linear_idx(xi,yi)*DEPTH_BUFFER_COUNT)+layer])
        return res
    def get_depth_min_max(self,layer:int =0)->tuple[int,int]:
        cdef int buffer_index = 0;
    
        cdef s_drawbuffer_cell athing 
        max_depth:float = -10**8
        min_depth:float = 10**8
        depth_val:float = 0
        for i in range(self.size):
            buffer_index = (i *  DEPTH_BUFFER_COUNT) + layer
            athing = self._raw_data[buffer_index ]

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


    cpdef list canvas_to_list_hashed(self,int minx,int miny,int width,int height,dict cache_,list allchars):
        cdef list ret = []

        cdef list current_line = []
        cdef int idx

        cdef unsigned long long hashvalue 

        cdef unsigned char current_elem[8]

        cdef int curr_x = minx
        cdef int curr_y = miny
        cdef int max_x = minx + width
        cdef int max_y = miny + height

        for curr_y in range(miny,max_y):
            current_line = []
            for curr_x in range (minx,max_x):
                idx = curr_y*self.width + curr_x

                current_elem = (self._raw_canvas[idx].aleph)

                hashvalue = hash_function((current_elem) , self.bit_reductions)
                        
                        
                asegment = cache_.get(hashvalue, None)
                if asegment is None:
                    asegment = Segment(
                        allchars[<int> ( current_elem[7] )],
                        Style(
                            color=Color.from_triplet(ColorTriplet(
                                                    <int> ( current_elem[0] ),
                                                    <int> ( current_elem[1] ),
                                                    <int> ( current_elem[2] ))),
                            bgcolor=Color.from_triplet(ColorTriplet(
                                                    <int> ( current_elem[3] ),
                                                    <int> ( current_elem[4] ),
                                                    <int> ( current_elem[5] ),
                            )),
                        ),
                    )

                    cache_[hashvalue] = asegment
                current_line.append(asegment)
            
            ret.append(Strip(current_line))
        return ret



    
    
    cpdef list drawbuffer_to_list(self,int layer=0):
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
    x[0].geom_id = -1

cdef void set_depth_content(s_drawbuffer_cell* the_raw_array,
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
    cdef int the_point = ((yi*raw_array_width)+xi) * DEPTH_BUFFER_COUNT
    cdef int the_layer = 0
    cdef int is_done = 0
    cdef s_drawbuffer_cell* thecell 
    cdef s_drawbuffer_cell* thenextcell 
    
    
    while the_layer < DEPTH_BUFFER_COUNT and is_done==0:
    
        thecell= &(the_raw_array[the_point+the_layer]) #&self.drawbuffer[self.linear_idx(xi,yi)]

        if thecell.geom_id == geom_id:
            is_done= 1
        elif depth_value < thecell.depth_value:
            # moving current cell to next layer
            if the_layer+1<DEPTH_BUFFER_COUNT:
                thenextcell= &(the_raw_array[the_point+the_layer+1]) 
                thenextcell[0] = thecell[0]

            # set myself
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
            is_done = 1
        else:
            the_layer += 1


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




cdef unsigned long long hash_function(unsigned char nums[8], unsigned char bit_reductions[6]):
    """
    :param nums: An array of 8 unsigned char values to be hashed.
    :param bit_reductions: An array of 6 unsigned char values specifying the number of bits to retain for the first 6 elements of nums.
    
    The hashing method is as follows:
    - For the first 6 elements of nums (indices 0 to 5), only the highest bits as specified by bit_reductions are used.
    - The 7th element of nums (index 6) is ignored.
    - The 8th element of nums (index 7) is used without any bit reduction.

    The resulting hash value is a unique positive integer derived from the provided nums and bit_reductions.
    """
    cdef unsigned long long hash_value = 0
    cdef int i

    # Iterate over the first 6 elements of nums
    for i in range(6):
        # Use only the highest bits as specified by bit_reductions
        hash_value = (hash_value << bit_reductions[i]) | (nums[i] >> (8 - bit_reductions[i]))
    
    # Use the 8th element of nums (nums[7]) directly
    hash_value = (hash_value << 8) | nums[7]

    return hash_value