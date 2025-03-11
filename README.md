# TinyTiny 3D Engine

A minimalistic 2D/3D engine implemented in Rust and bound to Python, designed to render 3D objects using ASCII art.

## Features

* **Rendering Primitives**: Supports points, lines, and triangles in both 2D and 3D contexts.
* **ASCII Output**: Renders 3D scenes in a charming ASCII art style.
* **Color Shading Support**: Renders with RGB colors.
* **Materials**: Supports 14 materials, including:
    * **Texture Mapping**: Supports textures up to 256x256 pixels.
    * **Double Raster**: Allows the use of 2 colors per ASCII character (background and foreground).
    * **Perlin Noise**: Basic Perlin noise mapped texture.

## Recommended Terminals :

| Terminal              | Windows                      | macOS                | Linux                |
|-----------------------|------------------------------|----------------------|----------------------|
| wez Terminal          | :star: :star: :star:          |                      |                      |
| tabby                 | :star:                        |                      |                      |
| default Windows Terminal | :x:                        |                      |                      |
| VScode terminal       | :x: :x: :x:                 | :x:                    | :x:                   |
| gostty                |                               | :star: :star: :star: | :star: :star: :star: |
| kitty                 |                              | :star: :star:          | :star: :star:        |
| iTerm/iTerm2          |                              | :x:                  | :x:                   |


## Setting Up the Development Version

To set up a development version of this engine:

1. Clone this repository:
    ```bash
    git clone <repo_url>
    ```
2. If you have Poetry, run:
    ```bash
    poetry install --with dev --no-root
    ```
   This will set up the dependencies.
3. If you don't have Poetry, follow these steps:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install poetry
    # Now you have Poetry in the virtual environment
    poetry install
    ```
4. Compile the Rust version locally:

    ```bash
    poetry run maturin develop --profile release
    ```
5. Check the demo:
    ```bash
    PYTHONPATH=python poetry run python demos/3d/some_models.py
    ```

6. Run the Rust unit tests:
    ```bash
    cargo test
    ```
7. Run the Python unit tests:
    ```bash
    poetry run pytest
    ```



### Tips for Python Path in VSCode

Due to the mix of Python and Rust in this project, the Python code is located in the `python` folder. More information can be found [here](https://www.maturin.rs/project_layout#mixed-rustpython-project).

In `launch.json` for VSCode:

```json
"env": {"PYTHONPATH": "${workspaceFolder}/python"}
```

In `settings.json`:

```json
{
    "python.analysis.extraPaths": [
        "python"
    ]
}
```

### Known Issues

* Many...
