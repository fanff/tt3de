
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from libc.math cimport floor,ceil,round,lrint,nearbyint,abs
import cython
from cpython.array cimport array, clone
from tt3de.glm.c_texture cimport Texture2D

cpdef fu():
    Texture2D(2,3)


cdef int c_ceil(double a):
    return int(ceil(a))

cdef int c_floor(double a):
    return int(floor(a))

cdef int c_round(double x):
    return int(round(x))


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

def c_ceil_f(a:float )->int : return c_ceil(a)
def c_floor_f(a:float )->int : return c_floor(a)
def c_round_f(a:float )->int : return c_round(a)
def c_clamp_and_round_f(a:float,maxvalue:int )->int : return round_in_screen(a,maxvalue)


cdef inline double c_determinant(double[3][3] mat):
    # custom determinant for matrix of triangle, ignoring the z component
    # Since the last row is [1, 1, 1], we can expand the determinant along this row:
    # det = a11 * (a22 - a23) - a12 * (a21 - a23) + a13 * (a21 - a22)
    return mat[0][0] * (mat[1][1] - mat[1][2]) - mat[0][1] * (mat[1][0] - mat[1][2]) + mat[0][2] * (mat[1][0] - mat[1][1])

cdef void adjoint_mat(double[3][3] mat, double[3][3] adj_mat):
    # mat[0] is the first col
    # mat[:][0] is the row
    # Calculate the adjoint matrix into destination
    # assuming the last row or 'mat' is [1, 1, 1]

    # Elements of the input matrix
    cdef double a = mat[0][0]
    cdef double b = mat[0][1]
    cdef double c = mat[0][2]
    cdef double d = mat[1][0]
    cdef double e = mat[1][1]
    cdef double f = mat[1][2]
    
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
    

cdef mat3cast(src_mat:glm.mat3 , double[3][3] dst_mat):
    cdef int i, j
    for i in range(3):
        for j in range(3):
            dst_mat[j][i] = src_mat[i][j]

def mat3cast_f(src_mat:glm.mat3):
    cdef double[3][3] mat;
    mat3cast(src_mat,mat)

    return mat


cdef inline double _c_yvalue_from_adjoint_unprotected(double[3][3] adj_matrix,
                unsigned int side,
                 double x)  noexcept nogil:
    #a, b, c = adj_matrix[side][0]glm.row(adj_matrix,side)
    cdef double a = adj_matrix[0][side]
    cdef double b = adj_matrix[1][side]
    cdef double c = adj_matrix[2][side]
    a = (-a)/(b)
    c = (-c)/(b)

    return a * x + c

def iterate_pixel_buffer(unsigned int[:] buffer_data, max_idx:int):
    cdef unsigned int i = 0
    cdef unsigned int mid = <unsigned int> max_idx
    if max_idx<0:
        return
    
    for i in range(0,mid,2):
        yield(buffer_data[i],buffer_data[i+1])



@cython.boundscheck(False)
cdef inline unsigned int __yield_xi_yi(unsigned int[:] output,
                    unsigned int index,
                    unsigned int xi,unsigned int yi) noexcept nogil:
    "set the xiyi index in an array"
    output[index] = xi
    output[(index+1)] = yi
    return 2

def c_glm_triangle_render_to_buffer(tri:glm.mat3,
            screen_width_input:int,
            screen_height_input:int,
            outputbuffer: array.array ):
    cdef unsigned int screen_width = screen_width_input
    cdef unsigned int screen_height = screen_height_input

    cdef double[3][3] mat;
    mat3cast(tri,mat)
    cdef double[3][3] adjoint;
    adjoint_mat(mat,adjoint)
    
    cdef unsigned int[:] output_mem_view = outputbuffer

    cdef unsigned int count= 0
    with nogil:
        count = _c_glm_triangle_render_to_buffer(mat,adjoint,
                screen_width-1,screen_height-1,
                output_mem_view)
    return count


