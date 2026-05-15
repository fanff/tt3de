use nalgebra_glm::{RealNumber, TVec2, Vec2, Vec3, Vec4};
use primitivbuffer::{PointInfo, PrimitivReferences, PrimitiveBuffer, PrimitiveElements};
use pyo3::{pyfunction, PyRefMut, Python};

use crate::{
    drawbuffer::{drawbuffer::DrawBuffer, DrawingBufferPy},
    primitivbuffer::*,
    vertexbuffer::{vertex_buffer::VertexBuffer, vertex_buffer_py::VertexBufferPy},
};

pub mod raster_line;
use raster_line::*;

pub mod raster_point;
use raster_point::*;

pub mod raster_rect;
use raster_rect::*;
pub mod raster_triangle_tomato;
use raster_triangle_tomato::*;

pub mod vertex;
use vertex::*;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PassTag {
    Opaque,
    Transparent,
}

fn primitive_matches_pass(element: &PrimitiveElements, pass: Option<PassTag>) -> bool {
    let is_transparent = match element {
        PrimitiveElements::Line { fds, .. } => fds.transparent,
        PrimitiveElements::Point { fds, .. } => fds.transparent,
        PrimitiveElements::Static { fds, .. } => fds.transparent,
        PrimitiveElements::Triangle3D(t) => t.primitive_reference.transparent,
        PrimitiveElements::Rect(r) => r.primitive_reference.transparent,
    };
    match pass {
        None => true,
        Some(PassTag::Opaque) => !is_transparent,
        Some(PassTag::Transparent) => is_transparent,
    }
}

// function that "set stuff" in the drawing buffer; assuming its a double raster
fn set_pixel_double_weights<DEPTHACC: RealNumber, const DEPTHCOUNT: usize>(
    prim_ref: &PrimitivReferences,
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, DEPTHACC>,
    depth: DEPTHACC,
    normal: Vec3,
    col: usize,
    row: usize,
    u0: f32,
    v0: f32,
    u1: f32,
    v1: f32,
    point_coord: Vec2,
) {
    let w = TVec2::new(u0, v0);
    let w_alt = TVec2::new(u1, v1);
    drawing_buffer.set_depth_content(
        row,
        col,
        depth,
        normal,
        Vec3::zeros(),
        w,
        w_alt,
        prim_ref.node_id,
        prim_ref.geometry_id,
        prim_ref.material_id,
        prim_ref.primitive_id,
        true,
        0.0,
        point_coord,
    );
}

#[allow(dead_code)]
fn barycentric_coord(
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
    pc: &PointInfo<f32>,
    row: usize,
    col: usize,
) -> (f32, f32, f32) {
    let pa_col = pa.p.y;
    let pa_row = pa.p.x;
    let pb_col = pb.p.y;
    let pb_row = pb.p.x;
    let x3 = pc.p.y;
    let y3 = pc.p.x;
    let p_col = col as f32;
    let p_row = row as f32;

    // calculate the bar
    let denom = (pb_row - y3) * (pa_col - x3) + (x3 - pb_col) * (pa_row - y3);
    let w1 = ((pb_row - y3) * (p_col - x3) + (x3 - pb_col) * (p_row - y3)) / denom;
    let w2 = ((y3 - pa_row) * (p_col - x3) + (pa_col - x3) * (p_row - y3)) / denom;

    // that way of doing the calculation might be more stable on the edges
    let w3 = 1.0 - w1 - w2;
    //let w3 = ((pa_row - pb_row) * (p_col - pa_col) + (pb_col - pa_col) * (p_row - pa_row)) / denom;

    (w1, w2, w3)
}
#[allow(dead_code)]
fn barycentric_coord_shift(
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
    pc: &PointInfo<f32>,
    lower_shift: f32,
    row: usize,
    col: usize,
) -> (f32, f32, f32) {
    let x1 = pa.p.y;
    let y1 = pa.p.x;
    let x2 = pb.p.y;
    let y2 = pb.p.x;
    let x3 = pc.p.y;
    let y3 = pc.p.x;
    let px = col as f32;
    let py = (row as f32) + lower_shift;

    let denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3);
    let w1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom;
    let w2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom;
    let w3 = 1.0 - w1 - w2;

    (w1, w2, w3)
}

pub fn raster_element<const DEPTHCOUNT: usize>(
    element: &PrimitiveElements,
    _vertexbuffer: &VertexBuffer<Vec4>,
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
) {
    match element {
        PrimitiveElements::Line { fds, pa, pb } => {
            raster_line(drawing_buffer, fds, pa, pb);
        }
        PrimitiveElements::Point { fds, point, uv: _ } => {
            raster_point_info(drawing_buffer, fds, point);
        }
        PrimitiveElements::Triangle3D(t) => {
            // raster_triangle(drawing_buffer, &t.primitive_reference, &t.pa, &t.pb, &t.pc);
            tomato_draw_triangle(drawing_buffer, &t.primitive_reference, &t.pa, &t.pb, &t.pc)
        }
        PrimitiveElements::Rect(rect) => {
            raster_prect(drawing_buffer, &rect);
        }

        PrimitiveElements::Static { fds: _, index: _ } => todo!(),
    }
}

pub fn raster_all<const DEPTHCOUNT: usize>(
    primitivbuffer: &PrimitiveBuffer,
    vertexbuffer: &VertexBuffer<Vec4>,
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    pass_filter: Option<PassTag>,
) {
    for primitiv_idx in 0..primitivbuffer.current_size {
        let element = primitivbuffer.content[primitiv_idx];
        if primitive_matches_pass(&element, pass_filter) {
            raster_element(&element, vertexbuffer, drawing_buffer)
        }
    }
}

#[pyfunction]
#[pyo3(signature = (pb, vbuffpy, db, pass_filter=None))]
pub fn raster_all_py(
    _py: Python,
    pb: &PrimitiveBufferPy,
    vbuffpy: &VertexBufferPy,
    mut db: PyRefMut<'_, DrawingBufferPy>,
    pass_filter: Option<&str>,
) {
    let primitivbuffer = &pb.content;

    let pass = match pass_filter {
        Some("opaque") => Some(PassTag::Opaque),
        Some("transparent") => Some(PassTag::Transparent),
        _ => None,
    };
    match pass {
        Some(PassTag::Transparent) => {
            raster_all(
                primitivbuffer,
                &vbuffpy.buffer3d,
                &mut db.transparent_db,
                Some(PassTag::Transparent),
            );
        }
        _ => {
            raster_all(
                primitivbuffer,
                &vbuffpy.buffer3d,
                &mut db.opaque_db,
                Some(PassTag::Opaque),
            );
        }
    }
}
