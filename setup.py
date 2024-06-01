from setuptools import Extension, setup
from Cython.Build import cythonize
from Cython.Compiler import Options

# messing around with extensions.
#extensions = [
#    Extension("texture2d", ["tt3de/glm/Texture2D.pyx"]),
#    Extension("c_triangle_raster", ["tt3de/glm/c_triangle_raster.pyx"], include_dirs=["tt3de/glm/",".","tt3de/"]),
#]


setup(
    ext_modules = cythonize(["tt3de/glm/c_math.pyx",
                             "tt3de/glm/c_texture.pyx",
                             "tt3de/glm/drawing/c_drawing_buffer.pyx",
                             "tt3de/glm/material/c_material.pyx",
                             "tt3de/glm/raster/c_raster_point.pyx",
                             "tt3de/glm/raster/c_raster_tri.pyx",
                             "tt3de/glm/primitives/primitives.pyx",

                             "tt3de/glm/raster/raster.pyx",
                             "tt3de/glm/c_triangle_raster.pyx",
                             ],
                            compiler_directives={'boundscheck': True,
                                                 'embedsignature':True}),

)
