//! Lower a post-SSA TTSL module to CLIF.
//!
//! Seeded inputs are loaded from the VM register file once at entry. Everything
//! else stays in Cranelift SSA values (vectors as scalar lanes). Phis become
//! `FunctionBuilder` variable merges, with trampoline blocks on conditional
//! edges so each successor can receive a different incoming value.

use std::collections::HashMap;

use cranelift_codegen::ir::condcodes::FloatCC;
use cranelift_codegen::ir::immediates::Ieee32;
use cranelift_codegen::ir::{types, Block, InstBuilder, StackSlotData, StackSlotKind, Type, Value};
use cranelift_frontend::{FunctionBuilder, Variable};

use super::libcalls::Libcalls;
use super::mem;
use super::JitError;
use crate::ttsl::ir::{IrTy, SsaConst, SsaInstr, TtslSsaModule};

struct TempVars {
    ty: IrTy,
    comps: [Option<Variable>; 4],
}

pub struct IrLowerCx<'a, 'b> {
    builder: &'a mut FunctionBuilder<'b>,
    regs: Option<Value>,
    tex: Option<Value>,
    out: Option<Value>,
    regs_var: cranelift_frontend::Variable,
    tex_var: cranelift_frontend::Variable,
    out_var: cranelift_frontend::Variable,
    ptr_ty: Type,
    libcalls: &'a Libcalls,
    blocks: HashMap<u32, Block>,
    vars: HashMap<u32, TempVars>,
    consts: HashMap<u32, SsaConst>,
    module: &'a TtslSsaModule,
}

pub fn lower_module(
    builder: &mut FunctionBuilder,
    module: &TtslSsaModule,
    ptr_ty: Type,
    libcalls: &Libcalls,
) -> Result<(), JitError> {
    let mut blocks = HashMap::new();
    for block in &module.blocks {
        blocks.insert(block.id, builder.create_block());
    }
    let entry_clif = *blocks
        .get(&module.entry)
        .ok_or_else(|| JitError::Ir("entry block missing from CLIF map".into()))?;
    builder.append_block_params_for_function_params(entry_clif);

    let mut vars = HashMap::new();
    for (id_s, ty) in &module.temps {
        let id: u32 = id_s
            .parse()
            .map_err(|_| JitError::Ir(format!("bad temp id {id_s}")))?;
        vars.insert(id, declare_temp(builder, *ty));
    }
    for block in &module.blocks {
        for phi in &block.phis {
            vars.entry(phi.dst)
                .or_insert_with(|| declare_temp(builder, phi.ty));
            for (_, src) in &phi.operands {
                if let Some(ty) = module.temp_ty(*src) {
                    vars.entry(*src)
                        .or_insert_with(|| declare_temp(builder, ty));
                } else {
                    vars.entry(*src)
                        .or_insert_with(|| declare_temp(builder, phi.ty));
                }
            }
        }
        for instr in &block.instrs {
            if let Some(dst) = instr.dst {
                let ty = instr
                    .ty
                    .or_else(|| module.temp_ty(dst))
                    .ok_or_else(|| JitError::UnsupportedIr(format!("{} missing type", instr.op)))?;
                vars.entry(dst).or_insert_with(|| declare_temp(builder, ty));
            }
            for src in &instr.src {
                if let Some(ty) = module.temp_ty(*src) {
                    vars.entry(*src)
                        .or_insert_with(|| declare_temp(builder, ty));
                }
            }
        }
    }

    let consts = module
        .consts
        .iter()
        .cloned()
        .map(|c| (c.id, c))
        .collect::<HashMap<_, _>>();

    let regs_var = builder.declare_var(ptr_ty);
    let tex_var = builder.declare_var(ptr_ty);
    let out_var = builder.declare_var(ptr_ty);

    let mut cx = IrLowerCx {
        builder,
        regs: None,
        tex: None,
        out: None,
        regs_var,
        tex_var,
        out_var,
        ptr_ty,
        libcalls,
        blocks,
        vars,
        consts,
        module,
    };

    // Lower every block. ABI pointers and seeded inputs are bound in the entry
    // block so we never switch away from an unterminated block.
    let block_ids: Vec<u32> = module.blocks.iter().map(|b| b.id).collect();
    for id in block_ids {
        cx.lower_block(id)?;
    }
    Ok(())
}

