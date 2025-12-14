# -*- coding: utf-8 -*-
import ast
from typing import Any, Dict, List, Optional, Tuple

from pyglm import glm

from tt3de.ttsl.ttsl_assembly import (
    CFG,
    STR_TO_IRTYPE,
    IRInstr,
    IROperand,
    IRProgram,
    IRType,
    NodeID,
    OpCodes,
    SSAVarID,
    Temp,
    TempID,
    is_operand_ssavar,
)

PRELUDE_GLM_IMPORT = """
# GLM prelude
import pyglm as glm
vec2 = glm.vec2
vec3 = glm.vec3
vec4 = glm.vec4
# End GLM prelude
"""
# defines allowed types in the IR:
ALLOWED_IR_TYPES = {
    float: IRType.F32,
    int: IRType.I32,
    bool: IRType.BOOL,
    glm.vec2: IRType.V2,
    glm.vec3: IRType.V3,
    glm.vec4: IRType.V4,
}

VECTOR_CONSTRUCTORS = {"vec2": IRType.V2, "vec3": IRType.V3, "vec4": IRType.V4}

GLOBAL_VAR_TTSL_TIME = "ttsl_time"
PIXELVAR_TTSL_UV0 = "ttsl_uv0"
PIXELVAR_TTSL_UV1 = "ttsl_uv1"

GLOBAL_VARIABLES_STR_TYPE = {
    GLOBAL_VAR_TTSL_TIME: IRType.F32,
}

PIXEL_VARIABLES_STR_TYPE = {
    PIXELVAR_TTSL_UV0: IRType.V2,
    PIXELVAR_TTSL_UV1: IRType.V2,
}

NATIVE_UNI_OPS_TYPE = {
    "sin": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "cos": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "tan": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "abs": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "neg": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "norm": (IRType.V2, IRType.V3, IRType.V4),
}

NATIVE_BI_OPS_TYPE = {
    "cross": (IRType.V2, IRType.V3, IRType.V4),
    "dot": (IRType.V2, IRType.V3, IRType.V4),
}


class CleanPythonTreePass(ast.NodeTransformer):
    def visit_Expr(self, node):
        # Strip out bare `print(...)` calls from the AST
        if (
            isinstance(node.value, ast.Call)
            and getattr(node.value.func, "id", None) == "print"
        ):
            return None
        if isinstance(node.value, ast.Import) or isinstance(node.value, ast.ImportFrom):
            return None

        return node


class CompileError(Exception):
    def __init__(self, node, *args):
        super().__init__(*args)
        self.node = node


