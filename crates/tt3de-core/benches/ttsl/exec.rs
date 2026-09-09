//! Times the Cranelift-lowered TTSL path on demo shaders.
//!
//! Fixtures are compiled by `scripts/gen_ttsl_bench_fixtures.py` into
//! `ttsl/ssa/*.json` (post-SSA CFG) plus register seeds in `ttsl/fixtures.rs`.

use criterion::{Criterion, Throughput};
use nalgebra_glm::{Vec2, Vec3, Vec4};
use std::hint::black_box;

use tt3de_core::material::shader_material::ShaderSeedRegisters;
use tt3de_core::ttsl::jit::{compile_ttsl_json, CompiledShader};
use tt3de_core::ttsl::{Registers, TtslTextureEnv};

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

fn call_jit(
    compiled: &CompiledShader,
    regs: &mut Registers,
    tex: Option<&dyn TtslTextureEnv>,
) -> (Vec4, Vec4, i32) {
    compiled.run(regs, tex)
}

pub fn bench_ttsl_exec(c: &mut Criterion) {
    for fixture in FIXTURES {
        let seed = seed_registers(fixture);
        let tex = texture_env(fixture);
        let compiled =
            compile_ttsl_json(fixture.ssa_json).expect("cranelift IR compile should succeed");

        let mut group = c.benchmark_group(format!("ttsl_exec/{}", fixture.name));
        group.throughput(Throughput::Elements(1));

        let mut jit_regs = seed.clone_registers();
        group.bench_function("jit", |b| {
            b.iter(|| black_box(call_jit(&compiled, &mut jit_regs, tex)))
        });

        let mut jit_cell_regs = Registers::new();
        group.bench_function("jit_cell", |b| {
            b.iter(|| {
                seed.copy_seed_into(&mut jit_cell_regs);
                black_box(call_jit(&compiled, &mut jit_cell_regs, tex))
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
        group.bench_function(fixture.name, |b| {
            b.iter(|| {
                black_box(
                    compile_ttsl_json(black_box(fixture.ssa_json)).expect("compile should succeed"),
                )
            })
        });
    }
    group.finish();
}
