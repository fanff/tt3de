use std::hint::black_box;

use criterion::{criterion_group, criterion_main, Criterion};
use nalgebra_glm::{TVec4, Vec4};

// Integer path: TVec4<i16>
fn blend_i16(src: TVec4<i16>, dst: TVec4<i16>) -> TVec4<i16> {
    // src.a is alpha in 0..=255
    let a = src.w as i32;
    let ia = 255 - a;

    let r = (src.x as i32 * a + dst.x as i32 * ia) / 255;
    let g = (src.y as i32 * a + dst.y as i32 * ia) / 255;
    let b = (src.z as i32 * a + dst.z as i32 * ia) / 255;
    let a_out = 255; // or keep dst/ src etc. depending on your model

    TVec4::new(r as i16, g as i16, b as i16, a_out)
}

// Float path: TVec4<f32>
fn blend_f32(src: &Vec4, dst: &Vec4) -> TVec4<f32> {
    //let a = src.w; // 0.0..=1.0
    //let mut rgb = src.lerp(&dst, a);
    //rgb.w = 1.0;
    //rgb

    // src.a is alpha in 0..=255
    let a = src.w;
    let ia = 1.0 - a;

    let r = (src.x * a + dst.x * ia);
    let g = (src.y * a + dst.y * ia);
    let b = (src.z * a + dst.z * ia);
    let a_out = 1.0; // or keep dst/ src etc. depending on your model

    TVec4::new(r, g, b, a_out)
}

// Float path: TVec4<f32>
fn blend_u8(src: TVec4<u8>, dst: TVec4<u8>) -> TVec4<u8> {
    let a = src.w as f32 / 255.0; // 0.0..=1.0
    let ia = 1.0 - a;

    let cr = (src.x as f32 * a + dst.x as f32 * ia);
    let cg = (src.y as f32 * a + dst.y as f32 * ia);
    let cb = (src.z as f32 * a + dst.z as f32 * ia);
    let a_out = 255; // or src.w/other

    TVec4::new(cr as u8, cg as u8, cb as u8, a_out)
}

fn make_test_data_u8(len: usize) -> (Vec<[u8; 4]>, Vec<[u8; 4]>) {
    let mut src = Vec::with_capacity(len);
    let mut dst = Vec::with_capacity(len);

    // Simple deterministic pattern (no RNG needed)
    for i in 0..len {
        let v = (i * 73 % 256) as u8;
        let w = (255 - v) as u8;
        src.push([v, (v / 2), (v / 3), 128]); // 50% alpha
        dst.push([w, (w / 2), (w / 3), 255]); // opaque
    }

    (src, dst)
}

pub fn bench_blend_u8(c: &mut Criterion) {
    let len = 4096;
    let (src_raw, dst_raw) = make_test_data_u8(len);
    // Convert to TVec4<u8> once, outside the hot loop
    let src: Vec<TVec4<u8>> = src_raw
        .iter()
        .map(|&p| TVec4::new(p[0], p[1], p[2], p[3]))
        .collect();
    let dst: Vec<TVec4<u8>> = dst_raw
        .iter()
        .map(|&p| TVec4::new(p[0], p[1], p[2], p[3]))
        .collect();

    c.bench_function("blend_u8", |b| {
        b.iter(|| {
            let mut acc = TVec4::new(0u8, 0, 0, 0);
            for i in 0..len {
                // black_box so compiler can’t optimize everything away
                acc = blend_u8(black_box(src[i]), black_box(dst[i]));
            }
            black_box(acc);
        });
    });
}
pub fn bench_blend_i16(c: &mut Criterion) {
    let len = 4096;
    let (src_raw, dst_raw) = make_test_data_u8(len);

    // Convert to TVec4<i16> once, outside the hot loop
    let src: Vec<TVec4<i16>> = src_raw
        .iter()
        .map(|&p| TVec4::new(p[0] as i16, p[1] as i16, p[2] as i16, p[3] as i16))
        .collect();
    let dst: Vec<TVec4<i16>> = dst_raw
        .iter()
        .map(|&p| TVec4::new(p[0] as i16, p[1] as i16, p[2] as i16, p[3] as i16))
        .collect();

    c.bench_function("blend_i16", |b| {
        b.iter(|| {
            let mut acc = TVec4::new(0i16, 0, 0, 0);
            for i in 0..len {
                // black_box so compiler can’t optimize everything away
                acc = blend_i16(black_box(src[i]), black_box(dst[i]));
            }
            black_box(acc);
        });
    });
}

pub fn bench_blend_f32(c: &mut Criterion) {
    let len = 4096;
    let (src_raw, dst_raw) = make_test_data_u8(len);

    // Convert to TVec4<f32> once, outside the hot loop
    let src: Vec<TVec4<f32>> = src_raw
        .iter()
        .map(|&p| {
            TVec4::new(
                p[0] as f32 / 255.0,
                p[1] as f32 / 255.0,
                p[2] as f32 / 255.0,
                p[3] as f32 / 255.0,
            )
        })
        .collect();
    let dst: Vec<TVec4<f32>> = dst_raw
        .iter()
        .map(|&p| {
            TVec4::new(
                p[0] as f32 / 255.0,
                p[1] as f32 / 255.0,
                p[2] as f32 / 255.0,
                p[3] as f32 / 255.0,
            )
        })
        .collect();

    c.bench_function("blend_f32", |b| {
        b.iter(|| {
            let mut acc = TVec4::new(0.0f32, 0.0, 0.0, 0.0);
            for i in 0..len {
                acc = blend_f32(black_box(&src[i]), black_box(&dst[i]));
            }
            black_box(acc);
        });
    });
}

criterion_group!(benches, bench_blend_u8, bench_blend_i16, bench_blend_f32);
criterion_main!(benches);
