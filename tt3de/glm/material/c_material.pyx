



from libc.math cimport modff,fabsf
from tt3de.glm.c_math cimport clampf

from tt3de.glm.drawing.c_drawing_buffer cimport DrawingBuffer,s_drawbuffer_cell,s_canvas_cell


from tt3de.glm.c_texture cimport Texture2D,TextureArray,s_texture_array,s_texture256,map_uv_generic
from tt3de.glm.primitives.primitives cimport PrimitivesBuffer,s_drawing_primitive


from tt3de.glm.geometry.geometry cimport GeometryBuffer,s_geometry
from tt3de.glm.c_buffer cimport s_buffer,initBuffer,freeBuffer,addElement
from tt3de.glm.material.c_material cimport s_material
from tt3de.glm.perlin_noise cimport perlin

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
DEF TT3DE_MATERIAL_MODE_DEBUG_DOUBLE_WEIGHT = 11
DEF TT3DE_MATERIAL_MODE_DEBUG_DOUBLE_UV_MAP = 12
DEF TT3DE_MATERIAL_MODE_DOUBLE_UV_MAP = 13
DEF TT3DE_MATERIAL_MODE_DOUBLE_PERLIN_NOISE = 14


DEF TT3DE_TEXTURE_MAPPING_OPTION_REPEAT = 1
DEF TT3DE_TEXTURE_MAPPING_OPTION_TRANSPARENCY = 2


DEF TT3DE_APPLY_FRONT_DONE = 1
DEF TT3DE_APPLY_BACK_DONE = 2
DEF TT3DE_APPLY_GLYPH_DONE = 4
DEF TT3DE_APPLY_ALL_DONE = 7

DEF CONSTANT_A_THIRD = 1.0/3.0
DEF CONSTANT_TWO_THIRD = 2.0/3.0

DEF DEPTH_BUFFER_COUNT = 2



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
        self.texture_mapping_options = 0

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
    cpdef void set_texture_mapping_options(self,unsigned char opts):
        self.texture_mapping_options = opts


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
            texture_mapping_options = material.texture_mapping_options,
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
    cpdef int size(self):
        return <int> self.material_raw_buff.size

    cpdef s_material get_material(self,int idx):

        cdef s_material* avalue = <s_material* > ((<char*> (self.material_raw_buff.data)) + sizeof(s_material) * idx )

        return (avalue[0])

cpdef void apply_pixel_shader(
    PrimitivesBuffer primitive_buffer,
    DrawingBuffer drawing_buffer,
    MaterialBuffer material_buffer,
    GeometryBuffer geometry_buffer,
    TextureArray texture_array_object):
    
    cdef int drawing_buffer_width = drawing_buffer.get_width()
    cdef int drawing_buffer_height = drawing_buffer.get_height()
    
    cdef s_drawbuffer_cell* depth_buffer_raw = drawing_buffer.get_raw_depth_buffer()
    cdef s_canvas_cell* canvas_buffer_raw = drawing_buffer.get_raw_canvas_buffer()
    # unpacking the structs for fast execution
    cdef s_buffer* primitive_array_buffer = primitive_buffer.rawaccess_array()
    cdef s_geometry* gemoetry_buffer_raw = geometry_buffer.rawaccess()
    
    # deal with material to have its structure pointer
    cdef s_buffer* material_buffer_raw= material_buffer.get_raw()

    # deal with the texture buffer 
    cdef s_texture_array* texture_array = texture_array_object.get_raw()

    
    _apply_pixel_shader(  primitive_array_buffer  ,
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
    s_texture_array* texture_array,
    int drawing_buffer_width ,
    int drawing_buffer_height    ) noexcept nogil:

    cdef int xi = 0
    cdef int yi = 0 
    cdef int idx = 0

    cdef unsigned char *aleph
    cdef s_drawbuffer_cell* thecell 

    cdef s_drawing_primitive* aprimitiv
    cdef s_geometry* the_geom

    cdef s_material* anymat


    cdef int apply_finished = 0
    cdef int depth_layer = DEPTH_BUFFER_COUNT-1
    for yi in range(drawing_buffer_height):
        for xi in range(drawing_buffer_width):
            aleph = canvas_buffer_raw[idx].aleph
            while depth_layer >= 0:

                thecell = &(depth_buffer_raw[ (idx * DEPTH_BUFFER_COUNT) + depth_layer])
                # grabing the geometry element
                the_geom =  &(gemoetry_buffer_raw[thecell.geom_id]);
                # grabing the generated primitive quickly 
                aprimitiv = <s_drawing_primitive* > ((<char*> ((primitive_array_buffer).data)) + sizeof(s_drawing_primitive) * thecell.primitiv_id )

                anymat = <s_material* > ((<char*> ((material_buffer_raw).data)) + sizeof(s_material) * thecell.material_id )

                some_kind_ofapply(anymat,aleph, thecell, aprimitiv, the_geom, texture_array , &apply_finished)
                depth_layer = depth_layer - 1
                                
            idx+=1
            apply_finished = 0
            depth_layer = DEPTH_BUFFER_COUNT-1