class TTSLCompilerContext:
    def __init__(self, globals_dict: Dict[SSAVarID, IRType]):
        self.code = IRProgram()
        self.globals: Dict[SSAVarID, IRType] = globals_dict
        self.named_variables: Dict[SSAVarID, Temp] = {}
        self.next_temp_id = len(self.named_variables)

        # place holder for later passes
        self.cfg: CFG | None = None
        self.ssa_var_definitions: Dict[SSAVarID, List[NodeID]] = {}
        self.const_pool: dict[int, Any] = {}

        # Predefine some variables
        for name, ty in self.allways_present_variables_at_init().items():
            self.named_variables[name] = self.alloc_reg_for_type(ty)
        for name, ty in self.globals.items():
            self.named_variables[name] = self.alloc_reg_for_type(ty)

    def temp_id_to_variable(self, temp_id: TempID) -> Optional[SSAVarID]:
        for var_name, temp in self.named_variables.items():
            if temp.id == temp_id:
                return var_name
        return None

    def allways_present_variables_at_init(self) -> Dict[str, IRType]:
        return {
            "ttsl_uv0": IRType.V2,
            "ttsl_uv1": IRType.V2,
        }

    def comment(self, text: str):
        instr = IRInstr(
            op=OpCodes.COMMENT,
            src1=None,
            src2=None,
            src3=None,
            src4=None,
            dst=None,
            imm=None,
            label=None,
            comment=text,
        )
        return self.code.append(instr)

    def emit_1(self, op, src1, dst, comment=None, imm=None):
        instr = IRInstr(
            op=op,
            src1=src1,
            src2=None,
            src3=None,
            src4=None,
            dst=dst,
            imm=imm,
            label=None,
            comment=comment,
        )
        return self.code.append(instr)

    def emit_2(self, op, src1, src2, dst, comment=None):
        instr = IRInstr(
            op=op,
            src1=src1,
            src2=src2,
            src3=None,
            src4=None,
            dst=dst,
            imm=None,
            label=None,
            comment=comment,
        )
        return self.code.append(instr)

    def emit(self, op, src1, src2, src3, src4, dst, comment=None):
        instr = IRInstr(
            op=op,
            src1=src1,
            src2=src2,
            src3=src3,
            src4=src4,
            dst=dst,
            imm=None,
            label=None,
            comment=comment,
        )
        return self.code.append(instr)

    def alloc_reg_for_type(self, ty: IRType) -> Temp:
        reg = Temp(id=self.next_temp_id, ty=ty)
        self.next_temp_id += 1
        return reg

    def compile_block(self, stmts: list[ast.stmt]):
        with self.code.block() as _block:
            for s in stmts:
                self.compile_stmt(s)

    def compile_stmt(self, node):
        if isinstance(node, ast.Assign):
            raise NotImplementedError("Use AnnAssign for typed assignments")
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
            ty = type_of_annotation(node.annotation)

            t = self.compile_expr(target, forced_type=ty)
            v = self.compile_expr(value, forced_type=ty)
            # emit store from v to t
            comment = f"Assign r{v.id}:{ty} to r{t.id}:{ty}"
            self.emit_1(OpCodes.STORE, v, t, comment=comment)
        elif isinstance(node, ast.If):
            self.compile_if(node)
        elif isinstance(node, ast.While):
            self.compile_while(node)
        elif isinstance(node, ast.Return):
            returned_type = self.type_of(node.value)

            ret_reg = self.compile_expr(node.value, forced_type=returned_type)
            self.emit_1(
                OpCodes.RET,
                ret_reg,
                None,
                comment=f"return r{ret_reg.id} : {returned_type}",
            )
        else:
            raise NotImplementedError(type(node))

    def compile_expr(self, node, forced_type=None) -> Temp:
        if isinstance(node, ast.Name):
            if node.id not in self.named_variables:
                if forced_type is not None:
                    # Declare a new temp for this variable with the forced type
                    reg = self.alloc_reg_for_type(forced_type)
                    self.named_variables[node.id] = reg
                else:
                    raise CompileError(
                        node, f"Undefined variable Type '{node.id}'. Type not known."
                    )
            in_env = self.named_variables[node.id]
            if forced_type is not None and in_env.ty != forced_type:
                raise CompileError(
                    node,
                    f"Type mismatch for variable {node.id}: expected {forced_type}, got {in_env.ty}",
                )
            return self.named_variables[node.id]
        if isinstance(node, ast.Attribute):
            if node.attr in ("x", "y", "z", "w"):
                if forced_type is not None and forced_type != IRType.F32:
                    raise RuntimeError(
                        f"Type mismatch: expected {forced_type}, got F32 from attribute access"
                    )
                parent_type = self.type_of(node.value)
                if parent_type not in (IRType.V2, IRType.V3, IRType.V4):
                    raise RuntimeError(
                        f"Attribute access on non-vector type: {parent_type}"
                    )
                reg = self.compile_expr(node.value, forced_type=parent_type)

                if reg.ty in (IRType.V2, IRType.V3, IRType.V4):
                    result_reg = self.alloc_reg_for_type(IRType.F32)
                    # read the x component from a vector into a float
                    opcode = {
                        "x": OpCodes.READ_AXIS_X,
                        "y": OpCodes.READ_AXIS_Y,
                        "z": OpCodes.READ_AXIS_Z,
                        "w": OpCodes.READ_AXIS_W,
                    }[node.attr]
                    self.emit_1(opcode, reg, result_reg)
                    return result_reg

            raise NotImplementedError(type(node))
        if isinstance(node, ast.Constant):
            type_ret = self.type_of(node)
            reg = self.alloc_reg_for_type(type_ret)
            const_index = self.code.add_constant(node.value, type_ret)
            comment = (
                f"load_const [{const_index}] '{node.value}':{type_ret} into r{reg.id}"
            )
            self.emit_1(OpCodes.LOAD_CONST, None, reg, comment=comment, imm=const_index)
            return reg

        if isinstance(node, ast.BinOp):
            left_type = self.type_of(node.left)
            right_type = self.type_of(node.right)
            left_reg = self.compile_expr(node.left, left_type)
            right_reg = self.compile_expr(node.right, right_type)
            result_reg = self.alloc_reg_for_type(self.type_of(node))
            opcode = opcode_for_binop(node.op, left_reg.ty, right_reg.ty)
            comment = (
                f"({opcode.name} r{left_reg.id}, r{right_reg.id}) -> r{result_reg.id}"
            )
            self.emit_2(
                opcode,
                left_reg,
                right_reg,
                result_reg,
                comment=comment,
            )
            return result_reg
        if isinstance(node, ast.UnaryOp):
            operand_type = self.type_of(node.operand)
            operand_reg = self.compile_expr(node.operand, operand_type)
            if isinstance(node.op, ast.USub):
                result_reg = self.alloc_reg_for_type(operand_type)
                opcode = OpCodes.NEG

                comment = f"NEG r{operand_reg.id} -> r{result_reg.id}"
                self.emit_1(opcode, operand_reg, result_reg, comment=comment)
                return result_reg
            raise NotImplementedError(type(node))
        if isinstance(node, ast.Call):
            func = node.func
            args = node.args
            if "id" in func._fields:
                if func.id in ("sin", "abs", "cos"):
                    assert len(args) == 1
                    return_type = self.type_of(args[0])
                    arg_reg = self.compile_expr(args[0], return_type)
                    result_reg = self.alloc_reg_for_type(return_type)

                    opcode = opcode_for_uniop(func.id, return_type)
                    self.emit_1(opcode, arg_reg, result_reg)
                    return result_reg
                elif func.id in VECTOR_CONSTRUCTORS:
                    return self.compile_vec_constructor(
                        node, vec_name=func.id, args=args
                    )
            elif "attr" in func._fields:
                if "value" in func._fields and "id" in func.value._fields:
                    if func.value.id == "glm":
                        if func.attr in VECTOR_CONSTRUCTORS:
                            return self.compile_vec_constructor(
                                node, vec_name=func.attr, args=args
                            )
                        elif func.attr in NATIVE_UNI_OPS_TYPE:
                            assert len(args) == 1
                            return_type = self.type_of(args[0])  #
                            arg_reg = self.compile_expr(args[0], return_type)
                            result_reg = self.alloc_reg_for_type(return_type)
                            opcode = opcode_for_uniop(func.attr, return_type)
                            self.emit_1(
                                opcode,
                                arg_reg,
                                result_reg,
                                comment=f"glm.{func.attr} r{arg_reg.id} -> r{result_reg.id}",
                            )
                            return result_reg
            raise NotImplementedError(type(node))

        if isinstance(node, ast.Compare):
            # left: expr
            # ops: list[cmpop]
            # comparators: list[expr]

            left_type = self.type_of(node.left)
            left_reg = self.compile_expr(node.left, left_type)
            assert len(node.ops) == 1
            assert len(node.comparators) == 1
            right_type = self.type_of(node.comparators[0])
            right_reg = self.compile_expr(node.comparators[0], right_type)

            if left_type != right_type:
                raise CompileError(
                    node, f"Type mismatch in comparison: {left_type} vs {right_type}"
                )

            result_reg = self.alloc_reg_for_type(IRType.BOOL)
            if isinstance(node.ops[0], ast.Gt):
                opcode = OpCodes.CMP_GT
                self.emit_2(opcode, left_reg, right_reg, result_reg)
                return result_reg
            elif isinstance(node.ops[0], ast.GtE):
                opcode = OpCodes.CMP_GTE
                self.emit_2(opcode, left_reg, right_reg, result_reg)
                return result_reg
            elif isinstance(node.ops[0], ast.Lt):
                # a < b  <=>  b > a
                opcode = OpCodes.CMP_GT
                self.emit_2(opcode, right_reg, left_reg, result_reg)
                return result_reg
            elif isinstance(node.ops[0], ast.LtE):
                # a <= b  <=>  b >= a
                opcode = OpCodes.CMP_GTE
                self.emit_2(opcode, right_reg, left_reg, result_reg)
                return result_reg
            else:
                raise NotImplementedError(
                    f"Unsupported comparison operator {node.ops[0]}"
                )
        raise NotImplementedError(type(node))

    def compile_vec_constructor(
        self, node: ast.Call, vec_name: str, args: list[ast.expr]
    ) -> Temp:
        target_vector_dimension = {"vec2": 2, "vec3": 3, "vec4": 4}[vec_name]
        if not len(args) == target_vector_dimension:
            raise CompileError(
                node,
                f"Function 'glm.{vec_name}' expects {target_vector_dimension} arguments, got {len(args)}",
            )
        for arg in args:
            arg_type = self.type_of(arg)
            if arg_type != IRType.F32:
                raise CompileError(
                    node,
                    f"Function 'glm.{vec_name}' expects f32 arguments, got {arg_type}",
                )
        arg_regs = [self.compile_expr(arg, IRType.F32) for arg in args]
        result_type = {
            2: IRType.V2,
            3: IRType.V3,
            4: IRType.V4,
        }[target_vector_dimension]
        result_reg = self.alloc_reg_for_type(result_type)
        # Assuming a constructor call
        comment = f"glm.{vec_name} arg {[r.id for r in arg_regs]} -> r{result_reg.id}"
        if target_vector_dimension == 2:
            self.emit_2(
                OpCodes.STORE_VEC_FROM_SCALAR,
                arg_regs[0],
                arg_regs[1],
                result_reg,
                comment=comment,
            )
        elif target_vector_dimension == 3:
            self.emit(
                OpCodes.STORE_VEC_FROM_SCALAR,
                arg_regs[0],
                arg_regs[1],
                arg_regs[2],
                None,
                result_reg,
                comment=comment,
            )
        elif target_vector_dimension == 4:
            self.emit(
                OpCodes.STORE_VEC_FROM_SCALAR,
                arg_regs[0],
                arg_regs[1],
                arg_regs[2],
                arg_regs[3],
                result_reg,
                comment=comment,
            )
        else:
            raise CompileError(
                node,
                f"Unsupported vector dimension: {target_vector_dimension}",
            )
        return result_reg

    def compile_if(self, node: ast.If):
        # 1. condition
        test_type = self.type_of(node.test)
        if test_type != IRType.BOOL:
            raise CompileError(
                node,
                f"If condition must be of type BOOL, got {test_type}",
            )
        cond_reg = self.compile_expr(node.test, test_type)

        # 2. jump to else if false
        jmp_false_pos = self.emit_2(
            OpCodes.JMP_IF_FALSE, cond_reg, None, None
        )  # target to fill later

        # 3. then block
        self.compile_block(node.body)

        # 4. jump to end (skip else)
        jmp_end_pos = self.emit_2(OpCodes.JMP, None, None, None)  # target to fill later

        # 5. else block
        else_start = self.code.instructions_count()
        self.compile_block(node.orelse)

        # 6. patch false jump to else start
        self.code.patch_target(jmp_false_pos, else_start)

        # 7. patch jump to end
        end_pos = self.code.instructions_count()
        # self.emit_1(
        #    OpCodes.COMMENT,
        #    None,
        #    None,
        #    comment="End of if-else",
        # )
        self.code.patch_target(jmp_end_pos, end_pos)

    def compile_while(self, node: ast.While):
        loop_start = len(self.code)

        cond_reg = self.compile_expr(node.test)

        jmp_exit_pos = self.emit_2(
            OpCodes.JMP_IF_FALSE, cond_reg.index, 0, 0
        )  # patch later

        self.compile_block(node.body)

        self.emit_2(OpCodes.JMP, loop_start, 0, 0)
        exit_pos = len(self.code)
        self.code.patch_target(jmp_exit_pos, exit_pos)

    def parse_args(self, fn_node: ast.FunctionDef):
        for arg in fn_node.args.args:
            arg_name = arg.arg
            assert "annotation" in arg._fields
            arg_annotation = arg.annotation
            try:
                arg_type = type_of_annotation(arg_annotation)
            except NotImplementedError as e:
                raise CompileError(
                    arg,
                    f"Unsupported type annotation for argument '{arg_name}': {arg_annotation}",
                ) from e
            # Allocate a temp for this argument
            arg_temp = self.alloc_reg_for_type(arg_type)
            self.named_variables[arg_name] = arg_temp

    def type_of(self, node: ast.expr, type_args=None) -> IRType:
        if isinstance(node, ast.Constant):
            py_type = type(node.value)
            if py_type in ALLOWED_IR_TYPES:
                return ALLOWED_IR_TYPES[type(node.value)]
            else:
                raise NotImplementedError(f"Constant of type {py_type} not supported")
        elif isinstance(node, ast.BinOp):
            left_type = self.type_of(node.left)
            right_type = self.type_of(node.right)
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                if left_type == right_type:
                    return left_type
                elif left_type in (IRType.F32, IRType.I32) and right_type in (
                    IRType.V2,
                    IRType.V3,
                    IRType.V4,
                ):
                    return right_type
                elif right_type in (IRType.F32, IRType.I32) and left_type in (
                    IRType.V2,
                    IRType.V3,
                    IRType.V4,
                ):
                    return left_type
                else:
                    raise RuntimeError(
                        f"Type mismatch in binary operation: {left_type} vs {right_type}"
                    )
            else:
                raise NotImplementedError(
                    f"Unsupported binary operation {node.op} for types: {left_type}, {right_type}"
                )
        elif isinstance(node, ast.Name):
            if "id" in node._fields:
                if node.id in self.named_variables:
                    return self.named_variables[node.id].ty
                elif node.id in ("abs", "sin", "cos"):
                    if type_args is not None and len(type_args) == 1:
                        return type_args[0]
                    raise CompileError(
                        node, f"Cannot determine return type of function '{node.id}'"
                    )
                elif node.id in PIXEL_VARIABLES_STR_TYPE:  #
                    return PIXEL_VARIABLES_STR_TYPE[node.id]
                elif node.id in GLOBAL_VARIABLES_STR_TYPE:  #
                    return GLOBAL_VARIABLES_STR_TYPE[node.id]
                elif node.id in STR_TO_IRTYPE:  #
                    return STR_TO_IRTYPE[node.id]

            raise RuntimeError(f"Cannot determine type of name'{node.id}'")
        elif isinstance(node, ast.Attribute):
            if node.attr in ("x", "y", "z", "w"):
                value_type = self.type_of(node.value)
                if value_type == IRType.V2:
                    return IRType.F32
                elif value_type == IRType.V3:
                    return IRType.F32
                elif value_type == IRType.V4:
                    return IRType.F32
            elif node.attr in ("sin", "cos"):
                if type_args is not None and len(type_args) == 1:
                    return type_args[0]
                raise CompileError(
                    node,
                    f"Function '{node.attr}' expects one Typed argument, got {type_args}",
                )
            elif node.attr in ("vec3", "vec2", "vec4"):
                count = {"vec2": 2, "vec3": 3, "vec4": 4}[node.attr]
                if type_args is not None and len(type_args) == count:
                    for type_arg in type_args:
                        if type_arg != IRType.F32:
                            raise CompileError(
                                node,
                                f"Function '{node.attr}' expects f32 arguments, got {type_args}",
                            )

                    return {
                        2: IRType.V2,
                        3: IRType.V3,
                        4: IRType.V4,
                    }[count]

                raise CompileError(
                    node,
                    f"Function '{node.attr}' expects {count} f32 arguments, got {type_args}",
                )
        elif isinstance(node, ast.Call):
            func = node.func
            args = node.args
            type_args = [self.type_of(arg) for arg in args]
            func_type = self.type_of(func, type_args)
            return func_type
        elif isinstance(node, ast.Compare):
            return IRType.BOOL
        # elif isinstance(node, ast.Return):
        elif isinstance(node, ast.UnaryOp):
            operand_type = self.type_of(node.operand)
            if isinstance(node.op, ast.USub):
                return operand_type
            else:
                raise NotImplementedError(f"Unsupported unary operation {node.op}")
        raise NotImplementedError(f"Cannot determine type of node: {node}")


