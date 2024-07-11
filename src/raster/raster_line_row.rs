use nalgebra_glm::Vec2;

use crate::drawbuffer::drawbuffer::DrawBuffer;

use super::{
    primitivbuffer::{PointInfo, PrimitivReferences},
    raster_horizontal_line, set_pixel_double_weights,
};

pub fn raster_vertical_line<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
) {
    if pa.row == pb.row {
        set_pixel_double_weights(
            prim_ref,
            drawing_buffer,
            pa.depth,
            pa.col,
            pa.row,
            1.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
        );
        return;
    } else if pa.row > pb.row {
        for row in pb.row..=pa.row {
            // calculate barycentric factor
            let ratio = ((row as f32) - (pb.row as f32)) / ((pa.row as f32) - (pb.row as f32));
            let depth = pb.depth * (1.0 - ratio) + pa.depth * ratio;
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                pa.col,
                row,
                ratio,
                1.0 - ratio,
                0.0,
                ratio,
                1.0 - ratio,
                0.0,
            );
        }
    } else {
        for row in pa.row..=pb.row {
            // calculate barycentric factor
            let ratio = (row - pa.row) as f32 / (pb.row - pa.row) as f32;
            let depth = pa.depth * (1.0 - ratio) + pb.depth * ratio;
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                pa.col,
                row,
                1.0 - ratio,
                ratio,
                0.0,
                1.0 - ratio,
                ratio,
                0.0,
            );
        }
    }
}
pub fn raster_line_along_rows<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
) {
    if pa.row == pb.row {
        raster_horizontal_line(drawing_buffer, prim_ref, pa, pb);
        return;
    } else if pa.col == pb.col {
        raster_vertical_line(drawing_buffer, prim_ref, pa, pb);
        return;
    }

    let pa_vec = pa.as_vec2_row_col();
    let pb_vec = pb.as_vec2_row_col();
    let pa_vec_row = pa_vec.x;
    let pa_vec_col = pa_vec.y;

    let line_vec = pb_vec - pa_vec;
    let line_vec_row: f32 = line_vec.x;
    let line_vec_col: f32 = line_vec.y;
    let line_vec_l2_len = line_vec.norm();
    let direction_factor_live_vec = (line_vec_col) / (line_vec_row);

    let intercept_line_vec = pa_vec_col - (direction_factor_live_vec * pa_vec_row);

    let iterat = if pa.row > pb.row {
        pb.row..=pa.row
    } else {
        pa.row..=pb.row
    };
    for row in iterat {
        let row_f32 = row as f32;
        // calculate y based on direction_factor and intercept
        let col = (direction_factor_live_vec * row_f32) + intercept_line_vec;
        let ratio = (Vec2::new(row_f32, col) - pa_vec).norm() / line_vec_l2_len;
        let ratio_caped = ratio.min(1.0).max(0.0);
        let col_rounded = col.round();
        let col_rounder_as_usize = col_rounded as usize;
        let depth = pa.depth * (1.0 - ratio_caped) + pb.depth * ratio_caped;
        set_pixel_double_weights(
            prim_ref,
            drawing_buffer,
            depth,
            col_rounder_as_usize,
            row,
            1.0 - ratio_caped,
            ratio_caped,
            0.0,
            1.0 - ratio_caped,
            ratio_caped,
            0.0,
        );
    }
}

#[cfg(test)]
pub mod test_raster_line_along_rows {
    use approx::abs_diff_eq;

    use crate::{
        drawbuffer::drawbuffer::DrawBuffer,
        raster::{
            primitivbuffer::{PointInfo, PrimitivReferences},
            raster_line_along_rows,
        },
    };

    macro_rules! assert_almost_eq {
        ($left:expr, $right:expr $(,)?) => {
            assert!(
                (($left - $right).abs() < 0.001),
                "left: {}, right: {}",
                $left,
                $right
            );
        };
    }

