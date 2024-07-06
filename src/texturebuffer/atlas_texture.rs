use super::Texture;

#[derive(Clone)]
pub struct TextureAtlas<const SIZE: usize> {
    pub texture: Texture<SIZE>,
    pub pix_size: usize, // how many pixel size are the atlas elements? 8px is small, 16 is normal
}