fn declare_temp(builder: &mut FunctionBuilder, ty: IrTy) -> TempVars {
    let mut comps = [None; 4];
    let clif_ty = match ty {
        IrTy::Bool => types::I8,
        IrTy::I32 => types::I32,
        IrTy::F32 | IrTy::V2 | IrTy::V3 | IrTy::V4 => types::F32,
    };
    for i in 0..ty.width() {
        comps[i] = Some(builder.declare_var(clif_ty));
    }
    TempVars { ty, comps }
}

impl IrLowerCx<'_, '_> {
    fn refresh_abi(&mut self) {
        self.regs = Some(self.builder.use_var(self.regs_var));
        self.tex = Some(self.builder.use_var(self.tex_var));
        self.out = Some(self.builder.use_var(self.out_var));
    }

    fn regs(&self) -> Result<Value, JitError> {
        self.regs
            .ok_or_else(|| JitError::Ir("ABI registers used before entry bind".into()))
    }

    fn tex(&self) -> Result<Value, JitError> {
        self.tex
            .ok_or_else(|| JitError::Ir("ABI tex used before entry bind".into()))
    }

    fn out(&self) -> Result<Value, JitError> {
        self.out
            .ok_or_else(|| JitError::Ir("ABI out used before entry bind".into()))
    }

    fn clif(&self, id: u32) -> Result<Block, JitError> {
        self.blocks
            .get(&id)
            .copied()
            .ok_or_else(|| JitError::Ir(format!("jump to missing block {id}")))
    }

    fn temp(&self, id: u32) -> Result<&TempVars, JitError> {
        self.vars
            .get(&id)
            .ok_or_else(|| JitError::Ir(format!("unknown temp {id}")))
    }

    fn use_temp(&mut self, id: u32) -> Result<Vec<Value>, JitError> {
        let comps: Vec<Variable> = {
            let vars = self.temp(id)?;
            (0..vars.ty.width())
                .map(|i| vars.comps[i].expect("component declared"))
                .collect()
        };
        let mut out = Vec::with_capacity(comps.len());
        for v in comps {
            out.push(self.builder.use_var(v));
        }
        Ok(out)
    }

    fn def_temp(&mut self, id: u32, vals: &[Value]) -> Result<(), JitError> {
        let width = self.temp(id)?.ty.width();
        if vals.len() != width {
            return Err(JitError::Ir(format!(
                "temp {id} expected {width} lanes, got {}",
                vals.len()
            )));
        }
        let comps: Vec<Variable> = (0..width)
            .map(|i| self.vars[&id].comps[i].expect("component declared"))
            .collect();
        for (var, val) in comps.into_iter().zip(vals.iter().copied()) {
            self.builder.def_var(var, val);
        }
        Ok(())
    }

    fn zeros(&mut self, ty: IrTy) -> Vec<Value> {
        match ty {
            IrTy::Bool => vec![self.builder.ins().iconst(types::I8, 0)],
            IrTy::I32 => vec![self.builder.ins().iconst(types::I32, 0)],
            IrTy::F32 | IrTy::V2 | IrTy::V3 | IrTy::V4 => {
                let z = self.builder.ins().f32const(Ieee32::with_float(0.0));
                vec![z; ty.width()]
            }
        }
    }

