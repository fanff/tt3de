use crate::utils::convert_tuple_texture_rgba;
use pyo3::{
    pyclass, pymethods,
    types::{PyAnyMethods, PyList},
    Bound, Py, PyAny, Python, ToPyObject,
};

pub mod noise_texture;
use noise_texture::*;
pub mod atlas_texture;
use atlas_texture::*;
pub mod texture_buffer;
use texture_buffer::*;

#[derive(Clone, Copy)]
pub struct RGBA {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: u8,
}

impl RGBA {
    pub fn new(r: u8, g: u8, b: u8, a: u8) -> Self {
        Self { r, g, b, a }
    }
}

#[derive(Clone)]
pub struct Texture<const SIZE: usize> {
    data: Box<[RGBA]>, // Fixed-size array of RGBA colors

    repeat_x: bool,
    repeat_y: bool,
}

impl<const SIZE: usize> Texture<SIZE> {
    pub fn new(data: RGBA, repeat_x: bool, repeat_y: bool) -> Self {
        let d = vec![data; SIZE * SIZE].into_boxed_slice();
        Texture {
            data: d,
            repeat_x,
            repeat_y,
        }
    }
    pub fn from_iter<I: IntoIterator<Item = RGBA>>(
        iter: I,
        repeat_x: bool,
        repeat_y: bool,
    ) -> Self {
        let data: Vec<RGBA> = iter.into_iter().collect();
        Texture {
            data: data.into_boxed_slice(),
            repeat_x,
            repeat_y,
        }
    }
    pub fn uv_map(&self, u: f32, v: f32) -> RGBA {
        let u_val = if self.repeat_x {
            u % 1.0
        } else {
            u.clamp(0.0, 1.0)
        };
        let v_val = if self.repeat_y {
            v % 1.0
        } else {
            v.clamp(0.0, 1.0)
        };

        // Convert u, v to texture coordinates
        let x = (u_val * ((SIZE - 1) as f32)) as usize;
        let y = (v_val * ((SIZE - 1) as f32)) as usize;

        // Return the color at the computed coordinates
        self.data[x * SIZE + y]
    }
}

#[derive(Clone)]
pub struct TextureCustom<const SIZE: usize> {
    texture: Texture<SIZE>,
    width: usize,
    height: usize,
    repeat_x: bool,
    repeat_y: bool,
}

impl<const SIZE: usize> TextureCustom<SIZE> {
    pub fn new<I: IntoIterator<Item = RGBA>>(
        iter: I,
        width: usize,
        height: usize,
        repeat_x: bool,
        repeat_y: bool,
    ) -> Self {
        let data: Vec<RGBA> = iter.into_iter().collect();
        assert!(
            data.len() == width * height,
            "Data array size must be width * height"
        );
        TextureCustom {
            texture: Texture {
                data: data.into_boxed_slice(),
                repeat_x,
                repeat_y,
            },
            width,
            height,
            repeat_x,
            repeat_y,
        }
    }

    pub fn uv_map(&self, u: f32, v: f32) -> RGBA {
        let u_val = if self.repeat_x {
            u % 1.0
        } else {
            u.clamp(0.0, 1.0)
        };
        let v_val = if self.repeat_y {
            v % 1.0
        } else {
            v.clamp(0.0, 1.0)
        };

        // Convert u, v to texture coordinates
        let x = (u_val * self.width as f32) as usize;
        let y = (v_val * self.height as f32) as usize;

        self.texture.data[y * self.width + x]
    }
}

#[derive(Clone)]
pub enum TextureType<const SIZE: usize> {
    Custom(TextureCustom<SIZE>),
    Fixed(Texture<SIZE>),
    Atlas(TextureAtlas<SIZE>),
    Noise(NoiseTexture),
}

impl<const SIZE: usize> TextureType<SIZE> {
    pub fn uv_map(&self, u: f32, v: f32) -> RGBA {
        match self {
            TextureType::Custom(t) => t.uv_map(u, v),
            TextureType::Fixed(t) => t.uv_map(u, v),
            TextureType::Atlas(t) => t.texture.uv_map(u, v),
            TextureType::Noise(t) => t.uv_map(u, v),
        }
    }
}

/// START of the python stufff
///
///
///
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
            convert_tuple_texture_rgba(self.py, item.to_object(self.py))
        } else {
            None
        }
    }
}

#[pyclass]
pub struct TextureBufferPy {
    pub data: TextureBuffer<256>,
}

#[pymethods]
impl TextureBufferPy {
    #[new]
    fn new(max_size: usize) -> TextureBufferPy {
        let tb = TextureBuffer::new(max_size);
        TextureBufferPy { data: tb }
    }
    fn size(&self) -> usize {
        self.data.current_size
    }
    fn get_wh_of(&self, idx: usize) -> (usize, usize) {
        self.data.get_wh_of(idx)
    }

    #[pyo3(signature = (width,height,pixels,repeat_width=true,repeat_height=true, ))]
    fn add_texture(
        &mut self,
        py: Python,
        width: usize,
        height: usize,
        pixels: Py<PyList>,
        repeat_width: bool,
        repeat_height: bool,
    ) -> usize {
        let pixel_iter = pixels.bind(py).downcast::<PyList>().unwrap();
        let texture_iter = TextureIterator::new(py, pixel_iter);

        self.data
            .add_texture_from_iter(width, height, texture_iter, repeat_width, repeat_height)
    }
    fn add_noise_texture(&mut self, seed: i32, int_config: i32) -> usize {
        self.data.add_noise_texture(seed, int_config)
    }

    fn get_rgba_at(&self, idx: usize, u: f32, v: f32) -> (u8, u8, u8, u8) {
        let c = self.data.get_rgba_at(idx, u, v);
        (c.r, c.g, c.b, c.a)
    }
}