cdef void some_kind_ofapply(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture_array* texture_array,
                int* apply_finished) noexcept nogil:
    cdef int i
    cdef float afloat

    if material.texturemode == TT3DE_MATERIAL_MODE_DEBUG:
        for i in range(8):
            aleph[i] = i
        apply_finished[0] = TT3DE_APPLY_ALL_DONE;
    elif material.texturemode == TT3DE_MATERIAL_MODE_STATIC_FRONT_ALBEDO:
        aleph[0] = material.albedo_front_r
        aleph[1] = material.albedo_front_g
        aleph[2] = material.albedo_front_b
        apply_finished[0] = (apply_finished[0]) | TT3DE_APPLY_FRONT_DONE
    
    elif material.texturemode == TT3DE_MATERIAL_MODE_STATIC_BACK_ALBEDO:
        aleph[3] = material.albedo_back_r
        aleph[4] = material.albedo_back_g
        aleph[5] = material.albedo_back_b
        apply_finished[0] = (apply_finished[0]) | TT3DE_APPLY_BACK_DONE
    
    elif material.texturemode == TT3DE_MATERIAL_MODE_STATIC_GLYPH:
        aleph[6] = material.glyph_a 
        aleph[7] = material.glyph_b 
        apply_finished[0] = (apply_finished[0]) | TT3DE_APPLY_GLYPH_DONE

    elif material.texturemode == TT3DE_MATERIAL_MODE_STATIC_ALL:
        aleph[0] = material.albedo_front_r
        aleph[1] = material.albedo_front_g
        aleph[2] = material.albedo_front_b

        aleph[3] = material.albedo_back_r
        aleph[4] = material.albedo_back_g
        aleph[5] = material.albedo_back_b

        aleph[6] = material.glyph_a 
        aleph[7] = material.glyph_b 

        apply_finished[0] = TT3DE_APPLY_ALL_DONE;


    elif material.texturemode == TT3DE_MATERIAL_MODE_DEBUG_WEIGHTS:
        
        aleph[3] = <int>fabsf(thecell.w1 * <float> 255.0)#material.albedo_back_r
        aleph[4] = <int>fabsf(thecell.w2 * <float> 255.0)#material.albedo_back_g
        aleph[5] = <int>fabsf(thecell.w3 * <float> 255.0)#material.albedo_back_b
        #thecell.node_id
        #thecell.geom_id,
        #thecell.material_id,
        #thecell.primitiv_id ,

        apply_finished[0] = (apply_finished[0]) | TT3DE_APPLY_BACK_DONE


    elif material.texturemode == TT3DE_MATERIAL_MODE_DEBUG_DEPTH_BUFFER:
    
        afloat = max(0.0, min(1.0, thecell.depth_value)) 
        aleph[3] = <int> (255 * afloat)
        aleph[4] = 0
        aleph[5] = 0
        
        apply_finished[0] = (apply_finished[0]) | TT3DE_APPLY_BACK_DONE


    elif material.texturemode == TT3DE_MATERIAL_MODE_BACK_DEPTH_SHADING:
        pass
    elif material.texturemode == TT3DE_MATERIAL_MODE_UV_MAPPING_DEBUG:
        
        apply_mode_uv_mapping_debug(material,aleph, thecell, the_primitive, the_geometry,texture_array)
        
        apply_finished[0] = TT3DE_APPLY_ALL_DONE


    elif material.texturemode == TT3DE_MATERIAL_MODE_UV_MAPPING_TEXT1:
        
        apply_mode_uv_mapping_texture_id(material, aleph, thecell, the_primitive, the_geometry, texture_array, apply_finished)
            
    elif material.texturemode == TT3DE_MATERIAL_MODE_DEBUG_DOUBLE_WEIGHT:
        
        apply_mode_debug_double_weight(material,aleph, thecell, the_primitive, the_geometry,texture_array)
        apply_finished[0] = TT3DE_APPLY_ALL_DONE



    elif material.texturemode == TT3DE_MATERIAL_MODE_DEBUG_DOUBLE_UV_MAP:
        apply_mode_debug_double_uv_map(material,aleph, thecell, the_primitive, the_geometry,texture_array)
        apply_finished[0] = TT3DE_APPLY_ALL_DONE



    elif material.texturemode == TT3DE_MATERIAL_MODE_DOUBLE_UV_MAP:
        apply_mode_double_up_mapping_texture_id(material,aleph, thecell, the_primitive, the_geometry,texture_array,apply_finished)
    elif material.texturemode ==  TT3DE_MATERIAL_MODE_DOUBLE_PERLIN_NOISE:
        apply_mode_double_perlin_noise(material,aleph, thecell, the_primitive, the_geometry,texture_array,apply_finished)
    
