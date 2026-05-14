# -*- coding: utf-8 -*-
import subprocess
from dataclasses import dataclass, field
from typing import List

from tt3de.ttsl.ttsl_assembly import IRType, OpCodes

IRTYPE_TO_REGISTER_NAME = {
    IRType.BOOL: "bool_",
    IRType.I32: "i32_",
    IRType.F32: "f32_",
    IRType.V2: "v2",
    IRType.V3: "v3",
    IRType.V4: "v4",
}


class Form(dict):
    pass

    @property
    def name(self) -> str:
        return self["name"]

    @property
    def output_type(self) -> IRType:
        return self["type"]

    @property
    def input_types(self) -> List[IRType]:
        return self["input_types"]

    @property
    def opcode_index(self) -> int:
        return self["opcode_index"]


@dataclass
class CategoryGroup:
    name: str
    forms: List[Form] = field(default_factory=list)


class Rustgen:
    @staticmethod
    def unsafe_block(rust_expr: str) -> str:
        return f"unsafe {{ {rust_expr} \n}}"

    @staticmethod
    def let_base_register_be(irty: IRType) -> str:
        regname = IRTYPE_TO_REGISTER_NAME[irty]
        base_name = f"base_{regname}"
        return f"let {base_name} = regs.{regname}.as_mut_ptr();"

    @staticmethod
    def let_operand_register_be(op_name: str, irty: IRType) -> str:
        regname = IRTYPE_TO_REGISTER_NAME[irty]
        base_name = f"base_{regname}"
        return f"let {op_name}_val = *{base_name}.add({op_name} as usize);"

    @staticmethod
    def base_register_is(
        inner_expression,
        irty: IRType,
    ):
        regname = IRTYPE_TO_REGISTER_NAME[irty]
        base_name = f"base_{regname}"
        return f"*{base_name}.add(dst as usize) = {inner_expression};"

    @staticmethod
    def generate_binary_op(
        irty: IRType,
        rust_expr_template: str,
    ) -> str:
        return Rustgen.unsafe_block(
            "\n".join(
                [
                    Rustgen.let_base_register_be(irty),
                    Rustgen.let_operand_register_be("a", irty),
                    Rustgen.let_operand_register_be("b", irty),
                    Rustgen.base_register_is(
                        rust_expr_template.format(a="a_val", b="b_val"), irty
                    ),
                ]
            )
        )

    @staticmethod
    def generate_cross_type_binary_op(
        irty_left: IRType,
        irty_right: IRType,
        rust_expr_template: str,
        target_type: IRType | None = None,
    ) -> str:
        if target_type is None:
            return Rustgen.unsafe_block(
                "\n".join(
                    [
                        Rustgen.let_base_register_be(irty_left),
                        Rustgen.let_operand_register_be("a", irty_left),
                        Rustgen.let_operand_register_be("b", irty_right),
                        Rustgen.base_register_is(
                            rust_expr_template.format(a="a_val", b="b_val"), irty_left
                        ),
                    ]
                )
            )
        else:
            base_toload = set((irty_left, irty_right, target_type))
            bases = [Rustgen.let_base_register_be(base) for base in base_toload]
            return Rustgen.unsafe_block(
                "\n".join(
                    bases
                    + [
                        Rustgen.let_operand_register_be("a", irty_left),
                        Rustgen.let_operand_register_be("b", irty_right),
                        Rustgen.base_register_is(
                            rust_expr_template.format(a="a_val", b="b_val"),
                            target_type,
                        ),
                    ]
                )
            )

    def generate_unary_op(
        irty: IRType,
        rust_expr_template: str,
    ) -> str:
        return Rustgen.unsafe_block(
            "\n".join(
                [
                    Rustgen.let_base_register_be(irty),
                    Rustgen.let_operand_register_be("a", irty),
                    Rustgen.base_register_is(
                        rust_expr_template.format(a="a_val"), irty
                    ),
                ]
            )
        )

    def generate_cross_type_unary_op(
        irty_left: IRType,
        irty_right: IRType,
        rust_expr_template: str,
    ) -> str:
        return Rustgen.unsafe_block(
            "\n".join(
                [
                    Rustgen.let_base_register_be(irty_left),
                    Rustgen.let_operand_register_be("a", irty_right),
                    Rustgen.base_register_is(
                        rust_expr_template.format(a="a_val"), irty_left
                    ),
                ]
            )
        )