def compile_ttsl(src, function_name, globals_dict: Dict) -> TTSLCompilerContext:
    # Parse it into an AST
    tree = ast.parse(src)

    # 3. Find the FunctionDef node corresponding to `fn`
    # `ast.parse` returns a Module with .body list
    fn_node = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            fn_node = node
            break

    if fn_node is None:
        raise RuntimeError("Could not find function node in AST")

    return compile_ttsl_function(fn_node, globals_dict)


def compile_ttsl_function(
    fn_node: ast.FunctionDef, globals_dict: Dict
) -> TTSLCompilerContext:
    tree = CleanPythonTreePass().visit(fn_node)
    tree = ast.fix_missing_locations(tree)

    typed_globals = {}
    for k, pytype in globals_dict.items():
        if pytype not in ALLOWED_IR_TYPES:
            raise RuntimeError(f"Unsupported global variable type: {pytype}")
        typed_globals[k] = ALLOWED_IR_TYPES[pytype]
    sc = TTSLCompilerContext(typed_globals)
    sc.parse_args(fn_node)
    sc.compile_block(tree.body)
    sc.code.fix_jump_targets()
    return sc


def type_of_annotation(arg_annotation) -> IRType:
    if isinstance(arg_annotation, ast.Attribute):
        return IRType.from_str(arg_annotation.attr)
    elif isinstance(arg_annotation, ast.Name):
        return IRType.from_str(arg_annotation.id)
    raise NotImplementedError(f"Unsupported annotation type: {arg_annotation}")


