use nalgebra_glm::TVec2;

use crate::drawbuffer::drawbuffer::DrawBuffer;

use super::{primitivbuffer::PrimitivReferences, Vertex};

/// Draws a triangle with a flat bottom edge.
///
/// This function assumes that the triangle's vertices are pre-sorted such that:
/// - `pb` and `pc` share the same y-coordinate and form the horizontal bottom edge.
///   Specifically, `pb` is the leftmost vertex (smaller x value) and `pc` is the rightmost.
/// - `pa` is the top vertex of the triangle.
///
/// The following ASCII diagram illustrates the vertex positions:
///
///         pa
///         /\
///        /  \
///       /    \
///      /      \
///    pb--------pc
///
/// # Parameters
///
/// - `drawing_buffer`: A mutable reference to the drawing buffer used for rendering.
/// - `prim_ref`: A reference to the primitive resources (e.g., textures or other attributes).
/// - `pa`: The top vertex of the triangle.
/// - `pb`: The left vertex on the horizontal bottom edge.
/// - `pc`: The right vertex on the horizontal bottom edge.
///
/// # Type Parameters
///
/// - `DEPTHCOUNT`: The number of depth layers in the drawing buffer.
///
/// # Remarks
///
/// The ordering of the vertices simplifies the rasterization process for triangles with a flat bottom edge.
pub fn draw_flat_bottom_triangle<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &Vertex,
    pb: &Vertex,
    pc: &Vertex,
) {
    // calculate dVertex / d row
    let delta_row = pc.pos.y - pa.pos.y;
    let dit0 = (*pb - *pa) / (delta_row);
    let dit1 = (*pc - *pa) / (delta_row);

    // right edge interpolant
    let mut it_edge1 = *pa;

    draw_flat_triangle_double_raster(
        drawing_buffer,
        prim_ref,
        pa,
        pb,
        pc,
        dit0,
        dit1,
        &mut it_edge1,
    );
}

/// Draws a triangle with a flat top edge.
///
/// This function assumes that the triangle's vertices are pre-sorted such that:
/// - `pa` and `pb` share the same y-coordinate and form the horizontal top edge.
///   Specifically, `pa` is the leftmost point (smaller x value) and `pb` is the rightmost.
/// - `pc` is the bottom vertex of the triangle.
///
/// The following ASCII diagram illustrates the vertex positions:
///
///           pa-----------pb
///             \         /
///              \       /
///               \     /
///                \   /
///                  pc
/// # Parameters
///
/// - `drawing_buffer`: A mutable reference to the drawing buffer used for rendering.
/// - `prim_ref`: A reference to primitive resources (e.g., textures or other attributes).
/// - `pa`: The leftmost vertex on the top edge.
/// - `pb`: The rightmost vertex on the top edge.
/// - `pc`: The bottom vertex of the triangle.
///
/// # Type Parameters
///
/// - `DEPTHCOUNT`: The number of depth layers in the drawing buffer.
///
/// # Remarks
///
/// This ordering simplifies the rasterization process for flat top triangles.
pub fn draw_flat_top_triangle<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &Vertex,
    pb: &Vertex,
    pc: &Vertex,
) {
    // calculate dVertex / d row
    let delta_row = pc.pos.y - pa.pos.y;
    let dit0 = (*pc - *pa) / (delta_row);
    let dit1 = (*pc - *pb) / (delta_row);

    // right edge interpolant
    let mut it_edge1 = *pb;

    draw_flat_triangle_double_raster(
        drawing_buffer,
        prim_ref,
        pa,
        pb,
        pc,
        dit0,
        dit1,
        &mut it_edge1,
    );
}

