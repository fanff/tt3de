use crate::drawbuffer::drawbuffer::{CanvasCell, DepthBufferCell, PixInfo};
use crate::primitivbuffer::primitivbuffer::PrimitiveElements;
use crate::texturebuffer::texture_buffer::TextureBuffer;
use crate::vertexbuffer::UVBuffer;

use super::super::texturebuffer::RGBA;

use super::{apply_noise, calc_uv_coord, noise_mat::*, DebugDepth, DebugUV, DebugWeight};

#[derive(Clone)]
pub enum Material {
    DoNothing {},
    Texture {
        albedo_texture_idx: usize,
        glyph_idx: u8,
    },
    StaticColor {
        front_color: RGBA,
        back_color: RGBA,
        glyph_idx: u8,
    },
    Noise {
        noise: NoiseMaterial,
        glyph_idx: u8,
    },

    DebugWeight(DebugWeight),
    DebugDepth(DebugDepth),
    DebugUV(DebugUV),
}

pub trait RenderMatTrait<
    const TEXTURE_BUFFER_SIZE: usize,
    const DEPTHLAYER: usize,
    const UVCOUNT: usize,
>
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        uv_buffer: &UVBuffer<UVCOUNT, f32>,
    );
}

impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize, const UVCOUNT: usize>
    RenderMatTrait<TEXTURE_BUFFER_SIZE, DEPTHLAYER, UVCOUNT> for Material
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        match self {
            Material::DoNothing {} => {}
            Material::Texture {
                albedo_texture_idx,
                glyph_idx,
            } => {
                cell.glyph = *glyph_idx;

                let (uva, uvb, uvc) = uv_buffer.get_uv(primitive_element.get_uv_idx());
                let (ufront, vfront) =
                    calc_uv_coord(pixinfo, (uva.x, uva.y, uvb.x, uvb.y, uvc.x, uvc.y), 0);

                let front_rgba = texture_buffer.get_rgba_at(*albedo_texture_idx, ufront, vfront);
                cell.front_color.copy_from(&front_rgba);

                let (uback, vback) =
                    calc_uv_coord(pixinfo, (uva.x, uva.y, uvb.x, uvb.y, uvc.x, uvc.y), 1);

                let back_rgba = texture_buffer.get_rgba_at(*albedo_texture_idx, uback, vback);
                cell.front_color.copy_from(&back_rgba);
            }
            Material::StaticColor {
                front_color,
                back_color,
                glyph_idx,
            } => {
                cell.glyph = *glyph_idx;
                cell.front_color.copy_from(front_color);
                cell.back_color.copy_from(back_color);
            }
            Material::Noise { noise, glyph_idx } => {
                let (uva, uvb, uvc) = uv_buffer.get_uv(primitive_element.get_uv_idx());
                let (ufront, vfront) =
                    calc_uv_coord(pixinfo, (uva.x, uva.y, uvb.x, uvb.y, uvc.x, uvc.y), 0);

                let valuefront = apply_noise(noise, pixinfo, ufront, vfront);

                cell.glyph = *glyph_idx;

                let front_rgba = RGBA {
                    r: (valuefront * 255.0) as u8,
                    g: (valuefront * 255.0) as u8,
                    b: (valuefront * 255.0) as u8,
                    a: 255,
                };
                cell.front_color.copy_from(&front_rgba);
                cell.back_color.copy_from(&front_rgba);
            }
            Material::DebugWeight(m) => m.render_mat(
                cell,
                depth_cell,
                pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            ),
            Material::DebugDepth(m) => m.render_mat(
                cell,
                depth_cell,
                pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            ),
            Material::DebugUV(m) => m.render_mat(
                cell,
                depth_cell,
                pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            ),
        }
    }
} // juste un maxi match pour l'implem