def generate_binary_unitype_forms(input_types, op_code_family) -> List[Form]:
    """
    Generate forms for binary operations like add, mul, sub, div. All forms is having
    same input & output types.

    E.g., ADD_F32: f32 = f32 + f32 unsafe {             // regs.f32_[dst as usize] =
    regs.f32_[a as usize] + regs.f32_[b as usize];             let base =
    regs.f32_.as_mut_ptr();             let a_val = *base.add(a as usize); let b_val =
    *base.add(b as usize);             *base.add(dst as usize) = a_val + b_val; }
    """
    forms = []
    for ir_type in input_types:
        for op_code in op_code_family:
            form = Form(
                {
                    "name": f"{op_code.name}_{ir_type.name}",
                    "type": ir_type,
                    "input_types": [
                        ir_type,
                        ir_type,
                    ],
                    "rust_expr": "{a} "
                    + {
                        OpCodes.ADD: "+",
                        OpCodes.MUL: "*",
                        OpCodes.SUB: "-",
                        OpCodes.DIV: "/",
                    }[op_code]
                    + " {b}",
                    "bank": ir_type.name.lower() + "_",
                }
            )
            match_code = f"""
                {form["name"]} => {{
                    {Rustgen.generate_binary_op(
                        form["type"],
                        form["rust_expr"],
                    )}
                None
                }}
                """
            form["rust_match_code"] = match_code
            forms.append(form)
    return forms


def generate_binary_cross_type_forms(
    input_types_left, input_types_right, op_code_family
):
    """
    Generate forms for cross-type operations like add, mul, sub, div.

    All forms is having different input types but same output type. E.g., ADD_V3_V2: v3
    = v3 + v2
    """
    forms = []
    for ir_type_left in input_types_left:
        for ir_type_right in input_types_right:
            if ir_type_left == ir_type_right:
                continue

            target_type = ir_type_left if ir_type_right == IRType.F32 else ir_type_right

            for op_code in op_code_family:
                form = Form(
                    {
                        "name": f"{op_code.name}_{ir_type_left.name}_{ir_type_right.name}",
                        "type": target_type,
                        "input_types": [
                            ir_type_left,
                            ir_type_right,
                        ],
                        "rust_expr": "{a} "
                        + {
                            OpCodes.ADD: "+",
                            OpCodes.MUL: "*",
                            OpCodes.SUB: "-",
                            OpCodes.DIV: "/",
                        }[op_code]
                        + " {b}",
                        "bank": ir_type_left.name.lower() + "_",
                    }
                )

                match_code = f"""
                {form["name"]} => {{
                    {Rustgen.generate_cross_type_binary_op(
                        ir_type_left,
                        ir_type_right,
                        form["rust_expr"],
                        target_type=target_type,
                    )}
                None
                }}
                """
                form["rust_match_code"] = match_code

                forms.append(form)

    return forms


MATH_FUNCTION_NATIVE_TYPES = {
    OpCodes.NEG: "-{a}",
    OpCodes.ABS: "{a}.abs()",
    OpCodes.SQRT: "{a}.sqrt()",
    OpCodes.SIN: "{a}.sin()",
    OpCodes.COS: "{a}.cos()",
    OpCodes.TAN: "{a}.tan()",
    OpCodes.EXP: "{a}.exp()",
    OpCodes.LN: "{a}.ln()",
    OpCodes.LOG: "{a}.log2()",
    OpCodes.FLOOR: "{a}.floor()",
    OpCodes.CEIL: "{a}.ceil()",
    OpCodes.FRACT: "{a}.fract()",
    OpCodes.STORE: "{a}",
}
MATH_FUNCTION_VEC_TYPES = {
    OpCodes.NEG: "-{a}",
    OpCodes.ABS: "abs(&{a})",
    OpCodes.SQRT: "sqrt(&{a})",
    OpCodes.SIN: "sin(&{a})",
    OpCodes.COS: "cos(&{a})",
    OpCodes.TAN: "tan(&{a})",
    OpCodes.EXP: "exp(&{a})",
    OpCodes.LN: "log2(&{a})",
    OpCodes.LOG: "log(&{a})",
    OpCodes.FLOOR: "floor(&{a})",
    OpCodes.CEIL: "ceil(&{a})",
    OpCodes.FRACT: "fract(&{a})",
    OpCodes.STORE: "{a}",
}


