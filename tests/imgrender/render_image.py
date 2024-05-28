


import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import tt3de

from tt3de.asset_fastloader import fast_load
from tt3de.glm.pyglmtexture import GLMCamera, GLMMesh3D, GLMRenderContext
from tt3de.richtexture import ImageTexture, RenderContext, Segmap, StaticTexture, get_cube_vertices
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Point3D, PointElem, Triangle3D
from glm import vec3

import math

from PIL import Image, ImageDraw, ImageFont


def main():
    WIDTH = 300
    HEIGHT = 80


    


    # Step 1: Create a new image (white background, 800x400 pixels)
    image = Image.new('RGB', (128, 128), color = (255, 255, 255))

    # Step 2: Initialize the drawing context
    draw = ImageDraw.Draw(image)

    # Step 3: Load a custom font (make sure you have the font file in the same directory or provide the full path)
    font_path =os.path.dirname(__file__)+os.sep+"SpaceMono-Regular.ttf"
    font_path =os.sep.join((os.path.dirname(__file__),"fonts","0xprotofont","0xProtoNerdFontMono-Regular.ttf"))
    print(font_path)
    
    

    # Step 4: Define the text and position
    text = "▞▓▒░█░▒▓▚\nTHE QUICK|BROWN FOX\n JUMPS \nOVER THE \nLAZY█DOG\n 1234567890"


    bgcolor = (0, 0, 0) 
    text_color = (255, 0, 255)
    
    #font_size = 12
    #yshift = 17
    #xshift = 9

    font_size = 14
    yshift = 20
    xshift = 10
    

    font_size = 24
    yshift = 34
    xshift = 18



    posxstart = 10
    posy = 2


    font = ImageFont.truetype(font_path, font_size)


    posx = posxstart
    for c in text:
        if c =="\n":
            posy+=yshift
            posx = posxstart
        else:
            bgy = posy
            draw.rectangle(((posx,bgy),(posx+xshift-2,bgy+yshift-2)),fill=bgcolor)
            draw.text((posx,posy), c , font=font, fill=text_color)
            posx+=xshift
    # Step 6: Save the image
    output_path = "output_image.png"
    image.save(output_path)
if __name__ == '__main__':

    main()