cdef void apply_mode_uv_mapping_debug(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture_array* texture_array) noexcept nogil:
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
                s_texture_array* texture_array,
                int* apply_finished
                ) noexcept nogil:
    #unpack the uvs 
    cdef float au = the_geometry.uv_array[0]
    cdef float av = the_geometry.uv_array[1]
    cdef float bu = the_geometry.uv_array[2]
    cdef float bv = the_geometry.uv_array[3]
    cdef float cu = the_geometry.uv_array[4]
    cdef float cv = the_geometry.uv_array[5]

    # get uv coordinates 
    cdef float u = au * thecell.w1 + bu*thecell.w2 + cu*thecell.w3
    cdef float v = av * thecell.w1 + bv*thecell.w2 + cv*thecell.w3

    # get the texture
    cdef s_texture256* thetexture= <s_texture256*> (texture_array.pointer_map[material.texture_id_array[0]]) 

    cdef int use_repeat = material.texture_mapping_options & TT3DE_TEXTURE_MAPPING_OPTION_REPEAT
    cdef int use_transp = material.texture_mapping_options & TT3DE_TEXTURE_MAPPING_OPTION_TRANSPARENCY
    
    map_uv_generic(thetexture,use_repeat,use_transp,
                        u,v,
                        &(aleph[3]),&(aleph[4]),&(aleph[5]),apply_finished)
    
    apply_finished[0] = (apply_finished[0]) | TT3DE_APPLY_BACK_DONE


#### DOUBLE MAPPING MODE 
cdef void apply_mode_debug_double_weight(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture_array* texture_array) noexcept nogil:
    
    # set the front as top
    aleph[0] =<int>abs(max(0.0, min(1.0, thecell.w1)) * 255)
    aleph[1] =<int>abs(max(0.0, min(1.0, thecell.w2)) * 255)
    aleph[2] =<int>abs(max(0.0, min(1.0, thecell.w3)) * 255)


    # set the back
    aleph[3] = <int>abs(max(0.0, min(1.0, thecell.w1_alt)) * 255)
    aleph[4] = <int>abs(max(0.0, min(1.0, thecell.w2_alt)) * 255)
    aleph[5] = <int>abs(max(0.0, min(1.0, thecell.w3_alt)) * 255)

    # set the glyph id
    aleph[6] = material.glyph_a 
    aleph[7] = material.glyph_b 

cdef void apply_mode_debug_double_uv_map(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture_array* texture_array) noexcept nogil:
    #unpack the uvs 
    cdef float au = the_geometry.uv_array[0]
    cdef float av = the_geometry.uv_array[1]
    cdef float bu = the_geometry.uv_array[2]
    cdef float bv = the_geometry.uv_array[3]
    cdef float cu = the_geometry.uv_array[4]
    cdef float cv = the_geometry.uv_array[5]


    cdef float u = au * thecell.w1 + bu*thecell.w2 + cu*thecell.w3
    cdef float v = av * thecell.w1 + bv*thecell.w2 + cv*thecell.w3


    cdef float u_alt = au * thecell.w1_alt + bu*thecell.w2_alt + cu*thecell.w3_alt
    cdef float v_alt = av * thecell.w1_alt + bv*thecell.w2_alt + cv*thecell.w3_alt
    

    u = max(0.0, min(1.0, u))
    v = max(0.0, min(1.0, v))
    u_alt = max(0.0, min(1.0, u_alt))
    v_alt = max(0.0, min(1.0, v_alt))


    # set the front as top
    aleph[0] =<unsigned char>((u) * 255)
    aleph[1] =<unsigned char>((v) * 255)
    aleph[2] =0

    # set the back
    aleph[3] = <unsigned char>((u_alt) * 255)
    aleph[4] = <unsigned char>((v_alt) * 255)
    aleph[5] = 0

    # set the glyph id
    aleph[6] = material.glyph_a 
    aleph[7] = material.glyph_b 



    