def generate_unary_forms(
    input_types: List[IRType], op_code_family: List[OpCodes]
) -> List[Form]:
    forms = []
    for ir_type in input_types:
        for op_code in op_code_family:
            if ir_type in [IRType.F32]:
                math_function_dict = MATH_FUNCTION_NATIVE_TYPES
            else:
                math_function_dict = MATH_FUNCTION_VEC_TYPES
            form = Form(
                {
                    "name": f"{op_code.name}_{ir_type.name}",
                    "type": ir_type,
                    "rust_expr": math_function_dict[op_code],
                    "input_types": [ir_type],
                    "bank": ir_type.name.lower() + "_",
                }
            )
            match_code = f"""

                {form["name"]} => {{
                    {Rustgen.generate_unary_op(
                        ir_type,
                        form["rust_expr"],
                    )}
                None
                }}
                """
            form["rust_match_code"] = match_code
            forms.append(form)
    return forms


def _mod_rust_body_f32() -> str:
    return Rustgen.unsafe_block(
        "\n".join(
            [
                Rustgen.let_base_register_be(IRType.F32),
                Rustgen.let_operand_register_be("a", IRType.F32),
                Rustgen.let_operand_register_be("b", IRType.F32),
                Rustgen.base_register_is(
                    "a_val - b_val * (a_val / b_val).floor()", IRType.F32
                ),
            ]
        )
    )


def _mod_rust_body_vec(ir_type: IRType) -> str:
    """Component-wise GLSL mod for vectors: map(|c| c.0 - c.1 * (c.0 / c.1).floor())."""
    comp_count = {IRType.V2: 2, IRType.V3: 3, IRType.V4: 4}[ir_type]
    vec_name = {IRType.V2: "Vec2", IRType.V3: "Vec3", IRType.V4: "Vec4"}[ir_type]
    axes = ["x", "y", "z", "w"][:comp_count]
    components = ", ".join(
        f"a_val.{ax} - b_val.{ax} * (a_val.{ax} / b_val.{ax}).floor()" for ax in axes
    )
    regname = IRTYPE_TO_REGISTER_NAME[ir_type]
    return Rustgen.unsafe_block(
        "\n".join(
            [
                Rustgen.let_base_register_be(ir_type),
                Rustgen.let_operand_register_be("a", ir_type),
                Rustgen.let_operand_register_be("b", ir_type),
                f"*base_{regname}.add(dst as usize) = {vec_name}::new({components});",
            ]
        )
    )


def generate_mod_forms() -> List[Form]:
    """Generate MOD forms: GLSL-style mod(x, y) = x - y * floor(x / y)."""
    forms = []
    for ir_type in [IRType.F32, IRType.V2, IRType.V3, IRType.V4]:
        form = Form(
            {
                "name": f"MOD_{ir_type.name}",
                "type": ir_type,
                "input_types": [ir_type, ir_type],
                "bank": ir_type.name.lower() + "_",
            }
        )
        if ir_type == IRType.F32:
            rust_body = _mod_rust_body_f32()
        else:
            rust_body = _mod_rust_body_vec(ir_type)
        match_code = f"""
                {form["name"]} => {{
                    {rust_body}
                None
                }}
                """
        form["rust_match_code"] = match_code
        forms.append(form)
    return forms


def generate_store_vec_from_scalar():
    all_vec_types = [IRType.V2, IRType.V3, IRType.V4]

    operand_name_order = ["a", "b", "c", "d"]
    forms = []
    for some_val, ir_type in enumerate(all_vec_types):
        vec_compnant: int = some_val + 2
        # Vec3::new(0.0, 0.0, 0.0);

        vecnew = f"Vec{vec_compnant}::new("
        vecnew += ",".join(
            [f"{operand_name_order[i]}_val" for i in range(vec_compnant)]
        )
        vecnew += ")"

        form = Form(
            {
                "name": f"{OpCodes.STORE_VEC_FROM_SCALAR.name}_{ir_type.name}_F32",
                "type": ir_type,
                "rust_expr": vecnew,
                "input_types": [IRType.F32] * vec_compnant,
                "bank": ir_type.name.lower() + "_",
            }
        )
        input_vars = [
            Rustgen.let_operand_register_be(operand_name_order[i], IRType.F32)
            for i in range(vec_compnant)
        ]
        rust_code = Rustgen.unsafe_block(
            "\n".join(
                [
                    Rustgen.let_base_register_be(IRType.F32),
                ]
                + input_vars
                + [
                    Rustgen.let_base_register_be(ir_type),
                    Rustgen.base_register_is(vecnew.format(a="a_val"), ir_type),
                ]
            )
        )
        match_code = f"""
                {form["name"]} => {{
                    {rust_code}
                None
                }}
                """
        form["rust_match_code"] = match_code
        forms.append(form)
    return forms


