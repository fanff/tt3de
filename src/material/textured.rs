use nalgebra::Matrix1x4;
use nalgebra_glm::{TVec4, Vec3, Vec4};

use crate::{
    drawbuffer::{
        drawbuffer::{CanvasCell, Color, DepthBufferCell, PixInfo},
        glyphset::{HALF_UPPER_BLOCK, SPACE},
    },
    primitivbuffer::primitivbuffer::PrimitiveElements,
    texturebuffer::{
        texture_buffer::TextureBuffer,
        toglyph_methods::{ToGlyphIndex, ToGlyphMethod},
        RGBA,
    },
    vertexbuffer::uv_buffer::UVBuffer,
};

use super::materials::RenderMaterial;

#[derive(Clone, Copy, Debug)]
pub struct BaseTexture {
    pub albedo_texture_idx: usize,
    pub albedo_texture_subid: usize,
    pub glyph_texture_idx: usize,
    pub glyph_texture_subid: usize,
    pub front: bool,
    pub back: bool,
    pub glyph: bool,

    pub front_uv_0: bool,
    pub back_uv_0: bool,
    pub glyph_uv_0: bool,
    pub to_glyph_method: ToGlyphMethod,
}
impl BaseTexture {
    pub fn new(
        albedo_texture_idx: usize,
        albedo_texture_subid: usize,
        glyph_texture_idx: usize,
        glyph_texture_subid: usize,
        front: bool,
        back: bool,
        glyph: bool,
        front_uv_0: bool,
        back_uv_0: bool,
        glyph_uv_0: bool,
        to_glyph_method: ToGlyphMethod,
    ) -> Self {
        Self {
            albedo_texture_idx,
            albedo_texture_subid,
            glyph_texture_idx,
            glyph_texture_subid,
            front,
            back,
            glyph,
            front_uv_0,
            back_uv_0,
            glyph_uv_0,
            to_glyph_method: to_glyph_method,
        }
    }
}
impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize>
    RenderMaterial<TEXTURE_BUFFER_SIZE, DEPTHLAYER> for BaseTexture
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        _depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        _depth_layer: usize,
        pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        _uv_buffer: &UVBuffer<f32>,
    ) {
        // first we handle the glyph if necessary
        let mut applyied_glyph: Option<u8> = None;
        if self.glyph {
            let uv = {
                if self.glyph_uv_0 {
                    pixinfo.uv
                } else {
                    pixinfo.uv_1
                }
            };

            match self.to_glyph_method {
                ToGlyphMethod::Static(glyphidx) => {
                    //cell.glyph = glyphidx;
                    applyied_glyph = Some(glyphidx);
                }
                _ => {
                    let texture_color = texture_buffer.get_rgba_at_v(
                        self.glyph_texture_idx,
                        &uv,
                        self.glyph_texture_subid,
                    );
                    //cell.glyph = self.to_glyph_method.to_glyph_index(&texture_color);
                    applyied_glyph = Some(self.to_glyph_method.to_glyph_index(&texture_color));
                }
            }
        }

        match applyied_glyph {
            Some(glyphidx) => {
                if glyphidx == HALF_UPPER_BLOCK && (self.front && self.back) {
                    // half upper block , we blend half to front color, half to back color
                    let front_color = texture_buffer.get_rgba_at_v(
                        self.albedo_texture_idx,
                        &{
                            if self.front_uv_0 {
                                pixinfo.uv
                            } else {
                                pixinfo.uv_1
                            }
                        },
                        self.albedo_texture_subid,
                    );

                    let back_color = texture_buffer.get_rgba_at_v(
                        self.albedo_texture_idx,
                        &{
                            if self.back_uv_0 {
                                pixinfo.uv
                            } else {
                                pixinfo.uv_1
                            }
                        },
                        self.albedo_texture_subid,
                    );
                    blend_half_upper_to_cell(cell, (&front_color), (&back_color));
                    return;
                } else {
                    cell.glyph = glyphidx;
                }
            }
            None => {}
        }

        if self.front_uv_0 == self.back_uv_0 {
            // only one UV
            let uv = {
                if self.front_uv_0 {
                    pixinfo.uv
                } else {
                    pixinfo.uv_1
                }
            };

            //

            let texture_color = texture_buffer.get_rgba_at_v(
                self.albedo_texture_idx,
                &uv,
                self.albedo_texture_subid,
            );

            if self.front {
                blend_color_to_cell_single(&mut cell.front_color, &texture_color);
            }
            if self.back {
                blend_color_to_cell_single(&mut cell.back_color, &texture_color);
            }
        } else {
            // two UVs
            if self.front {
                let uv_front = {
                    if self.front_uv_0 {
                        pixinfo.uv
                    } else {
                        pixinfo.uv_1
                    }
                };
                let texture_color_front = texture_buffer.get_rgba_at_v(
                    self.albedo_texture_idx,
                    &uv_front,
                    self.albedo_texture_subid,
                );
                blend_color_to_cell_single(&mut cell.front_color, &texture_color_front);
            }
            if self.back {
                let uv_back = {
                    if self.back_uv_0 {
                        pixinfo.uv
                    } else {
                        pixinfo.uv_1
                    }
                };
                let texture_color_back = texture_buffer.get_rgba_at_v(
                    self.albedo_texture_idx,
                    &uv_back,
                    self.albedo_texture_subid,
                );
                blend_color_to_cell_single(&mut cell.back_color, &texture_color_back);
            }
        }
    }
}

