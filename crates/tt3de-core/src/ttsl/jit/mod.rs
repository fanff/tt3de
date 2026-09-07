use cranelift_codegen::ir::{types, AbiParam, InstBuilder, UserFuncName};
use cranelift_codegen::settings::{self, Configurable};
use cranelift_frontend::{FunctionBuilder, FunctionBuilderContext};
use cranelift_jit::{JITBuilder, JITModule};
use cranelift_module::{default_libcall_names, Linkage, Module, ModuleError};
use nalgebra_glm::Vec4;

use super::{Instr, Registers, TtslTextureEnv};

mod libcalls;
mod lower;
mod mem;

/// Compiled shader ABI: register file, optional texture env, output struct.
///
/// Returns the glyph index (also stored in [`JitOutputs::glyph`]).
pub type ShaderFn =
    unsafe extern "C" fn(*mut Registers, *const JitTextureEnv, *mut JitOutputs) -> i32;

/// `true` once [`compile_ttsl`] lowers bytecode instead of emitting a dummy.
pub const LOWERS_BYTECODE: bool = true;

/// Front/back colors and glyph written by `OP_RET`.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct JitOutputs {
    pub front: [f32; 4],
    pub back: [f32; 4],
    pub glyph: i32,
}

/// Packed `dyn TtslTextureEnv` fat pointer for the compiled calling convention.
///
/// Pass a null `*const JitTextureEnv` when the interpreter would get `None`.
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

/// Owns JIT code pages for as long as the compiled shader is used.
pub struct CompiledShader {
    _module: JITModule,
    func: ShaderFn,
}

impl CompiledShader {
    pub fn as_fn(&self) -> ShaderFn {
        self.func
    }

    /// Run the compiled shader against the same register file and texture env
    /// the interpreter uses.
    pub fn run(&self, regs: &mut Registers, tex: Option<&dyn TtslTextureEnv>) -> (Vec4, Vec4, i32) {
        let env = tex.map(JitTextureEnv::from_ref);
        let env_ptr = env
            .as_ref()
            .map(|e| e as *const JitTextureEnv)
            .unwrap_or(std::ptr::null());
        let mut out = JitOutputs::default();
        let glyph = unsafe { (self.func)(regs, env_ptr, &mut out) };
        (
            Vec4::new(out.front[0], out.front[1], out.front[2], out.front[3]),
            Vec4::new(out.back[0], out.back[1], out.back[2], out.back[3]),
            glyph,
        )
    }
}

#[derive(Debug)]
pub enum JitError {
    Native(String),
    Settings(settings::SetError),
    Codegen(cranelift_codegen::CodegenError),
    Module(ModuleError),
    Unsupported(u8),
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
            Self::Unsupported(op) => write!(f, "unsupported TTSL opcode: {op}"),
        }
    }
}

impl std::error::Error for JitError {}

fn check_supported(instrs: &[Instr; 256]) -> Result<(), JitError> {
    for instr in instrs {
        if !lower::opcode_supported(instr.opcode) {
            return Err(JitError::Unsupported(instr.opcode));
        }
    }
    Ok(())
}

