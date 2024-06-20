import struct
import unittest
import pytest
from tt3de.asset_fastloader import fast_load
from tt3de.richtexture import ImageTexture
import random


from tt3de.glm.drawing.c_drawing_buffer import DrawingBuffer


def drawbuffer_to_pil(drawbuffer: DrawingBuffer, img_name="out.png", layer="front"):
    """

    front,back,glyph
    depth, weights,


    primitiv_id
    geom_id
    node_id
    material_id



    """
    from PIL import Image

    if layer == "depth":
        return _drawbuffer_to_pil_depth(drawbuffer, img_name)
    # Extract the min and max values for x and y
    min_x = 0
    min_y = 0
    max_x, max_y = drawbuffer.shape()

    # Calculate canvas size with extra 10 pixels on each side
    width = (max_x - min_x) + 20
    height = (max_y - min_y) + 20

    # Create a blank white canvas
    canvas = Image.new("RGB", (width, height), "white")

    thelist = drawbuffer.canvas_to_list()
    # Plot each point on the canvas
    for x in range(max_x):
        for y in range(max_y):
            canvas_idx = (x * max_y) + y

            apix = thelist[canvas_idx]
            # Adjust coordinates to account for the offset
            x_img, y_img = x - min_x + 10, y - min_y + 10

            if layer == "front":
                r, g, b = apix[:3]
            if layer == "back":
                r, g, b = apix[3:6]
            elif layer == "glyph":
                r = 0
                g, b = apix[6:]
            elif layer == "weights":
                wa, wb, wc = apix[1:4]
                r, g, b = 0, 0, 0  # TODO
            else:
                r, g, b = apix[:3]
            canvas.putpixel((x_img, y_img), (r, g, b))  # Black pixel

    canvas.save(img_name)


def _drawbuffer_to_pil_depth(drawbuffer: DrawingBuffer, img_name):
    from PIL import Image

    # Extract the min and max values for x and y
    min_x = 0
    min_y = 0
    max_x, max_y = drawbuffer.shape()

    # Calculate canvas size with extra 10 pixels on each side
    width = (max_x - min_x) + 20
    height = (max_y - min_y) + 20

    # Create a blank white canvas
    canvas = Image.new("RGB", (width, height), "white")
    mind, maxd = drawbuffer.get_depth_min_max()

    # Plot each point on the canvas
    for x in range(max_x):
        for y in range(max_y):
            x_img, y_img = x - min_x + 10, y - min_y + 10
            if mind == maxd:
                canvas.putpixel((x_img, y_img), (0, 0, 0))  # Black pixel
            else:
                db_return = drawbuffer.get_depth_buff_content(x, y)
                depth_ratio = abs(db_return["depth_value"] - mind) / (maxd - mind)

                depth_ratio = int(depth_ratio * 254)
                canvas.putpixel(
                    (x_img, y_img), (depth_ratio, depth_ratio, depth_ratio)
                )  # greypixel

    canvas.save(img_name)


