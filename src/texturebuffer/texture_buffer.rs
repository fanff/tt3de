use nalgebra_glm::{Vec2, Vec4};

use crate::texturebuffer::UvMapper;

use super::{FilterMode, NoiseTexture, Texture, TextureAtlas, TextureCustom, TextureType, RGBA};

pub struct TextureBuffer<const SIZE: usize> {
    pub max_size: usize,
    pub current_size: usize,
    pub textures: Box<[TextureType<SIZE>]>,
}

fn make_texture<const SIZE: usize>(
    width: usize,
    height: usize,
    input: impl IntoIterator<Item = RGBA>,
    repeat_width: bool,
    repeat_height: bool,
    filter_mode: FilterMode,
) -> TextureType<SIZE> {
    let texture_type = if width == SIZE && height == SIZE {
        TextureType::Fixed(Texture::<SIZE>::from_iter(
            input,
            repeat_width,
            repeat_height,
            filter_mode,
        ))
    } else {
        TextureType::Custom(TextureCustom::<SIZE>::new(
            input,
            width,
            height,
            repeat_width,
            repeat_height,
            filter_mode,
        ))
    };
    texture_type
}
impl<const SIZE: usize> TextureBuffer<SIZE> {
    pub fn new(max_size: usize) -> TextureBuffer<SIZE> {
        let init_color = RGBA {
            r: 0,
            g: 0,
            b: 0,
            a: 255,
        };
        let init_texture = TextureType::Fixed(Texture::<SIZE>::new(init_color, true, true, FilterMode::Bilinear));
        // Create a fixed-size array of None values
        let textures = vec![init_texture; max_size].into_boxed_slice();

        TextureBuffer {
            max_size,
            current_size: 0,
            textures,
        }
    }

    pub fn get_rgba_at(&self, texture_idx: usize, u: f32, v: f32, uv_idx: usize) -> RGBA {
        let atexture = &self.textures[texture_idx];

        atexture.uv_map(u, v, uv_idx)
    }

    pub fn get_rgba_at_v(&self, idx: usize, uv: &Vec2, uv_idx: usize) -> RGBA {
        let atexture = &self.textures[idx];

        atexture.uv_map(uv.x, uv.y, uv_idx)
    }

    pub fn get_wh_of(&self, idx: usize) -> (usize, usize) {
        let atext = &self.textures[idx];

        match atext {
            TextureType::Custom(t) => (t.width, t.height),
            TextureType::Fixed(_) => (SIZE, SIZE),
            TextureType::Atlas(_) => (SIZE, SIZE),
            TextureType::Noise(_) => (SIZE, SIZE),
            TextureType::AtlasCustom(_texture_atlas) => todo!(),
        }
    }
    pub fn add_texture_from_iter<I: IntoIterator<Item = RGBA>>(
        &mut self,
        width: usize,
        height: usize,
        input: I,
        repeat_width: bool,
        repeat_height: bool,
        filter_mode: FilterMode,
    ) -> usize {
        if self.current_size >= self.max_size {
            panic!("Texture buffer is full");
        }

        let texture_type = make_texture::<SIZE>(width, height, input, repeat_width, repeat_height, filter_mode);

        self.textures[self.current_size] = texture_type;
        self.current_size += 1;

        self.current_size - 1
    }
    pub fn add_noise_texture(&mut self, seed: i32, int_config: i32) -> usize {
        if self.current_size >= self.max_size {
            panic!("Texture buffer is full");
        }

        let noise_texture = NoiseTexture::new(seed, int_config);

        self.textures[self.current_size] = TextureType::Noise(noise_texture);
        self.current_size += 1;
        self.current_size - 1
    }
    pub fn add_atlas_texture_from_iter<I: IntoIterator<Item = RGBA>>(
        &mut self,
        width: usize,
        height: usize,
        pix_size_width: usize,
        pix_size_height: usize,
        input: I,
        filter_mode: FilterMode,
    ) -> usize {
        if self.current_size >= self.max_size {
            panic!("Texture buffer is full");
        }

        if width == SIZE && height == SIZE {
            let text = TextureType::Atlas(TextureAtlas {
                texture: Texture::<SIZE>::from_iter(input, false, false, filter_mode),
                pix_size_width,
                pix_size_height,
            });
            self.textures[self.current_size] = text;
        } else {
            let text = TextureType::AtlasCustom(
                TextureAtlas {
                    texture: TextureCustom::<SIZE>::new(
                        input,
                        width,
                        height,
                        false,
                        false,
                        filter_mode,
                    ),
                    pix_size_width,
                    pix_size_height,
                },

            );

            self.textures[self.current_size] = text;
        }

        if width == SIZE && height == SIZE {
            let text = TextureType::Atlas(TextureAtlas {
                texture: Texture::<SIZE>::from_iter(input, false, false, filter_mode),
                pix_size_width,
                pix_size_height,
            });
            self.textures[self.current_size] = text;
        } else {
            let text = TextureType::AtlasCustom(
                TextureAtlas {
                    texture: TextureCustom::<SIZE>::new(
                        input,
                        width,
                        height,
                        false,
                        false,
                        filter_mode,
                    ),
                    pix_size_width,
                    pix_size_height,
                },

            );

            self.textures[self.current_size] = text;
        }
        self.current_size += 1;
        self.current_size - 1
    }
}

impl<const SIZE: usize> crate::ttsl::TtslTextureEnv for TextureBuffer<SIZE> {
    fn sample_tt_texture(&self, idx: i32, uv: Vec2) -> Vec4 {
        if idx < 0 {
            return Vec4::new(0.0, 0.0, 0.0, 1.0);
        }
        let ui = idx as usize;
        if ui >= self.current_size || ui >= self.max_size {
            return Vec4::new(0.0, 0.0, 0.0, 1.0);
        }
        let rgba = self.get_rgba_at_v(ui, &uv, 0);
        Vec4::new(
            rgba.r as f32 / 255.0,
            rgba.g as f32 / 255.0,
            rgba.b as f32 / 255.0,
            rgba.a as f32 / 255.0,
        )
    }
}
