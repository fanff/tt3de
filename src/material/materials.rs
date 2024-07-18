use nalgebra_glm::Vec2;

use crate::drawbuffer::drawbuffer::{CanvasCell, Color, DepthBufferCell, PixInfo};
use crate::primitivbuffer::primitivbuffer::PrimitiveElements;
use crate::texturebuffer::texture_buffer::TextureBuffer;

use crate::vertexbuffer::UVBuffer;

use super::super::texturebuffer::RGBA;

use super::{apply_noise, noise_mat::*, DebugDepth, DebugUV, Texture};

#[derive(Clone)]
pub enum Material {
    DoNothing {},
    Texture(Texture),
    StaticColor {
        front_color: RGBA,
        back_color: RGBA,
        glyph_idx: u8,
    },
    Noise {
        noise: NoiseMaterial,
        glyph_idx: u8,
    },

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
        depth_layer: usize,
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
        depth_layer: usize,
        pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        match self {
            Material::DoNothing {} => {}
            Material::Texture(t) => t.render_mat(
                cell,
                depth_cell,
                depth_layer,
                pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            ),
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
                let uv = pixinfo.uv.xy();

                let valuefront = apply_noise(noise, pixinfo, uv.x, uv.y);

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

            Material::DebugDepth(m) => m.render_mat(
                cell,
                depth_cell,
                depth_layer,
                pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            ),
            Material::DebugUV(m) => m.render_mat(
                cell,
                depth_cell,
                depth_layer,
                pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            ),
        }
    }
} // juste un maxi match pour l'implem
