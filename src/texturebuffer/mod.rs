use crate::utils::convert_tuple_texture_rgba;
use pyo3::{pyclass, pymethods, types::PyList, Py, PyAny, Python};

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
        let u = if self.repeat_x {
            u % 1.0
        } else {
            u.clamp(0.0, 1.0)
        };
        let v = if self.repeat_y {
            v % 1.0
        } else {
            v.clamp(0.0, 1.0)
        };

        // Convert u, v to texture coordinates
        let x = (u * SIZE as f32) as usize;
        let y = (v * SIZE as f32) as usize;

        // Return the color at the computed coordinates
        self.data[y * SIZE + x]
    }
}

#[derive(Clone)]
pub struct TextureAtlas<const SIZE: usize> {
    texture: Texture<SIZE>,
    pix_size: usize, // how many pixel size are the atlas elements? 8px is small, 16 is normal
}

#[derive(Clone, Copy)]
pub struct RGBA {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: u8,
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
        let u = if self.repeat_x {
            u % 1.0
        } else {
            u.clamp(0.0, 1.0)
        };
        let v = if self.repeat_y {
            v % 1.0
        } else {
            v.clamp(0.0, 1.0)
        };

        // Convert u, v to texture coordinates
        let x = (u * self.width as f32) as usize;
        let y = (v * self.height as f32) as usize;

        self.texture.data[y * SIZE + x]
    }
}

#[derive(Clone)]
pub enum TextureType<const SIZE: usize> {
    Custom(TextureCustom<SIZE>),
    Fixed(Texture<SIZE>),
    Atlas(TextureAtlas<SIZE>),
}

impl<const SIZE: usize> TextureType<SIZE> {
    pub fn uv_map(&self, u: f32, v: f32) -> RGBA {
        match self {
            TextureType::Custom(t) => t.uv_map(u, v),
            TextureType::Fixed(t) => t.uv_map(u, v),
            TextureType::Atlas(t) => t.texture.uv_map(u, v),
        }
    }
}

pub struct TextureBuffer<const SIZE: usize> {
    pub max_size: usize,
    pub current_size: usize,
    pub textures: Box<[TextureType<SIZE>]>,
}

impl<const SIZE: usize> TextureBuffer<SIZE> {
    pub fn new(max_size: usize) -> TextureBuffer<SIZE> {
        let init_color = RGBA {
            r: 0,
            g: 0,
            b: 0,
            a: 255,
        };
        let init_texture = TextureType::Fixed(Texture::<SIZE>::new(init_color, true, true));
        // Create a fixed-size array of None values
        let textures = vec![init_texture; max_size].into_boxed_slice();

        TextureBuffer {
            max_size,
            current_size: 0,
            textures,
        }
    }

    pub fn get_rgba_at(&self, idx: usize, u: f32, v: f32) -> RGBA {
        let atexture = &self.textures[idx];
        let color = atexture.uv_map(u, v);

        color
    }
    pub fn get_wh_of(&self, idx: usize) -> (usize, usize) {
        let atext = &self.textures[idx];

        match atext {
            TextureType::Custom(t) => (t.width, t.height),
            TextureType::Fixed(_) => (SIZE, SIZE),
            TextureType::Atlas(_) => (SIZE, SIZE),
        }
    }
    pub fn add_texture_from_iter<I: IntoIterator<Item = RGBA>>(
        &mut self,
        width: usize,
        height: usize,
        input: I,
    ) -> usize {
        if self.current_size >= self.max_size {
            panic!("Texture buffer is full");
        }

        let texture_type = if width == SIZE && height == SIZE {
            TextureType::Fixed(Texture::<SIZE>::from_iter(input, true, true))
        } else {
            TextureType::Custom(TextureCustom::<SIZE>::new(input, width, height, true, true))
        };

        self.textures[self.current_size] = texture_type;
        self.current_size += 1;

        self.current_size - 1
    }

    pub fn add_atlas_texture_from_iter<I: IntoIterator<Item = RGBA>>(
        &mut self,
        pix_size: usize,
        input: I,
    ) -> usize {
        if self.current_size >= self.max_size {
            panic!("Texture buffer is full");
        }

        let atlas_texture = TextureAtlas {
            texture: Texture::<SIZE>::from_iter(input, true, true),
            pix_size,
        };

        self.textures[self.current_size] = TextureType::Atlas(atlas_texture);
        self.current_size += 1;
        self.current_size - 1
    }
}

/// START of the python stufff
///
///
///
pub struct TextureIterator<'a> {
    py: Python<'a>,
    pixels: &'a PyList,
    index: usize,
}

impl<'a> TextureIterator<'a> {
    fn new(py: Python<'a>, pixels: &'a PyList) -> Self {
        TextureIterator {
            py,
            pixels,
            index: 0,
        }
    }
}

impl<'a> Iterator for TextureIterator<'a> {
    type Item = RGBA;

    fn next(&mut self) -> Option<Self::Item> {
        if self.index < self.pixels.len() {
            let item: &PyAny = self.pixels.get_item(self.index).ok().unwrap();
            self.index += 1;
            convert_tuple_texture_rgba(self.py, item.into())
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
    fn add_texture(
        &mut self,
        py: Python,
        width: usize,
        height: usize,
        pixels: Py<PyList>,
    ) -> usize {
        let texture_iter = TextureIterator::new(py, &pixels.as_ref(py));

        self.data.add_texture_from_iter(width, height, texture_iter)
    }

    fn get_rgba_at(&self, idx: usize, u: f32, v: f32) -> (u8, u8, u8, u8) {
        let c = self.data.get_rgba_at(idx, u, v);
        (c.r, c.g, c.b, c.a)
    }
}
