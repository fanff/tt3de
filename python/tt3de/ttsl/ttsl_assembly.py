# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tt3de.ttsl.compiler import TTSLCompilerContext

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Tuple, Set

NodeID = int
TempID = int
SSAVarID = str


class IRType(Enum):
    F32 = auto()
    I32 = auto()
    BOOL = auto()
    V2 = auto()
    V3 = auto()
    V4 = auto()

    @staticmethod
    def from_str(type_str: str) -> "IRType":
        if type_str in STR_TO_IRTYPE:
            return STR_TO_IRTYPE[type_str]
        else:
            raise ValueError(f"Unknown IRType string: {type_str}")


STR_TO_IRTYPE = {
    "float": IRType.F32,
    "int": IRType.I32,
    "bool": IRType.BOOL,
    "vec2": IRType.V2,
    "vec3": IRType.V3,
    "vec4": IRType.V4,
}


@dataclass
class Temp:
    id: TempID
    ty: IRType


IROperand = Temp | SSAVarID


def is_operand_temp(op: IROperand) -> bool:
    return isinstance(op, Temp)


def is_operand_ssavar(op: IROperand) -> bool:
    if isinstance(op, str):
        return True


class OpCodes(Enum):
    PHI = "phi"
    COMMENT = "comment"
    LABEL = "label"
    LOAD_CONST = "load_const"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    NEG = "neg"

    JMP = "jmp"
    JMP_IF_FALSE = "jmp_if_false"

    RET = "ret"
    CMP_GT = "cmp_gt"
    CMP_GTE = "cmp_gte"

    STORE = "store"
    STORE_VEC_FROM_SCALAR = "store_vec_from_scalar"
    READ_AXIS_X = "read_axis_x"
    READ_AXIS_Y = "read_axis_y"
    READ_AXIS_Z = "read_axis_z"
    READ_AXIS_W = "read_axis_w"

    SIN = "sin"
    ABS = "abs"
    SQRT = "sqrt"
    COS = "cos"
    TAN = "tan"
    EXP = "exp"
    LN = "ln"
    LOG = "log"
    MIX = "mix"


@dataclass
class IRInstr:
    op: OpCodes  # "add_f32", "mul_v3f", "cmp_gt_f32", "jmp", "jmp_if_false", "ret_v3", ...
    dst: Optional[IROperand]  # result temp, or None for pure control-flow
    src1: Optional[IROperand]  #
    src2: Optional[IROperand]  #
    src3: Optional[IROperand]  #
    src4: Optional[IROperand]  #
    imm: Optional[int]  # literal  index into const pool
    label: Optional[str]  # only used for marking a label at this position
    comment: Optional[str]  # optional comment for debugging

    phi_operands: Optional[Dict[NodeID, Temp]] = None  # only for phi nodes
    byte_code: Optional[List[int]] = None  # placeholder for bytecode representation

    def uniop(
        op: OpCodes,
        dst: Optional[IROperand] = None,
        src: Optional[IROperand] = None,
        comment: Optional[str] = None,
    ) -> "IRInstr":
        return IRInstr(
            op=op,
            dst=dst,
            src1=src,
            src2=None,
            src3=None,
            src4=None,
            imm=None,
            label=None,
            comment=comment,
        )

    def __post_init__(self):
        self.phi_operands = {}
        self.byte_code = [0] * 6  # placeholder for bytecode representation

    def copy(self) -> "IRInstr":
        return IRInstr(
            op=self.op,
            dst=self.dst,
            src1=self.src1,
            src2=self.src2,
            src3=self.src3,
            src4=self.src4,
            imm=self.imm,
            label=self.label,
            comment=self.comment,
            phi_operands=(
                self.phi_operands.copy() if self.phi_operands is not None else None
            ),
        )

    @property
    def ty(self) -> Optional[IRType]:
        if self.dst is not None and is_operand_temp(self.dst):
            return self.dst.ty
        return None


