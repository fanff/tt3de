use cranelift_codegen::ir::{types, AbiParam, FuncRef};
use cranelift_jit::{JITBuilder, JITModule};
use cranelift_module::{Linkage, Module};
use nalgebra_glm::{length as glm_length, Vec2, Vec3, Vec4};

use super::{JitError, JitLightEnv, JitTextureEnv};
use crate::ttsl::{TtslLightEnv, TtslTextureEnv};

pub(super) const SIN_F32: &str = "ttsl_jit_sin_f32";
pub(super) const COS_F32: &str = "ttsl_jit_cos_f32";
pub(super) const FLOOR_F32: &str = "ttsl_jit_floor_f32";
pub(super) const CEIL_F32: &str = "ttsl_jit_ceil_f32";
pub(super) const FRACT_F32: &str = "ttsl_jit_fract_f32";
pub(super) const MOD_F32: &str = "ttsl_jit_mod_f32";
pub(super) const MAX_F32: &str = "ttsl_jit_max_f32";
pub(super) const CLAMP_F32: &str = "ttsl_jit_clamp_f32";
pub(super) const LENGTH_V2: &str = "ttsl_jit_length_v2";
pub(super) const SAMPLE: &str = "ttsl_jit_sample";
pub(super) const LIGHT_COUNT: &str = "ttsl_jit_light_count";
pub(super) const LIGHT_TYPE: &str = "ttsl_jit_light_type";
pub(super) const LIGHT_COLOR: &str = "ttsl_jit_light_color";
pub(super) const LIGHT_DIRECTION: &str = "ttsl_jit_light_direction";
pub(super) const LIGHT_POSITION: &str = "ttsl_jit_light_position";
pub(super) const LIGHT_ATTENUATION: &str = "ttsl_jit_light_attenuation";

pub struct Libcalls {
    pub sin_f32: FuncRef,
    pub cos_f32: FuncRef,
    pub floor_f32: FuncRef,
    pub ceil_f32: FuncRef,
    pub fract_f32: FuncRef,
    pub mod_f32: FuncRef,
    pub max_f32: FuncRef,
    pub clamp_f32: FuncRef,
    pub length_v2: FuncRef,
    pub sample: FuncRef,
    pub light_count: FuncRef,
    pub light_type: FuncRef,
    pub light_color: FuncRef,
    pub light_direction: FuncRef,
    pub light_position: FuncRef,
    pub light_attenuation: FuncRef,
}

pub extern "C" fn ttsl_jit_sin_f32(x: f32) -> f32 {
    x.sin()
}

pub extern "C" fn ttsl_jit_cos_f32(x: f32) -> f32 {
    x.cos()
}

pub extern "C" fn ttsl_jit_floor_f32(x: f32) -> f32 {
    x.floor()
}

pub extern "C" fn ttsl_jit_ceil_f32(x: f32) -> f32 {
    x.ceil()
}

pub extern "C" fn ttsl_jit_fract_f32(x: f32) -> f32 {
    x - x.floor()
}

/// GLSL `mod(x, y) = x - y * floor(x / y)`.
pub extern "C" fn ttsl_jit_mod_f32(x: f32, y: f32) -> f32 {
    x - y * (x / y).floor()
}

pub extern "C" fn ttsl_jit_max_f32(a: f32, b: f32) -> f32 {
    a.max(b)
}

pub extern "C" fn ttsl_jit_clamp_f32(x: f32, min: f32, max: f32) -> f32 {
    x.clamp(min, max)
}

pub extern "C" fn ttsl_jit_length_v2(x: f32, y: f32) -> f32 {
    glm_length(&Vec2::new(x, y))
}

/// `env` is null when no texture buffer is bound.
pub unsafe extern "C" fn ttsl_jit_sample(
    env: *const JitTextureEnv,
    idx: i32,
    uv_x: f32,
    uv_y: f32,
    out_v4: *mut f32,
) {
    let sampled = if env.is_null() {
        Vec4::new(0.0, 0.0, 0.0, 1.0)
    } else {
        let tex: &dyn TtslTextureEnv = unsafe { (*env).as_ref() };
        tex.sample_tt_texture(idx, Vec2::new(uv_x, uv_y))
    };
    unsafe {
        *out_v4.add(0) = sampled.x;
        *out_v4.add(1) = sampled.y;
        *out_v4.add(2) = sampled.z;
        *out_v4.add(3) = sampled.w;
    }
}