ALL_NUMERIC_TYPES = [IRType.F32, IRType.V2, IRType.V3, IRType.V4]


op_code_family = [OpCodes.ADD, OpCodes.MUL, OpCodes.SUB, OpCodes.DIV]


# TODO add the unary cross type forms like the "norm" operation that vecn > f32


def generate_normalize_forms() -> List[Form]:
    """Generate NORMALIZE forms for V2, V3, V4 with zero-vector guard.

    nalgebra_glm::normalize returns NaN for zero-length input. GLSL implementations
    typically return zero; this guard matches that convention.
    """
    VEC_AXES = {
        IRType.V2: ["x", "y"],
        IRType.V3: ["x", "y", "z"],
        IRType.V4: ["x", "y", "z", "w"],
    }
    VEC_NAMES = {
        IRType.V2: "Vec2",
        IRType.V3: "Vec3",
        IRType.V4: "Vec4",
    }

    forms = []
    for ir_type in [IRType.V2, IRType.V3, IRType.V4]:
        axes = VEC_AXES[ir_type]
        vec_name = VEC_NAMES[ir_type]
        regname = IRTYPE_TO_REGISTER_NAME[ir_type]

        len_sq_terms = " + ".join(f"a_val.{ax} * a_val.{ax}" for ax in axes)

        rust_body = Rustgen.unsafe_block(
            "\n".join([
                Rustgen.let_base_register_be(ir_type),
                Rustgen.let_operand_register_be("a", ir_type),
                f"let len_sq = {len_sq_terms};",
                f"let result = if len_sq == 0.0 {{ {vec_name}::zeros() }} "
                f"else {{ a_val / len_sq.sqrt() }};",
                f"*base_{regname}.add(dst as usize) = result;",
            ])
        )

        form = Form({
            "name": f"NORMALIZE_{ir_type.name}",
            "type": ir_type,
            "input_types": [ir_type],
            "bank": ir_type.name.lower() + "_",
        })
        form["rust_match_code"] = f"""
                {form["name"]} => {{
                    {rust_body}
                None
                }}
                """
        forms.append(form)

    return forms


def generate_read_axis_forms():
    read_axis_forms = []
    AXIS = ["X", "Y", "Z", "W"]
    AXIS_SIZE = {
        IRType.V2: 2,
        IRType.V3: 3,
        IRType.V4: 4,
    }
    for ir_type in [IRType.V2, IRType.V3, IRType.V4]:
        for axis_index, axis_name in enumerate(AXIS):
            if axis_index >= AXIS_SIZE[ir_type]:
                continue
            form = Form(
                {
                    "name": f"READ_AXIS_{axis_name}_{ir_type.name}_TO_F32",
                    "type": IRType.F32,
                    "input_types": [ir_type],
                    "rust_expr": f"{axis_name.lower()}",
                    "bank": "f32_",
                }
            )
            rust_body = f"""
                    {Rustgen.let_base_register_be(ir_type)}
                    {Rustgen.let_operand_register_be("a", ir_type)}
                    {Rustgen.let_base_register_be(IRType.F32)}
                    *base_f32_.add(dst as usize) = a_val.{axis_name.lower()};
                    """
            rust_body = Rustgen.unsafe_block(rust_body)
            match_code = f"""
                {form["name"]} => {{
                    {rust_body}
                None
                }}
                """
            form["rust_match_code"] = match_code
            read_axis_forms.append(form)
    return read_axis_forms


# {'bank': 'v2_', 'name': 'SIN_V2', 'rust_expr': '{a}.sin()', 'type': 'v2'},


