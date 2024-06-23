
from tt3de.glm.c_buffer cimport s_buffer
from tt3de.glm.primitives.primitives cimport PrimitivesBuffer,s_drawing_primitive,_add_point,_add_line,_add_triangle_no_object

from tt3de.glm.geometry.geometry cimport GeometryBuffer,s_geometry

DEF POINT = 0    # floats for each pixel [depth, wa,wb,wc]
DEF LINE = 1     # integer for each pixel [material_id,triangle_id]
DEF TRIANGLE = 2 # integer for each pixel [material_id,triangle_id]
DEF POLYGON = 3  # 


cpdef void build_primitives(GeometryBuffer geometry_buffer, PrimitivesBuffer primitive_buffer):


    cdef s_geometry* geom = geometry_buffer.rawaccess()
    cdef unsigned int geometry_count = geometry_buffer.geometry_count()
    cdef s_buffer* primitiv_buffer_array = primitive_buffer.rawaccess_array()

    c_build_primitives(geom, geometry_count,  primitiv_buffer_array)
                                




cdef void c_build_primitives(s_geometry* geom_buffer, unsigned int geometry_count, s_buffer* primitiv_buffer_array)  :
    # build the primitive_buffer array from the geometry buffer. 
    # line , point, triangles are mapped 1:1 
    # geom could be generative and build other stuff.
    cdef int current_geom_idx = 0
    cdef s_geometry* geom
    cdef int current_triangle_idx = 0
    cdef int current_node_id = 0
    cdef int current_material_id = 0
    cdef int current_polygon_count = 0


    if geometry_count > primitiv_buffer_array.capacity :  
        return

    primitiv_buffer_array.size=0
    while current_geom_idx < geometry_count:
        geom = (<s_geometry* > ((<char*> geom_buffer) + sizeof(s_geometry) * current_geom_idx ))
        if (geom).geom_type == POINT:
            _add_point(primitiv_buffer_array,
                geom.node_id,
                current_geom_idx,  # Assuming geometry_id is the index in the geometry buffer
                geom.material_id,
                geom.ax,
                geom.ay,
                geom.az
            )
            primitiv_buffer_array.size+=1
            current_geom_idx += 1
        elif (geom).geom_type == LINE:
            _add_line(primitiv_buffer_array,
                geom.node_id,
                current_geom_idx,  # Assuming geometry_id is the index in the geometry buffer
                geom.material_id,
                geom.ax,
                geom.ay,
                geom.az,
                geom.bx,
                geom.by,
                geom.bz
            )
            primitiv_buffer_array.size+=1
            current_geom_idx += 1
        elif (geom).geom_type == TRIANGLE:
            _add_triangle_no_object(primitiv_buffer_array,
                geom.node_id,
                current_geom_idx,  # Assuming geometry_id is the index in the geometry buffer
                geom.material_id,
                geom.ax,
                geom.ay,
                geom.az,
                geom.bx,
                geom.by,
                geom.bz,
                geom.cx,
                geom.cy,
                geom.cz,
                geom.uv_array
            )
            primitiv_buffer_array.size+=1
            current_geom_idx += 1

        elif geom.geom_type == POLYGON:
            # keep this one as reference
            current_node_id = geom.node_id
            current_material_id = geom.material_id
            current_polygon_count = geom.polygon_count
            for current_triangle_idx in range(current_polygon_count):
                geom = (<s_geometry* > ((<char*> geom_buffer) + sizeof(s_geometry) * (current_geom_idx+current_triangle_idx) ))

                _add_triangle_no_object(primitiv_buffer_array,
                    current_node_id,
                    current_geom_idx,  
                    current_material_id,
                    geom.ax,
                    geom.ay,
                    geom.az,
                    geom.bx,
                    geom.by,
                    geom.bz,
                    geom.cx,
                    geom.cy,
                    geom.cz,
                    geom.uv_array
                )
                primitiv_buffer_array.size+=1
            current_geom_idx += current_polygon_count
        