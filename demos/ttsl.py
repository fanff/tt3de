# -*- coding: utf-8 -*-
import asyncio
import ast
import time
import traceback
from typing import Any

from textual import widgets as txw
from textual import work
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.worker import Worker, WorkerState
from rich.syntax import Syntax

from tt3de.ttsl.compiler import (
    GLOBAL_VAR_TT_TIME,
    CompilationStateResult,
    all_passes_compilation_with_state,
)
from tt3de.ttsl.ttsl_assembly import IRType, OpCodes, Temp

DEFAULT_SHADER_CODE = """\
# Built-in inputs follow the GLSL `gl_*` naming style as `tt_*`.
# See `source/ttsl.md` and `source/ttsl_compiler.md`.
# Shaders return (front_rgb, back_rgb, glyph_index).

def my_shader(tt_FragCoord: glm.vec2) -> tuple[glm.vec3, glm.vec3, int]:
    uv: glm.vec2 = tt_TexCoord0
    pulse: float = abs(glm.sin(tt_Time * 1.25))
    if uv.x > uv.y:
        return (
            glm.vec3(uv.x, uv.y, pulse),
            glm.vec3(uv.x, uv.y, pulse),
            0,
        )
    else:
        return (
            glm.vec3(0.0, pulse, 1.0 - pulse),
            glm.vec3(0.0, pulse, 1.0 - pulse),
            0,
        )
"""


class EditorPane(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield ControlsPane(id="controls-pane")
            yield txw.TextArea.code_editor(
                DEFAULT_SHADER_CODE,
                language="python",
                theme="dracula",
                id="ttsl-editor",
            )


class ControlsPane(Widget):
    def compose(self) -> ComposeResult:
        with Horizontal(id="controls-row"):
            yield txw.Button(
                "Compile",
                id="compile-btn",
                variant="success",
                compact=True,
                classes="-textual-compact",
            )
            yield txw.Button(
                "Reset", id="reset-btn", compact=True, classes="-textual-compact"
            )
            yield txw.Checkbox("Auto-compile", id="autocompile", 
            value=False,
            compact=True,
            classes="-textual-compact",
            )
            yield txw.Static("Status: idle", id="compile-status")


class OutputTabsPane(Widget, can_focus=False):
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
                with VerticalScroll(id="ast-scroll", classes="output-panel"):
                    yield txw.Static("", id="ast-output", markup=False)
            with txw.TabPane("IR", id="ir-tab"):
                with VerticalScroll(id="ir-vscroll", classes="output-panel"):
                    with Vertical(id="ir-content"):
                        yield txw.Static("Variables", classes="ir-section-title")
                        yield txw.DataTable(
                            id="ir-variables-table", classes="ir-table"
                        )
                        yield txw.Static("Constant Pool", classes="ir-section-title")
                        yield txw.DataTable(id="ir-const-table", classes="ir-table")
                        yield txw.Static("CFG Arcs", classes="ir-section-title")
                        yield txw.DataTable(id="ir-cfg-arcs-table", classes="ir-table")
                        yield txw.Static("CFG Blocks", classes="ir-section-title")
                        yield txw.DataTable(
                            id="ir-blocks-table", classes="ir-table ir-wide-table"
                        )
            with txw.TabPane("Bytecode", id="bytecode-tab"):
                yield txw.Static(
                    "", classes="output-panel", id="bytecode-output", markup=False
                )
            with txw.TabPane("Logs", id="diagnostics-tab"):
                yield txw.Log(id="diagnostics-log", highlight=True)
            with txw.TabPane("Variables/Registers", id="symbols-tab"):
                table = txw.DataTable(id="symbols-table")
                table.add_columns("Name", "Type", "Storage")
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
        height: auto;
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
        height: auto;
        align: left middle;
    }

    #controls-row Button {
        margin-right: 1;
        min-width: 6;
    }

    #controls-row Checkbox {
        margin-right: 1;
        width: auto;
        height: auto;
    }

    #compile-status {
        color: $text-muted;
        width: 1fr;
        content-align: right middle;
    }

    #compile-status.status-working {
        color: $warning;
    }

    #compile-status.status-ok {
        color: $success;
    }

    #compile-status.status-failed {
        color: $error;
    }

    #diagnostics-log {
        height: 1fr;
    }

    #symbols-table {
        height: 1fr;
    }

    #ast-scroll {
        height: 1fr;
        overflow-y: auto;
        overflow-x: auto;
        border: none;
        padding: 0;
    }

    #ast-output {
        border: none;
        padding: 0;
    }

    #ir-vscroll {
        height: 1fr;
        overflow-y: auto;
        overflow-x: auto;
        border: none;
        padding: 0;
    }

    #ir-content {
        width: 1fr;
        height: auto;
        min-width: 140;
    }

    .ir-section-title {
        margin: 0 0 1 0;
        text-style: bold;
    }

    .ir-table {
        margin: 0 0 1 0;
        height: auto;
        min-height: 6;
    }

    .ir-wide-table {
        min-width: 180;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="top-row"):
                yield EditorPane(id="editor-pane")
                yield OutputTabsPane(id="outputs-pane")