cdef int _c_glm_triangle_render_to_buffer (
    double[3][3] mat, 
    double[3][3] adjoint,
    unsigned int scw_1, 
    unsigned int sch_1,
    unsigned int[:] output) noexcept nogil:

    #gax,gbx,gcx = iround(clamp(row(tri,0),0.0,screen_width-1))#round(xclamped.x),round(xclamped.y),round(xclamped.z)
    #gay,gby,gcy = iround(clamp(row(tri,1),0.0,screen_height-1))#round(yclamped.x),round(yclamped.y),round(yclamped.z)
    
    cdef unsigned int ax = round_in_screen(mat[0][0], scw_1)
    cdef unsigned int ay = round_in_screen(mat[1][0], sch_1)
    cdef unsigned int bx = round_in_screen(mat[0][1], scw_1)
    cdef unsigned int by = round_in_screen(mat[1][1], sch_1)
    cdef unsigned int cx = round_in_screen(mat[0][2], scw_1)
    cdef unsigned int cy = round_in_screen(mat[1][2], sch_1)
    cdef unsigned int buffer_index = 0

    
    cdef unsigned int minxi= 0
    cdef unsigned int maxxi= 0
    cdef unsigned int cutx = 0

    # iterator to use
    cdef unsigned int xi=0
    cdef unsigned int yi=0
    
    # sometime xi is casted to double value
    cdef double xi_double = 0.0

    # min_max y values used during iteration
    cdef unsigned int miny = 0
    cdef unsigned int maxy = 0

    cdef unsigned int seg1= 0
    cdef unsigned int seg2= 0
    cdef unsigned int seg3= 0
    cdef unsigned int seg4= 0
    # segment index 
    # 0: CB
    # 1: AC
    # 2: AB
    # identifying triangle positionning
     

    cdef unsigned int tri_left_yi = 0
    cdef unsigned int tri_cut_yi= 0
    cdef unsigned int tri_right_yi= 0
    
    cdef unsigned int diff_cut_min = 0
    cdef unsigned int diff_maxx_cutx = 0

    if ax < cx:
        if cx < bx:
            #  ..-C.
            # A-----B
            # 
            minxi= ax
            maxxi= bx
            cutx = cx

            # seg1 to seg2; then seg3 to seg4
            seg1 = 2  # AB
            seg2 = 1  # AC
            seg3 = 2  
            seg4 = 0  # CB
            # heights to use, for min, cut, max
            tri_left_yi,tri_cut_yi,tri_right_yi = ay,cy,by
        else:
            if ax<bx:
                #       _---C.
                #   .-^    /
                # A-----B/
                # common branch is upper
                minxi = ax
                maxxi = cx
                cutx = bx

                seg1 = 2 # AB
                seg2 = 1 # AC
                seg3 = 0 # CB
                seg4 = 1 # AC
                tri_left_yi,tri_cut_yi,tri_right_yi = ay, by, cy    
            else:
                #     A   
                #         C
                #  B    
                #   
                minxi= bx
                maxxi= cx
                cutx = ax

                seg1 = 0 # CB
                seg2 = 2 # AB
                seg3 = 0 # CB
                seg4 = 1 # AC
                tri_left_yi,tri_cut_yi,tri_right_yi = by,ay,cy
    else:
        if ax < bx:
            #    C        B 
            #    
            #         A          
            #   common branch is upper
            minxi= cx
            maxxi= bx
            cutx = ax

            seg1 = 1 # AC
            seg2 = 0 # CB
            seg3 = 2 # AB
            seg4 = 0 # CB
            tri_left_yi,tri_cut_yi,tri_right_yi = cy,ay,by
        else:
            
            if cx<bx:
                #      B      
                #    
                #   C        A          
                #   
                minxi= cx
                maxxi= ax
                cutx = bx

                seg1 = 1 # AC
                seg2 = 0 # CB
                seg3 = 1 # AC
                seg4 = 2 # AB
                tri_left_yi,tri_cut_yi,tri_right_yi = cy,by,ay


            else:
                #   B        A   
                #       
                #        C
                # common branch is upper
                minxi= bx
                maxxi= ax
                cutx = cx

                seg1 = 0 # CB
                seg2 = 2 # AB
                seg3 = 1 # AC
                seg4 = 2 # AB
                tri_left_yi,tri_cut_yi,tri_right_yi = by,cy,ay

    

    # ys is actually tri_left_yi,tri_cut_yi,tri_right_yi


    # first part
    # from left to the cutindex
    # the drawing is NOT including the cut 
    
    diff_cut_min = cutx-minxi
    if diff_cut_min==0:
        # its a vertical stuff
        buffer_index+=__yield_xi_yi(output,buffer_index,minxi,tri_left_yi)
        # minxi,ys[0] # returning left point height
    else:
        if diff_cut_min==1:
            for yi in range(tri_left_yi,tri_cut_yi):  # from left height, to cut height
                buffer_index+=__yield_xi_yi(output,buffer_index, minxi,yi)
            
        else:
            
            # left corner return (minxi,tri_left_yi)
            
            buffer_index+=__yield_xi_yi(output, buffer_index, minxi,tri_left_yi)

            for xi in range(minxi+1,cutx):

                xi_double = <double> xi
                miny = floor_in_screen(_c_yvalue_from_adjoint_unprotected(adjoint, seg1, xi_double),sch_1)
                maxy = ceil_in_screen(_c_yvalue_from_adjoint_unprotected(adjoint, seg2, xi_double),sch_1)
                for yi in range(miny,maxy):
                    buffer_index+=__yield_xi_yi(output,buffer_index,  xi,yi)
                #for yi in glmiterate(adjoint,seg1,seg2,xi,screen_height):
                #    yield xi,yi

