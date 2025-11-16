# -*- coding: utf-8 -*-
from typing import Tuple

from tt3de.asset_load import load_bmp, load_obj, read_file
from tt3de.points import Point2D, Point3D
from tt3de.richtexture import ImageTexture
from tt3de.tt_3dnodes import TT3DPolygon
from tt3de.tt3de import MaterialBufferPy, TextureBufferPy, find_glyph_indices_py


def fast_load(
    obj_file: str,
    cls=None,
    reverse_uv_u=False,
    reverse_uv_v=False,
    inverse_uv=False,
    flip_triangles=False,
):
    if obj_file.endswith(".obj"):
        (
            vertices,
            texture_coords,
            normals,
            triangles,
            triangles_vindex,
        ) = load_obj(read_file(obj_file))

        polygon = TT3DPolygon()

        for triangle in triangles:
            polygon.vertex_list.append(triangle.v1)
            if flip_triangles:
                polygon.vertex_list.append(triangle.v3)
                polygon.vertex_list.append(triangle.v2)
            else:
                polygon.vertex_list.append(triangle.v2)
                polygon.vertex_list.append(triangle.v3)

            uvs = []
            for p in triangle.uvmap[0]:
                uv_u = p.x if not reverse_uv_u else 1.0 - p.x
                uv_v = p.y if not reverse_uv_v else 1.0 - p.y
                uv_point = (
                    Point2D(uv_u, uv_v) if not inverse_uv else Point2D(uv_v, uv_u)
                )
                uvs.append(uv_point)
            uv1, uv2, uv3 = uvs
            if flip_triangles:
                polygon.uvmap.append([uv1, uv3, uv2])
            else:
                polygon.uvmap.append([uv1, uv2, uv3])

        return polygon

    elif obj_file.endswith(".bmp"):
        with open(obj_file, "rb") as fin:
            imgdata = load_bmp(fin)

        if cls is None:
            return ImageTexture(imgdata)
        else:
            return cls(imgdata)


class MaterialPerfab:
    @staticmethod
    def rust_set_0() -> Tuple[TextureBufferPy, MaterialBufferPy]:
        """
        Initializes texture and material buffers with pre-loaded images and defined
        materials.

        Textures:
            0: "models/test_screen256.bmp" (repeat_width=True, repeat_height=True)
            1: "models/test_screen256.bmp" (repeat_width=False, repeat_height=False)
            2: "models/sky1.bmp" (repeat_width=True, repeat_height=True)
            3: "models/sky1.bmp" (repeat_width=True, repeat_height=True)
            4: "models/cubetest2.bmp" (repeat_width=True, repeat_height=True)
            5: "models/car/car5_taxi.bmp" (repeat_width=True, repeat_height=True)

        Materials (glyph index):
            0: Static material - diffuse: (200, 10, 10), specular: (50, 50, 50), glyph index: 0
            1: Static white     - diffuse: (200, 200, 200), specular: (100, 100, 100), glyph index: 99
            2: Static red       - diffuse: (200, 0, 0), specular: (100, 100, 100), glyph index: 50
            3: Static green     - diffuse: (10, 200, 0), specular: (100, 100, 100), glyph index: 39
            4: Static blue      - diffuse: (10, 5, 200), specular: (100, 100, 100), glyph index: 34
            5: Debug UV         - glyph index: 5
            6: Debug Depth      - glyph index: 6
            7: Debug UV         - glyph index: 7
            8: Textured (from static index 0) - glyph index: 99
            9: Textured (from static index 1) - glyph index: 99
            10: Textured (from static index 2) - glyph index: 99
            11: Textured (from static index 4) - glyph index: 99
            12: Textured (from static index 5) - glyph index: 99

        Returns:
            A tuple containing the configured texture buffer and material buffer.
        """
        texture_buffer = TextureBufferPy(32)

        img: ImageTexture = fast_load("models/test_screen256.bmp")
        texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )

        img: ImageTexture = fast_load("models/test_screen256.bmp")
        texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), False, False
        )

        img: ImageTexture = fast_load("models/sky1.bmp")
        texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )

        img: ImageTexture = fast_load("models/sky1.bmp")
        texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )

        img: ImageTexture = fast_load("models/cubetest2.bmp")
        texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )

        img: ImageTexture = fast_load("models/car/car5_taxi.bmp")
        texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )

        HALF_BLOCK = find_glyph_indices_py("▀")
        FULL_BLOCK = find_glyph_indices_py("█")

        material_buffer = MaterialBufferPy()
        material_buffer.add_static((200, 10, 10), (50, 50, 50), 0)  # 0
        material_buffer.add_static(
            (200, 200, 200), (100, 100, 100), FULL_BLOCK
        )  # 1 white
        material_buffer.add_static(
            (200, 0, 0), (100, 100, 100), find_glyph_indices_py("R")
        )  # 2 R letter in red
        material_buffer.add_static((10, 200, 0), (100, 100, 100), 39)  # G
        material_buffer.add_static((10, 5, 200), (100, 100, 100), 34)  # B

        material_buffer.add_debug_uv(5)  # 5
        material_buffer.add_debug_depth(6)  # 6
        material_buffer.add_debug_uv(7)  # 7

        material_buffer.add_textured(0, HALF_BLOCK)  # idx = 8
        material_buffer.add_textured(1, HALF_BLOCK)  # idx = 9
        material_buffer.add_textured(2, HALF_BLOCK)  # idx = 10

        material_buffer.add_textured(4, HALF_BLOCK)  # idx = 11
        material_buffer.add_textured(5, HALF_BLOCK)  # idx = 12

        return texture_buffer, material_buffer


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
    def unitary_square_polygon():
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

        m = object()
        m.vertex_list = vertices
        m.uvmap = texture_coords
        return m

    @staticmethod
    def uv_coord_from_atlas(
        atlas_item_size: int = 32, idx_x: int = 0, idx_y: int = 0
    ) -> list:
        atlas_step = float(atlas_item_size) / 256

        ministep = 0.01 / 256
        u_min, u_max = (
            (idx_x * atlas_step) + ministep,
            ((idx_x + 1) * atlas_step) - ministep,
        )
        v_min, v_max = (
            (idx_y * atlas_step) + ministep,
            ((idx_y + 1) * atlas_step) - ministep,
        )

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