    fn def_phis_from(&mut self, pred: u32, dest: u32) -> Result<(), JitError> {
        let phis: Vec<_> = self
            .module
            .block(dest)
            .map(|b| b.phis.clone())
            .unwrap_or_default();
        for phi in phis {
            let vals = match phi.operand_from(pred) {
                Some(src) => self.use_temp(src)?,
                None => self.zeros(phi.ty),
            };
            self.def_temp(phi.dst, &vals)?;
        }
        Ok(())
    }

    fn dest_has_phis(&self, dest: u32) -> bool {
        self.module
            .block(dest)
            .map(|b| !b.phis.is_empty())
            .unwrap_or(false)
    }

    fn jump_to(&mut self, from: u32, dest: u32) -> Result<(), JitError> {
        self.def_phis_from(from, dest)?;
        let block = self.clif(dest)?;
        self.builder.ins().jump(block, &[]);
        Ok(())
    }

    fn brif_to(
        &mut self,
        from: u32,
        cond: Value,
        taken: u32,
        fallthrough: u32,
    ) -> Result<(), JitError> {
        let then_bb = self.maybe_tramp(fallthrough)?;
        let else_bb = self.maybe_tramp(taken)?;
        self.builder.ins().brif(cond, then_bb, &[], else_bb, &[]);
        self.fill_tramp(from, fallthrough, then_bb)?;
        self.fill_tramp(from, taken, else_bb)?;
        Ok(())
    }

    fn maybe_tramp(&mut self, dest: u32) -> Result<Block, JitError> {
        if self.dest_has_phis(dest) {
            Ok(self.builder.create_block())
        } else {
            self.clif(dest)
        }
    }

    fn fill_tramp(&mut self, from: u32, dest: u32, bb: Block) -> Result<(), JitError> {
        if !self.dest_has_phis(dest) {
            return Ok(());
        }
        let dest_block = self.clif(dest)?;
        self.builder.switch_to_block(bb);
        self.def_phis_from(from, dest)?;
        self.builder.ins().jump(dest_block, &[]);
        Ok(())
    }

    fn lower_block(&mut self, id: u32) -> Result<(), JitError> {
        let clif = self.clif(id)?;
        self.builder.switch_to_block(clif);
        if id == self.module.entry {
            let params = {
                let p = self.builder.block_params(clif);
                [p[0], p[1], p[2]]
            };
            self.builder.def_var(self.regs_var, params[0]);
            self.builder.def_var(self.tex_var, params[1]);
            self.builder.def_var(self.out_var, params[2]);
            self.regs = Some(params[0]);
            self.tex = Some(params[1]);
            self.out = Some(params[2]);
            self.load_inputs()?;
        } else {
            self.refresh_abi();
        }
        let instrs = self.module.block(id).expect("block exists").instrs.clone();
        for instr in instrs {
            if self.lower_instr(id, &instr)? {
                return Ok(());
            }
        }
        Err(JitError::Ir(format!("block {id} fell off the end")))
    }

    fn load_inputs(&mut self) -> Result<(), JitError> {
        let inputs = self.module.inputs.clone();
        let regs = self.regs()?;
        for input in inputs {
            let reg = input
                .reg
                .ok_or_else(|| JitError::Ir(format!("input {} has no VM register", input.name)))?;
            if reg > 255 {
                return Err(JitError::Ir(format!(
                    "input {} register {reg} is out of range",
                    input.name
                )));
            }
            let loaded = load_from_regs(self.builder, regs, input.ty, reg as u8);
            self.def_temp(input.temp, &loaded)?;
        }
        Ok(())
    }