class TTSLCompilerTesterApp(App):
    COMPILE_TIMEOUT_SECONDS = 8.0
    TITLE = "TTSL Compiler Shader Tester"
    SUB_TITLE = "Layout scaffold"
    BINDINGS = [
        Binding("ctrl+enter", "compile", "Compile"),
        Binding("ctrl+r", "reset_source", "Reset Source"),
        Binding("r", "show_render_tab", "Render Tab"),
        Binding("a", "show_ast_tab", "AST Tab"),
        Binding("i", "show_ir_tab", "IR Tab"),
        Binding("b", "show_bytecode_tab", "Bytecode Tab"),
        Binding("l", "show_logs_tab", "Logs Tab"),
        Binding("v", "show_variables_tab", "Variables Tab"),
        Binding("e", "focus_editor", "Focus Editor", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._compile_in_progress = False
        self._autocompile_seq = 0
        self._editor_change_seq = 0
        self._active_compile_seq = 0
        self._last_compiled_seq = 0

    def compose(self) -> ComposeResult:
        yield txw.Header(show_clock=True)
        yield MainLayout()
        yield txw.Footer()

    def on_mount(self) -> None:
        editor = self.query_one("#ttsl-editor", txw.TextArea)
        tabs = self.query_one("#output-tabs", txw.TabbedContent)
        tabs.can_focus = False
        # Force syntax highlighting settings explicitly at runtime.
        editor.language = "python"
        editor.theme = "dracula"
        editor.refresh()
        self._init_ir_tables()
        self._append_log("Ready. Compile to populate AST / IR / Bytecode / Variables panels.")

    def _init_ir_tables(self) -> None:
        variables_table = self.query_one("#ir-variables-table", txw.DataTable)
        variables_table.add_columns("VarId", "Value")

        const_table = self.query_one("#ir-const-table", txw.DataTable)
        const_table.add_columns("Idx", "Value")

        arcs_table = self.query_one("#ir-cfg-arcs-table", txw.DataTable)
        arcs_table.add_column(" ")

        blocks_table = self.query_one("#ir-blocks-table", txw.DataTable)
        blocks_table.add_columns(
            "Block",
            "Idx",
            "Label",
            "Op",
            "Dst",
            "Src1",
            "Src2",
            "Src3",
            "Src4",
            "Imm",
            "Comment",
        )

    def action_focus_editor(self) -> None:
        self.query_one("#ttsl-editor", txw.TextArea).focus()

    def action_compile(self) -> None:
        if self._compile_in_progress:
            self._append_log("Compile request ignored: a compilation is already running.")
            return

        source = self.query_one("#ttsl-editor", txw.TextArea).text
        self._active_compile_seq = self._editor_change_seq
        self._compile_in_progress = True
        self._clear_logs()
        self._set_status("Status: compiling...", "working")
        self._set_output_tab("diagnostics-tab")
        self._append_log("Starting full pipeline compilation (worker)...")
        self._compile_worker(source)

    def on_key(self, event: events.Key) -> None:
        # TextArea may consume ctrl+enter before global bindings trigger.
        if event.key in {"ctrl+enter", "ctrl+return"}:
            event.stop()
            self.action_compile()

    def action_reset_source(self) -> None:
        editor = self.query_one("#ttsl-editor", txw.TextArea)
        editor.text = DEFAULT_SHADER_CODE
        self._set_status("Status: source reset")
        self._append_log("Editor reset to default shader source.")

    def _set_output_tab(self, tab_id: str) -> None:
        tabs = self.query_one("#output-tabs", txw.TabbedContent)
        tabs.active = tab_id

    def _focus_output_tab(self, tab_id: str) -> None:
        self._set_output_tab(tab_id)
        if tab_id == "ast-tab":
            self.query_one("#ast-scroll", VerticalScroll).focus()
        elif tab_id == "ir-tab":
            self.query_one("#ir-vscroll", VerticalScroll).focus()
        elif tab_id == "bytecode-tab":
            self.query_one("#output-tabs", txw.TabbedContent).blur()
        elif tab_id == "diagnostics-tab":
            self.query_one("#diagnostics-log", txw.Log).focus()
        elif tab_id == "symbols-tab":
            self.query_one("#symbols-table", txw.DataTable).focus()
        elif tab_id == "render-tab":
            self.query_one("#output-tabs", txw.TabbedContent).blur()

    def action_show_ast_tab(self) -> None:
        self._focus_output_tab("ast-tab")

    def action_show_render_tab(self) -> None:
        self._focus_output_tab("render-tab")

    def action_show_ir_tab(self) -> None:
        self._focus_output_tab("ir-tab")

    def action_show_bytecode_tab(self) -> None:
        self._focus_output_tab("bytecode-tab")

    def action_show_logs_tab(self) -> None:
        self._focus_output_tab("diagnostics-tab")

    def action_show_variables_tab(self) -> None:
        self._focus_output_tab("symbols-tab")

    def on_button_pressed(self, event: txw.Button.Pressed) -> None:
        if event.button.id == "compile-btn":
            self.action_compile()
        elif event.button.id == "reset-btn":
            self.action_reset_source()

    def on_text_area_changed(self, event: txw.TextArea.Changed) -> None:
        if event.text_area.id != "ttsl-editor":
            return
        self._editor_change_seq += 1
        checkbox = self.query_one("#autocompile", txw.Checkbox)
        if checkbox.value:
            self._queue_autocompile(self._editor_change_seq)

    def on_checkbox_changed(self, event: txw.Checkbox.Changed) -> None:
        if event.checkbox.id != "autocompile":
            return
        if event.value:
            # If there are pending edits when auto-compile is enabled, schedule once.
            if self._editor_change_seq > self._last_compiled_seq:
                self._queue_autocompile(self._editor_change_seq)
        else:
            # Invalidate pending queued timers when disabling auto-compile.
            self._autocompile_seq += 1

    def _queue_autocompile(self, target_seq: int) -> None:
        self._autocompile_seq += 1
        pending_ticket = self._autocompile_seq
        self._set_status("Status: auto-compile queued...")

        def trigger() -> None:
            if pending_ticket != self._autocompile_seq:
                return
            if not self.query_one("#autocompile", txw.Checkbox).value:
                return
            if target_seq != self._editor_change_seq:
                return
            if self._last_compiled_seq >= target_seq:
                return
            if self._compile_in_progress:
                self._set_status("Status: waiting for current compile...", "working")
                return
            self.action_compile()

        self.set_timer(0.45, trigger)

    @staticmethod
    def _sync_compile(source: str) -> CompilationStateResult:
        try:
            return all_passes_compilation_with_state(
                src=source,
                func_name="my_shader",
                globals_dict={GLOBAL_VAR_TT_TIME: float},
            )
        except Exception as exc:
            return CompilationStateResult(
                last_completed_stage="worker_exception",
                error=exc,
                traceback_text=traceback.format_exc(),
            )

    @work(exclusive=True, group="compile", exit_on_error=False)
    async def _compile_worker(self, source: str) -> None:
        start = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._sync_compile, source),
                timeout=self.COMPILE_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            result = CompilationStateResult(
                last_completed_stage="timeout",
                error=TimeoutError(
                    f"Compilation timed out after {self.COMPILE_TIMEOUT_SECONDS:.1f}s"
                ),
                traceback_text="",
            )
        except Exception as exc:
            result = CompilationStateResult(
                last_completed_stage="worker_exception",
                error=exc,
                traceback_text=traceback.format_exc(),
            )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        self._on_compile_finished(elapsed_ms, result)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group != "compile":
            return
        if event.state == WorkerState.ERROR:
            self._compile_in_progress = False
            err = event.worker.error
            try:
                self.query_one("#diagnostics-log", txw.Log)
            except Exception:
                return
            self._set_status(
                f"Status: compile worker crashed ({type(err).__name__ if err else 'unknown'})"
                ,
                "failed",
            )
            self._append_log(
                f"Compile worker crashed: {type(err).__name__ if err else 'unknown'}: {err}"
            )
            if err is not None:
                for line in traceback.format_exception(type(err), err, err.__traceback__):
                    for sub in line.splitlines():
                        self._append_log(sub)
        elif event.state == WorkerState.CANCELLED:
            self._compile_in_progress = False

    def _on_compile_finished(
        self, elapsed_ms: int, result: CompilationStateResult
    ) -> None:
        self._compile_in_progress = False
        self._last_compiled_seq = max(self._last_compiled_seq, self._active_compile_seq)
        self.query_one("#compile-status", txw.Static)
        self.query_one("#diagnostics-log", txw.Log)

        ast_renderable = self._format_ast_panel(result)
        bytecode_text = self._format_bytecode_panel(result)
        variables_rows = self._format_variables_panel(result)
        self.query_one("#ast-output", txw.Static).update(ast_renderable)
        self._refresh_ir_tables(result)
        self.query_one("#bytecode-output", txw.Static).update(bytecode_text)
        table = self.query_one("#symbols-table", txw.DataTable)
        table.clear()
        for row in variables_rows:
            table.add_row(*row)

        if result.ok:
            bytecode_size = len(result.byte_array) if result.byte_array is not None else 0
            self._set_status(f"Status: compile OK ({elapsed_ms} ms)", "ok")
            self._append_log(
                f"Compilation succeeded in {elapsed_ms} ms. Bytecode size: {bytecode_size} bytes."
            )
        else:
            error = result.error
            assert error is not None
            self._set_status(
                f"Status: compile failed ({elapsed_ms} ms) at {result.last_completed_stage}"
                ,
                "failed",
            )
            self._append_log(
                f"Compilation failed in {elapsed_ms} ms at {result.last_completed_stage}: "
                f"{type(error).__name__}: {error}"
            )
            if result.traceback_text:
                for line in result.traceback_text.strip().splitlines():
                    self._append_log(line)
        self._set_output_tab("diagnostics-tab")
        auto_compile_enabled = self.query_one("#autocompile", txw.Checkbox).value
        if auto_compile_enabled and self._editor_change_seq > self._last_compiled_seq:
            self._queue_autocompile(self._editor_change_seq)

    def _format_ast_panel(self, result: CompilationStateResult) -> Any:
        if result.ast_module is None:
            return ""
        ast_text = ast.dump(result.ast_module, indent=2)
        return Syntax(ast_text, "python", theme="dracula", word_wrap=False)

    def _refresh_ir_tables(self, result: CompilationStateResult) -> None:
        variables_table = self.query_one("#ir-variables-table", txw.DataTable)
        const_table = self.query_one("#ir-const-table", txw.DataTable)
        arcs_table = self.query_one("#ir-cfg-arcs-table", txw.DataTable)
        blocks_table = self.query_one("#ir-blocks-table", txw.DataTable)

        variables_table.clear()
        const_table.clear()
        arcs_table.clear(columns=True)
        blocks_table.clear()

        cc = result.context
        if cc is None:
            arcs_table.add_column(" ")
            return

        for name, temp in sorted(cc.named_variables.items()):
            variables_table.add_row(name, self._format_ir_operand(temp))

        for idx, (const_value, const_type) in sorted(cc.const_pool.items()):
            const_table.add_row(str(idx), f"{const_type.name} {const_value}")

        arcs_table.add_column(" ")
        if cc.cfg is None:
            return

        nodes = list(cc.cfg.node_items())
        for node_id, node in nodes:
            arcs_table.add_column(f"{node.name}\n[{node_id}]")

        for node_id, node in nodes:
            row = [node.name]
            successors = cc.cfg.successors(node_id)
            for dst_id, _ in nodes:
                row.append("X" if dst_id in successors else "")
            arcs_table.add_row(*row)

        for node_id, node in nodes:
            current_line = 0
            for instr in node.instrs():
                if instr.op == OpCodes.PHI:
                    line_label = "-"
                    operands = [
                        f"B{block_id}>{self._format_ir_operand(temp)}"
                        for block_id, temp in instr.phi_operands.items()
                    ]
                    src1 = operands[0] if len(operands) > 0 else "-"
                    src2 = operands[1] if len(operands) > 1 else "-"
                    src3 = operands[2] if len(operands) > 2 else "-"
                    src4 = operands[3] if len(operands) > 3 else "-"
                    imm = "-"
                    comment_tail = ", ".join(operands[4:]) if len(operands) > 4 else ""
                    comment = (
                        f"{comment_tail} {instr.comment}".strip()
                        if comment_tail
                        else (instr.comment or "-")
                    )
                else:
                    current_line += 1
                    line_label = str(current_line)
                    src1 = self._format_ir_operand(instr.src1)
                    src2 = self._format_ir_operand(instr.src2)
                    src3 = self._format_ir_operand(instr.src3)
                    src4 = self._format_ir_operand(instr.src4)
                    imm = str(instr.imm) if instr.imm is not None else "-"
                    comment = instr.comment if instr.comment else "-"

                blocks_table.add_row(
                    f"{node.name}[{node_id}]",
                    line_label,
                    instr.label or "",
                    instr.op.name,
                    self._format_ir_operand(instr.dst),
                    src1,
                    src2,
                    src3,
                    src4,
                    imm,
                    comment,
                )

    def _format_bytecode_panel(self, result: CompilationStateResult) -> str:
        if result.final_byte_code is None:
            return ""
        lines = []
        for idx, words in enumerate(result.final_byte_code):
            lines.append(f"{idx:04d}: {words}")
        return "\n".join(lines)

    def _format_variables_panel(self, result: CompilationStateResult) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        cc = result.context
        if cc is None:
            return rows

        rar = result.register_allocation
        for name in sorted(cc.named_variables.keys()):
            temp = cc.named_variables[name]
            temp_ty = self._ir_type_name(temp.ty)
            storage = f"temp:{temp.id}"
            if rar is not None and name in rar.var_names_to_registers:
                _ty, reg_id = rar.var_names_to_registers[name]
                storage = f"r{reg_id}"
            rows.append((name, temp_ty, storage))
        return rows

    def _format_ir_operand(self, operand: Any) -> str:
        if operand is None:
            return "-"
        if isinstance(operand, Temp):
            return f"{self._ir_type_name(operand.ty)} r{operand.id}"
        return str(operand)

    def _ir_type_name(self, ir_type: IRType) -> str:
        return ir_type.name if isinstance(ir_type, IRType) else str(ir_type)

    def _set_status(self, message: str, state: str = "idle") -> None:
        status = self.query_one("#compile-status", txw.Static)
        status.remove_class("status-working")
        status.remove_class("status-ok")
        status.remove_class("status-failed")
        if state == "working":
            status.add_class("status-working")
        elif state == "ok":
            status.add_class("status-ok")
        elif state == "failed":
            status.add_class("status-failed")
        status.update(message)

    def _clear_logs(self) -> None:
        log = self.query_one("#diagnostics-log", txw.Log)
        log.clear()
        log.scroll_end(animate=False)

    def _append_log(self, line: str) -> None:
        log = self.query_one("#diagnostics-log", txw.Log)
        log.write_line(line)
        log.scroll_end(animate=False)


if __name__ == "__main__":
    TTSLCompilerTesterApp().run()
