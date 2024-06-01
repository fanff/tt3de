

ctypedef packed struct line_coef:
    float alpha
    float beta

ctypedef packed struct s_drawing_primitive:
    
    unsigned int node_id
    unsigned int geometry_id
    unsigned int material_id
    unsigned int unique_id
    
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


    # fields bellow are calculated by the raster stage; i guess



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
    cdef s_drawing_primitive* _raw_content
    cdef int size

    cdef unsigned int content_idx


    cdef s_drawing_primitive* rawaccess(self)
    cpdef unsigned int primitive_count(self)
    cpdef bint can_add(self)
    
    cpdef s_drawing_primitive get_primitive(self,int ixd)
    
    
    cpdef void add_triangle(self, unsigned int  node_id,
                            unsigned int  geometry_id,
                            unsigned int  material_id,
                            unsigned int  unique_id,
                            float ax,
                            float ay,
                            float az,

                            float bx,
                            float by,
                            float bz,

                            float cx,
                            float cy,
                            float cz,
                            )
    cpdef void add_line(self, int  node_id,
                            int  geometry_id,
                            int  material_id,
                            int  unique_id,
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
                            int  unique_id,
                            float x,
                            float y,
                            float z)


