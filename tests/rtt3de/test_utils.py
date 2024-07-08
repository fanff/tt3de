import math
import glm


def perspective_divide(v:glm.vec4):
    return glm.vec3(v.x/v.w,v.y/v.w,v.z/v.w)


def assertPointPrimitiveAlmostEqual(prim0,prim1):
    for key in ['primitive_id','geometry_id','node_id','material_id']:
        assert prim0[key] == prim1[key]
    for key in ['row','col','depth']:
        assert math.isclose(prim0[key],prim1[key],abs_tol=0.001)

        