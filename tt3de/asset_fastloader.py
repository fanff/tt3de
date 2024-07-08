from typing import Tuple
from tt3de.asset_load import load_bmp, load_obj, read_file

from tt3de.richtexture import ImageTexture
from tt3de.tt3de import Point2D, Point3D, Triangle3D
from tt3de.tt_2dnodes import TT2Polygon
from tt3de.utils import TT3DEMaterialMode, TT3DEMaterialTextureMappingOptions


def fast_load(obj_file: str, cls=None):
    if obj_file.endswith(".obj"):
        return load_obj(cls, read_file(obj_file))
    elif obj_file.endswith(".bmp"):
        with open(obj_file, "rb") as fin:
            imgdata = load_bmp(fin)

        if cls is None:
            return ImageTexture(imgdata)
        else:
            return cls(imgdata)


from tt3de.glm.c_texture import TextureArray
from tt3de.glm.material.c_material import MaterialBuffer
from tt3de.glm.material.c_material import Material
from rtt3de import MaterialBufferPy
from rtt3de import TextureBufferPy
from rtt3de import VertexBufferPy,TransformPackPy

class MaterialPerfab:
    @staticmethod
    def rust_set_0() -> Tuple[TextureBufferPy, MaterialBufferPy]:
        texture_buffer = TextureBufferPy(32)
        material_buffer = MaterialBufferPy()
        material_buffer.add_static((200,10,10),(50,50,50),0)
        material_buffer.add_static((10,200,10),(50,100,50),2)
        material_buffer.add_static((10,10,200),(200,20,20),99)
        
        return texture_buffer,material_buffer

    @staticmethod
    def set_0() -> Tuple[TextureArray, MaterialBuffer]:
        """Return a tuple containing a TextureArray and a MaterialBuffer.

        This function initializes a TextureArray and a MaterialBuffer with various materials for different purposes:
        - A background colorizer material with specific albedo values for front and back faces.
        - Another background colorizer material with different albedo values.
        - A material for debugging the depth buffer with specific albedo values and glyph settings.
        - A material for debugging weights with specific albedo values and glyph settings.
        - A material for UV mapping debug with specific albedo values and glyph settings.
        - A material for UV mapping text with specific albedo values, glyph settings, and texture IDs.

        Returns:
            Tuple[TextureArray, MaterialBuffer]: A tuple containing the initialized TextureArray and MaterialBuffer.
        """
        texture_array = TextureArray()
        texture_array.load_texture256_from_list(
            fast_load("models/cubetest32.bmp").img_data
        )
        texture_array.load_texture256_from_list(
            fast_load("models/test_screen32.bmp").img_data
        )

        material_buffer = MaterialBuffer()

        # a background colorizer
        mat = Material(texturemode=3)
        mat.set_albedo_front(1, 2, 3)
        mat.set_albedo_back(100, 80, 80)
        material_buffer.add_material(mat)

        # another background colorizer
        mat = Material(texturemode=3)
        mat.set_albedo_front(1, 2, 3)
        mat.set_albedo_back(80, 100, 80)
        material_buffer.add_material(mat)

        # depth buffer debug
        mat1 = Material(texturemode=TT3DEMaterialMode.DEBUG_DEPTH_BUFFER.value)
        mat1.set_albedo_front(16, 0, 150)
        mat1.set_albedo_back(255, 255, 255)
        mat1.set_glyph(4, 4)
        mat1.set_texture_ids([0, -1, -1])  # using 0 for the texture array
        material_buffer.add_material(mat1)

        # WEIGHT DEBUG
        mat1 = Material(texturemode=TT3DEMaterialMode.DEBUG_WEIGHTS.value)
        mat1.set_albedo_front(16, 0, 150)
        mat1.set_albedo_back(255, 0, 255)
        mat1.set_glyph(4, 4)
        material_buffer.add_material(mat1)

        # UV debug
        mat1 = Material(texturemode=TT3DEMaterialMode.UV_MAPPING_DEBUG.value)
        mat1.set_albedo_front(16, 0, 150)
        mat1.set_albedo_back(255, 0, 255)
        mat1.set_glyph(4, 4)
        material_buffer.add_material(mat1)

        # uv mapping debug
        mat2 = Material(texturemode=TT3DEMaterialMode.UV_MAPPING_TEXT1.value)
        mat2.set_albedo_front(0, 200, 150)
        mat2.set_albedo_back(200, 0, 0)
        mat2.set_glyph(0, 1)
        mat2.set_texture_ids([1, -1, -1])
        material_buffer.add_material(mat2)

        # double raster DEBUG WEIGHT
        mat2 = Material(texturemode=11)
        mat2.set_albedo_front(0, 200, 150)
        mat2.set_albedo_back(200, 0, 0)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([1, -1, -1])
        material_buffer.add_material(mat2)

        # double raster DEBUG UV
        mat2 = Material(texturemode=12)
        mat2.set_albedo_front(0, 200, 150)
        mat2.set_albedo_back(200, 0, 0)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([1, -1, -1])
        material_buffer.add_material(mat2)

        # double raster Texture 0
        mat2 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat2.set_albedo_front(0, 200, 150)
        mat2.set_albedo_back(200, 0, 0)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([1, -1, -1])
        material_buffer.add_material(mat2)

        # double perlin noise
        mat2 = Material(texturemode=TT3DEMaterialMode.DOUBLE_PERLIN_NOISE.value)
        mat2.set_albedo_front(0, 200, 150)
        mat2.set_albedo_back(200, 0, 0)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([1, -1, -1])
        material_buffer.add_material(mat2)

        return texture_array, material_buffer

    def set_1() -> Tuple[TextureArray, MaterialBuffer]:
        
        texture_array = TextureArray()
        texture_array.load_texture256_from_list(
            fast_load("models/cubetest32.bmp").img_data
        )
        texture_array.load_texture256_from_list(
            fast_load("models/test_screen32.bmp").img_data
        )
        texture_array.load_texture256_from_list(
            fast_load("models/test_screen256.bmp").img_data
        )
        texture_array.load_texture256_from_list(
            fast_load("models/sky1.bmp").img_data
        )
        texture_array.load_texture256_from_list(
            fast_load("models/numbersheet.bmp").img_data,
            0,0,255
        )
        texture_array.load_texture256_from_list(
            fast_load("models/sprite_sheet_8px.bmp").img_data,
            0,0,0
        )



        material_buffer = MaterialBuffer()

        # a background colorizer; index 0 
        mat = Material(texturemode=TT3DEMaterialMode.STATIC_BACK_ALBEDO.value)
        mat.set_albedo_front(1, 2, 3)
        mat.set_albedo_back(100, 80, 80)
        material_buffer.add_material(mat)

        # double raster Texture 1 (small 32 text)
        mat2 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([1, -1, -1])
        material_buffer.add_material(mat2)

        # double raster Texture 2 ( 256 texture)
        mat2 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([2, -1, -1])
        material_buffer.add_material(mat2)

        # double raster Texture 3 (sky texture)
        mat2 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([3, -1, -1])
        mops = TT3DEMaterialTextureMappingOptions()
        mops.texture_mapping_repetition = 1
        mat2.set_texture_mapping_options(mops.get_value())
        material_buffer.add_material(mat2)


        # double raster Texture 4 (number_sheet texture)
        mat2 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([4, -1, -1])
        mops = TT3DEMaterialTextureMappingOptions()
        mops.texture_mapping_repetition = 0
        mops.texture_transparency_mode = 1
        mat2.set_texture_mapping_options(mops.get_value())
        material_buffer.add_material(mat2)


        # double raster Texture 4 (number_sheet texture) ; with repetition
        mat2 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([4, -1, -1])
        mops = TT3DEMaterialTextureMappingOptions()
        mops.texture_mapping_repetition = 1
        mops.texture_transparency_mode = 1
        mat2.set_texture_mapping_options(mops.get_value())
        material_buffer.add_material(mat2)


        # double raster Texture 4 (8px sprite sheet) ; with repetition
        mat2 = Material(texturemode=TT3DEMaterialMode.DOUBLE_UV_MAPPING_TEXT1.value)
        mat2.set_glyph(0, 157)
        mat2.set_texture_ids([5, -1, -1])
        mops = TT3DEMaterialTextureMappingOptions()
        mops.texture_mapping_repetition = 1
        mops.texture_transparency_mode = 1
        mat2.set_texture_mapping_options(mops.get_value())
        material_buffer.add_material(mat2)

        return texture_array, material_buffer
    