#    # second part
#    
    diff_maxx_cutx = maxxi-cutx
    if diff_maxx_cutx == 0:
        # its a vertical line. 
        buffer_index+=__yield_xi_yi(output,buffer_index,  cutx, tri_cut_yi) #yield cutx,ys[0]
    elif diff_maxx_cutx == 1:
        for yi in range(tri_cut_yi,tri_right_yi):
            buffer_index+=__yield_xi_yi(output,buffer_index, cutx,yi)
            
        buffer_index+=__yield_xi_yi(output,buffer_index, maxxi,tri_right_yi)

    else:
        for xi in range(cutx,maxxi):
            xi_double = <double> xi
            miny = floor_in_screen(_c_yvalue_from_adjoint_unprotected(adjoint, seg3, xi_double),sch_1)
            maxy = ceil_in_screen(_c_yvalue_from_adjoint_unprotected(adjoint, seg4, xi_double),sch_1)

            for yi in range(miny,maxy):
                buffer_index+=__yield_xi_yi(output,buffer_index,  xi,yi)
            
    return buffer_index






############################################################



def ut_adjoint_calculation(tri:glm.mat3):
    """unit testing code """
    cdef double[3][3] mat;
    mat3cast(tri,mat)
    cdef double[3][3] adjoint;
    adjoint_mat(mat,adjoint)

    dmat = c_determinant(mat)
    

    return adjoint,dmat



def ut_yvalue_calculation(tri:glm.mat3,side:int,x:int):
    """unit testing code """

    cdef double[3][3] mat;
    cdef double[3][3] adjoint;
    mat3cast(tri,mat)
    adjoint_mat(mat,adjoint)

    return _c_yvalue_from_adjoint_unprotected(adjoint,side,x)


def ut_factors_calculation(tri:glm.mat3,scw_1,sch_1):

    cdef double[3][3] mat;
    mat3cast(tri,mat)



    cdef unsigned int ax = round_in_screen(mat[0][0], scw_1)
    cdef unsigned int ay = round_in_screen(mat[1][0], sch_1)
    cdef unsigned int bx = round_in_screen(mat[0][1], scw_1)
    cdef unsigned int by = round_in_screen(mat[1][1], sch_1)
    cdef unsigned int cx = round_in_screen(mat[0][2], scw_1)
    cdef unsigned int cy = round_in_screen(mat[1][2], sch_1)


    return ax,ay, bx,by, cx,cy

def ut_output_array_set(outputbuffer,index,valuex,valuey):
    cdef unsigned int[:] output_mem_view = outputbuffer

    __yield_xi_yi(output_mem_view,index,valuex,valuey)

    
############################
# Triangle structures 







############################ 

DEF TRIANGLE_PIXEL_DATA_COUNT = 4  # floats for each pixel [depth, wa,wb,wc]
DEF TRIANGLE_PIXEL_INDEX_COUNT = 2 # integer for each pixel [material_id,triangle_id]

