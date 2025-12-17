# -*- coding: utf-8 -*-


import os
from typing import List, Tuple

from glm import floor

from tt3de.points import Point2D, Point3D
from tt3de.richtexture import ImageTexture
from tt3de.tt3de import MaterialBufferPy, TextureBufferPy
from tt3de.tt_3dnodes import TT3DPolygon, TT3DPolygonFan
import png


class OBJData:
    def __init__(self):
        self.vertices = []
        self.texture_coords = []
        self.normals = []
        self.groups: List[OBJGroup] = []
        self.materials = []

    def get_material_by_name(self, name):
        for m in self.materials:
            if m.name == name:
                return m
        return None


class OBJGroup:
    def __init__(self, name=""):
        self.name = name

        self.faces_ngon = []
        """
        faces_ngon is a list of tuples.

        Each tuple contains a list of strings representing the vertices of the ngon and
        the material name.
        """

    def add_ngon_strs(self, ngon_str, obj_material):
        """
        Add a ngon represented by a list of strings representing its point attributes
        and its material.

        example: ngon_str=["1/1/1", "2/2/2", "3/3/3"],obj_material=obj_material_instance
        """
        self.faces_ngon.append((ngon_str, obj_material))

    def triangulate(self, obj_data: OBJData, flip_triangles=False):
        """For every ngon in faces_ngon, return a list of triangles and their
        material."""
        triangles: List[Tuple[List[str], OBJMaterial]] = []
        polygon_fans: List[Tuple[List[str], OBJMaterial]] = []
        for ngon_strs, obj_material in self.faces_ngon:
            # if there is 3 elements in ngon_strs, it is already a triangle
            if len(ngon_strs) == 3:
                triangles.append((ngon_strs, obj_material))
            else:
                # it is assumed to be a polygon fan
                polygon_fans.append((ngon_strs, obj_material))

        # the triangles list will be extracted as a TT3DPolygon of independant triangles for every material
        material_indexed_triangles = {}
        for triangle_strs, obj_material in triangles:
            triangle_vertices = []
            triangle_texture_coords = []
            triangle_normals = []
            for vertex_str in triangle_strs:
                vertex_data = vertex_str.split("/")
                # retrieve the vertex, uv and normal data
                vertice_index = int(vertex_data[0])
                uv_index = int(vertex_data[1])
                normal_index = int(vertex_data[2])
                vertice = obj_data.vertices[vertice_index - 1]
                uv = obj_data.texture_coords[uv_index - 1]
                normal = obj_data.normals[normal_index - 1]

                # append the data to the triangle lists
                triangle_vertices.append(vertice)
                triangle_texture_coords.append(uv)
                triangle_normals.append(normal)

            if obj_material.name not in material_indexed_triangles:
                material_indexed_triangles[obj_material.name] = []
            material_indexed_triangles[obj_material.name].append(
                (
                    triangle_vertices,
                    triangle_texture_coords,
                    triangle_normals,
                    obj_material,
                )
            )

        # create one TT3DPolygon for every material
        polygons = []
        for material_name, triangles_data in material_indexed_triangles.items():
            polygon = TT3DPolygon()
            for (
                triangle_vertices,
                triangle_texture_coords,
                triangle_normals,
                obj_material,
            ) in triangles_data:
                # adding all triangles to the polygon
                points = [Point3D(x, y, z) for x, y, z in triangle_vertices]

                if flip_triangles:
                    points = [points[0], points[2], points[1]]
                polygon.vertex_list.extend(points)

                uv = [Point2D(x, y) for x, y in triangle_texture_coords]
                if flip_triangles:
                    uv = [uv[0], uv[2], uv[1]]
                polygon.uvmap.append(uv)
            polygon.material_id = obj_material.material_index

            polygons.append(polygon)

        # the polygon_fans list will be extracted as a TT3DPolygonFan of independant triangles
        material_indexed_polygon_fans = {}
        for polygon_fan_strs, obj_material in polygon_fans:
            polygon_fan_vertices = []
            polygon_fan_texture_coords = []
            polygon_fan_normals = []
            for vertex_str in polygon_fan_strs:
                vertex_data = vertex_str.split("/")
                # retrieve the vertex, uv and normal data
                vertice_index = int(vertex_data[0])
                uv_index = int(vertex_data[1])
                normal_index = int(vertex_data[2])
                vertice = obj_data.vertices[vertice_index - 1]
                uv = obj_data.texture_coords[uv_index - 1]
                normal = obj_data.normals[normal_index - 1]

                # append the data to the triangle lists
                polygon_fan_vertices.append(vertice)
                polygon_fan_texture_coords.append(uv)
                polygon_fan_normals.append(normal)

            if obj_material.name not in material_indexed_polygon_fans:
                material_indexed_polygon_fans[obj_material.name] = []
            material_indexed_polygon_fans[obj_material.name].append(
                (
                    polygon_fan_vertices,
                    polygon_fan_texture_coords,
                    polygon_fan_normals,
                    obj_material,
                )
            )

        polygon_fans = []
        # build the polygon_fans
        for material_name, polygon_fans_data in material_indexed_polygon_fans.items():
            polygon_fan = TT3DPolygonFan()
            for (
                polygon_fan_vertices,
                polygon_fan_texture_coords,
                polygon_fan_normals,
                obj_material,
            ) in polygon_fans_data:
                # adding all triangles to the polygon
                points = [Point3D(x, y, z) for x, y, z in polygon_fan_vertices]
                polygon_fan.vertex_list.extend(points)

                # unfan the uv by tripplets
                centrer_u, center_v = polygon_fan_texture_coords[0]
                for i in range(1, len(polygon_fan_texture_coords) - 1):
                    p1x, p1y = polygon_fan_texture_coords[i]
                    p2x, p2y = polygon_fan_texture_coords[i + 1]

                    # shift the uv toward positive values
                    minu = floor(min(centrer_u, p1x, p2x))
                    minv = floor(min(center_v, p1y, p2y))
                    uv = [
                        Point2D(centrer_u - minu, center_v - minv),
                        Point2D(p1x - minu, p1y - minv),
                        Point2D(p2x - minu, p2y - minv),
                    ]
                    if flip_triangles:
                        uv = [uv[0], uv[2], uv[1]]
                    polygon_fan.uvmap.append(uv)

                # uv = [Point2D(x,y) for x,y in polygon_fan_texture_coords]
                # polygon_fan.uvmap.append(uv)
            polygon_fan.material_id = obj_material.material_index

            polygon_fans.append(polygon_fan)
        return polygons, polygon_fans


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
):
    # get directory of obj file
    directory = os.path.dirname(file_path)
    obj_data = OBJData()
    with open(file_path, "r") as f:
        all_lines = f.readlines()
    current_mtl_obj = None
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
            if current_mtl_obj is not None:
                current_obj_group = OBJGroup("default")
                obj_data.groups.append(current_obj_group)
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

    all_polygons, all_polygon_fans = [], []
    # now proceed to triangulate the ngons
    for obj_group in obj_data.groups:
        polygons, polygon_fans = obj_group.triangulate(obj_data)
        all_polygons.extend(polygons)
        all_polygon_fans.extend(polygon_fans)
    return all_polygons, all_polygon_fans
