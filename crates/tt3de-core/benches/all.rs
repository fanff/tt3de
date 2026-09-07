use crate::bench_bertex_buffer::bench_mvp;
use criterion::{criterion_group, criterion_main, Criterion};
pub mod color_bench;
use color_bench::{bench_blend_f32, bench_blend_i16, bench_blend_u8};

pub mod bench_bertex_buffer;
pub mod min_bench;
pub mod ttsl;
use ttsl::exec::{bench_ttsl_compile, bench_ttsl_exec};

fn all_benchs(c: &mut Criterion) {
    bench_mvp(c);
    bench_blend_u8(c);
    bench_blend_i16(c);
    bench_blend_f32(c);
    bench_ttsl_exec(c);
    bench_ttsl_compile(c);
}

criterion_group!(benches, all_benchs);
criterion_main!(benches);