class IRProgram:
    instrs: list[IRInstr]

    label_counter: int = 0

    def __init__(self):
        self.instrs = []

        # index -> value
        self.const_pool: dict[int, Tuple[Any, IRType]] = {}

        # keep track of spans that starts with a label and end with either
        # a label, or end of program, or a jump
        self.spans: Dict[int, IRSpan] = {}

        self.current_span: Optional[int] = None

    def __len__(self) -> int:
        return len(self.instrs)

    def instructions_count(self) -> int:
        return len(self.instrs)

    def append(self, instr: IRInstr) -> int:
        if self.current_span is not None:
            pass
        self.instrs.append(instr)
        return len(self.instrs) - 1  # return position

    def add_constant(self, value: Any, value_type: IRType) -> int:
        # Check if already in const pool
        for idx, (val, ty) in self.const_pool.items():
            if val == value and ty == value_type:
                return idx
        # Add new constant
        new_idx = len(self.const_pool)
        self.const_pool[new_idx] = (value, value_type)
        return new_idx

    def get_constant(self, index: int) -> Any:
        return self.const_pool[index]

    def patch_target(self, instr_pos: int, target_pos: int) -> None:
        instr = self.instrs[instr_pos]
        if instr.op in {OpCodes.JMP, OpCodes.JMP_IF_FALSE}:
            if target_pos >= len(self.instrs):
                instr.dst = target_pos
                return
            target_instr = self.instrs[target_pos]
            if target_instr.label is None:
                # we can create a one.
                target_instr.label = f"S_{self.label_counter}"
                self.label_counter += 1
            instr.dst = target_instr.label
        else:
            raise ValueError(
                f"Instruction at position {instr_pos} is not a jump instruction."
            )

    def fix_jump_targets(self) -> None:
        """Replace jump instruction targets from positions to labels."""
        pos_to_label: Dict[int, str] = {}
        for idx, instr in enumerate(self.instrs):
            if instr.label is not None:
                pos_to_label[idx] = instr.label

        for idx, instr in enumerate(self.instrs):
            if instr.op in {OpCodes.JMP, OpCodes.JMP_IF_FALSE}:
                if isinstance(instr.dst, int):
                    target_line = instr.dst
                    if target_line in pos_to_label:
                        target_pos = pos_to_label[target_line]
                        instr.dst = target_pos
                    else:
                        # we need to create a label at that position
                        self.instrs[target_line].label = f"S_{self.label_counter}"
                        self.label_counter += 1

                        instr.dst = self.instrs[target_line].label

    def block(self):
        s = IRSpan(self, self.label_counter)
        self.spans[self.label_counter] = s

        self.current_span = self.label_counter

        self.label_counter += 1
        return s

    def end_span(self, span_id: int) -> None:
        pass


class IRSpan:
    def __init__(self, irprog: IRProgram, statement_id: int):
        self.irprog = irprog
        self.statement_id = statement_id
        self.start_idx: Optional[int] = None
        self.end_idx: Optional[int] = None

    def __enter__(self):
        self.start_idx = self.irprog.append(
            IRInstr(
                op=OpCodes.LABEL,
                dst=None,
                src1=None,
                src2=None,
                src3=None,
                src4=None,
                imm=None,
                label=f"S_{self.statement_id}",
                comment=" ",
            )
        )

    def __exit__(self, exc_type, exc_value, traceback):
        self.end_idx = (
            self.irprog.append(
                IRInstr(
                    op=OpCodes.COMMENT,
                    dst=None,
                    src1=None,
                    src2=None,
                    src3=None,
                    src4=None,
                    imm=None,
                    label=None,
                    comment=f"End  S_{self.statement_id}",
                )
            )
            + 1
        )
        self.irprog.end_span(self.statement_id)

    def is_jumping(self) -> bool:
        for instr in reversed(self.irprog.instrs[self.start_idx : self.end_idx]):
            if instr.op in {OpCodes.JMP, OpCodes.JMP_IF_FALSE}:
                return True


