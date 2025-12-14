# -*- coding: utf-8 -*-
from rich.text import Text
from rich.style import Style
from rich.table import Table
from typing import List, Any, Dict

from tt3de.ttsl.compiler import TTSLCompilerContext
from tt3de.ttsl.ttsl_assembly import CFG, IRInstr, IRType, OpCodes, Temp

TYPE_COLORS = {
    IRType.F32: Style(color="cyan"),
    IRType.I32: Style(color="green"),
    IRType.BOOL: Style(color="yellow"),
    IRType.V2: Style(color="magenta"),
    IRType.V3: Style(color="magenta"),
    IRType.V4: Style(color="magenta"),
}
BLOCK_ID_COLOR = Style(color="blue")


def type_to_rich(ty: IRType) -> Text:
    style = TYPE_COLORS.get(ty, Style(color="white"))
    return Text(ty.name, style=style)


def block_id_to_rich(bid: int) -> Text:
    return Text(f"B{bid}", style=BLOCK_ID_COLOR)


def temp_to_rich(temp: Temp | str) -> Text:
    if isinstance(temp, str):
        return Text(temp, style=Style(color="yellow"))
    elif isinstance(temp, Temp):
        return Text.assemble(type_to_rich(temp.ty), " ", Text(f"r{temp.id}"))
    else:
        return Text(f"?{temp}?", style=Style(color="red"))


def const_pool_to_rich(const_pool: Dict) -> Table:
    const_table = Table(
        show_header=True, title="Constant Pool", header_style="bold magenta"
    )

    const_table.add_column("Idx", style="dim", width=6)
    const_table.add_column("Value")
    for idx, (const, const_type) in const_pool.items():
        const_table.add_row(
            str(idx), Text.assemble(type_to_rich(const_type), " ", str(const))
        )
    return const_table


def instr_list_to_rich(instrs: List[IRInstr]) -> Table:
    table = Table(show_header=True, title="IR Program", header_style="bold magenta")
    table.add_column("Idx", style="dim", width=6)
    table.add_column(
        "Label",
        justify="right",
    )
    table.add_column("Op")
    table.add_column("Dst")
    table.add_column("Src1")
    table.add_column("Src2")
    table.add_column("Src3")
    table.add_column("Src4")
    table.add_column("Imm")
    table.add_column("Comment")

    for idx, instr in enumerate(instrs):
        if instr.op == OpCodes.PHI:
            table.add_section()
            operands_txt = [
                Text.assemble(block_id_to_rich(block_id), ">", temp_to_rich(temp))
                for block_id, temp in instr.phi_operands.items()
            ]

            vars = ["-"] * 5
            for var in range(5):
                if len(operands_txt) > 0:
                    vars[var] = operands_txt.pop(0)

            vars.append(
                Text.assemble(
                    *(operands_txt + [instr.comment]),
                )
            )

            table.add_row(
                str(idx), instr.label, instr.op.name, temp_to_rich(instr.dst), *vars
            )
            continue
        dst = temp_to_rich(instr.dst) if instr.dst is not None else Text("-")
        src1 = temp_to_rich(instr.src1) if instr.src1 is not None else Text("-")
        src2 = temp_to_rich(instr.src2) if instr.src2 is not None else Text("-")
        src3 = temp_to_rich(instr.src3) if instr.src3 is not None else Text("-")
        src4 = temp_to_rich(instr.src4) if instr.src4 is not None else Text("-")
        imm = Text(str(instr.imm)) if instr.imm is not None else Text("-")
        label = (
            Text(f"{instr.label}:", style=Style(color="yellow"))
            if instr.label is not None
            else Text("")
        )
        comment = Text(instr.comment) if instr.comment is not None else Text("-")

        table.add_row(
            str(idx),
            label,
            instr.op.name,
            dst,
            src1,
            src2,
            src3,
            src4,
            imm,
            comment,
        )

    return table


def env_table_to_rich(env: Dict[str, Temp]) -> Table:
    table = Table(show_header=True, title="Variables", header_style="bold magenta")
    table.add_column("VarId", style="dim")
    table.add_column(
        "Value",
    )

    for name, temp in env.items():
        table.add_row(name, temp_to_rich(temp))

    return table


def compiler_to_rich(compiler: TTSLCompilerContext) -> List[Any]:
    compiler.code
    compiler.named_variables

    env_table = env_table_to_rich(compiler.named_variables)

    return [env_table] + const_pool_to_rich(compiler.code)


def cfg_to_rich(cfg: CFG) -> Table:
    """Represent the CFG as rich tables with accessiblity matrix."""

    table = Table(show_header=True, title="Variables", header_style="bold magenta")

    table.add_column("  ", style="dim")
    for node_idx, node in cfg.node_items():
        table.add_column(f"{node.name}\n[{node_idx}]", style="dim")
    for node_idx, node in cfg.node_items():
        row = [Text(f"{node.name}", style=Style(color="yellow"))]
        for dst_idx, _ in cfg.node_items():
            if dst_idx in cfg.successors(node_idx):
                row.append(Text("X", style=Style(color="green")))
            else:
                row.append(Text(" ", style=Style(color="red")))
        table.add_row(*row)
    return table