# now lets generate the COMparison forms
def generate_comparison_forms() -> List[Form]:
    compare_forms = []
    COM_FORMS = [OpCodes.CMP_GT, OpCodes.CMP_GTE]
    for ir_type in [IRType.F32, IRType.I32]:
        for op_code in COM_FORMS:
            form = Form(
                {
                    "name": f"{op_code.name}_{ir_type.name}",
                    "type": IRType.BOOL,
                    "input_types": [ir_type, ir_type],
                    "rust_expr": {
                        OpCodes.CMP_GT: "{a} > {b}",
                        OpCodes.CMP_GTE: "{a} >= {b}",
                    }[op_code],
                    "bank": "bool_",
                }
            )

            match_code = f"""
                {form["name"]} => {{
                    {Rustgen.generate_cross_type_binary_op(
                        ir_type,
                        ir_type,
                        form["rust_expr"],
                        target_type=IRType.BOOL,
                    )}
                None
                }}
                """
            form["rust_match_code"] = match_code
            compare_forms.append(form)
    return compare_forms


def generate_jump_forms() -> List[Form]:
    jump_form = Form(
        {
            "name": "OP_JMP",
            "type": None,
            "input_types": [IRType.I32, None, None, None],
            "rust_match_code": """OP_JMP => {
            // Unconditional jump to instruction at address 'a'
            *ip = dst as usize - 1; // -1 because ip will be incremented after this
            None
        }""",
        }
    )

    jump_if_false_form = Form(
        {
            "name": "OP_JMP_IF_FALSE",
            "type": None,
            "input_types": [IRType.I32, None, None, None],
            "rust_match_code": """
            OP_JMP_IF_FALSE => {
            // Conditional jump: if f32_[a] is false (0.0), jump to instruction at address 'b'
            unsafe {
                let base_bool_ = regs.bool_.as_mut_ptr();
                let a_val = *base_bool_.add(a as usize);
                if a_val == false {
                    *ip = dst as usize - 1; // -1 because ip will be incremented after this
                }
            }
            None
        }""",
        }
    )
    return [jump_form, jump_if_false_form]


# we will add the RET opcode, it is special
def generate_return_form() -> Form:
    return_form = Form(
        {
            "name": "OP_RET",
            "type": None,
            "input_types": [IRType.V4, IRType.V4, IRType.I32],
        }
    )
    return_form["rust_match_code"] = """
    OP_RET => {
            return Some((
                regs.v4[a as usize],
                regs.v4[b as usize],
                regs.i32_[c as usize],
            ));
        }
    """
    return return_form


def generate_dot_forms() -> List[Form]:
    """Generate DOT forms: vecN × vecN → f32 for V2, V3, V4."""
    forms = []
    for ir_type in [IRType.V2, IRType.V3, IRType.V4]:
        form = Form({
            "name": f"DOT_{ir_type.name}",
            "type": IRType.F32,
            "input_types": [ir_type, ir_type],
            "bank": "f32_",
        })
        rust_body = Rustgen.generate_cross_type_binary_op(
            ir_type, ir_type,
            "nalgebra_glm::dot(&{a}, &{b})",
            target_type=IRType.F32,
        )
        match_code = (
            "                " + form["name"] + " => {\n"
            "                    " + rust_body + "\n"
            "                None\n"
            "                }\n"
        )
        form["rust_match_code"] = match_code
        forms.append(form)
    return forms


def generate_length_forms() -> List[Form]:
    """Generate LENGTH forms: vecN → f32 for V2, V3, V4.

    Uses custom unsafe block because generate_cross_type_unary_op only declares
    the output bank's base register; length reads from a vector bank and writes to f32.
    """
    forms = []
    for ir_type in [IRType.V2, IRType.V3, IRType.V4]:
        regname = IRTYPE_TO_REGISTER_NAME[ir_type]
        rust_body = Rustgen.unsafe_block(
            "\n".join([
                Rustgen.let_base_register_be(ir_type),
                Rustgen.let_base_register_be(IRType.F32),
                Rustgen.let_operand_register_be("a", ir_type),
                Rustgen.base_register_is(
                    "glm_length(&a_val)", IRType.F32,
                ),
            ])
        )
        form = Form({
            "name": f"LENGTH_{ir_type.name}",
            "type": IRType.F32,
            "input_types": [ir_type],
            "bank": "f32_",
        })
        match_code = (
            "                " + form["name"] + " => {\n"
            "                    " + rust_body + "\n"
            "                None\n"
            "                }\n"
        )
        form["rust_match_code"] = match_code
        forms.append(form)
    return forms


