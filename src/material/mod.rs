use pyo3::{
    pyclass, pymethods,
    types::{PyAnyMethods, PyTuple, PyTupleMethods},
    Bound, Py, Python,
};

use crate::{
    drawbuffer::{
        self,
        drawbuffer::{CanvasCell, PixInfo},
    },
    texturebuffer::{TextureBuffer, RGBA},
    utils::convert_tuple_rgba,
};

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
}

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
}

pub fn apply_material<T: nalgebra_glm::Number, const SIZE: usize>(
    material_buffer: &MaterialBuffer,
    texture_buffer: &TextureBuffer<SIZE>,
    pixinfo: &PixInfo<T>,
    cell: &mut CanvasCell,
) {
    let mat = &material_buffer.mats[pixinfo.material_id];

    match mat {
        Material::DoNothing {} => {}
        Material::Texture {
            albedo_texture_idx,
            glyph_idx,
        } => {
            cell.glyph = *glyph_idx;
            let u: f32 = 0.0;
            let v: f32 = 1.0;
            let c = texture_buffer.get_rgba_at(*albedo_texture_idx, u, v);
            cell.front_color.copy_from(&c);
            //cell.back_color.copy_from(back_color);
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
    }
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

    fn add_textured(&mut self, py: Python, albedo_texture_idx: usize, glyph_idx: u8) -> usize {
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
}
