use super::texturebuffer::texture_buffer::TextureBuffer;
use super::texturebuffer::RGBA;
use crate::vertexbuffer::uv_buffer::UVBuffer;
use crate::{
    drawbuffer::blend::{BlendMode, GlyphPolicy},
    drawbuffer::drawbuffer::{CanvasCell, DepthBufferCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveBuffer,
};

use nalgebra_glm::Number;
pub mod debug_mat;
use debug_mat::*;

pub mod materials;
use materials::*;
pub mod shader_material;
use shader_material::*;

/// Invalidate thread-local TTSL register caches for a new full-buffer material pass.
pub fn bump_material_apply_generation_for_pass() {
    shader_material::bump_material_apply_generation();
}

pub mod textured;

use textured::*;
pub mod noise_mat;
use noise_mat::*;

pub struct MaterialBuffer {
    pub max_size: usize,
    pub current_size: usize,
    pub mats: Box<[Material]>,
}

impl MaterialBuffer {
    pub fn new(max_size: usize) -> Self {
        let mats = vec![Material::DoNothing {}; max_size].into_boxed_slice();
        MaterialBuffer {
            max_size,
            current_size: 0,
            mats,
        }
    }
    pub fn clear(&mut self) {
        self.current_size = 0;
    }
    pub fn add_material(&mut self, mat: Material) -> usize {
        self.mats[self.current_size] = mat;

        self.current_size += 1;
        self.current_size - 1
    }
    pub fn set_material(&mut self, idx: usize, mat: Material) {
        self.mats[idx] = mat;
    }

    pub fn add_static(&mut self, front_color: RGBA, back_color: RGBA, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::StaticColor {
            front: true,
            back: true,
            glyph: true,
            front_color,
            back_color,
            glyph_idx,
            blend_mode: BlendMode::Replace,
            glyph_policy: GlyphPolicy::PreserveExisting,
        };

        self.current_size += 1;
        retur
    }
    pub fn add_textured(&mut self, albedo_texture_idx: usize, glyph_idx: u8) -> usize {
        self.mats[self.current_size] =
            Material::Texture(Textured::new(albedo_texture_idx, glyph_idx));

        self.current_size += 1;
        self.current_size - 1
    }

    #[allow(dead_code)]
    fn add_noop(&mut self) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::DoNothing {};

        self.current_size += 1;
        retur
    }

    pub fn add_debug_depth(&mut self, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::DebugDepth(DebugDepth::new(glyph_idx));

        self.current_size += 1;
        retur
    }

    pub fn add_debug_uv(&mut self, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::DebugUV(DebugUV::new(glyph_idx));

        self.current_size += 1;
        retur
    }
}

pub fn apply_material<const SIZE: usize, const DEPTHLAYER: usize>(
    pixinfo: PixInfo<f32>,
    material_buffer: &MaterialBuffer,
    texture_buffer: &TextureBuffer<SIZE>,
    uv_buffer: &UVBuffer<f32>,
    primitive_buffer: &PrimitiveBuffer,
    depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
    depth_layer: usize,
    cell: &mut CanvasCell,
) {
    let primitive_element = &primitive_buffer.content[pixinfo.primitive_id];
    let mat = &material_buffer.mats[pixinfo.material_id];
    mat.render_mat(
        cell,
        depth_cell,
        depth_layer,
        &pixinfo,
        primitive_element,
        texture_buffer,
        uv_buffer,
    );
}

pub fn apply_noise<T: Number>(noise: &NoiseMaterial, _pixinfo: &PixInfo<T>, u: f32, v: f32) -> f32 {
    let noise = noise.make_instance();
    let noise_val = noise.get_noise_2d(u, v);

    (noise_val + 1.0) / 2.0
}
