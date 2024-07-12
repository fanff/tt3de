use crate::{
    drawbuffer::drawbuffer::{CanvasCell, DepthBufferCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveBuffer,
    utils::convert_tuple_rgba,
    vertexbuffer::{UVBuffer, VertexBuffer},
};

use super::texturebuffer::texture_buffer::TextureBuffer;
use super::texturebuffer::RGBA;

use nalgebra_glm::{Number, TVec3, Vec3};
pub mod debug_mat;
use debug_mat::*;

mod materials;
use materials::*;

mod noise_mat;
use noise_mat::*;

use pyo3::{pyclass, pymethods, types::PyTuple, Bound, Python};

pub struct MaterialBuffer {
    pub max_size: usize,
    pub current_size: usize,
    pub mats: Box<[Material]>,
}

impl MaterialBuffer {
    fn new(max_size: usize) -> Self {
        let mats = vec![Material::DoNothing {}; max_size].into_boxed_slice();
        MaterialBuffer {
            max_size: max_size,
            current_size: 0,
            mats: mats,
        }
    }
    fn clear(&mut self) {
        self.current_size = 0;
    }
    fn add_static(&mut self, front_color: RGBA, back_color: RGBA, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::StaticColor {
            front_color: front_color,
            back_color: back_color,
            glyph_idx: glyph_idx,
        };

        self.current_size += 1;
        retur
    }
    fn add_textured(&mut self, albedo_texture_idx: usize, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::Texture {
            albedo_texture_idx: albedo_texture_idx,
            glyph_idx: glyph_idx,
        };

        self.current_size += 1;
        retur
    }

    fn add_noop(&mut self) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::DoNothing {};

        self.current_size += 1;
        retur
    }

    fn add_debug_weight(&mut self, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::DebugWeight(DebugWeight::new(glyph_idx));

        self.current_size += 1;
        retur
    }

    fn add_debug_depth(&mut self, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::DebugDepth(DebugDepth::new(glyph_idx));

        self.current_size += 1;
        retur
    }

    fn add_debug_uv(&mut self, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::DebugUV(DebugUV::new(glyph_idx));

        self.current_size += 1;
        retur
    }
}

pub fn calc_uv_coord<DEPTHACC: nalgebra_glm::Number>(
    pixinfo: &PixInfo<DEPTHACC>,
    (ua, va, ub, vb, uc, vc): (DEPTHACC, DEPTHACC, DEPTHACC, DEPTHACC, DEPTHACC, DEPTHACC),
    weight_idx: usize,
) -> (DEPTHACC, DEPTHACC) {
    let uvec: TVec3<DEPTHACC> = TVec3::new(ua, ub, uc);
    let vvec: TVec3<DEPTHACC> = TVec3::new(va, vb, vc);

    match weight_idx {
        1 => (pixinfo.w_1.dot(&uvec), pixinfo.w_1.dot(&vvec)),
        _ => (pixinfo.w.dot(&uvec), pixinfo.w.dot(&vvec)),
    }
}

pub fn apply_material<const SIZE: usize, const UVCOUNT: usize, const DEPTHLAYER: usize>(
    material_buffer: &MaterialBuffer,
    texture_buffer: &TextureBuffer<SIZE>,
    uv_buffer: &UVBuffer<UVCOUNT, f32>,
    primitive_buffer: &PrimitiveBuffer,
    depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
    pixinfo: &PixInfo<f32>,
    cell: &mut CanvasCell,
) {
    let mat = &material_buffer.mats[pixinfo.material_id];

    let primitive_element = &primitive_buffer.content[pixinfo.primitive_id];
    mat.render_mat(
        cell,
        depth_cell,
        pixinfo,
        primitive_element,
        texture_buffer,
        uv_buffer,
    );
}

pub fn apply_noise<T: Number>(noise: &NoiseMaterial, pixinfo: &PixInfo<T>, u: f32, v: f32) -> f32 {
    let noise = noise.make_instance();
    let noise_val = noise.get_noise_2d(u, v);
    let noise_val = (noise_val + 1.0) / 2.0;
    noise_val
}

#[pyclass]
pub struct MaterialBufferPy {
    pub content: MaterialBuffer,
}

#[pymethods]
impl MaterialBufferPy {
    #[new]
    #[pyo3(signature = (max_size=64))]
    fn new(max_size: usize) -> Self {
        MaterialBufferPy {
            content: MaterialBuffer::new(max_size),
        }
    }
    fn clear(&mut self) {
        self.content.clear()
    }
    fn count(&self) -> usize {
        self.content.current_size
    }

    fn add_textured(&mut self, _py: Python, albedo_texture_idx: usize, glyph_idx: u8) -> usize {
        self.content.add_textured(albedo_texture_idx, glyph_idx)
    }

    fn add_static(
        &mut self,
        py: Python,
        front_rgba: &Bound<PyTuple>,
        back_rgba: &Bound<PyTuple>,
        glyph_idx: u8,
    ) -> usize {
        let fr = convert_tuple_rgba(front_rgba).unwrap();
        let bg = convert_tuple_rgba(back_rgba).unwrap();
        self.content.add_static(fr, bg, glyph_idx)
    }

    fn add_debug_weight(&mut self, _py: Python, glyph_idx: u8) -> usize {
        self.content.add_debug_weight(glyph_idx)
    }

    fn add_debug_depth(&mut self, _py: Python, glyph_idx: u8) -> usize {
        self.content.add_debug_depth(glyph_idx)
    }

    fn add_debug_uv(&mut self, _py: Python, glyph_idx: u8) -> usize {
        self.content.add_debug_uv(glyph_idx)
    }
}
