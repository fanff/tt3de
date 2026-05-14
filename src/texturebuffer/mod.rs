use crate::utils::convert_tuple_texture_rgba;
use pyo3::{
    pyclass, pymethods,
    types::{PyAnyMethods, PyList},
    Bound, Py, PyAny, Python,
};

pub mod noise_texture;
use noise_texture::*;
pub mod atlas_texture;
use atlas_texture::*;
pub mod texture_buffer;
use texture_buffer::*;

pub mod toglyph_methods_py;
pub mod toglyph_methods;

#[derive(Clone, Copy, PartialEq, Debug)]
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
            r: (self.r as f32 * f).round() as u8,
            g: (self.g as f32 * f).round() as u8,
            b: (self.b as f32 * f).round() as u8,
            a: self.a,
        }
    }
    pub fn luminance(&self) -> f32 {
        0.2126 * (self.r as f32) + 0.7152 * (self.g as f32) + 0.0722 * (self.b as f32)
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum FilterMode {
    Nearest,
    Bilinear,
}

#[inline(always)]
fn lerp_rgba(a: RGBA, b: RGBA, t: f32) -> RGBA {
    RGBA {
        r: (a.r as f32 + (b.r as f32 - a.r as f32) * t).round() as u8,
        g: (a.g as f32 + (b.g as f32 - a.g as f32) * t).round() as u8,
        b: (a.b as f32 + (b.b as f32 - a.b as f32) * t).round() as u8,
        a: (a.a as f32 + (b.a as f32 - a.a as f32) * t).round() as u8,
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
    data: Box<[RGBA]>,
    repeat_x: bool,
    repeat_y: bool,
    filter_mode: FilterMode,
}

impl<const SIZE: usize> Texture<SIZE> {
    pub fn new(data: RGBA, repeat_x: bool, repeat_y: bool, filter_mode: FilterMode) -> Self {
        let d = vec![data; SIZE * SIZE].into_boxed_slice();
        Texture {
            data: d,
            repeat_x,
            repeat_y,
            filter_mode,
        }
    }
    pub fn from_iter<I: IntoIterator<Item = RGBA>>(
        iter: I,
        repeat_x: bool,
        repeat_y: bool,
        filter_mode: FilterMode,
    ) -> Self {
        let data: Vec<RGBA> = iter.into_iter().collect();
        Texture {
            data: data.into_boxed_slice(),
            repeat_x,
            repeat_y,
            filter_mode,
        }
    }
    #[inline(always)]
    pub fn uv_map_inline(&self, u: f32, v: f32) -> RGBA {
        let tx = u * (SIZE as f32);
        let ty = v * (SIZE as f32);

        let ix = tx.floor() as isize;
        let iy = ty.floor() as isize;
        let fx = tx - (ix as f32);
        let fy = ty - (iy as f32);

        let ix0 = if self.repeat_x {
            (ix & (SIZE as isize - 1)) as usize
        } else {
            ix.clamp(0, (SIZE - 1) as isize) as usize
        };

        if self.filter_mode == FilterMode::Nearest {
            let iy0 = if self.repeat_y {
                (iy & (SIZE as isize - 1)) as usize
            } else {
                iy.clamp(0, (SIZE - 1) as isize) as usize
            };
            let shift = SIZE.trailing_zeros() as usize;
            return self.data[(iy0 << shift) + ix0];
        }

        let ix1 = if self.repeat_x {
            ((ix + 1) & (SIZE as isize - 1)) as usize
        } else {
            (ix + 1).clamp(0, (SIZE - 1) as isize) as usize
        };
        let iy0 = if self.repeat_y {
            (iy & (SIZE as isize - 1)) as usize
        } else {
            iy.clamp(0, (SIZE - 1) as isize) as usize
        };
        let iy1 = if self.repeat_y {
            ((iy + 1) & (SIZE as isize - 1)) as usize
        } else {
            (iy + 1).clamp(0, (SIZE - 1) as isize) as usize
        };

        let shift = SIZE.trailing_zeros() as usize;
        let row0 = iy0 << shift;
        let row1 = iy1 << shift;

        let c00 = self.data[row0 + ix0];
        let c10 = self.data[row0 + ix1];
        let c01 = self.data[row1 + ix0];
        let c11 = self.data[row1 + ix1];

        lerp_rgba(lerp_rgba(c00, c10, fx), lerp_rgba(c01, c11, fx), fy)
    }
}

#[derive(Clone)]
pub struct TextureCustom<const SIZE: usize> {
    texture: Texture<SIZE>,
    width: usize,
    height: usize,
    repeat_x: bool,
    repeat_y: bool,
    filter_mode: FilterMode,
}

impl<const SIZE: usize> TextureCustom<SIZE> {
    pub fn new<I: IntoIterator<Item = RGBA>>(
        iter: I,
        width: usize,
        height: usize,
        repeat_x: bool,
        repeat_y: bool,
        filter_mode: FilterMode,
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
                filter_mode,
            },
            width,
            height,
            repeat_x,
            repeat_y,
            filter_mode,
        }
    }

    pub fn uv_map_inline(&self, u: f32, v: f32) -> RGBA {
        let u_val = if self.repeat_x {
            u.rem_euclid(1.0)
        } else {
            u.clamp(0.0, 1.0)
        };
        let v_val = if self.repeat_y {
            v.rem_euclid(1.0)
        } else {
            v.clamp(0.0, 1.0)
        };

        let tx = u_val * self.width as f32;
        let ty = v_val * self.height as f32;

        let ix = tx.floor() as isize;
        let iy = ty.floor() as isize;
        let fx = tx - (ix as f32);
        let fy = ty - (iy as f32);

        let w = self.width as isize;
        let h = self.height as isize;
        let wm1 = w - 1;
        let hm1 = h - 1;

        let ix0 = if self.repeat_x {
            ix.rem_euclid(w) as usize
        } else {
            ix.clamp(0, wm1) as usize
        };

        if self.filter_mode == FilterMode::Nearest {
            let iy0 = if self.repeat_y {
                iy.rem_euclid(h) as usize
            } else {
                iy.clamp(0, hm1) as usize
            };
            return self.texture.data[iy0 * self.width + ix0];
        }

        let ix1 = if self.repeat_x {
            (ix + 1).rem_euclid(w) as usize
        } else {
            (ix + 1).clamp(0, wm1) as usize
        };
        let iy0 = if self.repeat_y {
            iy.rem_euclid(h) as usize
        } else {
            iy.clamp(0, hm1) as usize
        };
        let iy1 = if self.repeat_y {
            (iy + 1).rem_euclid(h) as usize
        } else {
            (iy + 1).clamp(0, hm1) as usize
        };

        let c00 = self.texture.data[iy0 * self.width + ix0];
        let c10 = self.texture.data[iy0 * self.width + ix1];
        let c01 = self.texture.data[iy1 * self.width + ix0];
        let c11 = self.texture.data[iy1 * self.width + ix1];

        lerp_rgba(lerp_rgba(c00, c10, fx), lerp_rgba(c01, c11, fx), fy)
    }
}

