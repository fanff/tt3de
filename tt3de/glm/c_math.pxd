
from libc.math cimport floor,ceil,round
ctypedef fused cnumeric:
    double 
    float


cdef inline unsigned int round_in_screen(double value, unsigned int b) noexcept nogil:
    if value < 0.0: 
        return 0
    cdef unsigned int rounded_a = <unsigned int> round(value)
    if rounded_a > b:
        return b
    else:
        return rounded_a

cdef inline unsigned int ceil_in_screen(double value, unsigned int b) noexcept nogil:
    if value < 0.0: 
        return 0
    cdef unsigned int _a = <unsigned int> ceil(value)
    if _a > b:
        return b
    else:
        return _a

cdef inline unsigned int floor_in_screen(double value, unsigned int b) noexcept nogil:
    if value < 0.0: 
        return 0
    cdef unsigned int _a = <unsigned int> floor(value)
    if _a > b:
        return b
    else:
        return _a






cdef inline unsigned int round_in_screenf(float value, unsigned int b) noexcept nogil:
    if value < 0.0: 
        return 0
    cdef unsigned int rounded_a = <unsigned int> round(value)
    if rounded_a > b:
        return b
    else:
        return rounded_a

cdef inline unsigned int ceil_in_screenf(float value, unsigned int b) noexcept nogil:
    if value < 0.0: 
        return 0
    cdef unsigned int _a = <unsigned int> ceil(value)
    if _a > b:
        return b
    else:
        return _a

cdef inline unsigned int floor_in_screenf(float value, unsigned int b) noexcept nogil:
    if value < 0.0: 
        return 0
    cdef unsigned int _a = <unsigned int> floor(value)
    if _a > b:
        return b
    else:
        return _a


# Determinant calculation for specific cases:

cdef inline cnumeric flat_determinant_g((cnumeric )[3][3] mat):
    # custom determinant for matrix of triangle, ignoring the z component
    # Since the last row is [1, 1, 1], we can expand the determinant along this row:
    # det = a11 * (a22 - a23) - a12 * (a21 - a23) + a13 * (a21 - a22)
    return mat[0][0] * (mat[1][1] - mat[1][2]) - mat[0][1] * (mat[1][0] - mat[1][2]) + mat[0][2] * (mat[1][0] - mat[1][1])


cdef inline adjoint_mat(cnumeric[3][3] mat, cnumeric[3][3] adj_mat):
    # mat[0] is the first col
    # mat[:][0] is the row
    # Calculate the adjoint matrix into destination
    # assuming the last row or 'mat' is [1, 1, 1]

    # Elements of the input matrix
    cdef cnumeric a = mat[0][0]
    cdef cnumeric b = mat[0][1]
    cdef cnumeric c = mat[0][2]
    cdef cnumeric d = mat[1][0]
    cdef cnumeric e = mat[1][1]
    cdef cnumeric f = mat[1][2]
    
    # Calculate the cofactors (with assumption that last row is [1, 1, 1])

    #diff y 
    adj_mat[0][0] = e - f
    adj_mat[0][1] = f - d
    adj_mat[0][2] = d - e

    # diff x 
    adj_mat[1][0] = c - b
    adj_mat[1][1] = a - c
    adj_mat[1][2] = b - a


    adj_mat[2][0] = b*f - c*e
    adj_mat[2][1] = c*d - a*f
    adj_mat[2][2] = a*e - b*d


    # some extra values could be calculated :
    # segment index 
    # 0: CB
    # 1: AC
    # 2: AB
    # xalpha = (-adj_matrix[0][side])/adj_matrix[1][side]
    # xintercept = (-adj_matrix[2][side])/adj_matrix[1][side]