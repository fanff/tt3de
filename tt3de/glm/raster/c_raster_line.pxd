
from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell
from tt3de.glm.primitives.primitives cimport s_drawing_primitive

# preraster code 
cdef int compute_code(float x, float y, int screen_width, int screen_height) noexcept nogil


cdef int clip_in_screen(float axf, float ayf, float bxf, float byf, int screen_width, int screen_height,
                        float* ax_clipped, float* ay_clipped, float* bx_clipped, float* by_clipped)noexcept nogil



# raster code 
#the raster function , during the full raster 
cdef void raster_line(s_drawing_primitive* dprim,
     s_drawbuffer_cell* the_raw_array,
     int raw_array_width) noexcept nogil