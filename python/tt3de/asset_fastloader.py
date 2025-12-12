# -*- coding: utf-8 -*-
from enum import Enum
from typing import Dict, List, Tuple

from tt3de.asset_load import load_bmp, load_obj, read_file
from tt3de.points import Point2D, Point3D
from tt3de.richtexture import ImageTexture
from tt3de.tt3de import materials
from tt3de.tt_3dnodes import TT3DPolygon
from tt3de.tt3de import MaterialBufferPy, TextureBufferPy, find_glyph_indices_py
from tt3de.tt3de import toglyphmethod


def fast_load(
    obj_file: str,
    cls=None,
    reverse_uv_u=False,
    reverse_uv_v=False,
    inverse_uv=False,
    flip_triangles=False,
    transparent_colors: List[Tuple[int, int, int]] = None,
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
        polygon.flipped_normals = flip_triangles
        polygon.vertex_list = vertices
        polygon.triangles = triangles_vindex
        for triangle in triangles:
            polygon.uvmap.append(triangle.uvmap[0])

        #  for triangle in triangles:
        #     for p in triangle.uvmap[0]:
        #         uv_u = p.x if not reverse_uv_u else 1.0 - p.x
        #         uv_v = p.y if not reverse_uv_v else 1.0 - p.y
        #         uv_point = (
        #             Point2D(uv_u, uv_v) if not inverse_uv else Point2D(uv_v, uv_u)
        #         )
        #         uvs.append(uv_point)
        #     uv1, uv2, uv3 = uvs
        #     if flip_triangles:
        #         polygon.uvmap.append([uv1, uv3, uv2])
        #     else:
        #         polygon.uvmap.append([uv1, uv2, uv3])

        return polygon

    elif obj_file.endswith(".bmp"):
        with open(obj_file, "rb") as fin:
            imgdata = load_bmp(fin, alpha=255, transparent_colors=transparent_colors)

        if cls is None:
            return ImageTexture(imgdata)
        else:
            return cls(imgdata)


class DefaultSpriteSheet32px(Enum):
    ZERO: int = 0
    ONE: int = 1
    TWO: int = 2
    THREE: int = 3
    FOUR: int = 4
    FIVE: int = 5
    SIX: int = 6
    SEVEN: int = 7
    EIGHT: int = 8
    NINE: int = 9

    BOX_LARGE: int = 10
    BOX_MEDIUM: int = 11
    BOX_SMALL: int = 12
    BOX_TINY: int = 13

    MOUSE_CURSOR: int = 14
    MOUSE_CROSS: int = 15

    SPACE: int = 16
    DOT: int = 17
    DOUBLE_DOT: int = 18

    def convert_string_to_sprites(s: str) -> List["DefaultSpriteSheet32px"]:
        result: List[DefaultSpriteSheet32px] = []
        for ch in s:
            if ch.isdigit():
                result.append(DefaultSpriteSheet32px(int(ch)))
            elif ch == " ":
                result.append(DefaultSpriteSheet32px.SPACE)
            elif ch == ".":
                result.append(DefaultSpriteSheet32px.DOT)
            elif ch == ":":
                result.append(DefaultSpriteSheet32px.DOUBLE_DOT)
            else:
                result.append(DefaultSpriteSheet32px.SPACE)

        return result


class SpriteSheetMap:
    sprite_sheet_mapping: Dict[DefaultSpriteSheet32px, int] = {}

    def map_string_to_matidx(self, s: str) -> List[int]:
        return [
            self.sprite_sheet_mapping[sprite]
            for sprite in DefaultSpriteSheet32px.convert_string_to_sprites(s)
        ]


class MaterialPerfab:
    @staticmethod
    def rust_set_0(
        with_sprite_map=False,
    ) -> Tuple[TextureBufferPy, MaterialBufferPy, SpriteSheetMap]:
        """
        Initializes texture and material buffers with pre-loaded images and defined
        materials.

        Textures:
            0: "models/test_screen256.bmp" (repeat_width=True, repeat_height=True)
            1: "models/test_screen256.bmp" (repeat_width=False, repeat_height=False)
            2: "models/sky1.bmp" ( a skybox texture repeat_width=True, repeat_height=True)
            3: "models/sprint_sheet_32px.bmp" (repeat_width=True, repeat_height=True)
            4: "models/cubetest2.bmp" (repeat_width=True, repeat_height=True)
            5: "models/car/car5_taxi.bmp" (repeat_width=True, repeat_height=True)

        Materials:
            0: Static material - diffuse: (200, 10, 10), specular: (50, 50, 50), glyph index: 0
            1: Static white     - diffuse: (200, 200, 200), specular: (100, 100, 100), glyph index: 99
            2: Static red       - diffuse: (200, 0, 0), specular: (100, 100, 100), glyph index: 50
            3: Static green     - diffuse: (10, 200, 0), specular: (100, 100, 100), glyph index: 39
            4: Static blue      - diffuse: (10, 5, 200), specular: (100, 100, 100), glyph index: 34
            5: Debug UV         - glyph index: 5
            6: Debug Depth      - glyph index: 6
            7: Debug UV         - glyph index: 7
            8: Textured (from texture index 0) - with glyph ▀
            9: Textured (from texture index 1) - with glyph ▀
            10: Textured (from texture index 2) - with glyph ▀
            11: Textured (from texture index 4) - with glyph ▀
            12: Textured (from texture index 5) - with glyph ▀
            # for Atlas mapping:
            13: Textured (from texture index 3) - with glyph ▀
            14: Textured (from texture index 3) - glyph " "

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

        img: ImageTexture = ImageTexture(
            load_bmp(
                open("models/sprite_sheet_32px.bmp", "rb"),
                alpha=255,
                transparent_colors=[(0, 0, 255)],
            )
        )
        texture_buffer.add_atlas_texture_from_iter(
            img.image_width, img.image_height, img.chained_data(), 32, 32
        )

        img: ImageTexture = fast_load("models/cubetest2.bmp")
        texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )
        img: ImageTexture = fast_load("models/car/car5_taxi.bmp")
        texture_buffer.add_texture(
            img.image_width, img.image_height, img.chained_data(), True, True
        )

        HALF_UPPER_BLOCK = find_glyph_indices_py("▀")
        FULL_BLOCK = find_glyph_indices_py("█")

        material_buffer = MaterialBufferPy()
        material_buffer.add_static((50, 50, 50), (50, 50, 50), 0)  # 0
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

        material_buffer.add_textured(0, HALF_UPPER_BLOCK)  # idx = 8
        material_buffer.add_textured(1, HALF_UPPER_BLOCK)  # idx = 9
        material_buffer.add_textured(2, HALF_UPPER_BLOCK)  # idx = 10

        material_buffer.add_textured(4, HALF_UPPER_BLOCK)  # idx = 11
        material_buffer.add_textured(5, HALF_UPPER_BLOCK)  # idx = 12

        material_buffer.add_textured(3, HALF_UPPER_BLOCK)  # idx = 13

        # idx = 14 -> 23 are numbers , in background
        for i in range(10):
            material_buffer.add_base_texture(
                materials.BaseTexturePy(
                    albedo_texture_idx=3,
                    albedo_texture_subid=i,
                    glyph_texture_idx=0,
                    glyph_texture_subid=0,
                    front=False,
                    back=True,
                    glyph=False,
                    glyph_uv_0=True,
                    front_uv_0=True,
                    back_uv_0=True,
                    glyph_method=toglyphmethod.ToGlyphMethodPyStatic(
                        find_glyph_indices_py(" ")
                    ),
                )
            )

        # inserting the default sprite sheet elements
        sprite_sheet_map = SpriteSheetMap()
        for sprite in DefaultSpriteSheet32px:
            mat_idx = material_buffer.add_base_texture(
                materials.BaseTexturePy(
                    albedo_texture_idx=3,
                    albedo_texture_subid=sprite.value,
                    glyph_texture_idx=0,
                    glyph_texture_subid=0,
                    front=True,
                    back=True,
                    glyph=True,
                    glyph_uv_0=True,
                    front_uv_0=True,
                    back_uv_0=False,
                    glyph_method=toglyphmethod.ToGlyphMethodPyStatic(HALF_UPPER_BLOCK),
                )
            )

            sprite_sheet_map.sprite_sheet_mapping[sprite] = mat_idx

        if with_sprite_map:
            return texture_buffer, material_buffer, sprite_sheet_map
        return texture_buffer, material_buffer

    @staticmethod
    def character_to_material_index(ch: str) -> int:
        if ch.isdigit():
            return 24 + int(ch)  # digit materials start at 24
        else:
            return 24  # default


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
