use nalgebra_glm::{TVec3, Vec3};
use pyo3::{pyclass, pymethods, types::PyTuple, Bound, Python};

use crate::{
    drawbuffer::drawbuffer::{CanvasCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveBuffer,
    texturebuffer::{TextureBuffer, RGBA},
    utils::convert_tuple_rgba,
    vertexbuffer::{UVBuffer, VertexBuffer},
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
pub fn calc_uv_coord<DEPTHACC: nalgebra_glm::Number>(
    pixinfo: &PixInfo<DEPTHACC>,
    (ua, va, ub, vb, uc, vc): (DEPTHACC, DEPTHACC, DEPTHACC, DEPTHACC, DEPTHACC, DEPTHACC),
) -> (DEPTHACC, DEPTHACC) {
    let uvec: TVec3<DEPTHACC> = TVec3::new(ua, ub, uc);
    let vvec: TVec3<DEPTHACC> = TVec3::new(va, vb, vc);

    (pixinfo.w.dot(&uvec), pixinfo.w.dot(&vvec))
}

pub fn apply_material<const SIZE: usize, const UVCOUNT: usize>(
    material_buffer: &MaterialBuffer,
    texture_buffer: &TextureBuffer<SIZE>,
    uv_buffer: &UVBuffer<UVCOUNT, f32>,
    primitive_buffer: &PrimitiveBuffer<f32>,
    pixinfo: &PixInfo<f32>,
    cell: &mut CanvasCell,
) {
    let mat = &material_buffer.mats[pixinfo.material_id];

    let prim = &primitive_buffer.content[pixinfo.primitive_id];

    match mat {
        Material::DoNothing {} => {}
        Material::Texture {
            albedo_texture_idx,
            glyph_idx,
        } => {
            cell.glyph = *glyph_idx;

            let uv_idx = prim.get_uv_idx();
            let (uva, uvb, uvc) = uv_buffer.get_uv(uv_idx);
            let (ufront, vfront) =
                calc_uv_coord(pixinfo, (uva.x, uva.y, uvb.x, uvb.y, uvc.x, uvc.y));

            let front_rgba = texture_buffer.get_rgba_at(*albedo_texture_idx, ufront, vfront);
            cell.front_color.copy_from(&front_rgba);

            let (uback, vback) = calc_uv_coord(pixinfo, (uva.x, uva.y, uvb.x, uvb.y, uvc.x, uvc.y));

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
