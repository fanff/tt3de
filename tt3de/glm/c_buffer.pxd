

ctypedef packed struct s_buffer:
    void *data;
    size_t elementSize;
    size_t size;
    size_t capacity;



cdef void initBuffer(s_buffer *array, size_t elementSize, size_t initialCapacity)
cdef void freeBuffer(s_buffer *array) 
cdef int addElement(s_buffer *array, void *element) 
cdef void clearBuffer(s_buffer *array) 


cdef inline int getBuffersize(s_buffer *array):
    return <int> array.size