impl<const SIZE: usize> Texture<SIZE> {
    pub fn new(data: RGBA, repeat_x: bool, repeat_y: bool, filter_mode: FilterMode) -> Self {
        let d = vec![data; SIZE * SIZE].into_boxed_slice();
        Texture {
            data: d,
            repeat_x,
            repeat_y,
            filter_mode,
        }
    }
    pub fn from_iter<I: IntoIterator<Item = RGBA>>(
        iter: I,
        repeat_x: bool,
        repeat_y: bool,
        filter_mode: FilterMode,
    ) -> Self {
        let data: Vec<RGBA> = iter.into_iter().collect();
        Texture {
            data: data.into_boxed_slice(),
            repeat_x,
            repeat_y,
            filter_mode,
        }
    }
    #[inline(always)]
    pub fn uv_map_inline(&self, u: f32, v: f32) -> RGBA {
        let tx = u * (SIZE as f32);
        let ty = v * (SIZE as f32);

        let ix = tx.floor() as isize;
        let iy = ty.floor() as isize;
        let fx = tx - (ix as f32);
        let fy = ty - (iy as f32);

        let ix0 = if self.repeat_x {
            (ix & (SIZE as isize - 1)) as usize
        } else {
            ix.clamp(0, (SIZE - 1) as isize) as usize
        };

        if self.filter_mode == FilterMode::Nearest {
            let iy0 = if self.repeat_y {
                (iy & (SIZE as isize - 1)) as usize
            } else {
                iy.clamp(0, (SIZE - 1) as isize) as usize
            };
            let shift = SIZE.trailing_zeros() as usize;
            return self.data[(iy0 << shift) + ix0];
        }

        let ix1 = if self.repeat_x {
            ((ix + 1) & (SIZE as isize - 1)) as usize
        } else {
            (ix + 1).clamp(0, (SIZE - 1) as isize) as usize
        };
        let iy0 = if self.repeat_y {
            (iy & (SIZE as isize - 1)) as usize
        } else {
            iy.clamp(0, (SIZE - 1) as isize) as usize
        };
        let iy1 = if self.repeat_y {
            ((iy + 1) & (SIZE as isize - 1)) as usize
        } else {
            (iy + 1).clamp(0, (SIZE - 1) as isize) as usize
        };

        let shift = SIZE.trailing_zeros() as usize;
        let row0 = iy0 << shift;
        let row1 = iy1 << shift;

        let c00 = self.data[row0 + ix0];
        let c10 = self.data[row0 + ix1];
        let c01 = self.data[row1 + ix0];
        let c11 = self.data[row1 + ix1];

        lerp_rgba(lerp_rgba(c00, c10, fx), lerp_rgba(c01, c11, fx), fy)
    }
}

