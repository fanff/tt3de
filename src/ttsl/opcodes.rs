// Generated with Love <3.

use nalgebra_glm::{abs, cos, exp, log, log2, sin, sqrt, tan, Vec2, Vec3, Vec4};

use crate::ttsl::Registers;

pub const ADD_F32: u8 = 0;
pub const SUB_F32: u8 = 1;
pub const ADD_V2: u8 = 2;
pub const SUB_V2: u8 = 3;
pub const ADD_V3: u8 = 4;
pub const SUB_V3: u8 = 5;
pub const ADD_V4: u8 = 6;
pub const SUB_V4: u8 = 7;
pub const MUL_F32: u8 = 8;
pub const DIV_F32: u8 = 9;
pub const MUL_I32: u8 = 10;
pub const DIV_I32: u8 = 11;
pub const MUL_V2_F32: u8 = 12;
pub const DIV_V2_F32: u8 = 13;
pub const MUL_V3_F32: u8 = 14;
pub const DIV_V3_F32: u8 = 15;
pub const MUL_V4_F32: u8 = 16;
pub const DIV_V4_F32: u8 = 17;
pub const MUL_F32_V2: u8 = 18;
pub const MUL_F32_V3: u8 = 19;
pub const MUL_F32_V4: u8 = 20;
pub const NEG_F32: u8 = 21;
pub const ABS_F32: u8 = 22;
pub const SQRT_F32: u8 = 23;
pub const SIN_F32: u8 = 24;
pub const COS_F32: u8 = 25;
pub const TAN_F32: u8 = 26;
pub const EXP_F32: u8 = 27;
pub const LN_F32: u8 = 28;
pub const LOG_F32: u8 = 29;
pub const STORE_F32: u8 = 30;
pub const NEG_V2: u8 = 31;
pub const ABS_V2: u8 = 32;
pub const SQRT_V2: u8 = 33;
pub const SIN_V2: u8 = 34;
pub const COS_V2: u8 = 35;
pub const TAN_V2: u8 = 36;
pub const EXP_V2: u8 = 37;
pub const LN_V2: u8 = 38;
pub const LOG_V2: u8 = 39;
pub const STORE_V2: u8 = 40;
pub const NEG_V3: u8 = 41;
pub const ABS_V3: u8 = 42;
pub const SQRT_V3: u8 = 43;
pub const SIN_V3: u8 = 44;
pub const COS_V3: u8 = 45;
pub const TAN_V3: u8 = 46;
pub const EXP_V3: u8 = 47;
pub const LN_V3: u8 = 48;
pub const LOG_V3: u8 = 49;
pub const STORE_V3: u8 = 50;
pub const NEG_V4: u8 = 51;
pub const ABS_V4: u8 = 52;
pub const SQRT_V4: u8 = 53;
pub const SIN_V4: u8 = 54;
pub const COS_V4: u8 = 55;
pub const TAN_V4: u8 = 56;
pub const EXP_V4: u8 = 57;
pub const LN_V4: u8 = 58;
pub const LOG_V4: u8 = 59;
pub const STORE_V4: u8 = 60;
pub const CMP_GT_F32: u8 = 61;
pub const CMP_GTE_F32: u8 = 62;
pub const CMP_GT_I32: u8 = 63;
pub const CMP_GTE_I32: u8 = 64;
pub const STORE_V2_FROM_F32: u8 = 65;
pub const STORE_V3_FROM_F32: u8 = 66;
pub const STORE_V4_FROM_F32: u8 = 67;
pub const OP_JMP: u8 = 68;
pub const OP_JMP_IF_FALSE: u8 = 69;
pub const OP_RET: u8 = 70;

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
        ADD_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_f32_.add(dst as usize) = a_val + b_val;
            }
            None
        }

        SUB_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_f32_.add(dst as usize) = a_val - b_val;
            }
            None
        }

        ADD_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                let b_val = *base_v2.add(b as usize);
                *base_v2.add(dst as usize) = a_val + b_val;
            }
            None
        }

        SUB_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                let b_val = *base_v2.add(b as usize);
                *base_v2.add(dst as usize) = a_val - b_val;
            }
            None
        }

        ADD_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                let b_val = *base_v3.add(b as usize);
                *base_v3.add(dst as usize) = a_val + b_val;
            }
            None
        }

        SUB_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                let b_val = *base_v3.add(b as usize);
                *base_v3.add(dst as usize) = a_val - b_val;
            }
            None
        }

        ADD_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                let b_val = *base_v4.add(b as usize);
                *base_v4.add(dst as usize) = a_val + b_val;
            }
            None
        }

        SUB_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                let b_val = *base_v4.add(b as usize);
                *base_v4.add(dst as usize) = a_val - b_val;
            }
            None
        }

        MUL_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_f32_.add(dst as usize) = a_val * b_val;
            }
            None
        }

        DIV_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_f32_.add(dst as usize) = a_val / b_val;
            }
            None
        }

        MUL_I32 => {
            unsafe {
                let base_i32_ = regs.i32_.as_mut_ptr();
                let a_val = *base_i32_.add(a as usize);
                let b_val = *base_i32_.add(b as usize);
                *base_i32_.add(dst as usize) = a_val * b_val;
            }
            None
        }

        DIV_I32 => {
            unsafe {
                let base_i32_ = regs.i32_.as_mut_ptr();
                let a_val = *base_i32_.add(a as usize);
                let b_val = *base_i32_.add(b as usize);
                *base_i32_.add(dst as usize) = a_val / b_val;
            }
            None
        }

        MUL_V2_F32 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_v2.add(dst as usize) = a_val * b_val;
            }
            None
        }

        DIV_V2_F32 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_v2.add(dst as usize) = a_val / b_val;
            }
            None
        }

        MUL_V3_F32 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_v3.add(dst as usize) = a_val * b_val;
            }
            None
        }

        DIV_V3_F32 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_v3.add(dst as usize) = a_val / b_val;
            }
            None
        }

        MUL_V4_F32 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_v4.add(dst as usize) = a_val * b_val;
            }
            None
        }

        DIV_V4_F32 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_v4.add(dst as usize) = a_val / b_val;
            }
            None
        }

        MUL_F32_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_v2.add(b as usize);
                *base_v2.add(dst as usize) = a_val * b_val;
            }
            None
        }

        MUL_F32_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_v3.add(b as usize);
                *base_v3.add(dst as usize) = a_val * b_val;
            }
            None
        }

        MUL_F32_V4 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_v4.add(b as usize);
                *base_v4.add(dst as usize) = a_val * b_val;
            }
            None
        }

        NEG_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = -a_val;
            }
            None
        }

        ABS_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val.abs();
            }
            None
        }

        SQRT_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val.sqrt();
            }
            None
        }

        SIN_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val.sin();
            }
            None
        }

        COS_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val.cos();
            }
            None
        }

        TAN_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val.tan();
            }
            None
        }

        EXP_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val.exp();
            }
            None
        }

        LN_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val.ln();
            }
            None
        }

        LOG_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val.log2();
            }
            None
        }

        STORE_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                *base_f32_.add(dst as usize) = a_val;
            }
            None
        }

        NEG_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = -a_val;
            }
            None
        }

        ABS_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = abs(&a_val);
            }
            None
        }

        SQRT_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = sqrt(&a_val);
            }
            None
        }

        SIN_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = sin(&a_val);
            }
            None
        }

        COS_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = cos(&a_val);
            }
            None
        }

        TAN_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = tan(&a_val);
            }
            None
        }

        EXP_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = exp(&a_val);
            }
            None
        }

        LN_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = log2(&a_val);
            }
            None
        }

        LOG_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = log(&a_val);
            }
            None
        }

        STORE_V2 => {
            unsafe {
                let base_v2 = regs.v2.as_mut_ptr();
                let a_val = *base_v2.add(a as usize);
                *base_v2.add(dst as usize) = a_val;
            }
            None
        }

        NEG_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = -a_val;
            }
            None
        }

        ABS_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = abs(&a_val);
            }
            None
        }

        SQRT_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = sqrt(&a_val);
            }
            None
        }

        SIN_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = sin(&a_val);
            }
            None
        }

        COS_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = cos(&a_val);
            }
            None
        }

        TAN_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = tan(&a_val);
            }
            None
        }

        EXP_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = exp(&a_val);
            }
            None
        }

        LN_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = log2(&a_val);
            }
            None
        }

        LOG_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = log(&a_val);
            }
            None
        }

        STORE_V3 => {
            unsafe {
                let base_v3 = regs.v3.as_mut_ptr();
                let a_val = *base_v3.add(a as usize);
                *base_v3.add(dst as usize) = a_val;
            }
            None
        }

        NEG_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = -a_val;
            }
            None
        }

        ABS_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = abs(&a_val);
            }
            None
        }

        SQRT_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = sqrt(&a_val);
            }
            None
        }

        SIN_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = sin(&a_val);
            }
            None
        }

        COS_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = cos(&a_val);
            }
            None
        }

        TAN_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = tan(&a_val);
            }
            None
        }

        EXP_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = exp(&a_val);
            }
            None
        }

        LN_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = log2(&a_val);
            }
            None
        }

        LOG_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = log(&a_val);
            }
            None
        }

        STORE_V4 => {
            unsafe {
                let base_v4 = regs.v4.as_mut_ptr();
                let a_val = *base_v4.add(a as usize);
                *base_v4.add(dst as usize) = a_val;
            }
            None
        }

        CMP_GT_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let base_bool_ = regs.bool_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_bool_.add(dst as usize) = a_val > b_val;
            }
            None
        }

        CMP_GTE_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let base_bool_ = regs.bool_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                *base_bool_.add(dst as usize) = a_val >= b_val;
            }
            None
        }

        CMP_GT_I32 => {
            unsafe {
                let base_i32_ = regs.i32_.as_mut_ptr();
                let base_bool_ = regs.bool_.as_mut_ptr();
                let a_val = *base_i32_.add(a as usize);
                let b_val = *base_i32_.add(b as usize);
                *base_bool_.add(dst as usize) = a_val > b_val;
            }
            None
        }

        CMP_GTE_I32 => {
            unsafe {
                let base_i32_ = regs.i32_.as_mut_ptr();
                let base_bool_ = regs.bool_.as_mut_ptr();
                let a_val = *base_i32_.add(a as usize);
                let b_val = *base_i32_.add(b as usize);
                *base_bool_.add(dst as usize) = a_val >= b_val;
            }
            None
        }

        STORE_V2_FROM_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                let base_v2 = regs.v2.as_mut_ptr();
                *base_v2.add(dst as usize) = Vec2::new(a_val, b_val);
            }
            None
        }

        STORE_V3_FROM_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                let c_val = *base_f32_.add(c as usize);
                let base_v3 = regs.v3.as_mut_ptr();
                *base_v3.add(dst as usize) = Vec3::new(a_val, b_val, c_val);
            }
            None
        }

        STORE_V4_FROM_F32 => {
            unsafe {
                let base_f32_ = regs.f32_.as_mut_ptr();
                let a_val = *base_f32_.add(a as usize);
                let b_val = *base_f32_.add(b as usize);
                let c_val = *base_f32_.add(c as usize);
                let d_val = *base_f32_.add(d as usize);
                let base_v4 = regs.v4.as_mut_ptr();
                *base_v4.add(dst as usize) = Vec4::new(a_val, b_val, c_val, d_val);
            }
            None
        }

        OP_JMP => {
            // Unconditional jump to instruction at address 'a'
            *ip = a as usize - 1; // -1 because ip will be incremented after this
            None
        }

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
        }

        OP_RET => {
            return Some((
                regs.v3[a as usize],
                regs.v3[b as usize],
                regs.i32_[c as usize],
            ));
        }

        _ => panic!("Unknown opcode: {}", opcode),
    }
}
