use crate::texturebuffer::{Texture, TextureCustom, UvMapper, RGBA};

#[derive(Clone)]
pub struct TextureAtlas<T, const SIZE: usize>
where
    T: UvMapper,
{
    pub texture: T,
    pub pix_size_width: usize, // how many pixel size are the atlas elements? 8px is small, 16 is normal
    pub pix_size_height: usize,
}

impl<T, const SIZE: usize> UvMapper for TextureAtlas<T, SIZE>
where
    T: UvMapper,
{
    fn uv_map(&self, u: f32, v: f32, idx: usize) -> RGBA {
        // idx determines which sub-texture to use;
        // iterating top to bottom, left to right
        // Calculate number of textures per row
        let textures_per_row = self.texture.get_width() / self.pix_size_width;
        let row = textures_per_row - (idx / textures_per_row) - 1;
        let col = idx % textures_per_row;
        let u_offset = (col * self.pix_size_width) as f32 / self.texture.get_width() as f32;
        let v_offset = (row * self.pix_size_height) as f32 / self.texture.get_height() as f32;

        // Delegates to the backing texture
        //self.texture.uv_map(
        //    u / self.get_width() as f32 + u_offset,
        //    v / self.get_height() as f32 + v_offset,
        //    0,
        //)
        self.texture.uv_map(
            u / textures_per_row as f32 + u_offset,
            v / (self.texture.get_height() / self.pix_size_height) as f32 + v_offset,
            0,
        )
    }

    fn get_width(&self) -> usize {
        self.texture.get_width()
    }

    fn get_height(&self) -> usize {
        self.texture.get_height()
    }
}
