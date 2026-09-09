# -*- coding: utf-8 -*-
"""Serialize post-SSA TTSL CFG into the JSON module Cranelift consumes.

The snapshot is taken after ``PassSSARenamer`` and before phi lowering, so
block params / phi operands are still present. Register ids for seeded
inputs are filled in after ``RegisterAllocatorPass``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from tt3de.ttsl.ttsl_assembly import CFG, IRInstr, IRType, OpCodes, Temp

SSA_MODULE_VERSION = 1

_SKIP_OPS = {OpCodes.COMMENT, OpCodes.LABEL, OpCodes.PHI}


def ir_type_name(ty: IRType) -> str:
    return ty.name


def encode_const_value(value: Any, ty: IRType) -> List[float | int]:
    if ty == IRType.BOOL:
        return [1 if value else 0]
    if ty == IRType.I32:
        return [int(value)]
    if ty == IRType.F32:
        return [float(value)]
    if ty == IRType.V2:
        x, y = _vec_components(value, 2)
        return [float(x), float(y)]
    if ty == IRType.V3:
        x, y, z = _vec_components(value, 3)
        return [float(x), float(y), float(z)]
    if ty == IRType.V4:
        x, y, z, w = _vec_components(value, 4)
        return [float(x), float(y), float(z), float(w)]
    raise TypeError(f"cannot encode constant of type {ty}: {value!r}")


def _vec_components(value: Any, width: int) -> Sequence[Any]:
    if isinstance(value, (list, tuple)):
        if len(value) != width:
            raise ValueError(f"expected {width} components, got {value!r}")
        return value
    attrs = ("x", "y", "z", "w")[:width]
    return tuple(getattr(value, name) for name in attrs)


def _temp_id(op: Any) -> Optional[int]:
    if isinstance(op, Temp):
        return int(op.id)
    return None


def _record_temp(temps: Dict[int, str], op: Any) -> None:
    if isinstance(op, Temp):
        temps[int(op.id)] = ir_type_name(op.ty)


def snapshot_ssa_cfg(cc: Any) -> Dict[str, Any]:
    """Dump the SSA CFG and const pool. Input register ids are left unset."""
    cfg: CFG = cc.cfg
    assert cfg is not None

    temps: Dict[int, str] = {}
    inputs: List[Dict[str, Any]] = []
    for name in sorted(cc.ssa_entry_seed_names):
        temp = cc.named_variables[name]
        _record_temp(temps, temp)
        inputs.append(
            {
                "name": name,
                "ty": ir_type_name(temp.ty),
                "temp": int(temp.id),
                "reg": None,
            }
        )

    consts: List[Dict[str, Any]] = []
    const_pool = cc.const_pool
    for const_id in sorted(const_pool.keys()):
        value, ty = const_pool[const_id]
        consts.append(
            {
                "id": int(const_id),
                "ty": ir_type_name(ty),
                "value": encode_const_value(value, ty),
            }
        )

    blocks: List[Dict[str, Any]] = []
    for node_id, node in cfg.node_items():
        if node.name == "_END_":
            continue
        phis: List[Dict[str, Any]] = []
        for _var, phi in sorted(node.phis.items(), key=lambda item: item[0]):
            if phi.op != OpCodes.PHI or not isinstance(phi.dst, Temp):
                continue
            _record_temp(temps, phi.dst)
            operands: List[List[int]] = []
            for pred_id, src_tid in sorted(phi.phi_operands.items()):
                operands.append([int(pred_id), int(src_tid)])
            phis.append(
                {
                    "dst": int(phi.dst.id),
                    "ty": ir_type_name(phi.dst.ty),
                    "operands": operands,
                }
            )

        instrs: List[Dict[str, Any]] = []
        for instr in node.instructions:
            dumped = _dump_instr(cfg, node_id, instr, temps)
            if dumped is not None:
                instrs.append(dumped)

        if not instrs or instrs[-1]["op"] not in {"jmp", "jmp_if_false", "ret"}:
            _append_fallthrough(cfg, node_id, instrs)

        if not instrs and not phis:
            continue

        blocks.append(
            {
                "id": int(node_id),
                "name": node.name,
                "phis": phis,
                "instrs": instrs,
            }
        )

    return {
        "version": SSA_MODULE_VERSION,
        "entry": int(cfg.init_idx),
        "inputs": inputs,
        "temps": {str(tid): ty for tid, ty in sorted(temps.items())},
        "consts": consts,
        "blocks": blocks,
    }


def attach_ssa_inputs(module: Dict[str, Any], cc: Any, rar: Any) -> Dict[str, Any]:
    """Fill ``inputs[].reg`` from the register allocator (same slots the VM seeds)."""
    names_to_regs: Mapping[str, tuple] = rar.var_names_to_registers
    for item in module["inputs"]:
        name = item["name"]
        if name not in names_to_regs:
            continue
        ty, reg = names_to_regs[name]
        item["ty"] = ir_type_name(ty)
        item["reg"] = int(reg)
        named = cc.named_variables.get(name)
        if isinstance(named, Temp):
            item["temp"] = int(named.id)
    return module


def dump_ssa_module(cc: Any, rar: Any | None = None) -> Dict[str, Any]:
    module = snapshot_ssa_cfg(cc)
    if rar is not None:
        attach_ssa_inputs(module, cc, rar)
    return module


def _dump_instr(
    cfg: CFG, node_id: int, instr: IRInstr, temps: Dict[int, str]
) -> Optional[Dict[str, Any]]:
    if instr.op in _SKIP_OPS:
        return None

    for op in (instr.dst, instr.src1, instr.src2, instr.src3, instr.src4):
        _record_temp(temps, op)

    if instr.op == OpCodes.JMP:
        return {"op": "jmp", "target": _jump_target(cfg, instr)}

    if instr.op == OpCodes.JMP_IF_FALSE:
        target = _jump_target(cfg, instr)
        fallthrough = _jmp_if_false_fallthrough(cfg, node_id, target)
        src = _temp_id(instr.src1)
        if src is None:
            raise ValueError("jmp_if_false missing boolean source temp")
        return {
            "op": "jmp_if_false",
            "src": [src],
            "target": target,
            "fallthrough": fallthrough,
        }

    if instr.op == OpCodes.RET:
        src = [
            _require_temp(instr.src1, "ret front"),
            _require_temp(instr.src2, "ret back"),
            _require_temp(instr.src3, "ret glyph"),
        ]
        return {"op": "ret", "src": src}

    dumped: Dict[str, Any] = {"op": instr.op.value}
    dst = _temp_id(instr.dst)
    if dst is not None:
        dumped["dst"] = dst
        dumped["ty"] = ir_type_name(instr.dst.ty) if isinstance(instr.dst, Temp) else None
    srcs = [
        tid
        for tid in (
            _temp_id(instr.src1),
            _temp_id(instr.src2),
            _temp_id(instr.src3),
            _temp_id(instr.src4),
        )
        if tid is not None
    ]
    if srcs:
        dumped["src"] = srcs
    if instr.op == OpCodes.LOAD_CONST:
        dumped["imm"] = int(instr.imm)
    return dumped


def _require_temp(op: Any, label: str) -> int:
    tid = _temp_id(op)
    if tid is None:
        raise ValueError(f"{label} is not a Temp: {op!r}")
    return tid


def _jump_target(cfg: CFG, instr: IRInstr) -> int:
    label = instr.dst
    if not isinstance(label, str):
        raise ValueError(f"jump target is not a block label: {label!r}")
    return int(cfg.get_idx(label))


def _jmp_if_false_fallthrough(cfg: CFG, node_id: int, target: int) -> int:
    succs = [s for s in cfg.successors(node_id) if s != target]
    if len(succs) != 1:
        raise ValueError(
            f"jmp_if_false in block {node_id} expected one fallthrough, got {succs}"
        )
    return int(succs[0])


def _append_fallthrough(cfg: CFG, node_id: int, instrs: List[Dict[str, Any]]) -> None:
    succs = [
        s
        for s in cfg.successors(node_id)
        if cfg.nodes[s] is not None and cfg.nodes[s].name != "_END_"
    ]
    if len(succs) == 1:
        instrs.append({"op": "jmp", "target": int(succs[0])})
    elif len(succs) > 1:
        raise ValueError(
            f"unterminated block {node_id} has multiple successors {succs}"
        )
