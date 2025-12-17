# -*- coding: utf-8 -*-
import struct
from typing import List, Tuple

from tt3de.points import Point2D, Point3D


def read_file(obj_file):
    with open(obj_file, "rb") as fin:
        return fin.read()


def load_bmp(
    f, alpha=255, transparent_colors: List[Tuple[int, int, int]] = None
) -> List[List[int]]:
    def read_bytes(f, num):
        return struct.unpack("<" + "B" * num, f.read(num))

    def read_int(f):
        return struct.unpack("<I", f.read(4))[0]

    def read_short(f):
        return struct.unpack("<H", f.read(2))[0]

    # Read BMP header
    header_field = read_bytes(f, 2)
    if header_field != (0x42, 0x4D):  # 'BM'
        raise ValueError("Not a BMP file")

    file_size = read_int(f)
    reserved1 = read_short(f)
    reserved2 = read_short(f)
    pixel_array_offset = read_int(f)

    # Read DIB header
    dib_header_size = read_int(f)
    width = read_int(f)
    height = read_int(f)
    planes = read_short(f)
    bit_count = read_short(f)
    compression = read_int(f)
    image_size = read_int(f)
    x_pixels_per_meter = read_int(f)
    y_pixels_per_meter = read_int(f)
    colors_used = read_int(f)
    important_colors = read_int(f)

    # Check if it's a 24-bit BMP
    if bit_count != 24:
        raise ValueError("Only 24-bit BMP files are supported")

    # Move to pixel array
    f.seek(pixel_array_offset)

    # Read pixel data
    row_padded = (
        width * 3 + 3
    ) & ~3  # Row size is padded to the nearest 4-byte boundary

    image_rows: List[List[int]] = []

    for y in range(height):
        row = []
        for x in range(width):
            b, g, r = read_bytes(f, 3)

            # make color and append to the row
            if transparent_colors and (r, g, b) in transparent_colors:
                row.append((r, g, b, 0))
            else:
                row.append((r, g, b, alpha))

        image_rows.insert(0, row)  # BMP files are bottom to top
        f.read(row_padded - width * 3)  # Skip padding

    return list(reversed(image_rows))


def round_to_palette(
    pixel_data: List[List[Tuple[int, int, int]]], palette: List[Tuple[int, int, int]]
) -> List[List[Tuple[int, int, int]]]:
    def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
        return (
            (c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2
        ) ** 0.5

    def find_closest_color(
        pixel: Tuple[int, int, int], palette: List[Tuple[int, int, int]]
    ) -> Tuple[int, int, int]:
        return min(palette, key=lambda color: color_distance(pixel, color))

    rounded_pixel_data = []
    for row in pixel_data:
        rounded_row = [find_closest_color(pixel, palette) for pixel in row]
        rounded_pixel_data.append(rounded_row)

    return rounded_pixel_data


def extract_palette(
    pixel_data: List[List[Tuple[int, int, int]]],
) -> List[Tuple[int, int, int]]:
    unique_colors = set()
    for row in pixel_data:
        for pixel in row:
            unique_colors.add(pixel)
    return list(unique_colors)


def load_palette(filename):
    return extract_palette(load_bmp(filename))


class Triangle3D:
    def __init__(self, v1: Point3D, v2: Point3D, v3: Point3D, normal: Point3D):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.normal = normal
        self.uvmap: List[tuple[Point2D, Point2D, Point2D]] = None


def load_obj(obj_bytes):
    vertices = []
    texture_coords = [[] for _ in range(8)]
    normals = []
    triangles: List[Triangle3D] = []
    triangles_vindex = []
    lines = obj_bytes.decode("utf-8").split("\n")

    for line in lines:
        parts = line.split()
        if not parts:
            continue
        # print(len(normals))
        if parts[0] == "v":
            # Vertex definition
            x, y, z = map(float, parts[1:4])
            vertices.append(Point3D(x, y, z))
        elif parts[0] == "vt":
            # Texture coordinate definition
            u, v = map(float, parts[1:3])
            texture_coords[0].append(Point2D(u, v))
        elif parts[0] == "vn":
            # Normal vector definition
            x, y, z = map(float, parts[1:4])
            normals.append(Point3D(x, y, z))
        elif parts[0] == "f":
            # Face definition
            face_vertices = []
            face_tex_coords = [[] for _ in range(8)]
            face_normals = []

            # list of vertex indices
            face_vertices_index = []

            for part in parts[1:]:
                # print("part is "+part)
                vertex_indices = part.split("/")
                vertex_index = int(vertex_indices[0]) - 1
                face_vertices.append(vertices[vertex_index])
                face_vertices_index.append(vertex_index)

                if len(vertex_indices) > 1 and vertex_indices[1]:
                    # index of the point2D of the uv
                    tex_coord_index = int(vertex_indices[1]) - 1
                    face_tex_coords[0].append(texture_coords[0][tex_coord_index])
                else:
                    face_tex_coords[0].append(None)

                if len(vertex_indices) > 2 and vertex_indices[2]:
                    normal_index = int(vertex_indices[2]) - 1
                    # print(f"normal_index {normal_index}")
                    face_normals.append(normals[normal_index])
                else:
                    face_normals.append(None)

            if len(face_vertices) == 3:
                uv_vectors = [face_tex_coords[layer][0:3] for layer in range(8)]
                t = Triangle3D(
                    face_vertices[0], face_vertices[1], face_vertices[2], None
                )

                triangles_vindex.append(tuple(face_vertices_index))
                t.uvmap = uv_vectors

                FNnormals = face_normals[0:3]

                # print(f"norml {FNnormals}")
                triangles.append(t)
            else:
                for i in range(1, len(face_vertices) - 1):
                    uv_vectors = [
                        [
                            face_tex_coords[layer][0],
                            face_tex_coords[layer][i],
                            face_tex_coords[layer][i + 1],
                        ]
                        for layer in range(1)
                    ]

                    FNnormals = face_normals[0:3]

                    t = Triangle3D(
                        face_vertices[0],
                        face_vertices[i],
                        face_vertices[i + 1],
                        None,
                    )
                    triangles_vindex.append(
                        (
                            face_vertices_index[0],
                            face_vertices_index[i],
                            face_vertices_index[i + 1],
                        )
                    )

                    t.uvmap = uv_vectors
                    triangles.append(t)

    return (
        vertices,
        texture_coords,
        normals,
        triangles,
        triangles_vindex,
    )
