use crate::utils::convert_tuple_texture_rgba;
use nalgebra::{Const, VecStorage};
use nalgebra_glm::Vec4;
use pyo3::{
    pyclass, pymethods,
    types::{PyAnyMethods, PyList, PyTuple},
    Bound, Py, PyAny, Python,
};

pub mod noise_texture;
use noise_texture::*;
pub mod atlas_texture;
use atlas_texture::*;
pub mod texture_buffer;
use texture_buffer::*;

pub mod toglyph_methods_py;
use toglyph_methods_py::*;
pub mod toglyph_methods;
use toglyph_methods::*;

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
    pub fn from_tuple(t: (u8, u8, u8, u8)) -> Self {
        Self {
            r: t.0,
            g: t.1,
            b: t.2,
            a: t.3,
        }
    }
    pub fn mult_albedo(&self, factor: f32) -> Self {
        let f = factor.clamp(0.0, 1.0);
        RGBA {
            r: (self.r as f32 * f) as u8,
            g: (self.g as f32 * f) as u8,
            b: (self.b as f32 * f) as u8,
            a: self.a,
        }
    }
    pub fn luminance(&self) -> f32 {
        0.2126 * (self.r as f32) + 0.7152 * (self.g as f32) + 0.0722 * (self.b as f32)
    }
}

pub trait UvMapper {
    fn get_width(&self) -> usize;
    fn get_height(&self) -> usize;
    fn uv_map(&self, u: f32, v: f32, idx: usize) -> RGBA;
}

impl<const SIZE: usize> UvMapper for Texture<SIZE> {
    fn get_width(&self) -> usize {
        SIZE
    }
    fn get_height(&self) -> usize {
        SIZE
    }
    fn uv_map(&self, u: f32, v: f32, _idx: usize) -> RGBA {
        self.uv_map_inline(u, v)
    }
}
impl<const SIZE: usize> UvMapper for TextureCustom<SIZE> {
    fn get_width(&self) -> usize {
        self.width
    }
    fn get_height(&self) -> usize {
        self.height
    }
    fn uv_map(&self, u: f32, v: f32, _idx: usize) -> RGBA {
        self.uv_map_inline(u, v)
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
    #[inline(always)]
    pub fn uv_map_inline(&self, u: f32, v: f32) -> RGBA {
        // Compute the x coordinate
        let x = if self.repeat_x {
            // For repeating textures, use rem_euclid to get a positive remainder,
            // then multiply by SIZE and wrap via bitwise AND.
            let u = u.rem_euclid(1.0);
            ((u * (SIZE as f32)) as usize) & (SIZE - 1)
        } else {
            // For clamped textures, clamp u to [0,1] and ensure u==1 maps to SIZE-1.
            let u = u.clamp(0.0, 1.0);
            let idx = (u * (SIZE as f32)) as usize;
            if idx >= SIZE {
                SIZE - 1
            } else {
                idx
            }
        };

        // Compute the y coordinate similarly
        let y = if self.repeat_y {
            let v = v.rem_euclid(1.0);
            ((v * (SIZE as f32)) as usize) & (SIZE - 1)
        } else {
            let v = v.clamp(0.0, 1.0);
            let idx = (v * (SIZE as f32)) as usize;
            if idx >= SIZE {
                SIZE - 1
            } else {
                idx
            }
        };

        // Use bit-shift instead of multiplication because SIZE is a power of 2.
        // Compute the number of bits to shift: log2(SIZE).
        let shift = SIZE.trailing_zeros() as usize;
        self.data[(y << shift) + x]
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

    pub fn uv_map_inline(&self, u: f32, v: f32) -> RGBA {
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
        //self.texture.data[x * self.height + y]
    }
}

#[derive(Clone)]
pub enum TextureType<const SIZE: usize> {
    Custom(TextureCustom<SIZE>),
    Fixed(Texture<SIZE>),
    AtlasCustom(TextureAtlas<TextureCustom<SIZE>, SIZE>),
    Atlas(TextureAtlas<Texture<SIZE>, SIZE>),
    Noise(NoiseTexture),
}

impl<const SIZE: usize> UvMapper for TextureType<SIZE> {
    fn uv_map(&self, u: f32, v: f32, idx: usize) -> RGBA {
        match self {
            TextureType::Custom(t) => t.uv_map(u, v, 0),
            TextureType::Fixed(t) => t.uv_map(u, v, 0),
            TextureType::Atlas(t) => t.uv_map(u, v, idx),
            TextureType::Noise(t) => t.uv_map(u, v, 0),
            TextureType::AtlasCustom(texture_atlas) => texture_atlas.uv_map(u, v, idx),
        }
    }

    fn get_width(&self) -> usize {
        match self {
            TextureType::Custom(t) => t.get_width(),
            TextureType::Fixed(t) => t.get_width(),
            TextureType::Atlas(t) => t.get_width(),
            TextureType::Noise(_) => SIZE,
            TextureType::AtlasCustom(texture_atlas) => texture_atlas.get_width(),
        }
    }

    fn get_height(&self) -> usize {
        match self {
            TextureType::Custom(t) => t.get_height(),
            TextureType::Fixed(t) => t.get_height(),
            TextureType::Atlas(t) => t.get_height(),
            TextureType::Noise(_) => SIZE,
            TextureType::AtlasCustom(texture_atlas) => texture_atlas.get_height(),
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

    fn add_atlas_texture_from_iter(
        &mut self,
        py: Python,
        width: usize,
        height: usize,
        pixels: Py<PyList>,
        pix_size_width: usize,
        pix_size_height: usize,
    ) -> usize {
        let pixel_iter = pixels.bind(py).cast::<PyList>().unwrap();
        let texture_iter = TextureIterator::new(py, pixel_iter);

        self.data.add_atlas_texture_from_iter(
            width,
            height,
            pix_size_width,
            pix_size_height,
            texture_iter,
        )
    }
    fn add_noise_texture(&mut self, seed: i32, int_config: i32) -> usize {
        self.data.add_noise_texture(seed, int_config)
    }

    fn get_rgba_at(&self, idx: usize, u: f32, v: f32) -> (u8, u8, u8, u8) {
        let c = self.data.get_rgba_at(idx, u, v, 0);
        (c.r, c.g, c.b, c.a)
    }
}
