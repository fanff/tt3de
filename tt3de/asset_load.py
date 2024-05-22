


import struct
from typing import List, Tuple

def read_file(obj_file):
    with open(obj_file, 'rb') as fin:
        return fin.read()
    

def load_bmp(f):
    def read_bytes(f, num):
        return struct.unpack('<' + 'B' * num, f.read(num))

    def read_int(f):
        return struct.unpack('<I', f.read(4))[0]

    def read_short(f):
        return struct.unpack('<H', f.read(2))[0]

    # Read BMP header
    header_field = read_bytes(f, 2)
    if header_field != (0x42, 0x4D):  # 'BM'
        raise ValueError('Not a BMP file')

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
        raise ValueError('Only 24-bit BMP files are supported')

    # Move to pixel array
    f.seek(pixel_array_offset)

    # Read pixel data
    row_padded = (width * 3 + 3) & ~3  # Row size is padded to the nearest 4-byte boundary
    pixel_data:List[List[int]] = []

    for y in range(height):
        row = []
        for x in range(width):
            b, g, r = read_bytes(f, 3)
            row.append((r, g, b))
        pixel_data.insert(0, row)  # BMP files are bottom to top
        f.read(row_padded - width * 3)  # Skip padding

    return pixel_data
    



def round_to_palette(pixel_data: List[List[Tuple[int, int, int]]], palette: List[Tuple[int, int, int]]) -> List[List[Tuple[int, int, int]]]:
    def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
        return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5

    def find_closest_color(pixel: Tuple[int, int, int], palette: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        return min(palette, key=lambda color: color_distance(pixel, color))

    rounded_pixel_data = []
    for row in pixel_data:
        rounded_row = [find_closest_color(pixel, palette) for pixel in row]
        rounded_pixel_data.append(rounded_row)
    
    return rounded_pixel_data


def extract_palette(pixel_data: List[List[Tuple[int, int, int]]]) -> List[Tuple[int, int, int]]:
    unique_colors = set()
    for row in pixel_data:
        for pixel in row:
            unique_colors.add(pixel)
    return list(unique_colors)



def load_palette(filename):
    return extract_palette(load_bmp(filename))

        