    fn lower_instr(&mut self, from: u32, instr: &SsaInstr) -> Result<bool, JitError> {
        match instr.op.as_str() {
            "jmp" => {
                let dest = instr
                    .target
                    .ok_or_else(|| JitError::UnsupportedIr("jmp missing target".into()))?;
                self.jump_to(from, dest)?;
                Ok(true)
            }
            "jmp_if_false" => {
                let dest = instr
                    .target
                    .ok_or_else(|| JitError::UnsupportedIr("jmp_if_false missing target".into()))?;
                let fall = instr.fallthrough.ok_or_else(|| {
                    JitError::UnsupportedIr("jmp_if_false missing fallthrough".into())
                })?;
                let cond = scalar(self.use_temp(src1(instr)?)?)?;
                self.brif_to(from, cond, dest, fall)?;
                Ok(true)
            }
            "ret" => {
                if instr.src.len() != 3 {
                    return Err(JitError::UnsupportedIr("ret needs 3 sources".into()));
                }
                let front = vec4(self.use_temp(instr.src[0])?)?;
                let back = vec4(self.use_temp(instr.src[1])?)?;
                let glyph = scalar(self.use_temp(instr.src[2])?)?;
                mem::store_outputs_values(self.builder, self.out()?, front, back, glyph);
                self.builder.ins().return_(&[glyph]);
                Ok(true)
            }
            "load_const" => {
                let dst = dst_of(instr)?;
                let imm = instr
                    .imm
                    .ok_or_else(|| JitError::UnsupportedIr("load_const missing imm".into()))?;
                let c = self
                    .consts
                    .get(&imm)
                    .ok_or_else(|| JitError::Ir(format!("missing const {imm}")))?
                    .clone();
                let vals = self.const_values(&c)?;
                self.def_temp(dst, &vals)?;
                Ok(false)
            }
            "store" => {
                let dst = dst_of(instr)?;
                let src = self.use_temp(src1(instr)?)?;
                self.def_temp(dst, &src)?;
                Ok(false)
            }
            "add" => self.bin(instr, BinKind::Add),
            "sub" => self.bin(instr, BinKind::Sub),
            "mul" => self.bin(instr, BinKind::Mul),
            "div" => self.bin(instr, BinKind::Div),
            "neg" => self.uni_neg(instr),
            "abs" => self.uni_abs(instr),
            "sin" => {
                let f = self.libcalls.sin_f32;
                self.call_f32_lanes(instr, f, 1)
            }
            "cos" => {
                let f = self.libcalls.cos_f32;
                self.call_f32_lanes(instr, f, 1)
            }
            "floor" => {
                let f = self.libcalls.floor_f32;
                self.call_f32_lanes(instr, f, 1)
            }
            "ceil" => {
                let f = self.libcalls.ceil_f32;
                self.call_f32_lanes(instr, f, 1)
            }
            "fract" => {
                let f = self.libcalls.fract_f32;
                self.call_f32_lanes(instr, f, 1)
            }
            "mod" => {
                let f = self.libcalls.mod_f32;
                self.call_f32_lanes(instr, f, 2)
            }
            "max" => {
                let f = self.libcalls.max_f32;
                self.call_f32_lanes(instr, f, 2)
            }
            "clamp" => {
                let f = self.libcalls.clamp_f32;
                self.call_f32_lanes(instr, f, 3)
            }
            "cmp_gt" => self.cmp(instr, FloatCC::GreaterThan),
            "cmp_gte" => self.cmp(instr, FloatCC::GreaterThanOrEqual),
            "dot" => self.dot(instr),
            "length" => self.length(instr),
            "normalize" => self.normalize(instr),
            "read_axis_x" => self.read_axis(instr, 0),
            "read_axis_y" => self.read_axis(instr, 1),
            "read_axis_z" => self.read_axis(instr, 2),
            "read_axis_w" => self.read_axis(instr, 3),
            "store_vec_from_scalar" => self.store_vec_from_scalar(instr),
            "tt_texture" => self.tt_texture(instr),
            other => Err(JitError::UnsupportedIr(other.into())),
        }
    }

