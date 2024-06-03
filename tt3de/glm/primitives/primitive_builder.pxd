


from tt3de.glm.c_buffer cimport s_buffer
from tt3de.glm.geometry.geometry cimport s_geometry



cdef void c_build_primitives(s_geometry* geom, unsigned int geometry_count, s_buffer* primitiv_buffer_array)