def _max_rust_body_vec(ir_type: IRType) -> str:
    """Component-wise max for vectors: compare each element with f32::max."""
    comp_count = {IRType.V2: 2, IRType.V3: 3, IRType.V4: 4}[ir_type]
    vec_name = {IRType.V2: "Vec2", IRType.V3: "Vec3", IRType.V4: "Vec4"}[ir_type]
    axes = ["x", "y", "z", "w"][:comp_count]
    components = ", ".join(
        f"a_val.{ax}.max(b_val.{ax})" for ax in axes
    )
    regname = IRTYPE_TO_REGISTER_NAME[ir_type]
    return Rustgen.unsafe_block(
        "\n".join([
            Rustgen.let_base_register_be(ir_type),
            Rustgen.let_operand_register_be("a", ir_type),
            Rustgen.let_operand_register_be("b", ir_type),
            f"*base_{regname}.add(dst as usize) = {vec_name}::new({components});",
        ])
    )


def generate_max_forms() -> List[Form]:
    """Generate MAX forms: T × T → T for F32, V2, V3, V4.

    Uses f32::max for scalars, component-wise f32::max for vectors
    (nalgebra_glm::max only supports (vec, scalar), not (vec, vec)).
    """
    forms = []
    for ir_type in [IRType.F32, IRType.V2, IRType.V3, IRType.V4]:
        if ir_type == IRType.F32:
            rust_body = Rustgen.generate_binary_op(ir_type, "{a}.max({b})")
        else:
            rust_body = _max_rust_body_vec(ir_type)
        form = Form({
            "name": f"MAX_{ir_type.name}",
            "type": ir_type,
            "input_types": [ir_type, ir_type],
            "bank": ir_type.name.lower() + "_",
        })
        match_code = (
            "                " + form["name"] + " => {\n"
            "                    " + rust_body + "\n"
            "                None\n"
            "                }\n"
        )
        form["rust_match_code"] = match_code
        forms.append(form)
    return forms


def _clamp_rust_body_vec(ir_type: IRType) -> str:
    """Component-wise clamp for vectors: clamp each element with f32::clamp."""
    comp_count = {IRType.V2: 2, IRType.V3: 3, IRType.V4: 4}[ir_type]
    vec_name = {IRType.V2: "Vec2", IRType.V3: "Vec3", IRType.V4: "Vec4"}[ir_type]
    axes = ["x", "y", "z", "w"][:comp_count]
    components = ", ".join(
        f"a_val.{ax}.clamp(b_val.{ax}, c_val.{ax})" for ax in axes
    )
    regname = IRTYPE_TO_REGISTER_NAME[ir_type]
    return Rustgen.unsafe_block(
        "\n".join([
            Rustgen.let_base_register_be(ir_type),
            Rustgen.let_operand_register_be("a", ir_type),
            Rustgen.let_operand_register_be("b", ir_type),
            Rustgen.let_operand_register_be("c", ir_type),
            f"*base_{regname}.add(dst as usize) = {vec_name}::new({components});",
        ])
    )


def generate_clamp_forms() -> List[Form]:
    """Generate CLAMP forms: T × T × T → T for F32, V2, V3, V4.

    Uses f32::clamp for scalars, component-wise f32::clamp for vectors
    (nalgebra_glm::clamp only supports (vec, scalar, scalar), not (vec, vec, vec)).
    3-source operand layout (same pattern as MIX: a=x, b=lo, c=hi).
    """
    forms = []
    for ir_type in [IRType.F32, IRType.V2, IRType.V3, IRType.V4]:
        if ir_type == IRType.F32:
            rust_block = Rustgen.unsafe_block(
                "\n".join([
                    Rustgen.let_base_register_be(ir_type),
                    Rustgen.let_operand_register_be("a", ir_type),
                    Rustgen.let_operand_register_be("b", ir_type),
                    Rustgen.let_operand_register_be("c", ir_type),
                    Rustgen.base_register_is(
                        "a_val.clamp(b_val, c_val)", ir_type,
                    ),
                ])
            )
        else:
            rust_block = _clamp_rust_body_vec(ir_type)
        form = Form({
            "name": f"CLAMP_{ir_type.name}",
            "type": ir_type,
            "input_types": [ir_type, ir_type, ir_type],
            "bank": ir_type.name.lower() + "_",
        })
        match_code = (
            "                " + form["name"] + " => {\n"
            "                    " + rust_block + "\n"
            "                None\n"
            "                }\n"
        )
        form["rust_match_code"] = match_code
        forms.append(form)
    return forms


