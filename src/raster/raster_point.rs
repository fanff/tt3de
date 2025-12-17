use nalgebra_glm::Vec3;

use crate::drawbuffer::drawbuffer::DrawBuffer;

use super::{
    primitivbuffer::{PointInfo, PrimitivReferences},
    set_pixel_double_weights,
};

pub fn raster_point_info<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    point: &PointInfo<f32>,
) {
    if point.row >= drawing_buffer.row_count || point.col >= drawing_buffer.col_count {
        return;
    }
    set_pixel_double_weights(
        prim_ref,
        drawing_buffer,
        point.depth(),
        Vec3::new(0.0, 0.0, 1.0),
        point.col,
        point.row,
        1.0,
        0.0,
        0.5,
        0.5,
    )
}
