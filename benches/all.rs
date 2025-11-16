use crate::bench_bertex_buffer::bench_mvp;
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

pub mod bench_bertex_buffer;
pub mod min_bench;
fn all_benchs(c: &mut Criterion) {
    bench_mvp(c);
}
criterion_group!(benches, all_benchs);
criterion_main!(benches);