    fn bin(&mut self, instr: &SsaInstr, kind: BinKind) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let ty = self.temp(dst)?.ty;
        let lhs = broadcast(self.use_temp(src_at(instr, 0)?)?, ty.width())?;
        let rhs = broadcast(self.use_temp(src_at(instr, 1)?)?, ty.width())?;
        let mut out = Vec::with_capacity(ty.width());
        for i in 0..ty.width() {
            let x = lhs[i];
            let y = rhs[i];
            let r = match (ty, kind) {
                (IrTy::I32, BinKind::Add) => self.builder.ins().iadd(x, y),
                (IrTy::I32, BinKind::Sub) => self.builder.ins().isub(x, y),
                (IrTy::I32, BinKind::Mul) => self.builder.ins().imul(x, y),
                (IrTy::F32 | IrTy::V2 | IrTy::V3 | IrTy::V4, BinKind::Add) => {
                    self.builder.ins().fadd(x, y)
                }
                (IrTy::F32 | IrTy::V2 | IrTy::V3 | IrTy::V4, BinKind::Sub) => {
                    self.builder.ins().fsub(x, y)
                }
                (IrTy::F32 | IrTy::V2 | IrTy::V3 | IrTy::V4, BinKind::Mul) => {
                    self.builder.ins().fmul(x, y)
                }
                (IrTy::F32 | IrTy::V2 | IrTy::V3 | IrTy::V4, BinKind::Div) => {
                    self.builder.ins().fdiv(x, y)
                }
                _ => return Err(JitError::UnsupportedIr(format!("{kind:?} on {ty}"))),
            };
            out.push(r);
        }
        self.def_temp(dst, &out)?;
        Ok(false)
    }

    fn uni_neg(&mut self, instr: &SsaInstr) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let src = self.use_temp(src1(instr)?)?;
        let mut out = Vec::new();
        for v in src {
            out.push(self.builder.ins().fneg(v));
        }
        self.def_temp(dst, &out)?;
        Ok(false)
    }

    fn uni_abs(&mut self, instr: &SsaInstr) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let src = self.use_temp(src1(instr)?)?;
        let mut out = Vec::new();
        for v in src {
            out.push(self.builder.ins().fabs(v));
        }
        self.def_temp(dst, &out)?;
        Ok(false)
    }

    fn call_f32_lanes(
        &mut self,
        instr: &SsaInstr,
        func: cranelift_codegen::ir::FuncRef,
        n: usize,
    ) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        if instr.src.len() != n {
            return Err(JitError::UnsupportedIr(format!(
                "{} expected {n} args",
                instr.op
            )));
        }
        let width = self.temp(dst)?.ty.width();
        let mut arg_lanes = Vec::with_capacity(n);
        for src in &instr.src {
            arg_lanes.push(broadcast(self.use_temp(*src)?, width)?);
        }
        let mut out = Vec::with_capacity(width);
        for i in 0..width {
            let args: Vec<Value> = arg_lanes.iter().map(|a| a[i]).collect();
            let call = self.builder.ins().call(func, &args);
            out.push(self.builder.inst_results(call)[0]);
        }
        self.def_temp(dst, &out)?;
        Ok(false)
    }

    fn cmp(&mut self, instr: &SsaInstr, cc: FloatCC) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let x = scalar(self.use_temp(src_at(instr, 0)?)?)?;
        let y = scalar(self.use_temp(src_at(instr, 1)?)?)?;
        let r = self.builder.ins().fcmp(cc, x, y);
        self.def_temp(dst, &[r])?;
        Ok(false)
    }

    fn dot(&mut self, instr: &SsaInstr) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let a = self.use_temp(src_at(instr, 0)?)?;
        let b = self.use_temp(src_at(instr, 1)?)?;
        if a.len() != b.len() {
            return Err(JitError::UnsupportedIr("dot width mismatch".into()));
        }
        let mut acc = None;
        for (x, y) in a.into_iter().zip(b) {
            let p = self.builder.ins().fmul(x, y);
            acc = Some(match acc {
                None => p,
                Some(prev) => self.builder.ins().fadd(prev, p),
            });
        }
        self.def_temp(dst, &[acc.expect("dot of empty vector")])?;
        Ok(false)
    }

    fn length(&mut self, instr: &SsaInstr) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let v = self.use_temp(src1(instr)?)?;
        let r = if v.len() == 2 {
            let call = self
                .builder
                .ins()
                .call(self.libcalls.length_v2, &[v[0], v[1]]);
            self.builder.inst_results(call)[0]
        } else {
            let mut acc = None;
            for lane in v {
                let sq = self.builder.ins().fmul(lane, lane);
                acc = Some(match acc {
                    None => sq,
                    Some(prev) => self.builder.ins().fadd(prev, sq),
                });
            }
            self.builder
                .ins()
                .sqrt(acc.expect("length of empty vector"))
        };
        self.def_temp(dst, &[r])?;
        Ok(false)
    }

    fn normalize(&mut self, instr: &SsaInstr) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let v = self.use_temp(src1(instr)?)?;
        let mut acc = None;
        for lane in &v {
            let sq = self.builder.ins().fmul(*lane, *lane);
            acc = Some(match acc {
                None => sq,
                Some(prev) => self.builder.ins().fadd(prev, sq),
            });
        }
        let len_sq = acc.expect("normalize empty");
        let zero = self.builder.ins().f32const(Ieee32::with_float(0.0));
        let is_zero = self.builder.ins().fcmp(FloatCC::Equal, len_sq, zero);
        let len = self.builder.ins().sqrt(len_sq);
        let mut out = Vec::new();
        for lane in v {
            let n = self.builder.ins().fdiv(lane, len);
            out.push(self.builder.ins().select(is_zero, zero, n));
        }
        self.def_temp(dst, &out)?;
        Ok(false)
    }

    fn read_axis(&mut self, instr: &SsaInstr, axis: usize) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let v = self.use_temp(src1(instr)?)?;
        let lane = *v
            .get(axis)
            .ok_or_else(|| JitError::UnsupportedIr(format!("axis {axis} oob")))?;
        self.def_temp(dst, &[lane])?;
        Ok(false)
    }

    fn store_vec_from_scalar(&mut self, instr: &SsaInstr) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let width = self.temp(dst)?.ty.width();
        if instr.src.len() != width {
            return Err(JitError::UnsupportedIr(format!(
                "store_vec_from_scalar expected {width} scalars"
            )));
        }
        let mut out = Vec::new();
        for src in &instr.src {
            out.push(scalar(self.use_temp(*src)?)?);
        }
        self.def_temp(dst, &out)?;
        Ok(false)
    }

    fn tt_texture(&mut self, instr: &SsaInstr) -> Result<bool, JitError> {
        let dst = dst_of(instr)?;
        let idx = scalar(self.use_temp(src_at(instr, 0)?)?)?;
        let uv = self.use_temp(src_at(instr, 1)?)?;
        if uv.len() != 2 {
            return Err(JitError::UnsupportedIr("tt_texture uv must be V2".into()));
        }
        let slot = self.builder.create_sized_stack_slot(StackSlotData::new(
            StackSlotKind::ExplicitSlot,
            16,
            2,
        ));
        let ptr = self.builder.ins().stack_addr(self.ptr_ty, slot, 0);
        let tex = self.tex()?;
        self.builder
            .ins()
            .call(self.libcalls.sample, &[tex, idx, uv[0], uv[1], ptr]);
        let x = self.builder.ins().load(types::F32, mem_flags(), ptr, 0);
        let y = self.builder.ins().load(types::F32, mem_flags(), ptr, 4);
        let z = self.builder.ins().load(types::F32, mem_flags(), ptr, 8);
        let w = self.builder.ins().load(types::F32, mem_flags(), ptr, 12);
        self.def_temp(dst, &[x, y, z, w])?;
        Ok(false)
    }

    fn const_values(&mut self, c: &SsaConst) -> Result<Vec<Value>, JitError> {
        match c.ty {
            IrTy::Bool => {
                let bit = if c.value.first().copied().unwrap_or(0.0) != 0.0 {
                    1
                } else {
                    0
                };
                Ok(vec![self.builder.ins().iconst(types::I8, bit)])
            }
            IrTy::I32 => {
                let n = c.value.first().copied().unwrap_or(0.0) as i64;
                Ok(vec![self.builder.ins().iconst(types::I32, n)])
            }
            IrTy::F32 | IrTy::V2 | IrTy::V3 | IrTy::V4 => {
                let width = c.ty.width();
                if c.value.len() != width {
                    return Err(JitError::Ir(format!(
                        "const {} expected {width} lanes, got {}",
                        c.id,
                        c.value.len()
                    )));
                }
                let mut out = Vec::with_capacity(width);
                for n in &c.value {
                    let v = self.builder.ins().f32const(Ieee32::with_float(*n as f32));
                    out.push(v);
                }
                Ok(out)
            }
        }
    }
}

