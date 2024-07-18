from typing import Tuple
from tt3de.asset_load import load_bmp, load_obj, read_file

from tt3de.richtexture import ImageTexture
from tt3de.tt3de import Point2D, Point3D
from tt3de.tt_2dnodes import TT2Polygon
from tt3de.tt_3dnodes import TT3DPolygon


def fast_load(obj_file: str, cls=None):
    if obj_file.endswith(".obj"):
        (vertices,
        texture_coords,
        normals,
        triangles,
        triangles_vindex,) =load_obj(read_file(obj_file))

        p = TT3DPolygon()

        for triangle in triangles:
            p.vertex_list.append(triangle.v1)
            p.vertex_list.append(triangle.v2)
            p.vertex_list.append(triangle.v3)

            uvs = [Point2D(p.x,1.0-p.y) for p in triangle.uvmap[0]]
            p.uvmap.append(uvs)
        return p

    elif obj_file.endswith(".bmp"):
        with open(obj_file, "rb") as fin:
            imgdata = load_bmp(fin)

        if cls is None:
            return ImageTexture(imgdata)
        else:
            return cls(imgdata)



from rtt3de import MaterialBufferPy
from rtt3de import TextureBufferPy

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
        
        img: ImageTexture = fast_load("models/sky1.bmp")
        texture_buffer.add_texture(img.image_width ,img.image_height ,img.chained_data(),
                                   True,True)
        
        img: ImageTexture = fast_load("models/cubetest2.bmp")
        texture_buffer.add_texture(img.image_width ,img.image_height ,img.chained_data(),
                                   True,True)
        
        img: ImageTexture = fast_load("models/car/car5_taxi.bmp")
        texture_buffer.add_texture(img.image_width ,img.image_height ,img.chained_data(),
                                   True,True)


        material_buffer = MaterialBufferPy()
        material_buffer.add_static((200,10,10),(50,50,50),0) # 0 
        material_buffer.add_static((200,200,200),(100,100,100),99) # white	
        material_buffer.add_static((200,0,0),(100,100,100),50)  # R
        material_buffer.add_static((10,200,0),(100,100,100),39) # G
        material_buffer.add_static((10,5,200),(100,100,100),34) # B

        material_buffer.add_debug_weight(5) # 5
        material_buffer.add_debug_depth(6) # 6
        material_buffer.add_debug_uv(7) # 7


        material_buffer.add_textured(0,99) # idx = 8
        material_buffer.add_textured(1,99) # idx = 9
        material_buffer.add_textured(2,99) # idx = 10

        material_buffer.add_textured(4,99) # idx = 11
        material_buffer.add_textured(5,99) # idx = 12

        
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


