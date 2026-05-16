# -*- coding: utf-8 -*-
import math
import os
from pathlib import Path
from time import time

from pyglm import glm

from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Static,
)

from tt3de.obj_loader import load_obj

from tt3de.textual_widget import TT3DFpsView

from tt3de.tt_3dnodes import TT3DNode

_DEMO_DIR = Path(__file__).resolve().parent


class GLMTester(TT3DFpsView):
    def __init__(self):
        super().__init__(
            vertex_buffer_size=4096 * 20,
            geometry_buffer_size=4096 * 2,
            texture_buffer_size=64,
            transform_buffer_size=4096 * 2,
            primitive_buffer_size=4096 * 20,
            use_left_hand_perspective=False,
        )

    def initialize(self):
        self.rc.material_buffer.add_static((200, 10, 10), (50, 50, 50), 0)  # 0

        # create a root 3D node
        self.root3Dnode = TT3DNode()

        obj_file = str(_DEMO_DIR / "Dust" / "Dust.obj")

        polys = load_obj(obj_file, self.rc.texture_buffer, self.rc.material_buffer)

        for poly in polys.all_polygons(True):
            self.root3Dnode.add_child(poly)

        self.root3Dnode.local_transform = glm.rotate(
            math.radians(90), glm.vec3(-1, 0, 0)
        )
        # final append
        self.rc.append_root(self.root3Dnode)

        # setup a time reference, to avoid trigonometry issues
        self.reftime = time()

    def update_step(self, delta_time: float):
        pass


class Content(Static):
    def compose(self) -> ComposeResult:
        yield GLMTester()


class Demo3dView(App):
    DEFAULT_CSS = """
    Content {
        layout: horizontal;
        height: 100%;
    }
    TT3DView {
        height: 100%;
        width: 4fr;

    }

    .someinfo {
        height: 100%;
        width: 1fr;
        border: solid red;
    }

    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Content()


def download_extract(url, dest, folder_name="Dust"):
    import requests
    import zipfile
    import io

    target_obj = os.path.join(dest, folder_name, "Dust.obj")
    if os.path.exists(target_obj):
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://models.spriters-resource.com/",
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    content_type = r.headers.get("Content-Type", "")
    if "zip" not in content_type and not r.content[:4] == b"PK\x03\x04":
        raise RuntimeError(
            f"Download from {url} did not return a zip file "
            f"(Content-Type: {content_type}). "
            "The URL may have changed. Please update the download link."
        )

    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(dest)


download_extract(
    "https://models.spriters-resource.com/media/assets/308/310948.zip?updated=1755502951",
    str(_DEMO_DIR),
)

download_extract(
    "https://models.spriters-resource.com/media/assets/308/310948.zip?updated=1755502951",
    str(_DEMO_DIR),
)

if __name__ == "__main__":
    app = Demo3dView()
    app._disable_tooltips = True
    app.run()