DEF TRIANGLE_FACE_DATA_COUNT = 64 # each triangle face can store normal/uv stuff
DEF TRIANGLE_MESH_DATA_COUNT = 64 # each Mesh can store some info, like the transform it was at render time
DEF UNIFORM_DATA_COUNT = 64 # some data for holding global light info/ environment info / screen_info 

def _c_constants() -> dict[str:int]:

    headers = ["UNIFORM_DATA_COUNT","TRIANGLE_MESH_DATA_COUNT","TRIANGLE_FACE_DATA_COUNT","TRIANGLE_PIXEL_DATA_COUNT","TRIANGLE_PIXEL_INDEX_COUNT"]
    values = [UNIFORM_DATA_COUNT,TRIANGLE_MESH_DATA_COUNT,TRIANGLE_FACE_DATA_COUNT,TRIANGLE_PIXEL_DATA_COUNT,TRIANGLE_PIXEL_INDEX_COUNT]
    return dict(zip(headers,values))

def make_per_pixel_data_buffer(screen_width,screen_height,initial_value:float=0.0):
    """this is essentially a depth buffer with 4 vaues in it."""
    return array("d",[initial_value]*(TRIANGLE_PIXEL_DATA_COUNT*screen_width*screen_height))

def make_per_pixel_index_buffer(screen_width,screen_height):
    """array of int to store the material_id and triangle_id while generation"""
    return array("I",[0]*(TRIANGLE_PIXEL_INDEX_COUNT*screen_width*screen_height))



def make_uniform_data_buffer():
    """array of int to store the material_id and triangle_id while generation"""
    return array("d",[0.0]*(UNIFORM_DATA_COUNT))


def make_per_mesh_data_buffer():
    """array of int to store the material_id and triangle_id while generation"""
    return array("d",[0.0]*(TRIANGLE_MESH_DATA_COUNT))



ctypedef packed struct line_coef:
    double alpha
    double beta


cdef void init_line_coef(line_coef* x,size_t index,double a,double b):
    x[index].alpha = a
    x[index].beta = b




ctypedef packed struct triangle_shape:
    double[3][3] mat
    double[3][3] adjoint
    line_coef[3] coefs 


    double[TRIANGLE_FACE_DATA_COUNT]  face_data # layout as you will

    # flat determinant of the triangle (surface on screen)
    double flat_determinant

    unsigned int material_id
    unsigned int unique_id
    # screen limit -1 for the triangle
    unsigned int scw_1
    unsigned int sch_1
    
    unsigned int ax 
    unsigned int ay 
    unsigned int bx 
    unsigned int by 
    unsigned int cx 
    unsigned int cy 


cdef void init_triangle(triangle_shape* tris,size_t idx):
    tris[idx].mat     =  [[.0,.0,.0],[.0,.0,.0],[.0,.0,.0]]
    tris[idx].adjoint =  [[.0,.0,.0],[.0,.0,.0],[.0,.0,.0]]
    tris[idx].coefs   =  [line_coef(.0,.0),line_coef(.0,.0),line_coef(.0,.0)]

