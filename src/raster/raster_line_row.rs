use nalgebra_glm::{Vec2, Vec3};

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
            pa.p.z,
            Vec3::new(0.0, 0.0, 1.0),
            pa.col,
            pa.row,
            1.0,
            0.0,
            1.0,
            0.0,
        );
    } else if pa.row > pb.row {
        for row in pb.row..=pa.row {
            // calculate barycentric factor
            let ratio = ((row as f32) - (pb.row as f32)) / ((pa.row as f32) - (pb.row as f32));
            let depth = pb.p.z * (1.0 - ratio) + pa.p.z * ratio;
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                Vec3::new(0.0, 0.0, 1.0),
                pa.col,
                row,
                ratio,
                1.0 - ratio,
                ratio,
                1.0 - ratio,
            );
        }
    } else {
        for row in pa.row..=pb.row {
            // calculate barycentric factor
            let ratio = (row - pa.row) as f32 / (pb.row - pa.row) as f32;
            let depth = pa.p.z * (1.0 - ratio) + pb.p.z * ratio;
            set_pixel_double_weights(
                prim_ref,
                drawing_buffer,
                depth,
                Vec3::new(0.0, 0.0, 1.0),
                pa.col,
                row,
                1.0 - ratio,
                ratio,
                1.0 - ratio,
                ratio,
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
        let depth = pa.p.z * (1.0 - ratio_caped) + pb.p.z * ratio_caped;
        set_pixel_double_weights(
            prim_ref,
            drawing_buffer,
            depth,
            Vec3::new(0.0, 0.0, 1.0),
            col_rounder_as_usize,
            row,
            1.0 - ratio_caped,
            ratio_caped,
            1.0 - ratio_caped,
            ratio_caped,
        );
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
        raster_line_along_rows(&mut drawing_buffer, &prim_ref, &pa, &pb);
        let cell_origin = drawing_buffer.get_depth_buffer_cell(0, 0);

        // depth is still origin,
        assert_eq!(cell_origin.depth, [100.0, 100.0]);

        let cell_55 = drawing_buffer.get_depth_buffer_cell(5, 5);

        // depth is changed
        assert_eq!(cell_55.depth, [0.0, 100.0]);
    }
}
