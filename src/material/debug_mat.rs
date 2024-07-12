use nalgebra_glm::{clamp, floor, max, pi, Vec1, Vec2, Vec3};

use crate::{
    drawbuffer::drawbuffer::{CanvasCell, Color, DepthBufferCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveElements,
    texturebuffer::{texture_buffer::TextureBuffer, RGBA},
    vertexbuffer::UVBuffer,
};

use super::{calc_uv_coord, RenderMatTrait};

#[derive(Clone)]
pub struct DebugWeight {
    pub glyph_idx: u8,
}
impl DebugWeight {
    pub fn new(glyph_idx: u8) -> Self {
        Self { glyph_idx }
    }
}
impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize, const UVCOUNT: usize>
    RenderMatTrait<TEXTURE_BUFFER_SIZE, DEPTHLAYER, UVCOUNT> for DebugWeight
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        _depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements,
        _texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        _uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        cell.glyph = self.glyph_idx;

        cell.front_color = Color::new_opaque_from_vec3(&pixinfo.w);
        cell.back_color = Color::new_opaque_from_vec3(&pixinfo.w);
    }
}

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
        _pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements,
        _texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        _uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        cell.glyph = self.glyph_idx;
        let d = depth_cell.depth[0];
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
        _pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements,
        _texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        cell.glyph = self.glyph_idx;

        let uv_vectors = uv_buffer.get_uv(primitive_element.get_uv_idx());
        let uv_point_a = uv_vectors.0;
        let uv_point_b = uv_vectors.1;
        let uv_point_c = uv_vectors.2;
        let (u, v) = calc_uv_coord(
            _pixinfo,
            (
                uv_point_a.x,
                uv_point_a.y,
                uv_point_b.x,
                uv_point_b.y,
                uv_point_c.x,
                uv_point_c.y,
            ),
            0,
        );
        let uv = &Vec2::new(u, v);
        cell.front_color = Color::new_opaque_from_vec2(&uv);
        cell.back_color = Color::new_opaque_from_vec2(&uv);
    }
}
