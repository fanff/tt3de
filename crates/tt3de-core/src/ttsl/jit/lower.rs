use cranelift_codegen::ir::condcodes::FloatCC;
use cranelift_codegen::ir::immediates::Ieee32;
use cranelift_codegen::ir::{Block, InstBuilder, Value};
use cranelift_frontend::FunctionBuilder;

use super::libcalls::Libcalls;
use super::mem;
use super::JitError;
use crate::ttsl::opcodes::*;
use crate::ttsl::Instr;

pub fn opcode_supported(opcode: u8) -> bool {
    matches!(
        opcode,
        ADD_F32
            | SUB_F32
            | ADD_V3
            | MUL_F32
            | DIV_F32
            | MUL_V3_F32
            | NORMALIZE_V3
            | DOT_V3
            | LENGTH_V2
            | MAX_F32
            | CLAMP_F32
            | SIN_F32
            | STORE_F32
            | STORE_V2
            | NEG_V3
            | STORE_V3
            | STORE_V4
            | CMP_GTE_F32
            | STORE_VEC_FROM_SCALAR_V2_F32
            | STORE_VEC_FROM_SCALAR_V3_F32
            | STORE_VEC_FROM_SCALAR_V4_F32
            | READ_AXIS_X_V2_TO_F32
            | READ_AXIS_Y_V2_TO_F32
            | READ_AXIS_X_V3_TO_F32
            | READ_AXIS_Y_V3_TO_F32
            | READ_AXIS_Z_V3_TO_F32
            | READ_AXIS_X_V4_TO_F32
            | READ_AXIS_Y_V4_TO_F32
            | READ_AXIS_Z_V4_TO_F32
            | TT_TEXTURE
            | OP_JMP
            | OP_JMP_IF_FALSE
            | OP_RET
    )
}

pub struct LowerCx<'a, 'b> {
    pub builder: &'a mut FunctionBuilder<'b>,
    pub regs: Value,
    pub tex: Value,
    pub out: Value,
    pub blocks: &'a [Block],
    pub libcalls: &'a Libcalls,
}

