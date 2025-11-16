use nalgebra_glm::{dot, vec2, vec3, vec4, Number, Vec3, Vec4};
use primitivbuffer::PrimitiveBuffer;
use pyo3::{pyfunction, PyRefMut};

use crate::{
    drawbuffer::{
        drawbuffer::{apply_material_on, apply_material_on_parallel, DrawBuffer},
        DrawingBufferPy,
    },
    geombuffer::{GeometryBuffer, GeometryBufferPy, Polygon},
    material::MaterialBufferPy,
    primitivbuffer::*,
    raster::vertex::Vertex,
    texturebuffer::TextureBufferPy,
    vertexbuffer::{
        transform_pack::TransformPack,
        transform_pack_py::TransformPackPy,
        uv_buffer::UVBuffer,
        vertex_buffer::{self, VertexBuffer},
        vertex_buffer_py::VertexBufferPy,
    },
};

pub mod triangle_clipping;
use triangle_clipping::*;
pub mod tomato_triangle_clipping;
use tomato_triangle_clipping::*;

pub mod point_clipping;
use point_clipping::*;

pub mod line_clipping;
use line_clipping::*;

pub mod rectangle_clipping;

fn perspective_divide(v: &Vec4) -> Vec3 {
    Vec3::new(v.x / v.w, v.y / v.w, v.z / v.w)
}

fn perspective_divide_v4_v4(v: &Vec4) -> Vec4 {
    Vec4::new(v.x / v.w, v.y / v.w, v.z / v.w, 1.0 / v.w)
}

fn perspective_divide_triplet(va: &Vec4, vb: &Vec4, vc: &Vec4) -> (Vec4, Vec4, Vec4) {
    let wa_inv = 1.0 / va.w;
    let wb_inv = 1.0 / vb.w;
    let wc_inv = 1.0 / vc.w;
    (
        Vec4::new(va.x * wa_inv, va.y * wa_inv, va.z * wa_inv, wa_inv),
        Vec4::new(vb.x * wb_inv, vb.y * wb_inv, vb.z * wb_inv, wb_inv),
        Vec4::new(vc.x * wc_inv, vc.y * wc_inv, vc.z * wc_inv, wc_inv),
    )
}

fn polygon_fan_as_primitive<const PIXCOUNT: usize, DEPTHACC: Number>(
    polygon: &Polygon,
    geometry_id: usize,
    transform_pack: &TransformPack,
    vertex_buffer: &mut VertexBuffer<Vec4>,
    uv_array: &UVBuffer<f32>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer,
) {
    let va = vertex_buffer.get_calculated(polygon.p_start);
    let eyepos: Vec4 = transform_pack.projection_matrix_3d * (&vec4(0.0, 0.0, 0.0, 1.0));
    for triangle_id in 0..polygon.triangle_count {
        let p_start = polygon.p_start + triangle_id;
        let vb = vertex_buffer.get_calculated(p_start + 1);
        let vc = vertex_buffer.get_calculated(p_start + 2);

        let normal_vec: Vec3 = (vb.xyz() - va.xyz()).cross(&(vc.xyz() - va.xyz()));
        // cull backfacing triangles with cross product (%) shenanigans
        if dot(&normal_vec, &(va - eyepos).xyz()) > 0.0 {
            continue;
        }

        // get the uv coordinates
        let uvs = uv_array.get_uv(polygon.uv_start + triangle_id);
        // clip the first triangle
        let mut output_buffer: TriangleBuffer<12> = TriangleBuffer::new();
        tomato_clip_triangle_to_clip_space(va, vb, vc, uvs, &mut output_buffer);

        for (t, uvs) in output_buffer.iter() {
            // perform the perspective division to get in the ndc space
            let (vadiv, vbdiv, vcdiv) = perspective_divide_triplet(&t[0], &t[1], &t[2]);

            // convert from ndc to screen space
            let point_a = drawbuffer.ndc_to_screen_floating(&vadiv.xy());
            let point_b = drawbuffer.ndc_to_screen_floating(&vbdiv.xy());
            let point_c = drawbuffer.ndc_to_screen_floating(&vcdiv.xy());

            primitivbuffer.add_triangle3d(
                polygon.geom_ref.node_id,
                geometry_id,
                polygon.geom_ref.material_id,
                // Keep the w value for the perspective correction
                Vertex::new(
                    vec4(point_a.x, point_a.y, vadiv.z, vadiv.w),
                    normal_vec,
                    uvs[0] * vadiv.w,
                ),
                Vertex::new(
                    vec4(point_b.x, point_b.y, vbdiv.z, vbdiv.w),
                    normal_vec,
                    uvs[1] * vbdiv.w,
                ),
                Vertex::new(
                    vec4(point_c.x, point_c.y, vcdiv.z, vcdiv.w),
                    normal_vec,
                    uvs[2] * vcdiv.w,
                ),
            );
        }
    }
}

