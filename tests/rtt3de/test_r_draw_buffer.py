

import unittest
from rtt3de import AbigDrawing
import pytest
from rtt3de import apply_material_py
from rtt3de import MaterialBufferPy,TextureBufferPy
import glm 
from rtt3de import VertexBufferPy,TransformPackPy
from rtt3de import PrimitiveBufferPy


class Test_DrawBuffer(unittest.TestCase):
    

    def test_create16(self):
        from rtt3de import Small16Drawing
        gb = Small16Drawing()

        gb.hard_clear(1000.0)
#
        self.assertEqual(gb.get_at(0,0,0),1000.0)
        self.assertEqual(gb.get_at(0,0,1),1000.0)
#
        gb.hard_clear(10.0)
#
        self.assertEqual(gb.get_at(1,1,0),10.0)
        self.assertEqual(gb.get_at(1,1,1),10.0)

    def test_create_verybig(self):
        from rtt3de import AbigDrawing

        gb = AbigDrawing(10,10)

        layer = 0
        v =gb.get_depth_buffer_cell(0,0,layer)
        self.assertEqual(v,{"depth":10.0,
                            "pix_info":  layer,
                            "uv":   [0.0,0.0],
                            "uv_1": [0.0,0.0],
                            "material_id":0,
                            "geometry_id":0,
                            "node_id":0,
                            "primitive_id":0})
        
        layer = 1
        v =gb.get_depth_buffer_cell(0,0,layer)
        self.assertEqual(v,{"depth":10.0,
                            "pix_info":  layer,
                            "uv":   [0.0,0.0],
                            "uv_1": [0.0,0.0],
                            "material_id":0,
                            "geometry_id":0,
                            "node_id":0,
                            "primitive_id":0})
        
        for pix_idx in range(10*10*2):
            self.assertEqual(
                gb.get_pix_info_element(pix_idx),
                {
                    "uv":   [0.0,0.0],
                    "uv_1": [0.0,0.0],
                    "primitive_id": 0,
                    "geometry_id": 0,
                    "node_id": 0,
                    "material_id": 0,
                },
            )


        ccelldict =gb.get_canvas_cell(0,0)

        self.assertEqual(len(ccelldict),7)

        hyp = {
           "f_r":0, 
            "f_b":0, 
            "f_g":0, 
            "b_r":0, 
            "b_g":0, 
            "b_b":0, 
            "glyph":0
        }
        self.assertEqual(ccelldict,hyp)
    def test_apply_material(self):
        
        

        draw_buffer = AbigDrawing(10,10)
        draw_buffer.hard_clear(100.0)

        material_buffer = MaterialBufferPy()
        texture_buffer = TextureBufferPy(32)

        vertex_buffer = VertexBufferPy()
        primitive_buffer = PrimitiveBufferPy(3)
        apply_material_py(material_buffer,texture_buffer,vertex_buffer,primitive_buffer,draw_buffer)

    def test_wh_canvas(self):
        drawbuffer = AbigDrawing(max_row=23, max_col=178)
        self.assertEqual(drawbuffer.get_row_count(),23)
        self.assertEqual(drawbuffer.get_col_count(),178)

    def test_clear_canvas(self):
        drawbuffer = AbigDrawing(512, 512)

        drawbuffer.hard_clear(12.0)

        layer = 0
        v =drawbuffer.get_depth_buffer_cell(0,0,layer)
        self.assertEqual(v,{"depth":12.0,
                            "pix_info":  layer,
                            "w":   [0.0,0.0,0.0],
                            "w_1": [0.0,0.0,0.0],
                            "material_id":0,
                            "geometry_id":0,
                            "node_id":0,
                            "primitive_id":0})
        
        layer = 1
        v =drawbuffer.get_depth_buffer_cell(0,0,layer)
        self.assertEqual(v,{"depth":12.0,
                            "pix_info":  layer,
                            "w":   [0.0,0.0,0.0],
                            "w_1": [0.0,0.0,0.0],
                            "material_id":0,
                            "geometry_id":0,
                            "node_id":0,
                            "primitive_id":0})
        
        for pix_idx in range(10*10*2):
            self.assertEqual(
                drawbuffer.get_pix_info_element(pix_idx),
                {
                    "w":   [0.0,0.0,0.0],
                    "w_1": [0.0,0.0,0.0],
                    "primitive_id": 0,
                    "geometry_id": 0,
                    "node_id": 0,
                    "material_id": 0,
                },
            )


        
        mind, maxd = drawbuffer.get_min_max_depth(0)

        self.assertEqual(mind, 12.0)
        self.assertEqual(maxd, 12.0)

        mind, maxd = drawbuffer.get_min_max_depth(1)

        self.assertEqual(mind, 12.0)
        self.assertEqual(maxd, 12.0)



    def test_set_canvasX(self):

        drawbuffer = AbigDrawing(32, 32)

        drawbuffer.hard_clear(10)
        drawbuffer.set_canvas_cell(3,0,[3, 0, 255,0], [2, 3, 4, 5,] ,8)

        apix = drawbuffer.get_canvas_cell(0, 0)
        hyp = {
            "f_r":0, 
            "f_b":0, 
            "f_g":0, 
            "b_r":0, 
            "b_g":0, 
            "b_b":0, 
            "glyph":0
        }
        self.assertEqual(apix, hyp)

        canvas_content = drawbuffer.get_canvas_cell(3, 0)
        hyp = {
            "f_r":3, 
            "f_b":255, 
            "f_g":0, 
            "b_r":2, 
            "b_g":3, 
            "b_b":4, 
            "glyph":8
        }
        self.assertEqual(len(canvas_content), 7)
        self.assertEqual(canvas_content, hyp)


    def test_set_canvasY(self):
        drawbuffer = AbigDrawing(32, 32)

        drawbuffer.hard_clear(10)
        drawbuffer.set_canvas_cell(1,3,(3, 0, 255,0), [2, 3, 4, 5,] ,8)

        apix = drawbuffer.get_canvas_cell(0, 0)
        hyp = {
            "f_r":0, 
            "f_b":0, 
            "f_g":0, 
            "b_r":0, 
            "b_g":0, 
            "b_b":0, 
            "glyph":0
        }
        self.assertEqual(apix, hyp)

        canvas_content = drawbuffer.get_canvas_cell(1,3)
        hyp = {
            "f_r":3, 
            "f_b":255, 
            "f_g":0, 
            "b_r":2, 
            "b_g":3, 
            "b_b":4, 
            "glyph":8
        }
        self.assertEqual(len(canvas_content), 7)
        self.assertEqual(canvas_content, hyp)


    def test_set_depth(self):
        w, h = 32, 32
        drawbuffer = AbigDrawing(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        # setting info in the depth buffer
        primitiv_id = 42
        geom_id = 12
        node_id = 222
        material_id = 3

        inpuut_tuple = [
            1.0,  # depth value
            glm.vec3(2,3,4),
            glm.vec3(5,6,7),
            node_id,
            geom_id,
            material_id,
            primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple)
        

        ### since we set depth at 0 0 ; the pixel idx 0 is moved to back
        ### therefore we "rolled" the buffer and put ourself in the index 1.
        pix_info1 = drawbuffer.get_pix_info_element(1)
        self.assertEqual(
            pix_info1,
            {
                "w":   [2.0,3.0,4.0],
                "w_1": [5.0,6.0,7.0],
                "primitive_id": primitiv_id,
                "geometry_id": geom_id,
                "node_id": node_id,
                "material_id": material_id,
            },
        )

        # this one is actually the one that was before me :)
        pix_info0 = drawbuffer.get_pix_info_element(0)
        self.assertEqual(
            pix_info0,
            {
                "w":   [0.0,0.0,0.0],
                "w_1": [0.0,0.0,0.0],
                "primitive_id": 0,
                "geometry_id": 0,
                "node_id": 0,
                "material_id": 0,
            },
        )

        # Layer 0 has changed, and Layer 1 has not; 
        # at layer 0; we have pix_info 1
        db_return = drawbuffer.get_depth_buffer_cell(0, 0 , layer=0)
        self.assertEqual(
            db_return,
            {
                "depth": 1.0,
                'pix_info': 1,
                "w":   [2.0,3.0,4.0],
                "w_1": [5.0,6.0,7.0],
                "primitive_id": primitiv_id,
                "geometry_id": geom_id,
                "node_id": node_id,
                "material_id": material_id,
            },
        )


        # at layer 1; we have pix_info 0
        db_return_layer1 = drawbuffer.get_depth_buffer_cell(0, 0 , layer=1)
        self.assertEqual(
            db_return_layer1,
            {
                "depth": 10.0,
                'pix_info': 0,
                "w":   [0.0,0.0,0.0],
                "w_1": [0.0,0.0,0.0],
                "primitive_id": 0,
                "geometry_id": 0,
                "node_id": 0,
                "material_id": 0,
            },
        )
        mind, maxd = drawbuffer.get_min_max_depth(layer=0)

        self.assertEqual(mind, 1.0)
        self.assertEqual(maxd, 10.0)

        mind, maxd = drawbuffer.get_min_max_depth(layer=1)
        self.assertEqual(mind, 10.0)
        self.assertEqual(maxd, 10.0)


    def test_set_depth_movelayer_diffent_depth(self):
        w, h = 32, 32
        drawbuffer = AbigDrawing(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        # setting info in the depth buffer
        _0_primitiv_id = 42
        _0_geom_id = 12
        _0_node_id = 222
        _0_material_id = 3

        inpuut_tuple_0 = [
            3.0,  # depth value
            glm.vec3(2,3,4),
            glm.vec3(5,6,7),
            _0_node_id,
            _0_geom_id,
            _0_material_id,
            _0_primitiv_id,
        ]

        # we set at 3; this will be in layer 0, 1 is at 10
        # this will create a roll operation, rolling the pix_info
        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_0)


        # we check here the rolling operation
        db_return0 = drawbuffer.get_depth_buffer_cell(0, 0 , layer=0)
        self.assertEqual(
            db_return0["pix_info"],1)
        db_return1 = drawbuffer.get_depth_buffer_cell(0, 0 , layer=1)
        self.assertEqual(
            db_return1["pix_info"],0)
        
        # and here we check that at layer0; the current tuple values
        self.assertEqual(
            db_return0,
            {
                "depth": 3.0, 
                "pix_info": 1, 
                "w":   [2.0,3.0,4.0],
                "w_1": [5.0,6.0,7.0],
                "primitive_id": _0_primitiv_id,
                "geometry_id": _0_geom_id,
                "node_id": _0_node_id,
                "material_id": _0_material_id,
            },
            
        )


        # setting AGAIN info in the depth buffer
        _1_primitiv_id = 24
        _1_geom_id = 21
        _1_node_id = 333
        _1_material_id = 1

        inpuut_tuple_1 = [
            1.0,  # depth value lower
            glm.vec3(20,30,40),
            glm.vec3(50,60,70),
            _1_node_id,
            _1_geom_id,
            _1_material_id,
            _1_primitiv_id,
        ]

        # After this, layer 0 is at 1.0 and layer 1 at 3.0; 
        # we operated the rolling operation once more
        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_1)

        # we check here the rolling operation once again, 
        db_return0_second = drawbuffer.get_depth_buffer_cell(0, 0 , layer=0)
        self.assertEqual(
            db_return0_second["pix_info"],0)
        db_return1_second = drawbuffer.get_depth_buffer_cell(0, 0 , layer=1)
        self.assertEqual(
            db_return1_second["pix_info"],1)



        # the layer 0 contains the new values; the one
        self.assertEqual(
            db_return0_second,
            {
                "depth": 1.0, 
                "pix_info": 0, 
                "w":   [20.0,30.0,40.0],
                "w_1": [50.0,60.0,70.0],
                "primitive_id": _1_primitiv_id,
                "geometry_id": _1_geom_id,
                "node_id": _1_node_id,
                "material_id": _1_material_id,
                
            },
            
        )

        # the layer 1 contains the bellow this, at depth 3
        # we just set the value on the layer 1; leaving 0 untouched.
        self.assertEqual(
            db_return1_second,
            {
                "depth": 3.0,
                "pix_info": 1, 
                "w":   [2.0,3.0,4.0],
                "w_1": [5.0,6.0,7.0],
                "primitive_id": _0_primitiv_id,
                "geometry_id": _0_geom_id,
                "node_id": _0_node_id,
                "material_id": _0_material_id,
            },
        )

    def test_set_depth_different_depth(self):
        w, h = 32, 32
        drawbuffer = AbigDrawing(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        # setting info in the depth buffer
        _0_primitiv_id = 42
        _0_geom_id = 12
        _0_node_id = 222
        _0_material_id = 3

        inpuut_tuple_0 = [
            1.0,  # depth value # this one is in front
            glm.vec3(2,3,4),
            glm.vec3(5,6,7),
            _0_node_id,
            _0_geom_id,
            _0_material_id,
            _0_primitiv_id,
        ]
        # setting at 0,0  the value; 
        # since this is lower than the current layer; this will create a roll operation
        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_0)

        # we check here the rolling operation
        db_return0 = drawbuffer.get_depth_buffer_cell(0, 0 , layer=0)
        self.assertEqual(
            db_return0["pix_info"],1)
        db_return1 = drawbuffer.get_depth_buffer_cell(0, 0 , layer=1)
        self.assertEqual(
            db_return1["pix_info"],0)
        
        # and here we check that at layer0; the current tuple values
        self.assertEqual(
            db_return0,
            {
                "depth": 1.0, 
                "pix_info": 1, 
                "w":   [2.0,3.0,4.0],
                "w_1": [5.0,6.0,7.0],
                "primitive_id": _0_primitiv_id,
                "geometry_id":  _0_geom_id,
                "node_id":      _0_node_id,
                "material_id":  _0_material_id,
            },
            
        )

        # setting AGAIN info in the depth buffer
        _1_primitiv_id = 24
        _1_geom_id = 21
        _1_node_id = 333
        _1_material_id = 1

        inpuut_tuple_1 = [
            3.0,  #  THIS one it in the back
            glm.vec3(20,30,40),
            glm.vec3(50,60,70),
            _1_node_id,
            _1_geom_id,
            _1_material_id,
            _1_primitiv_id,
        ]


        # We set; but, its after the existing point .
        # so; there is no rolling operation with the layer0
        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_1)
        
        
        # we check here the rolling operation has not changed since the last insert
        db_return0 = drawbuffer.get_depth_buffer_cell(0, 0 , layer=0)
        self.assertEqual(
            db_return0["pix_info"],1)
        db_return1 = drawbuffer.get_depth_buffer_cell(0, 0 , layer=1)
        self.assertEqual(
            db_return1["pix_info"],0)
        


        db_return = drawbuffer.get_depth_buffer_cell(0, 0 , layer=0)
        self.assertEqual(
            db_return,
            {
                "depth": 1.0,
                "pix_info": 1, 
                "w":   [2.0,3.0,4.0],
                "w_1": [5.0,6.0,7.0],
                "primitive_id": _0_primitiv_id,
                "geometry_id":  _0_geom_id,
                "node_id":      _0_node_id,
                "material_id":  _0_material_id,
            },
        )

        db_return_layer1 = drawbuffer.get_depth_buffer_cell(0, 0 , layer=1)
        self.assertEqual(
            db_return_layer1,
            {
                "depth": 3.0,
                "pix_info": 0, 
                "w":   [20.0,30.0,40.0],
                "w_1": [50.0,60.0,70.0],
                "primitive_id": _1_primitiv_id,
                "geometry_id":     _1_geom_id,
                "node_id":     _1_node_id,
                "material_id": _1_material_id,            
                },
        )


