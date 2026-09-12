use cranelift_codegen::ir::{types, AbiParam, UserFuncName};
use cranelift_codegen::settings::{self, Configurable};
use cranelift_frontend::{FunctionBuilder, FunctionBuilderContext};
use cranelift_jit::{JITBuilder, JITModule};
use cranelift_module::{default_libcall_names, Linkage, Module, ModuleError};
use nalgebra_glm::Vec4;

use super::{Registers, TtslLightEnv, TtslTextureEnv};
use crate::ttsl::ir::TtslSsaModule;

mod ir_lower;
mod libcalls;
mod mem;

/// Compiled shader ABI: register file, optional texture env, optional light env, output struct.
///
/// Returns the glyph index (also stored in [`JitOutputs::glyph`]).
pub type ShaderFn = unsafe extern "C" fn(
    *mut Registers,
    *const JitTextureEnv,
    *const JitLightEnv,
    *mut JitOutputs,
) -> i32;

/// `true` once [`compile_ttsl`] lowers post-SSA IR to native code.
pub const LOWERS_IR: bool = true;

/// Front/back colors and glyph written by the IR `ret` terminator.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct JitOutputs {
    pub front: [f32; 4],
    pub back: [f32; 4],
    pub glyph: i32,
}

/// Packed `dyn TtslTextureEnv` fat pointer for the compiled calling convention.
///
/// Pass a null `*const JitTextureEnv` when no texture buffer is bound.
#[repr(C)]
#[derive(Clone, Copy)]
pub struct JitTextureEnv {
    data: *const (),
    meta: *const (),
}

impl JitTextureEnv {
    pub fn from_ref(tex: &dyn TtslTextureEnv) -> Self {
        unsafe { std::mem::transmute(tex as *const dyn TtslTextureEnv) }
    }

    unsafe fn as_ref(&self) -> &dyn TtslTextureEnv {
        let ptr: *const dyn TtslTextureEnv = std::mem::transmute(*self);
        unsafe { &*ptr }
    }
}

/// Packed `dyn TtslLightEnv` fat pointer for the compiled calling convention.
///
/// Pass a null `*const JitLightEnv` when no light buffer is bound.
#[repr(C)]
#[derive(Clone, Copy)]
pub struct JitLightEnv {
    data: *const (),
    meta: *const (),
}

impl JitLightEnv {
    pub fn from_ref(light: &dyn TtslLightEnv) -> Self {
        unsafe { std::mem::transmute(light as *const dyn TtslLightEnv) }
    }

    unsafe fn as_ref(&self) -> &dyn TtslLightEnv {
        let ptr: *const dyn TtslLightEnv = std::mem::transmute(*self);
        unsafe { &*ptr }
    }
}

/// Owns JIT code pages for as long as the compiled shader is used.
pub struct CompiledShader {
    _module: JITModule,
    func: ShaderFn,
}

impl CompiledShader {
    pub fn as_fn(&self) -> ShaderFn {
        self.func
    }

    /// Run the compiled shader against the register file and optional host envs.
    pub fn run(
        &self,
        regs: &mut Registers,
        tex: Option<&dyn TtslTextureEnv>,
        light: Option<&dyn TtslLightEnv>,
    ) -> (Vec4, Vec4, i32) {
        let tex_env = tex.map(JitTextureEnv::from_ref);
        let tex_ptr = tex_env
            .as_ref()
            .map(|e| e as *const JitTextureEnv)
            .unwrap_or(std::ptr::null());
        let light_env = light.map(JitLightEnv::from_ref);
        let light_ptr = light_env
            .as_ref()
            .map(|e| e as *const JitLightEnv)
            .unwrap_or(std::ptr::null());
        let mut out = JitOutputs::default();
        let glyph = unsafe { (self.func)(regs, tex_ptr, light_ptr, &mut out) };
        (
            Vec4::new(out.front[0], out.front[1], out.front[2], out.front[3]),
            Vec4::new(out.back[0], out.back[1], out.back[2], out.back[3]),
            glyph,
        )
    }
}

