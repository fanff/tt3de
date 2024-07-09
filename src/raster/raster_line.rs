use crate::drawbuffer::drawbuffer::DrawBuffer;

use super::{
    primitivbuffer::{PointInfo, PrimitivReferences},
    raster_line_along_rows, raster_vertical_line, set_pixel_double_weights,
};

pub fn raster_horizontal_line<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
) {
    if pa.col == pb.col {
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
    } else if pa.col > pb.col {
        for col in pb.col..=pa.col {
            // calculate barycentric factor
            let ratio = ((col as f32) - (pb.col as f32)) / ((pa.col as f32) - (pb.col as f32));
            let depth = pb.depth * (1.0 - ratio) + pa.depth * ratio;
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                col,
                pa.row,
                1.0 - ratio,
                ratio,
                0.0,
                1.0 - ratio,
                ratio,
                0.0,
            );
        }
    } else {
        for col in pa.col..=pb.col {
            // calculate barycentric factor
            let ratio = (col - pa.col) as f32 / (pb.col - pa.col) as f32;
            let depth = pa.depth * (1.0 - ratio) + pb.depth * ratio;
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                col,
                pa.row,
                ratio,
                1.0 - ratio,
                0.0,
                ratio,
                1.0 - ratio,
                0.0,
            );
        }
    }
}

