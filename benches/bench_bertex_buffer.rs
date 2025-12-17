use criterion::{criterion_group, criterion_main, Criterion};
use nalgebra_glm::{Mat4, Vec3, Vec4};
use std::hint::black_box;
use tt3de::vertexbuffer::vertex_buffer::VertexBuffer;
// --- tiny helpers for the benchmark ---

fn make_test_mats() -> (Mat4, Mat4, Mat4) {
    // Pick non-trivial transforms so LLVM can't fold everything away.
    // Adjust for your math lib if needed.
    let model = Mat4::new_scaling(10.5);
    let view = Mat4::new_translation(&Vec3::new(0.1, -0.2, 0.3));
    let proj = Mat4::new_perspective(60_f32.to_radians(), 16.0 / 9.0, 0.1, 1000.0);
    (model, view, proj)
}

fn fill_buffer(buf: &mut VertexBuffer<Vec4>, n: usize) {
    // Deterministic data; avoid RNG cost in the hot path.
    for i in 0..n {
        let f = i as f32;
        let v = Vec4::new(
            f * 0.001 + 1.0,
            (f % 97.0) * 0.01,
            1.0 + (f % 13.0) * 0.001,
            1.0,
        );
        buf.add_vertex(&v);
    }
}

/// Returns seconds per call of `apply_mvp` over the full range.
fn bench_apply_once(buf: &mut VertexBuffer<Vec4>, mvp: (&Mat4, &Mat4, &Mat4)) {
    // Black-box the inputs to avoid constant-folding.
    buf.apply_mvp(mvp.0, mvp.1, mvp.2, 0, buf.len());
    // Consume a couple of outputs per rep.
    let idx = (buf.len().saturating_sub(1)).min(3);
    black_box({
        buf.get_calculated(idx).y;
    });
}

pub fn bench_mvp(c: &mut Criterion) {
    let cases = [10usize, 1_000, 100_000];
    let mut group = c.benchmark_group("vertex_buffer4_apply_mvp");
    for n in cases {
        let bench_id = format!("apply_mvp_vec4_n{}", n);
        let (model, view, proj) = make_test_mats();

        let mut buf = VertexBuffer::<Vec4>::with_capacity(n);
        fill_buffer(&mut buf, n);
        group.throughput(criterion::Throughput::Elements(n as u64));
        group.bench_function(&bench_id, |b| {
            b.iter(|| {
                bench_apply_once(black_box(&mut buf), black_box((&model, &view, &proj)));
            })
        });
    }
    group.finish();
}

criterion_group!(benches, bench_mvp);
criterion_main!(benches);