/// Draws a flat triangle by interpolating between vertices along its edges.
///
/// This function is used internally by both `draw_flat_top_triangle` and `draw_flat_bottom_triangle`
/// to render triangles that have one horizontal edge (either the top or bottom).
///
/// The vertices are expected to be arranged as follows:
/// - `pa` is the apex vertex of the triangle.
/// - `_pb` is included for consistency in the triangle definition, but is not used directly for interpolation.
/// - `pc` is the vertex that, together with `pa`, defines the sloped edge.
///
/// The interpolation parameters are defined as:
/// - `left_edge_step`: The per-row interpolation increment for the left edge of the triangle.
///   This value represents how the vertex attributes should change from `pa` towards `pc` along the left side.
/// - `right_edge_step`: The per-row interpolation increment for the right edge of the triangle.
///   It determines how the vertex attributes are interpolated along the right side.
/// - `current_right_edge`: A mutable parameter that tracks the current state along the right edge during
///   the rasterization process. It is updated on each row using `right_edge_step`.
///
/// # Parameters
///
/// - `drawing_buffer`: A mutable reference to the drawing buffer used for rendering.
/// - `prim_ref`: A reference to the primitive resources (e.g., textures, shading parameters).
/// - `pa`: The apex vertex of the triangle.
/// - `_pb`: A vertex included in the triangle definition (unused for interpolation).
/// - `pc`: The vertex that defines the sloped edge of the triangle.
/// - `left_edge_step`: The per-row interpolation increment for the left edge.
/// - `right_edge_step`: The per-row interpolation increment for the right edge.
/// - `current_right_edge`: A mutable vertex tracking the current position along the right edge during interpolation.
///
/// # Type Parameters
///
/// - `DEPTHCOUNT`: The number of depth layers in the drawing buffer.
///
/// # Remarks
///
/// This interpolation-based approach enables smooth gradients and attribute transitions along the triangle edges,
/// simplifying the rasterization process for triangles with a flat side.
pub fn draw_flat_triangle<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &Vertex,
    _pb: &Vertex,
    pc: &Vertex,
    left_edge_step: Vertex,
    right_edge_step: Vertex,
    right_edge_interpolant: &mut Vertex,
) {
    // Create an interpolant for the left edge, starting at the apex (pa).
    let mut left_edge_interpolant = *pa;

    // Determine the starting scanline (row_start) by:
    // 1. Aligning pa.pos.y to the pixel grid (subtract 0.5),
    // 2. Using ceil() to jump to the next full pixel row,
    // 3. Clamping the value to at least 0.
    let row_start = (pa.pos.y - 0.5f32).ceil().max(0.0) as usize;

    // Determine the ending scanline (row_end) based on pc.pos.y by:
    // 1. Aligning the y-coordinate similarly (subtract 0.5 and ceil()),
    // 2. Clamping the result to not exceed the drawing buffer's row count.
    let row_end = (pc.pos.y - 0.5f32)
        .ceil()
        .min(drawing_buffer.row_count as f32) as usize;

    // do interpolant prestep
    // Advance both the left and right edge interpolants to the center of the starting scanline.
    // This "pre-step" corrects their positions by the difference between the center of the first scanline
    // (row_start + 0.5) and the original y-coordinate of pa.
    left_edge_interpolant += left_edge_step * ((row_start as f32 + 0.5f32) - pa.pos.y);
    *right_edge_interpolant += right_edge_step * ((row_start as f32 + 0.5f32) - pa.pos.y);

    #[cfg(test)]
    {
        println!("draw_flat_triangle rows  : {:?},{:?}", row_start, row_end);
    }

    for row in row_start..row_end {
        // Calculate the starting and ending column indices for the current scanline:
        // - col_start is derived from the x-coordinate of left_edge_interpolant.
        // - col_end is derived from the x-coordinate of right_edge_interpolant.
        // Both values are adjusted to align with the pixel grid and clamped within valid ranges.
        let col_start = (left_edge_interpolant.pos.x - 0.5f32).ceil().max(0.0) as usize;
        let col_end = (right_edge_interpolant.pos.x - 0.5f32)
            .ceil()
            .min((drawing_buffer.col_count - 1) as f32) as usize;

        #[cfg(test)]
        {
            println!("draw_flat_triangle cols  : {:?},{:?}", col_start, col_end);
        }

        // Initialize the scanline interpolant starting at the left edge of the current scanline.
        let mut current_scanline_interpolant = left_edge_interpolant;

        // Calculate the horizontal distance between the right and left edge interpolants.
        let delta_col = right_edge_interpolant.pos.x - left_edge_interpolant.pos.x;

        // Compute the per-column interpolation step along the scanline.
        // This determines how attributes interpolate horizontally from the left to the right edge.
        let scanline_step = (*right_edge_interpolant - current_scanline_interpolant) / (delta_col);

        // Pre-step the scanline interpolant to the center of the starting column (col_start)
        // to ensure that interpolation for each pixel begins at the correct position.
        current_scanline_interpolant +=
            scanline_step * (col_start as f32 + 0.5f32 - left_edge_interpolant.pos.x);

        for col in col_start..col_end {
            // Recover the interpolated reciprocal of w (1/w) from the current scanline interpolant.
            // This value is used to correct perspective distortion in the interpolation process.
            let w = 1.0f32 / current_scanline_interpolant.pos.w;

            // Apply the perspective correction by multiplying the interpolated vertex attributes by w.
            // The result, `attr`, represents the correctly interpolated attributes (e.g., texture coordinates) for the current pixel.
            let attr = current_scanline_interpolant * w;

            // Set the pixel's depth and attribute content in the drawing buffer.
            // This function call writes the computed depth (z value), texture coordinates (uv), and other identifiers
            // into the buffer for the pixel located at (row, col).
            drawing_buffer.set_depth_content(
                row,
                col,
                current_scanline_interpolant.pos.z,
                attr.uv,
                TVec2::new(0.0, 0.0),
                prim_ref.node_id,
                prim_ref.geometry_id,
                prim_ref.material_id,
                prim_ref.primitive_id,
            );
            // Step the scanline interpolant to the next column by adding the horizontal interpolation step.
            // This updates `i_line` so that it correctly represents the vertex attributes for the next pixel.
            current_scanline_interpolant += scanline_step;
        }

        // After processing the current scanline, advance both the left and right edge interpolants
        // by adding their respective per-row steps, preparing them for the next scanline.
        left_edge_interpolant += left_edge_step;
        *right_edge_interpolant += right_edge_step;
    }
}