pub fn raster_line_along_columns<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
) {
    if pa.col == pb.col {
        raster_vertical_line(drawing_buffer, prim_ref, pa, pb)
    } else if pa.row == pb.row {
        raster_horizontal_line(drawing_buffer, prim_ref, pa, pb);
    } else if pa.col > pb.col {
        let line_col_len = pa.col as f32 - pb.col as f32;
        let line_row_len = pa.row as f32 - pb.row as f32;
        let line_l2_len = (line_col_len.powi(2) + line_row_len.powi(2)).sqrt();
        let direction_factor = line_col_len / line_row_len;
        let intercept = pa.row as f32 - direction_factor * pa.col as f32;

        for col in pb.col..=pa.col {
            // calculate y based on direction_factor and intercept
            let row = direction_factor * (col as f32) + intercept;

            // calculate barycentric factor using L2 norm of (row,col) and pa
            let ratio = ((row - pa.row as f32).powi(2) + (col as f32 - pa.col as f32).powi(2))
                .sqrt()
                / line_l2_len;
            let depth = pa.depth * (1.0 - ratio) + pb.depth * ratio;

            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                col,
                row as usize,
                1.0 - ratio,
                ratio,
                0.0,
                1.0 - ratio,
                ratio,
                0.0,
            );
        }
    } else {
        let line_col_len = pa.col as f32 - pb.col as f32;
        let line_row_len = pa.row as f32 - pb.row as f32;
        let line_l2_len = (line_col_len.powi(2) + line_row_len.powi(2)).sqrt();
        let direction_factor = line_col_len / line_row_len;
        let intercept = pa.row as f32 - direction_factor * pa.col as f32;

        for col in pa.col..=pb.col {
            // calculate y based on direction_factor and intercept
            let row = direction_factor * (col as f32) + intercept;

            // calculate barycentric factor using L2 norm of (row,col) and pa
            let ratio = ((row - pa.row as f32).powi(2) + (col as f32 - pa.col as f32).powi(2))
                .sqrt()
                / line_l2_len;
            let depth = pa.depth * (1.0 - ratio) + pb.depth * ratio;
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                col,
                row as usize,
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

#[cfg(test)]
pub mod test_raster_line_along_columns {
    use crate::{
        drawbuffer::drawbuffer::DrawBuffer,
        raster::{
            primitivbuffer::{PointInfo, PrimitivReferences},
            raster_line_along_columns,
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
        raster_line_along_columns(&mut drawing_buffer, &prim_ref, &pa, &pb);
        let cell_origin = drawing_buffer.get_depth_buffer_cell(0, 0);

        // depth is still origin,
        assert_eq!(cell_origin.depth, [100.0, 100.0]);

        let cell_55 = drawing_buffer.get_depth_buffer_cell(5, 5);

        // depth is changed
        assert_eq!(cell_55.depth, [0.0, 100.0]);
    }
    #[test]
    fn test_raster_line_horizontal_pa_left_pb_right() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };
        let pa = PointInfo {
            row: 5,
            col: 2,
            depth: 0.0,
        };
        let pb = PointInfo {
            row: 5,
            col: 8,
            depth: 1.0,
        };
        raster_line_along_columns(&mut drawing_buffer, &prim_ref, &pa, &pb);

        for col in 2..=8 {
            let cell = drawing_buffer.get_depth_buffer_cell(5, col);

            let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(5, col, 0);

            assert_eq!(pixinfo.node_id, prim_ref.node_id);
            assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
            assert_eq!(pixinfo.material_id, prim_ref.material_id);
            assert_eq!(pixinfo.primitive_id, prim_ref.primitive_id);

            let expected_depth = pa.depth + (pb.depth - pa.depth) * ((col - 2) as f32 / 6.0);
            assert_almost_eq!(cell.depth[0], expected_depth);
        }
    }

    #[test]
    fn test_raster_line_horizontal_pa_right_pb_left() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };
        let pa = PointInfo {
            row: 5,
            col: 8,
            depth: 1.0,
        };
        let pb = PointInfo {
            row: 5,
            col: 2,
            depth: 0.0,
        };
        raster_line_along_columns(&mut drawing_buffer, &prim_ref, &pa, &pb);

        for col in 2..=8 {
            let cell = drawing_buffer.get_depth_buffer_cell(5, col);

            let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(5, col, 0);

            assert_eq!(pixinfo.node_id, prim_ref.node_id);
            assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
            assert_eq!(pixinfo.material_id, prim_ref.material_id);
            assert_eq!(pixinfo.primitive_id, prim_ref.primitive_id);

            let expected_depth = pb.depth + (pa.depth - pb.depth) * ((col - 2) as f32 / 6.0);
            assert_almost_eq!(cell.depth[0], expected_depth);
        }
    }

    #[test]
    fn test_raster_line_along_columns_topleft_to_bottomright() {
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
        raster_line_along_columns(&mut drawing_buffer, &prim_ref, &pa, &pb);

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
    fn test_raster_line_along_columns_topright_to_leftbotton() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };
        let pa = PointInfo {
            row: 0,
            col: 5,
            depth: 0.0,
        };
        let pb = PointInfo {
            row: 5,
            col: 0,
            depth: 0.0,
        };
        raster_line_along_columns(&mut drawing_buffer, &prim_ref, &pa, &pb);
        let cell_origin = drawing_buffer.get_depth_buffer_cell(0, 0);

        // depth is still origin,
        assert_eq!(cell_origin.depth, [100.0, 100.0]);

        // at pb location
        let pbcell = drawing_buffer.get_depth_buffer_cell(5, 0);
        let pacell = drawing_buffer.get_depth_buffer_cell(0, 5);

        assert_eq!(pbcell.depth, [0.0, 100.0]);
        // at pa location
        assert_eq!(pacell.depth, [0.0, 100.0]);
    }
}

pub fn raster_line<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
) {
    // check boundaries
    if pa.row >= drawing_buffer.row_count || pa.col >= drawing_buffer.col_count {
        return;
    }
    if pb.row >= drawing_buffer.row_count || pb.col >= drawing_buffer.col_count {
        return;
    }

    let row_count = (pb.row as isize - pa.row as isize).abs();
    let col_count = (pb.col as isize - pa.col as isize).abs();

    if row_count > col_count {
        raster_line_along_rows(drawing_buffer, prim_ref, pa, pb);
    } else {
        raster_line_along_columns(drawing_buffer, prim_ref, pa, pb);
    }
}
