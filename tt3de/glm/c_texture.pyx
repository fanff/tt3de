from libc.stdlib cimport malloc, free
from libc.string cimport memset

from tt3de.glm.c_texture cimport s_texture32

cdef class TextureArray:
    # cdef s_texture32[32] t32_array
    # cdef int t32_size 
    def __cinit__(self):
        self.t32_size = 0
    cpdef int size(self):
        return self.t32_size
    cdef s_texture32* get_raw(self):
        return (self.t32_array)
    def load_texture32_from_list(self, list data):

        cdef s_texture32 atexture = (self.t32_array[self.t32_size])

        
        cdef int i, j, index
        #cdef unsigned char* ptr = atexture.data
        for i in range(32):
            for j in range(32):
                index = (i * 32 + j) * 3
                atexture.data[i][j][0]= data[i][j][0]
                atexture.data[i][j][1]= data[i][j][1]
                atexture.data[i][j][2]= data[i][j][2]
        self.t32_array[self.t32_size] = atexture

        self.t32_size+=1



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


cpdef bench_n_uvcacl(Texture2D atexture,int count ):
    cdef unsigned char r,g,b;
    cdef double lol = 3
    cdef int xi,yi
    for i in range(count):      
        xi = (int) (lol * count +1)
        yi = (int) (lol * count +1)
        atexture._get_pixel(0,0,&r,&g,&b)