cdef class TrianglesBuffer:
    cdef triangle_shape* array_of_triangles
    cdef size_t max_count 
    cdef size_t idx_limit 

    def __cinit__(self, size_t number):
        # allocate some memory (uninitialised, may contain arbitrary data)
        self.array_of_triangles = <triangle_shape*> PyMem_Malloc(
            (number+1) * sizeof(triangle_shape))

        self.max_count = number

        self.idx_limit = 0
        # init memory
        for i in range(self.max_count):
            init_triangle(self.array_of_triangles,i)

        if not self.array_of_triangles:
            raise MemoryError()
        
    def get_triangle(self,idx:int ):
        cdef triangle_shape tr = self.array_of_triangles[idx]

        return tr

    def count(self)->int:
        return int(self.idx_limit)
    def clear(self):
        self.idx_limit = 0
    
    def as_pylist(self):
        return [self.array_of_triangles[i] for i in range(self.idx_limit)]
    def __dealloc__(self):
        PyMem_Free(self.array_of_triangles)  # no-op if self.array_of_triangles is NULL
    def add_triangle_info(self, tri, material_id:int =0 , uvmap:tuple[float,float,float,float,float,float]=None)->int:
        """
        uvmap can be a matrix 3x2 with uv vectore for 3 points; list(itertools.chain(*uvmap.to_tuple())) to listify 
        """
        cdef unsigned int inserted_at = self.idx_limit
        cdef triangle_shape* tr = &self.array_of_triangles[inserted_at]
        
        tr.material_id = <unsigned int> material_id
        tr.unique_id = inserted_at


        cdef size_t i, j
        for i in range(3):
            for j in range(3):
                tr.mat[j][i] = tri[i][j]


        cdef double[6] fds
        if uvmap is not None:
            #tr.face_data[0:6] =  
            fds = uvmap
            tr.face_data[0:6] = fds
        
        if self.idx_limit < self.max_count:
            self.idx_limit+=1
        return inserted_at

    def add_many_triangles(self, triangles):
        for tri in triangles:
            self.add_triangle_info(tri)
        

    def calculate_internal(self,screen_width:int,screen_height:int):
        cdef triangle_shape* tr

        cdef unsigned int scw_1 = <unsigned int> screen_width-1
        cdef unsigned int sch_1 = <unsigned int> screen_height-1

        # Elements of the input matrix
        cdef double axf ;
        cdef double ayf ;
        cdef double bxf ;
        cdef double byf ;
        cdef double cxf ;
        cdef double cyf ;

        cdef size_t side;

        cdef size_t i;
        for i in range(self.idx_limit):
            tr = &self.array_of_triangles[i]
            tr.flat_determinant = c_determinant(tr.mat)
            
            tr.scw_1 = scw_1
            tr.sch_1 = sch_1

            axf = tr.mat[0][0]
            ayf = tr.mat[1][0]
            bxf = tr.mat[0][1]
            byf = tr.mat[1][1]
            cxf = tr.mat[0][2]
            cyf = tr.mat[1][2]

            # getting the rounded values of the corners; 
            # clamped into the screen
            tr.ax = round_in_screen(axf, scw_1)
            tr.ay = round_in_screen(ayf, sch_1)
            tr.bx = round_in_screen(bxf, scw_1)
            tr.by = round_in_screen(byf, sch_1)
            tr.cx = round_in_screen(cxf, scw_1)
            tr.cy = round_in_screen(cyf, sch_1)
            
    
            # Calculate the cofactors (with assumption that last row is [1, 1, 1])
            tr.adjoint[0][0] = byf - cyf  #diff y 
            tr.adjoint[0][1] = cyf - ayf
            tr.adjoint[0][2] = ayf - byf
            tr.adjoint[1][0] = cxf - bxf  # diff x 
            tr.adjoint[1][1] = axf - cxf
            tr.adjoint[1][2] = bxf - axf
            tr.adjoint[2][0] = bxf*cyf - cxf*byf
            tr.adjoint[2][1] = cxf*ayf - axf*cyf
            tr.adjoint[2][2] = axf*byf - bxf*ayf
            #  C
            # A  B
            # some extra values could be calculated :
            # segment index 
            # 0: CB
            # 1: AC
            # 2: BA
            
            side=0
            if tr.cx!=tr.bx:
                tr.coefs[side].alpha = (-tr.adjoint[0][side])/tr.adjoint[1][side]
                tr.coefs[side].beta = (-tr.adjoint[2][side])/tr.adjoint[1][side]

            side=1
            if tr.ax!=tr.cx:
                tr.coefs[side].alpha = (-tr.adjoint[0][side])/tr.adjoint[1][side]
                tr.coefs[side].beta = (-tr.adjoint[2][side])/tr.adjoint[1][side]
            side=2
            if tr.ax!=tr.bx:
                tr.coefs[side].alpha = (-tr.adjoint[0][side])/tr.adjoint[1][side]
                tr.coefs[side].beta = (-tr.adjoint[2][side])/tr.adjoint[1][side]
    
    def get_triangle_face_data(self, idx:int):
        return self._get_triangle_face_data(idx)


    cdef double[:] _get_triangle_face_data(self,unsigned int idx):
        return self.array_of_triangles[idx].face_data

    def raster_to_buffer(self, 
        depth_buffer: array.array,
        index_buffer:array.array):
        """"""
        cdef unsigned int [:] index_array = index_buffer
        cdef double[:] depth_buffer_mem_view = depth_buffer
        self._raster_to_buffer(depth_buffer_mem_view,index_array)

    cdef void _raster_to_buffer(self,double[:] depth_buffer,unsigned int [:] index_array) noexcept :

        
        cdef triangle_shape* tr

        cdef size_t side;

        cdef size_t i;
        for tr in self.array_of_triangles[:self.idx_limit]:
            _raster_tr(tr,depth_buffer,index_array)


