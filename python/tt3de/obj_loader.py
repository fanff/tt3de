# -*- coding: utf-8 -*-


import os
from typing import List, Tuple, Dict, Any

from glm import floor

from tt3de.points import Point2D, Point3D
from tt3de.richtexture import ImageTexture
from tt3de.tt3de import MaterialBufferPy, TextureBufferPy
from tt3de.tt_3dnodes import TT3DPolygon
import png


class OBJData:
    def __init__(self):
        self.vertices: List[List[float]] = []
        self.texture_coords: List[List[float]] = []
        self.normals = []
        self.groups: List[OBJGroup] = []
        self.materials = []

    def get_material_by_name(self, name):
        for m in self.materials:
            if m.name == name:
                return m
        return None

    def all_polygons(self, flip_triangles=False) -> List[TT3DPolygon]:
        """Triangulate all groups ngones into TT3DPolygons; One TT3DPolygon per material
        for every triangle sharing the same material."""
        all_polygons: List[TT3DPolygon] = []
        for obj_group in self.groups:
            group_polygons = obj_group.triangulate(self, flip_triangles)
            for material_name, polygon in group_polygons.items():
                all_polygons.append(polygon)
        return all_polygons

    def merge_by_material(self, flip_triangles=False) -> Dict[str, TT3DPolygon]:
        """Triangulate all groups ngones into TT3DPolygons; One TT3DPolygon per material
        for every triangle sharing the same material."""
        all_polygons: Dict[str, TT3DPolygon] = {}
        for obj_group in self.groups:
            group_polygons = obj_group.triangulate(self, flip_triangles)
            for material_name, polygon in group_polygons.items():
                if material_name in all_polygons:
                    existing_polygon = all_polygons[material_name]
                    # merge polygons together
                    offset = len(existing_polygon.vertex_list)
                    existing_polygon.vertex_list.extend(polygon.vertex_list)
                    existing_polygon.uvmap.extend(polygon.uvmap)
                    for tri in polygon.triangles:
                        existing_polygon.triangles.append(
                            tuple(idx + offset for idx in tri)
                        )
                else:
                    all_polygons[material_name] = polygon
        return all_polygons