fn polygon_as_primitive<const PIXCOUNT: usize, DEPTHACC: Number>(
    polygon: &Polygon,
    geometry_id: usize,
    transform_pack: &TransformPack,
    vertex_buffer: &mut VertexBuffer<Vec4>,
    uv_array: &UVBuffer<f32>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer,
) {
    let eyepos: Vec4 = transform_pack.projection_matrix_3d * (&vec4(0.0, 0.0, 0.0, 1.0));
    for triangle_id in 0..polygon.triangle_count {
        let p_start = polygon.p_start + (triangle_id * 3);
        let va = vertex_buffer.get_calculated(p_start);
        let vb = vertex_buffer.get_calculated(p_start + 1);
        let vc = vertex_buffer.get_calculated(p_start + 2);

        let normal_vec: Vec3 = (vb.xyz() - va.xyz()).cross(&(vc.xyz() - va.xyz()));
        // cull backfacing triangles
        if dot(&normal_vec, &(va - eyepos).xyz()) > 0.0 {
            continue;
        }
        // get the uv coordinates
        let uvs = uv_array.get_uv(polygon.uv_start + triangle_id);
        // clip the triangle
        let mut output_buffer: TriangleBuffer<12> = TriangleBuffer::new();
        tomato_clip_triangle_to_clip_space(va, vb, vc, uvs, &mut output_buffer);

        //clip_triangle_to_clip_space(&vadiv, &vbdiv, &vcdiv, uvs, &mut output_buffer);

        for (t, uvs) in output_buffer.iter() {
            // perform the perspective division to get in the ndc space
            let (vacdiv, vbcdiv, vccdiv) = perspective_divide_triplet(&t[0], &t[1], &t[2]);
            // convert from ndc to screen space
            let point_a = drawbuffer.ndc_to_screen_floating(&vacdiv.xy());
            let point_b = drawbuffer.ndc_to_screen_floating(&vbcdiv.xy());
            let point_c = drawbuffer.ndc_to_screen_floating(&vccdiv.xy());

            primitivbuffer.add_triangle3d(
                polygon.geom_ref.node_id,
                geometry_id,
                polygon.geom_ref.material_id,
                // Keep the w value for the perspective correction
                Vertex::new(
                    vec4(point_a.x, point_a.y, vacdiv.z, vacdiv.w),
                    normal_vec,
                    uvs[0] * vacdiv.w,
                ),
                Vertex::new(
                    vec4(point_b.x, point_b.y, vbcdiv.z, vbcdiv.w),
                    normal_vec,
                    uvs[1] * vbcdiv.w,
                ),
                Vertex::new(
                    vec4(point_c.x, point_c.y, vccdiv.z, vccdiv.w),
                    normal_vec,
                    uvs[2] * vccdiv.w,
                ),
            );
        }
    }
}
pub fn build_primitives<const PIXCOUNT: usize, DEPTHACC: Number>(
    geombuffer: &GeometryBuffer,
    vertex_buffer_3d: &mut VertexBuffer<Vec4>,
    vertex_buffer_2d: &mut VertexBuffer<Vec4>,
    transform_pack: &TransformPack,
    uv_array_input: &UVBuffer<f32>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer,
) {
    for geometry_id in 1..geombuffer.current_size {
        let geom_element = geombuffer.content.get(geometry_id).unwrap();
        match geom_element {
            crate::geombuffer::GeomElement::Rect2D(p) => {
                let model_matrix = transform_pack.get_node_transform(p.geom_ref.node_id);
                let view_matrix = &transform_pack.view_matrix_2d;

                vertex_buffer_2d.apply_mv(
                    model_matrix,
                    view_matrix,
                    p.point_start,
                    p.point_start + p.point_count,
                );

                // get the two points that make the rectangle
                let top_left = vertex_buffer_2d.get_calculated(p.point_start);
                let bottom_right = vertex_buffer_2d.get_calculated(p.point_start + 1);
                // get the uv coordinates
                let (uv_start, uv_end, _uv) = uv_array_input.get_uv(p.uv_idx);

                let clipped_boundaries = rectangle_clipping::clip_rectangle(
                    &top_left,
                    &bottom_right,
                    (uv_start, uv_end),
                );

                if let Some(cb) = clipped_boundaries {
                    let top_left = cb.0 .0;
                    let bottom_right = cb.0 .1;
                    let uv_start = cb.1 .0;
                    let uv_end = cb.1 .1;
                    let in_screen_space_tl =
                        drawbuffer.ndc_to_screen_floating_with_clamp(&top_left.xy());
                    let in_screen_space_br =
                        drawbuffer.ndc_to_screen_floating_with_clamp(&bottom_right.xy());
                    let top_left_vertex = Vertex::new(
                        Vec4::new(
                            in_screen_space_tl.x,
                            in_screen_space_tl.y,
                            top_left.z,
                            top_left.w,
                        ),
                        vec3(0.0, 0.0, 1.0),
                        uv_start,
                    );
                    let bottom_right_vertex = Vertex::new(
                        Vec4::new(
                            in_screen_space_br.x,
                            in_screen_space_br.y,
                            bottom_right.z,
                            bottom_right.w,
                        ),
                        vec3(0.0, 0.0, 1.0),
                        uv_end,
                    );

                    // add two triangles to make the rectangle
                    primitivbuffer.add_rect(
                        p.geom_ref.node_id,
                        geometry_id,
                        p.geom_ref.material_id,
                        top_left_vertex,
                        bottom_right_vertex,
                    );
                };
            }
            crate::geombuffer::GeomElement::Points2D(p) => {
                let model_matrix = transform_pack.get_node_transform(p.geom_ref.node_id);
                let view_matrix = &transform_pack.view_matrix_2d;

                vertex_buffer_2d.apply_mv(
                    model_matrix,
                    view_matrix,
                    p.point_start,
                    p.point_start + p.point_count,
                );

                for point_idx in 0..p.point_count {
                    let point_vertex_idx = p.point_start + point_idx;
                    let point_clip_space = vertex_buffer_2d.get_calculated(point_vertex_idx);
                    // clip the point to the clip frustum
                    if clip_point_to_clip_space(point_clip_space) {
                        // convert from clip to screen space
                        let screen_ccord =
                            drawbuffer.ndc_to_screen_floating_with_clamp(&point_clip_space.xy());
                        let _ = primitivbuffer.add_point(
                            p.geom_ref.node_id,
                            geometry_id,
                            p.geom_ref.material_id,
                            screen_ccord.y,
                            screen_ccord.x,
                            point_clip_space.z,
                            p.uv_idx + point_idx,
                        );
                    }
                }
            }
            crate::geombuffer::GeomElement::Point3D(p) => {
                //grab the vertex idx
                let point_vertex_idx = p.pa;
                vertex_buffer_3d.apply_mvp(
                    transform_pack.get_node_transform(p.geom_ref.node_id),
                    &transform_pack.view_matrix_3d,
                    &transform_pack.projection_matrix_3d,
                    point_vertex_idx,
                    point_vertex_idx + 1,
                );

                let point_clip_space = vertex_buffer_3d.get_calculated(point_vertex_idx);
                // clip the point to the clip frustum
                if clip_point_to_clip_space(point_clip_space) {
                    // perform the perspective division
                    let v = perspective_divide(point_clip_space);
                    // convert from clip to screen space
                    let screen_ccord = drawbuffer.ndc_to_screen_floating_with_clamp(&v.xy());
                    let _ = primitivbuffer.add_point(
                        p.geom_ref.node_id,
                        geometry_id,
                        p.geom_ref.material_id,
                        screen_ccord.y,
                        screen_ccord.x,
                        v.z,
                        0,
                    );
                }
            }
            crate::geombuffer::GeomElement::Line3D(l) => {
                vertex_buffer_3d.apply_mvp(
                    transform_pack.get_node_transform(l.geom_ref.node_id),
                    &transform_pack.view_matrix_3d,
                    &transform_pack.projection_matrix_3d,
                    l.p_start,
                    l.p_start + 2,
                );

                line_as_primitive(
                    l,
                    geometry_id,
                    vertex_buffer_3d,
                    uv_array_input,
                    drawbuffer,
                    primitivbuffer,
                )
            }
            crate::geombuffer::GeomElement::Polygon2D(polygon) => {
                let model_matrix = transform_pack.get_node_transform(polygon.geom_ref.node_id);
                let view_matrix = &transform_pack.view_matrix_2d;

                vertex_buffer_2d.apply_mv(model_matrix, view_matrix, 0, 2);
                todo!();
            }
            crate::geombuffer::GeomElement::PolygonFan3D(polygon) => {
                // apply mv operation
                vertex_buffer_3d.apply_mvp(
                    transform_pack.get_node_transform(polygon.geom_ref.node_id),
                    &transform_pack.view_matrix_3d,
                    &transform_pack.projection_matrix_3d,
                    polygon.p_start,
                    polygon.triangle_count + 2 + polygon.p_start,
                );
                polygon_fan_as_primitive(
                    polygon,
                    geometry_id,
                    transform_pack,
                    vertex_buffer_3d,
                    uv_array_input,
                    drawbuffer,
                    primitivbuffer,
                )
            }
            crate::geombuffer::GeomElement::Polygon3D(polygon) => {
                // apply mv operation
                vertex_buffer_3d.apply_mvp(
                    transform_pack.get_node_transform(polygon.geom_ref.node_id),
                    &transform_pack.view_matrix_3d,
                    &transform_pack.projection_matrix_3d,
                    polygon.p_start,
                    (polygon.triangle_count * 3) + polygon.p_start,
                );
                polygon_as_primitive(
                    polygon,
                    geometry_id,
                    transform_pack,
                    vertex_buffer_3d,
                    uv_array_input,
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
    dbpy: &DrawingBufferPy,
    primitivbuffer: &mut PrimitiveBufferPy,
) {
    let prim_content = &mut primitivbuffer.content;

    build_primitives(
        &geometry_buffer.buffer,
        &mut vbpy.buffer3d,
        &mut vbpy.buffer2d,
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
    mut draw_buffer_py: PyRefMut<'_, DrawingBufferPy>,
) {
    apply_material_on(
        &mut draw_buffer_py.db,
        &material_buffer.content,
        &texturebuffer.data,
        &vertex_buffer.uv_array,
        &primitivbuffer.content,
    );
}

#[pyfunction]
pub fn apply_material_py_parallel(
    material_buffer: &MaterialBufferPy,
    texturebuffer: &TextureBufferPy,
    vertex_buffer: &VertexBufferPy,
    primitivbuffer: &PrimitiveBufferPy,
    mut draw_buffer_py: PyRefMut<'_, DrawingBufferPy>,
) {
    apply_material_on_parallel(
        &mut draw_buffer_py.db,
        &material_buffer.content,
        &texturebuffer.data,
        &vertex_buffer.uv_array,
        &primitivbuffer.content,
    );
}
