
from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell
from tt3de.glm.primitives.primitives cimport s_drawing_primitive



cdef void raster_triangle(s_drawing_primitive* dprim,
    s_drawbuffer_cell* the_raw_array,
    int screenWidth,int screenHeight) noexcept nogil




cdef void raster_triangle_double_weights(s_drawing_primitive* dprim,
    s_drawbuffer_cell* the_raw_array,
    int screenWidth,int screenHeight) noexcept nogil
  