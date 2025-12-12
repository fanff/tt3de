use std::collections::HashMap;

use pyo3::types::{PyAnyMethods, PyDict};
use pyo3::{prelude::*, PyClass};
use pyo3::{BoundObject, Py, PyAny, PyRef};

use crate::texturebuffer::toglyph_methods::ToGlyphMethod;

#[derive(Clone)]
#[pyclass(subclass)]
pub struct ToGlyphMethodPy {
    pub met_id: usize,
    pub glyph_idx: u8,
    pub glyph_set: (u8, u8, u8, u8),
}
impl ToGlyphMethodPy {
    pub fn to_method(&self) -> ToGlyphMethod {
        match self.met_id {
            0 => ToGlyphMethod::Static(self.glyph_idx),
            1 => ToGlyphMethod::Map4Luminance(
                self.glyph_set.0,
                self.glyph_set.1,
                self.glyph_set.2,
                self.glyph_set.3,
            ),
            _ => panic!("Unknown ToGlyphMethodPy id"),
        }
    }
}

/// Static glyph
///
/// Use the given glyph index for all pixels.
#[pyclass(extends=ToGlyphMethodPy)]
#[derive(Clone)]
pub struct ToGlyphMethodPyStatic {
    #[pyo3(get, set)]
    pub glyph_idx: u8,
}
#[pymethods]
impl ToGlyphMethodPyStatic {
    #[new]
    pub fn new(glyph_idx: u8) -> PyClassInitializer<Self> {
        let parent = ToGlyphMethodPy {
            met_id: 0,
            glyph_idx,
            glyph_set: (0, 0, 0, 0),
        };
        PyClassInitializer::from(parent).add_subclass(ToGlyphMethodPyStatic { glyph_idx })
    }
}

/// Map4 Luminance
///
/// Calculate the luminance of the texture color and map it to one of four glyphs.
#[pyclass(extends=ToGlyphMethodPy)  ]
#[derive(Clone)]
pub struct ToGlyphMethodPyMap4Luminance {
    #[pyo3(get, set)]
    pub glyph_set: (u8, u8, u8, u8),
}
#[pymethods]
impl ToGlyphMethodPyMap4Luminance {
    #[new]
    fn new(glyph_set: (u8, u8, u8, u8)) -> PyClassInitializer<Self> {
        let parent = ToGlyphMethodPy {
            met_id: 1,
            glyph_idx: 0,
            glyph_set,
        };
        PyClassInitializer::from(parent).add_subclass(ToGlyphMethodPyMap4Luminance { glyph_set })
    }
}