cdef double calc_y_for_triangle(triangle_shape *tr,unsigned int side,double xif ) noexcept nogil:
    return tr.coefs[side].alpha * xif + tr.coefs[side].beta


@cython.boundscheck(False)
cdef inline void depth_buffer_insert(double[:] db,unsigned int [:] index_array,
                    unsigned int xi,
                    unsigned int yi,
                    triangle_shape* tr) noexcept nogil:

    cdef double x = <double> (xi)
    cdef double y = <double> (yi)

    #side 0
    cdef double wa = tr.adjoint[0][0] * x  +  tr.adjoint[1][0] * y + tr.adjoint[2][0]
    #side 1
    cdef double wb = tr.adjoint[0][1] * x  +  tr.adjoint[1][1] * y + tr.adjoint[2][1]
    #side 2
    cdef double wc = tr.adjoint[0][2] * x  +  tr.adjoint[1][2] * y + tr.adjoint[2][2]
    


    cdef double depth = tr.mat[2][0] * wa +  tr.mat[2][1] * wb + tr.mat[2][2] * wc
    
    cdef unsigned int index = (((tr.sch_1+1) * xi) + yi)

    cdef unsigned int index_depth = index*TRIANGLE_PIXEL_DATA_COUNT
    cdef unsigned int index_integer_array = index*TRIANGLE_PIXEL_INDEX_COUNT

    if depth < db[index_depth] :


        db[index_depth] = depth
        db[index_depth+1] = wa
        db[index_depth+2] = wb
        db[index_depth+3] = wc

        index_array[index_integer_array] = tr.unique_id
        index_array[index_integer_array+1] = tr.material_id
    

