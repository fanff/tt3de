use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn min_with_array(a: u16, b: u16, c: u16) -> u16 {
    [a, b, c].iter().copied().min().unwrap()
}

fn min_with_cmp(a: u16, b: u16, c: u16) -> u16 {
    std::cmp::min(std::cmp::min(a, b), c)
}

pub fn bench_min(c: &mut Criterion) {
    let a: u16 = 10;
    let bval: u16 = 20;
    let c_val: u16 = 5;

    c.bench_function("min_with_array", |b| {
        b.iter(|| min_with_array(black_box(a), black_box(bval), black_box(c_val)))
    });

    c.bench_function("min_with_cmp", |b| {
        b.iter(|| min_with_cmp(black_box(a), black_box(bval), black_box(c_val)))
    });
}

criterion_group!(benches, bench_min);
criterion_main!(benches);