class Prefab2D:

    @staticmethod
    def unitary_triangle(meshclass):
        vertices = [
            Point3D(0, 0, 1.0),
            Point3D(1.0, 0.0, 1.0),
            Point3D(1.0, 1.0, 1.0),
        ]
        texture_coords = [
            Point2D(0.0, 0),
            Point2D(1, 0),
            Point2D(1, 1),
        ]

        m = meshclass()
        m.vertex_list = vertices
        m.uvmap = [texture_coords]
        return m

    @staticmethod
    def unitary_square(meshclass):
        vertices = [
            [
                Point3D(0.0, 0.0, 1.0),
                Point3D(1.0, 0.0, 1.0),
                Point3D(1.0, 1.0, 1.0),
            ],
            [
                Point3D(0.0, 0.0, 1.0),
                Point3D(1.0, 1.0, 1.0),
                Point3D(0.0, 1.0, 1.0),
            ],
        ]
        texture_coords = [
            [
                Point2D(0.0, 0),
                Point2D(1.0, 0.0),
                Point2D(1.0, 1.0),
            ],
            [
                Point2D(0.0, 0),
                Point2D(1.0, 1.0),
                Point2D(0.0, 1.0),
            ],
        ]

        m = meshclass()
        m.elements = vertices
        m.uvmap = texture_coords
        return m

    @staticmethod
    def unitary_square_polygon() -> TT2Polygon:
        vertices = [
                Point3D(0.0, 0.0, 1.0),
                Point3D(1.0, 0.0, 1.0),
                Point3D(1.0, 1.0, 1.0),
                Point3D(0.0, 1.0, 1.0),
            ]
        texture_coords = [
            [
                Point2D(0.0, 0),
                Point2D(1.0, 0.0),
                Point2D(1.0, 1.0),
            ],
            [
                Point2D(0.0, 0),
                Point2D(1.0, 1.0),
                Point2D(0.0, 1.0),
            ],
        ]

        m = TT2Polygon()
        m.vertex_list = vertices
        m.uvmap = texture_coords
        return m
    @staticmethod
    def uv_coord_from_atlas(atlas_item_size:int=32,idx_x:int = 0,idx_y:int = 0) -> list:

        atlas_step = float(atlas_item_size)/256

        ministep = 0.01/256
        u_min,u_max = (idx_x*atlas_step) + ministep, ((idx_x+1)*atlas_step) - ministep
        v_min,v_max = (idx_y*atlas_step) + ministep, ((idx_y+1)*atlas_step) - ministep

        return [
            [
                Point2D(u_min, v_min),
                Point2D(u_max, v_min),
                Point2D(u_max, v_max),
            ],
            [
                Point2D(u_min, v_min),
                Point2D(u_max, v_max),
                Point2D(u_min, v_max),
            ],
        ]