/// triangle drawing function
///
/// Credits to planetchili for the original code
///
///
pub fn tomato_draw_triangle<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &Vertex,
    pb: &Vertex,
    pc: &Vertex,
) {
    // sorting vertices by y (row)
    let mut p0 = pa;
    let mut p1 = pb;
    let mut p2 = pc;

    #[cfg(test)]
    {
        println!("original points  : {:?}", pa);
        println!("original points  : {:?}", pb);
        println!("original points  : {:?}", pc);
    }

    if p1.pos.y < p0.pos.y {
        std::mem::swap(&mut p0, &mut p1);
    }
    if p2.pos.y < p1.pos.y {
        std::mem::swap(&mut p1, &mut p2);
    }
    if p1.pos.y < p0.pos.y {
        std::mem::swap(&mut p0, &mut p1);
    }
    // After sorting:
    // - p0 is guaranteed to be the topmost point (smallest y value),
    // - p1 is the middle point, and
    // - p2 is the bottommost point (largest y value).

    #[cfg(test)]
    {
        println!("post y sorting points  : {:?}", p0);
        println!("post y sorting points  : {:?}", p1);
        println!("post y sorting points  : {:?}", p2);
    }

    // sort out the top and bottom triangles
    if p0.pos.y == p1.pos.y {
        // flat top
        // For the flat top triangle (when p0.pos.y == p1.pos.y):
        //   - ensures that p0 becomes the leftmost point (smallest x value)
        //     and p1 becomes the rightmost point of the top edge.
        if p1.pos.x < p0.pos.x {
            std::mem::swap(&mut p0, &mut p1);
        }

        draw_flat_top_triangle(drawing_buffer, prim_ref, p0, p1, p2);
    } else if p1.pos.y == p2.pos.y {
        // flat bottom
        // For the flat bottom triangle (when p1.pos.y == p2.pos.y):
        //   - The if statement makes sure that p1 is the leftmost point (smallest x value)
        //     and p2 is the rightmost point of the bottom edge.
        if p2.pos.x < p1.pos.x {
            std::mem::swap(&mut p1, &mut p2);
        }
        draw_flat_bottom_triangle(drawing_buffer, prim_ref, p0, p1, p2);
    } else {
        // general case where we need to split the triangle in 2
        // and draw the top and bottom triangles separately

        // calculate the new point on the edge
        let split_point = (p1.pos.y - p0.pos.y) / (p2.pos.y - p0.pos.y);
        let p_split = *p0 + ((*p2 - *p0) * split_point); // PointInfo::new_from_interpolate(p0, p2, split_point);

        #[cfg(test)]
        {
            println!("split betwen a and c : {:?}", split_point);
            println!("p_split : {:?}", p_split);
        }

        if p1.pos.x < p_split.pos.x {
            // major right
            #[cfg(test)]
            {
                println!("flat bottom  (a,b,split), then flat top (b , split , c");
            }
            draw_flat_bottom_triangle(drawing_buffer, prim_ref, p0, p1, &p_split);
            draw_flat_top_triangle(drawing_buffer, prim_ref, p1, &p_split, p2);
        } else {
            // major left
            draw_flat_bottom_triangle(drawing_buffer, prim_ref, p0, &p_split, p1);
            draw_flat_top_triangle(drawing_buffer, prim_ref, &p_split, p1, p2);
        }
    }
}

