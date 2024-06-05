
from tt3de.glm.drawing.c_drawing_buffer cimport DrawingBuffer,s_drawbuffer_cell,s_canvas_cell

from tt3de.glm.c_texture cimport Texture2D,s_texture32,TextureArray
from tt3de.glm.primitives.primitives cimport PrimitivesBuffer,s_drawing_primitive


from tt3de.glm.geometry.geometry cimport GeometryBuffer,s_geometry
from tt3de.glm.c_buffer cimport s_buffer,initBuffer,freeBuffer,addElement
from tt3de.glm.material.c_material cimport s_material




DEF TT3DE_MATERIAL_MODE_DO_NOTHING=0
DEF TT3DE_MATERIAL_MODE_DEBUG=1
DEF TT3DE_MATERIAL_MODE_STATIC_FRONT_ALBEDO=2
DEF TT3DE_MATERIAL_MODE_STATIC_BACK_ALBEDO=3
DEF TT3DE_MATERIAL_MODE_STATIC_GLYPH=4
DEF TT3DE_MATERIAL_MODE_STATIC_ALL=5


DEF TT3DE_MATERIAL_MODE_DEBUG_WEIGHTS=6

DEF TT3DE_MATERIAL_MODE_DEBUG_DEPTH_BUFFER=7

DEF TT3DE_MATERIAL_MODE_BACK_DEPTH_SHADING = 8

DEF TT3DE_MATERIAL_MODE_UV_MAPPING_DEBUG = 9

DEF TT3DE_MATERIAL_MODE_UV_MAPPING_TEXT1 = 10


DEF CONSTANT_A_THIRD = 1.0/3.0
DEF CONSTANT_TWO_THIRD = 2.0/3.0


cdef class Material:
    # helper class for creating material
    def __cinit__(self, is_texture_alignated=True,texturemode=0):
        self.texts = []
        self.is_texture_alignated = is_texture_alignated
        self.texturemode = texturemode

        
        self.albedo_front_r = 0
        self.albedo_front_g = 0
        self.albedo_front_b = 0

        self.albedo_back_r = 0
        self.albedo_back_g = 0
        self.albedo_back_b = 0

        self.glyph_a = 0
        self.glyph_b = 0

        self.texture_id_array = [-1,-1,-1,-1,-1,-1,-1,-1]


    cdef void _rgb_uv_map(self,int texture_id, int index, unsigned char* r, unsigned char* g, unsigned char* b):
        self.texts[texture_id]._get_at(index,r,g,b)

    cpdef int texture_factor(self,int texture_id):
        return (self.texts[texture_id]).get_height()

    cdef void blit_texture_front(self,const int texture_id, int xi_texture,int yi_texture, unsigned char *aleph):

        cdef Texture2D textuyre = self.texts[texture_id]
        cdef int factor = textuyre.get_height()



        cdef int xiyi_texture = (factor*xi_texture)  + yi_texture
    
        self._rgb_uv_map( texture_id,xiyi_texture , &(aleph[0]),&(aleph[1]),&(aleph[2]))



    cdef void blit_alignated_ascii_pixel(self, int xiyi_texture, unsigned char *aleph):
        cdef unsigned char c = 0
        self._rgb_uv_map( 0,xiyi_texture , &(aleph[0]),&(aleph[1]),&(aleph[2]))
        self._rgb_uv_map( 1,xiyi_texture , &(aleph[3]),&(aleph[4]),&(aleph[5]))
        self._rgb_uv_map( 2,xiyi_texture , &(aleph[6]),&(aleph[7]),&c)

    

    cpdef void set_albedo_front(self,unsigned char r, unsigned char g, unsigned char b):
        self.albedo_front_r = r
        self.albedo_front_b = b
        self.albedo_front_g = g

    cpdef void set_albedo_back(self,unsigned char r, unsigned char g, unsigned char b):
        self.albedo_back_r = r
        self.albedo_back_b = b
        self.albedo_back_g = g

    cpdef void set_glyph(self,unsigned char glyph_a, unsigned char glyph_b):
        """set glyph"""
        self.glyph_a = glyph_a
        self.glyph_b = glyph_b

    def set_texture_ids(self, list values):
        for i,v in enumerate(values):
            self.texture_id_array[i] = v

    def add_texture(self,texture:Texture2D):
        self.texts.append(texture)