class OBJGroup:
    def __init__(self, name: str = ""):
        self.name: str = name

        self.faces_ngon = []
        """
        faces_ngon is a list of tuples.

        Each tuple contains a list of strings representing the vertices of the ngon and
        the material name. 1/2/3 means vertex 1, uv 2, normal 3.
        e.g. [("1/1/1", "2/2/2", "3/3/3"), obj_material_instance] => a triangle with the given material
        2. [("1/1/1", "2/2/2", "3/3/3", "4/4/4"), obj_material_instance] => a quad with the given material
        etc.
        """

    def add_ngon_strs(self, ngon_str, obj_material):
        """
        Add a ngon represented by a list of strings representing its point attributes
        and its material.

        example: ngon_str=["1/1/1", "2/2/2", "3/3/3"],obj_material=obj_material_instance
        """
        self.faces_ngon.append((ngon_str, obj_material))

    def triangulate(
        self, obj_data: OBJData, flip_triangles=False
    ) -> Dict[str, TT3DPolygon]:
        """Triangulate the ngons in this group into TT3DPolygons; One TT3DPolygon per
        material for every triangle sharing the same material."""
        triangles: List[Tuple[List[str], OBJMaterial]] = []
        for ngon_strs, obj_material in self.faces_ngon:
            # if there is 3 elements in ngon_strs, it is already a triangle
            if len(ngon_strs) == 3:
                triangles.append((ngon_strs, obj_material))
            else:
                # it is assumed to be a polygon fan so we can expand it into triangles
                first_vertex = ngon_strs[0]
                for i in range(1, len(ngon_strs) - 1):
                    triangle_strs = [
                        first_vertex,
                        ngon_strs[i],
                        ngon_strs[i + 1],
                    ]
                    triangles.append((triangle_strs, obj_material))

        # parsing triangles info and remapping vertices
        material_indexed_triangles: Dict[str, List[Any]] = {}

        for triangle_strs, obj_material in triangles:
            triangle_vertices_index: List[int] = []
            triangle_texture_coords: List[Tuple[float, float]] = []
            triangle_normals = []

            for vertex_str in triangle_strs:
                vertex_data = vertex_str.split("/")
                # retrieve the vertex, uv and normal data
                vertice_index = int(vertex_data[0])
                uv_index = int(vertex_data[1])
                normal_index = int(vertex_data[2])
                _vertice = obj_data.vertices[vertice_index - 1]
                uv = obj_data.texture_coords[uv_index - 1]
                normal = obj_data.normals[normal_index - 1]

                # append the data to the triangle lists
                triangle_vertices_index.append(vertice_index)
                triangle_texture_coords.append(uv)
                triangle_normals.append(normal)

            if obj_material.name not in material_indexed_triangles:
                material_indexed_triangles[obj_material.name] = []
            material_indexed_triangles[obj_material.name].append(
                (
                    triangle_vertices_index,
                    triangle_texture_coords,
                    triangle_normals,
                    obj_material,
                )
            )

        # group_vidx = {}
        # for obj_v, group_v in vertices_remapper.items():
        #     vertice = obj_data.vertices[obj_v - 1]
        #     group_vidx[group_v] = Point3D(vertice[0], vertice[1], vertice[2])
        # [v for k, v in sorted(group_vidx.items(), key=lambda x: x[0])]
        # create one TT3DPolygon for every material
        polygons: Dict[str, TT3DPolygon] = {}
        for material_name, triangles_data in material_indexed_triangles.items():
            if material_name in polygons:
                polygon = polygons[material_name]
            else:
                polygon = TT3DPolygon()
                polygons[material_name] = polygon
            vertex_remapper = {}
            vertex_counter = 0
            for (
                triangle_vertices_index,
                triangle_texture_coords,
                triangle_normals,
                obj_material,
            ) in triangles_data:
                # adding all triangles to the polygon
                rebuilded_vertices_idx = []

                for vidx in triangle_vertices_index:
                    if vidx not in vertex_remapper:
                        vertex_remapper[vidx] = vertex_counter
                        vertex_counter += 1
                    rebuilded_vertices_idx.append(vertex_remapper[vidx])

                if flip_triangles:
                    rebuilded_vertices_idx = [
                        rebuilded_vertices_idx[0],
                        rebuilded_vertices_idx[2],
                        rebuilded_vertices_idx[1],
                    ]
                # polygon.vertex_list.extend(points)

                uvl: List[Point2D] = [Point2D(x, y) for x, y in triangle_texture_coords]
                p0x, p0y = triangle_texture_coords[0]
                p1x, p1y = triangle_texture_coords[1]
                p2x, p2y = triangle_texture_coords[2]

                # shift the uv toward somewhere positive (TT3DE can't manage negative uv for now)
                if False:
                    minu = floor(min(p0x, p1x, p2x))
                    minv = floor(min(p0y, p1y, p2y))
                else:
                    minu = 0
                    minv = 0
                uv = [
                    Point2D(p0x - minu, p0y - minv),
                    Point2D(p1x - minu, p1y - minv),
                    Point2D(p2x - minu, p2y - minv),
                ]
                if flip_triangles:
                    uv = (uvl[0], uvl[2], uvl[1])
                else:
                    uv = (uvl[0], uvl[1], uvl[2])
                polygon.uvmap.append(uv)
                polygon.triangles.append(tuple(rebuilded_vertices_idx))
            polygon.material_id = obj_material.material_index

            group_vidx: Dict[int, Point3D] = {}
            for obj_v, group_v in vertex_remapper.items():
                # vertice = obj_data.vertices[obj_v - 1]
                group_vidx[group_v] = Point3D(*obj_data.vertices[obj_v - 1])
            polygon.vertex_list = [
                v for k, v in sorted(group_vidx.items(), key=lambda x: x[0])
            ]

        return polygons