def eliminate_unused_variables(ir_program: IRProgram) -> None:
    used_temps: Dict[int, int] = {}

    for instr in ir_program.instrs:
        for temp in [instr.src1, instr.src2, instr.src3, instr.src4]:
            if temp is not None:
                used_temps[temp.id] = used_temps.get(temp.id, 0) + 1

    optimized_instrs = []
    for instr in ir_program.instrs:
        if instr.dst is None or instr.dst.id in used_temps:
            optimized_instrs.append(instr)

    ir_program.instrs = optimized_instrs


def regroup_load_consts_at_top(
    ir_program: IRProgram,
) -> Temp:
    load_consts = []
    other_instrs = []
    for instr in ir_program.instrs:
        if instr.op == OpCodes.LOAD_CONST:
            load_consts.append(instr)
        else:
            other_instrs.append(instr)
    ir_program.instrs = load_consts + other_instrs


class CFGNode:
    def __init__(self, name: str):
        self.name: str = name
        # self.cfg: "CFG" = None
        self.phis: Dict[SSAVarID, IRInstr] = {}

        self.instructions: List[IRInstr] = []

    def instrs(self, include_phis=True) -> List[IRInstr]:
        top = []
        # deterministic order is nice for debugging
        if self.phis and include_phis:
            top.extend(
                v for k, v in (sorted(self.phis.items(), key=lambda item: item[0]))
            )  # or sorted by var id
        top.extend(self.instructions)
        return top

    def append_instruction(self, instr: IRInstr) -> None:
        self.instructions.append(instr)

    def insert_before_terminator(self, instr: IRInstr) -> None:
        term_ops = {OpCodes.JMP, OpCodes.JMP_IF_FALSE, OpCodes.RET}
        instrs = self.instructions  # however you store them
        if instrs and instrs[-1].op in term_ops:
            instrs.insert(len(instrs) - 1, instr)
        else:
            instrs.append(instr)

    def is_jumping(self) -> bool:
        for instr in reversed(self.instrs()):
            if instr.op in {OpCodes.JMP, OpCodes.JMP_IF_FALSE}:
                return True
        return False

    def is_returning(self) -> bool:
        for instr in reversed(self.instrs()):
            if instr.op == OpCodes.RET:
                return True
        return False

    def is_followthrough(self) -> bool:
        return not self.is_jumping() and not self.is_returning()

    def set_end(self, end: int) -> None:
        pass

    def find_temp_operand(
        self, temp_id: TempID, only_on_dest: bool = False
    ) -> Optional[IRInstr]:
        for instr in self.instrs():
            if not only_on_dest:
                for op in [instr.src1, instr.src2, instr.src3, instr.src4]:
                    if isinstance(op, (Temp, TempID)):
                        if is_operand_temp(op) and op.id == temp_id:
                            return instr
            for op in [instr.dst]:
                if isinstance(op, (Temp, TempID)):
                    if is_operand_temp(op) and op.id == temp_id:
                        return instr
        return None

    def set_instrs(self, instrs: List[IRInstr]) -> None:
        self.instructions = instrs

    def get_terminator(self) -> Optional[IRInstr]:
        if self.instructions:
            last_instr = self.instructions[-1]
            if last_instr.op in {OpCodes.JMP, OpCodes.JMP_IF_FALSE, OpCodes.RET}:
                return last_instr
        return None


