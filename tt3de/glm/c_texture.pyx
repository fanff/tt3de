from libc.stdlib cimport malloc, free
from libc.string cimport memset
from libc.math cimport modff,fabsf
from tt3de.glm.c_texture cimport s_texture256,s_texture_array

cdef class TextureArray:
    # cdef s_texture32[32] t32_array
    # cdef int t32_size 
    def __cinit__(self):
        self.raw_array.inner_size = 0

        for i in range(64):
            self.raw_array.inner_map[i] = 0
            self.raw_array.pointer_map[i] = &self.raw_array.data
        self.raw_array.current_pointer =  &self.raw_array.data


    cpdef int size(self):
        return self.raw_array.inner_size
    cdef s_texture_array* get_raw(self):
        return (&self.raw_array)

    def get_inner_map(self):
        return [int(self.raw_array.inner_map[i]) for i in range(64)]
    def get_wh_of(self,i:int ):
        cdef s_texture256* atext = <s_texture256*> (self.raw_array.pointer_map[i])
        return [atext.width,atext.height]
    def get_pixel_of(self,i:int, u:float,v:float, repeat:bool = True, transp:bool = True):
        cdef s_texture256* atext = <s_texture256*> (self.raw_array.pointer_map[i])

        cdef unsigned char r = 0
        cdef unsigned char g = 0
        cdef unsigned char b = 0
        cdef int use_repeat = 1 if repeat else 0
        cdef int use_transp = 1 if transp else 0
        cdef int result = 0
        map_uv_generic(atext,use_repeat,use_transp, u,v,&r,&g,&b , &result)

        return [<int> r,
        <int> g,
        <int> b]

    def load_texture256_from_list(self, list data, int tr_r=0,int tr_g=0, int tr_b=0):

        cdef int in_width = len(data[0])
        cdef int in_height = len(data)
        cdef s_texture256 *atexture256 = <s_texture256*> self.raw_array.current_pointer 
        atexture256.width = in_width
        atexture256.height = in_height

        atexture256.tr_r=<unsigned char> tr_r
        atexture256.tr_g=<unsigned char> tr_g
        atexture256.tr_b=<unsigned char> tr_b


        for i in range(in_height):
            for j in range(in_width):
                atexture256.data[i][j][0] = data[i][j][0]
                atexture256.data[i][j][1] = data[i][j][1]
                atexture256.data[i][j][2] = data[i][j][2]

        self.raw_array.pointer_map[self.raw_array.inner_size] = atexture256
        self.raw_array.inner_map[self.raw_array.inner_size] = 1 # ONE for 256 texture
        self.raw_array.inner_size+=1
        #self.current_pointer+=sizeof(s_texture256)
        self.raw_array.current_pointer = <void*>((<char*>self.raw_array.current_pointer) + sizeof(s_texture256))



cdef class Texture2D:
    def __cinit__(self, int width, int height):
        self.width = width
        self.height = height
        self.data = <unsigned char*>malloc(width * height * 3 * sizeof(unsigned char))
        if not self.data:
            raise MemoryError("Unable to allocate memory for texture data")
        memset(self.data, 0, width * height * 3)

    def __dealloc__(self):
        if self.data:
            free(self.data)
    cdef int get_width(self):
        return self.width
    cdef int get_height(self):
        return  self.height
    cdef void _set_pixel(self, int x, int y, unsigned char r, unsigned char g, unsigned char b):
        cdef int index = (y * self.width + x) * 3
        self.data[index] = r
        self.data[index + 1] = g
        self.data[index + 2] = b

    cpdef void _get_at(self, int index, unsigned char* r, unsigned char* g, unsigned char* b):
        r[0] = self.data[index]
        g[0] = self.data[index + 1]
        b[0] = self.data[index + 2]

    cdef void _get_pixel(self, int x, int y, unsigned char* r, unsigned char* g, unsigned char* b):
        cdef int index = (y * self.width + x) * 3
        r[0] = self.data[index]
        g[0] = self.data[index + 1]
        b[0] = self.data[index + 2]

    cpdef void set_pixel_uv(self, double u, double v, unsigned char r, unsigned char g, unsigned char b):
        cdef int x = int(u * self.width)
        cdef int y = int(v * self.height)
        if 0 <= x < self.width and 0 <= y < self.height:
            self._set_pixel(x, y, r, g, b)

    cpdef tuple get_pixel_uv(self, double u, double v):
        cdef int x = int(u * self.width)
        cdef int y = int(v * self.height)
        cdef unsigned char r, g, b
        if 0 <= x < self.width and 0 <= y < self.height:
            self._get_pixel(x, y, &r, &g, &b)
            return (r, g, b)
        else:
            return (0, 0, 0)

    def load_from_list(self, list data):
        cdef int i, j, index
        cdef unsigned char* ptr = self.data
        for i in range(self.height):
            for j in range(self.width):
                index = (i * self.width + j) * 3
                ptr[index] = data[i][j][0]
                ptr[index + 1] = data[i][j][1]
                ptr[index + 2] = data[i][j][2]

    

####################


cdef void calc_uv( const int repeat, const int width, const int height, const float u, const float v, int* wi,int* hi) noexcept nogil:
    cdef float one = 1.0
    if repeat==1:
        wi[0] = <int> ( (<float>(width )) * modff(fabsf(u),&one))  
        hi[0] = <int> ( (<float>(height)) * modff(fabsf(v),&one))   
    else:
        wi[0] = <int> ( (<float> width ) * max(0.0, min(0.9999, u))   )
        hi[0] = <int> ( (<float> height) * max(0.0, min(0.9999, v))   )


cdef void map_uv_generic(s_texture256* texture,
                        const int repeat, const int transparency,
                        const float u, const float v,
                        unsigned char* r,unsigned char* g,unsigned char* b,
                        int* apply_finished) noexcept nogil:
    
    
    cdef int wi 
    cdef int hi 

    cdef unsigned char on_text_r 
    cdef unsigned char on_text_g 
    cdef unsigned char on_text_b 


    calc_uv(repeat,texture.width,texture.height,u,v,&wi,&hi)
    
    
    on_text_r = texture.data[hi][wi][0]
    on_text_g = texture.data[hi][wi][1]
    on_text_b = texture.data[hi][wi][2]


    if transparency!=0 and (on_text_r == texture.tr_r and on_text_g == texture.tr_g and on_text_b == texture.tr_b):
        pass
    else:
        r[0] = on_text_r 
        g[0] = on_text_g 
        b[0] = on_text_b 
        apply_finished[0] = 1

cpdef bench_n_uvcacl(Texture2D atexture,int count ):
    cdef unsigned char r,g,b;
    cdef double lol = 3
    cdef int xi,yi
    for i in range(count):      
        xi = (int) (lol * count +1)
        yi = (int) (lol * count +1)
        atexture._get_pixel(0,0,&r,&g,&b)
