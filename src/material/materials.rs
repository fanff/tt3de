use crate::drawbuffer::drawbuffer::{CanvasCell, PixInfo};
use crate::primitivbuffer::primitivbuffer::PrimitiveElements;
use crate::texturebuffer::texture_buffer::TextureBuffer;
use crate::vertexbuffer::UVBuffer;

use super::super::texturebuffer::RGBA;

use super::{noise_mat::*, DebugWeight};

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
}

pub trait RenderMatTrait<const SIZE: usize, const UVCOUNT: usize> {
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements<f32>,
        texture_buffer: &TextureBuffer<SIZE>,
        uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        // Default implem  ?
    }
}

impl<const SIZE: usize, const UVCOUNT: usize> RenderMatTrait<SIZE, UVCOUNT> for Material {
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements<f32>,
        texture_buffer: &TextureBuffer<SIZE>,
        uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        match self {
            Material::DoNothing {} => todo!(),
            Material::Texture {
                albedo_texture_idx,
                glyph_idx,
            } => todo!(),
            Material::StaticColor {
                front_color,
                back_color,
                glyph_idx,
            } => todo!(),
            Material::Noise { noise, glyph_idx } => todo!(),
            Material::DebugWeight(m) => {
                m.render_mat(cell, pixinfo, primitive_element, texture_buffer, uv_buffer)
            }
        }
    }
} // juste un maxi match pour l'implem