cdef class MaterialBuffer:
    def __cinit__(self, int capacity=64):
        initBuffer(&(self.material_raw_buff), sizeof(s_material), capacity)

    def __dealloc__(self):
        freeBuffer(&self.material_raw_buff)

    cpdef void add_material_ele(self,s_material material):
        cdef s_material a = material 
        addElement(&self.material_raw_buff , &a)

    cpdef void add_material(self,Material material):

        cdef s_material amat = s_material(texturemode=material.texturemode,
            texturemode=material.texturemode,
            albedo_front_r=material.albedo_front_r,
            albedo_front_g=material.albedo_front_g,
            albedo_front_b=material.albedo_front_b,
            albedo_back_r= material.albedo_back_r,
            albedo_back_g= material.albedo_back_g,
            albedo_back_b= material.albedo_back_b,
            glyph_a = material.glyph_a ,
            glyph_b = material.glyph_b    ,
            texture_id_array = material.texture_id_array)
        addElement(&self.material_raw_buff , &amat)


    cdef s_buffer* get_raw(self):
        return &(self.material_raw_buff)


    cpdef s_material get_material(self,int idx):

        cdef s_material* avalue = <s_material* > ((<char*> (self.material_raw_buff.data)) + sizeof(s_material) * idx )

        return (avalue[0])

cpdef void apply_pixel_shader(
    PrimitivesBuffer primitive_buffer,
    DrawingBuffer drawing_buffer,
    MaterialBuffer material_buffer,
    GeometryBuffer geometry_buffer,
    TextureArray texture_array_object):
    
    cdef unsigned int drawing_buffer_width = drawing_buffer.get_width()
    cdef unsigned int drawing_buffer_height = drawing_buffer.get_height()
    
    cdef s_drawbuffer_cell* depth_buffer_raw = drawing_buffer.get_raw_depth_buffer()
    cdef s_canvas_cell* canvas_buffer_raw = drawing_buffer.get_raw_canvas_buffer()
    # unpacking the structs for fast execution
    cdef s_buffer* primitive_array_buffer = primitive_buffer.rawaccess_array()
    cdef s_geometry* gemoetry_buffer_raw = geometry_buffer.rawaccess()
    
    # deal with material to have its structure pointer
    cdef s_buffer* material_buffer_raw= material_buffer.get_raw()

    # deal with the texture buffer 
    cdef s_texture32* texture_array = texture_array_object.get_raw()
    _apply_pixel_shader(  primitive_array_buffer  ,
            #drawing_buffer,
            depth_buffer_raw,
            canvas_buffer_raw,
            material_buffer_raw,
            gemoetry_buffer_raw ,
            texture_array,
            drawing_buffer_width ,
            drawing_buffer_height
             )

cdef void _apply_pixel_shader(
    s_buffer* primitive_array_buffer,
    s_drawbuffer_cell* depth_buffer_raw,
    s_canvas_cell* canvas_buffer_raw,
    s_buffer* material_buffer_raw,
    s_geometry* gemoetry_buffer_raw  ,
    s_texture32* texture_array,
    unsigned int drawing_buffer_width ,
    unsigned int drawing_buffer_height    ) noexcept nogil:

    cdef int xi = 0
    cdef int yi = 0 
    cdef int idx = 0

    cdef unsigned char *aleph
    cdef s_drawbuffer_cell* thecell 

    cdef s_drawing_primitive* aprimitiv
    cdef s_geometry* the_geom

    cdef s_material* anymat

    for yi in range(drawing_buffer_height):
        for xi in range(drawing_buffer_width):

            #idx = (yi*drawing_buffer_width)+xi # drawing_buffer.linear_idx(xi,yi)
            
            #aleph = drawing_buffer.aleph(idx)
            aleph = &(canvas_buffer_raw[idx].aleph[0])

            thecell = &(depth_buffer_raw[idx])
            # grabing the geometry element
            the_geom =  &(gemoetry_buffer_raw[thecell.geom_id]);
            # grabing the generated primitive quickly 
            aprimitiv = <s_drawing_primitive* > ((<char*> ((primitive_array_buffer).data)) + sizeof(s_drawing_primitive) * thecell.primitiv_id )


            anymat = <s_material* > ((<char*> ((material_buffer_raw).data)) + sizeof(s_material) * thecell.material_id )


            #material = material_buffer.get_material(thecell.material_id)
            some_kind_ofapply(anymat,aleph, thecell, aprimitiv, the_geom, texture_array)

            idx+=1


