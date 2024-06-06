

def make_glm_object():

    mat = glm.mat4(3.0)

    # a very important identity matrix
    m      = glm.mat4()

    # a ctypes pointer to m's data
    ptr    = glm.value_ptr(m) 

    # size of m's data in bytes (here 4 * 4 * 4 = 64 bytes)
    nbytes = glm.sizeof(m)

    #glBufferData(GL_UNIFORM_BUFFER, nbytes, ptr, GL_STATIC_DRAW)