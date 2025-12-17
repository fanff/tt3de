# -*- coding: utf-8 -*-
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual import widgets as txw
from textual.containers import Container
from rich.text import Text
from textual.binding import Binding

default_shader_code = """\

# this is the default shader code.

@ttsl(globals={"time": float, "position": glm.vec3})
def my_shader(pos: glm.vec2) -> glm.vec3:
    # accessing variables coming from the fragment:
    uv0: glm.vec2 = ttsl_uv0
    uv1: glm.vec2 = ttsl_uv1

    if uv0.x < 0.5:
        return glm.vec3(1.0, -2.0, 0.0)
    else:
        return glm.vec3(
            abs(glm.sin(pos.x * 10.0 + ttsl_time / 2.0)),
            abs(glm.sin(pos.y * 10.0 + ttsl_time / 2.0)),
            0.5,
        )

"""


class TTSLEditor(Widget):
    DEFAULT_CSS = """
    TTSLEditor {
        height: 1fr;
        border: solid green;
    }
    """

    def compose(self) -> ComposeResult:
        yield txw.TextArea()

    def on_mount(self) -> None:
        self.border_title = Text("TTSL Editor")
        self.query_one(txw.TextArea).text = default_shader_code

    def _compile(self) -> None:
        pass


class TTSLAssemblyViewer(Widget):
    DEFAULT_CSS = """
    TTSLAssemblyViewer {
        height: 1fr;

        layout: horizontal;
        border: solid green;
    }

    # Limit size of text area

    .assembly-viewer {
        width: 70%;
    }
    TTSLAssemblyViewer > TTSLNamedVariables {
        width: 30%;
    }
    """

    def compose(self) -> ComposeResult:
        yield TTSLNamedVariables()
        yield Widget(classes="assembly-viewer")

    def on_mount(self) -> None:
        self.border_title = "TTSL Assembly"


class TTSLNamedVariables(Widget):
    DEFAULT_CSS = """
    TTSLNamedVariables {
        border: solid blue;
    }
    """

    def compose(self) -> ComposeResult:
        yield txw.Label("variables tables", shrink=True)


class MainPage(Container):
    DEFAULT_CSS = """
    MainPage {
        height: 1fr;
        border: solid green;
    }
    TTSLEditor {
        width: 1fr;
    }
    TTSLAssemblyViewer {
        width: 2fr;
        width: 1fr;
    }

    """

    def compose(self) -> ComposeResult:
        yield TTSLEditor()
        yield TTSLAssemblyViewer()


class TTSLCompilerTesterApp(App):
    BINDINGS = [
        # Cursor movement
        Binding("e", "focus_editor", "Focus Editor", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield txw.Header()
        yield MainPage()
        yield txw.Footer()

    def action_focus_editor(self) -> None:
        self.query_one(TTSLEditor).focus()


if __name__ == "__main__":
    app = TTSLCompilerTesterApp()
    app.run()