pub fn draw_flat_triangle_double_raster<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &Vertex,
    _pb: &Vertex,
    pc: &Vertex,
    left_edge_step: Vertex,
    right_edge_step: Vertex,
    right_edge_interpolant: &mut Vertex,
) {
    // --- Edge Interpolant Initialization ---
    // Create an interpolant for the left edge, starting at the apex (pa).
    let mut left_edge_interpolant = *pa;

    // --- Scanline Calculation ---
    // Determine the starting scanline (row_start) by:
    // 1. Aligning pa.pos.y to the pixel grid (subtract 0.5),
    // 2. Using ceil() to jump to the next full pixel row,
    // 3. Clamping the value to at least 0.
    let row_start = (pa.pos.y - 0.5f32).ceil().max(0.0) as usize;

    // Determine the ending scanline (row_end) based on pc.pos.y by:
    // 1. Aligning the y-coordinate similarly (subtract 0.5 and ceil()),
    // 2. Clamping the result to not exceed the drawing buffer's row count.
    let row_end = (pc.pos.y - 0.5f32)
        .ceil()
        .min(drawing_buffer.row_count as f32) as usize;

    // --- Interpolant Pre-step for Vertical Position ---
    // Advance both the left and right edge interpolants to the center of the starting scanline.
    // This "pre-step" corrects their positions by the difference between the center of the first scanline
    // (row_start + 0.5) and the original y-coordinate of pa.
    left_edge_interpolant += left_edge_step * ((row_start as f32 + 0.5f32) - pa.pos.y);
    *right_edge_interpolant += right_edge_step * ((row_start as f32 + 0.5f32) - pa.pos.y);

    #[cfg(test)]
    {
        println!("draw_flat_triangle rows  : {:?}, {:?}", row_start, row_end);
    }

    // --- Rasterization Loop Over Scanlines ---
    for row in row_start..row_end {
        // Calculate the starting and ending column indices for the current scanline:
        // - col_start is derived from the x-coordinate of left_edge_interpolant.
        // - col_end is derived from the x-coordinate of right_edge_interpolant.
        // Both values are adjusted to align with the pixel grid and clamped within valid ranges.
        let col_start = (left_edge_interpolant.pos.x - 0.5f32).ceil().max(0.0) as usize;
        let col_end = (right_edge_interpolant.pos.x - 0.5f32)
            .ceil()
            .min((drawing_buffer.col_count - 1) as f32) as usize;

        #[cfg(test)]
        {
            println!("draw_flat_triangle cols  : {:?}, {:?}", col_start, col_end);
        }

        // --- Vertical Subdivision for Non-Square (Vertical Rectangle) Pixels ---
        // In this new version, each pixel is a vertical rectangle and is subdivided into two samples:
        //   * The upper sample uses texture coordinates (UV) computed at a vertical offset of 0.25 from the top.
        //   * The lower sample uses texture coordinates (UV_1) computed at a vertical offset of 0.75 from the top.
        // The current edge interpolants represent values at the pixel center (offset 0.5).
        // Adjust the left and right edge values for both the upper and lower parts.
        let upper_left_edge = left_edge_interpolant - left_edge_step * 0.25;
        let upper_right_edge = *right_edge_interpolant - right_edge_step * 0.25;
        let lower_left_edge = left_edge_interpolant + left_edge_step * 0.25;
        let lower_right_edge = *right_edge_interpolant + right_edge_step * 0.25;

        // --- Horizontal Interpolation for Upper Part ---
        // Compute the horizontal distance and per-column interpolation step for the upper part.
        let delta_col_upper = upper_right_edge.pos.x - upper_left_edge.pos.x;
        let upper_scanline_step = (upper_right_edge - upper_left_edge) / delta_col_upper;
        // Pre-step the upper scanline interpolant to the center of the starting column.
        let mut current_upper_scanline_interpolant = upper_left_edge
            + upper_scanline_step * ((col_start as f32 + 0.5f32) - upper_left_edge.pos.x);

        // --- Horizontal Interpolation for Lower Part ---
        // Compute the horizontal distance and per-column interpolation step for the lower part.
        let delta_col_lower = lower_right_edge.pos.x - lower_left_edge.pos.x;
        let lower_scanline_step = (lower_right_edge - lower_left_edge) / delta_col_lower;
        // Pre-step the lower scanline interpolant to the center of the starting column.
        let mut current_lower_scanline_interpolant = lower_left_edge
            + lower_scanline_step * ((col_start as f32 + 0.5f32) - lower_left_edge.pos.x);

        // --- Rasterize the Current Scanline Pixel by Pixel ---
        for col in col_start..col_end {
            // --- Upper Sample Calculation ---
            // Recover the interpolated reciprocal of w for the upper part.
            // This value corrects perspective distortion for the current interpolated vertex.
            let w_upper = 1.0f32 / current_upper_scanline_interpolant.pos.w;
            // Apply perspective correction to obtain the vertex attributes for the upper sample.
            let upper_attr = current_upper_scanline_interpolant * w_upper;

            // --- Lower Sample Calculation ---
            // Recover the interpolated reciprocal of w for the lower part.
            let w_lower = 1.0f32 / current_lower_scanline_interpolant.pos.w;
            // Apply perspective correction to obtain the vertex attributes for the lower sample.
            let lower_attr = current_lower_scanline_interpolant * w_lower;

            // Write the computed pixel data into the drawing buffer.
            // - The depth (z value) is taken from the interpolated value (assumed similar for both samples).
            // - `upper_attr.uv` provides the UV coordinates for the upper part of the rectangle.
            // - `lower_attr.uv` provides the UV_1 coordinates for the lower part of the rectangle.
            drawing_buffer.set_depth_content(
                row,
                col,
                current_upper_scanline_interpolant.pos.z,
                upper_attr.uv,
                lower_attr.uv,
                prim_ref.node_id,
                prim_ref.geometry_id,
                prim_ref.material_id,
                prim_ref.primitive_id,
            );

            // Advance the horizontal interpolants to the next column.
            current_upper_scanline_interpolant += upper_scanline_step;
            current_lower_scanline_interpolant += lower_scanline_step;
        }

        // --- Advance Vertical Edge Interpolants ---
        // After processing the current scanline, advance both the left and right edge interpolants
        // by adding their respective per-row steps, preparing them for the next scanline.
        left_edge_interpolant += left_edge_step;
        *right_edge_interpolant += right_edge_step;
    }
}

