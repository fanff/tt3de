use nalgebra_glm::{clamp, floor, max, pi, Vec1, Vec2, Vec3};

use crate::{
    drawbuffer::drawbuffer::{CanvasCell, Color, DepthBufferCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveElements,
    texturebuffer::{texture_buffer::TextureBuffer, RGBA},
    vertexbuffer::UVBuffer,
};

use super::RenderMatTrait;

#[derive(Clone)]
pub struct DebugDepth {
    pub glyph_idx: u8,
}
impl DebugDepth {
    pub fn new(glyph_idx: u8) -> Self {
        Self { glyph_idx }
    }
}
impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize, const UVCOUNT: usize>
    RenderMatTrait<TEXTURE_BUFFER_SIZE, DEPTHLAYER, UVCOUNT> for DebugDepth
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        depth_layer: usize,
        _pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements,
        _texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        _uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        cell.glyph = self.glyph_idx;

        let d = depth_cell.get_depth(depth_layer);

        let dd = (clamp(&Vec1::new(d), 0.001, 1.0) * 255.0);
        let shade = dd.x as u8;
        cell.front_color = Color::new(shade, 0, 0, 255);
        cell.back_color = Color::new(shade, 0, 0, 255);
    }
}

#[derive(Clone)]
pub struct DebugUV {
    pub glyph_idx: u8,
}
impl DebugUV {
    pub fn new(glyph_idx: u8) -> Self {
        Self { glyph_idx }
    }
}
impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize, const UVCOUNT: usize>
    RenderMatTrait<TEXTURE_BUFFER_SIZE, DEPTHLAYER, UVCOUNT> for DebugUV
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        _depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        depth_layer: usize,
        _pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements,
        _texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        cell.glyph = self.glyph_idx;

        cell.front_color = Color::new_opaque_from_vec2(&_pixinfo.uv);
        cell.back_color = Color::new_opaque_from_vec2(&_pixinfo.uv_1);
    }
}