class CFG:
    def __init__(self):
        self.nodes: List[CFGNode] = []
        self.arcs: List[Tuple[NodeID, NodeID]] = []

        # Special nodes
        self.terminal_node: CFGNode = CFGNode(
            name="_END_",
        )
        self.init_node: CFGNode = CFGNode(
            name="_INIT_",
        )

        # Optional: a fast map from Node name to index (makes APIs nicer)
        self._node_name_to_id: Dict[str, NodeID] = {}

        # Insert init/end nodes in graph at start
        self.init_idx = self.add_node(self.init_node)
        self.end_idx = self.add_node(self.terminal_node)

    def add_node(self, node: CFGNode) -> NodeID:
        """Add a node and return its index."""
        idx = len(self.nodes)
        self.nodes.append(node)
        # node.cfg = self
        if node.name in self._node_name_to_id:
            raise ValueError(f"Duplicate node name: {node.name}")
        self._node_name_to_id[node.name] = idx
        return idx

    def remove_node(self, idx: NodeID) -> None:
        """Remove a node by its index."""
        node = self.nodes[idx]
        del self._node_name_to_id[node.name]
        self.nodes[idx] = None  # or some placeholder
        # Also remove associated arcs
        self.arcs = [
            (src, dst) for (src, dst) in self.arcs if src != idx and dst != idx
        ]

    def get_idx(self, name: str) -> NodeID:
        """Get node index from its name."""
        return self._node_name_to_id[name]

    def add_arc_idx(self, src_idx: NodeID, dst_idx: NodeID) -> None:
        """Add an edge using node indices."""
        self.arcs.append((src_idx, dst_idx))

    def remove_arc_idx(self, src_idx: int, dst_idx: int) -> None:
        self.arcs = [
            (s, d) for (s, d) in self.arcs if not (s == src_idx and d == dst_idx)
        ]

    def get_arcs(self) -> List[Tuple[NodeID, NodeID]]:
        """Get all arcs in the CFG."""
        return self.arcs

    def add_arc(self, src_name: str, dst_name: str) -> None:
        """Add an edge using node names."""
        self.add_arc_idx(self.get_idx(src_name), self.get_idx(dst_name))

    # ------------ Basic graph queries ------------

    def successors(self, idx: NodeID) -> List[NodeID]:
        return [dst for (src, dst) in self.arcs if src == idx]

    def predecessors(self, idx: NodeID) -> List[NodeID]:
        return [src for (src, dst) in self.arcs if dst == idx]

    def all_nodes(self) -> List[NodeID]:
        return [nidx for nidx, node in enumerate(self.nodes) if node is not None]

    def node_items(self) -> List[Tuple[NodeID, CFGNode]]:
        return [
            (nidx, node) for nidx, node in enumerate(self.nodes) if node is not None
        ]

    def bfs(self, start_idx: NodeID) -> List[NodeID]:
        visited: Set[NodeID] = set()
        order: List[NodeID] = []
        q: deque[NodeID] = deque()

        visited.add(start_idx)
        q.append(start_idx)

        while q:
            v = q.popleft()
            order.append(v)

            for w in self.successors(v):
                if w not in visited:
                    visited.add(w)
                    q.append(w)

        return order

    def dfs(self, start_idx: int) -> List[int]:
        visited: Set[int] = set()
        order: List[int] = []

        def _dfs(v: int) -> None:
            visited.add(v)
            order.append(v)
            for w in self.successors(v):
                if w not in visited:
                    _dfs(w)

        _dfs(start_idx)
        return order

    def dfs_from(self, start_name: str) -> List[CFGNode]:
        start_idx = self.get_idx(start_name)
        return [self.nodes[i] for i in self.dfs(start_idx)]

    def reverse_post_order(self, entry_idx: Optional[NodeID] = None) -> List[NodeID]:
        """
        Compute Reverse Post Order (RPO) of the CFG starting from entry_idx. Only
        reachable nodes are included.

        RPO is commonly used for block layout and many forward dataflow passes.
        """
        if entry_idx is None:
            entry_idx = self.init_idx

        visited: Set[int] = set()
        postorder: List[int] = []

        def dfs(n: int) -> None:
            visited.add(n)
            for s in self.successors(n):
                if s not in visited and self.nodes[s] is not None:
                    dfs(s)
            postorder.append(n)

        if self.nodes[entry_idx] is None:
            return []

        dfs(entry_idx)
        postorder.reverse()
        return postorder

    # ---------------- Dominator analysis ----------------
    def compute_dominators(
        self, entry_idx: Optional[int] = None
    ) -> Dict[int, Set[int]]:
        """
        Classic iterative dominator sets computation.

        dom[n] = set of nodes that dominate n.
        """
        if entry_idx is None:
            entry_idx = self.init_idx

        nodes = self.all_nodes()
        node_set = set(nodes)

        dom: Dict[int, Set[int]] = {}

        # Init
        for n in nodes:
            if n == entry_idx:
                dom[n] = {n}
            else:
                dom[n] = set(node_set)

        changed = True
        while changed:
            changed = False
            for n in nodes:
                if n == entry_idx:
                    continue

                preds = [p for p in self.predecessors(n) if p in node_set]

                # If no predecessors (disconnected), define dom[n] conservatively as {n}
                if not preds:
                    new_dom = {n}
                else:
                    # Intersection of predecessors dominators, plus self
                    new_dom = set(node_set)
                    for p in preds:
                        new_dom.intersection_update(dom[p])
                    new_dom.add(n)

                if new_dom != dom[n]:
                    dom[n] = new_dom
                    changed = True

        return dom

    def dominators_of(
        self, node_idx: int, dom: Optional[Dict[int, Set[int]]] = None
    ) -> Set[int]:
        """Return the dominator set for a node."""
        if dom is None:
            dom = self.compute_dominators()
        return dom.get(node_idx, set())

    def dominates(
        self, a_idx: int, b_idx: int, dom: Optional[Dict[int, Set[int]]] = None
    ) -> bool:
        """Return True iff node a dominates node b."""
        if dom is None:
            dom = self.compute_dominators()
        return a_idx in dom.get(b_idx, set())

    def compute_immediate_dominators(
        self, entry_idx: Optional[int] = None, dom: Optional[Dict[int, Set[int]]] = None
    ) -> Dict[int, Optional[int]]:
        """
        Compute immediate dominators (idom) from dominator sets.

        idom[entry] = None
        """
        if entry_idx is None:
            entry_idx = self.init_idx
        if dom is None:
            dom = self.compute_dominators(entry_idx)

        nodes = self.all_nodes()
        idom: Dict[int, Optional[int]] = {entry_idx: None}

        for n in nodes:
            if n == entry_idx:
                continue

            candidates = set(dom.get(n, set())) - {n}
            if not candidates:
                # Unreachable / isolated node
                idom[n] = None
                continue

            # Immediate dominator = the dominator that is not dominated by any other dominator candidate.
            # I.e., pick d such that no other c in candidates dominates d.
            chosen: Optional[int] = None
            for d in candidates:
                dominated_by_other = False
                for c in candidates:
                    if c == d:
                        continue
                    if d in dom.get(c, set()):  # c dominates d
                        dominated_by_other = True
                        break
                if not dominated_by_other:
                    chosen = d
                    break

            idom[n] = chosen

        return idom

    def dominator_tree(
        self,
        entry_idx: Optional[int] = None,
        idom: Optional[Dict[int, Optional[int]]] = None,
        dom: Optional[Dict[int, Set[int]]] = None,
    ) -> Dict[int, List[int]]:
        """
        Build dominator tree adjacency list: parent -> [children].
        Returns a dict keyed by node idx (including entry), each mapped to a list of child node indices.
        """
        if entry_idx is None:
            entry_idx = self.init_idx
        if idom is None:
            idom = self.compute_immediate_dominators(entry_idx=entry_idx, dom=dom)

        tree: Dict[int, List[int]] = {n: [] for n in self.all_nodes()}
        for n, parent in idom.items():
            if parent is None:
                continue
            if parent in tree:
                tree[parent].append(n)
            else:
                tree[parent] = [n]

        return tree

    def compute_dominance_frontiers(
        self,
        entry_idx: int,
        idom: Dict[int, Optional[int]],
        dom: Dict[int, Set[int]],
    ) -> Dict[int, Set[int]]:
        """
        Compute dominance frontiers for all nodes.

        Returns: DF[n] = set of node indices in the dominance frontier of n.
        """
        if entry_idx is None:
            entry_idx = self.init_idx

        if dom is None:
            dom = self.compute_dominators(entry_idx)

        if idom is None:
            idom = self.compute_immediate_dominators(entry_idx, dom)

        # Initialize empty frontiers
        DF: Dict[int, Set[int]] = {n: set() for n in self.all_nodes()}

        for n in self.all_nodes():
            preds = self.predecessors(n)
            if len(preds) < 2:
                continue

            for p in preds:
                runner = p
                while runner is not None and runner != idom.get(n):
                    DF[runner].add(n)
                    runner = idom.get(runner)

        return DF

    def cytron_insert_phi_nodes(
        self,
        variables_defs: Dict[SSAVarID, Set[NodeID]],
        named_variables: Dict[SSAVarID, Temp],
        dominance_frontier: Dict[NodeID, Set[NodeID]],
    ) -> Dict[NodeID, Dict[SSAVarID, IRInstr]]:
        """
        Cytron et al. phi insertion (iterative worklist).

        Inputs:
          - variables_defs: var -> set(block) where var is assigned
          - named_variables: var -> Temp representing the variable
          - dominance_frontier: DF[block] -> set(block) in its dominance frontier

        Output:
          - block_phis: block -> { var -> PhiInstr }
            (phi operands/dst are placeholders; filled during SSA renaming)
        """
        block_phis: Dict[NodeID, Dict[SSAVarID, IRInstr]] = {}

        for var, def_blocks in variables_defs.items():
            # Worklist initialized with all definition blocks of var
            W: Deque[NodeID] = deque(def_blocks)
            # Tracks where we've already inserted a phi for this var
            has_phi: Set[NodeID] = set()

            # We need a mutable set because Cytron adds new "def blocks" when phi inserted
            defsites: Set[NodeID] = set(def_blocks)

            while W:
                n = W.popleft()

                for y in dominance_frontier.get(n, set()):
                    if y not in has_phi:
                        # Insert phi(var) at start of block y
                        temp = named_variables[var]
                        phi = IRInstr(
                            op=OpCodes.PHI,
                            dst=var,
                            src1=None,
                            src2=None,
                            src3=None,
                            src4=None,
                            imm=None,
                            label=None,
                            comment=f"Phi for {var}({temp.id}) (insert at block {y})",
                            phi_operands={},
                        )
                        block_phis.setdefault(y, {})[var] = phi
                        has_phi.add(y)

                        # Cytron: if y is not already a defsite, add it and continue iteration
                        if y not in defsites:
                            defsites.add(y)
                            W.append(y)

        return block_phis

    def to_irprog(self) -> List[IRInstr]:
        rewritten_instructions: List[IRInstr] = []
        for node_idx in self.all_nodes():
            node = self.nodes[node_idx]
            instrs = node.instrs()
            for instr in instrs:
                rewritten_instructions.append(instr)

        return rewritten_instructions


