use nalgebra_glm::Vec4;

use super::drawbuffer::Color;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BlendMode {
    Replace,
    AlphaBlend,
    Additive,
    GlyphDither,
    HalfBlockComposite,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum GlyphPolicy {
    PreserveExisting,
    ReplaceFromShader,
}

impl Default for BlendMode {
    fn default() -> Self {
        Self::Replace
    }
}

impl Default for GlyphPolicy {
    fn default() -> Self {
        Self::PreserveExisting
    }
}

#[inline]
fn clamp_u8_from_unit(v: f32) -> u8 {
    (v.clamp(0.0, 1.0) * 255.0).round() as u8
}

#[inline]
fn src_rgb(src: &Vec4) -> (f32, f32, f32) {
    (
        src.x.clamp(0.0, 1.0),
        src.y.clamp(0.0, 1.0),
        src.z.clamp(0.0, 1.0),
    )
}

#[inline]
fn dst_rgb(dst: &Color) -> (f32, f32, f32) {
    (
        dst.r as f32 / 255.0,
        dst.g as f32 / 255.0,
        dst.b as f32 / 255.0,
    )
}

pub fn blend_front(dst: &Color, src: &Vec4, mode: BlendMode) -> Color {
    let (sr, sg, sb) = src_rgb(src);
    let (dr, dg, db) = dst_rgb(dst);
    let sa = src.w.clamp(0.0, 1.0);

    let (r, g, b) = match mode {
        BlendMode::Replace => (sr, sg, sb),
        BlendMode::AlphaBlend => (
            sr * sa + dr * (1.0 - sa),
            sg * sa + dg * (1.0 - sa),
            sb * sa + db * (1.0 - sa),
        ),
        BlendMode::Additive => (dr + sr, dg + sg, db + sb),
        // TODO(evol-transparency-depth-layers): add dedicated ASCII-native math.
        // For now these are deterministic conservative fallbacks.
        BlendMode::GlyphDither => (
            sr * sa + dr * (1.0 - sa),
            sg * sa + dg * (1.0 - sa),
            sb * sa + db * (1.0 - sa),
        ),
        BlendMode::HalfBlockComposite => (
            sr * sa + dr * (1.0 - sa),
            sg * sa + dg * (1.0 - sa),
            sb * sa + db * (1.0 - sa),
        ),
    };

    Color::new(
        clamp_u8_from_unit(r),
        clamp_u8_from_unit(g),
        clamp_u8_from_unit(b),
        255,
    )
}

#[cfg(test)]
mod tests {
    use nalgebra_glm::vec4;

    use super::*;

    #[test]
    fn blend_replace_overwrites() {
        let dst = Color::new(255, 0, 0, 255);
        let out = blend_front(&dst, &vec4(0.0, 1.0, 0.0, 1.0), BlendMode::Replace);
        assert_eq!(out, Color::new(0, 255, 0, 255));
    }

    #[test]
    fn blend_alpha_blend_half_mix() {
        let dst = Color::new(255, 0, 0, 255);
        let out = blend_front(&dst, &vec4(0.0, 1.0, 0.0, 0.5), BlendMode::AlphaBlend);
        assert_eq!(out, Color::new(128, 128, 0, 255));
    }

    #[test]
    fn blend_alpha_zero_keeps_dst() {
        let dst = Color::new(255, 255, 255, 255);
        let out = blend_front(&dst, &vec4(0.0, 0.0, 0.0, 0.0), BlendMode::AlphaBlend);
        assert_eq!(out, Color::new(255, 255, 255, 255));
    }

    #[test]
    fn blend_additive_clamps() {
        let dst = Color::new(128, 0, 0, 255);
        let out = blend_front(&dst, &vec4(0.0, 0.0, 1.0, 1.0), BlendMode::Additive);
        assert_eq!(out, Color::new(128, 0, 255, 255));
    }

    #[test]
    fn blend_clamps_input_channels() {
        let dst = Color::new(255, 255, 255, 255);
        let out = blend_front(&dst, &vec4(2.0, -1.0, 0.5, 2.0), BlendMode::AlphaBlend);
        assert_eq!(out, Color::new(255, 0, 128, 255));
    }
}
