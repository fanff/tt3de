
from tt3de.glm.c_buffer cimport s_buffer


ctypedef packed struct line_coef:
    float alpha
    float beta

ctypedef packed struct s_drawing_primitive:

    int clipped
    int primitive_type_id
    int node_id
    int geometry_id
    int material_id
    int unique_id

    float * uv_array
    
    
    # fields arbitrary compatible with any kind of primitive
    
    float[3][3] mat      # a matrix storing 9 data for the primitive

    # axf = tr.mat[0][0]
    # ayf = tr.mat[1][0]
    # azf = tr.mat[2][0]

    # bxf = tr.mat[0][1]
    # byf = tr.mat[1][1]
    # bzf = tr.mat[2][1]

    # cxf = tr.mat[0][2]
    # cyf = tr.mat[1][2]
    # czf = tr.mat[2][2]


    # fields bellow are calculated by the raster stage; 



    float[3][3] adjoint  # an adjoint matrix 
    line_coef[3] coefs   # line coef for lines/ triangles / 




    # flat determinant of the triangle (surface on screen)
    float flat_determinant
    
    # clamped limits of the triangle
    unsigned int ax 
    unsigned int ay 
    unsigned int bx 
    unsigned int by 
    unsigned int cx 
    unsigned int cy 





cdef class PrimitivesBuffer:
    cdef s_drawing_primitive* _raw_content # to be removed
    cdef int size
    cdef s_buffer an_arrayofstuff 


    cdef s_drawing_primitive* rawaccess(self)
    cdef s_buffer* rawaccess_array(self)
    cpdef unsigned int primitive_count(self)
    cpdef bint can_add(self)
    cpdef void clear(self)
    cdef inline s_drawing_primitive* index_of(self,int idx):
        return <s_drawing_primitive* > ((<char*> ((&self.an_arrayofstuff).data)) + sizeof(s_drawing_primitive) * idx )


    cpdef void add_line(self, int  node_id,
                            int  geometry_id,
                            int  material_id,
                            float ax,
                            float ay,
                            float az,

                            float bx,
                            float by,
                            float bz,
                            )
    cpdef void add_point(self,int  node_id,
                            int  geometry_id,
                            int  material_id,
                            float x,
                            float y,
                            float z)





cdef void _add_triangle_no_object(s_buffer* primitiv_buffer_array,
                            int node_id,
                            int  geometry_id,
                            int  material_id,
                            float ax,
                            float ay,
                            float az,

                            float bx,
                            float by,
                            float bz,

                            float cx,
                            float cy,
                            float cz,

                            float * uv_array,
                            ) 

cdef void _add_line(s_buffer* primitiv_buffer_array, int  node_id,
                            int  geometry_id,
                            int  material_id,
                            float ax,
                            float ay,
                            float az,

                            float bx,
                            float by,
                            float bz,
                            )


cdef void _add_point(s_buffer* primitiv_buffer_array,int  node_id,
                            int  geometry_id,
                            int  material_id,
                            float x,
                            float y,
                            float z)