def opcode_for_binop(op, left_type: IRType, right_type: IRType) -> OpCodes:
    if isinstance(op, ast.Add):
        return OpCodes.ADD
    if isinstance(op, ast.Sub):
        return OpCodes.SUB
    if isinstance(op, ast.Mult):
        return OpCodes.MUL
    if isinstance(op, ast.Div):
        return OpCodes.DIV
    raise NotImplementedError(
        f"Unsupported binary operation for types: {left_type}, {right_type}"
    )


def opcode_for_uniop(op_name: str, operand_type: IRType) -> OpCodes:
    if operand_type in (IRType.BOOL,):
        raise NotImplementedError(
            f"Unsupported unary operation for type: {operand_type}"
        )
    elif operand_type in (IRType.F32, IRType.I32, IRType.V2, IRType.V3, IRType.V4):
        name_to_op = {
            "sin": OpCodes.SIN,
            "abs": OpCodes.ABS,
        }
        if op_name in name_to_op:
            return name_to_op[op_name]
    raise NotImplementedError(f"Unsupported unary operation: {op_name}")


class SSARenamer:
    def __init__(
        self,
        cfg: CFG,
        ttsl_compiler: TTSLCompilerContext,
        dom_tree: Dict[NodeID, List[NodeID]],
        entry_idx: NodeID,
    ):
        self.cfg = cfg
        self.ttsl_compiler = ttsl_compiler
        self.ir: IRProgram = ttsl_compiler.code
        self.dom_tree = dom_tree
        self.entry_idx = entry_idx

        # var -> stack of TempID (SSA versions)
        self.stack: Dict[SSAVarID, List[TempID]] = {}

        # var -> counter (optional; if you just use global temp allocator, you don’t need this)
        # self.var_version: Dict[Any, int] = {}
        self.__allocated_temps: List[Temp] = []

    def _has_allocated_temp_for_id(self, tid: TempID) -> bool:
        # Check if allocated Temp exists for given TempID
        return any(_t.id == tid for _t in self.__allocated_temps)

    def _allocated_temps_for_id(self, tid: TempID) -> Temp:
        # Find allocated Temp by its ID or raise Exception if not found
        found_temps = [_t for _t in self.__allocated_temps if _t.id == tid]
        if not found_temps:
            raise RuntimeError(f"TempID {tid} not found in allocated temps")
        return found_temps[0]

    def new_temp(self, ty: IRType) -> Temp:
        """Allocate a fresh TempID."""
        assert ty is not None
        temp = self.ttsl_compiler.alloc_reg_for_type(ty)
        self.__allocated_temps.append(temp)
        return temp

    # ---------- Stack helpers ----------
    def push(self, var: SSAVarID, tid: TempID) -> None:
        self.stack.setdefault(var, []).append(tid)

    def pop(self, var: SSAVarID) -> TempID:
        return self.stack[var].pop()

    def top(self, var: SSAVarID) -> Optional[TempID]:
        st = self.stack.get(var)
        return st[-1] if st else None

    # ---------- Operand rewriting ----------
    def rewrite_use(self, op: Optional[IROperand]) -> Optional[IROperand]:
        """Rewrite a use operand: VarRef(v) -> TempRef(current_version(v))."""
        if op is None:
            return None

        if is_operand_ssavar(op):
            v = op
            t = self.top(v)
            if t is None:
                # Uninitialized use:
                raise ValueError(f"SSA rename: use of variable {v!r} before definition")
            return self._allocated_temps_for_id(t)
            # return TempID(t)
        elif isinstance(op, Temp):
            # TODO if op is a temps which ID is actually SSAVarID string
            maybe_variable = self.ttsl_compiler.temp_id_to_variable(op.id)
            if maybe_variable is not None:
                v = maybe_variable
                t = self.top(v)
                if t is None:
                    raise ValueError(
                        f"SSA rename: use of variable {v!r} before definition"
                    )
                if self._has_allocated_temp_for_id(t):
                    return self._allocated_temps_for_id(t)
                else:
                    return op
                # return TempID(t)
        return op  # TempRef/ConstRef unchanged

    def is_var_def(self, dst: Optional[IROperand]) -> bool:
        """True if this instruction defines a variable (dst is VarRef)."""

        if isinstance(dst, Temp):
            if self.ttsl_compiler.temp_id_to_variable(dst.id) is not None:
                # This is a named variable (not a temporary)
                return True
        elif isinstance(dst, int):
            if self._has_allocated_temp_for_id(dst):
                return True
        return dst is not None and is_operand_ssavar(dst)

    def rewrite_def(self, dst: IROperand, ty: IRType) -> Tuple[SSAVarID, Temp]:
        """
        Rewrite a definition: VarRef(v) = ... becomes TempRef(new) = ...
        Push the new temp as current version for v.
        """

        assert (
            is_operand_ssavar(dst)
            or self.ttsl_compiler.temp_id_to_variable(dst.id) is not None
        )
        v = self.ttsl_compiler.temp_id_to_variable(dst.id)
        new_temp = self.new_temp(ty)
        new_tid = new_temp.id
        self.push(v, new_tid)

        return v, self._allocated_temps_for_id(new_tid)

    # ---------- Instruction rewriting ----------
    def rewrite_instruction(self, instr: IRInstr) -> List[Any]:
        """
        Rewrite one instruction in-place.

        Returns list of variables pushed (so we can pop when leaving the block).
        """
        pushed_vars: List[SSAVarID] = []
        if instr.op == OpCodes.JMP or instr.op == OpCodes.JMP_IF_FALSE:
            # Jump targets are not rewritten here
            return pushed_vars
        # Rewrite uses first
        instr.src1 = self.rewrite_use(instr.src1)
        instr.src2 = self.rewrite_use(instr.src2)
        instr.src2 = self.rewrite_use(instr.src3)
        instr.src2 = self.rewrite_use(instr.src4)
        # If you have extra operands, rewrite them too.

        # Rewrite def if dst is a VarRef

        if self.is_var_def(instr.dst):
            ty = instr.dst.ty

            v, new_dst = self.rewrite_def(instr.dst, ty=ty)
            instr.dst = new_dst
            pushed_vars.append(v)

        return pushed_vars

    # ---------- Phi rewriting ----------
    def define_phi_dsts(self, node_id: NodeID) -> List[SSAVarID]:
        """
        At block entry: for each phi(var) in this block,
        allocate a new TempID, assign phi.dst, push it.
        Return list of vars pushed for popping later.
        """
        node = self.cfg.nodes[node_id]
        pushed: List[SSAVarID] = []

        for var, phi in node.phis.items():
            # Allocate new SSA version for the phi result

            temp = self.new_temp(self.ttsl_compiler.named_variables[phi.dst].ty)
            tid = temp.id
            phi.dst = temp
            self.push(var, tid)
            pushed.append(var)

        return pushed

    def fill_phi_operands_from_block(self, block_idx: int) -> None:
        """For each successor S of block_idx, for each phi(var) in S, set operand for
        predecessor block_idx to current top(var)."""
        for succ_idx in self.cfg.successors(block_idx):
            succ_node = self.cfg.nodes[succ_idx]
            if succ_node is None:
                continue

            for var, phi in succ_node.phis.items():
                cur = self.top(var)
                if cur is None:
                    raise ValueError(
                        f"SSA rename: no current version for var {var!r} "
                        f"when filling phi operand from pred {block_idx} -> {succ_idx}"
                    )
                phi.phi_operands[block_idx] = cur

    # ---------- Main traversal ----------
    def rename(self) -> None:
        """
        Execute SSA renaming starting at entry (init) block.

        You MUST pre-seed stacks for globals/params if they’re representable as
        variables.
        """
        self._rename_block(self.entry_idx)

    def _rename_block(self, nodeId: NodeID) -> None:
        node = self.cfg.nodes[nodeId]
        if node is None:
            return

        # Track what we pushed in THIS block so we can pop on exit
        pushed_vars: List[SSAVarID] = []

        # 1) Phi defs at top of block
        pushed_vars.extend(self.define_phi_dsts(nodeId))

        # 2) Rewrite normal instructions within the block
        for instr in node.instrs():
            pushed_vars.extend(self.rewrite_instruction(instr))

        # 3) Fill phi operands in successors
        self.fill_phi_operands_from_block(nodeId)

        # 4) Recurse into dominator tree children
        for child in self.dom_tree.get(nodeId, []):
            self._rename_block(child)

        # 5) Pop versions defined in this block (in reverse push order)
        for v in reversed(pushed_vars):
            self.pop(v)


