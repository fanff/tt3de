import math
import pytest


from tt3de.render_context_cy import CyRenderContext
from textual.geometry import Region


def version1(rc,size):
    rc.to_textual_(Region(0,0,size,size))

def version2(rc,size):
    rc.to_textual_2(Region(0,0,size,size))


sizes = [128, 256, 512, 768]


@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="to_textual")
def test_method1(benchmark, size):
    rc = CyRenderContext(size,size)

    benchmark(version1, rc,size)

@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="to_textual")
def test_method2(benchmark, size):
    rc = CyRenderContext(size,size)
    benchmark(version2, rc,size)



#this version is actually the fastest;
def canvas_to_list_hashed(rc,size):
    rc.drawing_buffer.canvas_to_list_hashed(0,0,size,size,rc.auto_buffer,rc.allchars)

@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="canvas_to_list_hashed")
def test_to_list_hashed(benchmark, size):
    rc = CyRenderContext(size,size)
    benchmark(canvas_to_list_hashed, rc,size)


def r_version1(gb,size):
    res = gb.to_textual(0,size,0,size)


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