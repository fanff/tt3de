use crate::drawbuffer::drawbuffer::{CanvasCell, DepthBufferCell, PixInfo};
use crate::material::combo_material::ComboMaterial;
use crate::material::textured::{TexturedBack, TexturedFront};
use crate::primitivbuffer::primitivbuffer::PrimitiveElements;
use crate::texturebuffer::texture_buffer::TextureBuffer;

use crate::vertexbuffer::uv_buffer::UVBuffer;

use super::super::texturebuffer::RGBA;

use super::{apply_noise, noise_mat::*, DebugDepth, DebugUV, Textured};

#[derive(Clone)]
pub enum Material<T = ()> {
    DoNothing {},
    Texture(Textured),
    TexturedBack(TexturedBack),
    TexturedFront(TexturedFront),
    StaticColor {
        front_color: RGBA,
        back_color: RGBA,
        glyph_idx: u8, // b'a'
    },
    StaticColorBack {
        back_color: RGBA,
    },
    StaticColorFront {
        front_color: RGBA,
    },
    StaticGlyph {
        glyph_idx: u8,
    },
    Noise {
        noise: NoiseMaterial,
        glyph_idx: u8,
    },

    DebugDepth(DebugDepth),
    DebugUV(DebugUV),
    ComboMaterial(ComboMaterial),
    Custom(T),
}

pub trait RenderMaterial<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize> {
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        depth_layer: usize,
        pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        uv_buffer: &UVBuffer<f32>,
    );
}

impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize>
    RenderMaterial<TEXTURE_BUFFER_SIZE, DEPTHLAYER> for ()
{
    fn render_mat(
        &self,
        _cell: &mut CanvasCell,
        _depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        _depth_layer: usize,
        _pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements,
        _texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        _uv_buffer: &UVBuffer<f32>,
    ) {
    }
}

impl<
        const TEXTURE_BUFFER_SIZE: usize,
        const DEPTHLAYER: usize,
        T: RenderMaterial<TEXTURE_BUFFER_SIZE, DEPTHLAYER>,
    > RenderMaterial<TEXTURE_BUFFER_SIZE, DEPTHLAYER> for Material<T>
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        depth_layer: usize,
        pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        uv_buffer: &UVBuffer<f32>,
    ) {
        match self {
            Material::ComboMaterial(cm) => {}
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
            Material::Custom(t) => t.render_mat(
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
            Material::StaticColorBack { back_color } => {
                cell.back_color.copy_from(back_color);
            }
            Material::StaticColorFront { front_color } => {
                cell.front_color.copy_from(front_color);
            }
            Material::StaticGlyph { glyph_idx } => {
                cell.glyph = *glyph_idx;
            }
            Material::TexturedBack(textured_back) => textured_back.render_mat(
                cell,
                depth_cell,
                depth_layer,
                pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            ),
            Material::TexturedFront(textured_front) => textured_front.render_mat(
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
