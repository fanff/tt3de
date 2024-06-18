import pytest
import math
import pytest
import math
import unittest

from tt3de.richtexture import Segmap
import time


from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.style import Style
from rich.text import Segment
from textual.strip import Strip

from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer

sizes = [32]


def method_1(drawing_buffer, style_array):
    # canvas_data = drawing_buffer.canvas_to_list()
    segs = []
    for idx, (fr, fg, fb, br, bg, bb, g1, g2) in enumerate(
        drawing_buffer.canvas_to_list()
    ):
        asegment = Segment(
            " ",
            Style(
                color=Color.from_triplet(ColorTriplet(fr, fg, fb)),
                bgcolor=Color.from_triplet(ColorTriplet(br, bg, bb)),
            ),
        )
        segs.append(asegment)
    Strip(segs)


@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="to_textual")
def test_bench_to_textual_method1(benchmark, size):
    drawing_buffer = DrawingBuffer(size, size)
    drawing_buffer.hard_clear(100)

    style_array = [Style() for i in range(size * size)]
    benchmark(method_1, drawing_buffer, style_array)


def method_2(drawing_buffer, big_buffer, allchars):
    # canvas_data = drawing_buffer.canvas_to_list()
    factor = len(allchars)
    segs = []
    for fr, fg, fb, br, bg, bb, g1, g2 in drawing_buffer.canvas_to_list():
        segid = fb // 32 + 8 * (
            fg // 32 + 8 * (fr // 32 + 8 * (bb // 32 + 8 * (bg // 32 + 8 * (br // 32))))
        )
        segs.append(Segment(" ", big_buffer[segid]))
    Strip(segs)


@pytest.mark.parametrize("size", sizes)
@pytest.mark.benchmark(group="to_textual")
def test_bench_to_textual_method2(benchmark, size):
    drawing_buffer = DrawingBuffer(size, size)
    drawing_buffer.hard_clear(100)
    allchars = [chr(i) for i in range(32, 126)]

    big_buffer = []  # 262 144 values
    idx = 0
    for i in range(8):
        for j in range(8):
            for k in range(8):
                for bi in range(8):
                    for bj in range(8):
                        for bk in range(8):

                            big_buffer.append(
                                Style(
                                    color=Color.from_triplet(ColorTriplet(i, j, k)),
                                    bgcolor=Color.from_triplet(
                                        ColorTriplet(bi, bj, bk)
                                    ),
                                )
                            )

    benchmark(method_2, drawing_buffer, big_buffer, allchars)