fn blend_half_upper_to_cell(cell: &mut CanvasCell, color_f: &RGBA, color_b: &RGBA) {
    if cell.glyph == HALF_UPPER_BLOCK {
        // already half upper block, just blend colors
        blend_color_to_cell_single(&mut cell.front_color, color_f);
        blend_color_to_cell_single(&mut cell.back_color, color_b);
    } else {
        cell.glyph = HALF_UPPER_BLOCK;
        if color_f.a == 0 {
            if color_b.a == 0 {
                cell.front_color = cell.back_color;
            } else {
                blend_color_to_cell_single(&mut cell.back_color, color_b);
                cell.front_color = cell.back_color
            }
        } else {
            if color_b.a == 0 {
                blend_color_to_cell_single(&mut cell.front_color, color_f);
                //cell.back_color = cell.back_color;
            } else {
                blend_color_to_cell_single(&mut cell.front_color, color_f);
                blend_color_to_cell_single(&mut cell.back_color, color_b);
            }
        }
    }
}

fn blend_color_to_cell_single(cell_color: &mut Color, color: &RGBA) {
    if color.a == 0 {
        // fully transparent , do nothing
        return;
    } else if color.a == 255 {
        // opaque , just copy
        cell_color.r = color.r;
        cell_color.g = color.g;
        cell_color.b = color.b;
        cell_color.a = 255;
        return;
    } else {
        // simple alpha blending
        let alpha = color.a as f32 / 255.0;
        let inv_alpha = 1.0 - alpha;

        cell_color.r = (color.r as f32 * alpha + cell_color.r as f32 * inv_alpha) as u8;
        cell_color.g = (color.g as f32 * alpha + cell_color.g as f32 * inv_alpha) as u8;
        cell_color.b = (color.b as f32 * alpha + cell_color.b as f32 * inv_alpha) as u8;
        cell_color.a = 255;
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Textured {
    pub albedo_texture_idx: usize,
    pub glyph_idx: u8,
}
impl Textured {
    pub fn new(albedo_texture_idx: usize, glyph_idx: u8) -> Self {
        Self {
            albedo_texture_idx,
            glyph_idx,
        }
    }
}
impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize>
    RenderMaterial<TEXTURE_BUFFER_SIZE, DEPTHLAYER> for Textured
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        _depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        _depth_layer: usize,
        pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        _uv_buffer: &UVBuffer<f32>,
    ) {
        let uv = pixinfo.uv;
        let uv1 = pixinfo.uv_1;

        // vec3 , normal vector at this pixel, in camera space (0,0,1)
        let normal = pixinfo.normal;

        // calculate alignment between camera and normal vector using a dot product
        let shading = normal
            .normalize()
            .dot(&Vec3::new(0.0, 0.0, -1.0))
            .abs()
            .powf(2.0)
            * 0.5f32
            + 0.5f32;

        const zNear: f32 = 0.1f32;
        const zFar: f32 = 100.0f32;
        const max_distance: f32 = 20.0f32;
        let distance = _depth_cell.get_depth(_depth_layer);
        let z_n: f32 = 2.0f32 * distance - 1.0f32;
        let world_dist: f32 = 2.0f32 * zNear * zFar / (zFar + zNear - z_n * (zFar - zNear));
        let distance_shading = 1.0f32 - (world_dist.clamp(0.0, max_distance) / max_distance);

        let texture_color = texture_buffer
            .get_rgba_at_v(self.albedo_texture_idx, &uv, 0)
            .mult_albedo(distance_shading);
        let texture_color1 = texture_buffer
            .get_rgba_at_v(self.albedo_texture_idx, &uv1, 0)
            .mult_albedo(distance_shading);

        cell.glyph = self.glyph_idx;

        cell.front_color.copy_from(&texture_color);
        cell.back_color.copy_from(&texture_color1);
    }
}

