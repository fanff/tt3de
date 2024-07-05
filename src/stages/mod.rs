use nalgebra_glm::{Number, Real, Vec2, Vec3, Vec4};
use primitivbuffer::PrimitiveBuffer;
use pyo3::{pyfunction, PyRefMut, Python};

use crate::{
    drawbuffer::{
        drawbuffer::{apply_material_on, DrawBuffer},
        AbigDrawing,
    },
    geombuffer::{GeometryBuffer, GeometryBufferPy, Polygon},
    material::MaterialBufferPy,
    primitivbuffer::*,
    texturebuffer::TextureBufferPy,
    vertexbuffer::{TransformPack, TransformPackPy, VertexBuffer, VertexBufferPy},
};
pub mod clipping;
use clipping::*;

fn poly_as_primitive<const C: usize, const PIXCOUNT: usize, DEPTHACC: Number>(
    polygon: &Polygon,
    geometry_id: usize,
    vertex_buffer: &VertexBuffer<C>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer<f32>,
) {
    let va = vertex_buffer.get_world_space_vertex(polygon.p_start);
    for triangle_id in 0..polygon.triangle_count {
        let p_start = polygon.p_start + triangle_id;
        let vb = vertex_buffer.get_world_space_vertex(p_start + 1);
        let vc = vertex_buffer.get_world_space_vertex(p_start + 2);

        // clip the first triangle
        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_clip_space(va, vb, vc, &mut output_buffer);

        for t in output_buffer.iter() {
            // convert from clip to screen space
            let point_a = drawbuffer.ndc_to_screen_row_col(&t[0].xy());
            let point_b = drawbuffer.ndc_to_screen_row_col(&t[1].xy());
            let point_c = drawbuffer.ndc_to_screen_row_col(&t[2].xy());

            primitivbuffer.add_triangle(
                polygon.geom_ref.node_id,
                geometry_id,
                polygon.geom_ref.material_id,
                point_a.0,
                point_a.1,
                va.z,
                point_b.0,
                point_b.1,
                vb.z,
                point_c.0,
                point_c.1,
                vc.z,
                polygon.uv_start,
            );
        }
    }
}
pub fn build_primitives<const C: usize, const PIXCOUNT: usize, DEPTHACC: Number>(
    geombuffer: &GeometryBuffer,
    vertex_buffer: &mut VertexBuffer<C>,
    transform_pack: &TransformPack,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer<f32>,
) {
    for geometry_id in 1..geombuffer.current_size {
        let x = geombuffer.content.get(geometry_id).unwrap();
        match x {
            crate::geombuffer::GeomElement::Point(p) => {
                //grab the vertex idx
                let point_vertex_idx = p.pa;
                let v = vertex_buffer.get_world_space_vertex(point_vertex_idx);

                // convert from clip to screen space
                let (col, row) = drawbuffer.ndc_to_screen_row_col(&v.xy());
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
                // apply mv operation
                vertex_buffer.apply_mv(
                    transform_pack.get_node_transform(p.geom_ref.node_id),
                    &transform_pack.view_matrix,
                    p.p_start,
                    p.triangle_count + 2 + p.p_start,
                );
                poly_as_primitive(&p, geometry_id, vertex_buffer, drawbuffer, primitivbuffer)
            }
        }
    }
}

#[pyfunction]
pub fn build_primitives_py(
    geometry_buffer: &GeometryBufferPy,
    vbpy: &mut VertexBufferPy,
    trbuffer_py: &TransformPackPy,
    dbpy: &AbigDrawing,
    primitivbuffer: &mut PrimitiveBufferPy,
) {
    let geom_content = &geometry_buffer.buffer;

    let prim_content = &mut primitivbuffer.content;
    build_primitives(
        geom_content,
        &mut vbpy.buffer,
        &trbuffer_py.data,
        &dbpy.db,
        prim_content,
    );
}

#[pyfunction]
pub fn apply_material_py(
    material_buffer: &MaterialBufferPy,
    texturebuffer: &TextureBufferPy,
    vertex_buffer: &VertexBufferPy,
    primitivbuffer: &PrimitiveBufferPy,
    mut draw_buffer_py: PyRefMut<'_, AbigDrawing>,
) {
    let draw_buffer_content: &mut DrawBuffer<2, f32> = &mut draw_buffer_py.db;

    apply_material_on(
        draw_buffer_content,
        &material_buffer.content,
        &texturebuffer.data,
        &vertex_buffer.uv_array,
        &primitivbuffer.content,
    );
}
