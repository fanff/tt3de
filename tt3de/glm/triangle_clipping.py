from typing import List
import glm


def clip_triangle(v1:glm.vec3, v2:glm.vec3, v3:glm.vec3, near_plane:float, original_normal)->List[glm.vec3]:
    def interpolate(p1:glm.vec3, p2:glm.vec3, near_plane:float):
        t = (near_plane - p1.z) / (p2.z - p1.z)
        return p1 + t * (p2 - p1)

    def clip_against_near_plane(triangle:List[glm.vec3], near_plane:float):
        inside_points = []
        outside_points = []

        for point in triangle:
            # this is assuming the far plane is in z +
            if point.z >= near_plane : # near_plane:
                inside_points.append(point)
            else:
                outside_points.append(point)

        if len(inside_points) == 3:
            return triangle  # All points are inside

        if len(inside_points) == 0:
            return []  # All points are outside

        if len(inside_points) == 1 and len(outside_points) == 2:
            p1 = inside_points[0]
            p2 = interpolate(p1, outside_points[0], near_plane)
            p3 = interpolate(p1, outside_points[1], near_plane)

            normal =  calculate_normal(p1, p2, p3)
            if glm.dot(normal, original_normal)>0:
                return [p1, p2, p3]
            else:
                return [ p1, p3, p2 ]

        if len(inside_points) == 2 and len(outside_points) == 1:
            p1, p2 = inside_points
            p3 = interpolate(p1, outside_points[0], near_plane)
            p4 = interpolate(p2, outside_points[0], near_plane)
            
            return [p1, p2, p3, p4]

        return []

    return clip_against_near_plane([v1, v2, v3], near_plane)        

def calculate_normal(v1, v2, v3):
    edge1 = v2 - v1
    edge2 = v3 - v1
    return glm.normalize(glm.cross(edge1, edge2))


def check_winding(triangle, original_normal: glm.vec3) -> bool:
    normal = calculate_normal(triangle[0].position, triangle[1].position, triangle[2].position)
    return glm.dot(normal, original_normal) > 0


def split_quad_to_triangles(v1, v2, v3, v4, original_normal):
    # Return two triangles formed by the quad
    # TODO the return order here is not always the right one.

    # Check the winding order of the triangles and correct if necessary
    corrected_triangles = []
    triangles = [(v1, v2, v3), (v1, v2, v4)]
    for tri in triangles:
        normal = calculate_normal(*tri)
        if glm.dot(normal, original_normal)>0:
            corrected_triangles.append(tri)
        else:
            corrected_triangles.append([tri[0], tri[2], tri[1]])
    return corrected_triangles

def filter_clip_project(v1, v2, apoint3,near_plane:float, m, p, viewport) -> List[tuple[List[glm.vec3], glm.vec3]]:

    # Calculate normal of the original triangle
    normal = calculate_normal(v1, v2, apoint3)

    clipped_points = clip_triangle(v1, v2, apoint3, near_plane, normal)
    clipped_triangles = []
    if len(clipped_points) < 3:
        pass # entirely clipped

    if len(clipped_points) == 4:


        v1_clipped, v2_clipped, v3_clipped, v4_clipped = clipped_points

        
        triangles = split_quad_to_triangles(v1_clipped, v2_clipped, v3_clipped, v4_clipped,normal)


        for tri in triangles:
            pa,pb,pc = tri
            pa = glm.projectZO(pa, m, p, viewport)
            pb = glm.projectZO(pb, m, p, viewport)
            pc = glm.projectZO(pc, m, p, viewport)
            clipped_triangles.append(  ([pa,pb,pc],normal))
            
    if len(clipped_points) == 3:
        # Handle the case where only 3 points are inside (no need to split)

        pa,pb,pc = clipped_points
        pa = glm.projectZO(pa, m, p, viewport)
        pb = glm.projectZO(pb, m, p, viewport)
        pc = glm.projectZO(pc, m, p, viewport)
        clipped_triangles.append(  ([pa,pb,pc],normal))
    return clipped_triangles