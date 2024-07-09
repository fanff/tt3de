import math
import pytest
from textual.geometry import Region


sizes = [128, 256, 512, 768]


## this version is SUUUUUPER slow; because of all the instanciation that happen inside. 
# no cache / nothing here. 
def r_version1(gb,size):
    pass
    # res = gb.to_textual(0,size,0,size)


@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="canvas_to_list_hashed")
def test_rust_version1(benchmark, size):
    from rtt3de import AbigDrawing
    gb = AbigDrawing(size,size)
    gb.hard_clear(100.0)    
    benchmark(r_version1, gb,size)
        



#this version is actually the second fastest; close to the Cython, but not quite yet. 
def r_version2(gb,size):
    res = gb.to_textual_2(0,size,0,size)

@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="canvas_to_list_hashed")
def test_rust_version2(benchmark, size):
    from rtt3de import AbigDrawing
    gb = AbigDrawing(size,size)
    gb.hard_clear(100.0)    
    benchmark(r_version2, gb,size)