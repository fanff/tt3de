# -*- coding: utf-8 -*-
import threading
import time
import traceback

from textual import widgets as txw
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widget import Widget

from tt3de.ttsl.compiler import all_passes_compilation

DEFAULT_SHADER_CODE = """\
# Built-in inputs follow the GLSL `gl_*` naming style as `tt_*`.
# See `source/ttsl.md` and `source/ttsl_compiler.md`.

@ttsl(globals={"time": float})
def my_shader(tt_FragCoord: glm.vec2) -> glm.vec3:
    uv: glm.vec2 = tt_TexCoord0
    pulse: float = abs(glm.sin(tt_Time * 1.25))
    if uv.x > uv.y:
        return glm.vec3(uv.x, uv.y, pulse)
    else:
        return glm.vec3(0.0, pulse, 1.0 - pulse)
"""


class EditorPane(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield ControlsPane(id="controls-pane")
            yield txw.TextArea.code_editor(
                DEFAULT_SHADER_CODE, language="python", id="ttsl-editor"
            )


class ControlsPane(Widget):
    def compose(self) -> ComposeResult:
        with Horizontal(id="controls-row"):
            yield txw.Button("Compile", id="compile-btn", variant="success")
            yield txw.Button("Reset", id="reset-btn")
            yield txw.Checkbox("Auto-compile", id="autocompile", value=False)
            yield txw.Static("Status: idle", id="compile-status")


class OutputTabsPane(Widget):
    def compose(self) -> ComposeResult:
        with txw.TabbedContent(initial="render-tab", id="output-tabs"):
            with txw.TabPane("Render", id="render-tab"):
                yield txw.Static(
                    "Render wireframe placeholder\n\n"
                    "+--------------------------+\n"
                    "|                          |\n"
                    "|      future preview      |\n"
                    "|         viewport         |\n"
                    "|                          |\n"
                    "+--------------------------+",
                    classes="output-panel",
                )
            with txw.TabPane("AST", id="ast-tab"):
                yield txw.Static("AST output placeholder", classes="output-panel")
            with txw.TabPane("IR", id="ir-tab"):
                yield txw.Static("IR output placeholder", classes="output-panel")
            with txw.TabPane("Bytecode", id="bytecode-tab"):
                yield txw.Static("Bytecode output placeholder", classes="output-panel")
            with txw.TabPane("Diagnostics", id="diagnostics-tab"):
                yield txw.Log(id="diagnostics-log", highlight=True)
            with txw.TabPane("Variables/Registers", id="symbols-tab"):
                table = txw.DataTable(id="symbols-table")
                table.add_columns("Name", "Type", "Storage")
                table.add_row("tt_FragCoord", "vec2", "input")
                table.add_row("tt_TexCoord0", "vec2", "input")
                table.add_row("tt_Time", "float", "input")
                yield table


class MainLayout(Widget):
    DEFAULT_CSS = """
    MainLayout {
        height: 1fr;
    }

    #top-row {
        height: 1fr;
    }

    #outputs-pane {
        width: 1fr;
        min-width: 45;
        border: round $primary;
        margin-left: 1;
    }

    #editor-pane {
        width: 1fr;
        height: 1fr;
        border: round $accent;
        min-width: 45;
    }

    #controls-pane {
        height: 3;
        border: none;
        padding: 0;
        margin: 0 0 1 0;
    }

    .output-panel {
        height: 1fr;
        border: round $panel;
        padding: 1;
    }

    #ttsl-editor {
        height: 1fr;
    }

    #controls-row {
        height: 3;
        align: left middle;
    }

    #controls-row Button {
        margin-right: 1;
        min-width: 9;
        height: 3;
    }

    #controls-row Checkbox {
        margin-right: 1;
        width: auto;
        height: 3;
    }

    #compile-status {
        color: $text-muted;
        width: 1fr;
        content-align: right middle;
    }

    #diagnostics-log {
        height: 1fr;
    }

    #symbols-table {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="top-row"):
                yield EditorPane(id="editor-pane")
                yield OutputTabsPane(id="outputs-pane")


class TTSLCompilerTesterApp(App):
    TITLE = "TTSL Compiler Shader Tester"
    SUB_TITLE = "Layout scaffold"
    BINDINGS = [
        Binding("ctrl+enter", "compile", "Compile"),
        Binding("ctrl+r", "reset_source", "Reset Source"),
        Binding("a", "show_ast_tab", "AST Tab"),
        Binding("i", "show_ir_tab", "IR Tab"),
        Binding("b", "show_bytecode_tab", "Bytecode Tab"),
        Binding("d", "show_diagnostics_tab", "Diagnostics Tab"),
        Binding("v", "show_variables_tab", "Variables Tab"),
        Binding("e", "focus_editor", "Focus Editor", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._compile_in_progress = False
        self._autocompile_seq = 0

    def compose(self) -> ComposeResult:
        yield txw.Header(show_clock=True)
        yield MainLayout()
        yield txw.Footer()

    def on_mount(self) -> None:
        log = self.query_one("#diagnostics-log", txw.Log)
        log.write_line("Ready. Compiler wiring is intentionally not connected yet.")

    def action_focus_editor(self) -> None:
        self.query_one("#ttsl-editor", txw.TextArea).focus()

    def action_compile(self) -> None:
        log = self.query_one("#diagnostics-log", txw.Log)
        if self._compile_in_progress:
            log.write_line("Compile request ignored: a compilation is already running.")
            return

        source = self.query_one("#ttsl-editor", txw.TextArea).text
        self._compile_in_progress = True
        self.query_one("#compile-status", txw.Static).update("Status: compiling...")
        self._set_output_tab("diagnostics-tab")
        log.write_line("Starting full pipeline compilation in background thread...")
        thread = threading.Thread(
            target=self._run_compile_thread,
            args=(source,),
            name="ttsl-compile-thread",
            daemon=True,
        )
        thread.start()

    def action_reset_source(self) -> None:
        editor = self.query_one("#ttsl-editor", txw.TextArea)
        status = self.query_one("#compile-status", txw.Static)
        log = self.query_one("#diagnostics-log", txw.Log)
        editor.text = DEFAULT_SHADER_CODE
        status.update("Status: source reset")
        log.write_line("Editor reset to default shader source.")

    def _set_output_tab(self, tab_id: str) -> None:
        tabs = self.query_one("#output-tabs", txw.TabbedContent)
        tabs.active = tab_id

    def action_show_ast_tab(self) -> None:
        self._set_output_tab("ast-tab")

    def action_show_ir_tab(self) -> None:
        self._set_output_tab("ir-tab")

    def action_show_bytecode_tab(self) -> None:
        self._set_output_tab("bytecode-tab")

    def action_show_diagnostics_tab(self) -> None:
        self._set_output_tab("diagnostics-tab")

    def action_show_variables_tab(self) -> None:
        self._set_output_tab("symbols-tab")

    def on_button_pressed(self, event: txw.Button.Pressed) -> None:
        if event.button.id == "compile-btn":
            self.action_compile()
        elif event.button.id == "reset-btn":
            self.action_reset_source()

    def on_text_area_changed(self, event: txw.TextArea.Changed) -> None:
        if event.text_area.id != "ttsl-editor":
            return
        checkbox = self.query_one("#autocompile", txw.Checkbox)
        if checkbox.value:
            self._queue_autocompile()

    def _queue_autocompile(self) -> None:
        self._autocompile_seq += 1
        current_seq = self._autocompile_seq
        status = self.query_one("#compile-status", txw.Static)
        status.update("Status: auto-compile queued...")

        def trigger() -> None:
            if current_seq != self._autocompile_seq:
                return
            if self._compile_in_progress:
                status.update("Status: waiting for current compile...")
                self._queue_autocompile()
                return
            self.action_compile()

        self.set_timer(0.45, trigger)

    def _run_compile_thread(self, source: str) -> None:
        start = time.perf_counter()
        try:
            bytecode, _register_settings = all_passes_compilation(
                src=source,
                func_name="my_shader",
                globals_dict={"time": float},
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            self.call_from_thread(
                self._on_compile_success, elapsed_ms, len(bytecode)
            )
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            self.call_from_thread(
                self._on_compile_failure,
                elapsed_ms,
                exc,
                traceback.format_exc(),
            )

    def _on_compile_success(self, elapsed_ms: int, bytecode_size: int) -> None:
        self._compile_in_progress = False
        status = self.query_one("#compile-status", txw.Static)
        log = self.query_one("#diagnostics-log", txw.Log)
        status.update(f"Status: compile OK ({elapsed_ms} ms)")
        log.write_line(
            f"Compilation succeeded in {elapsed_ms} ms. Bytecode size: {bytecode_size} bytes."
        )
        self._set_output_tab("diagnostics-tab")

    def _on_compile_failure(
        self, elapsed_ms: int, exc: Exception, formatted_traceback: str
    ) -> None:
        self._compile_in_progress = False
        status = self.query_one("#compile-status", txw.Static)
        log = self.query_one("#diagnostics-log", txw.Log)
        status.update(f"Status: compile failed ({elapsed_ms} ms)")
        log.write_line(f"Compilation failed in {elapsed_ms} ms: {type(exc).__name__}: {exc}")
        for line in formatted_traceback.strip().splitlines():
            log.write_line(line)
        self._set_output_tab("diagnostics-tab")


if __name__ == "__main__":
    TTSLCompilerTesterApp().run()
