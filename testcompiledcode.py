from tt3de.glm.c_triangle_raster import _c_constants
import itertools
import glm

print(_c_constants())



uvmap = glm.mat3x2(glm.vec2(1.0,2.0),glm.vec2(3.0,4.0),glm.vec2(5.0,6.0))

print( list(itertools.chain(*uvmap)) )



uvmap = glm.mat4(2.0)

print( list(itertools.chain(*uvmap)) )


quit()

print()


uvmap = glm.mat3x2(1.0, 2.0,3.0, 4.0,5.0, 6.0)

a = glm.array(glm.packUint4x8(glm.u8vec4(1,2,3,4)))


print(a)
print(a*4)
print(glm.unpackUint4x8(a*4))
#
#v = glm.vec2([1,2])
#a = glm.array(glm.vec2([1,2]))#

#b = a.to_tuple()
#v.to_list()
#print(v.to_list())
#result = somekindoftest()
#print(f"Result: {result}")


#m = glm.mat4(1.0)
#rot = glm.rotate(1,glm.vec3(.2,.2,.2))
#rot = m*rot
#v = glm.vec3(1.0,2.0,3.0)
#screen_info = glm.vec4(0.0,0.0,1.0,1.0)
#
#perspectivematrix = glm.perspective(89,9.0,.01,10)
#r = glm.project(v,m,perspectivematrix,screen_info)
#print(r)