def prefab_mesh_single_square(meshcls):
    vertices = [
        Point3D(0, 0, 1.0),
        Point3D(1, 0, 1.0),
        Point3D(1, 1, 1.0),
        Point3D(0, 1, 1.0),
    ]
    texture_coords = [
        [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1)],
        [Point2D(0, 0), Point2D(1, 1), Point2D(0, 1)],
    ]
    normals = [
        Point3D(0, 0, 1),
        Point3D(0, 0, 1),
        Point3D(0, 0, 1),
    ]
    triangle_vindex = [(0, 1, 2), (0, 2, 3)]

    triangles = []
    for triangle_idx, vertex_ids in enumerate(triangle_vindex):
        v1, v2, v3 = vertex_ids
        t = Triangle3D(vertices[v1], vertices[v2], vertices[v3])
        t.uvmap = [texture_coords[triangle_idx]]

        triangles.append(t)

    m = meshcls()
    m.vertices = vertices
    m.normals = normals
    m.triangles_vindex = triangle_vindex
    m.triangles = triangles
    return m


def prefab_mesh_single_triangle(meshcls):
    vertices = [
        Point3D(0, 0, 1.0),
        Point3D(1, 0, 1.0),
        Point3D(1, 1, 1.0),
    ]
    texture_coords = [[Point2D(0, 0), Point2D(1, 0), Point2D(1, 1)]]
    normals = [
        Point3D(0, 0, 1),
        Point3D(0, 0, 1),
        Point3D(0, 0, 1),
    ]
    triangle_vindex = [(0, 1, 2)]

    triangles = []
    for triangle_idx, vertex_ids in enumerate(triangle_vindex):
        v1, v2, v3 = vertex_ids
        t = Triangle3D(vertices[v1], vertices[v2], vertices[v3])
        t.uvmap = [texture_coords[triangle_idx]]

        triangles.append(t)

    m = meshcls()
    m.vertices = vertices
    m.normals = normals
    m.triangles_vindex = triangle_vindex
    m.triangles = triangles
    return m
