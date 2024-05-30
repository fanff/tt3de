
from tt3de.asset_load import load_bmp, load_obj, read_file

from tt3de.richtexture import ImageTexture
from tt3de.tt3de import Point2D, Point3D, Triangle3D


def fast_load(obj_file:str,cls=None):
    if obj_file.endswith(".obj"):
        return load_obj(cls,read_file(obj_file))
    elif obj_file.endswith(".bmp"):
        with open(obj_file, 'rb') as fin:
            imgdata = load_bmp(fin)
        
        if cls is None:
            return ImageTexture(imgdata)
        else: 
            return cls(imgdata)

class Prefab2D():

    @staticmethod
    def unitary_triangle(meshclass):
        vertices = [
            Point3D(0, 0, 1.0),
            Point3D(1.0, 0.0, 1.0),
            Point3D(1., 1., 1.0),
        ]
        texture_coords = [
            Point2D(0.0, 0),
            Point2D(1, 0),
            Point2D(1, 1),
        ]
        
        m =meshclass()
        m.elements= [vertices]
        m.uvmap = [texture_coords]
        return m
    
    @staticmethod
    def unitary_square(meshclass):
        vertices = [[
            Point3D(0, 0, 1.0),
            Point3D(1.0, 0.0, 1.0),
            Point3D(1., 1., 1.0),
        ],
        [
            Point3D(0, 0, 1.0),
            Point3D(1., 1., 1.0),
            Point3D(0.0, 1.0, 1.0),
        ]]
        texture_coords = [[
            Point2D(0.0, 0),
            Point2D(1, 0),
            Point2D(1, 1),
        ],
        [
            Point2D(0.0, 0),
            Point2D(1.0, 1.0),
            Point2D(0.0, 1.0),
        ]]
        
        m =meshclass()
        m.elements= vertices
        m.uvmap = texture_coords
        return m

def prefab_mesh_single_triangle(meshcls):
    
    vertices = [
        Point3D(0, 1, 0),
        Point3D(-1, -1, 0),
        Point3D(1, -1, 0),
    ]
    texture_coords = [
        Point2D(0.5, 0),
        Point2D(0, 1),
        Point2D(1, 1),
    ]
    normals = [
        Point3D(0, 0, 1),
        Point3D(0, 0, 1),
        Point3D(0, 0, 1),
    ]
    triangle_vindex = [
        (0, 1, 2)
    ]

    t = Triangle3D(*vertices)

    t = Triangle3D(*vertices)
    t.uvmap= [list(texture_coords)]
    
    triangles=[t]
    m = meshcls()
    m.vertices = vertices
    m.texture_coords[0] = texture_coords
    m.normals = normals
    m.triangles_vindex = triangle_vindex
    m.triangles = triangles
    return m