class CompilationPass:
    def __init__(self, ttsl_compiler: TTSLCompilerContext):
        self.ttsl_compiler = ttsl_compiler


class PassSSARenamer(CompilationPass):
    def run(self) -> None:
        ttsl_compiler = self.ttsl_compiler
        cfg = ttsl_compiler.cfg
        # 1) Build dominators/idom/dom-tree (you have it)
        dom = cfg.compute_dominators()
        # console.print("compute_dominators:", dom)
        idom = cfg.compute_immediate_dominators(cfg.init_idx, dom)
        # console.print("idom Tree:", idom)
        dom_tree = cfg.dominator_tree(cfg.init_idx, idom=idom)
        # console.print("Dominator Tree:", dom_tree)
        dof = cfg.compute_dominance_frontiers(dom, idom)
        # console.print("compute_dominance_frontiers :", dof)

        # 1.b) Insert phi nodes
        cret = cfg.cytron_insert_phi_nodes(
            ttsl_compiler.ssa_var_definitions, ttsl_compiler.named_variables, dof
        )
        # print("cytron_insert_phi_nodes :", cret)
        for node_id, phis in cret.items():
            # console.print(f"Node {node_id} phi nodes:")
            cfg.nodes[node_id].phis = phis
            # for var, phi_instr in phis.items():
            #     pass
            #     #console.print(f"  Var {var}: {phi_instr}")

        # 2) Run renaming
        renamer = SSARenamer(cfg, ttsl_compiler, dom_tree, entry_idx=cfg.init_idx)

        # IMPORTANT: Seed stacks for variables that exist at entry (params/globals)
        # If params/globals are referenced as VarRef("uv"), VarRef("time"), etc.,
        # We must push an initial version for each, pointing to their existing temp/register temp.
        for name, ty in ttsl_compiler.allways_present_variables_at_init().items():
            existing_temp = ttsl_compiler.named_variables[name]
            # console.print(
            #     f"Seeding variable {name!r} at entry with existing temp id {existing_temp.id}"
            # )
            renamer.push(name, existing_temp.id)
        # renamer.push("time", existing_time_tempid)

        renamer.rename()
