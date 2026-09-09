use tt3de_core::drawbuffer::drawbuffer::DrawBuffer;

fn main() {
    let buffer = DrawBuffer::<1, f32>::new(24, 80, f32::INFINITY, false, false);
    println!(
        "created a {}x{} render buffer",
        buffer.row_count, buffer.col_count
    );
}