// Safety: after `finalize_definitions` the code pages are immutable. `run`
// only executes that code against caller-provided register files.
unsafe impl Send for CompiledShader {}
unsafe impl Sync for CompiledShader {}

#[derive(Debug)]
pub enum JitError {
    Native(String),
    Settings(settings::SetError),
    Codegen(cranelift_codegen::CodegenError),
    Module(ModuleError),
    UnsupportedIr(String),
    Ir(String),
}

impl From<settings::SetError> for JitError {
    fn from(value: settings::SetError) -> Self {
        Self::Settings(value)
    }
}

impl From<cranelift_codegen::CodegenError> for JitError {
    fn from(value: cranelift_codegen::CodegenError) -> Self {
        Self::Codegen(value)
    }
}

impl From<ModuleError> for JitError {
    fn from(value: ModuleError) -> Self {
        Self::Module(value)
    }
}

impl std::fmt::Display for JitError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Native(msg) => write!(f, "native ISA: {msg}"),
            Self::Settings(err) => write!(f, "cranelift settings: {err}"),
            Self::Codegen(err) => write!(f, "cranelift codegen: {err}"),
            Self::Module(err) => write!(f, "cranelift module: {err}"),
            Self::UnsupportedIr(op) => write!(f, "unsupported TTSL IR op: {op}"),
            Self::Ir(msg) => write!(f, "TTSL IR: {msg}"),
        }
    }
}

impl std::error::Error for JitError {}

/// Compile a post-SSA TTSL module to a native function with the shader ABI.
pub fn compile_ttsl(ssa: &TtslSsaModule) -> Result<CompiledShader, JitError> {
    let mut flag_builder = settings::builder();
    flag_builder.set("use_colocated_libcalls", "false")?;
    flag_builder.set("is_pic", "false")?;
    flag_builder.set("opt_level", "speed")?;

    let isa_builder =
        cranelift_native::builder().map_err(|msg| JitError::Native(msg.to_string()))?;
    let isa = isa_builder.finish(settings::Flags::new(flag_builder))?;
    let mut jit_builder = JITBuilder::with_isa(isa, default_libcall_names());
    libcalls::register_symbols(&mut jit_builder);
    let mut module = JITModule::new(jit_builder);

    let mut ctx = module.make_context();
    let mut func_ctx = FunctionBuilderContext::new();

    let ptr_ty = module.target_config().pointer_type();
    let mut sig = module.make_signature();
    sig.params.push(AbiParam::new(ptr_ty));
    sig.params.push(AbiParam::new(ptr_ty));
    sig.params.push(AbiParam::new(ptr_ty));
    sig.params.push(AbiParam::new(ptr_ty));
    sig.returns.push(AbiParam::new(types::I32));

    let func_id = module.declare_function("ttsl_shader", Linkage::Export, &sig)?;
    ctx.func.signature = sig;
    ctx.func.name = UserFuncName::user(0, func_id.as_u32());

    let libcalls = libcalls::declare(&mut module, &mut ctx.func)?;

    {
        let mut builder = FunctionBuilder::new(&mut ctx.func, &mut func_ctx);
        ir_lower::lower_module(&mut builder, ssa, ptr_ty, &libcalls)?;
        builder.seal_all_blocks();
        builder.finalize(module.target_config());
    }

    module.define_function(func_id, &mut ctx)?;
    module.clear_context(&mut ctx);
    module.finalize_definitions()?;

    let code = module.get_finalized_function(func_id);
    let func = unsafe { std::mem::transmute::<*const u8, ShaderFn>(code) };

    Ok(CompiledShader {
        _module: module,
        func,
    })
}

