from ast import List
from typing import Dict, Tuple
from pyglm import glm

from tt3de.tt3de.materials import (
    BaseTexturePy,
    StaticColorPy,
)

def get_glyph_set() -> str:
    """
    Returns the static glyph set as a string.

    Returns:
        str: The static glyph set.
    """
    ...

def find_glyph_indices_py(input: str) -> int:
    """
    Finds the glyph index for the given character.

    Args:
        input (str): A single character for which to find the glyph index.

    Returns:
        int: The glyph index.
    """
    ...

class TextureBufferPy:
    def __init__(self, max_size: int):
        """
        Initializes the texture buffer.
        Each Texture must be within self.max_texture_size size.

        Args:
            max_size (int): The maximum number of textures that can be stored.
        """
        self.max_texture_size = max_size
        ...

    def add_texture(
        self,
        image_width: int,
        image_height: int,
        chained_data: List[int],
        repeat_width: bool,
        repeat_height: bool,
    ) -> int:
        """
        Adds a texture to the buffer.

        Args:
            image_width (int): The width of the image.
            image_height (int): The height of the image.
            chained_data (List[int]): The image data.
            repeat_width (bool): Whether to repeat the texture horizontally.
            repeat_height (bool): Whether to repeat the texture vertically.

        Returns:
            int: The index of the texture.
        """
        ...

    def add_atlas_texture_from_iter(
        self,
        width: int,
        height: int,
        pixels: List[int],
        pix_size_width: int,
        pix_size_height: int,
    ) -> int:
        """
        Adds an atlas texture from an iterator of pixels.

        Args:
            width (int): The width of the atlas texture.
            height (int): The height of the atlas texture.
            pixels (List[int]): The pixel data.
            pix_size_width (int): The width of each pixel.
            pix_size_height (int): The height of each pixel.
        """
        ...

    def get_rgba_at(
        self, texture_idx: int, u: float, v: float
    ) -> Tuple[int, int, int, int]:
        """
        Fetches the RGBA value at the given UV coordinates for a specific texture.

        Args:
            texture_idx (int): The index of the texture.
            u (float): The U coordinate (0.0 to 1.0).
            v (float): The V coordinate (0.0 to 1.0).
        Returns:
            Tuple[int, int, int, int]: The RGBA value as a tuple.
        """
        ...

class MaterialBufferPy:
    def __init__(self, max_size=64):
        """
        Initializes the material buffer.
        Args:
            max_size (int): The maximum number of materials that can be stored.
        """
        ...

    def add_static_color(
        self,
        mat: StaticColorPy,
    ) -> int:
        """
        Adds a static color material to the buffer.

        Args:
            mat (StaticColorPy): The static color material to add.

        Returns:
            int: The index of the material.
        """
        ...

    def add_base_texture(
        self,
        mat: BaseTexturePy,
    ) -> int:
        """
        Adds a base texture material to the buffer.

        Args:
            mat (BaseTexturePy): The base texture material to add.

        Returns:
            int: The index of the material.
        """
        ...

    def add_textured(self, albedo_texture_idx: int, glyph_idx: int) -> int:
        """
        Adds a textured material to the buffer.

        Args:
            albedo_texture_idx (int): The index of the albedo texture.
            glyph_idx (int): The glyph index.

        Returns:
            int: The index of the material.
        """
        ...

class GeometryBufferPy:
    def __init__(self, max_size=64):
        """
        Initializes the geometry buffer.

        Args:
            max_size (int): The maximum number of geometries that can be stored.
        """
        ...

    def get_element(self, idx: int) -> dict:
        """
        Fetches a geometry element at the given index.

        Args:
            idx (int): The index of the geometry element to fetch.

        Returns:
            dict: A dictionary representing the geometry element.
        """
        ...

    def geometry_count(self) -> int:
        """
        Returns:
            int: The current number of geometries stored.
        """
        ...

    def add_points_2d(
        self,
        p_start: int,
        point_count: int,
        uv_idx: int,
        node_id: int,
        material_id: int,
    ) -> int:
        """
        Adds 2D points geometry to the buffer.
        Args:
            p_start (int): The starting point index.
            point_count (int): The number of points.
            uv_idx (int): The UV index.
            node_id (int): The node ID.
            material_id (int): The material ID.
        """
        ...

    def add_line2d(
        self,
        p_start: int,
        point_count: int,
        uv_idx: int,
        node_id: int,
        material_id: int,
    ) -> int:
        """
        Adds a 2D line geometry to the buffer.

        """
        ...

    def add_rect2d(
        self,
        p_start: int,
        uv_start_index: int,
        node_id: int,
        material_id: int,
    ) -> int:
        """
        Adds a 2D rectangle geometry to the buffer.
        Args:
            p_start (int): The starting point index.
            uv_start_index (int): The starting UV index.
            node_id (int): The node ID.
            material_id (int): The material ID.
        """
        ...

    def add_polygon2d(
        self,
        p_start: int,
        triangle_count: int,
        node_id: int,
        material_id: int,
        uv_start: int,
    ) -> int:
        """
        Adds polygon2d geometry to the buffer.
        Args:
            p_start (int): The starting point index.
            triangle_count (int): The number of triangles.
            node_id (int): The node ID.
            material_id (int): The material ID.
            uv_start (int): The starting UV index.
        """
        ...

