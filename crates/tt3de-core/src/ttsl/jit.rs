use cranelift_codegen::ir::{types, AbiParam, InstBuilder, UserFuncName};
use cranelift_codegen::settings::{self, Configurable};
use cranelift_frontend::{FunctionBuilder, FunctionBuilderContext};
use cranelift_jit::{JITBuilder, JITModule};
use cranelift_module::{default_libcall_names, Linkage, Module, ModuleError};

use super::{Instr, Registers};

/// Placeholder ABI for a future Cranelift-lowered shader.
///
/// The first implementation ignores the instruction stream and returns `0`.
pub type ShaderFn = unsafe extern "C" fn(*mut Registers) -> i32;

/// Owns JIT code pages for as long as the compiled shader is used.
pub struct CompiledShader {
    _module: JITModule,
    func: ShaderFn,
}

impl CompiledShader {
    pub fn as_fn(&self) -> ShaderFn {
        self.func
    }
}

#[derive(Debug)]
pub enum JitError {
    Native(String),
    Settings(settings::SetError),
    Codegen(cranelift_codegen::CodegenError),
    Module(ModuleError),
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
        }
    }
}

impl std::error::Error for JitError {}

/// Compile a dummy native function with the intended shader ABI.
///
/// `_instrs` is accepted so later opcode lowering can use this entry point
/// without renaming it. The current body does not interpret bytecode.
pub fn compile_ttsl(_instrs: &[Instr; 256]) -> Result<CompiledShader, JitError> {
    let mut flag_builder = settings::builder();
    flag_builder.set("use_colocated_libcalls", "false")?;
    flag_builder.set("is_pic", "false")?;

    let isa_builder =
        cranelift_native::builder().map_err(|msg| JitError::Native(msg.to_string()))?;
    let isa = isa_builder.finish(settings::Flags::new(flag_builder))?;
    let mut module = JITModule::new(JITBuilder::with_isa(isa, default_libcall_names()));

    let mut ctx = module.make_context();
    let mut func_ctx = FunctionBuilderContext::new();

    let mut sig = module.make_signature();
    sig.params
        .push(AbiParam::new(module.target_config().pointer_type()));
    sig.returns.push(AbiParam::new(types::I32));

    let func_id = module.declare_function("ttsl_dummy", Linkage::Export, &sig)?;
    ctx.func.signature = sig;
    ctx.func.name = UserFuncName::user(0, func_id.as_u32());

    {
        let mut builder = FunctionBuilder::new(&mut ctx.func, &mut func_ctx);
        let block = builder.create_block();
        builder.append_block_params_for_function_params(block);
        builder.switch_to_block(block);
        builder.seal_block(block);
        let zero = builder.ins().iconst(types::I32, 0);
        builder.ins().return_(&[zero]);
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
mod tests {
    use super::*;
    use crate::ttsl::decode_instrs_256;

    #[test]
    fn compile_ttsl_succeeds_on_padded_ret_stream() {
        let instrs = decode_instrs_256(&[]);
        compile_ttsl(&instrs).expect("dummy cranelift compile should succeed");
    }

    #[test]
    fn compiled_dummy_function_returns_zero() {
        let instrs = decode_instrs_256(&[]);
        let compiled = compile_ttsl(&instrs).expect("dummy cranelift compile should succeed");
        let mut regs = Registers::new();
        let ret = unsafe { (compiled.as_fn())(&mut regs) };
        assert_eq!(ret, 0);
    }
}
