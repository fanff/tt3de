import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.glm.c_texture import Texture2D, bench_n_uvcacl

from tt3de.richtexture import ImageTexture, Segmap
from tt3de.tt3de import PPoint2D, Point2D

UV_LOOP_COUNT = 1000000


def cversion(atexture):
    for i in range(UV_LOOP_COUNT):
        atexture.get_pixel_uv(0, 0)


@pytest.mark.benchmark(
    group="uv-map",
)
def test_bench_c_impl(benchmark):

    img: ImageTexture = fast_load("models/test_screen32.bmp")
    atexture = Texture2D(img.image_width, img.image_height)
    atexture.load_from_list(img.img_data)

    benchmark(cversion, atexture)


def cinternal(atexture):
    bench_n_uvcacl(atexture, UV_LOOP_COUNT)


@pytest.mark.benchmark(
    group="uv-map",
)
def test_bench_c_loop(benchmark):

    img: ImageTexture = fast_load("models/test_screen32.bmp")
    atexture = Texture2D(img.image_width, img.image_height)
    atexture.load_from_list(img.img_data)

    benchmark(cinternal, atexture)


def pythonversion(img, p):
    for i in range(UV_LOOP_COUNT):
        img.render_point(p)


@pytest.mark.benchmark(group="uv-map")
def test_bench_py_impl(benchmark):
    img: ImageTexture = fast_load("models/test_screen32.bmp")
    atexture = Texture2D(img.image_width, img.image_height)
    atexture.load_from_list(img.img_data)
    p = PPoint2D(0, 0)
    p.uv = Point2D(0.1, 0.1)

    s = Segmap()
    s.init()
    img.cache_output(s)
    benchmark(pythonversion, img, p)
