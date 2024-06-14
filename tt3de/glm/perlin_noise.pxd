

cimport cython
from libc.math cimport sin, cos, floor



cdef inline float fade(float t)noexcept nogil


cdef inline float lerp(float t, float a, float b)noexcept nogil

cdef inline float grad(int hash, float x, float y, float z)noexcept nogil

cdef  float perlin(float x, float y, float z) nogil noexcept
                                   