cdef void _raster_tr (
    triangle_shape* tr,
    double[:] depth_buffer,
    unsigned int [:] index_array) noexcept nogil:


    # init the boundaries
    cdef unsigned int minxi= 0
    cdef unsigned int maxxi= 0
    cdef unsigned int cutx = 0

    # iterator to use
    cdef unsigned int xi=0
    cdef unsigned int yi=0
    
    # sometime xi is casted to double value
    cdef double xi_double = 0.0

    # min_max y values used during iteration
    cdef unsigned int miny = 0
    cdef unsigned int maxy = 0

    cdef unsigned int seg1= 0
    cdef unsigned int seg2= 0
    cdef unsigned int seg3= 0
    cdef unsigned int seg4= 0
    # segment index 
    # 0: CB
    # 1: AC
    # 2: AB
    # identifying triangle positionning
     

    cdef unsigned int tri_left_yi = 0
    cdef unsigned int tri_cut_yi= 0
    cdef unsigned int tri_right_yi= 0
    
    cdef unsigned int diff_cut_min = 0
    cdef unsigned int diff_maxx_cutx = 0

    if tr.ax < tr.cx:
        if tr.cx < tr.bx:
            #  ..-C.
            # A-----B
            # 
            minxi= tr.ax
            maxxi= tr.bx
            cutx = tr.cx

            # seg1 to seg2; then seg3 to seg4
            seg1 = 2  # AB
            seg2 = 1  # AC
            seg3 = 2  
            seg4 = 0  # CB
            # heights to use, for min, cut, max
            tri_left_yi,tri_cut_yi,tri_right_yi = tr.ay,tr.cy,tr.by
        else:
            if tr.ax<tr.bx:
                #       _---C.
                #   .-^    /
                # A-----B/
                # common branch is upper
                minxi = tr.ax
                maxxi = tr.cx
                cutx  = tr.bx

                seg1 = 2 # AB
                seg2 = 1 # AC
                seg3 = 0 # CB
                seg4 = 1 # AC
                tri_left_yi,tri_cut_yi,tri_right_yi = tr.ay, tr.by, tr.cy    
            else:
                #     A   
                #         C
                #  B    
                #   
                minxi= tr.bx
                maxxi= tr.cx
                cutx = tr.ax

                seg1 = 0 # CB
                seg2 = 2 # AB
                seg3 = 0 # CB
                seg4 = 1 # AC
                tri_left_yi,tri_cut_yi,tri_right_yi = tr.by,tr.ay,tr.cy
    else:
        if tr.ax < tr.bx:
            #    C        B 
            #    
            #         A          
            #   common branch is upper
            minxi= tr.cx
            maxxi= tr.bx
            cutx = tr.ax

            seg1 = 1 # AC
            seg2 = 0 # CB
            seg3 = 2 # AB
            seg4 = 0 # CB
            tri_left_yi,tri_cut_yi,tri_right_yi = tr.cy,tr.ay,tr.by
        else:
            
            if tr.cx<tr.bx:
                #      B      
                #    
                #   C        A          
                #   
                minxi= tr.cx
                maxxi= tr.ax
                cutx = tr.bx

                seg1 = 1 # AC
                seg2 = 0 # CB
                seg3 = 1 # AC
                seg4 = 2 # AB
                tri_left_yi,tri_cut_yi,tri_right_yi = tr.cy,tr.by,tr.ay

            else:
                #   B        A   
                #       
                #        C
                # common branch is upper
                minxi= tr.bx
                maxxi= tr.ax
                cutx = tr.cx

                seg1 = 0 # CB
                seg2 = 2 # AB
                seg3 = 1 # AC
                seg4 = 2 # AB
                tri_left_yi,tri_cut_yi,tri_right_yi = tr.by,tr.cy,tr.ay
    
    

    # ys is actually tri_left_yi,tri_cut_yi,tri_right_yi


    # first part
    # from left to the cutindex
    # the drawing is NOT including the cut 
    
    diff_cut_min = cutx-minxi
    if diff_cut_min==0:
        # its a vertical stuff
        depth_buffer_insert(depth_buffer,index_array,minxi,tri_left_yi,tr)
        # minxi,ys[0] # returning left point height
    else:
        if diff_cut_min==1:
            for yi in range(tri_left_yi,tri_cut_yi):  # from left height, to cut height
                depth_buffer_insert(depth_buffer,index_array, minxi,yi,tr)
            
        else:
            
            # left corner return (minxi,tri_left_yi)
            
            depth_buffer_insert(depth_buffer,index_array,minxi,tri_left_yi,tr)

            for xi in range(minxi+1,cutx):
                xi_double = <double> xi
                miny = floor_in_screen(calc_y_for_triangle(tr,seg1, xi_double),tr.sch_1)
                maxy = ceil_in_screen(calc_y_for_triangle(tr, seg2, xi_double),tr.sch_1)
                for yi in range(miny,maxy):
                    depth_buffer_insert(depth_buffer,index_array, xi,yi,tr)

    #
    ##    # second part
    ##    
    diff_maxx_cutx = maxxi-cutx
    if diff_maxx_cutx == 0:
        # its a vertical line. 
        depth_buffer_insert(depth_buffer,index_array, cutx, tri_cut_yi,tr)
    elif diff_maxx_cutx == 1:
        for yi in range(tri_cut_yi,tri_right_yi):
            depth_buffer_insert(depth_buffer,index_array, cutx,yi,tr)
            
        depth_buffer_insert(depth_buffer,index_array, maxxi,tri_right_yi,tr)

    else:
        for xi in range(cutx,maxxi):
            xi_double = <double> xi
            miny = floor_in_screen(calc_y_for_triangle(tr, seg3, xi_double),tr.sch_1)
            maxy = ceil_in_screen(calc_y_for_triangle(tr, seg4, xi_double),tr.sch_1)

            for yi in range(miny,maxy):
                depth_buffer_insert(depth_buffer,index_array,  xi,yi,tr)



