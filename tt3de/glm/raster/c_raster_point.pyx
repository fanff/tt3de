

from tt3de.glm.primitives.primitives cimport s_drawing_primitive
from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell

from tt3de.glm.drawing.c_drawing_buffer cimport set_depth_content


from tt3de.glm.primitives.primitives cimport s_drawing_primitive


cdef void raster_point (
    s_drawing_primitive* dprim,
    s_drawbuffer_cell* drawing_buffer,
    int raw_array_width) noexcept nogil:
    
    cdef float depth = dprim.mat[2][0]


    cdef int xi = dprim.ax
    cdef int yi = dprim.ay
    
    set_depth_content(drawing_buffer, raw_array_width, xi,yi, 
            depth, 1.0,0.0,0.0,  
            0.5,0.5,0.0,
            dprim.node_id,  # pass node_id
            dprim.geometry_id, # pass geom 
            dprim.material_id,
            dprim.unique_id, # my primitive id 
             )
    
    #drawing_buffer.material_id
    #drawing_buffer.set_canvas_content(xi,yi, 0,0,0,0,0,0,0,0)


