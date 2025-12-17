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
    primitiv_building::triangle_3d::polygon3d_as_primitive_triangles,
    primitivbuffer::*,
    raster::vertex::Vertex,
    texturebuffer::TextureBufferPy,
    vertexbuffer::{
        transform_pack::TransformPack,
        transform_pack_py::TransformPackPy,
        uv_buffer::UVBuffer,
        vertex_buffer::{self, TriangleBuffer, VertexBuffer},
        vertex_buffer_py::VertexBufferPy,
    },
};

pub mod triangle_clipping;
use triangle_clipping::*;
pub mod tomato_triangle_clipping;
use tomato_triangle_clipping::*;
pub mod line_clipping_2d;
use line_clipping_2d::*;
pub mod point_clipping;
use point_clipping::*;

pub mod line_clipping;
use line_clipping::*;

pub mod rectangle_clipping;
pub mod triangle_3d;

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

pub fn build_primitives<const PIXCOUNT: usize, DEPTHACC: Number>(
    geombuffer: &GeometryBuffer,
    vertex_buffer_3d: &mut VertexBuffer<Vec4>,
    vertex_buffer_2d: &mut VertexBuffer<Vec4>,
    triangle_buffer: &TriangleBuffer,
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
                    &(view_matrix * model_matrix),
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
                    &(view_matrix * model_matrix),
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
            crate::geombuffer::GeomElement::Line2D(p) => {
                let model_matrix = transform_pack.get_node_transform(p.geom_ref.node_id);
                let view_matrix = &transform_pack.view_matrix_2d;

                vertex_buffer_2d.apply_mv(
                    &(view_matrix * model_matrix),
                    p.point_start,
                    p.point_start + p.point_count,
                );

                for segment_idx in 0..(p.point_count - 1) {
                    let point_vertex_idx = p.point_start + segment_idx;
                    let pa = vertex_buffer_2d.get_calculated(point_vertex_idx);
                    let pb = vertex_buffer_2d.get_calculated(point_vertex_idx + 1);

                    let (uva, uvb, _uvc) = uv_array_input.get_uv(p.uv_idx + segment_idx);

                    // clip the segment
                    let clipped = clip_line2d(pa, pb, uva, uvb);
                    if let Some((a_clip, b_clip, uva_clip, uvb_clip)) = clipped {
                        // convert from homogeneous coordinates to NDC

                        let point_a = drawbuffer.ndc_to_screen_floating_with_clamp(&a_clip.xy());
                        let point_b = drawbuffer.ndc_to_screen_floating_with_clamp(&b_clip.xy());
                        let pa_pos = vec4(point_a.x, point_a.y, a_clip.z, a_clip.w);
                        let pb_pos = vec4(point_b.x, point_b.y, b_clip.z, b_clip.w);

                        let normal_a = vec3(0.0, 0.0, 1.0);
                        let normal_b = vec3(0.0, 0.0, 1.0);

                        primitivbuffer.add_line(
                            p.geom_ref.node_id,
                            geometry_id,
                            p.geom_ref.material_id,
                            pa_pos,
                            normal_a,
                            uva_clip,
                            pb_pos,
                            normal_b,
                            uvb_clip,
                        );
                    }
                }
            }
            crate::geombuffer::GeomElement::Point3D(p) => {
                //grab the vertex idx
                let point_vertex_idx = p.point_start;
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
            crate::geombuffer::GeomElement::Line3D(points) => {
                vertex_buffer_3d.apply_mvp(
                    transform_pack.get_node_transform(points.geom_ref.node_id),
                    &transform_pack.view_matrix_3d,
                    &transform_pack.projection_matrix_3d,
                    points.point_start,
                    points.point_start + points.point_count,
                );

                for segment_idx in 0..(points.point_count - 1) {
                    let point_vertex_idx = points.point_start + segment_idx;
                    let pa = vertex_buffer_3d.get_calculated(point_vertex_idx);
                    let pb = vertex_buffer_3d.get_calculated(point_vertex_idx + 1);

                    let (uva, uvb, _uvc) = uv_array_input.get_uv(points.uv_idx + segment_idx);
                    line3d_as_primitive(
                        &pa,
                        &pb,
                        (uva, uvb, _uvc),
                        &points.geom_ref,
                        geometry_id,
                        vertex_buffer_3d,
                        uv_array_input,
                        drawbuffer,
                        primitivbuffer,
                    )
                }
            }
            crate::geombuffer::GeomElement::Polygon2D(polygon) => {
                let model_matrix = transform_pack.get_node_transform(polygon.geom_ref.node_id);
                let view_matrix = &transform_pack.view_matrix_2d;

                let p_start = polygon.p_start;
                let p_end = polygon.p_count + polygon.p_start;

                let t_start = polygon.triangle_start;
                vertex_buffer_2d.apply_mv(&(view_matrix * model_matrix), p_start, p_end);
                // for every triangle in the polygon
                for triangle_id in 0..polygon.triangle_count {
                    let (pa_idx, pb_idx, pc_idx, normal) =
                        triangle_buffer.get_triangle(t_start + triangle_id);

                    let va = vertex_buffer_2d.get_calculated(pa_idx);
                    let vb = vertex_buffer_2d.get_calculated(pb_idx);
                    let vc = vertex_buffer_2d.get_calculated(pc_idx);

                    // get the uv coordinates
                    let uvs = uv_array_input.get_uv(polygon.uv_start + triangle_id);
                    let normal_vec: Vec3 = *normal;
                    // clip the triangle
                    let mut output_buffer: SmallTriangleBuffer<8> = SmallTriangleBuffer::new();
                    clip_triangle_to_clip_space_xy(&va, &vb, &vc, uvs, &mut output_buffer);

                    for (t, uvs) in output_buffer.iter() {
                        // convert from ndc to screen space
                        let point_a = drawbuffer.ndc_to_screen_floating_with_clamp(&t[0].xy());
                        let point_b = drawbuffer.ndc_to_screen_floating_with_clamp(&t[1].xy());
                        let point_c = drawbuffer.ndc_to_screen_floating_with_clamp(&t[2].xy());

                        let pa_pos = vec4(point_a.x, point_a.y, t[0].z, t[0].w);
                        let pb_pos = vec4(point_b.x, point_b.y, t[1].z, t[1].w);
                        let pc_pos = vec4(point_c.x, point_c.y, t[2].z, t[2].w);

                        primitivbuffer.add_triangle(
                            polygon.geom_ref.node_id,
                            geometry_id,
                            polygon.geom_ref.material_id,
                            Vertex {
                                pos: pa_pos,
                                normal: normal_vec,
                                uv: uvs[0],
                            },
                            Vertex {
                                pos: pb_pos,
                                normal: normal_vec,
                                uv: uvs[1],
                            },
                            Vertex {
                                pos: pc_pos,
                                normal: normal_vec,
                                uv: uvs[2],
                            },
                        );
                    }
                }
            }
            crate::geombuffer::GeomElement::Polygon3D(polygon) => polygon3d_as_primitive_triangles(
                polygon,
                geometry_id,
                transform_pack,
                vertex_buffer_3d,
                triangle_buffer,
                uv_array_input,
                drawbuffer,
                primitivbuffer,
            ),
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
        &vbpy.triangle_buffer3d,
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