    #[test]
    fn test_raster_line_zero_len() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };
        let pa = PointInfo {
            row: 5,
            col: 5,
            depth: 0.0,
        };
        let pb = PointInfo {
            row: 5,
            col: 5,
            depth: 0.0,
        };
        raster_line_along_rows(&mut drawing_buffer, &prim_ref, &pa, &pb);
        let cell_origin = drawing_buffer.get_depth_buffer_cell(0, 0);

        // depth is still origin,
        assert_eq!(cell_origin.depth, [100.0, 100.0]);

        let cell_55 = drawing_buffer.get_depth_buffer_cell(5, 5);

        // depth is changed
        assert_eq!(cell_55.depth, [0.0, 100.0]);
    }

    #[test]
    fn test_raster_line_vertical_pa_top_pb_bottom() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };
        let pa = PointInfo {
            row: 2,
            col: 5,
            depth: 0.0,
        };
        let pb = PointInfo {
            row: 8,
            col: 5,
            depth: 1.0,
        };
        raster_line_along_rows(&mut drawing_buffer, &prim_ref, &pa, &pb);

        for row in 2..=8 {
            let cell = drawing_buffer.get_depth_buffer_cell(row, 5);

            let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(row, 5, 0);

            assert_eq!(pixinfo.node_id, prim_ref.node_id);
            assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
            assert_eq!(pixinfo.material_id, prim_ref.material_id);
            assert_eq!(pixinfo.primitive_id, prim_ref.primitive_id);

            let expected_depth = pa.depth + (pb.depth - pa.depth) * ((row - 2) as f32 / 6.0);
            assert_almost_eq!(cell.depth[0], expected_depth);
        }
    }

    #[test]
    fn test_raster_line_vertical_pa_bottom_pb_top() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };
        let pa = PointInfo {
            row: 8,
            col: 5,
            depth: 1.0,
        };
        let pb = PointInfo {
            row: 2,
            col: 5,
            depth: 0.0,
        };
        raster_line_along_rows(&mut drawing_buffer, &prim_ref, &pa, &pb);

        for row in 2..=8 {
            let cell = drawing_buffer.get_depth_buffer_cell(row, 5);

            let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(row, 5, 0);

            assert_eq!(pixinfo.node_id, prim_ref.node_id);
            assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
            assert_eq!(pixinfo.material_id, prim_ref.material_id);
            assert_eq!(pixinfo.primitive_id, prim_ref.primitive_id);

            let expected_depth = pb.depth + (pa.depth - pb.depth) * ((row - 2) as f32 / 6.0);
            assert_almost_eq!(cell.depth[0], expected_depth);
        }

        let cell_a = drawing_buffer.get_depth_buffer_cell(8, 5);
        let pix_info_a = drawing_buffer.get_pix_buffer_content_at_row_col(8, 5, 0);
        abs_diff_eq!(pix_info_a.w.x, 1.0, epsilon = 0.01);
        abs_diff_eq!(pix_info_a.w.y, 0.0, epsilon = 0.01);

        assert!(pix_info_a.w.x >= 0.0);
        assert!(pix_info_a.w.x <= 1.0);

        assert!(pix_info_a.w.y >= 0.0);
        assert!(pix_info_a.w.y <= 1.0);
    }

    #[test]
    fn test_raster_line_along_rows_topleft_to_bottomright() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };
        let pa = PointInfo {
            row: 0,
            col: 0,
            depth: 0.0,
        };
        let pb = PointInfo {
            row: 9,
            col: 9,
            depth: 1.0,
        };
        raster_line_along_rows(&mut drawing_buffer, &prim_ref, &pa, &pb);

        for i in 0..=9 {
            let cell = drawing_buffer.get_depth_buffer_cell(i, i);
            let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(i, i, 0);

            assert_eq!(pixinfo.node_id, prim_ref.node_id);
            assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
            assert_eq!(pixinfo.material_id, prim_ref.material_id);
            assert_eq!(pixinfo.primitive_id, prim_ref.primitive_id);

            let expected_depth = pa.depth + (pb.depth - pa.depth) * (i as f32 / 9.0);
            assert_almost_eq!(cell.depth[0], expected_depth);
        }
    }

    #[test]
    fn test_raster_line_along_rows_bottomright_to_topleft() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };
        let pa = PointInfo {
            row: 9,
            col: 9,
            depth: 1.0,
        };
        let pb = PointInfo {
            row: 0,
            col: 0,
            depth: 0.0,
        };
        raster_line_along_rows(&mut drawing_buffer, &prim_ref, &pa, &pb);

        for i in 0..=9 {
            let cell = drawing_buffer.get_depth_buffer_cell(i, i);
            let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(i, i, 0);

            assert_eq!(pixinfo.node_id, prim_ref.node_id);
            assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
            assert_eq!(pixinfo.material_id, prim_ref.material_id);
            assert_eq!(pixinfo.primitive_id, prim_ref.primitive_id);

            let expected_depth = pb.depth + (pa.depth - pb.depth) * (i as f32 / 9.0);
            assert_almost_eq!(cell.depth[0], expected_depth);
        }
    }
}