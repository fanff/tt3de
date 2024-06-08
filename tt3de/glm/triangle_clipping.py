from typing import List, Tuple
import glm

"""

some usefull ressources related 
http://tfpsly.free.fr/Docs/TomHammersley/frustum.htm
https://graphicscompendium.com/opengl/24-clipping-culling
"""

Triangle = Tuple[glm.vec4, glm.vec4, glm.vec4]
Polygon = List[glm.vec4]


def is_front_facing(triangle:Triangle):
    v0, v1, v2 = triangle
    edge1 = glm.vec3(v1) - glm.vec3(v0)
    edge2 = glm.vec3(v2) - glm.vec3(v0)
    normal = glm.cross(edge1, edge2)
    return normal.z > 0

def calculate_normal(triangle: Triangle)->glm.vec3:
    v0, v1, v2 = triangle
    return glm.normalize(glm.cross(glm.vec3(v1) - glm.vec3(v0), glm.vec3(v2) - glm.vec3(v0)))

def inside(plane:glm.vec4, point:glm.vec4)->bool:
    """tell if a point is inside a plane;  """
    return glm.dot(plane.xyz, point.xyz) + plane.w > 0


def inside_planes(planes:List[glm.vec4], point:glm.vec4)->bool:
    """tell if a point is inside a plane;  """
    return [inside(plane,point) for plane in planes]



def clipping_space_planes() -> List[glm.vec4]:
    """
    Returns the clipping planes for a ZO (Zero One) projection.
    x and y ranging from -1 to 1
    z ranging from 0 to 1


    
    Returns:
        List[glm.vec4]: A list of planes defined by glm.vec4, each representing a plane in the format (A, B, C, D)
    """
    planes = [
        glm.vec4(1, 0, 0, 1),    # Left   plane: x = -1   ->  1*x + 0*y + 0*z + 1 = 0
        glm.vec4(-1, 0, 0, 1),   # Right  plane: x = 1    -> -1*x + 0*y + 0*z + 1 = 0
        glm.vec4(0, 1, 0, 1),    # Bottom plane: y = -1   ->  0*x + 1*y + 0*z + 1 = 0
        glm.vec4(0, -1, 0, 1),   # Top    plane: y = 1    ->  0*x - 1*y + 0*z + 1 = 0
        glm.vec4(0, 0, 1, 0),    # Near   plane: z = 0    ->  0*x + 0*y + 1*z + 0 = 0
        glm.vec4(0, 0, -1, 1)    # Far    plane: z = 1    ->  0*x + 0*y - 1*z + 1 = 0
    ]
    return planes


def clipping_space_planes_NO() -> List[glm.vec4]:
    """
    Returns the clipping planes for a ZO (Zero One) projection.
    x and y ranging from -1 to 1
    z ranging from -1 to 1


    
    Returns:
        List[glm.vec4]: A list of planes defined by glm.vec4, each representing a plane in the format (A, B, C, D)
    """
    planes = [
        glm.vec4(1, 0, 0, 1),   # Left plane: x = -1
        glm.vec4(-1, 0, 0, 1),  # Right plane: x = 1
        glm.vec4(0, 1, 0, 1),   # Bottom plane: y = -1
        glm.vec4(0, -1, 0, 1),  # Top plane: y = 1
        glm.vec4(0, 0, 1, 1),   # Near plane: z = -1
        glm.vec4(0, 0, -1, 1)   # Far plane: z = 1
    ]
    
    return planes



def intersect(plane:glm.vec4, p1:glm.vec4, p2:glm.vec4)->glm.vec4:
    """Calculate the intersection point of a plane with a line segment .
    
        Args:
            plane: A glm.vec4 representing the plane equation in the form (a, b, c, d).
            p1: A glm.vec4 representing the starting point of the line segment.
            p2: A glm.vec4 representing the ending point of the line segment.
    
        Returns:
            A glm.vec4 representing the intersection point of the plane with the line segment.
    """
    #d1 = glm.dot(plane.xyz, p1.xyz) + plane.w
    #d2 = glm.dot(plane.xyz, p2.xyz) + plane.w
    #t = d1 / (d1 - d2)
    #return p1 + t * (p2 - p1)

    # Extract the plane coefficients
    a, b, c, d = plane.x, plane.y, plane.z, plane.w
    
    # Calculate the direction vector of the line segment
    direction = p2 - p1
    
    # Calculate the denominator of the parameter t
    denominator = a * direction.x + b * direction.y + c * direction.z
    
    if denominator == 0:
        # The line segment is parallel to the plane (no intersection or infinite intersections)
        return None
    
    # Calculate the numerator of the parameter t
    numerator = -(a * p1.x + b * p1.y + c * p1.z + d)
    
    # Calculate the parameter t
    t = numerator / denominator
    
    # Calculate the intersection point
    intersection = p1 + t * direction
    
    return glm.vec4(intersection.x, intersection.y, intersection.z, 1.0)



