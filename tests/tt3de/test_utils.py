import math
import glm


def perspective_divide(v:glm.vec4):
    return glm.vec3(v.x/v.w,v.y/v.w,v.z/v.w)


def assertPointPrimitiveAlmostEqual(prim0,prim1):
    for key in ['primitive_id','geometry_id','node_id','material_id']:
        assert prim0[key] == prim1[key]
    for key in ['row','col','depth']:
        assert math.isclose(prim0[key],prim1[key],abs_tol=0.001)

def assertLine3DPrimitiveKeyEqual(prim0,prim1):
    for key in ['primitive_id','geometry_id','node_id','material_id']:
        assert prim0[key] == prim1[key]

def assertTriangle3DPrimitiveKeyEqual(prim0,prim1):
    for key in ['primitive_id','geometry_id','node_id','material_id']:
        assert prim0[key] == prim1[key]
def assertPixInfoEqual(pix0,pix1,uv_tol=0.01):
    for key in ['primitive_id','geometry_id','node_id','material_id']:
        assert pix0[key] == pix1[key]
    for key in ['uv','uv_1']:
        assert math.isclose(pix0[key][0],pix1[key][0],abs_tol=uv_tol)
        assert math.isclose(pix0[key][1],pix1[key][1],abs_tol=uv_tol)



def assertPolygon3DEqual(poly0,poly1):
    assert len(poly0) == len(poly1)

    for key in poly0.keys():
        assert poly0[key] == poly1[key]

    