#[cfg(test)]
mod tests {
    use nalgebra_glm::vec2;

    use super::*;
    use crate::drawbuffer::drawbuffer::{CanvasCell, Color};
    use crate::primitivbuffer::primitiv_triangle::PTriangle3D;
    use crate::primitivbuffer::primitivbuffer::{PointInfo, PrimitivReferences, PrimitiveElements};
    use crate::texturebuffer::texture_buffer::TextureBuffer;
    use crate::texturebuffer::RGBA;
    use crate::vertexbuffer::uv_buffer::UVBuffer;

    #[test]
    fn test_render_mat() {
        // Create test data

        let glyph_idx = 1;
        let mut canvas_cell = CanvasCell::default();
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();

        let mut pixinfo = PixInfo::new();

        let primitive_element = PrimitiveElements::Triangle3D(PTriangle3D::zero());
        let mut texture_buffer: TextureBuffer<256> = TextureBuffer::new(10);
        let mut uv_buffer: UVBuffer<f32> = UVBuffer::new(128);

        uv_buffer.add_uv(&vec2(0.0, 0.0), &vec2(1.0, 0.0), &vec2(1.0, 1.0));

        texture_buffer.add_texture_from_iter(
            2,
            2,
            vec![
                RGBA::new(10, 0, 0, 255),
                RGBA::new(20, 0, 0, 255),
                RGBA::new(30, 0, 0, 255),
                RGBA::new(40, 0, 0, 255),
            ],
            false,
            false,
        );

        // Create the Texture instance
        let texture_material = Textured::new(0, glyph_idx);

        // close to point a
        // Call the render_mat function
        pixinfo.set_uv(vec2(0.0, 0.0));
        texture_material.render_mat(
            &mut canvas_cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );
        // Assert the expected results
        assert_eq!(canvas_cell.glyph, glyph_idx);
        assert_eq!(canvas_cell.front_color, Color::new(10, 0, 0, 255));
        assert_eq!(canvas_cell.back_color, Color::new(10, 0, 0, 255));

        // close to point b

        let mut pixinfob = PixInfo::new();
        pixinfob.set_uv(vec2(1.0, 0.0));
        pixinfob.set_uv_1(vec2(1.0, 0.0));
        let mut canvas_cell_b = CanvasCell::default();
        texture_material.render_mat(
            &mut canvas_cell_b,
            &DepthBufferCell::<f32, 2>::new(),
            0,
            &pixinfob,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );

        assert_eq!(canvas_cell_b.glyph, glyph_idx);
        assert_eq!(canvas_cell_b.front_color, Color::new(20, 0, 0, 255));
        assert_eq!(canvas_cell_b.back_color, Color::new(20, 0, 0, 255));

        // close to point c
        let mut pixinfo_c = PixInfo::new();
        pixinfo_c.set_uv(vec2(1.0, 1.0));
        pixinfo_c.set_uv_1(vec2(1.0, 1.0));
        let mut canvas_cell_c = CanvasCell::default();
        texture_material.render_mat(
            &mut canvas_cell_c,
            &depth_cell,
            0,
            &pixinfo_c,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );

        assert_eq!(canvas_cell_c.glyph, glyph_idx);
        assert_eq!(canvas_cell_c.front_color, Color::new(40, 0, 0, 255));
        assert_eq!(canvas_cell_c.back_color, Color::new(40, 0, 0, 255));
    }
}
