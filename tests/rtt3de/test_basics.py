import unittest


class Test_Material(unittest.TestCase):
    def test_create(self):
        from rtt3de import MyClass
        mc = MyClass()

        as_str = str(mc)
        pass
        mc+mc
