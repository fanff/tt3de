use crate::utils::convert_tuple_texture_rgba;
use pyo3::{
    exceptions::PyValueError,
    pyclass, pymethods,
    types::{PyAnyMethods, PyList},
    Bound, Py, PyAny, PyResult, Python,
};
use tt3de_core::texturebuffer::{texture_buffer::TextureBuffer, FilterMode, RGBA};
pub mod toglyph_methods_py;

fn parse_filter_mode(mode: &str) -> PyResult<FilterMode> {
    match mode.to_lowercase().as_str() {
        "nearest" => Ok(FilterMode::Nearest),
        "bilinear" => Ok(FilterMode::Bilinear),
        _ => Err(PyValueError::new_err(format!(
            "Unknown filter_mode: '{mode}'. Expected 'nearest' or 'bilinear'."
        ))),
    }
}

pub struct TextureIterator<'a> {
    py: Python<'a>,
    pix_list: &'a Bound<'a, PyList>,
    index: usize,
}

impl<'a> TextureIterator<'a> {
    fn new(py: Python<'a>, pix_list: &'a Bound<'a, PyList>) -> Self {
        TextureIterator {
            py,
            pix_list,
            index: 0,
        }
    }
}

impl<'a> Iterator for TextureIterator<'a> {
    type Item = RGBA;

    fn next(&mut self) -> Option<Self::Item> {
        if self.index < self.pix_list.len().ok().unwrap() {
            let item: &Bound<PyAny> = &self.pix_list.get_item(self.index).ok().unwrap();
            self.index += 1;
            let tuple = item.extract().ok()?;
            convert_tuple_texture_rgba(self.py, tuple)
        } else {
            None
        }
    }
}

#[pyclass]
pub struct TextureBufferPy {
    pub data: TextureBuffer<256>,

    #[pyo3(get)]
    pub max_texture_size: usize,
}

#[pymethods]
impl TextureBufferPy {
    #[new]
    fn new(max_size: usize) -> TextureBufferPy {
        let tb = TextureBuffer::new(max_size);
        TextureBufferPy {
            data: tb,
            max_texture_size: 256,
        }
    }
    fn size(&self) -> usize {
        self.data.current_size
    }
    fn get_wh_of(&self, idx: usize) -> (usize, usize) {
        self.data.get_wh_of(idx)
    }

    #[pyo3(signature = (width,height,pixels,repeat_width=true,repeat_height=true,filter_mode="bilinear"))]
    fn add_texture(
        &mut self,
        py: Python,
        width: usize,
        height: usize,
        pixels: Py<PyList>,
        repeat_width: bool,
        repeat_height: bool,
        filter_mode: &str,
    ) -> PyResult<usize> {
        let fm = parse_filter_mode(filter_mode)?;
        let pixel_iter = pixels.bind(py).cast::<PyList>().unwrap();
        let texture_iter = TextureIterator::new(py, pixel_iter);

        Ok(self.data.add_texture_from_iter(
            width,
            height,
            texture_iter,
            repeat_width,
            repeat_height,
            fm,
        ))
    }

    #[pyo3(signature = (width, height, pixels, pix_size_width, pix_size_height, filter_mode="bilinear"))]
    fn add_atlas_texture_from_iter(
        &mut self,
        py: Python,
        width: usize,
        height: usize,
        pixels: Py<PyList>,
        pix_size_width: usize,
        pix_size_height: usize,
        filter_mode: &str,
    ) -> PyResult<usize> {
        let fm = parse_filter_mode(filter_mode)?;
        let pixel_iter = pixels.bind(py).cast::<PyList>().unwrap();
        let texture_iter = TextureIterator::new(py, pixel_iter);

        Ok(self.data.add_atlas_texture_from_iter(
            width,
            height,
            pix_size_width,
            pix_size_height,
            texture_iter,
            fm,
        ))
    }
    fn add_noise_texture(&mut self, seed: i32, int_config: i32) -> usize {
        self.data.add_noise_texture(seed, int_config)
    }

    fn get_rgba_at(&self, idx: usize, u: f32, v: f32) -> (u8, u8, u8, u8) {
        let c = self.data.get_rgba_at(idx, u, v, 0);
        (c.r, c.g, c.b, c.a)
    }
}
