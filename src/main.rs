pub mod drawbuffer;
pub mod utils;
use drawbuffer::{
    drawbuffer::{create_pixinfo_init_f32, DrawBuffer, DEPTH_BUFFER_CELL_INIT_F32_2L},
    *,
};
use nalgebra_glm::Vec3;

fn main() {
    let mut db: DrawBuffer<2, f32> = DrawBuffer::new(
        10,
        10,
        DEPTH_BUFFER_CELL_INIT_F32_2L,
        create_pixinfo_init_f32(),
    );
    db.clear_depth(10.0);
    let w = Vec3::new(1.0, 2.0, 3.0);
    let w_alt = Vec3::new(1.0, 2.0, 3.0);

    db.set_depth_content(0, 0, 1.0, w, w_alt, 1, 2, 3, 4)
}
