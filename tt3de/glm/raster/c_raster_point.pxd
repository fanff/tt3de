
from tt3de.glm.primitives.primitives cimport s_drawing_primitive

from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell


cdef void raster_point (
    s_drawing_primitive* dprim,
    s_drawbuffer_cell* drawing_buffer,
    int raw_array_width) noexcept nogil