#[cfg(test)]
mod test_raster_duo_triangle {
    use approx::assert_abs_diff_eq;
    use nalgebra_glm::{Vec2, Vec3, Vec4};

    use crate::{drawbuffer::drawbuffer::DrawBuffer, raster::primitivbuffer::PrimitivReferences};

    use super::{tomato_draw_triangle, Vertex};

    #[test]
    fn triangle_major_right_a_b_c() {
        let (pa, pb, pc) = make_points_major_right();
        let (mut drawing_buffer, prim_ref) = setup_drawing();

        tomato_draw_triangle(&mut drawing_buffer, &prim_ref, &pa, &pb, &pc);

        assert_eq!(drawing_buffer.get_depth_buffer_cell(0, 0).depth[0], 10.0); // not blit

        // near pa
        assert_eq!(drawing_buffer.get_depth_buffer_cell(0, 6).depth[0], 0.0); //

        let uva = drawing_buffer
            .get_pix_buffer_content_at_row_col(0, 6, 0)
            .uv
            .xy();
        assert_abs_diff_eq!(uva.x, pa.uv.x, epsilon = 0.15);
        assert_abs_diff_eq!(uva.y, pa.uv.y, epsilon = 0.15);

        // blit near pb
        assert_eq!(drawing_buffer.get_depth_buffer_cell(3, 3).depth[0], 0.0);
        let uvb = drawing_buffer
            .get_pix_buffer_content_at_row_col(3, 3, 0)
            .uv
            .xy();
        assert_abs_diff_eq!(uvb.x, pb.uv.x, epsilon = 0.15);
        assert_abs_diff_eq!(uvb.y, pb.uv.y, epsilon = 0.25);

        // near pc
        assert_eq!(drawing_buffer.get_depth_buffer_cell(6, 5).depth[0], 0.0); // blit near pc
        let uvc = drawing_buffer
            .get_pix_buffer_content_at_row_col(6, 5, 0)
            .uv
            .xy();
        assert_abs_diff_eq!(uvc.x, pc.uv.x, epsilon = 0.25);
        assert_abs_diff_eq!(uvc.y, pc.uv.y, epsilon = 0.25);

        // center point
        assert_eq!(drawing_buffer.get_depth_buffer_cell(3, 5).depth[0], 0.0); // blit in middle
        let uvd = drawing_buffer
            .get_pix_buffer_content_at_row_col(3, 5, 0)
            .uv
            .xy();
        assert_abs_diff_eq!(uvd.x, 0.5, epsilon = 0.25);
        assert_abs_diff_eq!(uvd.y, 0.5, epsilon = 0.25);
    }
    #[test]
    fn triangle_major_left_a_b_c() {
        let (pa, pb, pc) = make_points_major_left();
        let (mut drawing_buffer, prim_ref) = setup_drawing();

        tomato_draw_triangle(&mut drawing_buffer, &prim_ref, &pa, &pb, &pc);

        assert_eq!(drawing_buffer.get_depth_buffer_cell(0, 0).depth[0], 10.0); // not blit

        assert_eq!(drawing_buffer.get_depth_buffer_cell(1, 3).depth[0], 0.0); // blit near pa
        assert_eq!(drawing_buffer.get_depth_buffer_cell(4, 4).depth[0], 0.0); // blit near pb
        assert_eq!(drawing_buffer.get_depth_buffer_cell(3, 5).depth[0], 0.0); // blit near pc

        assert_eq!(drawing_buffer.get_depth_buffer_cell(3, 4).depth[0], 0.0); // blit in middle
    }

