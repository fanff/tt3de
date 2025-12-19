# -*- coding: utf-8 -*-
from dataclasses import dataclass
from collections import defaultdict
import ast
from typing import Any, Dict, List, Optional, Tuple, Set

from pyglm import glm

from tt3de.ttsl.ttisa.low_level_def import generate_all_forms, Form
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
    CFGNode,
    build_cfg_from_ir,
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
PIXELVAR_TTSL_UV0: str = "ttsl_uv0"
PIXELVAR_TTSL_UV1: str = "ttsl_uv1"
ON_SCREEN_POSITION_VAR_NAME: str = "pos"

GLOBAL_VAR_SET = {
    GLOBAL_VAR_TTSL_TIME,
    PIXELVAR_TTSL_UV0,
    PIXELVAR_TTSL_UV1,
    ON_SCREEN_POSITION_VAR_NAME,
}

GLOBAL_VARIABLES_STR_TYPE = {
    GLOBAL_VAR_TTSL_TIME: IRType.F32,
}

PIXEL_VARIABLES_STR_TYPE = {
    PIXELVAR_TTSL_UV0: IRType.V2,
    PIXELVAR_TTSL_UV1: IRType.V2,
    ON_SCREEN_POSITION_VAR_NAME: IRType.V2,
}

NATIVE_UNI_OPS_TYPE = {
    "sin": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "cos": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "tan": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "abs": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "neg": (IRType.F32, IRType.V2, IRType.V3, IRType.V4),
    "norm": (IRType.V2, IRType.V3, IRType.V4),
}

