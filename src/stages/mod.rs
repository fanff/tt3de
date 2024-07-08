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
    vertexbuffer::{TransformPack, TransformPackPy, UVBuffer, VertexBuffer, VertexBufferPy},
};
pub mod clipping;
use clipping::*;

pub mod point_clipping;
use point_clipping::*;

fn perspective_divide(v: &Vec4) -> Vec3 {
    Vec3::new(v.x / v.w, v.y / v.w, v.z / v.w)
}
fn perspective_divide_triplet(va: &Vec4, vb: &Vec4, vc: &Vec4) -> (Vec3, Vec3, Vec3) {
    (
        perspective_divide(va),
        perspective_divide(vb),
        perspective_divide(vc),
    )
}
fn poly_as_primitive<
    const C: usize,
    const MAX_UV_CONTENT: usize,
    const PIXCOUNT: usize,
    DEPTHACC: Number,
>(
    polygon: &Polygon,
    geometry_id: usize,
    vertex_buffer: &VertexBuffer<C>,
    uv_array: &UVBuffer<MAX_UV_CONTENT, f32>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer<f32>,
) {
    let mut output_buffer = TriangleBuffer::new();
    let va = vertex_buffer.get_clip_space_vertex(polygon.p_start);
    for triangle_id in 0..polygon.triangle_count {
        let p_start = polygon.p_start + triangle_id;
        let vb = vertex_buffer.get_clip_space_vertex(p_start + 1);
        let vc = vertex_buffer.get_clip_space_vertex(p_start + 2);
        // get the uv coordinates
        let uvs = uv_array.get_uv(polygon.uv_start + triangle_id);
        // clip the first triangle
        clip_triangle_to_clip_space(va, vb, vc, uvs, &mut output_buffer);

        for (t, uvs) in output_buffer.iter() {
            // perform the perspective division to get in the ndc space
            let pdiv = perspective_divide_triplet(&t[0], &t[1], &t[2]);
            let (va, vb, vc) = pdiv;

            // convert from ndc to screen space
            let point_a = drawbuffer.ndc_to_screen_row_col(&va.xy());
            let point_b = drawbuffer.ndc_to_screen_row_col(&vb.xy());
            let point_c = drawbuffer.ndc_to_screen_row_col(&vc.xy());

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
        output_buffer.clear();
    }
}
pub fn build_primitives<
    const C: usize,
    const MAX_UV_CONTENT: usize,
    const PIXCOUNT: usize,
    DEPTHACC: Number,
>(
    geombuffer: &GeometryBuffer,
    vertex_buffer: &mut VertexBuffer<C>,
    transform_pack: &TransformPack,
    uv_array: &UVBuffer<MAX_UV_CONTENT, f32>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer<f32>,
) {
    for geometry_id in 1..geombuffer.current_size {
        let geom_element = geombuffer.content.get(geometry_id).unwrap();
        match geom_element {
            crate::geombuffer::GeomElement::Point3D(p) => {
                //grab the vertex idx
                let point_vertex_idx = p.pa;
                vertex_buffer.apply_mvp(
                    transform_pack.get_node_transform(p.geom_ref.node_id),
                    &transform_pack.view_matrix_3d,
                    &transform_pack.projection_matrix_3d,
                    point_vertex_idx,
                    point_vertex_idx + 1,
                );

                let point_clip_space = vertex_buffer.get_clip_space_vertex(point_vertex_idx);
                // clip the point to the clip frustum
                if clip_point_to_clip_space(point_clip_space) {
                    // perform the perspective division
                    let v = perspective_divide(point_clip_space);
                    // convert from clip to screen space
                    let (row, col) = drawbuffer.ndc_to_screen_row_col(&v.xy());
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
            }
            crate::geombuffer::GeomElement::Line(l) => todo!(),
            crate::geombuffer::GeomElement::Polygon(p) => {
                // apply mv operation
                vertex_buffer.apply_mv(
                    transform_pack.get_node_transform(p.geom_ref.node_id),
                    &transform_pack.view_matrix_2d,
                    p.p_start,
                    p.triangle_count + 2 + p.p_start,
                );
                poly_as_primitive(
                    &p,
                    geometry_id,
                    vertex_buffer,
                    uv_array,
                    drawbuffer,
                    primitivbuffer,
                )
            }
            crate::geombuffer::GeomElement::Polygon3D(polygon) => {
                // apply mv operation
                vertex_buffer.apply_mvp(
                    transform_pack.get_node_transform(polygon.geom_ref.node_id),
                    &transform_pack.view_matrix_3d,
                    &transform_pack.projection_matrix_3d,
                    polygon.p_start,
                    polygon.triangle_count + 2 + polygon.p_start,
                );
                poly_as_primitive(
                    &polygon,
                    geometry_id,
                    vertex_buffer,
                    uv_array,
                    drawbuffer,
                    primitivbuffer,
                )
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
        &vbpy.uv_array,
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
