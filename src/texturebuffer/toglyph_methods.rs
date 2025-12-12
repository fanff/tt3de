use crate::texturebuffer::RGBA;

pub trait ToGlyphIndex {
    fn to_glyph_index(&self, color: &RGBA) -> u8;
}

#[derive(Clone, Copy, Debug)]
pub enum ToGlyphMethod {
    Static(u8),
    FromAlpha,
    Map4Luminance(u8, u8, u8, u8),
    Map4Color(u8, u8, u8, u8),
}

fn map4<T: PartialOrd<u8> + From<u8>>(value: T, g0: u8, g1: u8, g2: u8, g3: u8) -> u8 {
    if value < 64u8 {
        g0
    } else if value < 128 {
        g1
    } else if value < 192 {
        g2
    } else {
        g3
    }
}
fn map4f<T: PartialOrd<f32> + From<f32>>(value: T, g0: u8, g1: u8, g2: u8, g3: u8) -> u8 {
    if value < 64.0 {
        g0
    } else if value < 128.0 {
        g1
    } else if value < 192.0 {
        g2
    } else {
        g3
    }
}

impl ToGlyphIndex for ToGlyphMethod {
    fn to_glyph_index(&self, color: &RGBA) -> u8 {
        match self {
            ToGlyphMethod::FromAlpha => color.a,
            ToGlyphMethod::Map4Luminance(g0, g1, g2, g3) => {
                let lum = color.luminance();
                // map lum [0..255] to one of the four glyphs
                map4f(lum, *g0, *g1, *g2, *g3)
            }
            ToGlyphMethod::Map4Color(g0, g1, g2, g3) => {
                let lum = color.r;
                map4(lum, *g0, *g1, *g2, *g3)
            }
            ToGlyphMethod::Static(glyphidx) => *glyphidx,
        }
    }
}