    fn make_points_major_right() -> (Vertex, Vertex, Vertex) {
        let pa = Vertex::new(
            Vec4::new(7.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        let pb = Vertex::new(
            Vec4::new(2.0, 4.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 1.0),
        );
        let pc = Vertex::new(
            Vec4::new(6.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(1.0, 1.0),
        );
        (pa, pb, pc)
    }

    fn make_points_major_left() -> (Vertex, Vertex, Vertex) {
        let pa = Vertex::new(
            Vec4::new(2.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        let pb = Vertex::new(
            Vec4::new(4.0, 6.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        let pc = Vertex::new(
            Vec4::new(7.0, 3.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        (pa, pb, pc)
    }

    fn setup_drawing() -> (DrawBuffer<2, f32>, PrimitivReferences) {
        (
            DrawBuffer::<2, f32>::new(8, 10, 10.0),
            PrimitivReferences {
                geometry_id: 1,
                material_id: 2,
                node_id: 3,
                primitive_id: 0,
            },
        )
    }
}
#[cfg(test)]
mod test_raster_mono_triangle {
    use nalgebra_glm::{Vec2, Vec3, Vec4};

    use crate::{drawbuffer::drawbuffer::DrawBuffer, raster::primitivbuffer::PrimitivReferences};

    use super::{tomato_draw_triangle, Vertex};

    #[test]
    fn triangle_case_flat_bottom_a_b_c() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(8, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };

        let pa = Vertex::new(
            Vec4::new(0.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pb = Vertex::new(
            Vec4::new(0.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pc = Vertex::new(
            Vec4::new(9.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        tomato_draw_triangle(&mut drawing_buffer, &prim_ref, &pa, &pb, &pc);

        // getting cell info at all corners
        let cell_info_0 = drawing_buffer.get_depth_buffer_cell(0, 0);
        let cell_info_1 = drawing_buffer.get_depth_buffer_cell(0, 9);
        let cell_info_2 = drawing_buffer.get_depth_buffer_cell(6, 7);
        let cell_info_3 = drawing_buffer.get_depth_buffer_cell(6, 0);

        assert_eq!(cell_info_0.depth[0], 0.0); // pa
        assert_eq!(cell_info_1.depth[0], 10.0); // not blit
        assert_eq!(cell_info_2.depth[0], 0.0); // pc
        assert_eq!(cell_info_3.depth[0], 0.0); // this is pb
    }
    #[test]
    fn triangle_case_flat_bottom_b_c_a() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(8, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };

        let pa = Vertex::new(
            Vec4::new(0.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pb = Vertex::new(
            Vec4::new(0.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pc = Vertex::new(
            Vec4::new(9.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        tomato_draw_triangle(&mut drawing_buffer, &prim_ref, &pb, &pc, &pa);

        // getting cell info at all corners
        let cell_info_0 = drawing_buffer.get_depth_buffer_cell(0, 0);
        let cell_info_1 = drawing_buffer.get_depth_buffer_cell(0, 9);
        let cell_info_2 = drawing_buffer.get_depth_buffer_cell(6, 7);
        let cell_info_3 = drawing_buffer.get_depth_buffer_cell(6, 0);

        assert_eq!(cell_info_0.depth[0], 0.0); // pa
        assert_eq!(cell_info_1.depth[0], 10.0); // not blit
        assert_eq!(cell_info_2.depth[0], 0.0); // pc
        assert_eq!(cell_info_3.depth[0], 0.0); // this is pb
    }
    #[test]
    fn triangle_case_flat_bottom_c_a_b() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(8, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };

        let pa = Vertex::new(
            Vec4::new(0.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pb = Vertex::new(
            Vec4::new(0.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pc = Vertex::new(
            Vec4::new(9.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        tomato_draw_triangle(&mut drawing_buffer, &prim_ref, &pc, &pa, &pb);

        // getting cell info at all corners
        let cell_info_0 = drawing_buffer.get_depth_buffer_cell(0, 0);
        let cell_info_1 = drawing_buffer.get_depth_buffer_cell(0, 9);
        let cell_info_2 = drawing_buffer.get_depth_buffer_cell(6, 7);
        let cell_info_3 = drawing_buffer.get_depth_buffer_cell(6, 0);

        assert_eq!(cell_info_0.depth[0], 0.0); // pa
        assert_eq!(cell_info_1.depth[0], 10.0); // not blit
        assert_eq!(cell_info_2.depth[0], 0.0); // pc
        assert_eq!(cell_info_3.depth[0], 0.0); // this is pb
    }

    #[test]
    fn triangle_case_flat_top_a_b_c() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(8, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };

        let pa = Vertex::new(
            Vec4::new(0.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pb = Vertex::new(
            Vec4::new(9.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pc = Vertex::new(
            Vec4::new(9.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        tomato_draw_triangle(&mut drawing_buffer, &prim_ref, &pa, &pb, &pc);

        // getting cell info at all corners
        let cell_info_0 = drawing_buffer.get_depth_buffer_cell(0, 1);
        let cell_info_1 = drawing_buffer.get_depth_buffer_cell(0, 8);
        let cell_info_2 = drawing_buffer.get_depth_buffer_cell(6, 8);
        let cell_info_3 = drawing_buffer.get_depth_buffer_cell(6, 0);

        assert_eq!(cell_info_0.depth[0], 0.0); // pa
        assert_eq!(cell_info_1.depth[0], 0.0); // pc
        assert_eq!(cell_info_2.depth[0], 0.0); // pc
        assert_eq!(cell_info_3.depth[0], 10.0); // this is pb
    }
    #[test]
    fn triangle_case_flat_top_b_c_a() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(8, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };

        let pa = Vertex::new(
            Vec4::new(0.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pb = Vertex::new(
            Vec4::new(9.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pc = Vertex::new(
            Vec4::new(9.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        tomato_draw_triangle(&mut drawing_buffer, &prim_ref, &pb, &pc, &pa);

        // getting cell info at all corners
        let cell_info_0 = drawing_buffer.get_depth_buffer_cell(0, 1);
        let cell_info_1 = drawing_buffer.get_depth_buffer_cell(0, 8);
        let cell_info_2 = drawing_buffer.get_depth_buffer_cell(6, 8);
        let cell_info_3 = drawing_buffer.get_depth_buffer_cell(6, 0);

        assert_eq!(cell_info_0.depth[0], 0.0); // pa
        assert_eq!(cell_info_1.depth[0], 0.0); // pc
        assert_eq!(cell_info_2.depth[0], 0.0); // pc
        assert_eq!(cell_info_3.depth[0], 10.0); // this is pb
    }
    #[test]
    fn triangle_case_flat_top_c_a_b() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(8, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };

        let pa = Vertex::new(
            Vec4::new(0.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pb = Vertex::new(
            Vec4::new(9.0, 7.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );
        let pc = Vertex::new(
            Vec4::new(9.0, 0.0, 0.0, 1.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec2::new(0.0, 0.0),
        );

        tomato_draw_triangle(&mut drawing_buffer, &prim_ref, &pc, &pa, &pb);

        // getting cell info at all corners
        let cell_info_0 = drawing_buffer.get_depth_buffer_cell(0, 1);
        let cell_info_1 = drawing_buffer.get_depth_buffer_cell(0, 8);
        let cell_info_2 = drawing_buffer.get_depth_buffer_cell(6, 8);
        let cell_info_3 = drawing_buffer.get_depth_buffer_cell(6, 0);

        assert_eq!(cell_info_0.depth[0], 0.0); // pa
        assert_eq!(cell_info_1.depth[0], 0.0); // pc
        assert_eq!(cell_info_2.depth[0], 0.0); // pc
        assert_eq!(cell_info_3.depth[0], 10.0); // this is pb
    }
}
