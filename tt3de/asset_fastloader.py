from typing import Tuple
from tt3de.asset_load import load_bmp, load_obj, read_file

from tt3de.richtexture import ImageTexture
from tt3de.tt3de import Point2D, Point3D
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



from rtt3de import MaterialBufferPy
from rtt3de import TextureBufferPy
from rtt3de import VertexBufferPy,TransformPackPy

class MaterialPerfab:
    @staticmethod
    def rust_set_0() -> Tuple[TextureBufferPy, MaterialBufferPy]:
        texture_buffer = TextureBufferPy(32)

        img: ImageTexture = fast_load("models/test_screen256.bmp")
        texture_buffer.add_texture(img.image_width ,img.image_height ,img.chained_data(),
                                   True,True
)

        img: ImageTexture = fast_load("models/test_screen256.bmp")
        texture_buffer.add_texture(img.image_width ,img.image_height ,img.chained_data(),
                                   False,False)

        img: ImageTexture = fast_load("models/sky1.bmp")
        texture_buffer.add_texture(img.image_width ,img.image_height ,img.chained_data(),
                                   True,True)


        material_buffer = MaterialBufferPy()
        material_buffer.add_static((200,10,10),(50,50,50),0)
        material_buffer.add_static((200,200,200),(100,100,100),99) # white	
        material_buffer.add_static((200,0,0),(100,100,100),50)  # R
        material_buffer.add_static((10,200,0),(100,100,100),39) # G
        material_buffer.add_static((10,5,200),(100,100,100),34) # B

        material_buffer.add_debug_weight(1) # 
        material_buffer.add_debug_depth(1) # 
        material_buffer.add_debug_uv(1) # 


        material_buffer.add_textured(0,60) # idx = 8
        material_buffer.add_textured(1,61) # idx = 9
        material_buffer.add_textured(2,62) # idx = 10

        
        return texture_buffer,material_buffer


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


