
from libc.string cimport memset
from libc.stdlib cimport malloc, free
import cython


from tt3de.glm.primitives.primitives cimport s_drawing_primitive


cpdef s_drawing_primitive make_point_primitive(int  node_id,
                                               int  geometry_id,
                                               int  material_id,
                                               int  unique_id,
                                                int ax,
                                                int ay,
                                                float depth
                                               ):
    cdef s_drawing_primitive aprimitiv 

    aprimitiv.node_id=node_id
    aprimitiv.geometry_id=geometry_id
    aprimitiv.material_id=material_id
    aprimitiv.unique_id = unique_id
    aprimitiv.mat[2][0] = depth



    aprimitiv.ax = ax 
    aprimitiv.ay = ay 



    return aprimitiv



@cython.boundscheck(False)
@cython.wraparound(False)
cdef class PrimitivesBuffer:

    def __cinit__(self, int size):

        cdef int _size = size
        self._raw_content = <s_drawing_primitive*> malloc(_size * sizeof(s_drawing_primitive))
        if not self._raw_content:
            raise MemoryError("Failed to allocate primitives buffer.")
        self.size = _size
        self.content_idx = 0
        # prepare a view
        #self.content  = <s_drawing_primitive[:_size]> self._raw_content
    def __dealloc__(self):
        free(self._raw_content)
    cdef s_drawing_primitive* rawaccess(self):
        return self._raw_content
    cpdef unsigned int primitive_count(self):
        return <unsigned int> self.content_idx

    cpdef bint can_add(self):
        return self.content_idx<self.size

    cpdef void add_triangle(self,unsigned int node_id,
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
                            ):

        if not self.can_add(): return

        cdef s_drawing_primitive* aprimitiv = &(self._raw_content[self.content_idx])

        aprimitiv[0].node_id=node_id
        aprimitiv[0].geometry_id=geometry_id
        aprimitiv[0].material_id=material_id
        aprimitiv[0].unique_id = unique_id
        aprimitiv[0].mat[0][0] = ax
        aprimitiv[0].mat[1][0] = ay
        aprimitiv[0].mat[2][0] = az
        aprimitiv[0].mat[0][1] = bx
        aprimitiv[0].mat[1][1] = by
        aprimitiv[0].mat[2][1] = bz
        aprimitiv[0].mat[0][2] = cx
        aprimitiv[0].mat[1][2] = cy
        aprimitiv[0].mat[2][2] = cz



        self.content_idx +=1

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
                            ):


        if not self.can_add(): return

        cdef s_drawing_primitive* aprimitiv = &(self._raw_content[self.content_idx])
        #self._raw_content[self.content_idx].node_id = node_id


        aprimitiv.node_id=node_id
        aprimitiv.geometry_id=geometry_id
        aprimitiv.material_id=material_id
        aprimitiv.unique_id = unique_id

        aprimitiv.mat[0][0] = ax
        aprimitiv.mat[1][0] = ay
        aprimitiv.mat[2][0] = az

        aprimitiv.mat[0][1] = bx
        aprimitiv.mat[1][1] = by
        aprimitiv.mat[2][1] = bz
        aprimitiv.mat[0][2] = 0.0
        aprimitiv.mat[1][2] = 0.0
        aprimitiv.mat[2][2] = 0.0


        self.content_idx +=1


    cpdef void add_point(self,int  node_id,
                            int  geometry_id,
                            int  material_id,
                            int  unique_id,
                            float x,
                            float y,
                            float z):

        if not self.can_add(): return

        cdef s_drawing_primitive* aprimitiv = &(self._raw_content[self.content_idx])
        #self._raw_content[self.content_idx].node_id = node_id


        aprimitiv.node_id=node_id
        aprimitiv.geometry_id=geometry_id
        aprimitiv.material_id=material_id
        aprimitiv.unique_id = unique_id

        aprimitiv.mat[0][0] = x
        aprimitiv.mat[1][0] = y
        aprimitiv.mat[2][0] = z

        aprimitiv.mat[0][1] = 0.0
        aprimitiv.mat[1][1] = 0.0
        aprimitiv.mat[2][1] = 0.0
        aprimitiv.mat[0][2] = 0.0
        aprimitiv.mat[1][2] = 0.0
        aprimitiv.mat[2][2] = 0.0


        self.content_idx +=1

    
    
    cpdef s_drawing_primitive get_primitive(self,int ixd):
        cdef s_drawing_primitive lol = (self._raw_content[ixd])
        if ixd<self.content_idx:
            return lol