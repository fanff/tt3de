
from tt3de.glm.c_texture cimport Texture2D
from tt3de.glm.primitives.primitives cimport s_drawing_primitive
from tt3de.glm.drawing.c_drawing_buffer cimport s_drawbuffer_cell

from tt3de.glm.geometry.geometry cimport s_geometry
from tt3de.glm.c_buffer cimport s_buffer



ctypedef packed struct s_material:

    int texturemode
    unsigned char albedo_front_r
    unsigned char albedo_front_g
    unsigned char albedo_front_b

    unsigned char albedo_back_r 
    unsigned char albedo_back_g 
    unsigned char albedo_back_b 

    unsigned char glyph_a 
    unsigned char glyph_b 

    int[8] texture_id_array



cdef class Material:
    cdef list[Texture2D] texts
    cdef bint is_texture_alignated
    cdef int texturemode
    cdef unsigned char albedo_front_r
    cdef unsigned char albedo_front_g
    cdef unsigned char albedo_front_b
    cdef unsigned char albedo_back_r 
    cdef unsigned char albedo_back_g 
    cdef unsigned char albedo_back_b 
    cdef unsigned char glyph_a 
    cdef unsigned char glyph_b 
    cdef int[8] texture_id_array


    
    cdef void _rgb_uv_map(self,int texture_id, int index, unsigned char* r, unsigned char* g, unsigned char* b)

    cpdef int texture_factor(self,int texture_id)
    
    cdef void blit_texture_front(self,const int texture_id, int xi_texture,int yi_texture, unsigned char *aleph)
    
    cdef void blit_alignated_ascii_pixel(self, int xiyi_texture, unsigned char *aleph)
    
    #cpdef void test_blit(self,int index_mat,int index_drawing,DrawingBuffer drawing_buffer)

    cdef void _rgb_uv_map(self,int texture_id, int index, unsigned char* r, unsigned char* g, unsigned char* b) 
    
    # albedo color static mode (2)
    cpdef void set_albedo_front(self,unsigned char r, unsigned char g, unsigned char b)


    cpdef void set_albedo_back(self,unsigned char r, unsigned char g, unsigned char b)

    cpdef void set_glyph(self,unsigned char glyph_a, unsigned char glyph_a)




cdef class MaterialBuffer:
    cdef s_buffer material_raw_buff


    cdef s_buffer* get_raw(self)
    cpdef int size(self)
    cpdef void add_material(self,Material material)

    cpdef void add_material_ele(self,s_material material)

    cpdef s_material get_material(self,int idx)