.. tt3de documentation master file, created by
   sphinx-quickstart on Thu Mar 13 19:54:49 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tt3de documentation
===================



Main Buffer usage
=================


Here are the details on every buffer used in the 3D engine :

Transform Buffer : store the 3D transformation for every every objects in the scene as well as the Camera perspective & transformation

Gometry buffer : store the 3D geometry objects (Polygon, PolygonFan, Line, Point, etc.) vertex and attributes like uv coordinates.

Primitive Buffer : store the 2D objects primitive after the projection onto the screen (Triangle, Line, Point)


Texture Buffer : store the 2D texture to map onto the 3D geometry objects

Material Buffer : store the material information, this define how the 3D geometry objects will be rendered (flat color, texture, etc.)




.. toctree::
   :maxdepth: 2
   :caption: Contents:
