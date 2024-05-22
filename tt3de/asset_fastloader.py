
from tt3de.asset_load import load_bmp, read_file
from tt3de.pyglmtexture import GLMMesh3D
from tt3de.richtexture import ImageTexture


def fast_load(obj_file:str,cls=None):
    if obj_file.endswith(".obj"):
        return cls.from_obj_bytes(read_file(obj_file))
    elif obj_file.endswith(".bmp"):
        with open(obj_file, 'rb') as fin:
            return ImageTexture(load_bmp(fin))