use std::mem::{offset_of, size_of};

use cranelift_codegen::ir::{types, InstBuilder, MemFlagsData, Value};
use cranelift_frontend::FunctionBuilder;
use nalgebra_glm::{Vec2, Vec3, Vec4};

use super::JitOutputs;
use crate::ttsl::Registers;

fn flags() -> MemFlagsData {
    MemFlagsData::trusted()
}

pub fn f32_off(idx: u8) -> i32 {
    (offset_of!(Registers, f32_) + size_of::<f32>() * idx as usize) as i32
}

pub fn i32_off(idx: u8) -> i32 {
    (offset_of!(Registers, i32_) + size_of::<i32>() * idx as usize) as i32
}

pub fn bool_off(idx: u8) -> i32 {
    (offset_of!(Registers, bool_) + size_of::<bool>() * idx as usize) as i32
}

pub fn v2_off(idx: u8, axis: u8) -> i32 {
    (offset_of!(Registers, v2)
        + size_of::<Vec2>() * idx as usize
        + size_of::<f32>() * axis as usize) as i32
}

pub fn v3_off(idx: u8, axis: u8) -> i32 {
    (offset_of!(Registers, v3)
        + size_of::<Vec3>() * idx as usize
        + size_of::<f32>() * axis as usize) as i32
}

pub fn v4_off(idx: u8, axis: u8) -> i32 {
    (offset_of!(Registers, v4)
        + size_of::<Vec4>() * idx as usize
        + size_of::<f32>() * axis as usize) as i32
}

pub fn load_f32(builder: &mut FunctionBuilder, regs: Value, idx: u8) -> Value {
    builder.ins().load(types::F32, flags(), regs, f32_off(idx))
}

pub fn load_i32(builder: &mut FunctionBuilder, regs: Value, idx: u8) -> Value {
    builder.ins().load(types::I32, flags(), regs, i32_off(idx))
}

pub fn load_bool(builder: &mut FunctionBuilder, regs: Value, idx: u8) -> Value {
    builder.ins().load(types::I8, flags(), regs, bool_off(idx))
}

pub fn load_v2(builder: &mut FunctionBuilder, regs: Value, idx: u8, axis: u8) -> Value {
    builder
        .ins()
        .load(types::F32, flags(), regs, v2_off(idx, axis))
}

pub fn load_v3(builder: &mut FunctionBuilder, regs: Value, idx: u8, axis: u8) -> Value {
    builder
        .ins()
        .load(types::F32, flags(), regs, v3_off(idx, axis))
}

pub fn load_v4(builder: &mut FunctionBuilder, regs: Value, idx: u8, axis: u8) -> Value {
    builder
        .ins()
        .load(types::F32, flags(), regs, v4_off(idx, axis))
}

fn out_front_off(axis: u8) -> i32 {
    (offset_of!(JitOutputs, front) + size_of::<f32>() * axis as usize) as i32
}

fn out_back_off(axis: u8) -> i32 {
    (offset_of!(JitOutputs, back) + size_of::<f32>() * axis as usize) as i32
}

pub fn store_outputs_values(
    builder: &mut FunctionBuilder,
    out: Value,
    front: [Value; 4],
    back: [Value; 4],
    glyph: Value,
) {
    for axis in 0..4 {
        builder
            .ins()
            .store(flags(), front[axis], out, out_front_off(axis as u8));
        builder
            .ins()
            .store(flags(), back[axis], out, out_back_off(axis as u8));
    }
    builder
        .ins()
        .store(flags(), glyph, out, offset_of!(JitOutputs, glyph) as i32);
}
