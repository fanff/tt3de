use nalgebra_glm::Vec4;

use crate::drawbuffer::drawbuffer::DrawBuffer;

use super::{
    barycentric_coord, barycentric_coord_shift, max_3_int, min_2_int, min_3_int,
    primitivbuffer::{PointInfo, PrimitivReferences},
    set_pixel_double_weights,
};

pub fn raster_triangl<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &PointInfo<f32>,
    pb: &PointInfo<f32>,
    pc: &PointInfo<f32>,
) {
    let min_col = min_3_int(pa.col, pb.col, pc.col); // min3int(axi, bxi, cxi);
    let mut max_col = max_3_int(pa.col, pb.col, pc.col); // min3int(ayi, byi, cyi);

    let min_row = min_3_int(pa.row, pb.row, pc.row); // max3int(axi, bxi, cxi);
    let mut max_row = max_3_int(pa.row, pb.row, pc.row); // max3int(ayi, byi, cyi);

    // Clip against screen bounds
    // useless in usize space :)
    // minX = max_2_int(minX, 0);
    // minY = max_2_int(minY, 0);

    max_col = min_2_int(max_col, drawing_buffer.col_count);
    max_row = min_2_int(max_row, drawing_buffer.row_count);

    for curr_row in min_row..max_row {
        for curr_col in min_col..max_col {
            let (w0, w1, w2) = barycentric_coord(pa, pb, pc, curr_row, curr_col);
            let depth = pa.p.z * w0 + pb.p.z * w1 + pc.p.z * w2;

            //vec3_bary_coord(
            //    &original_pa.xyz(),
            //    &original_pb.xyz(),
            //    &original_pc.xyz(),
            //    curr_row,
            //    curr_col,
            //    depth,
            //);

            if w0 >= 0.0 && w1 >= 0.0 && w2 >= 0.0 {
                let (w0_alt, w1_alt, w2_alt) =
                    barycentric_coord_shift(pa, pb, pc, 0.49, curr_row, curr_col);

                set_pixel_double_weights(
                    prim_ref,
                    drawing_buffer,
                    depth,
                    curr_col,
                    curr_row,
                    w0,
                    w1,
                    w2,
                    w0_alt,
                    w1_alt,
                    w2_alt,
                )
            }
        }
    }
}

#[cfg(test)]
mod test_raster_triangle {
    use crate::{
        drawbuffer::drawbuffer::DrawBuffer,
        raster::primitivbuffer::{PointInfo, PrimitivReferences},
    };

    use super::raster_triangl;

    // test raster all absolute zero side triangles
    #[test]
    fn zero_size_triange() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(8, 10, 10.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };

        for row in 0..8 {
            for col in 0..10 {
                let pa = PointInfo::new(row as f32, col as f32, 1.0);
                let pb = PointInfo::new(row as f32, col as f32, 3.0);
                let pc = PointInfo::new(row as f32, col as f32, 3.0);
                raster_triangl(&mut drawing_buffer, &prim_ref, &pa, &pb, &pc);

                // get cell bellow the triangle
                let content_at_location_layer0 =
                    drawing_buffer.get_pix_buffer_content_at_row_col(row, col, 0);
                let cell = drawing_buffer.get_depth_buffer_cell(row, col);
            }
        }
    }
}
