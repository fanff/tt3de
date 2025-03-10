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

        Args:
            max_size (int): The maximum number of textures that can be stored.
        """
        ...

    def add_texture(
        self,
        image_width: int,
        image_height: int,
        chained_data: bytes,
        repeat_width: bool,
        repeat_height: bool,
    ) -> int:
        """
        Adds a texture to the buffer.

        Args:
            image_width (int): The width of the image.
            image_height (int): The height of the image.
            chained_data (bytes): The image data.
            repeat_width (bool): Whether to repeat the texture horizontally.
            repeat_height (bool): Whether to repeat the texture vertically.

        Returns:
            int: The index of the texture.
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