/// Compile TTSL bytecode to a native function with the shader ABI.
pub fn compile_ttsl(instrs: &[Instr; 256]) -> Result<CompiledShader, JitError> {
    check_supported(instrs)?;

    let mut flag_builder = settings::builder();
    flag_builder.set("use_colocated_libcalls", "false")?;
    flag_builder.set("is_pic", "false")?;

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
    sig.returns.push(AbiParam::new(types::I32));

    let func_id = module.declare_function("ttsl_shader", Linkage::Export, &sig)?;
    ctx.func.signature = sig;
    ctx.func.name = UserFuncName::user(0, func_id.as_u32());

    let libcalls = libcalls::declare(&mut module, &mut ctx.func)?;

    {
        let mut builder = FunctionBuilder::new(&mut ctx.func, &mut func_ctx);
        let blocks: Vec<_> = (0..256).map(|_| builder.create_block()).collect();
        builder.append_block_params_for_function_params(blocks[0]);

        let regs_var = builder.declare_var(ptr_ty);
        let tex_var = builder.declare_var(ptr_ty);
        let out_var = builder.declare_var(ptr_ty);

        builder.switch_to_block(blocks[0]);
        let params = {
            let p = builder.block_params(blocks[0]);
            [p[0], p[1], p[2]]
        };
        builder.def_var(regs_var, params[0]);
        builder.def_var(tex_var, params[1]);
        builder.def_var(out_var, params[2]);

        for ip in 0..256 {
            builder.switch_to_block(blocks[ip]);
            let regs = builder.use_var(regs_var);
            let tex = builder.use_var(tex_var);
            let out = builder.use_var(out_var);
            let mut cx = lower::LowerCx {
                builder: &mut builder,
                regs,
                tex,
                out,
                blocks: &blocks,
                libcalls: &libcalls,
            };
            let terminated = lower::lower_instr(&mut cx, ip, &instrs[ip])?;
            if !terminated {
                if ip + 1 < 256 {
                    builder.ins().jump(blocks[ip + 1], &[]);
                } else {
                    let zero = builder.ins().iconst(types::I32, 0);
                    builder.ins().return_(&[zero]);
                }
            }
        }

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

#[cfg(test)]
#[allow(dead_code)]
#[path = "../../../benches/ttsl/fixtures.rs"]
mod bench_fixtures;

#[cfg(test)]
mod tests {
    use super::bench_fixtures;
    use super::*;
    use crate::ttsl::opcodes::*;
    use crate::ttsl::{decode_instrs_256, run_ttsl};
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
    }

    #[test]
    fn compile_ttsl_succeeds_on_padded_ret_stream() {
        let instrs = decode_instrs_256(&[]);
        compile_ttsl(&instrs).expect("empty ret stream should compile");
    }

    #[test]
    fn compiled_empty_function_returns_zeros() {
        let instrs = decode_instrs_256(&[]);
        let compiled = compile_ttsl(&instrs).unwrap();
        let mut regs = Registers::new();
        let out = compiled.run(&mut regs, None);
        assert_eq!(out, (Vec4::zeros(), Vec4::zeros(), 0));
    }

    #[test]
    fn unsupported_opcode_fails_compile() {
        let mut instrs = decode_instrs_256(&[]);
        instrs[0].opcode = COS_F32;
        match compile_ttsl(&instrs) {
            Err(JitError::Unsupported(COS_F32)) => {}
            Err(err) => panic!("expected Unsupported(COS_F32), got {err}"),
            Ok(_) => panic!("expected compile to fail for COS_F32"),
        }
    }

    #[test]
    fn fixtures_only_use_supported_opcodes() {
        for fixture in bench_fixtures::FIXTURES {
            for chunk in fixture.bytecode.chunks_exact(6) {
                let op = chunk[0];
                assert!(
                    lower::opcode_supported(op),
                    "{} uses opcode {op} the JIT does not lower",
                    fixture.name
                );
            }
        }
    }

    #[test]
    fn add_f32_matches_interpreter() {
        let instrs = decode_instrs_256(&[ADD_F32, 2, 0, 1, 0, 0, OP_RET, 0, 0, 0, 0, 0]);
        let mut regs = Registers::new();
        regs.f32_[0] = 1.5;
        regs.f32_[1] = 2.25;
        let compiled = compile_ttsl(&instrs).unwrap();
        let mut jit_regs = regs.clone();
        let interp = run_ttsl(&instrs, &mut regs, None);
        let jit = compiled.run(&mut jit_regs, None);
        assert_eq!(interp, jit);
        assert!((jit_regs.f32_[2] - 3.75).abs() < 1e-6);
    }

    #[test]
    fn jmp_if_false_matches_interpreter() {
        let instrs = decode_instrs_256(&[
            OP_JMP_IF_FALSE,
            2,
            5,
            0,
            0,
            0,
            OP_RET,
            0,
            1,
            1,
            0,
            0,
            OP_RET,
            0,
            2,
            2,
            0,
            0,
        ]);
        let compiled = compile_ttsl(&instrs).unwrap();

        let mut seed = Registers::new();
        seed.v4[1] = Vec4::new(1.0, 0.0, 0.0, 1.0);
        seed.v4[2] = Vec4::new(0.0, 1.0, 0.0, 1.0);

        for flag in [true, false] {
            let mut interp_regs = seed.clone();
            interp_regs.bool_[5] = flag;
            let mut jit_regs = interp_regs.clone();
            let interp = run_ttsl(&instrs, &mut interp_regs, None);
            let jit = compiled.run(&mut jit_regs, None);
            assert_eq!(interp, jit, "bool={flag}");
        }
    }

    #[test]
    fn tt_texture_with_and_without_env_matches_interpreter() {
        let instrs = decode_instrs_256(&[TT_TEXTURE, 12, 10, 11, 0, 0, OP_RET, 0, 12, 12, 0, 0]);
        let compiled = compile_ttsl(&instrs).unwrap();
        let mut seed = Registers::new();
        seed.i32_[10] = 0;
        seed.v2[11] = Vec2::new(0.25, 0.75);

        let mut interp_regs = seed.clone();
        let mut jit_regs = seed.clone();
        let interp = run_ttsl(&instrs, &mut interp_regs, None);
        let jit = compiled.run(&mut jit_regs, None);
        assert_eq!(interp, jit);

        let tex = ConstTextureEnv;
        let env: &dyn TtslTextureEnv = &tex;
        let mut interp_regs = seed.clone();
        let mut jit_regs = seed.clone();
        let interp = run_ttsl(&instrs, &mut interp_regs, Some(env));
        let jit = compiled.run(&mut jit_regs, Some(env));
        assert_eq!(interp, jit);
        assert!((jit.0.x - 0.25).abs() < 1e-5);
        assert!((jit.0.y - 0.75).abs() < 1e-5);
        assert!((jit.0.z - 0.5).abs() < 1e-5);
    }

    #[test]
    fn bench_fixtures_match_interpreter() {
        let tex = ConstTextureEnv;
        for fixture in bench_fixtures::FIXTURES {
            let instrs = decode_instrs_256(fixture.bytecode);
            let compiled = compile_ttsl(&instrs)
                .unwrap_or_else(|err| panic!("{}: compile failed: {err}", fixture.name));
            let seed = seed_fixture(fixture);
            let env = if fixture.needs_texture_env {
                Some(&tex as &dyn TtslTextureEnv)
            } else {
                None
            };
            let mut interp_regs = seed.clone();
            let mut jit_regs = seed;
            let interp = run_ttsl(&instrs, &mut interp_regs, env);
            let jit = compiled.run(&mut jit_regs, env);
            assert_eq!(interp, jit, "{}", fixture.name);
        }
    }
}