def apply_stage2( 
        TrianglesBuffer tr_buff, 
        double_values_buff : array.array,  
        integer_values_buff  : array.array,
        screen_width:int,
        screen_height:int,
        mesh_info : array.array,
        uniformvalues : array.array, # the contextual data
        output : array.array

    ):
    
    
    
    _apply_stage2(tr_buff,
    double_values_buff,
    integer_values_buff ,
    screen_width,
    screen_height,
    mesh_info ,
    uniformvalues ,
    output ,
    
    
    
    
    )

cdef void _apply_stage2(TrianglesBuffer tr_buff, 
        double[:] double_values_buff,    
        unsigned int[:] integer_values_buff,
        
        unsigned int screen_width,
        unsigned int screen_height,
        double[:] mesh_info,
        double[:] uniformvalues, # the contextual data
        unsigned int[:] output
        ):
    
    cdef unsigned int xi = 0
    cdef unsigned int xj = 0
    cdef unsigned int index = 0
    cdef unsigned int int_index = 0
    cdef unsigned int depth_index = 0

    cdef unsigned int material_id = 0
    cdef unsigned int triange_id = 0

    output[0] = 2

    output[screen_width*3] = 5
    
    for xi in range(screen_width):  
        for yi in range(screen_height):
            

            index =(((screen_height) * xi) + yi)
            
            int_index = TRIANGLE_PIXEL_INDEX_COUNT * index
            depth_index = TRIANGLE_PIXEL_DATA_COUNT * index


            #double_values_buff[index]
            material_id =  integer_values_buff[int_index+1]

            if material_id>0:
                triange_id  =  integer_values_buff[int_index]
                #output[(((screen_width) * yi) + xi)] = material_id
                # pixel_info = double_values_buff[depth_index:depth_index+4]
                # mesh_info = 
                apply_material(material_id,
                        xi,yi,(((screen_width) * yi) + xi) , # the canvas buffer is reversed
                        double_values_buff[depth_index:depth_index+TRIANGLE_PIXEL_DATA_COUNT], # pixel info
                        tr_buff._get_triangle_face_data(triange_id), # face_info
                        mesh_info,   
                        uniformvalues,
                        output)



cpdef void apply_material(unsigned int material_id, # paint this on that
    unsigned int xi,unsigned int yi, unsigned int combined_index,    # at this location
    double[:] pixel_info,               # (depth, wa,wb,wb relative to triangle corner)
    double[:] face_info,                # using info from the face like the normal. or the UV coordinates
    double[:] mesh_info,                # mesh info that the vertice come from at the stage zero (the project ) 
    double[:] uniformvalues,            # world uniform values the mesh comes from (like.. global light/environmnet)
    unsigned int[:] output    # some kind of output buffer 
    ):
    """
    face_info : arbitrary data about the face. like uv coordinates


    mesh_info will contain the camera model used at projection time


    uniformvalues contains the camera perspective info, screen wh info; 
    """
    #cdef Texture2D atexture = Texture2D()
    if material_id == 1:
        apply_material_debug(output,xi, yi, combined_index)
    #elif material_id == 2:
    #    apply_1textured_material(output, xi, yi, combined_index, 
    #    uniformvalues, mesh_info, face_info, pixel_info ,
    #    atexture)

cpdef inline void apply_material_debug(unsigned int[:] output,
        unsigned int xi,
        unsigned int yi,
        unsigned int combined_index):
    output[combined_index] = 1



cpdef void apply_1textured_material(unsigned int[:] output, 
    unsigned int xi,
    unsigned int yi,
    unsigned int combined_index,
    double[:] uniformvalues,
    double[:] mesh_info,    
    double[:] face_info,    
    double[:] pixel_info,
    #Texture2D thetexture
    ):

    # double precision UV mapping Oo , because.. precision <3 
    cdef double au = face_info[0] # uv map    
    cdef double av = face_info[1]
    cdef double bu = face_info[2] # uv map    
    cdef double bv = face_info[3]
    cdef double cu = face_info[4] # uv map    
    cdef double cv = face_info[5]

    pixel_info[0]# depth
    cdef double wa = pixel_info[0]
    cdef double wb = pixel_info[1]
    cdef double wc = pixel_info[2]

    cdef double pixu = au*wa + bu * wb + cu*wc
    cdef double pixv = av*wa + bv * wb + cv*wc

    #cdef Texture2D atexture = Texture2D(3,4)