/// Parse dumped SSA JSON and compile it.
pub fn compile_ttsl_json(json: &str) -> Result<CompiledShader, JitError> {
    let ssa = TtslSsaModule::from_json(json).map_err(JitError::Ir)?;
    compile_ttsl(&ssa)
}

#[cfg(test)]
#[allow(dead_code)]
#[path = "../../../benches/ttsl/fixtures.rs"]
mod bench_fixtures;

#[cfg(test)]
mod tests {
    use super::*;
    use nalgebra_glm::{Vec2, Vec3};
    use std::mem::{align_of, offset_of, size_of};

    struct ConstTextureEnv;
    impl TtslTextureEnv for ConstTextureEnv {
        fn sample_tt_texture(&self, _idx: i32, uv: Vec2) -> Vec4 {
            Vec4::new(uv.x, uv.y, 0.5, 1.0)
        }
    }

    fn seed_fixture(fixture: &bench_fixtures::TtslBenchFixture) -> Registers {
        let mut regs = Registers::new();
        for (reg, value) in fixture.seed_bool {
            regs.bool_[*reg] = *value;
        }
        for (reg, value) in fixture.seed_i32 {
            regs.i32_[*reg] = *value;
        }
        for (reg, value) in fixture.seed_f32 {
            regs.f32_[*reg] = *value;
        }
        for (reg, value) in fixture.seed_v2 {
            regs.v2[*reg] = Vec2::new(value[0], value[1]);
        }
        for (reg, value) in fixture.seed_v3 {
            regs.v3[*reg] = Vec3::new(value[0], value[1], value[2]);
        }
        for (reg, value) in fixture.seed_v4 {
            regs.v4[*reg] = Vec4::new(value[0], value[1], value[2], value[3]);
        }
        regs
    }

    #[test]
    fn register_layout_matches_nalgebra_packing() {
        assert_eq!(size_of::<Vec2>(), 8);
        assert_eq!(size_of::<Vec3>(), 12);
        assert_eq!(size_of::<Vec4>(), 16);
        assert_eq!(align_of::<Vec3>(), 4);
        assert_eq!(offset_of!(Registers, i32_) % 4, 0);
        assert_eq!(offset_of!(Registers, f32_) % 4, 0);
        assert_eq!(offset_of!(Registers, v2) % 4, 0);
        assert_eq!(offset_of!(Registers, v3) % 4, 0);
        assert_eq!(offset_of!(Registers, v4) % 4, 0);
        assert_eq!(
            size_of::<JitTextureEnv>(),
            size_of::<*const dyn TtslTextureEnv>()
        );
        assert_eq!(
            size_of::<JitLightEnv>(),
            size_of::<*const dyn TtslLightEnv>()
        );
    }

