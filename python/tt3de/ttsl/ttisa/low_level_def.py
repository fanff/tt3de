# -*- coding: utf-8 -*-
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
    def opcode_index(self) -> str:
        return self["opcode_index"]


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
                        None,
                        None,
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
                form = {
                    "name": f"{op_code.name}_{ir_type_left.name}_{ir_type_right.name}",
                    "type": target_type,
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
            form = {
                "name": f"{op_code.name}_{ir_type.name}",
                "type": ir_type.name.lower(),
                "rust_expr": math_function_dict[op_code],
                "bank": ir_type.name.lower() + "_",
            }
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

        form = {
            "name": f"STORE_{ir_type.name}_FROM_F32",
            "type": ir_type,
            "rust_expr": vecnew,
            "bank": ir_type.name.lower() + "_",
        }
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
# TODO add the narry cross type like the vecto builders operattion from f32 to vecn
# TODO add the cross type that read the vectore components into f32


# {'bank': 'v2_', 'name': 'SIN_V2', 'rust_expr': '{a}.sin()', 'type': 'v2'},


# now lets generate the COMparison forms
def generate_comparison_forms() -> List[Form]:
    compare_forms = []
    COM_FORMS = [OpCodes.CMP_GT, OpCodes.CMP_GTE]
    for ir_type in [IRType.F32, IRType.I32]:
        for op_code in COM_FORMS:
            form = {
                "name": f"{op_code.name}_{ir_type.name}",
                "type": IRType.BOOL,
                "rust_expr": {
                    OpCodes.CMP_GT: "{a} > {b}",
                    OpCodes.CMP_GTE: "{a} >= {b}",
                }[op_code],
                "bank": "bool_",
            }

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
            *ip = a as usize - 1; // -1 because ip will be incremented after this
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
            "input_types": [IRType.V3, IRType.V3, IRType.I32],
        }
    )
    return_form["rust_match_code"] = """
    OP_RET => {
            return Some((
                regs.v3[a as usize],
                regs.v3[b as usize],
                regs.i32_[c as usize],
            ));
        }
    """
    return return_form


def generate_all_forms() -> List[Form]:
    # binary operations generation
    nums_parallel_add_sub = generate_binary_unitype_forms(
        ALL_NUMERIC_TYPES,
        [
            OpCodes.ADD,
            OpCodes.SUB,
        ],
    )
    nums_parallel_mult_div = generate_binary_unitype_forms(
        [IRType.F32, IRType.I32],
        [
            OpCodes.MUL,
            OpCodes.DIV,
        ],
    )

    nums_vec_f = generate_binary_cross_type_forms(
        [IRType.V2, IRType.V3, IRType.V4], [IRType.F32], [OpCodes.MUL, OpCodes.DIV]
    )
    nums_f_vec = generate_binary_cross_type_forms(
        [IRType.F32], [IRType.V2, IRType.V3, IRType.V4], [OpCodes.MUL]
    )

    # TODO implement the f32/ vec with
    # let v = Vec4::new(a_val, a_val, a_val, a_val);
    # let r = v.component_div(&b_val);

    # unary operations generation
    unary_forms = generate_unary_forms(
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
            OpCodes.STORE,
        ],
    )

    comp_forms = generate_comparison_forms()

    store_vec_forms = generate_store_vec_from_scalar()

    jump_forms = generate_jump_forms()

    all_generated_forms = (
        nums_parallel_add_sub
        + nums_parallel_mult_div
        + nums_vec_f
        + nums_f_vec
        + unary_forms
        + comp_forms
        + store_vec_forms
        + jump_forms
    )
    # print(f"Total generated forms: {len(all_generated_forms)}")

    all_generated_forms.append(generate_return_form())
    for index, form in enumerate(all_generated_forms):
        form["opcode_index"] = index
    return all_generated_forms


if __name__ == "__main__":
    all_generated_forms = generate_all_forms()
    # now generate the rust file

    RUST_OPCODE_FILE_PRELUDE = """
    // Generated with Love <3.


    use nalgebra_glm::{abs, cos, exp, log, log2, sin, sqrt, tan, Vec2, Vec3, Vec4};

    use crate::ttsl::Registers;

    """

    op_code_definitions_statement = [
        f"""pub const {form['name']}: u8 = {form['opcode_index']};"""
        for form in all_generated_forms
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
    ) -> Option<(Vec3, Vec3, i32)> {
        match opcode {
    %s

    _ => panic!("Unknown opcode: {}", opcode),
        }
    }
    """

    rust_execopcode_match_arms = "\n".join(
        [form["rust_match_code"] for form in all_generated_forms]
    )

    # now put the pieces together
    rust_opcode_file_content = (
        RUST_OPCODE_FILE_PRELUDE
        + "\n".join(op_code_definitions_statement)
        + RUST_EXEC_OPCODE_MATCH_ARMS_TEMPLATE % rust_execopcode_match_arms
    )

    # print(rust_opcode_file_content)

    with open("src/ttsl/opcodes.rs", "w") as f:
        f.write(rust_opcode_file_content)