class Test_totextual(unittest.TestCase):
    
    def test_to_textual_2(self):
        from rtt3de import AbigDrawing
        gb = AbigDrawing(max_row=10,max_col=20)
        gb.hard_clear(100.0)    
        gb.set_canvas_cell(0,0,(0,100,200,255),(200,100,0,255),1)

        gb.set_bit_size_front(8,8,8)
        gb.set_bit_size_back(8,8,8)
        
        at00 = gb.get_canvas_cell(0,0)
        self.assertEqual( at00 , {
            "f_r":0, 
            "f_g":100, 
            "f_b":200, 
            "b_r":200, 
            "b_g":100, 
            "b_b":0, 
            "glyph":1
        })

        
        res = gb.to_textual_2(min_x=0,max_x=20,  min_y=0,max_y=10)


        self.assertEqual(len(res),10)
        self.assertEqual(len(res[0]),20)


        pix0 = res[0][0]
        self.assertEqual(pix0.text,"!")
        colr = pix0.style.color.triplet

        self.assertEqual(colr.red,0)
        self.assertEqual(colr.green,100)
        self.assertEqual(colr.blue,200)
        

        res = gb.to_textual_2(min_x=0,max_x=10,  min_y=1,max_y=9)
        self.assertEqual(len(res),8)
        self.assertEqual(len(res[0]),10)


    def test_to_textual_2_out_bound_x(self):
        from rtt3de import AbigDrawing
        gb = AbigDrawing(max_row=178,max_col=19)
        gb.hard_clear(100.0)    
        gb.set_bit_size_front(8,8,8)
        gb.set_bit_size_back(8,8,8)

        res = gb.to_textual_2(0,13,1,3)
        self.assertEqual(len(res),2)
        self.assertEqual(len(res[0]),13)


        res = gb.to_textual_2(5,13+5,1,3)
        self.assertEqual(len(res),2)
        self.assertEqual(len(res[0]),13)



        res = gb.to_textual_2(5,504+5,1,3)
        self.assertEqual(len(res),2)
        self.assertEqual(len(res[0]),504)


        res = gb.to_textual_2(min_x=0,max_x=20, min_y=0,max_y=178)
        self.assertEqual(len(res),178)
        self.assertEqual(len(res[0]),20)


    def test_to_textual_2_out_bound_y(self):
        from rtt3de import AbigDrawing
        gb = AbigDrawing(10,10)
        gb.hard_clear(100.0)    

        
        res = gb.to_textual_2(0,3,1,30)
        self.assertEqual(len(res),29)
        self.assertEqual(len(res[0]),3)



        res = gb.to_textual_2(0,30,1,30)
        self.assertEqual(len(res),29)
        self.assertEqual(len(res[0]),30)    

    def test_to_textual_2_zero_init(self):
        
        gb = AbigDrawing(max_row=0,  max_col=0)

        gb.set_bit_size_front(8,8,8)
        gb.set_bit_size_back(8,8,8)
        gb.hard_clear(100)
        self.assertEqual(gb.get_col_count(),0)
        self.assertEqual(gb.get_row_count(),0)

        res = gb.to_textual_2(min_x=0,max_x=178, min_y=0,max_y=25)


        self.assertEqual(len(res),25)
        self.assertEqual(len(res[0]),178)   


