use crate::drawbuffer::drawbuffer::DrawBuffer;

use super::{
    primitivbuffer::{PointInfo, PrimitivReferences},
    raster_line_along_columns, raster_line_along_rows,
};

pub fn raster_line<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
) {
    let row_count = (pb.row as isize - pa.row as isize).abs();
    let col_count = (pb.col as isize - pa.col as isize).abs();

    if row_count > col_count {
        raster_line_along_rows(drawing_buffer, prim_ref, pa, pb);
    } else {
        raster_line_along_columns(drawing_buffer, prim_ref, pa, pb);
    }
}

#[cfg(test)]
mod tests {
    use approx::abs_diff_eq;

    use super::*;

    #[test]
    fn test_raster_line() {
        // Test case 1: pa.row > drawing_buffer.row_count
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };
        let pa = PointInfo::new(0.0, 1.0, 1.0);
        let pb = PointInfo::new(8.0, 9.0, 3.0);

        raster_line(&mut drawing_buffer, &prim_ref, &pa, &pb);

        // Assert that raster_line_along_columns is called
    }
    #[test]
    fn test_raster_line_horizontal() {
        // Test case 1: pa.row > drawing_buffer.row_count
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };
        let pa = PointInfo::new(0.0, 0.0, 1.0);
        let pb = PointInfo::new(0.0, 1.0, 3.0);
        raster_line(&mut drawing_buffer, &prim_ref, &pa, &pb);

        // assert the line is rastered
        // get the point at 0, 0
        let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(0, 0, 0);
        assert_eq!(pixinfo.node_id, prim_ref.node_id);
        assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo.material_id, prim_ref.material_id);

        assert_eq!(pixinfo.uv.x, 1.0);
        assert_eq!(pixinfo.uv.y, 0.0);

        let cell = drawing_buffer.get_depth_buffer_cell(0, 0);
        assert_eq!(cell.depth[0], 1.0);
    }

    #[test]
    fn test_raster_line_vertical() {
        // Test case 1: pa.row > drawing_buffer.row_count
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };
        let pa = PointInfo::new(0.0, 0.0, 1.0);
        let pb = PointInfo::new(1.0, 0.0, 3.0);
        raster_line(&mut drawing_buffer, &prim_ref, &pa, &pb);

        // assert the line is rastered
        // get the point at 0, 0
        let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(0, 0, 0);
        assert_eq!(pixinfo.node_id, prim_ref.node_id);
        assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo.material_id, prim_ref.material_id);

        assert_eq!(pixinfo.uv.x, 1.0);
        assert_eq!(pixinfo.uv.y, 0.0);

        let cell = drawing_buffer.get_depth_buffer_cell(0, 0);
        assert_eq!(cell.depth[0], 1.0);
    }

    #[test]
    fn test_raster_line_problem1() {
        // seems like sometime, the final point is not reached
        // Test case 1: pa.row > drawing_buffer.row_count
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };
        let pa = PointInfo::new(0.0, 1.0, 1.0);
        let pb = PointInfo::new(5.0, 7.0, 3.0);
        raster_line(&mut drawing_buffer, &prim_ref, &pa, &pb);

        // assert the line is rastered
        // get the point at 0, 0
        let pixinfo_a = drawing_buffer.get_pix_buffer_content_at_row_col(0, 1, 0);
        assert_eq!(pixinfo_a.node_id, prim_ref.node_id);
        assert_eq!(pixinfo_a.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo_a.material_id, prim_ref.material_id);

        assert_eq!(pixinfo_a.uv.x, 1.0);
        assert_eq!(pixinfo_a.uv.y, 0.0);

        let cell_a = drawing_buffer.get_depth_buffer_cell(0, 1);
        assert_eq!(cell_a.depth[0], 1.0);

        let pixinfo_b = drawing_buffer.get_pix_buffer_content_at_row_col(5, 7, 0);
        assert_eq!(pixinfo_b.node_id, prim_ref.node_id);
        assert_eq!(pixinfo_b.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo_b.material_id, prim_ref.material_id);

        let _ = abs_diff_eq!(pixinfo_b.uv.x, 0.0, epsilon = 0.01);
        let _ = abs_diff_eq!(pixinfo_b.uv.y, 1.0, epsilon = 0.01);

        let cell_b = drawing_buffer.get_depth_buffer_cell(5, 7);
        let _ = abs_diff_eq!(cell_b.depth[0], 3.0, epsilon = 0.01);
    }

    #[test]
    fn test_raster_line_problem1_reversed() {
        // seems like sometime, the final point is not reached
        // Test case 1: pa.row > drawing_buffer.row_count
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };
        let pa = PointInfo::new(1.0, 0.0, 1.0);
        let pb = PointInfo::new(7.0, 5.0, 3.0);
        raster_line(&mut drawing_buffer, &prim_ref, &pa, &pb);

        // assert the line is rastered
        // get the point at 0, 0
        let pixinfo_a = drawing_buffer.get_pix_buffer_content_at_row_col(1, 0, 0);
        assert_eq!(pixinfo_a.node_id, prim_ref.node_id);
        assert_eq!(pixinfo_a.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo_a.material_id, prim_ref.material_id);

        let _ = abs_diff_eq!(pixinfo_a.uv.x, 1.0, epsilon = 0.01);
        let _ = abs_diff_eq!(pixinfo_a.uv.y, 0.0, epsilon = 0.01);

        let cell_a = drawing_buffer.get_depth_buffer_cell(1, 0);
        assert_eq!(cell_a.depth[0], 1.0);

        let pixinfo_b = drawing_buffer.get_pix_buffer_content_at_row_col(7, 5, 0);
        assert_eq!(pixinfo_b.node_id, prim_ref.node_id);
        assert_eq!(pixinfo_b.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo_b.material_id, prim_ref.material_id);

        let _ = abs_diff_eq!(pixinfo_b.uv.x, 0.0, epsilon = 0.01);
        let _ = abs_diff_eq!(pixinfo_b.uv.y, 1.0, epsilon = 0.01);

        let cell_b = drawing_buffer.get_depth_buffer_cell(7, 5);
        let _ = abs_diff_eq!(cell_b.depth[0], 3.0, epsilon = 0.01);
    }

    #[test]
    fn test_raster_line_problem2() {
        // seems like sometime, the weight are not correct
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };
        let pa = PointInfo::new(1.0, 0.0, 1.0);
        let pb = PointInfo::new(0.0, 0.0, 1.0);
        raster_line(&mut drawing_buffer, &prim_ref, &pa, &pb);

        // assert the line is rastered
        // get the point at 0, 0
        let pixinfo_a = drawing_buffer.get_pix_buffer_content_at_row_col(1, 0, 0);
        assert_eq!(pixinfo_a.node_id, prim_ref.node_id);
        assert_eq!(pixinfo_a.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo_a.material_id, prim_ref.material_id);

        assert_eq!(pixinfo_a.uv.x, 1.0);
        assert_eq!(pixinfo_a.uv.y, 0.0);

        let cell_a = drawing_buffer.get_depth_buffer_cell(1, 0);
        assert_eq!(cell_a.depth[0], 1.0);

        // test point B
        let pixinfo_b = drawing_buffer.get_pix_buffer_content_at_row_col(0, 0, 0);
        assert_eq!(pixinfo_b.node_id, prim_ref.node_id);
        assert_eq!(pixinfo_b.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo_b.material_id, prim_ref.material_id);

        let _ = abs_diff_eq!(pixinfo_b.uv.x, 0.0, epsilon = 0.01);
        let _ = abs_diff_eq!(pixinfo_b.uv.y, 1.0, epsilon = 0.01);

        let cell_b = drawing_buffer.get_depth_buffer_cell(0, 0);
        let _ = abs_diff_eq!(cell_b.depth[0], 3.0, epsilon = 0.01);
    }
}
