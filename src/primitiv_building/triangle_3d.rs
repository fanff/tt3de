use nalgebra_glm::{dot, vec2, vec3, vec4, Number, Vec3, Vec4};

use crate::{
    drawbuffer::{
        drawbuffer::{apply_material_on, apply_material_on_parallel, DrawBuffer},
        DrawingBufferPy,
    },
    geombuffer::{GeometryBuffer, GeometryBufferPy, Polygon},
    material::MaterialBufferPy,
    primitiv_building::{
        perspective_divide_triplet, tomato_triangle_clipping::tomato_clip_triangle_to_clip_space,
        triangle_clipping::SmallTriangleBuffer,
    },
    primitivbuffer::primitivbuffer::PrimitiveBuffer,
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

pub fn polygon3d_as_primitive_triangles<const PIXCOUNT: usize, DEPTHACC: Number>(
    polygon: &Polygon,
    geometry_id: usize,
    transform_pack: &TransformPack,
    vertex_buffer: &mut VertexBuffer<Vec4>,
    triangle_buffer: &TriangleBuffer,
    uv_array: &UVBuffer<f32>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer,
) {
    let mv =
        transform_pack.view_matrix_3d * transform_pack.get_node_transform(polygon.geom_ref.node_id);
    // Normal matrix = inverse-transpose of MV, using upper-left 3x3
    let normal_matrix_3x3 = mv
        .fixed_view::<3, 3>(0, 0) // or equivalent to get 3x3 part
        .try_inverse()
        .unwrap()
        .transpose();
    let perspective_matrix = &transform_pack.projection_matrix_3d;

    let p_start = polygon.p_start;
    let p_end = polygon.p_count + polygon.p_start;

    let t_start = polygon.triangle_start;

    vertex_buffer.apply_mv(&mv, p_start, p_end);

    for triangle_id in 0..polygon.triangle_count {
        let (pa_idx, pb_idx, pc_idx, normal) = triangle_buffer.get_triangle(t_start + triangle_id);

        let normal_obj: Vec3 = *normal;
        // Transform the normal into view space
        let normal_view: Vec3 = normal_matrix_3x3 * normal_obj;

        let va = vertex_buffer.get_calculated(pa_idx);
        let point_on_triangle_view: Vec3 = va.xyz();
        // Direction from triangle to eye (origin)
        let to_eye = -point_on_triangle_view; // since eye is at (0,0,0)

        // cull backfacing triangles
        if normal_view.dot(&to_eye) >= 0.0 {
            continue;
        }

        let vb = vertex_buffer.get_calculated(pb_idx);
        let vc = vertex_buffer.get_calculated(pc_idx);
        // get the uv coordinates
        let uvs = uv_array.get_uv(polygon.uv_start + triangle_id);

        // apply perspective projection
        let va_clip = perspective_matrix * va;
        let vb_clip = perspective_matrix * vb;
        let vc_clip = perspective_matrix * vc;

        // clip the triangle
        let mut output_buffer: SmallTriangleBuffer<12> = SmallTriangleBuffer::new();
        tomato_clip_triangle_to_clip_space(&va_clip, &vb_clip, &vc_clip, uvs, &mut output_buffer);

        for (t, uvs) in output_buffer.iter() {
            // perform the perspective division to get in the ndc space
            let (vacdiv, vbcdiv, vccdiv) = perspective_divide_triplet(&t[0], &t[1], &t[2]);
            // convert from ndc to screen space
            let point_a = drawbuffer.ndc_to_screen_floating(&vacdiv.xy());
            let point_b = drawbuffer.ndc_to_screen_floating(&vbcdiv.xy());
            let point_c = drawbuffer.ndc_to_screen_floating(&vccdiv.xy());

            primitivbuffer.add_triangle(
                polygon.geom_ref.node_id,
                geometry_id,
                polygon.geom_ref.material_id,
                // Keep the w value for the perspective correction
                Vertex::new(
                    vec4(point_a.x, point_a.y, vacdiv.z, vacdiv.w),
                    normal_view,
                    uvs[0] * vacdiv.w,
                ),
                Vertex::new(
                    vec4(point_b.x, point_b.y, vbcdiv.z, vbcdiv.w),
                    normal_view,
                    uvs[1] * vbcdiv.w,
                ),
                Vertex::new(
                    vec4(point_c.x, point_c.y, vccdiv.z, vccdiv.w),
                    normal_view,
                    uvs[2] * vccdiv.w,
                ),
            );
        }
    }
}
