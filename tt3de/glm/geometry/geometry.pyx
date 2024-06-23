
from libc.string cimport memset
from libc.stdlib cimport malloc, free
import cython



@cython.boundscheck(False)
@cython.wraparound(False)
cdef class GeometryBuffer:
    def __cinit__(self, int size):

        self.max_size = size
        self._raw_content = <s_geometry*> malloc(self.max_size * sizeof(s_geometry))
        if not self._raw_content:
            raise MemoryError("Failed to allocate primitives buffer.")
        self.content_idx = 0
        self.elements = 0
    def __dealloc__(self):
        free(self._raw_content)


    
    # methods
    cdef s_geometry* rawaccess(self):
        return self._raw_content


    cpdef bint can_add(self):
        return self.content_idx < self.max_size

    cpdef s_geometry get_geometry(self,int ixd):
        cdef s_geometry lol = (self._raw_content[ixd])
        return lol


    cpdef unsigned int geometry_count(self):
        return self.content_idx

    cpdef int element_count(self) :
        return self.elements

    cpdef void clear(self):
        self.content_idx=0
        self.elements = 0
        
    cdef void add_point(self, float x, float y, float z, float uv_array[8], int node_id, int material_id):
        if not self.can_add():
            return
        
        # Access the current geometry slot to fill
        cdef s_geometry* geom = &self._raw_content[self.content_idx]

        # Set the geometry type to point
        geom.geom_type = 0  # Point

        # Set coordinates
        geom.ax = x
        geom.ay = y
        geom.az = z

        # Initialize unused vertices to zero
        geom.bx = geom.by = geom.bz = 0
        geom.cx = geom.cy = geom.cz = 0

        # Set UV array
        for i in range(8):
            geom.uv_array[i] = uv_array[i]

        # Set IDs
        geom.node_id = node_id
        geom.material_id = material_id

        # Increment the buffer index
        self.content_idx += 1



    cdef void add_line(self, float ax, float ay, float az, float bx, float by, float bz, float uv_array[16], int node_id, int material_id):
        if not self.can_add():
            return
        
        cdef s_geometry* geom = &self._raw_content[self.content_idx]
        geom.geom_type = 1  # Line
        geom.ax = ax
        geom.ay = ay
        geom.az = az
        geom.bx = bx
        geom.by = by
        geom.bz = bz
        geom.cx = geom.cy = geom.cz = 0  # Unused

        for i in range(16):
            geom.uv_array[i] = uv_array[i]

        geom.node_id = node_id
        geom.material_id = material_id
        self.content_idx += 1


    cdef void set_polygon_count(self, int at, int count) noexcept nogil:
        cdef s_geometry* geom = &self._raw_content[at]
        geom[0].geom_type = 3  # Polygon
        geom[0].polygon_count = count

    cdef void add_triangle(self, float ax, float ay, float az, float bx, float by, float bz, float cx, float cy, float cz, float uv_array[48], int node_id, int material_id):
        if not self.can_add():
            return

        cdef s_geometry* geom = &self._raw_content[self.content_idx]
        geom.geom_type = 2  # Triangle
        geom.ax = ax
        geom.ay = ay
        geom.az = az
        geom.bx = bx
        geom.by = by
        geom.bz = bz
        geom.cx = cx
        geom.cy = cy
        geom.cz = cz

        for i in range(48):
            geom.uv_array[i] = uv_array[i]

        geom.node_id = node_id
        geom.material_id = material_id
        self.content_idx += 1

    cpdef add_point_to_buffer(self, float x, float y, float z, list uv_list, int node_id, int material_id):
        cdef float uv_array[32]
        if len(uv_list) != 32:
            raise ValueError("UV list must contain exactly 32 elements. [au,av, bu,bv]  for 8 layers")

        for i in range(32):
            uv_array[i] = uv_list[i]
        self.add_point(x, y, z, uv_array, node_id, material_id)
        self.elements += 1
    cpdef add_line_to_buffer(self, list start, list end, list uv_list, int node_id, int material_id):
        cdef float uv_array[16]
        if len(start) != 3 or len(end) != 3 or len(uv_list) != 16:
            raise ValueError("Start and end lists must contain exactly 3 elements each, and UV list must contain exactly 16 elements.")
        for i in range(16):
            uv_array[i] = uv_list[i]
        self.add_line(start[0], start[1], start[2], end[0], end[1], end[2], uv_array, node_id, material_id)
        self.elements += 1
    cpdef add_triangle_to_buffer(self, list point_a, list point_b, list point_c, list uv_list, int node_id, int material_id):
        cdef float uv_array[48]
        if len(point_a) != 3 or len(point_b) != 3 or len(point_c) != 3 or len(uv_list) != 48:
            raise ValueError("Point lists (A, B, C) must contain exactly 3 elements each, and UV list must contain exactly 48 elements.")
        for i in range(48):
            uv_array[i] = uv_list[i]
        self.add_triangle(point_a[0], point_a[1], point_a[2], point_b[0], point_b[1], point_b[2], point_c[0], point_c[1], point_c[2], uv_array, node_id, material_id)
        self.elements += 1

    cpdef add_polygon_to_buffer(self, list vertex,list face_uvs, int node_id, int material_id):
        cdef int facecount = len(face_uvs)
        cdef float uv_array[48]
        cdef int face_idx = 0

        cdef int polygon_index = self.content_idx

        for face_idx in range(facecount):
            the_uv = face_uvs[face_idx]
            point_a = vertex[0]
            point_b = vertex[face_idx+1]
            point_c = vertex[face_idx+2]
            for i in range(48):
                uv_array[i] = the_uv[i]
            self.add_triangle(point_a[0], point_a[1], point_a[2], point_b[0], point_b[1], point_b[2], point_c[0], point_c[1], point_c[2], uv_array, node_id, material_id)

        self.set_polygon_count(polygon_index,facecount)
        self.elements += 1

        
        