def clip_polygon_against_plane(plane:glm.vec4, polygon:Polygon):
    """Clip a polygon against a plane using 
    
    Args:
        plane (glm.vec4): The plane to clip the polygon against.
        polygon (Polygon): The polygon to be clipped.
    
    Returns:
        list: A list of points representing the clipped polygon.
    """
    clipped_polygon = []
    for i in range(len(polygon)):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]
        
        if inside(plane, p2):
            if not inside(plane, p1):
                clipped_polygon.append(intersect(plane, p1, p2))
            clipped_polygon.append(p2)
        elif inside(plane, p1):
            clipped_polygon.append(intersect(plane, p1, p2))
    
    return clipped_polygon

def check_if_triangle_in_planes_volume(triangle:Triangle,planes:list[glm.vec4]):
    p0_inclusion = inside_planes(planes,triangle[0])
    p1_inclusion = inside_planes(planes,triangle[1])
    p3_inclusion = inside_planes(planes,triangle[2])

    return (p0_inclusion,
            p1_inclusion,
            p3_inclusion)


def clip_triangle_in_planes(triangle, planes)->list[Triangle]:
    """Clip a triangle against a list of planes.
    Sutherland-Hodgman polygon clipping algorithm.
    Args:
        triangle (list): List of 3 points representing the triangle.
        planes (list): List of planes to clip the triangle against.
    
    Returns:
        list: List of triangles resulting from clipping the input triangle against the planes.
    """
    polygon = list(triangle)
    for plane in planes:
        polygon = clip_polygon_against_plane(plane, polygon)
        if len(polygon) < 3:
            return []
    
    triangles = []
    if len(polygon) >= 3:
        for i in range(1, len(polygon) - 1):
            triangles.append(((polygon[0], polygon[i], polygon[i + 1])))
    
    return triangles

def correct_winding(triangle: Triangle) -> Triangle:
    """reverse the triangle to be negative"""
    if not is_front_facing(triangle):
        v0, v1, v2 = triangle
        return (v0, v2, v1)
    return triangle

def triangulate_polygon(polygon:List[glm.vec4]) -> List[Triangle]:
    """return a list of triangles from the list of points, assuming a faning technique 
    """
    # Use fan triangulation method
    triangles = []
    if len(polygon) < 3:
        return triangles

    for i in range(1, len(polygon) - 1):
        triangles.append([polygon[0], polygon[i], polygon[i + 1]])
    
    return triangles




PLANE_LEFT = 0
PLANE_RIGHT = 1
PLANE_BOTTOM = 2
PLANE_TOP = 3
PLANE_NEAR = 4
PLANE_FAR = 5

def extract_planes(projection_matrix: glm.mat4):
    """
    
    In GLM, matrices are in column-major order, 
    meaning projection_matrix[i] accesses
      the i-th column, not the row
    
      to deal with this we transpose the input and extract from it 
    """
    # left_plane
    # right_plane
    # bottom_plane
    # top_plane
    # near_plane
    # far_plane

    projection_matrix_T = glm.transpose(projection_matrix)


    planes = []
    planes.append(projection_matrix_T[3] + projection_matrix_T[0])  # Left
    planes.append(projection_matrix_T[3] - projection_matrix_T[0])  # Right
    planes.append(projection_matrix_T[3] + projection_matrix_T[1])  # Bottom
    planes.append(projection_matrix_T[3] - projection_matrix_T[1])  # Top
    planes.append(projection_matrix_T[3] + projection_matrix_T[2])  # Near
    planes.append(projection_matrix_T[3] - projection_matrix_T[2])  # Far
    return planes
    
    