def build_cfg_from_ir(
    ttsl_compiler: "TTSLCompilerContext",
) -> CFG:
    cfg = CFG()
    terminal_node = cfg.terminal_node
    current_node = cfg.init_node

    for line, instr in enumerate(ttsl_compiler.code.instrs):
        if instr.label is not None:
            if current_node is not None:
                current_node.set_end(line)
            new_node = CFGNode(name=instr.label)
            cfg.add_node(new_node)

            if current_node is not None:
                cfg.add_arc(current_node.name, new_node.name)
            current_node = new_node

        if instr.op is OpCodes.RET:
            current_node.append_instruction(instr)
            current_node.set_end(line + 1)

            cfg.add_arc(current_node.name, terminal_node.name)
            current_node = None

        elif instr.op in {OpCodes.JMP, OpCodes.JMP_IF_FALSE}:
            if current_node is None:
                continue  # we have already returned, unless you have another later
            current_node.append_instruction(instr)
            current_node.set_end(line + 1)
            current_node = None
        else:
            if current_node is None:
                print("Warning: instruction after return/jump without label.")
                print(f"  Instr: {instr}")
            else:
                current_node.append_instruction(instr)

    if current_node is not None:
        current_node.set_end(len(ttsl_compiler.code.instrs))
        cfg.add_arc(current_node.name, terminal_node.name)
    else:
        pass
    # redo a pass to fill the arcs for jumps
    for node_idx, node in enumerate(cfg.nodes):
        for _line_idx, instr in enumerate(node.instructions):
            if instr.op in {OpCodes.JMP, OpCodes.JMP_IF_FALSE}:
                # find target node
                target_label = instr.dst
                for target_node_idx, target_node in enumerate(cfg.nodes):
                    if target_node.name == target_label:
                        cfg.add_arc(node.name, target_node.name)
                        break
                # if its jmp_if_false, also add fallthrough arc
                if instr.op == OpCodes.JMP_IF_FALSE:
                    if node_idx + 1 < len(cfg.nodes):
                        cfg.add_arc(node.name, cfg.nodes[node_idx + 1].name)

    ttsl_compiler.cfg = cfg  # store back in compiler for later passes
    ttsl_compiler.ssa_var_definitions = build_variables_definitions(cfg, ttsl_compiler)
    ttsl_compiler.const_pool = ttsl_compiler.code.const_pool
    return cfg