    #[test]
    fn unsupported_ir_op_fails_compile() {
        let json = r#"{
            "version": 1,
            "entry": 0,
            "temps": {"1": "F32"},
            "consts": [{"id": 0, "ty": "F32", "value": [0.0]}],
            "blocks": [{
                "id": 0,
                "name": "_INIT_",
                "instrs": [
                    {"op": "load_const", "ty": "F32", "dst": 1, "imm": 0},
                    {"op": "sqrt", "ty": "F32", "dst": 1, "src": [1]},
                    {"op": "ret", "src": [1, 1, 1]}
                ]
            }]
        }"#;
        match compile_ttsl_json(json) {
            Err(JitError::UnsupportedIr(op)) => assert_eq!(op, "sqrt"),
            Err(err) => panic!("expected UnsupportedIr(sqrt), got {err}"),
            Ok(_) => panic!("expected compile to fail for sqrt"),
        }
    }

    #[test]
    fn ir_phi_join_takes_true_branch() {
        let json = r#"{
            "version": 1,
            "entry": 0,
            "inputs": [],
            "temps": {
                "1": "F32", "2": "F32", "3": "BOOL",
                "4": "F32", "5": "F32", "6": "F32",
                "7": "F32", "8": "F32", "9": "F32", "10": "V4", "11": "I32"
            },
            "consts": [
                {"id": 0, "ty": "F32", "value": [1.0]},
                {"id": 1, "ty": "F32", "value": [0.5]},
                {"id": 2, "ty": "F32", "value": [4.0]},
                {"id": 3, "ty": "F32", "value": [5.0]},
                {"id": 4, "ty": "F32", "value": [0.0]},
                {"id": 5, "ty": "F32", "value": [1.0]},
                {"id": 6, "ty": "I32", "value": [0]}
            ],
            "blocks": [
                {"id": 0, "name": "entry", "phis": [], "instrs": [
                    {"op": "load_const", "ty": "F32", "dst": 1, "imm": 0},
                    {"op": "load_const", "ty": "F32", "dst": 2, "imm": 1},
                    {"op": "cmp_gt", "ty": "BOOL", "dst": 3, "src": [1, 2]},
                    {"op": "jmp_if_false", "src": [3], "target": 2, "fallthrough": 1}
                ]},
                {"id": 1, "name": "then", "phis": [], "instrs": [
                    {"op": "load_const", "ty": "F32", "dst": 4, "imm": 2},
                    {"op": "jmp", "target": 3}
                ]},
                {"id": 2, "name": "else", "phis": [], "instrs": [
                    {"op": "load_const", "ty": "F32", "dst": 5, "imm": 3},
                    {"op": "jmp", "target": 3}
                ]},
                {"id": 3, "name": "join", "phis": [
                    {"dst": 6, "ty": "F32", "operands": [[1, 4], [2, 5]]}
                ], "instrs": [
                    {"op": "load_const", "ty": "F32", "dst": 7, "imm": 4},
                    {"op": "load_const", "ty": "F32", "dst": 8, "imm": 4},
                    {"op": "load_const", "ty": "F32", "dst": 9, "imm": 5},
                    {"op": "store_vec_from_scalar", "ty": "V4", "dst": 10, "src": [6, 7, 8, 9]},
                    {"op": "load_const", "ty": "I32", "dst": 11, "imm": 6},
                    {"op": "ret", "src": [10, 10, 11]}
                ]}
            ]
        }"#;
        let compiled = compile_ttsl_json(json).expect("phi diamond should compile");
        let mut regs = Registers::new();
        let (front, _back, glyph) = compiled.run(&mut regs, None, None);
        assert!((front.x - 4.0).abs() < 1e-6, "front.x={}", front.x);
        assert_eq!(glyph, 0);
    }

    #[test]
    fn fixtures_compile_and_run() {
        let tex = ConstTextureEnv;
        for fixture in bench_fixtures::FIXTURES {
            let compiled = compile_ttsl_json(fixture.ssa_json)
                .unwrap_or_else(|err| panic!("{}: compile failed: {err}", fixture.name));
            let mut regs = seed_fixture(fixture);
            let env = if fixture.needs_texture_env {
                Some(&tex as &dyn TtslTextureEnv)
            } else {
                None
            };
            let (_front, _back, glyph) = compiled.run(&mut regs, env, None);
            let _ = glyph;
        }
    }

    #[test]
    fn tt_texture_samples_via_trait_env() {
        struct MockTex;
        impl TtslTextureEnv for MockTex {
            fn sample_tt_texture(&self, _idx: i32, _uv: Vec2) -> Vec4 {
                Vec4::new(0.25, 0.5, 0.75, 1.0)
            }
        }
        let json = r#"{
            "version": 1,
            "entry": 0,
            "inputs": [
                {"name": "idx", "ty": "I32", "temp": 1, "reg": 10},
                {"name": "uv", "ty": "V2", "temp": 2, "reg": 11}
            ],
            "temps": {"1": "I32", "2": "V2", "3": "V4", "4": "I32"},
            "consts": [{"id": 0, "ty": "I32", "value": [0]}],
            "blocks": [{
                "id": 0,
                "name": "entry",
                "instrs": [
                    {"op": "tt_texture", "ty": "V4", "dst": 3, "src": [1, 2]},
                    {"op": "load_const", "ty": "I32", "dst": 4, "imm": 0},
                    {"op": "ret", "src": [3, 3, 4]}
                ]
            }]
        }"#;
        let compiled = compile_ttsl_json(json).expect("tt_texture SSA should compile");
        let mut regs = Registers::new();
        regs.i32_[10] = 0;
        regs.v2[11] = Vec2::new(0.25, 0.75);
        let tex = MockTex;
        let (front, _back, glyph) =
            compiled.run(&mut regs, Some(&tex as &dyn TtslTextureEnv), None);
        assert!((front.x - 0.25).abs() < 1e-5);
        assert!((front.y - 0.5).abs() < 1e-5);
        assert!((front.z - 0.75).abs() < 1e-5);
        assert!((front.w - 1.0).abs() < 1e-5);
        assert_eq!(glyph, 0);
    }

    #[test]
    fn tt_texture_without_env_is_opaque_black() {
        let json = r#"{
            "version": 1,
            "entry": 0,
            "inputs": [
                {"name": "idx", "ty": "I32", "temp": 1, "reg": 0},
                {"name": "uv", "ty": "V2", "temp": 2, "reg": 1}
            ],
            "temps": {"1": "I32", "2": "V2", "3": "V4", "4": "I32"},
            "consts": [{"id": 0, "ty": "I32", "value": [0]}],
            "blocks": [{
                "id": 0,
                "name": "entry",
                "instrs": [
                    {"op": "tt_texture", "ty": "V4", "dst": 3, "src": [1, 2]},
                    {"op": "load_const", "ty": "I32", "dst": 4, "imm": 0},
                    {"op": "ret", "src": [3, 3, 4]}
                ]
            }]
        }"#;
        let compiled = compile_ttsl_json(json).expect("tt_texture SSA should compile");
        let mut regs = Registers::new();
        regs.i32_[0] = 0;
        regs.v2[1] = Vec2::new(0.5, 0.5);
        let (front, _back, _glyph) = compiled.run(&mut regs, None, None);
        assert!((front.x - 0.0).abs() < 1e-5);
        assert!((front.y - 0.0).abs() < 1e-5);
        assert!((front.z - 0.0).abs() < 1e-5);
        assert!((front.w - 1.0).abs() < 1e-5);
    }

    struct MockLights;
    impl TtslLightEnv for MockLights {
        fn light_count(&self) -> i32 {
            3
        }
        fn light_type(&self, index: i32) -> i32 {
            match index {
                0 => 1,
                1 => 2,
                2 => 3,
                _ => 0,
            }
        }
        fn light_color(&self, index: i32) -> Vec3 {
            match index {
                0 => Vec3::new(0.2, 0.2, 0.2),
                1 => Vec3::new(0.8, 0.7, 0.6),
                _ => Vec3::zeros(),
            }
        }
        fn light_direction(&self, _index: i32) -> Vec3 {
            Vec3::new(0.0, 1.0, 0.0)
        }
        fn light_position(&self, _index: i32) -> Vec3 {
            Vec3::new(1.0, 2.0, 3.0)
        }
        fn light_attenuation(&self, _index: i32) -> Vec3 {
            Vec3::new(1.0, 0.09, 0.032)
        }
    }

    #[test]
    fn tt_light_accessors_read_trait_env() {
        let json = r#"{
            "version": 1,
            "entry": 0,
            "inputs": [{"name": "idx", "ty": "I32", "temp": 1, "reg": 4}],
            "temps": {
                "1": "I32", "2": "I32", "3": "I32", "4": "V3",
                "5": "V3", "6": "V3", "7": "V3", "8": "F32",
                "9": "F32", "10": "F32", "11": "F32", "12": "V4", "13": "I32"
            },
            "consts": [
                {"id": 0, "ty": "F32", "value": [0.0]},
                {"id": 1, "ty": "F32", "value": [1.0]},
                {"id": 2, "ty": "I32", "value": [0]}
            ],
            "blocks": [{
                "id": 0,
                "name": "entry",
                "instrs": [
                    {"op": "tt_lightCount", "ty": "I32", "dst": 2},
                    {"op": "tt_lightType", "ty": "I32", "dst": 3, "src": [1]},
                    {"op": "tt_lightColor", "ty": "V3", "dst": 4, "src": [1]},
                    {"op": "tt_lightDirection", "ty": "V3", "dst": 5, "src": [1]},
                    {"op": "tt_lightPosition", "ty": "V3", "dst": 6, "src": [1]},
                    {"op": "tt_lightAttenuation", "ty": "V3", "dst": 7, "src": [1]},
                    {"op": "load_const", "ty": "F32", "dst": 8, "imm": 0},
                    {"op": "read_axis_x", "ty": "F32", "dst": 9, "src": [4]},
                    {"op": "read_axis_y", "ty": "F32", "dst": 10, "src": [5]},
                    {"op": "load_const", "ty": "F32", "dst": 11, "imm": 1},
                    {"op": "store_vec_from_scalar", "ty": "V4", "dst": 12, "src": [9, 10, 8, 11]},
                    {"op": "load_const", "ty": "I32", "dst": 13, "imm": 2},
                    {"op": "ret", "src": [12, 12, 2]}
                ]
            }]
        }"#;
        let compiled = compile_ttsl_json(json).expect("light accessors should compile");
        let mut regs = Registers::new();
        regs.i32_[4] = 1;
        let lights = MockLights;
        let (front, _back, glyph) =
            compiled.run(&mut regs, None, Some(&lights as &dyn TtslLightEnv));
        // color.x of directional = 0.8, direction.y = 1.0
        assert!((front.x - 0.8).abs() < 1e-5, "front.x={}", front.x);
        assert!((front.y - 1.0).abs() < 1e-5, "front.y={}", front.y);
        assert_eq!(glyph, 3);
    }

    #[test]
    fn tt_light_without_env_is_zero() {
        let json = r#"{
            "version": 1,
            "entry": 0,
            "temps": {"1": "I32", "2": "V3", "3": "F32", "4": "F32", "5": "F32", "6": "F32", "7": "V4", "8": "I32"},
            "consts": [
                {"id": 0, "ty": "I32", "value": [0]},
                {"id": 1, "ty": "F32", "value": [0.0]},
                {"id": 2, "ty": "F32", "value": [1.0]}
            ],
            "blocks": [{
                "id": 0,
                "name": "entry",
                "instrs": [
                    {"op": "tt_lightCount", "ty": "I32", "dst": 1},
                    {"op": "load_const", "ty": "I32", "dst": 8, "imm": 0},
                    {"op": "tt_lightColor", "ty": "V3", "dst": 2, "src": [8]},
                    {"op": "read_axis_x", "ty": "F32", "dst": 3, "src": [2]},
                    {"op": "load_const", "ty": "F32", "dst": 4, "imm": 1},
                    {"op": "load_const", "ty": "F32", "dst": 5, "imm": 1},
                    {"op": "load_const", "ty": "F32", "dst": 6, "imm": 2},
                    {"op": "store_vec_from_scalar", "ty": "V4", "dst": 7, "src": [3, 4, 5, 6]},
                    {"op": "ret", "src": [7, 7, 1]}
                ]
            }]
        }"#;
        let compiled = compile_ttsl_json(json).expect("light accessors should compile");
        let mut regs = Registers::new();
        let (front, _back, glyph) = compiled.run(&mut regs, None, None);
        assert!((front.x - 0.0).abs() < 1e-5);
        assert_eq!(glyph, 0);
    }
}