class OBJMaterial:
    def __init__(self):
        self.name = ""
        self.ambient = [0.0, 0.0, 0.0]
        self.diffuse = [0.0, 0.0, 0.0]
        self.specular = [0.0, 0.0, 0.0]
        self.shininess = 0.0
        self.texture = ""
        self.texture_index = None
        self.material_index = None

    def load_texture(
        self,
        texture_buffer: TextureBufferPy,
        relative_path,
        repeat_width=True,
        repeat_height=True,
    ):
        texture_full_path = os.path.join(relative_path, self.texture)
        if texture_full_path.endswith(".bmp"):
            pass
            # load the texture
            # return the texture
        elif texture_full_path.endswith(".png"):
            pixel_data: List[List[int]] = []
            reader = png.Reader(filename=texture_full_path)
            width, height, rows, metadata = reader.read()

            pixel_format = metadata["planes"]
            for row in rows:
                row_pixel = []
                for col in range(width):
                    if pixel_format == 1:
                        pixel = row[col]
                        row_pixel.append(pixel)
                    elif pixel_format == 3:
                        r, g, b = row[col * 3 : col * 3 + 3]
                        row_pixel.append((r, g, b))
                    elif pixel_format == 4:
                        r, g, b, a = row[col * 4 : col * 4 + 4]
                        row_pixel.append((r, g, b, a))
                pixel_data.append(row_pixel)
            img: ImageTexture = ImageTexture(list(reversed(pixel_data)))
            index_in_buffer = texture_buffer.add_texture(
                width, height, img.chained_data(), repeat_width, repeat_height
            )
            self.texture_index = index_in_buffer
        else:
            raise Exception("Unsupported texture format")

    def load_material(self, material_buffer: MaterialBufferPy):
        self.material_index = material_buffer.add_textured(self.texture_index, 95)


class OBJFace:
    def __init__(self):
        self.vertices = []
        self.texture_coords = []
        self.normals = []

    def get_triangle(self):
        if len(self.vertices) == 3:
            return self.vertices
        else:
            triangles = []
            for i in range(1, len(self.vertices) - 1):
                triangles.append(
                    [self.vertices[0], self.vertices[i], self.vertices[i + 1]]
                )
            return triangles


def load_mtl(
    file_path, texture_buffer: TextureBufferPy, material_buffer: MaterialBufferPy
):
    materials: List[OBJMaterial] = []
    current_material = None
    with open(file_path, "r") as f:
        all_lines = f.readlines()

    for line in all_lines:
        if line.startswith("newmtl "):
            if current_material is not None:
                materials.append(current_material)
            current_material = OBJMaterial()
            current_material.name = line[7:].strip()
        elif line.startswith("Ka "):
            current_material.ambient = [float(x) for x in line[3:].split()]
        elif line.startswith("Kd "):
            current_material.diffuse = [float(x) for x in line[3:].split()]
        elif line.startswith("Ks "):
            current_material.specular = [float(x) for x in line[3:].split()]
        elif line.startswith("Ns "):
            current_material.shininess = float(line[3:])
        elif line.startswith("map_Kd "):
            current_material.texture = line[7:].strip()

    if current_material is not None:
        materials.append(current_material)
    for material in materials:
        material.load_texture(texture_buffer, os.path.dirname(file_path))
        material.load_material(material_buffer)
    return materials


def load_obj(
    file_path, texture_buffer: TextureBufferPy, material_buffer: MaterialBufferPy
) -> OBJData:
    # get directory of obj file
    directory = os.path.dirname(file_path)
    obj_data = OBJData()
    with open(file_path, "r") as f:
        all_lines = f.readlines()
    current_mtl_obj = None
    current_obj_group: OBJGroup | None = None
    for line in all_lines:
        if line.startswith("v "):
            obj_data.vertices.append([float(x) for x in line[2:].split()])
        elif line.startswith("vt "):
            obj_data.texture_coords.append([float(x) for x in line[3:].split()])
        elif line.startswith("vn "):
            obj_data.normals.append([float(x) for x in line[3:].split()])
        elif line.startswith("g "):
            current_obj_group = OBJGroup(line[2:].strip())
            obj_data.groups.append(current_obj_group)
        elif line.startswith("f "):
            current_mtl_obj
            ngon_str = [x for x in line[2:].split()]
            if current_obj_group is None:
                current_obj_group = OBJGroup("default")
                obj_data.groups.append(current_obj_group)
            assert current_obj_group is not None
            current_obj_group.add_ngon_strs(ngon_str, current_mtl_obj)
        elif line.startswith("mtllib "):
            mtlfile_name = line[7:].strip()
            obj_data.materials = load_mtl(
                os.path.join(directory, mtlfile_name), texture_buffer, material_buffer
            )
        elif line.startswith("usemtl "):
            mtl_line = line[7:].strip()
            mtl_obj = obj_data.get_material_by_name(mtl_line)
            current_mtl_obj = mtl_obj

    # all_polygons = []
    ## now proceed to triangulate the ngons
    # for obj_group in obj_data.groups:
    #    obj_group.triangulate(obj_data)
    return obj_data