def build_variables_definitions(
    cfg: CFG,
    ttsl_compiler: "TTSLCompilerContext",
) -> Dict[SSAVarID, Set[NodeID]]:
    variables_defs: Dict[SSAVarID, Set[NodeID]] = {}
    for node_idx, node in cfg.node_items():
        for instr in node.instrs():
            if isinstance(instr.dst, Temp):
                # find variable name
                filt = [
                    name
                    for name, temp in ttsl_compiler.named_variables.items()
                    if temp.id == instr.dst.id
                ]
                if not filt:
                    continue
                var_name = filt[0]

                if var_name not in variables_defs:
                    variables_defs[var_name] = set()
                variables_defs[var_name].add(node_idx)
    return variables_defs


def eliminate_dead_nodes(cfg: CFG) -> None:
    """Eliminate unreachable nodes from the CFG."""

    bfs = cfg.bfs(start_idx=cfg.init_idx)

    changed_something = False
    for n in cfg.all_nodes():
        if n not in bfs:
            cfg.remove_node(n)
            changed_something = True
    if changed_something:
        eliminate_dead_nodes(cfg)


def join_branches(cfg: CFG) -> None:
    """Join contiguous branches in the CFG."""
    changed_something = False
    for node_strt, node_end in cfg.get_arcs():
        if node_strt == cfg.init_idx:
            continue
        node_strt_obj = cfg.nodes[node_strt]
        node_end_obj = cfg.nodes[node_end]
        suc_of_start = cfg.successors(node_strt)
        pred_of_end = cfg.predecessors(node_end)
        if (
            len(suc_of_start) == 1
            and suc_of_start[0] == node_end
            and len(pred_of_end) == 1
            and pred_of_end[0] == node_strt
        ):
            # Merge nodes

            suc_of_end = cfg.successors(node_end)
            node_strt_obj.add_instruction_range(
                node_end_obj.start + 1, node_end_obj.end
            )
            cfg.remove_node(node_end)
            for suc in suc_of_end:
                cfg.add_arc_idx(node_strt, suc)
            changed_something = True
            break
    if changed_something:
        join_branches(cfg)
