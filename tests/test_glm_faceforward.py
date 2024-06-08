import math
from typing import List
import unittest

import glm

from context import tt3de

from tt3de.glm.triangle_clipping import calculate_normal, clip_triangle, split_quad_to_triangles
from tt3de.tt3de import Camera, FPSCamera, Point3D, PointElem


from PIL import Image, ImageDraw


class TestFaceforward(unittest.TestCase):

    def test_many(self):
        
        n = glm.vec3(1.1,2.2,3.3)

        for i in range(100):
            import random
            Nref = glm.vec3(0,0,1) 
            n = glm.vec3(random.random()-.5,random.random()-.5,random.random()-.5)
            #Ivec = glm.vec3(random.random()-.5,random.random()-.5,random.random()-.5)
            Ivec = glm.vec3(.4,-.5,.5)

            result = glm.faceforward(n,Ivec,Nref)

            #print(n,result)
    def test_matrix_triangle(self):
        #https://computergraphics.stackexchange.com/questions/9537/how-does-graphics-api-like-opengl-determine-which-triangle-is-back-face-to-cull


        mat = glm.mat3(1,2,3,4,5,6,7,8,9)
        print(mat)

        mat = glm.mat3(glm.vec3(.5,0,78),glm.vec3(-1,1,100),glm.vec3(1,1,111))
        print(mat)
        mat_det = glm.determinant(mat)
        print(mat_det)

    def test_project_stuff(self):
        

        viewport = glm.vec4(0,0,1,1.0)
        v = glm.lookAt(glm.vec3(0,0,0),glm.vec3(0,0,1),glm.vec3(0,1,0))

        p = glm.perspectiveFovZO(math.radians(90),400,400,1.0,100.0)
        m = glm.mat4(1.0)

        apoint4 = glm.vec4(0,0,5,1)

        for pz in [-20,-5,-2,-1,1,2,5,20]:
            apoint3 = glm.vec3(1.0,0.0,pz)
            pp3 = glm.projectZO(apoint3, m*v,p,viewport)
            # afaik https://github.com/g-truc/glm/blob/master/glm/ext/matrix_projection.inl 
            # the glm project function are doing the /wi  internally. 
            
            print(f"{apoint3} -> {pp3} ()")
        1/0



    def test_triangle_clipping_project(self):
        v = glm.lookAt(glm.vec3(0,0,0),glm.vec3(0,0,1),glm.vec3(0,1,0))
        near_plane = 0.01

        

        #standart view port 
        viewport = glm.vec4(0,0,1,1.0)
        #standart perspective with near and far plane
        p = glm.perspectiveFovZO(math.radians(90),400,400,near_plane,100.0)
        
        m = glm.mat4(1.0)

        for pzidx,pz in enumerate(range(-10,40)):
            v1      = glm.vec3( 2,  -2,   .5*pz-10.1)
            v2      = glm.vec3(-2,  -2,   .5*pz-10.1)
            apoint3 = glm.vec3( 0.0,-2.0, .5*pz+.1)
            #tridet = glm.determinant(glm.mat3x3(v1,v2,apoint3))
            tri_dot = glm.dot( calculate_normal(v1,v2,apoint3) , glm.vec3(0,0,1) )

            triangle_to_draw = filter_clip(v1,v2,apoint3,near_plane+0.1,m,p,viewport)


                #for point in clipped_points:
                #    pp = glm.projectZO(point, m, p, viewport)
                #    print(f"Projected point: {pp}, Normal: {normal}")

            # siooome debug stuff
                
            pil_output_width, pil_output_height = 400, 400
            image = Image.new("RGB", (pil_output_width, pil_output_height), "white")
            draw = ImageDraw.Draw(image)

            print(f"{pzidx} triangle count : {len(triangle_to_draw)}")
            # Define the triangle vertices
            for tri,normal in triangle_to_draw:
                pp1_scaled_pil,pp2_scaled_pil,pp3_scaled_pil   = tri
                pp1_scaled_pil = pp1_scaled_pil*glm.vec3(pil_output_width,pil_output_height,1.0)
                pp2_scaled_pil = pp2_scaled_pil*glm.vec3(pil_output_width,pil_output_height,1.0)
                pp3_scaled_pil = pp3_scaled_pil*glm.vec3(pil_output_width,pil_output_height,1.0)


                triangle = [tuple(pp1_scaled_pil.xy),
                            tuple(pp2_scaled_pil.xy),
                            tuple(pp3_scaled_pil.xy)]  

                # Draw the triangle
                draw.polygon(triangle, outline="black", fill=False)
            #pp3_modified = pp3
            #if pp3.z>1.0 :
            #    if pp3.y<.5:
            #        pp3_modified.y = 1.0+ 1.0/(abs(pp3.z)-1.0)
            #
            #        pp3_modified_scaled_pil = pp3_modified*400
            #        triangle = [tuple(pp1_scaled_pil.xy),
            #                    tuple(pp2_scaled_pil.xy),
            #                    tuple(pp3_modified_scaled_pil.xy)]  #
            #        print(f"modified, to {pp3_modified.y}")
            #        # Draw the triangle
            #        draw.polygon(triangle, outline="red", fill="red")
            
            image.save(f"tu_clip_{pzidx}.png")
        1/0


    def test_project_inf_perspective(self):

        viewport = glm.vec4(0,0,1,1.0)
        v = glm.lookAt(glm.vec3(0,0,0),glm.vec3(0,0,1),glm.vec3(0,1,0))

        p = glm.infinitePerspective(math.radians(60),16.0/9.0,1.0)
        m = glm.mat4(1.0)

        apoint4 = glm.vec4(0,0,5,1)

        for pz in [-40,-20,-5,-2,-1,1,2,5,20,40]:
            apoint3 = glm.vec3(0,1.0,pz)
            apoint4 = glm.vec4(0,0,pz,1.0)
            pp3 = glm.project(apoint3, m*v,p,viewport)
            # afaik https://github.com/g-truc/glm/blob/master/glm/ext/matrix_projection.inl 
            # the glm project function are doing the /wi  internally. 

            print(f"{apoint3} -> {pp3}")
            #pp4=m*v*p*apoint4 
            #print(pp4)
        1/0


if __name__ == "__main__":
    unittest.main()