class Test_DrawCell(unittest.TestCase):
    def test_create(self):
        drawbuffer = DrawingBuffer(512, 512)

        max_x, max_y = drawbuffer.shape()
        self.assertEqual((512, 512), drawbuffer.shape())

        drawbuffer = DrawingBuffer(48, 23)
        drawbuffer = DrawingBuffer(2, 3)

    def test_clear_canvas(self):
        drawbuffer = DrawingBuffer(512, 512)
        drawbuffer.hard_clear(12.0)
        depth_content = drawbuffer.get_depth_buff_content(0, 0)

        print(depth_content)
        mind, maxd = drawbuffer.get_depth_min_max()

        self.assertEqual(mind, 12.0)
        self.assertEqual(maxd, 12.0)

        canvas_list = drawbuffer.canvas_to_list()
        depthbuffer_list = drawbuffer.drawbuffer_to_list()

        for i in range(512 * 512):
            self.assertEqual(depthbuffer_list[i], [12.0, 0.0, 0.0, 0.0, 0, 0, 0, 0])
            self.assertEqual(canvas_list[i], [0, 0, 0, 0, 0, 0, 0, 0])

    def test_to_list(self):
        w, h = 512, 512
        count = w * h
        drawbuffer = DrawingBuffer(w, h)
        drawbuffer.hard_clear(-32)

        canvas_list = drawbuffer.canvas_to_list()
        self.assertEqual(len(canvas_list), count)

        print(canvas_list[1])

        self.assertEqual(len(canvas_list[0]), 8)

        drawbuffer_list = drawbuffer.drawbuffer_to_list()
        self.assertEqual(len(drawbuffer_list), count)

        self.assertEqual(len(drawbuffer_list[0]), 8)

        acell = drawbuffer_list[0]

        self.assertEqual(acell[0], -32)

    def test_set_canvas(self):
        drawbuffer = DrawingBuffer(32, 32)
        drawbuffer.hard_clear(10)
        drawbuffer.set_canvas_content(0, 0, 255, 2, 3, 4, 5, 6, 7, 8)

        canvas_list = drawbuffer.canvas_to_list()

        apix = canvas_list[0]

        self.assertEqual([255, 2, 3], apix[:3])
        self.assertEqual([4, 5, 6], apix[3:6])
        self.assertEqual([7, 8], apix[6:])

        canvas_content = drawbuffer.get_canvas_content(0, 0)

        self.assertEqual(len(canvas_content), 8)
        self.assertEqual(canvas_content, [255, 2, 3, 4, 5, 6, 7, 8])
        drawbuffer_to_pil(drawbuffer, "set_canvas.png")

    def test_set_canvasX(self):
        drawbuffer = DrawingBuffer(32, 32)
        drawbuffer.hard_clear(10)
        drawbuffer.set_canvas_content(3, 0, 255, 2, 3, 4, 5, 6, 7, 8)

        apix = drawbuffer.get_canvas_content(0, 0)

        self.assertEqual(apix, [0] * 8)

        canvas_content = drawbuffer.get_canvas_content(3, 0)

        self.assertEqual(len(canvas_content), 8)
        self.assertEqual(canvas_content, [255, 2, 3, 4, 5, 6, 7, 8])

        drawbuffer_to_pil(drawbuffer, "set_canvas_x.png")

    def test_set_canvasY(self):
        drawbuffer = DrawingBuffer(32, 32)
        drawbuffer.hard_clear(10)
        drawbuffer.set_canvas_content(0, 3, 255, 2, 3, 4, 5, 6, 7, 8)

        apix = drawbuffer.get_canvas_content(0, 0)

        self.assertEqual(apix, [0] * 8)

        canvas_content = drawbuffer.get_canvas_content(0, 3)

        self.assertEqual(len(canvas_content), 8)
        self.assertEqual(canvas_content, [255, 2, 3, 4, 5, 6, 7, 8])

        # checking that depth is unaffected
        mind, maxd = drawbuffer.get_depth_min_max()
        self.assertEqual(mind, 10.0)
        self.assertEqual(maxd, 10.0)

        drawbuffer_to_pil(drawbuffer, "set_canvas_y.png")

    def test_set_depth(self):
        w, h = 32, 32
        count = w * h
        drawbuffer = DrawingBuffer(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        drawbuffer_list = drawbuffer.drawbuffer_to_list()

        self.assertEqual(len(drawbuffer_list), count)

        adepthelement_list = drawbuffer_list[0]

        self.assertEqual(len(adepthelement_list), 8)
        self.assertEqual(adepthelement_list[0], 10.0)

        # setting info in the depth buffer
        primitiv_id = 42

        geom_id = 12
        node_id = 222
        material_id = 3

        inpuut_tuple = [
            1.0,  # depth value
            2.0,  # weights
            3.0,  #
            4.0,  #

            5.0,
            6.0,
            7.0,
            node_id,
            geom_id,
            material_id,
            primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple)

        db_return = drawbuffer.get_depth_buff_content(0, 0 , layer=0)
        self.assertEqual(
            db_return,
            {
                "depth_value": 1.0,
                "w1": 2.0,
                "w2": 3.0,
                "w3": 4.0,
                "w1_alt": 5.0,
                "w2_alt": 6.0,
                "w3_alt": 7.0,
                "primitiv_id": primitiv_id,
                "geom_id": geom_id,
                "node_id": node_id,
                "material_id": material_id,
            },
        )

        db_return_layer1 = drawbuffer.get_depth_buff_content(0, 0 , layer=1)
        self.assertEqual(
            db_return_layer1,
            {
                "depth_value": 10.0,
                "w1": 0.0,
                "w2": 0.0,
                "w3": 0.0,
                "w1_alt": 0.0,
                "w2_alt": 0.0,
                "w3_alt": 0.0,
                "primitiv_id": 0,
                "geom_id": 0,
                "node_id": 0,
                "material_id": 0,
            },
        )



        mind, maxd = drawbuffer.get_depth_min_max(layer=0)
        self.assertEqual(mind, 1.0)
        self.assertEqual(maxd, 10.0)

        mind, maxd = drawbuffer.get_depth_min_max(layer=1)
        self.assertEqual(mind, 10.0)
        self.assertEqual(maxd, 10.0)


        drawbuffer_to_pil(drawbuffer, img_name="set_depth_00.png", layer="depth")
    def test_set_depth_movelayer(self):
        w, h = 32, 32
        count = w * h
        drawbuffer = DrawingBuffer(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        drawbuffer_list = drawbuffer.drawbuffer_to_list()

        self.assertEqual(len(drawbuffer_list), count)

        adepthelement_list = drawbuffer_list[0]

        self.assertEqual(len(adepthelement_list), 8)
        self.assertEqual(adepthelement_list[0], 10.0)

        # setting info in the depth buffer
        _0_primitiv_id = 42
        _0_geom_id = 12
        _0_node_id = 222
        _0_material_id = 3

        inpuut_tuple_0 = [
            1.0,  # depth value
            2.0,  # weights
            3.0,  #
            4.0,  #

            5.0,
            6.0,
            7.0,
            _0_node_id,
            _0_geom_id,
            _0_material_id,
            _0_primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_0)



        # setting AGAIN info in the depth buffer
        _1_primitiv_id = 24
        _1_geom_id = 21
        _1_node_id = 333
        _1_material_id = 1

        inpuut_tuple_1 = [
            1.0,  # depth value # is same
            20.0,  # weights
            30.0,  #
            40.0,  #

            50.0,
            60.0,
            70.0,
            _1_node_id,
            _1_geom_id,
            _1_material_id,
            _1_primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_1)



        # the layer 0 contains the 0
        db_return = drawbuffer.get_depth_buff_content(0, 0 , layer=0)
        self.assertEqual(
            db_return,
            {
                "depth_value": 1.0,
                "w1": 2.0,
                "w2": 3.0,
                "w3": 4.0,
                "w1_alt": 5.0,
                "w2_alt": 6.0,
                "w3_alt": 7.0,
                "primitiv_id": _0_primitiv_id,
                "geom_id": _0_geom_id,
                "node_id": _0_node_id,
                "material_id": _0_material_id,
            },
            
        )

        # the layer 1 contains the 1 (not moved, just jumped over) 
        db_return_layer1 = drawbuffer.get_depth_buff_content(0, 0 , layer=1)
        self.assertEqual(
            db_return_layer1,
            {
                "depth_value": 1.0,
                "w1": 20.0,
                "w2": 30.0,
                "w3": 40.0,
                "w1_alt": 50.0,
                "w2_alt": 60.0,
                "w3_alt": 70.0,
                "primitiv_id": _1_primitiv_id,
                "geom_id": _1_geom_id,
                "node_id": _1_node_id,
                "material_id": _1_material_id,
            },
        )

    def test_set_depth_movelayer_diffent_depth(self):
        w, h = 32, 32
        count = w * h
        drawbuffer = DrawingBuffer(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        drawbuffer_list = drawbuffer.drawbuffer_to_list()

        self.assertEqual(len(drawbuffer_list), count)

        adepthelement_list = drawbuffer_list[0]

        self.assertEqual(len(adepthelement_list), 8)
        self.assertEqual(adepthelement_list[0], 10.0)

        # setting info in the depth buffer
        primitiv_id = 42
        geom_id = 12
        node_id = 222
        material_id = 3

        inpuut_tuple_0 = [
            3.0,  # depth value
            2.0,  # weights
            3.0,  #
            4.0,  #

            5.0,
            6.0,
            7.0,
            node_id,
            geom_id,
            material_id,
            primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_0)



        # setting AGAIN info in the depth buffer
        primitiv_id = 24
        geom_id = 21
        node_id = 333
        material_id = 1

        inpuut_tuple_1 = [
            1.0,  # depth value # is before the previous one
            20.0,  # weights
            30.0,  #
            40.0,  #

            50.0,
            60.0,
            70.0,
            node_id,
            geom_id,
            material_id,
            primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_1)

        db_return = drawbuffer.get_depth_buff_content(0, 0 , layer=0)
        self.assertEqual(
            db_return,
            {
                "depth_value": 1.0,
                "w1": 20.0,
                "w2": 30.0,
                "w3": 40.0,
                "w1_alt": 50.0,
                "w2_alt": 60.0,
                "w3_alt": 70.0,
                "primitiv_id": 24,
                "geom_id": 21,
                "node_id": 333,
                "material_id": 1,
            },
        )

        db_return_layer1 = drawbuffer.get_depth_buff_content(0, 0 , layer=1)
        self.assertEqual(
            db_return_layer1,
            {
                "depth_value": 3.0,
                "w1": 2.0,
                "w2": 3.0,
                "w3": 4.0,
                "w1_alt": 5.0,
                "w2_alt": 6.0,
                "w3_alt": 7.0,
                "primitiv_id": 42,
                "geom_id": 12,
                "node_id": 222,
                "material_id": 3,
            },
        )

    def test_set_depth_different_depth(self):
        w, h = 32, 32
        count = w * h
        drawbuffer = DrawingBuffer(w, h)

        # setting initial depth buffer to 10
        drawbuffer.hard_clear(10)

        drawbuffer_list = drawbuffer.drawbuffer_to_list()

        self.assertEqual(len(drawbuffer_list), count)

        adepthelement_list = drawbuffer_list[0]

        self.assertEqual(len(adepthelement_list), 8)
        self.assertEqual(adepthelement_list[0], 10.0)

        # setting info in the depth buffer
        primitiv_id = 42
        geom_id = 12
        node_id = 222
        material_id = 3

        inpuut_tuple_0 = [
            1.0,  # depth value # this one is in front
            2.0,  # weights
            3.0,  #
            4.0,  #

            5.0,
            6.0,
            7.0,
            node_id,
            geom_id,
            material_id,
            primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_0)



        # setting AGAIN info in the depth buffer
        primitiv_id = 24
        geom_id = 21
        node_id = 333
        material_id = 1

        inpuut_tuple_1 = [
            3.0,  #  THIS one it in the back
            20.0,  # weights
            30.0,  #
            40.0,  #

            50.0,
            60.0,
            70.0,
            node_id,
            geom_id,
            material_id,
            primitiv_id,
        ]

        drawbuffer.set_depth_content(0, 0, *inpuut_tuple_1)

        db_return = drawbuffer.get_depth_buff_content(0, 0 , layer=0)
        self.assertEqual(
            db_return,
            {
                "depth_value": 1.0,
                "w1": 2.0,
                "w2": 3.0,
                "w3": 4.0,
                "w1_alt": 5.0,
                "w2_alt": 6.0,
                "w3_alt": 7.0,
                "primitiv_id": 42,
                "geom_id": 12,
                "node_id": 222,
                "material_id": 3,
            },
        )

        db_return_layer1 = drawbuffer.get_depth_buff_content(0, 0 , layer=1)
        self.assertEqual(
            db_return_layer1,
            {
                "depth_value": 3.0,
                "w1": 20.0,
                "w2": 30.0,
                "w3": 40.0,
                "w1_alt": 50.0,
                "w2_alt": 60.0,
                "w3_alt": 70.0,
                "primitiv_id": 24,
                "geom_id": 21,
                "node_id": 333,
                "material_id": 1,
            },
        )

def max_hash(bit_reductions):
    """
    Function to predict the maximum hash based on bit reductions.
    
    :param bit_reductions: List of 6 integers representing the number of bits to keep for the first 6 numbers
    :return: Maximum possible integer hash value
    """
    
    return 2**(sum(bit_reductions) + 8)

class Test_DrawingBuffer(unittest.TestCase):
    def test_create_some_hash(self):
        db = DrawingBuffer(64,64)

        db.set_bit_reduction([3]*6)

        self.assertEqual(db.hash_value([4]*8),4)
        self.assertEqual(db.hash_value([127]*8),28760959)
        self.assertEqual(db.hash_value([255]*8),67108863)

    def test_ignore_element6(self):

        db = DrawingBuffer(64,64)
        db.set_bit_reduction([7]*6)

        for i in range(100):
            v = [1,22,33,44,55,66,random.randint(0,255),34]

            self.assertEqual(db.hash_value([4]*8),1082196484)

    def test_max_hash1(self):

        max_hashf = max_hash([1]*6)
        self.assertEqual(max_hashf,16384)

    def test_max_hash2(self):
        max_hashf = max_hash([2]*6)
        self.assertEqual(max_hashf,1048576)


    def test_max_hash3(self):
        max_hashf = max_hash([3]*6)
        self.assertEqual(max_hashf,67108864)
        
    def test_max_hash4(self):

        max_hashf = max_hash([4]*6)
        self.assertEqual(max_hashf,4294967296)
    def test_max_hash5(self):
        max_hashf = max_hash([5]*6)
        self.assertEqual(max_hashf,274877906944)
        
    def test_to_hashed_list(self):
        drawing_buffer = DrawingBuffer(256, 256)
        drawing_buffer.hard_clear(100)
        drawing_buffer.set_bit_reduction([5,5,5,5,5,5])

        chars = ["a","b","c"]
        result = drawing_buffer.canvas_to_list_hashed(0,0,256, 256,dict(),chars)

        self.assertEqual(len(result),256)

        self.assertEqual(len(result[0]),256)

        astrip = result[0]

    def test_to_hashed_list_crop_limits(self):
        drawing_buffer = DrawingBuffer(256, 256)
        drawing_buffer.hard_clear(100)
        drawing_buffer.set_bit_reduction([5,5,5,5,5,5])

        chars = ["a","b","c"]
        result = drawing_buffer.canvas_to_list_hashed(0, 0, 5, 20,dict(),chars)
        self.assertEqual(len(result),20)
        self.assertEqual(len(result[0]),5)

        result = drawing_buffer.canvas_to_list_hashed(5, 5,5, 20,dict(),chars)
        self.assertEqual(len(result),20)
        self.assertEqual(len(result[0]),5)




        result = drawing_buffer.canvas_to_list_hashed(10,11,22, 33,dict(),chars)
        self.assertEqual(len(result[0]),22)
        self.assertEqual(len(result),33)

        astrip = result[0]