#[derive(Clone, Copy, Debug)]
enum BinKind {
    Add,
    Sub,
    Mul,
    Div,
}

fn mem_flags() -> cranelift_codegen::ir::MemFlagsData {
    cranelift_codegen::ir::MemFlagsData::trusted()
}

fn dst_of(instr: &SsaInstr) -> Result<u32, JitError> {
    instr
        .dst
        .ok_or_else(|| JitError::UnsupportedIr(format!("{} missing dst", instr.op)))
}

fn src1(instr: &SsaInstr) -> Result<u32, JitError> {
    src_at(instr, 0)
}

fn src_at(instr: &SsaInstr, i: usize) -> Result<u32, JitError> {
    instr
        .src
        .get(i)
        .copied()
        .ok_or_else(|| JitError::UnsupportedIr(format!("{} missing src {i}", instr.op)))
}

fn scalar(vals: Vec<Value>) -> Result<Value, JitError> {
    if vals.len() != 1 {
        return Err(JitError::Ir(format!(
            "expected scalar, got {} lanes",
            vals.len()
        )));
    }
    Ok(vals[0])
}

fn vec4(vals: Vec<Value>) -> Result<[Value; 4], JitError> {
    if vals.len() != 4 {
        return Err(JitError::Ir(format!(
            "expected V4, got {} lanes",
            vals.len()
        )));
    }
    Ok([vals[0], vals[1], vals[2], vals[3]])
}