#[derive(Clone)]
pub struct TextureCustom<const SIZE: usize> {
    texture: Texture<SIZE>,
    width: usize,
    height: usize,
    repeat_x: bool,
    repeat_y: bool,
    filter_mode: FilterMode,
}

impl<const SIZE: usize> TextureCustom<SIZE> {
    pub fn new<I: IntoIterator<Item = RGBA>>(
        iter: I,
        width: usize,
        height: usize,
        repeat_x: bool,
        repeat_y: bool,
        filter_mode: FilterMode,
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
                filter_mode,
            },
            width,
            height,
            repeat_x,
            repeat_y,
            filter_mode,
        }
    }

    pub fn uv_map_inline(&self, u: f32, v: f32) -> RGBA {
        let u_val = if self.repeat_x {
            u.rem_euclid(1.0)
        } else {
            u.clamp(0.0, 1.0)
        };
        let v_val = if self.repeat_y {
            v.rem_euclid(1.0)
        } else {
            v.clamp(0.0, 1.0)
        };

        let tx = u_val * self.width as f32;
        let ty = v_val * self.height as f32;

        let ix = tx.floor() as isize;
        let iy = ty.floor() as isize;
        let fx = tx - (ix as f32);
        let fy = ty - (iy as f32);

        let w = self.width as isize;
        let h = self.height as isize;
        let wm1 = w - 1;
        let hm1 = h - 1;

        let ix0 = if self.repeat_x {
            ix.rem_euclid(w) as usize
        } else {
            ix.clamp(0, wm1) as usize
        };

        if self.filter_mode == FilterMode::Nearest {
            let iy0 = if self.repeat_y {
                iy.rem_euclid(h) as usize
            } else {
                iy.clamp(0, hm1) as usize
            };
            return self.texture.data[iy0 * self.width + ix0];
        }

        let ix1 = if self.repeat_x {
            (ix + 1).rem_euclid(w) as usize
        } else {
            (ix + 1).clamp(0, wm1) as usize
        };
        let iy0 = if self.repeat_y {
            iy.rem_euclid(h) as usize
        } else {
            iy.clamp(0, hm1) as usize
        };
        let iy1 = if self.repeat_y {
            (iy + 1).rem_euclid(h) as usize
        } else {
            (iy + 1).clamp(0, hm1) as usize
        };

        let c00 = self.texture.data[iy0 * self.width + ix0];
        let c10 = self.texture.data[iy0 * self.width + ix1];
        let c01 = self.texture.data[iy1 * self.width + ix0];
        let c11 = self.texture.data[iy1 * self.width + ix1];

        lerp_rgba(lerp_rgba(c00, c10, fx), lerp_rgba(c01, c11, fx), fy)
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
    ) -> usize {
        let fm = parse_filter_mode(filter_mode);
        let pixel_iter = pixels.bind(py).cast::<PyList>().unwrap();
        let texture_iter = TextureIterator::new(py, pixel_iter);

        self.data
            .add_texture_from_iter(width, height, texture_iter, repeat_width, repeat_height, fm)
    }