fn write_v3(out: *mut f32, v: Vec3) {
    unsafe {
        *out.add(0) = v.x;
        *out.add(1) = v.y;
        *out.add(2) = v.z;
    }
}

fn light_env<'a>(env: *const JitLightEnv) -> Option<&'a dyn TtslLightEnv> {
    if env.is_null() {
        None
    } else {
        Some(unsafe { (*env).as_ref() })
    }
}

pub unsafe extern "C" fn ttsl_jit_light_count(env: *const JitLightEnv) -> i32 {
    light_env(env).map(|l| l.light_count()).unwrap_or(0)
}

pub unsafe extern "C" fn ttsl_jit_light_type(env: *const JitLightEnv, idx: i32) -> i32 {
    light_env(env).map(|l| l.light_type(idx)).unwrap_or(0)
}

pub unsafe extern "C" fn ttsl_jit_light_color(env: *const JitLightEnv, idx: i32, out_v3: *mut f32) {
    write_v3(
        out_v3,
        light_env(env)
            .map(|l| l.light_color(idx))
            .unwrap_or_else(Vec3::zeros),
    );
}

pub unsafe extern "C" fn ttsl_jit_light_direction(
    env: *const JitLightEnv,
    idx: i32,
    out_v3: *mut f32,
) {
    write_v3(
        out_v3,
        light_env(env)
            .map(|l| l.light_direction(idx))
            .unwrap_or_else(Vec3::zeros),
    );
}

pub unsafe extern "C" fn ttsl_jit_light_position(
    env: *const JitLightEnv,
    idx: i32,
    out_v3: *mut f32,
) {
    write_v3(
        out_v3,
        light_env(env)
            .map(|l| l.light_position(idx))
            .unwrap_or_else(Vec3::zeros),
    );
}

pub unsafe extern "C" fn ttsl_jit_light_attenuation(
    env: *const JitLightEnv,
    idx: i32,
    out_v3: *mut f32,
) {
    write_v3(
        out_v3,
        light_env(env)
            .map(|l| l.light_attenuation(idx))
            .unwrap_or_else(Vec3::zeros),
    );
}

pub fn register_symbols(jit_builder: &mut JITBuilder) {
    jit_builder.symbol(SIN_F32, ttsl_jit_sin_f32 as *const u8);
    jit_builder.symbol(COS_F32, ttsl_jit_cos_f32 as *const u8);
    jit_builder.symbol(FLOOR_F32, ttsl_jit_floor_f32 as *const u8);
    jit_builder.symbol(CEIL_F32, ttsl_jit_ceil_f32 as *const u8);
    jit_builder.symbol(FRACT_F32, ttsl_jit_fract_f32 as *const u8);
    jit_builder.symbol(MOD_F32, ttsl_jit_mod_f32 as *const u8);
    jit_builder.symbol(MAX_F32, ttsl_jit_max_f32 as *const u8);
    jit_builder.symbol(CLAMP_F32, ttsl_jit_clamp_f32 as *const u8);
    jit_builder.symbol(LENGTH_V2, ttsl_jit_length_v2 as *const u8);
    jit_builder.symbol(SAMPLE, ttsl_jit_sample as *const u8);
    jit_builder.symbol(LIGHT_COUNT, ttsl_jit_light_count as *const u8);
    jit_builder.symbol(LIGHT_TYPE, ttsl_jit_light_type as *const u8);
    jit_builder.symbol(LIGHT_COLOR, ttsl_jit_light_color as *const u8);
    jit_builder.symbol(LIGHT_DIRECTION, ttsl_jit_light_direction as *const u8);
    jit_builder.symbol(LIGHT_POSITION, ttsl_jit_light_position as *const u8);
    jit_builder.symbol(LIGHT_ATTENUATION, ttsl_jit_light_attenuation as *const u8);
}