def generate_glm_tool_mix_forms() -> List[Form]:
    # lets do mix (vecn, vecn, f32) -> vecn
    mix_forms = []
    for ir_type in [IRType.V2, IRType.V3, IRType.V4]:
        form = Form(
            {
                "name": f"MIX_{ir_type.name}",
                "type": ir_type,
                "input_types": [ir_type, ir_type, IRType.F32],
                "rust_expr": "mix(&{a}, &{b}, {c})",
                "bank": ir_type.name.lower() + "_",
            }
        )
        rust_block = Rustgen.unsafe_block(
            "\n".join(
                [
                    Rustgen.let_base_register_be(IRType.F32),
                    Rustgen.let_base_register_be(ir_type),
                    Rustgen.let_operand_register_be("a", ir_type),
                    Rustgen.let_operand_register_be("b", ir_type),
                    Rustgen.let_operand_register_be("c", IRType.F32),
                    Rustgen.base_register_is(
                        "mix(&{a}, &{b}, {c})".format(a="a_val", b="b_val", c="c_val"),
                        ir_type,
                    ),
                ]
            )
        )
        match_code = f"""
                {form["name"]} => {{
                    {rust_block}
                None
                }}
                """
        form["rust_match_code"] = match_code
        mix_forms.append(form)

    return mix_forms


def generate_glm_tools_forms() -> List[Form]:
    return generate_glm_tool_mix_forms()


def generate_tt_texture_form() -> Form:
    """Filtered 2D texture sample: vec4 = tt_texture(tex_index i32, uv vec2)."""
    return Form(
        {
            "name": "TT_TEXTURE",
            "type": IRType.V4,
            "input_types": [IRType.I32, IRType.V2],
            "rust_match_code": """
            TT_TEXTURE => {
                unsafe {
                    let base_i32_ = regs.i32_.as_mut_ptr();
                    let base_v2 = regs.v2.as_mut_ptr();
                    let base_v4 = regs.v4.as_mut_ptr();
                    let idx = *base_i32_.add(a as usize);
                    let uv = *base_v2.add(b as usize);
                    let sampled = tex
                        .as_ref()
                        .map(|t| t.sample_tt_texture(idx, uv))
                        .unwrap_or_else(|| Vec4::new(0.0, 0.0, 0.0, 1.0));
                    *base_v4.add(dst as usize) = sampled;
                }
                None
            }
            """,
        }
    )


def generate_all_forms() -> List[CategoryGroup]:
    categories = [
        CategoryGroup(
            "Binary Arithmetic (same type)",
            generate_binary_unitype_forms(
                ALL_NUMERIC_TYPES,
                [OpCodes.ADD, OpCodes.SUB],
            )
            + generate_binary_unitype_forms(
                [IRType.F32, IRType.I32],
                [OpCodes.MUL, OpCodes.DIV],
            ),
        ),
        CategoryGroup(
            "Binary Arithmetic (cross type, vec * scalar)",
            generate_binary_cross_type_forms(
                [IRType.V2, IRType.V3, IRType.V4],
                [IRType.F32],
                [OpCodes.MUL, OpCodes.DIV],
            ),
        ),
        CategoryGroup(
            "Binary Arithmetic (cross type, scalar * vec)",
            generate_binary_cross_type_forms(
                [IRType.F32],
                [IRType.V2, IRType.V3, IRType.V4],
                [OpCodes.MUL],
            ),
        ),
        CategoryGroup("Normalize", generate_normalize_forms()),
        CategoryGroup("Dot Product", generate_dot_forms()),
        CategoryGroup("Length", generate_length_forms()),
        CategoryGroup("Max", generate_max_forms()),
        CategoryGroup("Clamp", generate_clamp_forms()),
        CategoryGroup(
            "Unary Math",
            generate_unary_forms(
                [IRType.F32, IRType.V2, IRType.V3, IRType.V4],
                [
                    OpCodes.NEG,
                    OpCodes.ABS,
                    OpCodes.SQRT,
                    OpCodes.SIN,
                    OpCodes.COS,
                    OpCodes.TAN,
                    OpCodes.EXP,
                    OpCodes.LN,
                    OpCodes.LOG,
                    OpCodes.FLOOR,
                    OpCodes.CEIL,
                    OpCodes.FRACT,
                    OpCodes.STORE,
                ],
            ),
        ),
        CategoryGroup("Modulo", generate_mod_forms()),
        CategoryGroup("Comparison", generate_comparison_forms()),
        CategoryGroup("Store Vec from Scalars", generate_store_vec_from_scalar()),
        CategoryGroup("Read Axis", generate_read_axis_forms()),
        CategoryGroup("GLM Builtins", generate_glm_tools_forms()),
        CategoryGroup("Texture", [generate_tt_texture_form()]),
        CategoryGroup("Control Flow", generate_jump_forms()),
        CategoryGroup("Return", [generate_return_form()]),
    ]

    index = 0
    for cat in categories:
        for form in cat.forms:
            form["opcode_index"] = index
            index += 1
    return categories


