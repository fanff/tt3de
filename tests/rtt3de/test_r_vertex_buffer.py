from typing import Dict
import unittest

import glm
from rtt3de import VertexBufferPy,TransformPackPy

class Test_VertexBuffer(unittest.TestCase):
    def test_create(self):
        abuffer = VertexBufferPy()
        trpack = TransformPackPy(232)


        self.assertEqual(abuffer.get_max_content(),128)
        abuffer.add_vertex(1,2,3)
        self.assertEqual(abuffer.get_vertex(0),(1.0,2.0,3.0,1.0))

    def test_add_vertex(self):
        from rtt3de import VertexBufferPy
        import glm
        abuffer = VertexBufferPy()

        self.assertEqual(abuffer.add_vertex(1,2,3),0)
        self.assertEqual(abuffer.add_vertex(12,22,32),1)
        self.assertEqual(abuffer.add_vertex(11,21,31),2)
        self.assertEqual(abuffer.get_vertex_size(),3)

        self.assertEqual(abuffer.get_vertex(0),(1.0,2.0,3.0,1.0))
        self.assertEqual(abuffer.get_vertex(1),(12.0,22.0,32.0,1.0))
        self.assertEqual(abuffer.get_vertex(2),(11.0,21.0,31.0,1.0))

    def test_add_uv(self):
        from rtt3de import VertexBufferPy
        import glm
        abuffer = VertexBufferPy()

        self.assertEqual(abuffer.get_uv_size(),0)
        retidex = abuffer.add_uv(glm.vec2(1.0,1.5),glm.vec2(2.0,2.5),glm.vec2(3.0,3.5))
        self.assertEqual(retidex,0)
        self.assertEqual(abuffer.get_uv_size(),1)

        ret1 = abuffer.add_uv(glm.vec2(1.1,1.1),glm.vec2(2.1,2.1),glm.vec2(3.1,3.1))
        self.assertEqual(ret1,1)
        self.assertEqual(abuffer.get_uv_size(),2)

        self.assertEqual(abuffer.get_uv(0),(
            (1.0,1.5),
            (2.0,2.5),
            (3.0,3.5)
        )
        
        )
        # self.assertEqual(abuffer.get_uv(1),(
        #     (1.1,1.1),
        #     (2.1,2.1),
        #     (3.1,3.1)
        # )
        # 
        # )


    def test_multmv(self):
        from rtt3de import VertexBufferPy,TransformPackPy
        import glm

        abuffer = VertexBufferPy()
        trpack = TransformPackPy(23)
        
        trpack.add_node_transform(glm.translate(glm.vec3(1,2,3)))

        
        trpack.set_view_matrix_glm(glm.identity(glm.mat4))

        for i in range(abuffer.get_max_content()):
            abuffer.add_vertex(1+i,2+i,3+i)

        abuffer.apply_mv(trpack,0,0,abuffer.get_max_content())


        z = abuffer.get_vertex(0)
        self.assertEqual(z,(1.0, 2.0, 3.0, 1.0))

        z = abuffer.get_vertex(1)
        self.assertEqual(z,(2.0, 3.0, 4.0, 1.0))


        z0_mv = abuffer.get_world_space_vertex(0)
        self.assertEqual(z0_mv,(2.0, 4.0, 6.0, 1.0)) # translated
        # check conformal with glm calculation :
        res = glm.translate(glm.vec3(1,2,3))*glm.mat4(1)*glm.vec4(1,2,3,1)
        self.assertEqual(z0_mv,res.to_tuple())