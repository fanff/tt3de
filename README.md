



# TinyTiny 3d Engine 

A minimalistic 3D engine implemented entirely in Python, designed to render 3D objects using ASCII art.

# Features

* *Pure Python Implementation*: No external dependencies, making it easy to understand and extend.
* *Rendering Primitives*: Supports points, lines, and triangles.
* *ASCII Output*: Renders the 3D scenes in a charming ASCII art style.
* *Color Shading support*: Render with RGB colors and Shading level.

# Usage

Here’s a basic example to get you started:

```python

    from engine import Tiny3DEngine

    engine = Tiny3DEngine()

    # Define some points
    points = [
        (0, 0, 0),
        (1, 0, 0),
        (1, 1, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 0, 1),
        (1, 1, 1),
        (0, 1, 1),
    ]

    # Define some lines
    lines = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # bottom square
        (4, 5), (5, 6), (6, 7), (7, 4),  # top square
        (0, 4), (1, 5), (2, 6), (3, 7)   # vertical lines
    ]

    # Render the lines
    engine.render_lines(points, lines)
```

## Known issues 


* [ ] the line distance calculation is buggy for pure vertical lines
* [ ] triangle selection when drawing is too restrictive.
* [ ] triangle front/back culling 

