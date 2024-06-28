from typing import Dict
import unittest


class Test_Material(unittest.TestCase):
    def test_create(self):
        raise Exception("not done")
class Test_GeometryBuffer(unittest.TestCase):
    def test_create(self):
        from rtt3de import GeometryBufferPy
        gb = GeometryBufferPy()
        as_str = str(gb)
class Test_VertexBuffer(unittest.TestCase):
    def test_create(self):
        from rtt3de import VertexBufferPy,TransformPackPy
        abuffer = VertexBufferPy()
        trpack = TransformPackPy()
        self.assertEqual(abuffer.get_max_content(),128)
        abuffer.set_v3(1,2,3,1)
        self.assertEqual(abuffer.get_v3_t(0),(0,0,0))
        self.assertEqual(abuffer.get_v3_t(1),(1,2,3))
        
        
        self.assertEqual(abuffer.get_v4_t(0),(0,0,0,0))


    def test_multmv(self):
        from rtt3de import VertexBufferPy,TransformPackPy
        import glm

        abuffer = VertexBufferPy()
        trpack = TransformPackPy()
        
        trpack.set_model_matrix_glm(glm.mat4(1))
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
        trpack = TransformPackPy()

        
        inmat = [1.0]*16
        trpack.set_model_matrix(inmat)
        out = trpack.get_model_matrix_tuple()
        self.assertEqual(tuple(inmat),out)

        



    def test_set_glm_aslist(self):
        from rtt3de import TransformPackPy
        import glm
        import itertools
        trpack = TransformPackPy()
        m4 = glm.translate(glm.vec3(1,2,3))

        m4list = m4.to_list()
        as_list = list(itertools.chain(*m4.to_list()))
        trpack.set_model_matrix(as_list)
        as_tuple = tuple(as_list)
        out = trpack.get_model_matrix_tuple()

        self.assertEqual(as_tuple,out)
    def test_set_glm_as_tuple_rust(self):
        from rtt3de import TransformPackPy
        import glm
        import itertools
        trpack = TransformPackPy()

        # make a glm matrix
        m4 = glm.translate(glm.vec3(1,2,3))
        m4_as_tuple = tuple(list(itertools.chain(*m4.to_list())))
        m4.to_tuple()
        # give the matrix 
        trpack.set_model_matrix_glm(m4)


        # check result
        out = trpack.get_model_matrix_tuple()
        self.assertEqual(m4_as_tuple,out)

