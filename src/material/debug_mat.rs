use nalgebra_glm::{floor, max, Vec3};

use crate::{
    drawbuffer::drawbuffer::{CanvasCell, Color, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveElements,
    texturebuffer::{texture_buffer::TextureBuffer, RGBA},
    vertexbuffer::UVBuffer,
};

use super::RenderMatTrait;

#[derive(Clone)]
pub struct DebugWeight {
    pub glyph_idx: u8,
}
impl DebugWeight {
    pub fn new() -> Self {
        Self { glyph_idx: 0 }
    }
}
impl<const SIZE: usize, const UVCOUNT: usize> RenderMatTrait<SIZE, UVCOUNT> for DebugWeight {
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements<f32>,
        _texture_buffer: &TextureBuffer<SIZE>,
        _uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        cell.glyph = self.glyph_idx;
        let w = max(&floor(&(pixinfo.w * 256.0)), 0.0);

        cell.front_color = Color::new_opaque_from_vec3(&pixinfo.w);
        cell.back_color = Color::new_opaque_from_vec3(&pixinfo.w);
    }
}
