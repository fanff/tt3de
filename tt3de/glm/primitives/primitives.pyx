
from libc.string cimport memset,memcpy
from libc.stdlib cimport malloc, free
import cython


from tt3de.glm.primitives.primitives cimport s_drawing_primitive
from tt3de.glm.c_buffer cimport s_buffer,initBuffer,freeBuffer,getBuffersize,addElement

DEF PRIMITIVE_TYPE_POINT=0
DEF PRIMITIVE_TYPE_LINE=1
DEF PRIMITIVE_TYPE_TRIANGLE=2

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
        self.size = size
        # prepare a view
        #self.content  = <s_drawing_primitive[:_size]> self._raw_content
        
        initBuffer(&(self.an_arrayofstuff), sizeof(s_drawing_primitive), size)


    def __dealloc__(self):
        free(self._raw_content)
        freeBuffer(&self.an_arrayofstuff)


    cdef s_buffer* rawaccess_array(self):
        return &self.an_arrayofstuff

    cdef s_drawing_primitive* rawaccess(self):  #to be removed 
        return self._raw_content

    cpdef unsigned int primitive_count(self):
        return <unsigned int> getBuffersize(&self.an_arrayofstuff)

    cpdef bint can_add(self):
        return self.an_arrayofstuff.size<self.size

    cpdef void add_triangle(self,int node_id,  int  geometry_id,  int  material_id, float ax, float ay, float az, float bx, float by, float bz, float cx, float cy,
                            float cz):
        if self.an_arrayofstuff.size < self.an_arrayofstuff.capacity :         
            _add_triangle_no_object(&self.an_arrayofstuff,node_id,geometry_id,material_id,ax,ay,az,bx,by,bz,cx,cy,cz)
            self.an_arrayofstuff.size+=1     

    cpdef void add_line(self, int  node_id,  int  geometry_id,  int  material_id,  float ax,  float ay,  float az,  float bx,  float by,  float bz):
        if self.an_arrayofstuff.size < self.an_arrayofstuff.capacity :   
            _add_line(&self.an_arrayofstuff,node_id,geometry_id,material_id,ax,ay,az,bx,by,bz)  
            self.an_arrayofstuff.size+=1                                             
    

    cpdef void add_point(self,int  node_id,
                            int  geometry_id,
                            int  material_id,
                            float x,
                            float y,
                            float z):
        if self.an_arrayofstuff.size < self.an_arrayofstuff.capacity :   
            _add_point(&self.an_arrayofstuff,node_id,geometry_id,material_id,x,y,z)
            self.an_arrayofstuff.size+=1

    
    
    
    cpdef s_drawing_primitive get_primitive(self,int ixd):
        cdef s_drawing_primitive lol = s_drawing_primitive()
        #cdef s_drawing_primitive* dfssdf =self.index_of(ixd)
        memcpy(&lol,self.index_of(ixd) , self.an_arrayofstuff.elementSize)
        return lol


cdef void _add_triangle_no_object(s_buffer* primitiv_buffer_array,int node_id,
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
                            ) :
    cdef s_drawing_primitive* aprimitiv=<s_drawing_primitive* > ((<char*> ((primitiv_buffer_array).data)) + sizeof(s_drawing_primitive) * primitiv_buffer_array.size )
    aprimitiv.primitive_type_id=2
    
    aprimitiv.clipped=0
    aprimitiv.node_id=node_id
    aprimitiv.geometry_id=geometry_id
    aprimitiv.material_id=material_id
    aprimitiv.unique_id = <int> primitiv_buffer_array.size
    aprimitiv.mat[0][0] = ax
    aprimitiv.mat[1][0] = ay
    aprimitiv.mat[2][0] = az
    aprimitiv.mat[0][1] = bx
    aprimitiv.mat[1][1] = by
    aprimitiv.mat[2][1] = bz
    aprimitiv.mat[0][2] = cx
    aprimitiv.mat[1][2] = cy
    aprimitiv.mat[2][2] = cz



    #addElement(primitiv_buffer_array,aprimitiv) 

cdef void _add_line(s_buffer* primitiv_buffer_array, int  node_id,
                            int  geometry_id,
                            int  material_id,
                            float ax,
                            float ay,
                            float az,

                            float bx,
                            float by,
                            float bz,
                            ):

        cdef s_drawing_primitive* aprimitiv=<s_drawing_primitive* > ((<char*> ((primitiv_buffer_array).data)) + sizeof(s_drawing_primitive) * primitiv_buffer_array.size )

        #self._raw_content[self.content_idx].node_id = node_id
        aprimitiv.clipped=0
        aprimitiv.primitive_type_id=1

        aprimitiv.node_id=node_id
        aprimitiv.geometry_id=geometry_id
        aprimitiv.material_id=material_id
        aprimitiv.unique_id = <int> primitiv_buffer_array.size

        aprimitiv.mat[0][0] = ax
        aprimitiv.mat[1][0] = ay
        aprimitiv.mat[2][0] = az

        aprimitiv.mat[0][1] = bx
        aprimitiv.mat[1][1] = by
        aprimitiv.mat[2][1] = bz
        aprimitiv.mat[0][2] = 0.0
        aprimitiv.mat[1][2] = 0.0
        aprimitiv.mat[2][2] = 0.0


        #addElement(primitiv_buffer_array,aprimitiv) 


cdef void _add_point(s_buffer* primitiv_buffer_array,int  node_id,
                            int  geometry_id,
                            int  material_id,
                            float x,
                            float y,
                            float z):

        #if not self.can_add(): return

        cdef s_drawing_primitive* aprimitiv=<s_drawing_primitive* > ((<char*> ((primitiv_buffer_array).data)) + sizeof(s_drawing_primitive) * primitiv_buffer_array.size )
        
        aprimitiv.clipped=0
        aprimitiv.primitive_type_id=0
        aprimitiv.node_id=node_id
        aprimitiv.geometry_id=geometry_id
        aprimitiv.material_id=material_id
        aprimitiv.unique_id = <int> primitiv_buffer_array.size

        aprimitiv.mat[0][0] = x
        aprimitiv.mat[1][0] = y
        aprimitiv.mat[2][0] = z

        aprimitiv.mat[0][1] = 0.0
        aprimitiv.mat[1][1] = 0.0
        aprimitiv.mat[2][1] = 0.0
        aprimitiv.mat[0][2] = 0.0
        aprimitiv.mat[1][2] = 0.0
        aprimitiv.mat[2][2] = 0.0

        #addElement(primitiv_buffer_array,aprimitiv) 