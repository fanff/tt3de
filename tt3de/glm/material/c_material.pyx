
from tt3de.glm.drawing.c_drawing_buffer cimport DrawingBuffer,s_drawbuffer_cell


cdef class Material:
    cdef list[Texture2D] texts
    cdef bint is_texture_alignated
    def __cinit__(self, is_texture_alignated=True):
        self.texts = []
        self.is_texture_alignated = is_texture_alignated

    cdef void _rgb_uv_map(self,int texture_id, int index, unsigned char* r, unsigned char* g, unsigned char* b):
        self.texts[texture_id]._get_at(index,r,g,b)

    cpdef int texture_factor(self,int texture_id):
        return self.texts[texture_id].height

    cdef void blit_texture_front(self,const int texture_id, int xi_texture,int yi_texture, unsigned char *aleph):


        cdef int xiyi_texture = (self.texture_factor(texture_id)*xi_texture)  + yi_texture
    
        self._rgb_uv_map( texture_id,xiyi_texture , &(aleph[0]),&(aleph[1]),&(aleph[2]))



    cdef void blit_alignated_ascii_pixel(self, int xiyi_texture, unsigned char *aleph):

        cdef unsigned char c = 0
        self._rgb_uv_map( 0,xiyi_texture , &(aleph[0]),&(aleph[1]),&(aleph[2]))
        self._rgb_uv_map( 1,xiyi_texture , &(aleph[3]),&(aleph[4]),&(aleph[5]))
        self._rgb_uv_map( 2,xiyi_texture , &(aleph[6]),&(aleph[7]),&c)

    cpdef void test_blit(self,int index_mat,int index_drawing,DrawingBuffer drawing_buffer):

        cdef unsigned char *aleph = drawing_buffer.aleph(index_drawing)


        self.blit_alignated_ascii_pixel(index_mat,aleph)

        #self.blit_alignated_ascii_pixel(index)
        pass
    cdef some_kind_ofapply(self,unsigned char *aleph,s_drawbuffer_cell* thecell ):
        cdef int xi_texture = 0
        cdef int yi_texture = 0


        #thecell.w
        #thecell.primitiv_id 
        #thecell.geom_id
        #thecell.node_id
        #ua 
        #va 


        # do a uv mapping 
        #xi_texture = thecell.wa + thecell.wb + thecell.wc
        #yi_texture = 

        self.blit_texture_front(0,xi_texture,yi_texture, aleph)


    def add_texture(self,texture:Texture2D):
        self.texts.append(texture)


cdef class MaterialBuffer:
    cdef list[Material] materials

    def __cinit__(self, ):
        self.materials = []

    def add_material(self, material:Material):
        self.materials.append(material)

    cdef Material get_material(self,int idx):
        return self.materials[idx]


cpdef apply_pixel_shader(DrawingBuffer drawing_buffer,MaterialBuffer material_buffer):

    cdef int xi = 0
    cdef int yi = 0 
    cdef int idx = 0

    cdef unsigned char *aleph
    cdef s_drawbuffer_cell* thecell 

    for xi in range(drawing_buffer.width):
        for yi in range(drawing_buffer.height):
            idx = drawing_buffer.linear_idx(xi,yi)
            aleph = drawing_buffer.aleph(idx)

            thecell = &(drawing_buffer.drawbuffer[idx])

            thecell.primitiv_id 



            material_buffer.get_material(thecell.material_id).some_kind_ofapply(aleph,thecell)