/// Lowers one instruction. Returns true when a terminator was emitted.
pub fn lower_instr(cx: &mut LowerCx, ip: usize, instr: &Instr) -> Result<bool, JitError> {
    let Instr {
        opcode,
        dst,
        a,
        b,
        c,
        d,
    } = *instr;
    let builder = &mut *cx.builder;
    let regs = cx.regs;

    match opcode {
        ADD_F32 => bin_f32(builder, regs, dst, a, b, |b, x, y| b.ins().fadd(x, y)),
        SUB_F32 => bin_f32(builder, regs, dst, a, b, |b, x, y| b.ins().fsub(x, y)),
        MUL_F32 => bin_f32(builder, regs, dst, a, b, |b, x, y| b.ins().fmul(x, y)),
        DIV_F32 => bin_f32(builder, regs, dst, a, b, |b, x, y| b.ins().fdiv(x, y)),
        STORE_F32 => {
            let v = mem::load_f32(builder, regs, a);
            mem::store_f32(builder, regs, dst, v);
        }
        SIN_F32 => {
            let x = mem::load_f32(builder, regs, a);
            let call = builder.ins().call(cx.libcalls.sin_f32, &[x]);
            let y = builder.inst_results(call)[0];
            mem::store_f32(builder, regs, dst, y);
        }
        MAX_F32 => {
            let x = mem::load_f32(builder, regs, a);
            let y = mem::load_f32(builder, regs, b);
            let call = builder.ins().call(cx.libcalls.max_f32, &[x, y]);
            let r = builder.inst_results(call)[0];
            mem::store_f32(builder, regs, dst, r);
        }
        CLAMP_F32 => {
            let x = mem::load_f32(builder, regs, a);
            let lo = mem::load_f32(builder, regs, b);
            let hi = mem::load_f32(builder, regs, c);
            let call = builder.ins().call(cx.libcalls.clamp_f32, &[x, lo, hi]);
            let r = builder.inst_results(call)[0];
            mem::store_f32(builder, regs, dst, r);
        }
        CMP_GTE_F32 => {
            let x = mem::load_f32(builder, regs, a);
            let y = mem::load_f32(builder, regs, b);
            let cmp = builder.ins().fcmp(FloatCC::GreaterThanOrEqual, x, y);
            mem::store_bool(builder, regs, dst, cmp);
        }
        ADD_V3 => bin_v3(builder, regs, dst, a, b, |b, x, y| b.ins().fadd(x, y)),
        MUL_V3_F32 => {
            let s = mem::load_f32(builder, regs, b);
            for axis in 0..3 {
                let v = mem::load_v3(builder, regs, a, axis);
                let r = builder.ins().fmul(v, s);
                mem::store_v3(builder, regs, dst, axis, r);
            }
        }
        NEG_V3 => {
            for axis in 0..3 {
                let v = mem::load_v3(builder, regs, a, axis);
                let r = builder.ins().fneg(v);
                mem::store_v3(builder, regs, dst, axis, r);
            }
        }
        DOT_V3 => {
            let mut acc = None;
            for axis in 0..3 {
                let x = mem::load_v3(builder, regs, a, axis);
                let y = mem::load_v3(builder, regs, b, axis);
                let p = builder.ins().fmul(x, y);
                acc = Some(match acc {
                    None => p,
                    Some(prev) => builder.ins().fadd(prev, p),
                });
            }
            mem::store_f32(builder, regs, dst, acc.expect("v3 has 3 axes"));
        }
        LENGTH_V2 => {
            let x = mem::load_v2(builder, regs, a, 0);
            let y = mem::load_v2(builder, regs, a, 1);
            let call = builder.ins().call(cx.libcalls.length_v2, &[x, y]);
            let r = builder.inst_results(call)[0];
            mem::store_f32(builder, regs, dst, r);
        }
        NORMALIZE_V3 => lower_normalize_v3(builder, regs, dst, a),
        STORE_V2 => mem::copy_v2(builder, regs, dst, a),
        STORE_V3 => mem::copy_v3(builder, regs, dst, a),
        STORE_V4 => mem::copy_v4(builder, regs, dst, a),
        STORE_VEC_FROM_SCALAR_V2_F32 => {
            let x = mem::load_f32(builder, regs, a);
            let y = mem::load_f32(builder, regs, b);
            mem::store_v2(builder, regs, dst, 0, x);
            mem::store_v2(builder, regs, dst, 1, y);
        }
        STORE_VEC_FROM_SCALAR_V3_F32 => {
            let x = mem::load_f32(builder, regs, a);
            let y = mem::load_f32(builder, regs, b);
            let z = mem::load_f32(builder, regs, c);
            mem::store_v3(builder, regs, dst, 0, x);
            mem::store_v3(builder, regs, dst, 1, y);
            mem::store_v3(builder, regs, dst, 2, z);
        }
        STORE_VEC_FROM_SCALAR_V4_F32 => {
            let x = mem::load_f32(builder, regs, a);
            let y = mem::load_f32(builder, regs, b);
            let z = mem::load_f32(builder, regs, c);
            let w = mem::load_f32(builder, regs, d);
            mem::store_v4(builder, regs, dst, 0, x);
            mem::store_v4(builder, regs, dst, 1, y);
            mem::store_v4(builder, regs, dst, 2, z);
            mem::store_v4(builder, regs, dst, 3, w);
        }
        READ_AXIS_X_V2_TO_F32 => {
            let v = mem::load_v2(builder, regs, a, 0);
            mem::store_f32(builder, regs, dst, v);
        }
        READ_AXIS_Y_V2_TO_F32 => {
            let v = mem::load_v2(builder, regs, a, 1);
            mem::store_f32(builder, regs, dst, v);
        }
        READ_AXIS_X_V3_TO_F32 => {
            let v = mem::load_v3(builder, regs, a, 0);
            mem::store_f32(builder, regs, dst, v);
        }
        READ_AXIS_Y_V3_TO_F32 => {
            let v = mem::load_v3(builder, regs, a, 1);
            mem::store_f32(builder, regs, dst, v);
        }
        READ_AXIS_Z_V3_TO_F32 => {
            let v = mem::load_v3(builder, regs, a, 2);
            mem::store_f32(builder, regs, dst, v);
        }
        READ_AXIS_X_V4_TO_F32 => {
            let v = mem::load_v4(builder, regs, a, 0);
            mem::store_f32(builder, regs, dst, v);
        }
        READ_AXIS_Y_V4_TO_F32 => {
            let v = mem::load_v4(builder, regs, a, 1);
            mem::store_f32(builder, regs, dst, v);
        }
        READ_AXIS_Z_V4_TO_F32 => {
            let v = mem::load_v4(builder, regs, a, 2);
            mem::store_f32(builder, regs, dst, v);
        }
        TT_TEXTURE => {
            let idx = mem::load_i32(builder, regs, a);
            let uv_x = mem::load_v2(builder, regs, b, 0);
            let uv_y = mem::load_v2(builder, regs, b, 1);
            let dest = mem::v4_ptr(builder, regs, dst);
            builder
                .ins()
                .call(cx.libcalls.sample, &[cx.tex, idx, uv_x, uv_y, dest]);
        }
        OP_JMP => {
            builder.ins().jump(cx.blocks[dst as usize], &[]);
            return Ok(true);
        }
        OP_JMP_IF_FALSE => {
            let cond = mem::load_bool(builder, regs, a);
            let next = cx.blocks[ip + 1];
            let dest = cx.blocks[dst as usize];
            // Non-zero (true) falls through; zero (false) takes the jump.
            builder.ins().brif(cond, next, &[], dest, &[]);
            return Ok(true);
        }
        OP_RET => {
            mem::store_outputs(builder, regs, cx.out, a, b, c);
            let glyph = mem::load_i32(builder, regs, c);
            builder.ins().return_(&[glyph]);
            return Ok(true);
        }
        other => return Err(JitError::Unsupported(other)),
    }

    Ok(false)
}