cdef void apply_mode_double_up_mapping_texture_id(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture_array* texture_array,
                int* apply_finished) noexcept nogil:

                
    #unpack the uvs layer 1 
    cdef float au = the_geometry.uv_array[0]
    cdef float av = the_geometry.uv_array[1]
    cdef float bu = the_geometry.uv_array[2]
    cdef float bv = the_geometry.uv_array[3]
    cdef float cu = the_geometry.uv_array[4]
    cdef float cv = the_geometry.uv_array[5]

    # get uv coordinates 
    cdef float u = au * thecell.w1 + bu*thecell.w2 + cu*thecell.w3
    cdef float v = av * thecell.w1 + bv*thecell.w2 + cv*thecell.w3


    cdef float w1_alt_clamped = clampf(thecell.w1_alt,0.0,1.0 )
    cdef float w2_alt_clamped = clampf(thecell.w2_alt,0.0,1.0 )
    cdef float w3_alt_clamped = clampf(thecell.w3_alt,0.0,1.0 )

    cdef float u_alt = au * w1_alt_clamped + bu * w2_alt_clamped + cu * w3_alt_clamped
    cdef float v_alt = av * w1_alt_clamped + bv * w2_alt_clamped + cv * w3_alt_clamped
    
    # get the texture
    cdef s_texture256* thetexture= <s_texture256*> (texture_array.pointer_map[material.texture_id_array[0]]) 
    
    cdef int use_repeat =( material.texture_mapping_options & TT3DE_TEXTURE_MAPPING_OPTION_REPEAT) > 0
    cdef int use_transp = (material.texture_mapping_options & TT3DE_TEXTURE_MAPPING_OPTION_TRANSPARENCY) > 0


    cdef int application_result_front = 0
    cdef int application_result_back = 0


    map_uv_generic(thetexture,use_repeat,use_transp,
                    u,v,
                    &(aleph[0]),&(aleph[1]),&(aleph[2]),&application_result_front)


    map_uv_generic(thetexture,use_repeat,use_transp,
                    u_alt,v_alt,
                    &(aleph[3]),&(aleph[4]),&(aleph[5]),&application_result_back)
    if application_result_front or application_result_back:
        aleph[6] = material.glyph_a 
        aleph[7] = material.glyph_b 


cdef void apply_mode_double_perlin_noise(s_material* material,
                unsigned char *aleph, 
                s_drawbuffer_cell* thecell ,
                s_drawing_primitive* the_primitive,
                s_geometry* the_geometry,
                s_texture_array* texture_array,
                int* apply_finished) noexcept nogil:
    #unpack the uvs 
    cdef float au = the_geometry.uv_array[0]
    cdef float av = the_geometry.uv_array[1]
    cdef float bu = the_geometry.uv_array[2]
    cdef float bv = the_geometry.uv_array[3]
    cdef float cu = the_geometry.uv_array[4]
    cdef float cv = the_geometry.uv_array[5]

    # get uv coordinates 
    cdef float u = au * thecell.w1 + bu*thecell.w2 + cu*thecell.w3
    cdef float v = av * thecell.w1 + bv*thecell.w2 + cv*thecell.w3
    cdef float u_alt = au * thecell.w1_alt + bu*thecell.w2_alt + cu*thecell.w3_alt
    cdef float v_alt = av * thecell.w1_alt + bv*thecell.w2_alt + cv*thecell.w3_alt
    
    # 
    cdef float a_value = 0.0


    u = max(0.0, min(1.0, u))
    v = max(0.0, min(1.0, v))
    u_alt = max(0.0, min(1.0, u_alt))
    v_alt = max(0.0, min(1.0, v_alt))
    
    # get the color tripplet
    a_value = (perlin(u*2,v*2,5.0)+1.0)/2.0
    
    aleph[0] = <unsigned char>(a_value*255)
    aleph[1] = <unsigned char>(a_value*255)
    aleph[2] = <unsigned char>(a_value*255)


    
    # get the color tripplet
    a_value = (perlin(u_alt*2,v_alt*2,5.0)+1)/2.0
    
    aleph[3] = <unsigned char>(a_value*255)
    aleph[4] = <unsigned char>(a_value*255)
    aleph[5] = <unsigned char>(a_value*255)


    # set the glyph id
    aleph[6] = material.glyph_a 
    aleph[7] = material.glyph_b


    apply_finished[0] = TT3DE_APPLY_ALL_DONE