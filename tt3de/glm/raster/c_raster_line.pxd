
from tt3de.glm.drawing.c_drawing_buffer cimport DrawingBuffer
from tt3de.glm.primitives.primitives cimport s_drawing_primitive


cdef int compute_code(float x, float y, int screen_width, int screen_height)


cdef int clip_in_screen(float axf, float ayf, float bxf, float byf, int screen_width, int screen_height,
                        float* ax_clipped, float* ay_clipped, float* bx_clipped, float* by_clipped)


#the raster function , during the full raster 
cdef void raster_line(s_drawing_primitive* dprim,DrawingBuffer drawing_buffer)