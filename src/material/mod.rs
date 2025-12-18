use super::texturebuffer::texture_buffer::TextureBuffer;
use super::texturebuffer::RGBA;
use crate::primitivbuffer::primitivbuffer::PrimitiveElements;
use crate::texturebuffer::toglyph_methods_py::ToGlyphMethodPy;
use crate::vertexbuffer::uv_buffer::UVBuffer;
use crate::{
    drawbuffer::drawbuffer::{CanvasCell, DepthBufferCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveBuffer,
    utils::convert_tuple_rgba,
};

use nalgebra_glm::Number;
pub mod debug_mat;
use debug_mat::*;

pub mod materials_py;
use materials_py::*;
mod materials;
use materials::*;
mod textured;

use textured::*;
mod noise_mat;
use noise_mat::*;
pub mod combo_material;
use combo_material::*;
use pyo3::prelude::*;
use pyo3::types::{PyAnyMethods, PyDict};
use pyo3::{pyclass, pymethods, types::PyTuple, Bound, Python};
use pyo3::{BoundObject, Py, PyAny, PyRef};

pub struct MaterialBuffer {
    pub max_size: usize,
    pub current_size: usize,
    pub mats: Box<[Material]>,
}

impl MaterialBuffer {
    fn new(max_size: usize) -> Self {
        let mats = vec![Material::DoNothing {}; max_size].into_boxed_slice();
        MaterialBuffer {
            max_size,
            current_size: 0,
            mats,
        }
    }
    fn clear(&mut self) {
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

    fn add_static(&mut self, front_color: RGBA, back_color: RGBA, glyph_idx: u8) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::StaticColor {
            front: true,
            back: true,
            glyph: true,
            front_color,
            back_color,
            glyph_idx,
        };

        self.current_size += 1;
        retur
    }
    fn add_textured(&mut self, albedo_texture_idx: usize, glyph_idx: u8) -> usize {
        self.mats[self.current_size] =
            Material::Texture(Textured::new(albedo_texture_idx, glyph_idx));

        self.current_size += 1;
        self.current_size - 1
    }

    fn add_noop(&mut self) -> usize {
        let retur = self.current_size;
        self.mats[self.current_size] = Material::DoNothing {};

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
    // If mat is a Custom material we don't assume any specific payload here,
    // so just fall back to the default render path.
    if let Material::ComboMaterial(t) = mat {
        if t.count >= 1 {
            let mat0 = &material_buffer.mats[t.idx0];
            mat0.render_mat(
                cell,
                depth_cell,
                depth_layer,
                &pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            );
        }
        if t.count >= 2 {
            let mat1 = &material_buffer.mats[t.idx1];
            mat1.render_mat(
                cell,
                depth_cell,
                depth_layer,
                &pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            );
        }
        if t.count >= 3 {
            let mat2 = &material_buffer.mats[t.idx2];
            mat2.render_mat(
                cell,
                depth_cell,
                depth_layer,
                &pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            );
        }
        if t.count >= 4 {
            let mat3 = &material_buffer.mats[t.idx3];
            mat3.render_mat(
                cell,
                depth_cell,
                depth_layer,
                &pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            );
        }
        if t.count >= 5 {
            let mat4 = &material_buffer.mats[t.idx4];
            mat4.render_mat(
                cell,
                depth_cell,
                depth_layer,
                &pixinfo,
                primitive_element,
                texture_buffer,
                uv_buffer,
            );
        }
    } else {
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
}

pub fn apply_noise<T: Number>(noise: &NoiseMaterial, pixinfo: &PixInfo<T>, u: f32, v: f32) -> f32 {
    let noise = noise.make_instance();
    let noise_val = noise.get_noise_2d(u, v);

    (noise_val + 1.0) / 2.0
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
    fn add_material(&mut self, py: Python, mat: Bound<'_, MaterialPy>) -> usize {
        panic!("Not implemented");
    }

    fn set_material(&mut self, py: Python, idx: usize, mat: Bound<'_, MaterialPy>) {
        panic!("Not implemented");
    }

    fn add_base_texture<'py>(&mut self, py: Python<'py>, mat: &BaseTexturePy) -> usize {
        self.content
            .add_material(Material::BaseTexture(mat.to_native()))
    }

    fn add_static_color(&mut self, py: Python, mat: &StaticColorPy) -> usize {
        self.content.add_material(mat.to_native())
    }

    fn add_combo_material(&mut self, mat: &ComboMaterialPy) -> usize {
        return self
            .content
            .add_material(Material::ComboMaterial(ComboMaterial {
                count: mat.count,
                idx0: mat.idx0,
                idx1: mat.idx1,
                idx2: mat.idx2,
                idx3: mat.idx3,
                idx4: mat.idx4,
            }));
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
        _py: Python,
        front_rgba: &Bound<PyTuple>,
        back_rgba: &Bound<PyTuple>,
        glyph_idx: u8,
    ) -> usize {
        let fr = convert_tuple_rgba(front_rgba).unwrap();
        let bg = convert_tuple_rgba(back_rgba).unwrap();
        self.content.add_static(fr, bg, glyph_idx)
    }

    fn add_debug_depth(&mut self, _py: Python, glyph_idx: u8) -> usize {
        self.content.add_debug_depth(glyph_idx)
    }

    fn add_debug_uv(&mut self, _py: Python, glyph_idx: u8) -> usize {
        self.content.add_debug_uv(glyph_idx)
    }
}
