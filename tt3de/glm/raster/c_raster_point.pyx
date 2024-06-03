

from tt3de.glm.drawing.c_drawing_buffer cimport DrawingBuffer
from tt3de.glm.primitives.primitives cimport s_drawing_primitive


cpdef raster_on_stuff(s_drawing_primitive aprimitive,DrawingBuffer drawing_buffer):

    raster_point(&aprimitive,drawing_buffer)





cdef void raster_point (
    s_drawing_primitive* dprim,
    DrawingBuffer drawing_buffer) noexcept :
    
    cdef float depth = dprim.mat[2][0]


    cdef int xi = dprim.ax
    cdef int yi = dprim.ay
    

    # dprim.node_id
    # dprim.geometry_id
    # dprim.material_id
    # dprim.unique_id
    
    drawing_buffer.set_depth_content(xi,yi, 
            depth, 1.0,0.0,0.0,  
            dprim.node_id,  # pass node_id
            dprim.geometry_id, # pass geom 
            dprim.material_id,
            dprim.unique_id, # my primitive id 
             )
    
    #drawing_buffer.material_id
    #drawing_buffer.set_canvas_content(xi,yi, 0,0,0,0,0,0,0,0)


