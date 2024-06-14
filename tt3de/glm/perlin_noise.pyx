

cimport cython
from libc.math cimport sin, cos, floor

cdef int perm[512];

perm = [
    151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,
    30,69,142,8,99,37,240,21,10,23,190, 6,148,247,120,234,75,0,26,197,
    62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,
    125,136,171,168, 68,175,74,165,71,134,139,48,27,166,77,146,158,231,
    83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,
    143,54, 65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,
    196,135,130,116,188,159,86,164,100,109,198,173,186, 3,64,52,217,
    226,250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,
    47,16,58,17,182,189,28,42,223,183,170,213,119,248,152, 2,44,154,
    163, 70,221,153,101,155,167, 43,172,9,129,22,39,253, 19,98,108,110,
    79,113,224,232,178,185, 112,104,218,246,97,228,251,34,242,193,238,
    210,144,12,191,179,162,241, 81,51,145,235,249,14,239,107,49,192,
    214, 31,181,199,106,157,184, 84,204,176,115,121,50,45,127, 4,150,
    254,138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,
    61,156,180
] * 2

@cython.boundscheck(False)
@cython.wraparound(False)
cdef float fade(float t) noexcept nogil:
    return t * t * t * (t * (t * 6 - 15) + 10)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef float lerp(float t, float a, float b) noexcept nogil:
    return a + t * (b - a)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef float grad(int hash, float x, float y, float z) noexcept nogil :
    cdef int h = hash & 15
    cdef float u = x if h < 8 else y
    cdef float v = y if h < 4 else (x if h in (12, 14) else z)
    return ((u if h & 1 == 0 else -u) +
            (v if h & 2 == 0 else -v))

@cython.boundscheck(False)
@cython.wraparound(False)
cdef float perlin(float x, float y, float z) nogil noexcept:
    cdef int X = <int> (floor(x)) & 255
    cdef int Y = <int> (floor(y)) & 255
    cdef int Z = <int> (floor(z)) & 255

    cdef float u =0.0
    cdef float v =0.0
    cdef float w =0.0
    cdef int A =  0
    cdef int AA = 0
    cdef int AB = 0
    cdef int B =  0
    cdef int BA = 0
    cdef int BB = 0


    x -= floor(x)
    y -= floor(y)
    z -= floor(z)

    u = fade(x)
    v = fade(y)
    w = fade(z)

    A = perm[X] + Y
    AA = perm[A] + Z
    AB = perm[A + 1] + Z
    B = perm[X + 1] + Y
    BA = perm[B] + Z
    BB = perm[B + 1] + Z

    return lerp(w, lerp(v, lerp(u, grad(perm[AA], x, y, z),
                                   grad(perm[BA], x - 1, y, z)),
                           lerp(u, grad(perm[AB], x, y - 1, z),
                                   grad(perm[BB], x - 1, y - 1, z))),
                   lerp(v, lerp(u, grad(perm[AA + 1], x, y, z - 1),
                                   grad(perm[BA + 1], x - 1, y, z - 1)),
                           lerp(u, grad(perm[AB + 1], x, y - 1, z - 1),
                                   grad(perm[BB + 1], x - 1, y - 1, z - 1))))

