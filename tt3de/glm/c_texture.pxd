# texture2d.pxd

ctypedef packed struct s_texture256:
    int height;
    int width;
    char tr_r;
    char tr_g;
    char tr_b;
    unsigned char data[256][256][3];

ctypedef packed struct s_texture_array:
    char[12582912] data
    int inner_size
    unsigned char[64] inner_map
    void* pointer_map[64]
    void* current_pointer


    
cdef class TextureArray:
    cdef s_texture_array raw_array

    cpdef int size(self)
    cdef s_texture_array* get_raw(self)



    
cdef class Texture2D:
    cdef unsigned char* data
    cdef int width
    cdef int height

    cdef int get_width(self)
    cdef int get_height(self)
    
    cdef void _set_pixel(self, int x, int y, unsigned char r, unsigned char g, unsigned char b)
    cdef void _get_pixel(self, int x, int y, unsigned char* r, unsigned char* g, unsigned char* b)
    cpdef void _get_at(self, int index, unsigned char* r, unsigned char* g, unsigned char* b)
    cpdef tuple get_pixel_uv(self, double u, double v)
    cpdef void set_pixel_uv(self, double u, double v, unsigned char r, unsigned char g, unsigned char b)

cdef void map_uv_clamp(s_texture256* texture, const float u, const float v,unsigned char* r,unsigned char* g,unsigned char* b) noexcept nogil

cdef void map_uv_repeat(s_texture256* texture, const float u, const float v,unsigned char* r,unsigned char* g,unsigned char* b) noexcept nogil