class VertexBufferPy:
    def __init__(self, max_vertex_size=1024, max_uv_size=1024, max_vertex_2d_size=1024):
        """
        Initializes the vertex buffer.

        Args:
            max_vertex_size (int): The maximum number of 3D vertices that can be stored.
            max_uv_size (int): The maximum number of UV sets that can be stored.
            max_vertex_2d_size (int): The maximum number of 2D vertices that can be stored.
        """
        ...

    def add_2d_vertex(self, x: float, y: float, z: float) -> int:
        """
        Adds a 2D vertex to the buffer.

        Args:
            x (float): The x-coordinate of the vertex.
            y (float): The y-coordinate of the vertex.
            z (float): The z-coordinate of the vertex.

        Returns:
            int: The index of the newly added vertex.
        """
        ...

    def get_2d_vertex_tuple(self, idx: int) -> tuple:
        """
        Fetches a 2D vertex at the given index.

        Args:
            idx (int): The index of the vertex to fetch.

        Returns:
            tuple: A tuple representing the vertex (x, y, z, w).
        """
        ...

    def get_2d_calculated_tuple(self, idx: int) -> tuple:
        """
        Fetches a 2D vertex in clip space at the given index.

        Args:
            idx (int): The index of the vertex to fetch.
        Returns:

            tuple: A tuple representing the clip space vertex (x, y, z, w).
        """
        ...

    def add_3d_vertex(self, x: float, y: float, z: float) -> int:
        """
        Adds a 3D vertex to the buffer.

        Args:
            x (float): The x-coordinate of the vertex.
            y (float): The y-coordinate of the vertex.
            z (float): The z-coordinate of the vertex.

        Returns:
            int: The index of the newly added vertex.
        """
        ...

    def get_3d_capacity(self) -> int:
        """
        Returns:
            int: The maximum number of 3D vertices that can be stored.
        """
        ...

    def get_3d_len(self) -> int:
        """
        Returns:
            int: The current number of 3D vertices stored.
        """
        ...

    def get_2d_capacity(self) -> int:
        """
        Returns:
            int: The maximum number of 2D vertices that can be stored.
        """
        ...

    def get_2d_len(self) -> int:
        """
        Returns:
            int: The current number of 2D vertices stored.
        """
        ...

    def get_uv_size(self) -> int:
        """
        Returns:
            int: The current number of UV sets stored.
        """
        ...

    def get_3d_vertex_tuple(self, idx: int) -> tuple:
        """
        Fetches a vertex at the given index.

        Args:
            idx (int): The index of the vertex to fetch.

        Returns:
            tuple: A tuple representing the vertex (x, y, z, w).
        """
        ...

    def get_3d_calculated_tuple(self, idx: int) -> tuple:
        """
        Fetches a vertex in clip space at the given index.

        Args:
            idx (int): The index of the vertex to fetch.
        Returns:
            tuple: A tuple representing the clip space vertex (x, y, z, w).
        """
        ...

    def add_uv(
        self,
        uv0: glm.vec2,
        uv1: glm.vec2,
        uv2: glm.vec2,
    ) -> int:
        """
        Adds a UV set to the buffer.

        Args:
            uv0 (glm.vec2): The first UV coordinate.
            uv1 (glm.vec2): The second UV coordinate.
            uv2 (glm.vec2): The third UV coordinate.

        Returns:
            int: The index of the newly added UV set.
        """
        ...

    def add_3d_triangle(
        self,
        v0: int,
        v1: int,
        v2: int,
        uva: glm.vec2,
        uvb: glm.vec2,
        uvc: glm.vec2,
        normal: glm.vec3,
    ) -> Tuple[int, int]:
        """
        Adds a 3D triangle to the buffer.

        Args:
            v0 (int): The index of the first vertex.
            v1 (int): The index of the second vertex.
            v2 (int): The index of the third vertex.
            uva (glm.vec2): The UV coordinate for the first vertex.
            uvb (glm.vec2): The UV coordinate for the second vertex.
            uvc (glm.vec2): The UV coordinate for the third vertex.
            normal (glm.vec3): The normal vector for the triangle.

        Returns:
            (int, int): A tuple containing the UV index and triangle index.
        """
        ...

