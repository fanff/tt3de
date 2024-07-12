use nalgebra_glm::Vec2;

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
            pa.p.z,
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
            let ratio_to_a = ((col as f32) - (pb.col as f32)) / ((pa.col as f32) - (pb.col as f32));
            let depth = pb.depth() * (1.0 - ratio_to_a) + pa.depth() * ratio_to_a;
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                col,
                pa.row,
                ratio_to_a,
                1.0 - ratio_to_a,
                0.0,
                ratio_to_a,
                1.0 - ratio_to_a,
                0.0,
            );
        }
    } else {
        for col in pa.col..=pb.col {
            // calculate barycentric factor
            let ratio = (col - pa.col) as f32 / (pb.col - pa.col) as f32;
            let depth = pa.depth() * (1.0 - ratio) + pb.depth() * ratio;
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
    }
}

pub fn raster_line_along_columns<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
) {
    if pa.col == pb.col {
        raster_vertical_line(drawing_buffer, prim_ref, pa, pb);
        return;
    } else if pa.row == pb.row {
        raster_horizontal_line(drawing_buffer, prim_ref, pa, pb);
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
    let direction_factor_live_vec = (line_vec_row) / (line_vec_col);

    let intercept_line_vec = pa_vec_row - (direction_factor_live_vec * pa_vec_col);

    let iterat = if pa.col > pb.col {
        pb.col..=pa.col
    } else {
        pa.col..=pb.col
    };
    for col in iterat {
        let col_f32 = col as f32;
        // calculate y based on direction_factor and intercept
        let row = (direction_factor_live_vec * col_f32) + intercept_line_vec;
        let ratio = (Vec2::new(row, col_f32) - pa_vec).norm() / line_vec_l2_len;
        let ratio_caped = ratio.min(1.0).max(0.0);
        let row_rounded = row.round();
        let row_rounder_as_usize = row_rounded as usize;
        let depth = pa.depth() * (1.0 - ratio_caped) + pb.depth() * ratio_caped;
        set_pixel_double_weights(
            prim_ref,
            drawing_buffer,
            depth,
            col,
            row_rounder_as_usize,
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
        let pa = PointInfo::new(5.0, 5.0, 0.0);
        let pb = PointInfo::new(5.0, 5.0, 0.0);
        raster_line_along_columns(&mut drawing_buffer, &prim_ref, &pa, &pb);
        let cell_origin = drawing_buffer.get_depth_buffer_cell(0, 0);

        // depth is still origin,
        assert_eq!(cell_origin.depth, [100.0, 100.0]);

        let cell_55 = drawing_buffer.get_depth_buffer_cell(5, 5);

        // depth is changed
        assert_eq!(cell_55.depth, [0.0, 100.0]);
    }
}
