use nalgebra_glm::{dot, Number, Vec4};

use crate::{
    drawbuffer::drawbuffer::DrawBuffer,
    geombuffer::Line,
    vertexbuffer::{UVBuffer, VertexBuffer},
};

use super::{perspective_divide_v4_v4, primitivbuffer::PrimitiveBuffer};

/// Clip a line to the view frustum.
/// The line is defined by two points in clip space coordinates; in homogeneous coordinates (x, y, z, w).
/// The function returns the two points of the clipped line.
pub fn clip_line_to_clip_space(pa: &Vec4, pb: &Vec4) -> Option<(Vec4, Vec4)> {
    // Define the frustum planes in clip space
    // Left, Right, Bottom, Top, Near, Far
    let frustum_planes = [
        Vec4::new(-1.0, 0.0, 0.0, 1.0), // Left
        Vec4::new(1.0, 0.0, 0.0, 1.0),  // Right
        Vec4::new(0.0, -1.0, 0.0, 1.0), // Bottom
        Vec4::new(0.0, 1.0, 0.0, 1.0),  // Top
        Vec4::new(0.0, 0.0, 1.0, 0.0),  // Near
        Vec4::new(0.0, 0.0, -1.0, 1.0), // Far
    ];
    let mut pa_clipped = *pa;
    let mut pb_clipped = *pb;
    let mut is_visible = true;

    for plane in &frustum_planes {
        let dot_pa = dot(plane, &pa_clipped);
        let dot_pb = dot(plane, &pb_clipped);

        if dot_pa < 0.0 && dot_pb < 0.0 {
            // Both points are outside the frustum plane, the line is not visible
            is_visible = false;
            break;
        }

        if dot_pa < 0.0 {
            // pa is outside the frustum, clip it
            let t = dot_pa / (dot_pa - dot_pb);
            pa_clipped = pa_clipped + (t * (pb_clipped - pa_clipped));
        } else if dot_pb < 0.0 {
            // pb is outside the frustum, clip it
            let t = dot_pb / (dot_pb - dot_pa);
            pb_clipped = pb_clipped + t * (pa_clipped - pb_clipped);
        }
    }

    if is_visible {
        Some((pa_clipped, pb_clipped))
    } else {
        None
    }
}

/// Converts a line to a primitive and adds it to the drawbuffer.
/// Clip the line to the bounbding box of the view frustum.
pub fn line_as_primitive<
    const PIXCOUNT: usize,
    DEPTHACC: Number,
>(
    line: &Line,
    geometry_id: usize,
    vertex_buffer: &VertexBuffer,
    uv_array: &UVBuffer< f32>,
    drawbuffer: &DrawBuffer<PIXCOUNT, DEPTHACC>,
    primitivbuffer: &mut PrimitiveBuffer,
) {
    // coordinates of the two points of the line
    // in clip space coordinates (x, y, z, w) (homogeneous coordinates)
    let pa = vertex_buffer.get_clip_space_vertex(line.p_start);
    let pb = vertex_buffer.get_clip_space_vertex(line.p_start + 1);

    // get the uv coordinates
    let _uv = uv_array.get_uv(line.uv_start);

    // clip the line to the view frustum
    let clipped_line = clip_line_to_clip_space(pa, pb);
    match clipped_line {
        Some((a_clip, bclip)) => {
            // convert from homogeneous coordinates to NDC
            let pdiva = perspective_divide_v4_v4(&a_clip);
            let pdivb = perspective_divide_v4_v4(&bclip);

            let point_a = drawbuffer.ndc_to_screen_floating_with_clamp(&pdiva.xy());
            let point_b = drawbuffer.ndc_to_screen_floating_with_clamp(&pdivb.xy());
            primitivbuffer.add_line(
                line.geom_ref.node_id,
                geometry_id,
                line.geom_ref.material_id,
                point_a.y,
                point_a.x,
                pdiva.z,
                point_b.y,
                point_b.x,
                pdivb.z,
                0,
            );
        }
        None => {}
    }
}
