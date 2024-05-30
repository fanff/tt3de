from setuptools import Extension, setup
from Cython.Build import cythonize
from Cython.Compiler import Options
import glm


# messing around with extensions.
#extensions = [
#    Extension("texture2d", ["tt3de/glm/Texture2D.pyx"]),
#    Extension("c_triangle_raster", ["tt3de/glm/c_triangle_raster.pyx"], include_dirs=["tt3de/glm/",".","tt3de/"]),
#]


setup(
    ext_modules = cythonize(["tt3de/glm/c_texture.pyx","tt3de/glm/c_triangle_raster.pyx"],
                            compiler_directives={'boundscheck': True,
                                                 'embedsignature':True}),

)
