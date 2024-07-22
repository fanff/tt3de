use crate::{drawbuffer::drawbuffer::DrawBuffer, raster::set_pixel_double_weights};

use super::{primitivbuffer::PrimitivReferences, Vertex};

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

    draw_flat_triangle(
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

    draw_flat_triangle(
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

pub fn draw_flat_triangle<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &Vertex,
    _pb: &Vertex,
    pc: &Vertex,
    dit0: Vertex,
    dit1: Vertex,
    it_edge1: &mut Vertex,
) {
    // create edge interpolant for left edge (pa )
    let mut it_edge0 = *pa;

    // calculate start and end scanlines
    let row_start = (pa.pos.y - 0.5f32).ceil().max(0.0) as usize;
    let row_end = (pc.pos.y - 0.5f32)
        .ceil()
        .min(drawing_buffer.row_count as f32) as usize;

    // do interpolant prestep
    it_edge0 += dit0 * ((row_start as f32 + 0.5f32) - pa.pos.y);
    *it_edge1 += dit1 * ((row_start as f32 + 0.5f32) - pa.pos.y);

    #[cfg(test)]
    {
        println!("draw_flat_triangle rows  : {:?},{:?}", row_start, row_end);
    }
    for row in row_start..row_end {
        // calculate start and end columns
        let col_start = (it_edge0.pos.x - 0.5f32).ceil().max(0.0) as usize;
        let col_end = (it_edge1.pos.x - 0.5f32)
            .ceil()
            .min((drawing_buffer.col_count - 1) as f32) as usize;

        #[cfg(test)]
        {
            println!("draw_flat_triangle cols  : {:?},{:?}", col_start, col_end);
        }

        // create scanline interpolant
        let mut i_line = it_edge0;

        // calculate delta scaline interpolant / d col
        let delta_col = it_edge1.pos.x - it_edge0.pos.x;
        let di_line = (*it_edge1 - i_line) / (delta_col);

        // prestep scanline interpolant
        i_line += di_line * (col_start as f32 + 0.5f32 - it_edge0.pos.x);

        for col in col_start..col_end {
            //recover interpolated z for interpolated 1/z
            let w = 1.0f32 / i_line.pos.w;

            let attr = i_line * w;

            // put_pixel
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                i_line.pos.z,
                col,
                row,
                attr.uv.x,
                attr.uv.y,
                0.0,
                0.0,
                //attr.normal.x,
                //attr.normal.y,
                //attr.normal.z,
            );
            // step scanline interpolant
            i_line += di_line;
        }
        it_edge0 += dit0;
        *it_edge1 += dit1;
    }
}

/// triangle drawing function
///
/// Credits to planetchili for the original code
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

    #[cfg(test)]
    {
        println!("post y sorting points  : {:?}", p0);
        println!("post y sorting points  : {:?}", p1);
        println!("post y sorting points  : {:?}", p2);
    }

    // sort out the top and bottom triangles
    if p0.pos.y == p1.pos.y {
        // flat top
        if p1.pos.x < p0.pos.x {
            std::mem::swap(&mut p0, &mut p1);
        }
        draw_flat_top_triangle(drawing_buffer, prim_ref, p0, p1, p2);
    } else if p1.pos.y == p2.pos.y {
        // flat bottom
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