fn parse_filter_mode(mode: &str) -> FilterMode {
    match mode.to_lowercase().as_str() {
        "nearest" => FilterMode::Nearest,
        "bilinear" => FilterMode::Bilinear,
        _ => panic!("Unknown filter_mode: '{}'. Expected 'nearest' or 'bilinear'.", mode),
    }
}

fn parse_filter_mode(mode: &str) -> FilterMode {
    match mode.to_lowercase().as_str() {
        "nearest" => FilterMode::Nearest,
        "bilinear" => FilterMode::Bilinear,
        _ => panic!("Unknown filter_mode: '{}'. Expected 'nearest' or 'bilinear'.", mode),
    }
}

    fn add_atlas_texture_from_iter(
        &mut self,
        py: Python,
        width: usize,
        height: usize,
        pixels: Py<PyList>,
        pix_size_width: usize,
        pix_size_height: usize,
        filter_mode: &str,
    ) -> usize {
        let fm = parse_filter_mode(filter_mode);
        let pixel_iter = pixels.bind(py).cast::<PyList>().unwrap();
        let texture_iter = TextureIterator::new(py, pixel_iter);

        self.data.add_atlas_texture_from_iter(
            width,
            height,
            pix_size_width,
            pix_size_height,
            texture_iter,
            fm,
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lerp_rgba_exact() {
        let a = RGBA::new(0, 0, 0, 0);
        let b = RGBA::new(255, 255, 255, 255);
        assert_eq!(lerp_rgba(a, b, 0.0), a);
        assert_eq!(lerp_rgba(a, b, 1.0), b);
    }

    #[test]
    fn test_lerp_rgba_half() {
        let a = RGBA::new(0, 0, 0, 0);
        let b = RGBA::new(100, 200, 50, 128);
        let mid = lerp_rgba(a, b, 0.5);
        assert_eq!(mid, RGBA::new(50, 100, 25, 64));
    }

    #[test]
    fn test_texture_bilinear_center() {
        let data = vec![
            RGBA::new(10, 0, 0, 255),  // (0,0)
            RGBA::new(20, 0, 0, 255),  // (1,0)
            RGBA::new(30, 0, 0, 255),  // (2,0)
            RGBA::new(40, 0, 0, 255),  // (3,0)
            RGBA::new(50, 0, 0, 255),  // (0,1)
            RGBA::new(60, 0, 0, 255),  // (1,1)
            RGBA::new(70, 0, 0, 255),  // (2,1)
            RGBA::new(80, 0, 0, 255),  // (3,1)
            RGBA::new(90, 0, 0, 255),  // (0,2)
            RGBA::new(100, 0, 0, 255), // (1,2)
            RGBA::new(110, 0, 0, 255), // (2,2)
            RGBA::new(120, 0, 0, 255), // (3,2)
            RGBA::new(130, 0, 0, 255), // (0,3)
            RGBA::new(140, 0, 0, 255), // (1,3)
            RGBA::new(150, 0, 0, 255), // (2,3)
            RGBA::new(160, 0, 0, 255), // (3,3)
        ];
        let tex = Texture::<4>::from_iter(data, false, false, FilterMode::Bilinear);

        // At the corner of texels (1,1) / (2,1) / (1,2) / (2,2):
        // u = 1.5/4 = 0.375, v = 1.5/4 = 0.375
        // tx = 1.5, ty = 1.5 → ix=1, iy=1, fx=0.5, fy=0.5
        // Should average (60, 70, 100, 110) → (85, 0, 0, 255)
        let result = tex.uv_map_inline(0.375, 0.375);
        assert_eq!(result, RGBA::new(85, 0, 0, 255));
    }

    #[test]
    fn test_texture_bilinear_edge_clamp() {
        let data = vec![
            RGBA::new(10, 0, 0, 255), // (0,0)
            RGBA::new(20, 0, 0, 255), // (1,0)
            RGBA::new(30, 0, 0, 255), // (0,1)
            RGBA::new(40, 0, 0, 255), // (1,1)
        ];
        let tex = Texture::<2>::from_iter(data, false, false, FilterMode::Bilinear);

        // At u=0.75, v=0.75 → texel-space (1.5, 1.5)
        // floor=1,1 fract=0.5,0.5
        // ix0=1, ix1=1 (clamped), iy0=1, iy1=1 (clamped)
        // all samples from (1,1)=40
        let result = tex.uv_map_inline(0.75, 0.75);
        assert_eq!(result, RGBA::new(40, 0, 0, 255));
    }

    #[test]
    fn test_texture_bilinear_repeat_wrap() {
        let data = vec![
            RGBA::new(10, 0, 0, 255), // (0,0)
            RGBA::new(20, 0, 0, 255), // (1,0)
            RGBA::new(30, 0, 0, 255), // (0,1)
            RGBA::new(40, 0, 0, 255), // (1,1)
        ];
        let tex = Texture::<2>::from_iter(data, true, true, FilterMode::Bilinear);

        // At u=0.25, v=0.25 → texel-space (0.5, 0.5)
        // ix=0, iy=0, fx=0.5, fy=0.5
        // Average of (10, 20, 30, 40) = 25
        let result = tex.uv_map_inline(0.25, 0.25);
        assert_eq!(result, RGBA::new(25, 0, 0, 255));
    }

    #[test]
    fn test_texture_custom_bilinear_center() {
        let data = vec![
            RGBA::new(10, 0, 0, 255), // (0,0)
            RGBA::new(20, 0, 0, 255), // (1,0)
            RGBA::new(30, 0, 0, 255), // (2,0)
            RGBA::new(40, 0, 0, 255), // (3,0)
            RGBA::new(50, 0, 0, 255), // (0,1)
            RGBA::new(60, 0, 0, 255), // (1,1)
            RGBA::new(70, 0, 0, 255), // (2,1)
            RGBA::new(80, 0, 0, 255), // (3,1)
            RGBA::new(90, 0, 0, 255), // (0,2)
            RGBA::new(100, 0, 0, 255), // (1,2)
            RGBA::new(110, 0, 0, 255), // (2,2)
            RGBA::new(120, 0, 0, 255), // (3,2)
            RGBA::new(130, 0, 0, 255), // (0,3)
            RGBA::new(140, 0, 0, 255), // (1,3)
            RGBA::new(150, 0, 0, 255), // (2,3)
            RGBA::new(160, 0, 0, 255), // (3,3)
        ];
        let tex = TextureCustom::<8>::new(data, 4, 4, false, false, FilterMode::Bilinear);

        // Same test as Texture bilinear center: at (1.5, 1.5) in texel space
        let result = tex.uv_map_inline(1.5 / 4.0, 1.5 / 4.0);
        assert_eq!(result, RGBA::new(85, 0, 0, 255));
    }

    #[test]
    fn test_texture_custom_bilinear_repeat() {
        let data = vec![
            RGBA::new(10, 0, 0, 255), // (0,0)
            RGBA::new(20, 0, 0, 255), // (1,0)
            RGBA::new(30, 0, 0, 255), // (0,1)
            RGBA::new(40, 0, 0, 255), // (1,1)
        ];
        let tex = TextureCustom::<8>::new(data, 2, 2, true, true, FilterMode::Bilinear);

        // At u=1.25, v=0.25 → wraps to (0.25, 0.25) → same as Texture repeat test
        let result = tex.uv_map_inline(1.25, 0.25);
        assert_eq!(result, RGBA::new(25, 0, 0, 255));
    }
}
