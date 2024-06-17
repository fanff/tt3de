# cython: language_level=3str


cimport cython
from libc.math cimport sin, cos, floor



cdef  float fade(float t) noexcept nogil


cdef  float lerp(float t, float a, float b) noexcept nogil

cdef  float grad(int hash, float x, float y, float z) noexcept nogil

cdef  float perlin(float x, float y, float z) noexcept nogil
                                   