def _format_type(irty) -> str:
    if irty is None:
        return "-"
    return irty.name.lower()


def generate_markdown(categories: List[CategoryGroup]) -> str:
    lines = [
        "# TTSL Opcode Reference",
        "",
        "*This file is auto-generated by `scripts/gen_opcodes.sh` (or `scripts/gen_opcodes.ps1`). Do not edit manually.*",
        "",
    ]

    total = sum(len(cat.forms) for cat in categories)
    lines.append(f"**Total opcodes: {total}**")
    lines.append("")

    for cat in categories:
        lines.append(f"## {cat.name}")
        lines.append("")
        lines.append("| Opcode | Name | Output | Inputs |")
        lines.append("|--------|------|--------|--------|")
        for form in cat.forms:
            opcode = form["opcode_index"]
            name = form["name"]
            out_ty = _format_type(form.get("type"))
            in_tys = ", ".join(_format_type(t) for t in form.get("input_types", []))
            lines.append(f"| {opcode} | `{name}` | {out_ty} | {in_tys} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    categories = generate_all_forms()
    all_forms = [form for cat in categories for form in cat.forms]

    RUST_OPCODE_FILE_PRELUDE = """
    // Generated with Love <3.


    use nalgebra_glm::{abs, ceil, cos, exp, floor, fract, length as glm_length,
     log, log2, mix, sin, sqrt, tan, Vec2, Vec3, Vec4};

    use crate::ttsl::{Registers, TtslTextureEnv};

    """

    op_code_definitions_statement = [
        f"""pub const {form['name']}: u8 = {form['opcode_index']};"""
        for form in all_forms
    ]

    RUST_EXEC_OPCODE_MATCH_ARMS_TEMPLATE = """

    pub fn exec_opcode(
        opcode: u8,
        dst: u8,
        a: u8,
        b: u8,
        c: u8,
        d: u8,
        regs: &mut Registers,
        ip: &mut usize,
        tex: Option<&dyn TtslTextureEnv>,
    ) -> Option<(Vec4, Vec4, i32)> {
        match opcode {
    %s

    _ => panic!("Unknown opcode: {}", opcode),
        }
    }
    """

    rust_execopcode_match_arms = "\n".join(
        [form["rust_match_code"] for form in all_forms]
    )

    rust_opcode_file_content = (
        RUST_OPCODE_FILE_PRELUDE
        + "\n".join(op_code_definitions_statement)
        + RUST_EXEC_OPCODE_MATCH_ARMS_TEMPLATE % rust_execopcode_match_arms
    )

    rust_opcode_path = "src/ttsl/opcodes.rs"
    with open(rust_opcode_path, "w") as f:
        f.write(rust_opcode_file_content)

    subprocess.run(
        ["rustfmt", rust_opcode_path],
        check=True,
    )

    op_code_definitions_statement_py = [
        f"""{form['name']} = {form['opcode_index']}""" for form in all_forms
    ]
    with open("python/tt3de/ttsl/ttisa/ttisa_opcodes.py", "w") as f:
        f.write("\n".join(op_code_definitions_statement_py))

    with open("source/opcode_reference.md", "w") as f:
        f.write(generate_markdown(categories))


if __name__ == "__main__":
    main()
