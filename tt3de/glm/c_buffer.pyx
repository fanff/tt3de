
from libc.stdlib cimport malloc, free
from libc.string cimport memset
from libc.string cimport memcpy 
from tt3de.glm.c_buffer cimport s_buffer



cdef void initBuffer(s_buffer *array, size_t elementSize, size_t initialCapacity):
    array.data = malloc(elementSize * initialCapacity);
    array.elementSize = elementSize;
    array.size = 0;
    array.capacity = initialCapacity;


cdef void freeBuffer(s_buffer *array) :
    free(array.data);
    array.data = NULL;
    array.size = 0;
    array.capacity = 0;

cdef int addElement(s_buffer *array, void *element):
    if (array.size == array.capacity) :
        # // Not enough capacity
        return 0; #// Failure
    memcpy((<char *>array.data) + array.size * array.elementSize, element, array.elementSize);
    array.size = array.size+1;
    return 1; #// Success

cdef void clearBuffer(s_buffer *array):
    array.size = 0