fn bin_f32(
    builder: &mut FunctionBuilder,
    regs: Value,
    dst: u8,
    a: u8,
    b: u8,
    op: impl FnOnce(&mut FunctionBuilder, Value, Value) -> Value,
) {
    let x = mem::load_f32(builder, regs, a);
    let y = mem::load_f32(builder, regs, b);
    let r = op(builder, x, y);
    mem::store_f32(builder, regs, dst, r);
}

fn bin_v3(
    builder: &mut FunctionBuilder,
    regs: Value,
    dst: u8,
    a: u8,
    b: u8,
    op: impl Fn(&mut FunctionBuilder, Value, Value) -> Value,
) {
    for axis in 0..3 {
        let x = mem::load_v3(builder, regs, a, axis);
        let y = mem::load_v3(builder, regs, b, axis);
        let r = op(builder, x, y);
        mem::store_v3(builder, regs, dst, axis, r);
    }
}

/// Matches [`NORMALIZE_V3`]: zero-length vectors stay zero.
fn lower_normalize_v3(builder: &mut FunctionBuilder, regs: Value, dst: u8, src: u8) {
    let x = mem::load_v3(builder, regs, src, 0);
    let y = mem::load_v3(builder, regs, src, 1);
    let z = mem::load_v3(builder, regs, src, 2);
    let xx = builder.ins().fmul(x, x);
    let yy = builder.ins().fmul(y, y);
    let zz = builder.ins().fmul(z, z);
    let xy = builder.ins().fadd(xx, yy);
    let len_sq = builder.ins().fadd(xy, zz);
    let zero = builder.ins().f32const(Ieee32::with_float(0.0));
    let is_zero = builder.ins().fcmp(FloatCC::Equal, len_sq, zero);
    let len = builder.ins().sqrt(len_sq);
    let nx = builder.ins().fdiv(x, len);
    let ny = builder.ins().fdiv(y, len);
    let nz = builder.ins().fdiv(z, len);
    let ox = builder.ins().select(is_zero, zero, nx);
    let oy = builder.ins().select(is_zero, zero, ny);
    let oz = builder.ins().select(is_zero, zero, nz);
    mem::store_v3(builder, regs, dst, 0, ox);
    mem::store_v3(builder, regs, dst, 1, oy);
    mem::store_v3(builder, regs, dst, 2, oz);
}
