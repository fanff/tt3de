# -*- coding: utf-8 -*-
import unittest
import pytest

from tests.tt3de.test_utils import assertPixInfoEqual
from tt3de.tt3de import DrawingBufferPy
from tt3de.tt3de import apply_material_py
from tt3de.tt3de import MaterialBufferPy, TextureBufferPy
from pyglm import glm
from tt3de.tt3de import VertexBufferPy, TransformPackPy
from tt3de.tt3de import PrimitiveBufferPy

# Cell (row=0, col=0) center NDC on a 32×32 buffer with default flip flags (see ``cell_center_to_ndc``).
_FRAG_POS_NDC_32_R0_C0: list[float] = [-0.96875, 0.96875]


class Test_DrawBuffer(unittest.TestCase):
    def test_create_verybig(self):
        gb = DrawingBufferPy(10, 10)

        layer = 0
        v = gb.get_depth_buffer_cell(0, 0, layer)
        self.assertEqual(
            v,
            {
                "depth": 10.0,
                "pix_info": layer,
                "uv": [0.0, 0.0],
                "uv_1": [0.0, 0.0],
                "frag_pos": [0.0, 0.0],
                "material_id": 0,
                "geometry_id": 0,
                "node_id": 0,
                "primitive_id": 0,
                "front_facing": True,
                "line_coord": 0.0,
                "point_coord": [0.0, 0.0],
            },
        )

        layer = 1
        v = gb.get_depth_buffer_cell(0, 0, layer)
        self.assertEqual(v, {})

        for pix_idx in range(10 * 10):
            self.assertEqual(
                gb.get_pix_info_element(pix_idx),
                {
                    "uv": [0.0, 0.0],
                    "uv_1": [0.0, 0.0],
                    "frag_pos": [0.0, 0.0],
                    "primitive_id": 0,
                    "geometry_id": 0,
                    "node_id": 0,
                    "material_id": 0,
                    "normal": [0.0, 0.0, 1.0],
                    "front_facing": True,
                    "line_coord": 0.0,
                    "point_coord": [0.0, 0.0],
                },
            )

        ccelldict = gb.get_canvas_cell(0, 0)

        self.assertEqual(len(ccelldict), 7)

        hyp = {"f_r": 0, "f_b": 0, "f_g": 0, "b_r": 0, "b_g": 0, "b_b": 0, "glyph": 0}
        self.assertEqual(ccelldict, hyp)

    def test_apply_material(self):
        draw_buffer = DrawingBufferPy(10, 10)
        draw_buffer.hard_clear(100.0)

        material_buffer = MaterialBufferPy()
        texture_buffer = TextureBufferPy(32)

        vertex_buffer = VertexBufferPy(128, 128, 128)
        primitive_buffer = PrimitiveBufferPy(3)
        apply_material_py(
            material_buffer,
            texture_buffer,
            vertex_buffer,
            primitive_buffer,
            draw_buffer,
        )

    def test_wh_canvas(self):
        drawbuffer = DrawingBufferPy(max_row=23, max_col=178)
        self.assertEqual(drawbuffer.get_row_count(), 23)
        self.assertEqual(drawbuffer.get_col_count(), 178)

    def test_clear_canvas(self):
        drawbuffer = DrawingBufferPy(512, 512)

        drawbuffer.hard_clear(12.0)

        layer = 0
        v = drawbuffer.get_depth_buffer_cell(0, 0, layer)
        self.assertEqual(
            v,
            {
                "depth": 12.0,
                "pix_info": layer,
                "uv": [0.0, 0.0],
                "uv_1": [0.0, 0.0],
                "frag_pos": [0.0, 0.0],
                "material_id": 0,
                "geometry_id": 0,
                "node_id": 0,
                "primitive_id": 0,
                "front_facing": True,
                "line_coord": 0.0,
                "point_coord": [0.0, 0.0],
            },
        )

        layer = 1
        v = drawbuffer.get_depth_buffer_cell(0, 0, layer)
        self.assertEqual(v, {})

        for pix_idx in range(10 * 10):
            self.assertEqual(
                drawbuffer.get_pix_info_element(pix_idx),
                {
                    "uv": [0.0, 0.0],
                    "uv_1": [0.0, 0.0],
                    "frag_pos": [0.0, 0.0],
                    "primitive_id": 0,
                    "geometry_id": 0,
                    "node_id": 0,
                    "material_id": 0,
                    "normal": [0.0, 0.0, 1.0],
                    "front_facing": True,
                    "line_coord": 0.0,
                    "point_coord": [0.0, 0.0],
                },
            )

        mind, maxd = drawbuffer.get_min_max_depth(0)

        self.assertEqual(mind, 12.0)
        self.assertEqual(maxd, 12.0)

        mind, maxd = drawbuffer.get_min_max_depth(1)
        self.assertEqual(mind, 12.0)
        self.assertEqual(maxd, 12.0)

    def test_set_canvasX(self):
        drawbuffer = DrawingBufferPy(32, 32)

        drawbuffer.hard_clear(10)
        drawbuffer.set_canvas_cell(
            3,
            0,
            [3, 0, 255, 0],
            [
                2,
                3,
                4,
                5,
            ],
            8,
        )

        apix = drawbuffer.get_canvas_cell(0, 0)
        hyp = {"f_r": 0, "f_b": 0, "f_g": 0, "b_r": 0, "b_g": 0, "b_b": 0, "glyph": 0}
        self.assertEqual(apix, hyp)

        canvas_content = drawbuffer.get_canvas_cell(3, 0)
        hyp = {"f_r": 3, "f_b": 255, "f_g": 0, "b_r": 2, "b_g": 3, "b_b": 4, "glyph": 8}
        self.assertEqual(len(canvas_content), 7)
        self.assertEqual(canvas_content, hyp)

    def test_set_canvasY(self):
        drawbuffer = DrawingBufferPy(32, 32)

        drawbuffer.hard_clear(10)
        drawbuffer.set_canvas_cell(
            1,
            3,
            (3, 0, 255, 0),
            [
                2,
                3,
                4,
                5,
            ],
            8,
        )

        apix = drawbuffer.get_canvas_cell(0, 0)
        hyp = {"f_r": 0, "f_b": 0, "f_g": 0, "b_r": 0, "b_g": 0, "b_b": 0, "glyph": 0}
        self.assertEqual(apix, hyp)

        canvas_content = drawbuffer.get_canvas_cell(1, 3)
        hyp = {"f_r": 3, "f_b": 255, "f_g": 0, "b_r": 2, "b_g": 3, "b_b": 4, "glyph": 8}
        self.assertEqual(len(canvas_content), 7)
        self.assertEqual(canvas_content, hyp)

    def test_set_depth(self):
        w, h = 32, 32
        drawbuffer = DrawingBufferPy(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        # setting info in the depth buffer
        primitiv_id = 42
        geom_id = 12
        node_id = 222
        material_id = 3

        inpuut_tuple = [
            glm.vec3(1, 1, 1),
            1.0,  # depth value
            glm.vec2(2, 3),  # uv info
            glm.vec2(5, 6),  # uv info
            node_id,
            geom_id,
            material_id,
            primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple)

        # In the canonical single-layer buffer, the winning sample stays at pix index 0.
        pix_info1 = drawbuffer.get_pix_info_element(0)
        assertPixInfoEqual(
            pix_info1,
            {
                "uv": [2.0, 3.0],
                "uv_1": [5.0, 6.0],
                "primitive_id": primitiv_id,
                "geometry_id": geom_id,
                "node_id": node_id,
                "material_id": material_id,
            },
        )

        # Layer 0 has changed; layer 1 is not exposed in canonical mode.
        db_return = drawbuffer.get_depth_buffer_cell(0, 0, layer=0)
        self.assertEqual(
            db_return,
            {
                "depth": 1.0,
                "pix_info": 0,
                "uv": [2.0, 3.0],
                "uv_1": [5.0, 6.0],
                "frag_pos": _FRAG_POS_NDC_32_R0_C0,
                "primitive_id": primitiv_id,
                "geometry_id": geom_id,
                "node_id": node_id,
                "material_id": material_id,
                "front_facing": True,
                "line_coord": 0.0,
                "point_coord": [0.0, 0.0],
            },
        )

        # no legacy layer-1 view in canonical mode
        db_return_layer1 = drawbuffer.get_depth_buffer_cell(0, 0, layer=1)
        self.assertEqual(db_return_layer1, {})
        mind, maxd = drawbuffer.get_min_max_depth(0)

        self.assertEqual(mind, 1.0)
        self.assertEqual(maxd, 10.0)

        mind, maxd = drawbuffer.get_min_max_depth(1)
        self.assertEqual(mind, 1.0)
        self.assertEqual(maxd, 10.0)

    def test_set_depth_content_frag_pos_matches_cell_center_ndc(self):
        """``frag_pos`` is cell-center NDC (feeds TTSL ``tt_FragPos`` in
        ``ShaderMaterial``)."""
        w, h = 32, 32
        drawbuffer = DrawingBufferPy(w, h)
        drawbuffer.hard_clear(10.0)
        row, col = 0, 0
        payload = [
            glm.vec3(0.0, 0.0, 1.0),
            1.0,
            glm.vec2(0.0, 0.0),
            glm.vec2(0.0, 0.0),
            0,
            0,
            0,
            0,
        ]
        drawbuffer.set_depth_content(row, col, *payload)
        pix = drawbuffer.get_pix_info_element(0)
        half_x = w / 2.0
        half_y = h / 2.0
        sx = 1.0
        sy = -1.0
        cx = col + 0.5
        cy = row + 0.5
        exp_x = (cx / half_x - 1.0) / sx
        exp_y = (cy / half_y - 1.0) / sy
        self.assertAlmostEqual(pix["frag_pos"][0], exp_x, places=5)
        self.assertAlmostEqual(pix["frag_pos"][1], exp_y, places=5)

    def test_set_depth_content_line_coord_kwarg(self):
        drawbuffer = DrawingBufferPy(8, 8)
        drawbuffer.hard_clear(10.0)
        row, col = 0, 0
        payload = [
            glm.vec3(0.0, 0.0, 1.0),
            1.0,
            glm.vec2(0.0, 0.0),
            glm.vec2(0.0, 0.0),
            0,
            0,
            0,
            0,
        ]
        drawbuffer.set_depth_content(row, col, *payload, line_coord=0.375)
        pix = drawbuffer.get_pix_info_element(0)
        self.assertAlmostEqual(pix["line_coord"], 0.375, places=6)

    def test_set_depth_content_point_coord_kwarg(self):
        drawbuffer = DrawingBufferPy(8, 8)
        drawbuffer.hard_clear(10.0)
        row, col = 0, 0
        payload = [
            glm.vec3(0.0, 0.0, 1.0),
            1.0,
            glm.vec2(0.0, 0.0),
            glm.vec2(0.0, 0.0),
            0,
            0,
            0,
            0,
        ]
        pc = glm.vec2(0.25, 0.625)
        drawbuffer.set_depth_content(row, col, *payload, point_coord=pc)
        pix = drawbuffer.get_pix_info_element(0)
        self.assertAlmostEqual(pix["point_coord"][0], 0.25, places=6)
        self.assertAlmostEqual(pix["point_coord"][1], 0.625, places=6)

    def test_set_depth_overwrites_when_closer(self):
        w, h = 32, 32
        drawbuffer = DrawingBufferPy(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        # setting info in the depth buffer
        _0_primitiv_id = 42
        _0_geom_id = 12
        _0_node_id = 222
        _0_material_id = 3

        inpuut_tuple_0 = [
            glm.vec3(1, 1, 1),
            3.0,  # depth value
            glm.vec2(2, 3),
            glm.vec2(5, 6),
            _0_node_id,
            _0_geom_id,
            _0_material_id,
            _0_primitiv_id,
        ]

        # first set at depth 3
        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_0)

        # first write lands in layer 0
        db_return0 = drawbuffer.get_depth_buffer_cell(0, 0, layer=0)
        self.assertEqual(db_return0["pix_info"], 0)
        self.assertEqual(drawbuffer.get_depth_buffer_cell(0, 0, layer=1), {})

        # and here we check that at layer0; the current tuple values
        self.assertEqual(
            db_return0,
            {
                "depth": 3.0,
                "pix_info": 0,
                "uv": [2.0, 3.0],
                "uv_1": [5.0, 6.0],
                "frag_pos": _FRAG_POS_NDC_32_R0_C0,
                "primitive_id": _0_primitiv_id,
                "geometry_id": _0_geom_id,
                "node_id": _0_node_id,
                "material_id": _0_material_id,
                "front_facing": True,
                "line_coord": 0.0,
                "point_coord": [0.0, 0.0],
            },
        )

        # setting AGAIN info in the depth buffer
        _1_primitiv_id = 24
        _1_geom_id = 21
        _1_node_id = 333
        _1_material_id = 1

        inpuut_tuple_1 = [
            glm.vec3(1, 1, 1),
            1.0,  # depth value lower
            glm.vec2(20, 30),
            glm.vec2(50, 60),
            _1_node_id,
            _1_geom_id,
            _1_material_id,
            _1_primitiv_id,
        ]

        # second write is closer (depth 1), so it replaces layer 0
        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_1)

        # layer 0 now contains the newer closer value
        db_return0_second = drawbuffer.get_depth_buffer_cell(0, 0, layer=0)
        self.assertEqual(db_return0_second["pix_info"], 0)
        self.assertEqual(drawbuffer.get_depth_buffer_cell(0, 0, layer=1), {})

        # the layer 0 contains the new values; the one
        self.assertEqual(
            db_return0_second,
            {
                "depth": 1.0,
                "pix_info": 0,
                "uv": [20.0, 30.0],
                "uv_1": [50.0, 60.0],
                "frag_pos": _FRAG_POS_NDC_32_R0_C0,
                "primitive_id": _1_primitiv_id,
                "geometry_id": _1_geom_id,
                "node_id": _1_node_id,
                "material_id": _1_material_id,
                "front_facing": True,
                "line_coord": 0.0,
                "point_coord": [0.0, 0.0],
            },
        )

    def test_set_depth_keeps_closer_sample(self):
        w, h = 32, 32
        drawbuffer = DrawingBufferPy(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        # setting info in the depth buffer
        _0_primitiv_id = 42
        _0_geom_id = 12
        _0_node_id = 222
        _0_material_id = 3

        inpuut_tuple_0 = [
            glm.vec3(1, 1, 1),
            1.0,  # depth value # this one is in front
            glm.vec2(2, 3),
            glm.vec2(5, 6),
            _0_node_id,
            _0_geom_id,
            _0_material_id,
            _0_primitiv_id,
        ]
        # first write is closest
        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_0)

        # layer 0 stores first write
        db_return0 = drawbuffer.get_depth_buffer_cell(0, 0, layer=0)
        self.assertEqual(db_return0["pix_info"], 0)
        self.assertEqual(drawbuffer.get_depth_buffer_cell(0, 0, layer=1), {})

        # and here we check that at layer0; the current tuple values
        self.assertEqual(
            db_return0,
            {
                "depth": 1.0,
                "pix_info": 0,
                "uv": [2.0, 3.0],
                "uv_1": [5.0, 6.0],
                "frag_pos": _FRAG_POS_NDC_32_R0_C0,
                "primitive_id": _0_primitiv_id,
                "geometry_id": _0_geom_id,
                "node_id": _0_node_id,
                "material_id": _0_material_id,
                "front_facing": True,
                "line_coord": 0.0,
                "point_coord": [0.0, 0.0],
            },
        )

        # setting AGAIN info in the depth buffer
        _1_primitiv_id = 24
        _1_geom_id = 21
        _1_node_id = 333
        _1_material_id = 1

        inpuut_tuple_1 = [
            glm.vec3(1, 1, 1),
            3.0,  #  THIS one it in the back
            glm.vec2(20, 30),
            glm.vec2(50, 60),
            _1_node_id,
            _1_geom_id,
            _1_material_id,
            _1_primitiv_id,
        ]

        # second write is farther (depth 3), so existing sample remains
        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_1)

        # layer 0 still points to first write
        db_return0 = drawbuffer.get_depth_buffer_cell(0, 0, layer=0)
        self.assertEqual(db_return0["pix_info"], 0)
        self.assertEqual(drawbuffer.get_depth_buffer_cell(0, 0, layer=1), {})

        db_return = drawbuffer.get_depth_buffer_cell(0, 0, layer=0)
        self.assertEqual(
            db_return,
            {
                "depth": 1.0,
                "pix_info": 0,
                "uv": [2.0, 3.0],
                "uv_1": [5.0, 6.0],
                "frag_pos": _FRAG_POS_NDC_32_R0_C0,
                "primitive_id": _0_primitiv_id,
                "geometry_id": _0_geom_id,
                "node_id": _0_node_id,
                "material_id": _0_material_id,
                "front_facing": True,
                "line_coord": 0.0,
                "point_coord": [0.0, 0.0],
            },
        )

        self.assertEqual(drawbuffer.get_depth_buffer_cell(0, 0, layer=1), {})

    def test_constructor_rejects_legacy_layers_kwarg(self):
        with pytest.raises(TypeError):
            DrawingBufferPy(8, 8, legacy_layers=True)


