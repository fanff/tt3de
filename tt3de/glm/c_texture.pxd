# texture2d.pxd
cdef class Texture2D:
    cdef unsigned char* data
    cdef int width
    cdef int height

    cdef void _set_pixel(self, int x, int y, unsigned char r, unsigned char g, unsigned char b)
    cdef void _get_pixel(self, int x, int y, unsigned char* r, unsigned char* g, unsigned char* b)
    cpdef tuple get_pixel_uv(self, double u, double v)
    cpdef void set_pixel_uv(self, double u, double v, unsigned char r, unsigned char g, unsigned char b)