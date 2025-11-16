use crate::{
    drawbuffer::drawbuffer::{CanvasCell, DepthBufferCell, PixInfo},
    material::materials::RenderMaterial,
    primitivbuffer::primitivbuffer::PrimitiveElements,
    texturebuffer::texture_buffer::TextureBuffer,
    vertexbuffer::uv_buffer::UVBuffer,
};
use pyo3::{
    prelude::*,
    types::{PyFunction, PyInt, PyList, PyTuple},
};
use pyo3::{BoundObject, Py, PyAny, PyRef};

use pyo3::{pyclass, pymethods, types::PyTime};
use pyo3::{Bound, Python};

#[derive(Clone)]
pub struct ComboMaterial {
    pub count: usize,
    pub idx0: usize,
    pub idx1: usize,
    pub idx2: usize,
    pub idx3: usize,
    pub idx4: usize,
}
// implement render trait for ComboMaterial
impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize>
    RenderMaterial<TEXTURE_BUFFER_SIZE, DEPTHLAYER> for ComboMaterial
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

#[pyclass]
pub struct ComboMaterialPy {
    #[pyo3(get, set)]
    pub count: usize,
    #[pyo3(get, set)]
    pub idx0: usize,
    #[pyo3(get, set)]
    pub idx1: usize,
    #[pyo3(get, set)]
    pub idx2: usize,
    #[pyo3(get, set)]
    pub idx3: usize,
    #[pyo3(get, set)]
    pub idx4: usize,
}
#[pymethods]
impl ComboMaterialPy {
    #[new]
    fn new() -> Self {
        ComboMaterialPy {
            count: 0,
            idx0: 0,
            idx1: 0,
            idx2: 0,
            idx3: 0,
            idx4: 0,
        }
    }

    #[staticmethod]
    fn from_list(lst: Vec<i64>) -> Self {
        let mut mat = ComboMaterialPy::new();
        let len = lst.len();
        mat.count = len;
        if len > 0 {
            mat.idx0 = lst[0] as usize;
        }
        if len > 1 {
            mat.idx1 = lst[1] as usize;
        }
        if len > 2 {
            mat.idx2 = lst[2] as usize;
        }
        if len > 3 {
            mat.idx3 = lst[3] as usize;
        }
        if len > 4 {
            mat.idx4 = lst[4] as usize;
        }
        mat
    }
}

// implement into for ComboMaterialPy to ComboMaterial
impl From<ComboMaterialPy> for ComboMaterial {
    fn from(py: ComboMaterialPy) -> Self {
        ComboMaterial {
            count: py.count,
            idx0: py.idx0,
            idx1: py.idx1,
            idx2: py.idx2,
            idx3: py.idx3,
            idx4: py.idx4,
        }
    }
}