class TransformPackPy:
    def __init__(self, max_size=64):
        """
        Initializes the transform pack.

        Args:
            max_size (int): The maximum number of transforms that can be stored.
        """
        ...

    def clear(self) -> None:
        """
        Remove all stored node transforms.
        """
        ...

    def node_count(self) -> int:
        """
        Returns:
            int: The current number of stored node transforms.
        """
        ...

    def add_node_transform(self, value: glm.mat4) -> int:
        """
        Append a node transform.

        Args:
            value (glm.mat4): A 4x4 transform matrix (flat 16-length or 4x4 nested).

        Returns:
            int: The index of the newly added node.
        """
        ...

    def set_node_transform(self, idx: int, value: glm.mat4) -> None:
        """
        Overwrite a node transform at a given index.

        Args:
            idx (int): The node index to set.
            value (glm.mat4): A 4x4 transform matrix (flat 16-length or 4x4 nested).
        """
        ...

    def get_node_transform(self, idx: int) -> glm.mat4:
        """
        Fetch a node transform.

        Args:
            idx (int): The node index to read.

        Returns:
            glm.mat4: A 4x4 transform matrix.
        """
        ...

    def set_view_matrix_glm(self, value: glm.mat4) -> None:
        """
        Set the 2D view matrix.

        Args:
            value (Mat4Like): A 4x4 view matrix.
        """
        ...

    def get_view_matrix(self) -> glm.mat4:
        """
        Get the 2D view matrix.

        Returns:
            glm.mat4: The current 4x4 view matrix (typically a flat 16-length list).
        """
        ...

    def set_view_matrix_3d(self, value: glm.mat4) -> None:
        """
        Set the 3D view matrix.

        Args:
            value (glm.mat4): A 4x4 view matrix.
        """
        ...

    def get_view_matrix_3d(self) -> glm.mat4:
        """
        Get the 3D view matrix.

        Returns:
            glm.mat4: The current 4x4 3D view matrix (typically a flat 16-length list).
        """
        ...

    def set_projection_matrix(self, value: glm.mat4) -> None:
        """
        Set the 3D projection matrix.

        Args:
            value (glm.mat4): A 4x4 projection matrix.
        """
        ...

    def get_projection_matrix(self) -> glm.mat4:
        """
        Get the 3D projection matrix.

        Returns:
            glm.mat4: The current 4x4 projection matrix (typically a flat 16-length list).
        """
        ...

class DrawingBufferPy:
    def __init__(
        self, max_row: int, max_col: int, flip_x: bool = False, flip_y: bool = False
    ):
        """
        Initializes the drawing buffer.

        Args:
            max_row (int): The maximum number of rows.
            max_col (int): The maximum number of columns.
        """
        ...

    def set_depth_content(
        self,
        row: int,
        col: int,
        normal: glm.vec3,
        depth: float,
        uv0: glm.vec2,
        uv1: glm.vec2,
        node_id: int,
        geom_id: int,
        material_id: int,
        primitive_id: int,
    ) -> None:
        """
        Sets the depth content for a specific cell in the drawing buffer.
        Args:
            row (int): The row index.
            col (int): The column index.
            normal (glm.vec3): The normal vector.
            depth (float): The depth value.
            uv0 (glm.vec2): The first UV coordinate.
            uv1 (glm.vec2): The second UV coordinate.
            node_id (int): The node ID.
            geom_id (int): The geometry ID.
            material_id (int): The material ID.
            primitive_id (int): The primitive ID.
        """
        ...

class PrimitiveBufferPy:
    def __init__(self, max_size=64):
        """
        Initializes the primitive buffer.

        Args:
            max_size (int): The maximum number of primitives that can be stored.
        """
        ...

    def primitive_count(self) -> int:
        """
        Returns:
            int: The current number of primitives stored.
        """
        ...

    def clear(self) -> None:
        """
        Clears all stored primitives.
        """
        ...

    def get_all_as_dicts(self) -> List[Dict]:
        """
        Fetches all primitives as a list of dictionaries.

        Returns:
            list: A list of dictionaries representing the primitives.
        """
        ...

    def get_primitive(self, idx: int) -> dict:
        """
        Fetches a primitive at the given index.

        Args:
            idx (int): The index of the primitive to fetch.

        Returns:
            dict: A dictionary representing the primitive.
        """
        ...

def build_primitives_py(
    geometry_buffer: GeometryBufferPy,
    vertex_buffer: VertexBufferPy,
    transform_buffer: TransformPackPy,
    dbpy: DrawingBufferPy,
    primitive_buffer: PrimitiveBufferPy,
) -> None:
    """
    Builds primitives from the geometry buffer into the primitive buffer.
    """
    ...

def ttsl_run(*args) -> Tuple[glm.vec3, glm.vec3, int]:
    """
    Runs the TTSL bytecode with the provided registers.

    Args:
        *args: The registers and bytecode to run.

    Returns:
        Tuple[glm.vec3, glm.vec3, int]: A tuple containing the front vector, back vector, and glyph index.
    """
    ...
