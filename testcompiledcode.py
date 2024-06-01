
aint  = 4.0 # in bytes #  size of the int
anumeric_value_size = 4.0 # size of a float

acolor = 3.0 # bytes,  3 for 24 bits, 2 for 16 bits (still good) , 1 for 8bits

drawing_screen_pix_count = 1920*1080

indexor_size = 4.0  # 4 bytes  

uv_layer_count = 2
vertice_buffer_count = 2**16
primitive_buffer_count = 2**16


vec3 = 3 * anumeric_value_size
vec2 = 2 * anumeric_value_size

node_buffer_size = ( vec2*2 * 4 ) * min(primitive_buffer_count,vertice_buffer_count)
geometry_size =  ( indexor_size*3 + indexor_size + indexor_size + (vec2*3*uv_layer_count)  + indexor_size ) * min(primitive_buffer_count,vertice_buffer_count)
vertice_buffer_size =( vec3 + vec3 + indexor_size ) * vertice_buffer_count

primitive_size = ( indexor_size*3 + indexor_size + indexor_size + indexor_size )  * primitive_buffer_count
drawing_size =   ( anumeric_value_size + 3*anumeric_value_size + indexor_size + indexor_size+ indexor_size ) * drawing_screen_pix_count
canvas_size =    ( acolor + acolor + acolor ) * drawing_screen_pix_count


data = ({
    "node_buffer_size": node_buffer_size,
    "vertice_buffer_size" : vertice_buffer_size,
    "primitive_size" : primitive_size,
    "geometry_size" : geometry_size,
    "drawing_size" : drawing_size ,
    "canvas_size" : canvas_size
})

import pandas as pd 
df = pd.DataFrame([data])/(2**20)
print(df)
print(df.sum())
print(df.sum().sum())