fn broadcast(vals: Vec<Value>, width: usize) -> Result<Vec<Value>, JitError> {
    if vals.len() == width {
        return Ok(vals);
    }
    if vals.len() == 1 && width > 1 {
        return Ok(vec![vals[0]; width]);
    }
    Err(JitError::Ir(format!(
        "cannot broadcast {} lanes to {width}",
        vals.len()
    )))
}

fn load_from_regs(builder: &mut FunctionBuilder, regs: Value, ty: IrTy, idx: u8) -> Vec<Value> {
    match ty {
        IrTy::Bool => vec![mem::load_bool(builder, regs, idx)],
        IrTy::I32 => vec![mem::load_i32(builder, regs, idx)],
        IrTy::F32 => vec![mem::load_f32(builder, regs, idx)],
        IrTy::V2 => vec![
            mem::load_v2(builder, regs, idx, 0),
            mem::load_v2(builder, regs, idx, 1),
        ],
        IrTy::V3 => vec![
            mem::load_v3(builder, regs, idx, 0),
            mem::load_v3(builder, regs, idx, 1),
            mem::load_v3(builder, regs, idx, 2),
        ],
        IrTy::V4 => vec![
            mem::load_v4(builder, regs, idx, 0),
            mem::load_v4(builder, regs, idx, 1),
            mem::load_v4(builder, regs, idx, 2),
            mem::load_v4(builder, regs, idx, 3),
        ],
    }
}
