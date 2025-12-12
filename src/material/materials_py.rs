use std::collections::HashMap;
use std::hash::Hash;

use pyo3::prelude::*;
use pyo3::types::{PyAnyMethods, PyBool, PyDict};
use pyo3::{BoundObject, Py, PyAny, PyRef};

use pyo3::{pyclass, pymethods, types::PyTuple, Bound, Python};

use crate::material::materials::Material;
use crate::material::textured::BaseTexture;
use crate::texturebuffer;
use crate::texturebuffer::toglyph_methods_py::{ToGlyphMethodPy, ToGlyphMethodPyStatic};

#[pyclass(subclass)]
#[derive(Clone)]
pub struct MaterialPy {}
#[pymethods]
impl MaterialPy {
    #[new]
    pub fn new() -> Self {
        MaterialPy {}
    }
}
impl MaterialPy {
    pub fn to_native(py: Python, mat: &MaterialPy) -> Material {
        Material::DoNothing {}
    }
}

#[pyclass(extends=MaterialPy)]
#[derive(Clone)]
pub struct BaseTexturePy {
    #[pyo3(get, set)]
    pub albedo_texture_idx: usize,
    #[pyo3(get, set)]
    pub albedo_texture_subid: usize,
    #[pyo3(get, set)]
    pub glyph_texture_idx: usize,
    #[pyo3(get, set)]
    pub glyph_texture_subid: usize,

    #[pyo3(get, set)]
    pub front: bool,
    #[pyo3(get, set)]
    pub back: bool,
    #[pyo3(get, set)]
    pub glyph: bool,
    #[pyo3(get, set)]
    pub glyph_uv_0: bool,

    #[pyo3(get, set)]
    pub front_uv_0: bool,
    #[pyo3(get, set)]
    pub back_uv_0: bool,
    #[pyo3(get, set)]
    pub glyph_method: ToGlyphMethodPy,
}
impl BaseTexturePy {
    pub fn to_native(&self) -> BaseTexture {
        BaseTexture {
            albedo_texture_idx: self.albedo_texture_idx,
            albedo_texture_subid: self.albedo_texture_subid,
            glyph_texture_idx: self.glyph_texture_idx,
            glyph_texture_subid: self.glyph_texture_subid,
            front: self.front,
            back: self.back,
            glyph: self.glyph,
            front_uv_0: self.front_uv_0,
            back_uv_0: self.back_uv_0,
            glyph_uv_0: self.glyph_uv_0,
            to_glyph_method: self.glyph_method.to_method(), //self.glyph_method.to_method(),
        }
    }
}
#[pymethods]
impl BaseTexturePy {
    #[new]
    #[pyo3(signature = (albedo_texture_idx=0, albedo_texture_subid=0, glyph_texture_idx=0, glyph_texture_subid=0, front=true, back=true, glyph=true, front_uv_0=true, back_uv_0=true, glyph_uv_0=true, glyph_method=None))]
    fn new(
        albedo_texture_idx: usize,
        albedo_texture_subid: usize,
        glyph_texture_idx: usize,
        glyph_texture_subid: usize,
        front: bool,
        back: bool,
        glyph: bool,
        front_uv_0: bool,
        back_uv_0: bool,
        glyph_uv_0: bool,
        glyph_method: Option<ToGlyphMethodPy>,
    ) -> PyClassInitializer<Self> {
        let parent = MaterialPy::new();
        let glyph_method = match glyph_method {
            Some(gm) => gm,
            None => ToGlyphMethodPy {
                met_id: 0,
                glyph_idx: 0,
                glyph_set: (0, 0, 0, 0),
            },
        };
        PyClassInitializer::from(parent).add_subclass(BaseTexturePy {
            albedo_texture_idx,
            albedo_texture_subid,
            glyph_texture_idx,
            glyph_texture_subid,
            front,
            back,
            glyph,
            front_uv_0,
            back_uv_0,
            glyph_uv_0,
            glyph_method: glyph_method,
        })
    }
}

#[pyclass(extends=MaterialPy)]
#[derive(Clone)]
pub struct StaticColorPy {
    #[pyo3(get, set)]
    pub front: bool,
    #[pyo3(get, set)]
    pub back: bool,
    #[pyo3(get, set)]
    pub glyph: bool,

    #[pyo3(get, set)]
    pub front_color: (u8, u8, u8, u8),
    #[pyo3(get, set)]
    pub back_color: (u8, u8, u8, u8),

    #[pyo3(get, set)]
    glyph_idx: u8,
}

#[pymethods]
impl StaticColorPy {
    #[new]
    fn new(
        front: bool,
        back: bool,
        glyph: bool,
        front_color: (u8, u8, u8, u8),
        back_color: (u8, u8, u8, u8),
        glyph_idx: u8,
    ) -> PyClassInitializer<Self> {
        let parent = MaterialPy::new();
        PyClassInitializer::from(parent).add_subclass(StaticColorPy {
            front,
            back,
            glyph,
            front_color,
            back_color,
            glyph_idx,
        })
    }
}
impl StaticColorPy {
    pub fn to_native(&self) -> Material {
        Material::StaticColor {
            front: self.front,
            back: self.back,
            glyph: self.glyph,
            front_color: texturebuffer::RGBA {
                r: self.front_color.0,
                g: self.front_color.1,
                b: self.front_color.2,
                a: self.front_color.3,
            },
            back_color: texturebuffer::RGBA {
                r: self.back_color.0,
                g: self.back_color.1,
                b: self.back_color.2,
                a: self.back_color.3,
            },
            glyph_idx: self.glyph_idx,
        }
    }
}

#[pyclass(extends=MaterialPy)]
#[derive(Clone)]
pub struct StaticGlyphPy {
    #[pyo3(get, set)]
    pub glyph_idx: u8,
}
#[pymethods]
impl StaticGlyphPy {
    #[new]
    fn new(glyph_idx: u8) -> PyClassInitializer<Self> {
        let parent = MaterialPy::new();
        PyClassInitializer::from(parent).add_subclass(StaticGlyphPy { glyph_idx })
    }
}
