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
    if (pa.row == pb.row) && (pa.row == pc.row) {
        return;
    }
    if (pa.col == pb.col) && (pa.col == pc.col) {
        return;
    }

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

            if w0 >= 0.0 && w1 >= 0.0 && w2 >= 0.0 {
                let (w0_alt, w1_alt, w2_alt) =
                    barycentric_coord_shift(pa, pb, pc, 0.49, curr_row, curr_col);

                let depth = pa.depth * w0 + pb.depth * w1 + pc.depth * w2;

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
