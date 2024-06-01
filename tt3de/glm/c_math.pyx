
from libc.math cimport floor,ceil,round,lrint,nearbyint,abs



cdef inline int c_ceil(double a) noexcept nogil:
    return int(ceil(a))

cdef inline int c_floor(double a) noexcept nogil:
    return int(floor(a))

cdef inline int c_round(double x) noexcept nogil:
    return int(round(x))

def c_ceil_f(a:float )->int : return c_ceil(a)
def c_floor_f(a:float )->int : return c_floor(a)
def c_round_f(a:float )->int : return c_round(a)
cpdef  int c_clamp_and_round_f(float a,int maxvalue ) : return round_in_screen(<double>a,maxvalue)

