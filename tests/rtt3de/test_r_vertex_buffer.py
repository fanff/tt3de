from typing import Dict
import unittest

import glm
from rtt3de import VertexBufferPy,TransformPackPy

class Test_VertexBuffer(unittest.TestCase):
    def test_create(self):
        abuffer = VertexBufferPy()
        trpack = TransformPackPy(232)


        self.assertEqual(abuffer.get_max_content(),128)
        abuffer.set_v3(1,2,3,1)
        self.assertEqual(abuffer.get_v3_t(0),(0,0,0))
        self.assertEqual(abuffer.get_v3_t(1),(1,2,3))
        
        
        self.assertEqual(abuffer.get_v4_t(0),(0,0,0,0))

    def test_add_vertex(self):
        from rtt3de import VertexBufferPy
        import glm
        abuffer = VertexBufferPy()

        self.assertEqual(abuffer.add_vertex(1,2,3),0)
        self.assertEqual(abuffer.add_vertex(1,2,3),1)
        self.assertEqual(abuffer.add_vertex(1,2,3),2)
        self.assertEqual(abuffer.get_vertex_size(),3)

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
        
        trpack.set_view_matrix_glm(glm.mat4(1))

        for i in range(abuffer.get_max_content()):
            abuffer.set_v3(1+i,2+i,3+i,i)

        abuffer.apply_mv(trpack,0,abuffer.get_max_content())
        z = abuffer.get_v4_t(0)
        self.assertEqual(z,(1.0, 2.0, 3.0, 0.0))
        # check conformal with glm calculation :

        res = glm.mat4(1)*glm.mat4(1)*glm.vec4(1,2,3,0)
        self.assertEqual(z,res.to_tuple())

        z = abuffer.get_v4_t(1)
        self.assertEqual(z,(2.0, 3.0, 4.0, 0.0))


class Test_TransformationPack(unittest.TestCase):
    def test_create(self):
        from rtt3de import TransformPackPy
        trpack = TransformPackPy(23)

        
    def test_add_node(self):
        
        transform_buffer = TransformPackPy(128)

        m4 = glm.translate(glm.vec3(1,2,3))

        self.assertEqual(transform_buffer.node_count(),0)
        self.assertEqual(transform_buffer.add_node_transform(m4),0)
        self.assertEqual(transform_buffer.node_count(),1)

        self.assertEqual(transform_buffer.add_node_transform(m4),1)
        self.assertEqual(transform_buffer.node_count(),2)
        transform_buffer.clear()
        self.assertEqual(transform_buffer.node_count(),0)




