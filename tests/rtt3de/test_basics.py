import unittest


class Test_Material(unittest.TestCase):
    def test_create(self):
        from rtt3de import MyClass
        mc = MyClass()

        as_str = str(mc)
        pass
class Test_GeometryBuffer(unittest.TestCase):
    def test_create(self):
        from rtt3de import GeometryBuffer
        gb = GeometryBuffer()
        as_str = str(gb)


class Test_Small8Drawing(unittest.TestCase):
    def test_create(self):
        from rtt3de import Small8Drawing
        gb = Small8Drawing()
        as_str = str(gb)

        gb.hard_clear(1000.0)

        self.assertEqual(gb.get_at(0,0,0),1000.0)
        self.assertEqual(gb.get_at(0,0,1),1000.0)

        gb.hard_clear(10.0)

        self.assertEqual(gb.get_at(1,1,0),10.0)
        self.assertEqual(gb.get_at(1,1,1),10.0)
        




