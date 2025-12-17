use nalgebra_glm::Vec2;

use crate::texturebuffer::UvMapper;

use super::{NoiseTexture, Texture, TextureAtlas, TextureCustom, TextureType, RGBA};

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
) -> TextureType<SIZE> {
    let texture_type = if width == SIZE && height == SIZE {
        TextureType::Fixed(Texture::<SIZE>::from_iter(
            input,
            repeat_width,
            repeat_height,
        ))
    } else {
        TextureType::Custom(TextureCustom::<SIZE>::new(
            input,
            width,
            height,
            repeat_width,
            repeat_height,
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
        let init_texture = TextureType::Fixed(Texture::<SIZE>::new(init_color, true, true));
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
            TextureType::AtlasCustom(texture_atlas) => todo!(),
        }
    }
    pub fn add_texture_from_iter<I: IntoIterator<Item = RGBA>>(
        &mut self,
        width: usize,
        height: usize,
        input: I,
        repeat_width: bool,
        repeat_height: bool,
    ) -> usize {
        if self.current_size >= self.max_size {
            panic!("Texture buffer is full");
        }

        let texture_type = make_texture::<SIZE>(width, height, input, repeat_width, repeat_height);

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
    ) -> usize {
        if self.current_size >= self.max_size {
            panic!("Texture buffer is full");
        }

        if width == SIZE && height == SIZE {
            let text = TextureType::Atlas(TextureAtlas {
                texture: Texture::<SIZE>::from_iter(input, false, false),
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
