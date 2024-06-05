
from tt3de.glm.c_buffer cimport s_buffer
from tt3de.glm.primitives.primitives cimport PrimitivesBuffer,s_drawing_primitive,_add_point,_add_line,_add_triangle_no_object

from tt3de.glm.geometry.geometry cimport GeometryBuffer,s_geometry

DEF POINT = 0    # floats for each pixel [depth, wa,wb,wc]
DEF LINE = 1     # integer for each pixel [material_id,triangle_id]
DEF TRIANGLE = 2 # integer for each pixel [material_id,triangle_id]





cpdef void build_primitives(GeometryBuffer geometry_buffer, PrimitivesBuffer primitive_buffer):
    cdef unsigned int i
    cdef s_geometry* geom = geometry_buffer.rawaccess()
    cdef unsigned int geometry_count = geometry_buffer.geometry_count()
    cdef s_drawing_primitive primitive
    cdef s_buffer* primitiv_buffer_array = primitive_buffer.rawaccess_array()
    c_build_primitives(geom, geometry_count,  primitiv_buffer_array)
                                




cdef void c_build_primitives(s_geometry* geom_buffer, unsigned int geometry_count, s_buffer* primitiv_buffer_array)  :
    # build the primitive_buffer array from the geometry buffer. 
    # line , point, triangles are mapped 1:1 
    # geom could be generative and build other stuff.
    cdef int i
    cdef s_geometry* geom

    if geometry_count > primitiv_buffer_array.capacity :  
        return

    primitiv_buffer_array.size=0
    for i in range(geometry_count):
        geom = (<s_geometry* > ((<char*> geom_buffer) + sizeof(s_geometry) * i ))
        if (geom).geom_type == POINT:
            _add_point(primitiv_buffer_array,
                geom.node_id,
                i,  # Assuming geometry_id is the index in the geometry buffer
                geom.material_id,
                geom.ax,
                geom.ay,
                geom.az
            )
            primitiv_buffer_array.size+=1
        elif (geom).geom_type == LINE:
            _add_line(primitiv_buffer_array,
                geom.node_id,
                i,  # Assuming geometry_id is the index in the geometry buffer
                geom.material_id,
                geom.ax,
                geom.ay,
                geom.az,
                geom.bx,
                geom.by,
                geom.bz
            )
            primitiv_buffer_array.size+=1
        elif (geom).geom_type == TRIANGLE:
            _add_triangle_no_object(primitiv_buffer_array,
                geom.node_id,
                i,  # Assuming geometry_id is the index in the geometry buffer
                geom.material_id,
                geom.ax,
                geom.ay,
                geom.az,
                geom.bx,
                geom.by,
                geom.bz,
                geom.cx,
                geom.cy,
                geom.cz
            )
            primitiv_buffer_array.size+=1