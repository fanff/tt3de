

ctypedef packed struct s_geometry:
    unsigned char geom_type # 0 is point, 1 is line , 2 is triangle , 3 is polygon
    int polygon_count
    # 3 points in 3d ..
    float ax
    float ay 
    float az 

    float bx 
    float by 
    float bz 

    float cx 
    float cy 
    float cz 
    
    # N layers of uv
    float [48] uv_array  # 3*2*8  

    int node_id
    int material_id


cdef class GeometryBuffer:

    cdef s_geometry* _raw_content
    cdef int max_size
    cdef unsigned int content_idx

    cdef  int elements
    
    # methods
    cdef s_geometry* rawaccess(self)
    cpdef unsigned int geometry_count(self)
    cpdef int element_count(self)
    cpdef void clear(self)

    cdef void set_polygon_count(self, int at, int count) noexcept nogil

    cdef void add_point(self, float x, float y, float z, float uv_array[8], int node_id, int material_id)
    cdef void add_triangle(self, float ax, float ay, float az, float bx, float by, float bz, float cx, float cy, float cz, float uv_array[48], int node_id, int material_id)
    cdef void add_line(self, float ax, float ay, float az, float bx, float by, float bz, float uv_array[16], int node_id, int material_id)
    cpdef bint can_add(self)
    cpdef s_geometry get_geometry(self,int ixd)
    cpdef add_point_to_buffer(self, float x, float y, float z, list uv_list, int node_id, int material_id)
        

    cpdef add_line_to_buffer(self, list start, list end, list uv_list, int node_id, int material_id)
        

    cpdef add_triangle_to_buffer(self, list point_a, list point_b, list point_c, list uv_list, int node_id, int material_id)
    
    cpdef add_polygon_to_buffer(self,list vertex,list face_uvs, int node_id, int material_id)

    