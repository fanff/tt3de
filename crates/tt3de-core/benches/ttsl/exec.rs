//! Compares the TTSL interpreter loop against the Cranelift compile path.
//!
//! Fixtures are demo shaders compiled to bytecode by
//! `scripts/gen_ttsl_bench_fixtures.py` into `ttsl/fixtures.rs`.
//!
//! While `jit::LOWERS_BYTECODE` is `false`, `compile_ttsl` emits a dummy
//! function instead of lowering opcodes, so its arm measures the native call
//! floor rather than shader execution and output equivalence is not asserted.

use criterion::{Criterion, Throughput};
use nalgebra_glm::{Vec2, Vec3, Vec4};
use std::hint::black_box;

use tt3de_core::material::shader_material::ShaderSeedRegisters;
use tt3de_core::ttsl::jit::{self, compile_ttsl, CompiledShader};
use tt3de_core::ttsl::{decode_instrs_256, run_ttsl, Instr, Registers, TtslTextureEnv};

use super::fixtures::{TtslBenchFixture, FIXTURES};

/// Constant stand-in for a sampled texture, so `tt_texture` fixtures run
/// without dragging a real texture buffer into the measurement.
struct ConstTextureEnv;

impl TtslTextureEnv for ConstTextureEnv {
    fn sample_tt_texture(&self, _idx: i32, uv: Vec2) -> Vec4 {
        Vec4::new(uv.x, uv.y, 0.5, 1.0)
    }
}

static CONST_TEXTURE_ENV: ConstTextureEnv = ConstTextureEnv;

fn seed_registers(fixture: &TtslBenchFixture) -> ShaderSeedRegisters {
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
    ShaderSeedRegisters::from_registers(regs)
}

fn texture_env(fixture: &TtslBenchFixture) -> Option<&'static dyn TtslTextureEnv> {
    if fixture.needs_texture_env {
        Some(&CONST_TEXTURE_ENV)
    } else {
        None
    }
}

/// Runs the compiled function the way a shading pass would: registers in, glyph out.
fn call_jit(compiled: &CompiledShader, regs: &mut Registers) -> i32 {
    unsafe { (compiled.as_fn())(regs as *mut Registers) }
}

/// Fails loudly if a lowered JIT ever disagrees with the interpreter.
///
/// Only the glyph is compared: `ShaderFn` returns `i32`, so the two `Vec4`
/// colors `run_ttsl` yields have no place in the current ABI. Extend this once
/// lowering settles how the front and back colors leave the compiled function.
fn check_equivalence(
    fixture: &TtslBenchFixture,
    instrs: &[Instr; 256],
    seed: &ShaderSeedRegisters,
    compiled: &CompiledShader,
) {
    if !jit::LOWERS_BYTECODE {
        return;
    }
    let mut interp_regs = seed.clone_registers();
    let (_front, _back, glyph) = run_ttsl(instrs, &mut interp_regs, texture_env(fixture));

    let mut jit_regs = seed.clone_registers();
    let jit_glyph = call_jit(compiled, &mut jit_regs);

    assert_eq!(
        glyph, jit_glyph,
        "{}: JIT glyph output diverged from the interpreter",
        fixture.name
    );
}

pub fn bench_ttsl_exec(c: &mut Criterion) {
    // `jit_stub_floor` is not comparable to the interpreter arms until opcode
    // lowering lands; it only bounds how cheap a native call could ever be.
    let jit_arm = if jit::LOWERS_BYTECODE {
        "jit"
    } else {
        "jit_stub_floor"
    };

    for fixture in FIXTURES {
        let instrs = decode_instrs_256(fixture.bytecode);
        let seed = seed_registers(fixture);
        let tex = texture_env(fixture);
        let compiled = compile_ttsl(&instrs).expect("cranelift compile should succeed");
        check_equivalence(fixture, &instrs, &seed, &compiled);

        let mut group = c.benchmark_group(format!("ttsl_exec/{}", fixture.name));
        group.throughput(Throughput::Elements(1));

        // Dispatch cost alone: registers stay seeded across iterations.
        let mut regs = seed.clone_registers();
        group.bench_function("interp_vm", |b| {
            b.iter(|| black_box(run_ttsl(black_box(&instrs), &mut regs, tex)))
        });

        // What a rendered cell actually costs: `ShaderMaterial` restores the
        // seed banks before every pixel, and that copy is not free.
        let mut cell_regs = Registers::new();
        group.bench_function("interp_cell", |b| {
            b.iter(|| {
                seed.copy_seed_into(&mut cell_regs);
                black_box(run_ttsl(black_box(&instrs), &mut cell_regs, tex))
            })
        });

        let mut jit_regs = seed.clone_registers();
        group.bench_function(jit_arm, |b| {
            b.iter(|| black_box(call_jit(&compiled, &mut jit_regs)))
        });

        let mut jit_cell_regs = Registers::new();
        group.bench_function(format!("{jit_arm}_cell"), |b| {
            b.iter(|| {
                seed.copy_seed_into(&mut jit_cell_regs);
                black_box(call_jit(&compiled, &mut jit_cell_regs))
            })
        });

        group.finish();
    }
}

/// Compilation is per material, execution is per cell, so this is what decides
/// how many shaded cells a JIT needs before it pays for itself.
pub fn bench_ttsl_compile(c: &mut Criterion) {
    let mut group = c.benchmark_group("ttsl_compile");
    for fixture in FIXTURES {
        let instrs = decode_instrs_256(fixture.bytecode);
        group.bench_function(fixture.name, |b| {
            b.iter(|| {
                black_box(compile_ttsl(black_box(&instrs)).expect("compile should succeed"))
            })
        });
    }
    group.finish();
}