GLM_TOOLS = {
    "mix": (
        (IRType.V2, IRType.V3, IRType.V4),  # input types x
        (IRType.V2, IRType.V3, IRType.V4),  # input types y
        (IRType.F32),  # input type a
    ),
    "mix_vec": (
        (IRType.V2, IRType.V3, IRType.V4),
        (IRType.V2, IRType.V3, IRType.V4),
        (IRType.V2, IRType.V3, IRType.V4),
    ),
    "cross": (
        (IRType.V3,),
        (IRType.V3,),
    ),
    "dot": (
        (IRType.V2, IRType.V3, IRType.V4),
        (IRType.V2, IRType.V3, IRType.V4),
    ),
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
        self._temp_collection: List[Temp] = []

        # place holder for later passes
        self.cfg: CFG | None = None
        self.ssa_var_definitions: Dict[SSAVarID, Set[NodeID]] = {}
        self.const_pool: dict[int, Tuple[Any, IRType]] = {}

        # Predefine some variables
        for name, ty in self.always_present_variables_at_init().items():
            self.named_variables[name] = self.alloc_temp_for_type(ty)
        for name, ty in self.globals.items():
            self.named_variables[name] = self.alloc_temp_for_type(ty)

    def temp_id_to_variable(self, temp_id: TempID) -> Optional[SSAVarID]:
        for var_name, temp in self.named_variables.items():
            if temp.id == temp_id:
                return var_name
        return None

    def always_present_variables_at_init(self) -> Dict[str, IRType]:
        return self.always_present_variables()

    @classmethod
    def always_present_variables(cls) -> Dict[str, IRType]:
        d = {}
        d.update(PIXEL_VARIABLES_STR_TYPE)
        d.update(GLOBAL_VARIABLES_STR_TYPE)
        return d

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

    def alloc_temp_for_type(self, ty: IRType) -> Temp:
        reg = Temp(id=self.next_temp_id, ty=ty)
        self._temp_collection.append(reg)
        self.next_temp_id += 1
        return reg

    def get_tempid_type(self, tempid: TempID) -> IRType:
        for temp in self._temp_collection:
            if temp.id == tempid:
                return temp.ty
        raise RuntimeError(f"TempID {tempid} not found")

    def find_temp_by_id(self, tempid: TempID) -> Temp:
        for temp in self._temp_collection:
            if temp.id == tempid:
                return temp
        raise RuntimeError(f"TempID {tempid} not found")

    def compile_block(self, stmts: list[ast.stmt]):
        with self.code.block() as _block:
            for s in stmts:
                self.compile_stmt(s)

    def compile_stmt(self, node):
        if isinstance(node, ast.Assign):
            if not len(node.targets) == 1:
                raise CompileError(node, "Multiple assignment targets not supported")
            target = node.targets[0]
            value = node.value
            value_type = self.type_of(value)
            t = self.compile_expr(target, forced_type=value_type)
            v = self.compile_expr(value, forced_type=value_type)
            # emit store from v to t
            comment = f"r{t.id}:{value_type} <- r{v.id}:{value_type}"
            self.emit_1(OpCodes.STORE, v, t, comment=comment)
            # raise NotImplementedError("Use AnnAssign for typed assignments")
        elif isinstance(node, ast.AnnAssign):
            target = node.target

            value = node.value
            value_type = self.type_of(value)

            ty = type_of_annotation(node.annotation)

            if not (value_type == ty):
                raise CompileError(
                    node,
                    f"Type mismatch in assignment: expected {ty}, got {value_type}",
                )

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
                    reg = self.alloc_temp_for_type(forced_type)
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
                    result_reg = self.alloc_temp_for_type(IRType.F32)
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
            reg = self.alloc_temp_for_type(type_ret)
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
            result_reg = self.alloc_temp_for_type(self.type_of(node))
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
                result_reg = self.alloc_temp_for_type(operand_type)
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
                    result_reg = self.alloc_temp_for_type(return_type)

                    opcode = opcode_for_uniop(func.id, return_type)
                    self.emit_1(opcode, arg_reg, result_reg)
                    return result_reg
                elif func.id in VECTOR_CONSTRUCTORS:
                    return self.compile_vec_constructor(
                        node, vec_name=func.id, args=args
                    )
                elif func.id in GLM_TOOLS:
                    return self.compile_glm_tool_call(node, func.id, args)
                raise CompileError(node, f"Unsupported function call '{func.id}'")
            elif "attr" in func._fields:
                if "value" in func._fields and "id" in func.value._fields:
                    if func.value.id == "glm":
                        assert isinstance(func.attr, str)
                        func_name: str = func.attr
                        if func_name in VECTOR_CONSTRUCTORS:
                            return self.compile_vec_constructor(
                                node, vec_name=func_name, args=args
                            )
                        elif func_name in NATIVE_UNI_OPS_TYPE:
                            assert len(args) == 1
                            return_type = self.type_of(args[0])  #
                            arg_reg = self.compile_expr(args[0], return_type)
                            result_reg = self.alloc_temp_for_type(return_type)
                            opcode = opcode_for_uniop(func_name, return_type)
                            self.emit_1(
                                opcode,
                                arg_reg,
                                result_reg,
                                comment=f"glm.{func_name} r{arg_reg.id} -> r{result_reg.id}",
                            )
                            return result_reg
                        elif func_name in GLM_TOOLS:
                            return self.compile_glm_tool_call(node, func_name, args)
                        raise CompileError(
                            node, f"Unsupported glm function call '{func_name}'"
                        )
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

            result_reg = self.alloc_temp_for_type(IRType.BOOL)
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
        result_reg = self.alloc_temp_for_type(result_type)
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

    def compile_glm_tool_call(
        self, node: ast.Call, func_attr: str, args: list[ast.expr]
    ) -> Temp:
        tool_signatures = GLM_TOOLS[func_attr]
        if len(args) != len(tool_signatures):
            raise CompileError(
                node,
                f"Function 'glm.{func_attr}' expects {len(tool_signatures)} arguments, got {len(args)}",
            )
        if func_attr == "mix":
            # glm.mix(x: vecN, y: vecN, a: f32) -> vecN
            x_type = self.type_of(args[0])
            y_type = self.type_of(args[1])
            a_type = self.type_of(args[2])
            if x_type != y_type:
                raise CompileError(
                    node,
                    f"Function 'glm.{func_attr}' expects first two arguments of same type, got {x_type} and {y_type}",
                )
            if a_type != IRType.F32:
                raise CompileError(
                    node,
                    f"Function 'glm.{func_attr}' expects third argument of type f32, got {a_type}",
                )
            if x_type not in tool_signatures[0]:
                raise CompileError(
                    node,
                    f"Function 'glm.{func_attr}' does not support argument type {x_type}",
                )
            x_reg = self.compile_expr(args[0], x_type)
            y_reg = self.compile_expr(args[1], y_type)
            a_reg = self.compile_expr(args[2], IRType.F32)
            result_reg = self.alloc_temp_for_type(x_type)
            comment = f"glm.{func_attr} r{x_reg.id}, r{y_reg.id}, r{a_reg.id} -> r{result_reg.id}"
            self.emit(
                OpCodes.MIX,
                x_reg,
                y_reg,
                a_reg,
                None,
                result_reg,
                comment=comment,
            )
            return result_reg
        raise CompileError(
            node,
            f"Unsupported glm tool function '{func_attr}'",
        )

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
            arg_temp = self.alloc_temp_for_type(arg_type)
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
        temp = self.ttsl_compiler.alloc_temp_for_type(ty)
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
            assert isinstance(op, str)
            v = op
            t = self.top(v)
            if t is None:
                # Uninitialized use:
                raise ValueError(f"SSA rename: use of variable {v!r} before definition")
            return self._allocated_temps_for_id(t)

        elif isinstance(op, Temp):
            #  if op is a temps which ID is actually SSAVarID string
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
        assert isinstance(v, str)
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
        instr.src3 = self.rewrite_use(instr.src3)
        instr.src4 = self.rewrite_use(instr.src4)
        # If you have extra operands, rewrite them too.

        # Rewrite def if dst is a VarRef

        if self.is_var_def(instr.dst):
            assert isinstance(instr.dst, Temp)
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

        assert self.ttsl_compiler.named_variables is not None

        for var, phi in node.phis.items():
            # Allocate new SSA version for the phi result
            assert isinstance(phi.dst, SSAVarID)
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
                assert isinstance(phi.phi_operands, Dict)
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
        self.ttsl_compiler: TTSLCompilerContext = ttsl_compiler


class PassSSARenamer(CompilationPass):
    def __init__(self, ttsl_compiler: TTSLCompilerContext):
        super().__init__(ttsl_compiler)

    def run(self) -> None:
        ttsl_compiler = self.ttsl_compiler
        assert isinstance(ttsl_compiler.cfg, CFG)
        cfg = ttsl_compiler.cfg
        # 1) Build dominators/idom/dom-tree (you have it)
        dom = cfg.compute_dominators()
        # console.print("compute_dominators:", dom)
        idom = cfg.compute_immediate_dominators(cfg.init_idx, dom)
        # console.print("idom Tree:", idom)
        dom_tree = cfg.dominator_tree(cfg.init_idx, idom=idom)
        # console.print("Dominator Tree:", dom_tree)
        # dof = cfg.compute_dominance_frontiers(dom,idom)
        dof = cfg.compute_dominance_frontiers(cfg.init_idx, idom, dom)
        # console.print("compute_dominance_frontiers :", dof)

        # 1.b) Insert phi nodes

        ssavars_defs = ttsl_compiler.ssa_var_definitions
        cret = cfg.cytron_insert_phi_nodes(
            ssavars_defs, ttsl_compiler.named_variables, dof
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
        for name, ty in ttsl_compiler.always_present_variables_at_init().items():
            existing_temp = ttsl_compiler.named_variables[name]
            # console.print(
            #     f"Seeding variable {name!r} at entry with existing temp id {existing_temp.id}"
            # )
            renamer.push(name, existing_temp.id)
        # renamer.push("time", existing_time_tempid)

        renamer.rename()


# post optimization passes


class PassPhiNodeLowering(CompilationPass):
    @dataclass(frozen=True)
    class Copy:
        dst: TempID
        src: TempID

    def run(self) -> None:
        ttsl_compiler = self.ttsl_compiler
        cfg = ttsl_compiler.cfg
        assert isinstance(cfg, CFG)

        # ------------------------------------------------------------------
        # 1) Collect edge copy sets: (pred, block) -> [Copy(dst, src)]
        # ------------------------------------------------------------------
        edge_copies: Dict[Tuple[NodeID, NodeID], List[PassPhiNodeLowering.Copy]] = (
            defaultdict(list)
        )

        for b in cfg.all_nodes():
            block = cfg.nodes[b]
            if block is None:
                continue

            # Scan block instructions; collect phi copies; drop phi from block
            new_instrs: List[IRInstr] = []
            for instr in block.instrs():
                if instr.op == OpCodes.PHI:
                    # dst is the phi result temp
                    phi_dst = instr.dst
                    assert isinstance(phi_dst, Temp), "PHI dst must be Temp"
                    phi_dst_id: TempID = phi_dst.id

                    # operands: pred_node_id -> TempID
                    for pred_id, src_tid in instr.phi_operands.items():
                        assert isinstance(src_tid, int)
                        edge_copies[(pred_id, b)].append(
                            PassPhiNodeLowering.Copy(dst=phi_dst_id, src=src_tid)
                        )
                else:
                    new_instrs.append(instr)

            block.set_instrs(new_instrs)

        # Early exit: no phis
        if not edge_copies:
            return

        # ------------------------------------------------------------------
        # 2) For each edge with copies: split critical edges as needed
        #    and insert copy sequences (parallel-copy resolved).
        # ------------------------------------------------------------------
        for (pred_id, succ_id), copies in list(edge_copies.items()):
            # Skip trivial no-op copies (dst==src)
            copies = [c for c in copies if c.dst != c.src]
            if not copies:
                continue

            pred = cfg.nodes[pred_id]
            succ = cfg.nodes[succ_id]
            if pred is None or succ is None:
                continue

            pred_succs = cfg.successors(pred_id)
            succ_preds = cfg.predecessors(succ_id)

            is_critical = (len(pred_succs) > 1) and (len(succ_preds) > 1)

            if is_critical:
                # Split edge pred->succ into pred->split->succ
                split_id = self._split_edge(cfg, pred_id, succ_id)

                split_block = cfg.nodes[split_id]
                # Insert copies into split block (safe, executes only on that edge)
                self._emit_parallel_copies_into_block(
                    ttsl_compiler, split_block, copies
                )

            else:
                # Non-critical: insert into predecessor before terminator
                self._emit_parallel_copies_before_terminator(
                    ttsl_compiler, pred, copies
                )

    # ----------------------------------------------------------------------
    # Edge splitting
    # ----------------------------------------------------------------------
    def _split_edge(self, cfg: "CFG", pred_id: NodeID, succ_id: NodeID) -> NodeID:
        """
        Create a new block S such that pred->succ becomes pred->S->succ.

        Update:
          - pred terminator target(s)
          - CFG arcs
        """
        split_name = f"_split_{pred_id}_{succ_id}"
        split_node = CFGNode(name=split_name)
        split_id = cfg.add_node(split_node)

        # Split block will just jump to succ (terminator)
        split_node.set_instrs(
            [IRInstr.uniop(op=OpCodes.JMP, dst=cfg.nodes[succ_id].name)]
        )

        # Update predecessor terminator(s): replace succ_id with split_id
        self._replace_edge_in_terminator(
            cfg.nodes[pred_id], old_succ=succ_id, new_succ=split_id
        )

        # Update CFG arcs: remove (pred,succ), add (pred,split), (split,succ)
        cfg.remove_arc_idx(pred_id, succ_id)
        cfg.add_arc_idx(pred_id, split_id)
        cfg.add_arc_idx(split_id, succ_id)

        return split_id

    def _replace_edge_in_terminator(
        self, pred_node: "CFGNode", old_succ: NodeID, new_succ: NodeID
    ) -> None:
        """
        Replace successor target inside pred_node's terminator. You MUST adapt this to
        your exact terminator encoding.

        Common cases:
          - JMP: instr.target
          - JMP_IF_FALSE: instr.target (false) and/or instr.target_true
        """
        term = pred_node.get_terminator()
        if term is None:
            # fallthrough blocks: in your CFG world, these typically have implicit successor;
            # but since you said you use NodeID targets, you likely always have terminators.
            return

        cfg = self.ttsl_compiler.cfg
        assert isinstance(cfg, CFG)

        old_succ_name = cfg.nodes[old_succ].name
        new_succ_name = cfg.nodes[new_succ].name
        if term.op == OpCodes.JMP:
            if term.dst == old_succ_name:
                term.dst = new_succ_name

        elif term.op == OpCodes.JMP_IF_FALSE:
            # Adapt depending on your representation:
            # Example: term.target is the "false" target
            if term.dst == old_succ_name:
                term.dst = new_succ_name
            # # If you also store true-target:
            # if hasattr(term, "target_true") and term.target_true == old_succ_name:
            #     term.target_true = new_succ_name

        else:
            # RET/CRASH shouldn't have successors
            pass

    # ----------------------------------------------------------------------
    # Parallel copy emission
    # ----------------------------------------------------------------------
    def _emit_parallel_copies_before_terminator(
        self,
        ttsl_compiler: "TTSLCompilerContext",
        pred_node: "CFGNode",
        copies: List[Copy],
    ) -> None:
        seq = self._resolve_parallel_copies(ttsl_compiler, copies)
        for move in seq:
            pred_node.insert_before_terminator(move)

    def _emit_parallel_copies_into_block(
        self,
        ttsl_compiler: "TTSLCompilerContext",
        block: "CFGNode",
        copies: List[Copy],
    ) -> None:
        """Insert into block body *before* its terminator (block is a split node with
        JMP succ)."""
        seq = self._resolve_parallel_copies(ttsl_compiler, copies)
        for move in seq:
            block.insert_before_terminator(move)

    def _resolve_parallel_copies(
        self,
        ttsl_compiler: "TTSLCompilerContext",
        copies: List[Copy],
    ) -> List["IRInstr"]:
        """
        Resolve a set of parallel copies into a sequence of STORE (or MOVE)
        instructions. Handles cycles using a scratch temp.

        copies: list of (dst <- src) that must behave as if executed in parallel.
        """
        # Build mutable maps
        pending: Dict[TempID, TempID] = {c.dst: c.src for c in copies if c.dst != c.src}
        if not pending:
            return []

        out: List[IRInstr] = []

        def emit_store(dst: TempID, src: TempID) -> None:
            dst_temp = self.ttsl_compiler.find_temp_by_id(dst)
            src_temp = self.ttsl_compiler.find_temp_by_id(src)
            out.append(IRInstr.uniop(op=OpCodes.STORE, dst=dst_temp, src=src_temp))

        while pending:
            # Find an acyclic move: src not currently a dst of any pending move
            progress = False
            for dst, src in list(pending.items()):
                if src not in pending.keys():
                    emit_store(dst, src)
                    del pending[dst]
                    progress = True
            if progress:
                continue

            # Cycle exists. Break it using a scratch temp:
            # Choose any dst in the cycle.
            cycle_dst = next(iter(pending.keys()))
            cycle_src = pending[cycle_dst]

            # Allocate scratch of the right type.
            # You need a way to get temp type; adapt to your compiler.
            dst_ty = ttsl_compiler.get_tempid_type(cycle_dst)
            scratch = ttsl_compiler.alloc_temp_for_type(dst_ty)

            # scratch = cycle_src
            emit_store(scratch.id, cycle_src)

            # Now replace all occurrences of cycle_src in pending sources with scratch
            for d in list(pending.keys()):
                if pending[d] == cycle_src:
                    pending[d] = scratch.id

            # Now cycle_dst <- scratch is acyclic and will be emitted in the next loop iteration

        return out


class CFGSimplifyPass(CompilationPass):
    def run(self) -> None:
        ttsl_compiler = self.ttsl_compiler
        _cfg = ttsl_compiler.cfg


RegisterAddress = Tuple[IRType, int]  # (type, register_id)


@dataclass
class RegisterAllocationResult:
    var_names_to_registers: Dict[str, RegisterAddress]
    tempids_to_registers: Dict[TempID, RegisterAddress]
    const_id_to_registers: Dict[int, Tuple[RegisterAddress, Any]]


class RegisterAllocatorPass(CompilationPass):
    def run(self) -> RegisterAllocationResult:
        ttsl_compiler = self.ttsl_compiler
        cfg = ttsl_compiler.cfg
        assert isinstance(cfg, CFG)

        # count of registers per type
        register_counts: dict[IRType, int] = {
            IRType.BOOL: 32,
            IRType.I32: 32,
            IRType.F32: 32,
            IRType.V2: 32,
            IRType.V3: 32,
            IRType.V4: 32,
        }
        allocated_registers: Dict[IRType, Set[int]] = {}

        def next_free_register(ty: IRType) -> int:
            used = allocated_registers.setdefault(ty, set())
            for reg_id in range(1, register_counts[ty] + 1):
                if reg_id not in used:
                    used.add(reg_id)
                    return reg_id
            raise RuntimeError(f"No free registers available for type {ty}")

        # allocate registers for all variables first
        named_variables = ttsl_compiler.named_variables
        assert isinstance(named_variables, Dict)

        var_names_to_registers: Dict[str, RegisterAddress] = {}
        tempids_to_registers: Dict[TempID, RegisterAddress] = {}

        for var_name, temp in named_variables.items():
            assert isinstance(temp, Temp)
            assert isinstance(temp.ty, IRType)
            assert isinstance(var_name, str)

            idx = next_free_register(temp.ty)
            var_names_to_registers[var_name] = (temp.ty, idx)
            tempids_to_registers[temp.id] = (temp.ty, idx)

        # Then allocate registers for constants (because OpCode can't carry the constant value)
        const_pool = ttsl_compiler.const_pool
        assert const_pool is not None
        const_id_to_registers: Dict[int, Tuple[RegisterAddress, Any]] = {}

        # seek LoadConst Instructions and map their temps to the allocated registers
        for node_id, node in cfg.node_items():
            for instr in node.instrs():
                assert instr.byte_code is not None
                assert len(instr.byte_code) == 6

                if instr.op == OpCodes.LOAD_CONST:
                    # Then rewrite the LOADCONST opcode into a STORE to the allocated register
                    const_id = instr.imm
                    assert isinstance(const_id, int)
                    if const_id in const_id_to_registers:
                        pass
                    # reg_id, const_ty, pyvalue = const_id_to_registers[const_id]
                    constant_dst_temp = instr.dst
                    assert isinstance(constant_dst_temp, Temp)
                    assert const_id in const_pool

                    (pyvalue, const_ty) = const_pool[const_id]
                    const_temp_id = constant_dst_temp.id
                    const_temp_ty = constant_dst_temp.ty

                    assert (
                        const_temp_ty == const_ty
                    )  # type matches between temp and pool

                    if const_temp_id not in tempids_to_registers:
                        next_reg_id = next_free_register(constant_dst_temp.ty)
                        tempids_to_registers[const_temp_id] = (
                            constant_dst_temp.ty,
                            next_reg_id,
                        )

                    const_id_to_registers[const_id] = (
                        tempids_to_registers[const_temp_id],
                        pyvalue,
                    )

                    # now all necessary constants have assigned registers

        # Then simple register allocation: map each Temp to a unique register ID
        for node_id, node in cfg.node_items():
            for instr in node.instrs():
                if instr.op in (OpCodes.LABEL, OpCodes.COMMENT):
                    continue
                # Allocate registers for src operands
                for src in [instr.src1, instr.src2, instr.src3, instr.src4]:
                    if src is None:
                        continue
                    elif isinstance(src, Temp):
                        if src.id not in tempids_to_registers:
                            next_reg_id = next_free_register(src.ty)
                            tempids_to_registers[src.id] = (src.ty, next_reg_id)
                    else:
                        raise RuntimeError(
                            f"Unexpected source operand type for register allocation: {src}"
                        )

                if instr.op not in (OpCodes.JMP, OpCodes.JMP_IF_FALSE):
                    # Allocate register for dst operand
                    dst = instr.dst
                    if instr.op in (OpCodes.RET,):
                        continue  # no dst operand
                    elif isinstance(dst, Temp):
                        if dst.id not in tempids_to_registers:
                            next_reg_id = next_free_register(dst.ty)
                            tempids_to_registers[dst.id] = (dst.ty, next_reg_id)
                    else:
                        raise RuntimeError(
                            f"Unexpected dst operand type for register allocation: {dst}"
                        )

        return RegisterAllocationResult(
            var_names_to_registers=var_names_to_registers,
            tempids_to_registers=tempids_to_registers,
            const_id_to_registers=const_id_to_registers,
        )


class PassNormalizeTerminators(CompilationPass):
    def run(self) -> None:
        cfg = self.ttsl_compiler.cfg
        assert isinstance(cfg, CFG)
        cfg.remove_node(cfg.end_idx)  #
        for b in cfg.all_nodes():
            node = cfg.nodes[b]
            if node is None:
                continue

            term = node.get_terminator()
            if term is not None:
                continue

            succs = [s for s in cfg.successors(b) if cfg.nodes[s] is not None]
            if len(succs) != 1:
                raise ValueError(
                    f"Block {b} has no terminator but has {len(succs)} successors; "
                    f"cannot normalize."
                )

            node.append_instruction(
                IRInstr.uniop(op=OpCodes.JMP, dst=cfg.nodes[succs[0]].name)
            )


def build_layout_with_fallthrough(cfg: CFG, rpo: List[int]) -> List[int]:
    """
    Build a layout that respects *required* fallthrough: if a block has no terminator,
    its fallthrough successor must be the next block.

    Then it tries to improve fallthrough for other blocks greedily.
    """
    rpo_set = set(rpo)
    placed: Set[int] = set()
    layout: List[int] = []

    # --- 1) Compute required fallthrough edges: b -> ft[b] ---
    fallthrough: Dict[int, int] = {}

    for b in rpo:
        node = cfg.nodes[b]
        if node is None:
            continue
        term = node.get_terminator()
        if term is None:
            succs = [s for s in cfg.successors(b) if cfg.nodes[s] is not None]
            if len(succs) != 1:
                if b == cfg.end_idx:
                    # allow end block to have no terminator and no successors
                    continue
                raise ValueError(
                    f"Block {b} has no terminator but has {len(succs)} successors; "
                    f"cannot model fallthrough unambiguously."
                )
            fallthrough[b] = succs[0]

    # --- 2) Utility: follow required fallthrough chain ---
    def place_fallthrough_chain(start: int) -> None:
        cur = start
        while (
            cur is not None
            and cur in rpo_set
            and cur not in placed
            and cfg.nodes[cur] is not None
        ):
            placed.add(cur)
            layout.append(cur)

            nxt = fallthrough.get(cur)
            if nxt is None:
                break

            # if already placed, this is a layout conflict -> must introduce a JMP later or split.
            if nxt in placed:
                # We *could* allow this and later force a JMP at end of cur,
                # but if cur has no terminator, you said you'd be doomed.
                raise ValueError(
                    f"Required fallthrough from {cur} to {nxt} cannot be satisfied because {nxt} is already placed."
                )

            cur = nxt

    # --- 3) Preferred successor for non-required cases (simple heuristic) ---
    def pick_preferred_successor(b: int) -> Optional[int]:
        node = cfg.nodes[b]
        if node is None:
            return None
        term = node.get_terminator()
        if term is None:
            # required fallthrough handled by chain
            return None

        # Unconditional JMP: prefer its target
        if term.op == OpCodes.JMP:
            assert isinstance(term.dst, str)
            t = cfg._node_name_to_id[term.dst]

            if t in rpo_set and t not in placed and cfg.nodes[t] is not None:
                return t

        # Conditional: prefer any unplaced successor (heuristic)
        for s in cfg.successors(b):
            if s in rpo_set and s not in placed and cfg.nodes[s] is not None:
                return s

        return None

    def place_greedy_chain(start: int) -> None:
        cur = start
        while (
            cur is not None
            and cur in rpo_set
            and cur not in placed
            and cfg.nodes[cur] is not None
        ):
            # If cur has required fallthrough, place the entire required chain from cur
            if cur in fallthrough:
                place_fallthrough_chain(cur)
                return

            placed.add(cur)
            layout.append(cur)

            cur = pick_preferred_successor(cur)

    # --- 4) Build layout: ensure required fallthrough chains always placed intact ---
    for b in rpo:
        if b in placed or cfg.nodes[b] is None:
            continue
        # If b is in the middle of someone else's required chain, it will be placed when its head is placed.
        # We still allow starting at b; chain logic will enforce correctness.
        place_greedy_chain(b)

    return layout


class PassToByteCode(CompilationPass):
    def run(self, rar: RegisterAllocationResult) -> List[List[int]]:
        self.all_ops = generate_all_forms()

        ttsl_compiler = self.ttsl_compiler
        cfg = ttsl_compiler.cfg
        assert isinstance(cfg, CFG)
        # order the nodes in a way that respects control flow
        rpo: List[NodeID] = cfg.reverse_post_order()
        layout: List[NodeID] = build_layout_with_fallthrough(cfg, rpo)
        # all_nodes = cfg.bfs(cfg.init_idx)

        self.blocks_name_to_address: Dict[str, int] = {}

        # clean up instructions per block
        for node_id in layout:
            node = cfg.nodes[node_id]
            rewrittend_instructions: List[IRInstr] = []
            for instr in node.instrs(include_phis=False):
                if instr.op == OpCodes.PHI:
                    raise Exception(
                        "PHI nodes should have been lowered before bytecode emission"
                    )
                elif instr.op == OpCodes.LABEL:
                    # Labels are not emitted in bytecode
                    continue
                elif instr.op == OpCodes.COMMENT:
                    # Comments are not emitted in bytecode
                    continue
                elif instr.op == OpCodes.LOAD_CONST:
                    # not emitted as LOAD_CONST; replaced by STORE to allocated register
                    continue
                else:
                    self.transform_instr_to_bytecode(instr, rar)
                    rewrittend_instructions.append(instr)
            node.set_instrs(rewrittend_instructions)
        # now assign addresses to blocks
        current_address = 0
        for node_id in layout:
            node = cfg.nodes[node_id]
            instrs = node.instrs(include_phis=False)
            self.blocks_name_to_address[node.name] = current_address
            current_address += len(instrs)

        # now patch jump targets in the bytecode
        for node_id in layout:
            node = cfg.nodes[node_id]
            for instr in node.instrs(include_phis=False):
                assert instr.byte_code is not None
                if instr.op == OpCodes.JMP:
                    target_block_name = instr.dst
                    assert isinstance(target_block_name, str)
                    target_address = self.blocks_name_to_address[target_block_name]

                    instr.byte_code[1] = target_address
                elif instr.op == OpCodes.JMP_IF_FALSE:
                    target_block_name = instr.dst
                    assert isinstance(target_block_name, str)
                    target_address = self.blocks_name_to_address[target_block_name]
                    instr.byte_code[1] = target_address

        # now extract final bytecode
        final_bytecode: List[List[int]] = []
        for node_id in layout:
            node = cfg.nodes[node_id]

            for instr in node.instrs(include_phis=False):
                assert instr.byte_code is not None
                final_bytecode.append(instr.byte_code)
        return final_bytecode

    def find_form(self, instr: IRInstr) -> Form:
        instr.src1
        instr.src2
        instr.src3
        instr.src4
        for form in self.all_ops:
            form["type"]  # output_type
            op_name = form["name"]  # opcode name

            form.opcode_index
            form.output_type
            input_types = [
                it for it in form["input_types"] if it is not None
            ]  # input types
            # form.opcode_index
            if instr.op == OpCodes.JMP and op_name == "OP_JMP":
                return form
            elif instr.op == OpCodes.JMP_IF_FALSE and op_name == "OP_JMP_IF_FALSE":
                return form
            elif instr.op == OpCodes.RET and op_name == "OP_RET":
                return form
            elif instr.op.name in op_name:
                # check types now
                instr_types = []
                if instr.dst is not None:
                    instr_types.append(instr.dst.ty)
                if instr.src1 is not None:
                    instr_types.append(instr.src1.ty)
                if instr.src2 is not None:
                    instr_types.append(instr.src2.ty)
                if instr.src3 is not None:
                    instr_types.append(instr.src3.ty)
                if instr.src4 is not None:
                    instr_types.append(instr.src4.ty)

                target_typing = tuple([form["type"]] + input_types)
                if tuple(instr_types) == target_typing:
                    return form

        raise ValueError(f"No matching form found for instruction: {instr}")

    def transform_instr_to_bytecode(
        self, instr: IRInstr, rar: RegisterAllocationResult
    ) -> None:
        if instr.op in (OpCodes.LABEL, OpCodes.PHI, OpCodes.COMMENT):
            return  # No bytecode for these

        form = self.find_form(instr)

        srcs = [instr.src1, instr.src2, instr.src3, instr.src4]
        dst = instr.dst

        # Convert operands to their integer representations
        src_ids: List[int] = []
        for src in srcs:
            if src is None:
                src_ids.append(0)
            elif isinstance(src, Temp):
                # find the register id for the temp
                op_ty, op_reg = rar.tempids_to_registers[src.id]  # get register id
                src_ids.append(op_reg)
            else:
                raise ValueError(f"Unsupported source operand type: {src}")
        assert len(src_ids) == 4

        #
        dst_id: Optional[int] = None
        if dst is None:
            dst_id = 0
        elif isinstance(dst, Temp):
            op_ty, op_reg = rar.tempids_to_registers[dst.id]  # get register id
            dst_id = op_reg
        elif instr.op in (OpCodes.JMP, OpCodes.JMP_IF_FALSE):
            dst_id = 0  # placeholder, will be patched later
        else:
            raise ValueError(f"Unsupported dst operand type: {dst}")

        assert isinstance(dst_id, int)
        assert isinstance(form.opcode_index, int)
        bytecode = [form.opcode_index, dst_id] + src_ids
        instr.byte_code = bytecode


class RegisterSettings:
    @classmethod
    def default_vars_to_registers(cls) -> Dict[str, RegisterAddress]:
        d = {}
        taken_registers: Dict[str, Set[int]] = {}
        for k, v in TTSLCompilerContext.always_present_variables().items():
            if k in taken_registers:
                used_regs = taken_registers[k]
                reg_id = 1
                while reg_id in used_regs:
                    reg_id += 1
                taken_registers[k].add(reg_id)
                d[k] = (v, reg_id)
            else:
                taken_registers[k] = {0}
                d[k] = (v, 0)  # default to register 0 for each variable
        return d

    def __init__(self, vars_to_registers: Dict[str, RegisterAddress]):
        self.regs: Dict[IRType, Dict[int, Any]] = {ty: {} for ty in IRType}
        self.var_name_to_registers: Dict[str, RegisterAddress] = vars_to_registers

    def set_register(self, ty: IRType, reg_id: int, value: Any):
        self.regs[ty][reg_id] = value

    def set_variable(self, name: str, value: Any):
        if name not in self.var_name_to_registers:
            raise ValueError(f"Variable {name} not found in register allocation.")
        ty, reg_id = self.var_name_to_registers[name]
        self.set_register(ty, reg_id, value)

    def get_register_list(self):
        reg_types = [
            IRType.BOOL,
            IRType.F32,
            IRType.I32,
            IRType.V2,
            IRType.V3,
            IRType.V4,
        ]
        regs = []
        for ty in reg_types:
            regs.append(self.regs[ty])
        return regs


def all_passes_compilation(
    src: str, func_name: str, globals_dict: Dict[str, Any]
) -> Tuple[bytes, RegisterSettings]:
    cc = compile_ttsl(src, func_name, globals_dict)
    build_cfg_from_ir(cc)
    PassSSARenamer(cc).run()

    PassPhiNodeLowering(cc).run()
    CFGSimplifyPass(cc).run()
    rar = RegisterAllocatorPass(cc).run()

    PassNormalizeTerminators(cc).run()
    final_byte_code = PassToByteCode(cc).run(rar)

    reg_settings = RegisterSettings(rar.var_names_to_registers)
    for (ty, reg_id), value in rar.const_id_to_registers.values():
        reg_settings.set_register(ty, reg_id, value)

    all_bytecode_instrs = []
    for bytecode_instr in final_byte_code:
        all_bytecode_instrs.extend(bytecode_instr)
    # convert the bytecode to a bytes array
    byte_array = bytes(all_bytecode_instrs)
    return byte_array, reg_settings
