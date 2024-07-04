use std::{
    borrow::BorrowMut,
    ops::{Mul, Sub},
};

use nalgebra_glm::{normalize, Number, Real, TVec3, Vec3, Vec4};
use primitivbuffer::{PointInfo, PrimitivReferences, PrimitiveBuffer, PrimitiveElements};
use pyo3::{pyfunction, IntoPy, Py, PyAny, PyRefMut, Python};

use crate::{
    drawbuffer::{self, drawbuffer::DrawBuffer, AbigDrawing},
    geombuffer::{GeometryBuffer, GeometryBufferPy, Polygon},
    material::{apply_material, MaterialBufferPy},
    primitivbuffer::*,
    texturebuffer::{self, TextureBufferPy},
    vertexbuffer::{VertexBuffer, VertexBufferPy},
};

fn ndc_to_screen(
    v: &Vec4,
    width: usize,
    height: usize,
    x_origin: usize,
    y_origin: usize,
) -> (usize, usize) {
    let xscreen = (width as f32 / 2.0 * (v.x + 1.0) + x_origin as f32).round() as usize;
    let yscreen = (height as f32 / 2.0 * (v.y + 1.0) + y_origin as f32).round() as usize;

    (yscreen, xscreen)
}

fn poly_as_primitive<const C: usize, const PIXCOUNT: usize, DEPTHACC: Number>(
    p: &Polygon,
    geometry_id: usize,
    vertex_buffer: &VertexBuffer<C>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer<f32>,
) {
    let va = vertex_buffer.get_at(p.p_start);
    let point_a = ndc_to_screen(va, drawbuffer.col_count, drawbuffer.row_count, 0, 0);

    let mut vb = vertex_buffer.get_at(p.p_start + 1);
    let mut point_b = ndc_to_screen(vb, drawbuffer.col_count, drawbuffer.row_count, 0, 0);
    let mut vc = vertex_buffer.get_at(p.p_start + 2);
    let mut point_c = ndc_to_screen(vc, drawbuffer.col_count, drawbuffer.row_count, 0, 0);

    primitivbuffer.add_triangle(
        p.geom_ref.node_id,
        geometry_id,
        p.geom_ref.material_id,
        point_a.0,
        point_a.1,
        va.z,
        point_b.0,
        point_b.1,
        vb.z,
        point_c.0,
        point_c.1,
        vc.z,
        p.uv_start,
    );

    let mut current_triangle: usize = 1;
    while current_triangle < p.p_end - p.p_start - 3 {
        vb = vc;
        point_b = point_c;

        vc = vertex_buffer.get_at(p.p_start + 2 + current_triangle);
        point_c = ndc_to_screen(vc, drawbuffer.col_count, drawbuffer.row_count, 0, 0);

        primitivbuffer.add_triangle(
            p.geom_ref.node_id,
            geometry_id,
            p.geom_ref.material_id,
            point_a.0,
            point_a.1,
            va.z,
            point_b.0,
            point_b.1,
            vb.z,
            point_c.0,
            point_c.1,
            vc.z,
            p.uv_start + current_triangle,
        );

        current_triangle += 1;
    }
}
pub fn build_primitives<const C: usize, const PIXCOUNT: usize, DEPTHACC: Number>(
    geombuffer: &GeometryBuffer,
    vertex_buffer: &VertexBuffer<C>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer<f32>,
) {
    for geometry_id in 1..geombuffer.current_size {
        let x = geombuffer.content.get(geometry_id).unwrap();
        match x {
            crate::geombuffer::GeomElement::Point(p) => {
                //grab the vertex idx
                let point_vertex_idx = p.pa;
                let v = vertex_buffer.get_at(point_vertex_idx);

                // convert from clip to screen space
                let (col, row) = ndc_to_screen(v, drawbuffer.col_count, drawbuffer.row_count, 0, 0);
                let _ = primitivbuffer.add_point(
                    p.geom_ref.node_id,
                    geometry_id,
                    p.geom_ref.material_id,
                    row,
                    col,
                    v.z,
                    0,
                );
            }
            crate::geombuffer::GeomElement::Line(l) => todo!(),
            crate::geombuffer::GeomElement::Polygon(p) => {
                poly_as_primitive(&p, geometry_id, vertex_buffer, drawbuffer, primitivbuffer)
            }
        }
    }
}

#[pyfunction]
pub fn build_primitives_py(
    py: Python,
    geometry_buffer: &GeometryBufferPy,
    vbpy: &VertexBufferPy,
    dbpy: &AbigDrawing,
    mut primitivbuffer: PyRefMut<'_, PrimitiveBufferPy>,
) {
    let geom_content = &geometry_buffer.buffer;

    let prim_content = &mut primitivbuffer.content;
    build_primitives(geom_content, &vbpy.buffer, &dbpy.db, prim_content);
}

#[pyfunction]
pub fn apply_material_py(
    py: Python,
    material_buffer: &MaterialBufferPy,
    texturebuffer: &TextureBufferPy,
    mut draw_buffer_py: PyRefMut<'_, AbigDrawing>,
) {
    let matbuff_content = &material_buffer.content;

    let draw_buffer_content = &mut draw_buffer_py.db;
    let texturebuffer_contetnt = &texturebuffer.data;
    draw_buffer_content.apply_material(matbuff_content, texturebuffer_contetnt)
}
