from tt3de.ttsl.ttisa.low_level_def import Rustgen
from tt3de.ttsl.ttsl_assembly import IRType


def test_cross_type_register_bases_preserve_operand_order():
    generated = Rustgen.generate_cross_type_binary_op(
        IRType.V2,
        IRType.F32,
        "{a} * {b}",
        target_type=IRType.V2,
    )

    assert generated.index("let base_v2") < generated.index("let base_f32_")
    assert generated.count("let base_v2") == 1