class Test_totextual(unittest.TestCase):
    def test_to_textual_2(self):
        gb = DrawingBufferPy(max_row=10, max_col=20)
        gb.hard_clear(100.0)
        gb.set_canvas_cell(0, 0, (0, 100, 200, 255), (200, 100, 0, 255), 0)

        gb.set_bit_size_front(8, 8, 8)
        gb.set_bit_size_back(8, 8, 8)

        at00 = gb.get_canvas_cell(0, 0)
        self.assertEqual(
            at00,
            {
                "f_r": 0,
                "f_g": 100,
                "f_b": 200,
                "b_r": 200,
                "b_g": 100,
                "b_b": 0,
                "glyph": 0,
            },
        )

        res = gb.to_textual_2(min_x=0, max_x=20, min_y=0, max_y=10)

        self.assertEqual(len(res), 10)
        self.assertEqual(len(res[0]), 20)

        pix0 = res[0][0]
        self.assertEqual(pix0.text, "!")
        colr = pix0.style.color.triplet

        self.assertEqual(colr.red, 0)
        self.assertEqual(colr.green, 100)
        self.assertEqual(colr.blue, 200)

        res = gb.to_textual_2(min_x=0, max_x=10, min_y=1, max_y=9)
        self.assertEqual(len(res), 8)
        self.assertEqual(len(res[0]), 10)

    def test_to_textual_2_out_bound_x(self):
        gb = DrawingBufferPy(max_row=178, max_col=19)
        gb.hard_clear(100.0)
        gb.set_bit_size_front(8, 8, 8)
        gb.set_bit_size_back(8, 8, 8)

        res = gb.to_textual_2(0, 13, 1, 3)
        self.assertEqual(len(res), 2)
        self.assertEqual(len(res[0]), 13)

        res = gb.to_textual_2(5, 13 + 5, 1, 3)
        self.assertEqual(len(res), 2)
        self.assertEqual(len(res[0]), 13)

        res = gb.to_textual_2(5, 504 + 5, 1, 3)
        self.assertEqual(len(res), 2)
        self.assertEqual(len(res[0]), 504)

        res = gb.to_textual_2(min_x=0, max_x=20, min_y=0, max_y=178)
        self.assertEqual(len(res), 178)
        self.assertEqual(len(res[0]), 20)

    def test_to_textual_2_out_bound_y(self):
        gb = DrawingBufferPy(10, 10)
        gb.hard_clear(100.0)

        res = gb.to_textual_2(0, 3, 1, 30)
        self.assertEqual(len(res), 29)
        self.assertEqual(len(res[0]), 3)

        res = gb.to_textual_2(0, 30, 1, 30)
        self.assertEqual(len(res), 29)
        self.assertEqual(len(res[0]), 30)

    def test_to_textual_2_zero_init(self):
        gb = DrawingBufferPy(max_row=0, max_col=0)

        gb.set_bit_size_front(8, 8, 8)
        gb.set_bit_size_back(8, 8, 8)
        gb.hard_clear(100)
        self.assertEqual(gb.get_col_count(), 0)
        self.assertEqual(gb.get_row_count(), 0)

        res = gb.to_textual_2(min_x=0, max_x=178, min_y=0, max_y=25)

        self.assertEqual(len(res), 25)
        self.assertEqual(len(res[0]), 178)

    def test_to_textual_2_glyph_indices_zero_one_two(self) -> None:
        """
        GLYPH_STATIC_STR[0], [1], [2] must round-trip through ``to_textual_2``.

        Regression guard for reports that glyph index 0 mis-extracts (e.g. black / wrong
        segment) after segment-cache reduction.
        """
        gb = DrawingBufferPy(max_row=1, max_col=3)
        gb.hard_clear(100.0)
        gb.set_bit_size_front(8, 8, 8)
        gb.set_bit_size_back(8, 8, 8)

        # Columns 0..2: glyph indices 0, 1, 2 with distinct non-black foregrounds.
        gb.set_canvas_cell(0, 0, (255, 40, 35, 255), (12, 12, 12, 255), 0)
        gb.set_canvas_cell(0, 1, (35, 255, 45, 255), (24, 24, 24, 255), 1)
        gb.set_canvas_cell(0, 2, (40, 38, 255, 255), (36, 36, 36, 255), 2)

        res = gb.to_textual_2(min_x=0, max_x=3, min_y=0, max_y=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 3)

        # Must match ``src/drawbuffer/glyphset.rs`` GLYPH_STATIC_STR[0..3].
        expected_chars = ("!", " ", "'")
        for i in range(3):
            seg = res[0][i]
            self.assertEqual(
                seg.text,
                expected_chars[i],
                msg=f"glyph index {i} -> Rich Segment text",
            )
            tri = seg.style.color.triplet
            self.assertNotEqual(
                (tri.red, tri.green, tri.blue),
                (0, 0, 0),
                msg=f"glyph index {i}: foreground triplet should not collapse to black",
            )

    def test_to_textual_2_default_bit_depth_unreduces_colors(self) -> None:
        """Without ``set_bit_size_*``, cache uses 4-bit reduction (see ``DrawingBufferPy::new``).

        Colors must be **unreduced** when building Rich segments — never treat reduced
        tuple bytes as 8-bit RGB. Raw black reduces to 0 in each channel; unreduce
        fills low bits so the displayed pair is (15, 15, 15), not (0, 0, 0).
        """
        gb = DrawingBufferPy(max_row=1, max_col=1, material_parallel_threads=0)
        gb.hard_clear(100.0)
        gb.set_canvas_cell(0, 0, (0, 0, 0, 255), (0, 0, 0, 255), 0)

        res = gb.to_textual_2(min_x=0, max_x=1, min_y=0, max_y=1)
        seg = res[0][0]
        self.assertEqual(seg.text, "!")
        self.assertEqual(seg.style.color.triplet.red, 15)
        self.assertEqual(seg.style.color.triplet.green, 15)
        self.assertEqual(seg.style.color.triplet.blue, 15)
        self.assertEqual(seg.style.bgcolor.triplet.red, 15)
        self.assertEqual(seg.style.bgcolor.triplet.green, 15)
        self.assertEqual(seg.style.bgcolor.triplet.blue, 15)

    def test_to_textual_2_same_colors_distinct_glyphs_no_wrong_cache_share(self) -> None:
        """Identical reduced fg/bg must still yield different segments per glyph
        index."""
        gb = DrawingBufferPy(max_row=1, max_col=2, material_parallel_threads=0)
        gb.hard_clear(100.0)
        gb.set_bit_size_front(8, 8, 8)
        gb.set_bit_size_back(8, 8, 8)
        fg = (90, 120, 140, 255)
        bg = (10, 20, 30, 255)
        gb.set_canvas_cell(0, 0, fg, bg, 0)
        gb.set_canvas_cell(0, 1, fg, bg, 1)

        res1 = gb.to_textual_2(0, 2, 0, 1)
        self.assertEqual(res1[0][0].text, "!")
        self.assertEqual(res1[0][1].text, " ")

        res2 = gb.to_textual_2(0, 2, 0, 1)
        self.assertEqual(res2[0][0].text, "!")
        self.assertEqual(res2[0][1].text, " ")

    def test_to_textual_2_second_pass_matches_first(self) -> None:
        """Segment cache reuse must not swap glyphs or colors."""
        gb = DrawingBufferPy(max_row=1, max_col=3, material_parallel_threads=0)
        gb.hard_clear(100.0)
        gb.set_bit_size_front(8, 8, 8)
        gb.set_bit_size_back(8, 8, 8)
        gb.set_canvas_cell(0, 0, (200, 10, 10, 255), (1, 2, 3, 255), 0)
        gb.set_canvas_cell(0, 1, (10, 200, 10, 255), (4, 5, 6, 255), 1)
        gb.set_canvas_cell(0, 2, (10, 10, 200, 255), (7, 8, 9, 255), 2)

        def row_snapshot(lines):
            return tuple(
                (
                    seg.text,
                    seg.style.color.triplet.red,
                    seg.style.color.triplet.green,
                    seg.style.color.triplet.blue,
                )
                for seg in lines[0]
            )

        a = row_snapshot(gb.to_textual_2(0, 3, 0, 1))
        b = row_snapshot(gb.to_textual_2(0, 3, 0, 1))
        self.assertEqual(a, b)