cdef void some_kind_ofapply(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture32* texture_array) noexcept nogil:
    cdef int i
    cdef float afloat
    


    if material.texturemode == TT3DE_MATERIAL_MODE_DEBUG:
        for i in range(8):
            aleph[i] = i
         
    elif material.texturemode == TT3DE_MATERIAL_MODE_STATIC_FRONT_ALBEDO:
        aleph[0] = material.albedo_front_r
        aleph[1] = material.albedo_front_g
        aleph[2] = material.albedo_front_b
         
    elif material.texturemode == TT3DE_MATERIAL_MODE_STATIC_BACK_ALBEDO:
        aleph[3] = material.albedo_back_r
        aleph[4] = material.albedo_back_g
        aleph[5] = material.albedo_back_b

    elif material.texturemode == TT3DE_MATERIAL_MODE_STATIC_GLYPH:
        aleph[6] = material.glyph_a 
        aleph[7] = material.glyph_b 


    elif material.texturemode == TT3DE_MATERIAL_MODE_STATIC_ALL:
        aleph[0] = material.albedo_front_r
        aleph[1] = material.albedo_front_g
        aleph[2] = material.albedo_front_b

        aleph[3] = material.albedo_back_r
        aleph[4] = material.albedo_back_g
        aleph[5] = material.albedo_back_b

        aleph[6] = material.glyph_a 
        aleph[7] = material.glyph_b 
    elif material.texturemode == TT3DE_MATERIAL_MODE_DEBUG_WEIGHTS:
        
        aleph[3] = <int>abs(thecell.w1 * 255)#material.albedo_back_r
        aleph[4] = <int>abs(thecell.w2 * 255)#material.albedo_back_g
        aleph[5] = <int>abs(thecell.w3 * 255)#material.albedo_back_b
        #thecell.node_id
        #thecell.geom_id,
        #thecell.material_id,
        #thecell.primitiv_id ,
    elif material.texturemode == TT3DE_MATERIAL_MODE_DEBUG_DEPTH_BUFFER:
         
        afloat = max(0.0, min(1.0, thecell.depth_value)) 

        if afloat < CONSTANT_A_THIRD:
            # Map to Blue range (0 - lower_bound)
            aleph[3] = int(255 * (1 - afloat / CONSTANT_A_THIRD))
        elif afloat < CONSTANT_TWO_THIRD:
            aleph[3] = 255
            # Map to Green range (lower_bound - upper_bound)
            aleph[4] = int(255 * ((afloat - CONSTANT_A_THIRD) / (CONSTANT_A_THIRD)))
        else:
            aleph[3] = 255
            aleph[4] = 255
            # Map to Red range (upper_bound - 1)
            aleph[5] = int(255 * ((afloat - CONSTANT_TWO_THIRD) / (CONSTANT_A_THIRD)))

    elif material.texturemode == TT3DE_MATERIAL_MODE_BACK_DEPTH_SHADING:
        pass
    elif material.texturemode == TT3DE_MATERIAL_MODE_UV_MAPPING_DEBUG:
        
        apply_mode_uv_mapping_debug(material,aleph, thecell, the_primitive, the_geometry,texture_array)
        
        # unproject the point to the original s
    elif material.texturemode == TT3DE_MATERIAL_MODE_UV_MAPPING_TEXT1:
        
        apply_mode_uv_mapping_texture_id(material,aleph, thecell, the_primitive, the_geometry,texture_array)
            
        
        
        
    
cdef void apply_mode_uv_mapping_debug(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture32* texture_array) noexcept nogil:
    #unpack the uvs 
    cdef float au = the_geometry.uv_array[0]
    cdef float av = the_geometry.uv_array[1]
    cdef float bu = the_geometry.uv_array[2]
    cdef float bv = the_geometry.uv_array[3]
    cdef float cu = the_geometry.uv_array[4]
    cdef float cv = the_geometry.uv_array[5]


    cdef float u = au * thecell.w1 + bu*thecell.w2 + cu*thecell.w3
    cdef float v = av * thecell.w1 + bv*thecell.w2 + cv*thecell.w3


    u = max(0.0, min(1.0, u))
    v = max(0.0, min(1.0, v))

    aleph[3] = <unsigned char>abs(u * 255)#material.albedo_back_r
    aleph[4] = <unsigned char>abs(v * 255)#material.albedo_back_g
    aleph[5] = 0


    
cdef void apply_mode_uv_mapping_texture_id(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture32* texture_array) noexcept nogil:
    #unpack the uvs 
    cdef float au = the_geometry.uv_array[0]
    cdef float av = the_geometry.uv_array[1]
    cdef float bu = the_geometry.uv_array[2]
    cdef float bv = the_geometry.uv_array[3]
    cdef float cu = the_geometry.uv_array[4]
    cdef float cv = the_geometry.uv_array[5]


    cdef float u = au * thecell.w1 + bu*thecell.w2 + cu*thecell.w3
    cdef float v = av * thecell.w1 + bv*thecell.w2 + cv*thecell.w3
    

    

    cdef s_texture32* thetexture = &(texture_array[material.texture_id_array[0]])
    cdef unsigned char * the_triplet
    cdef int uint = <int>abs(max(0.0, min(1.0, u)) * 31)
    cdef int vint = <int>abs(max(0.0, min(1.0, v)) * 31)

    the_triplet = (thetexture.data[uint][vint])
    
    aleph[3] = the_triplet[0]
    aleph[4] = the_triplet[1]
    aleph[5] = the_triplet[2]