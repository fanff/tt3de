use crate::drawbuffer::drawbuffer::DrawBuffer;

use super::{
    primitivbuffer::{PointInfo, PrimitivReferences}, raster_horizontal_line, set_pixel_double_weights
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
                1.0 - ratio,
                ratio,
                0.0,
                1.0 - ratio,
                ratio,
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
pub fn raster_line_along_rows<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
) {
    if pa.row == pb.row {
        raster_horizontal_line(drawing_buffer, prim_ref, pa, pb);
    } else if pa.col == pb.col {
        raster_vertical_line(drawing_buffer, prim_ref, pa, pb);
    } else if pa.row > pb.row {
        let line_row_len = pa.row as f32 - pb.row as f32;
        let line_col_len = pa.col as f32 - pb.col as f32;
        let line_l2_len = (line_row_len.powi(2) + line_col_len.powi(2)).sqrt();
        let direction_factor = line_col_len / line_row_len;
        let intercept = pa.col as f32 - direction_factor * pa.row as f32;

        for row in pb.row..=pa.row {
            // calculate x based on direction_factor and intercept
            let col = direction_factor * (row as f32) + intercept;

            // calculate barycentric factor using L2 norm of (row, col) and pa
            let ratio = ((row as f32 - pa.row as f32).powi(2) + (col - pa.col as f32).powi(2))
                .sqrt()
                / line_l2_len;
            let depth = pa.depth * (1.0 - ratio) + pb.depth * ratio;

            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                col as usize,
                row,
                1.0 - ratio,
                ratio,
                0.0,
                1.0 - ratio,
                ratio,
                0.0,
            );
        }
    } else {
        let line_row_len = pb.row as f32 - pa.row as f32;
        let line_col_len = pb.col as f32 - pa.col as f32;
        let line_l2_len = (line_row_len.powi(2) + line_col_len.powi(2)).sqrt();
        let direction_factor = line_col_len / line_row_len;
        let intercept = pa.col as f32 - direction_factor * pa.row as f32;

        for row in pa.row..=pb.row {
            // calculate x based on direction_factor and intercept
            let col = direction_factor * (row as f32) + intercept;

            // calculate barycentric factor using L2 norm of (row, col) and pa
            let ratio = ((row as f32 - pa.row as f32).powi(2) + (col - pa.col as f32).powi(2))
                .sqrt()
                / line_l2_len;
            let depth = pa.depth * (1.0 - ratio) + pb.depth * ratio;

            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                col as usize,
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


#[cfg(test)]
pub mod test_raster_line_along_rows {
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
