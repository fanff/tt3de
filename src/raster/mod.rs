use std::{
    borrow::BorrowMut,
    ops::{Mul, Sub},
};

use nalgebra_glm::{normalize, Number, Real, TVec3, Vec3};
use primitivbuffer::{PointInfo, PrimitivReferences, PrimitiveBuffer, PrimitiveElements};
use pyo3::{pyfunction, IntoPy, Py, PyAny, PyRefMut, Python};

use crate::{
    drawbuffer::{drawbuffer::DrawBuffer, AbigDrawing},
    primitivbuffer::*,
};

//  calculating min/max of multiple values;
fn min_3_int<T: Ord>(a: T, b: T, c: T) -> T {
    std::cmp::min(std::cmp::min(a, b), c)
}
fn max_3_int<T: Ord>(a: T, b: T, c: T) -> T {
    std::cmp::max(std::cmp::max(a, b), c)
}

fn min_2_int<T: Ord>(a: T, b: T) -> T {
    std::cmp::min(a, b)
}
fn max_2_int<T: Ord>(a: T, b: T) -> T {
    std::cmp::max(a, b)
}

// function that "set stuff" in the drawing buffer; assuming its a double raster
fn set_pixel_double_weights<DEPTHACC: Real, const DEPTHCOUNT: usize>(
    prim_ref: &PrimitivReferences,
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, DEPTHACC>,
    depth: DEPTHACC,
    px: usize,
    py: usize,
    w0: DEPTHACC,
    w1: DEPTHACC,
    w2: DEPTHACC,
    w0_alt: DEPTHACC,
    w1_alt: DEPTHACC,
    w2_alt: DEPTHACC,
) {
    let w = TVec3::new(w0, w1, w2);
    let w_alt = TVec3::new(w0_alt, w1_alt, w2_alt);
    drawing_buffer.set_depth_content(
        py,
        px,
        depth,
        normalize(&w),
        normalize(&w_alt),
        prim_ref.node_id,
        prim_ref.geometry_id,
        prim_ref.material_id,
        prim_ref.primitive_id,
    );
}

trait ToF32 {
    fn to_f32(&self) -> f32;
}

impl ToF32 for usize {
    fn to_f32(&self) -> f32 {
        *self as f32
    }
}

impl ToF32 for u16 {
    fn to_f32(&self) -> f32 {
        *self as f32
    }
}

impl ToF32 for u32 {
    fn to_f32(&self) -> f32 {
        *self as f32
    }
}

fn barycentric_coord(
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
    pc: &PointInfo<f32>,
    row: usize,
    col: usize,
) -> (f32, f32, f32) {
    let x1 = pa.col as f32;
    let y1 = pa.row as f32;
    let x2 = pb.col as f32;
    let y2 = pb.row as f32;
    let x3 = pc.col as f32;
    let y3 = pc.row as f32;
    let px = col as f32;
    let py = row as f32;

    let denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3);
    let w1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom;
    let w2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom;
    let w3 = 1.0 - w1 - w2;

    (w1, w2, w3)
}
fn barycentric_coord_shift(
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
    pc: &PointInfo<f32>,
    lower_shift: f32,
    row: usize,
    col: usize,
) -> (f32, f32, f32) {
    let x1 = pa.col as f32;
    let y1 = pa.row as f32;
    let x2 = pb.col as f32;
    let y2 = pb.row as f32;
    let x3 = pc.col as f32;
    let y3 = pc.row as f32;
    let px = col as f32;
    let py = (row as f32) + lower_shift;

    let denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3);
    let w1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom;
    let w2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom;
    let w3 = 1.0 - w1 - w2;

    (w1, w2, w3)
}
fn orient2di<T: Number>(ax: T, ay: T, bx: T, by: T, cx: T, cy: T) -> T {
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax);
}
fn orient2dr<T: Real>(ax: T, ay: T, bx: T, by: T, cx: T, cy: T) -> T {
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax);
}

fn raster_triangle<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
    pc: &PointInfo<f32>,
) {
    if (pa.row == pb.row) && (pa.row == pc.row) {
        return;
    }
    if (pa.col == pb.col) && (pa.col == pc.col) {
        return;
    }

    let mut minX = min_3_int(pa.col, pb.col, pc.col); // min3int(axi, bxi, cxi);
    let mut maxX = max_3_int(pa.col, pb.col, pc.col); // min3int(ayi, byi, cyi);

    let mut minY = min_3_int(pa.row, pb.row, pc.row); // max3int(axi, bxi, cxi);
    let mut maxY = max_3_int(pa.row, pb.row, pc.row); // max3int(ayi, byi, cyi);

    // Clip against screen bounds
    // useless in usize space :)
    // minX = max_2_int(minX, 0);
    // minY = max_2_int(minY, 0);

    maxX = min_2_int(maxX, drawing_buffer.col_count);
    maxY = min_2_int(maxY, drawing_buffer.row_count);

    for py in minY..maxY {
        for px in minX..maxX {
            let (w0, w1, w2) = barycentric_coord(pa, pb, pc, py, px);

            if w0 >= 0.0 && w1 >= 0.0 && w2 >= 0.0 {
                let (w0_alt, w1_alt, w2_alt) = barycentric_coord_shift(pa, pb, pc, 0.49, py, px);

                let depth = pa.depth * w0 + pb.depth * w1 + pc.depth * w2;

                set_pixel_double_weights(
                    prim_ref,
                    drawing_buffer,
                    depth,
                    px,
                    py,
                    w0,
                    w1,
                    w2,
                    w0_alt,
                    w1_alt,
                    w2_alt,
                )
            }
        }
    }
}

pub fn raster_element<const UVCONT: usize, const DEPTHCOUNT: usize>(
    element: &PrimitiveElements<UVCONT, f32, f32>,
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
) {
    match element {
        PrimitiveElements::Line { fds, pa, pb, uv } => {}
        PrimitiveElements::Point {
            fds,
            row,
            col,
            depth,
            uv,
        } => todo!(),
        PrimitiveElements::Triangle {
            fds,
            pa,
            pb,
            pc,
            uv,
        } => {
            raster_triangle(drawing_buffer, fds, pa, pb, pc);
        }
        PrimitiveElements::Static { fds, index } => todo!(),
    }
}

pub fn raster_all<const UVCONT: usize, const DEPTHCOUNT: usize>(
    primitivbuffer: &PrimitiveBuffer<UVCONT, f32>,
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
) {
    for primitiv_idx in 0..primitivbuffer.current_size {
        let element = primitivbuffer.content[primitiv_idx];

        raster_element(&element, drawing_buffer)
    }
}

#[pyfunction]
pub fn raster_all_py(py: Python, pb: &PrimitiveBufferPy, mut db: PyRefMut<'_, AbigDrawing>) {
    let primitivbuffer = &pb.content;

    let drawing_buffer = &mut db.db;
    raster_all(primitivbuffer, drawing_buffer);
}