pub fn declare(
    module: &mut JITModule,
    func: &mut cranelift_codegen::ir::Function,
) -> Result<Libcalls, JitError> {
    let ptr = module.target_config().pointer_type();

    let mut sin_sig = module.make_signature();
    sin_sig.params.push(AbiParam::new(types::F32));
    sin_sig.returns.push(AbiParam::new(types::F32));
    let sin_id = module.declare_function(SIN_F32, Linkage::Import, &sin_sig)?;
    let cos_id = module.declare_function(COS_F32, Linkage::Import, &sin_sig)?;

    let floor_id = module.declare_function(FLOOR_F32, Linkage::Import, &sin_sig)?;
    let ceil_id = module.declare_function(CEIL_F32, Linkage::Import, &sin_sig)?;
    let fract_id = module.declare_function(FRACT_F32, Linkage::Import, &sin_sig)?;

    let mut mod_sig = module.make_signature();
    mod_sig.params.push(AbiParam::new(types::F32));
    mod_sig.params.push(AbiParam::new(types::F32));
    mod_sig.returns.push(AbiParam::new(types::F32));
    let mod_id = module.declare_function(MOD_F32, Linkage::Import, &mod_sig)?;

    let mut max_sig = module.make_signature();
    max_sig.params.push(AbiParam::new(types::F32));
    max_sig.params.push(AbiParam::new(types::F32));
    max_sig.returns.push(AbiParam::new(types::F32));
    let max_id = module.declare_function(MAX_F32, Linkage::Import, &max_sig)?;

    let mut clamp_sig = module.make_signature();
    clamp_sig.params.push(AbiParam::new(types::F32));
    clamp_sig.params.push(AbiParam::new(types::F32));
    clamp_sig.params.push(AbiParam::new(types::F32));
    clamp_sig.returns.push(AbiParam::new(types::F32));
    let clamp_id = module.declare_function(CLAMP_F32, Linkage::Import, &clamp_sig)?;

    let mut length_sig = module.make_signature();
    length_sig.params.push(AbiParam::new(types::F32));
    length_sig.params.push(AbiParam::new(types::F32));
    length_sig.returns.push(AbiParam::new(types::F32));
    let length_id = module.declare_function(LENGTH_V2, Linkage::Import, &length_sig)?;

    let mut sample_sig = module.make_signature();
    sample_sig.params.push(AbiParam::new(ptr));
    sample_sig.params.push(AbiParam::new(types::I32));
    sample_sig.params.push(AbiParam::new(types::F32));
    sample_sig.params.push(AbiParam::new(types::F32));
    sample_sig.params.push(AbiParam::new(ptr));
    let sample_id = module.declare_function(SAMPLE, Linkage::Import, &sample_sig)?;

    let mut light_count_sig = module.make_signature();
    light_count_sig.params.push(AbiParam::new(ptr));
    light_count_sig.returns.push(AbiParam::new(types::I32));
    let light_count_id = module.declare_function(LIGHT_COUNT, Linkage::Import, &light_count_sig)?;

    let mut light_type_sig = module.make_signature();
    light_type_sig.params.push(AbiParam::new(ptr));
    light_type_sig.params.push(AbiParam::new(types::I32));
    light_type_sig.returns.push(AbiParam::new(types::I32));
    let light_type_id = module.declare_function(LIGHT_TYPE, Linkage::Import, &light_type_sig)?;

    let mut light_v3_sig = module.make_signature();
    light_v3_sig.params.push(AbiParam::new(ptr));
    light_v3_sig.params.push(AbiParam::new(types::I32));
    light_v3_sig.params.push(AbiParam::new(ptr));
    let light_color_id = module.declare_function(LIGHT_COLOR, Linkage::Import, &light_v3_sig)?;
    let light_dir_id = module.declare_function(LIGHT_DIRECTION, Linkage::Import, &light_v3_sig)?;
    let light_pos_id = module.declare_function(LIGHT_POSITION, Linkage::Import, &light_v3_sig)?;
    let light_att_id =
        module.declare_function(LIGHT_ATTENUATION, Linkage::Import, &light_v3_sig)?;

    Ok(Libcalls {
        sin_f32: module.declare_func_in_func(sin_id, func),
        cos_f32: module.declare_func_in_func(cos_id, func),
        floor_f32: module.declare_func_in_func(floor_id, func),
        ceil_f32: module.declare_func_in_func(ceil_id, func),
        fract_f32: module.declare_func_in_func(fract_id, func),
        mod_f32: module.declare_func_in_func(mod_id, func),
        max_f32: module.declare_func_in_func(max_id, func),
        clamp_f32: module.declare_func_in_func(clamp_id, func),
        length_v2: module.declare_func_in_func(length_id, func),
        sample: module.declare_func_in_func(sample_id, func),
        light_count: module.declare_func_in_func(light_count_id, func),
        light_type: module.declare_func_in_func(light_type_id, func),
        light_color: module.declare_func_in_func(light_color_id, func),
        light_direction: module.declare_func_in_func(light_dir_id, func),
        light_position: module.declare_func_in_func(light_pos_id, func),
        light_attenuation: module.declare_func_in_func(light_att_id, func),
    })
}
