use nalgebra_glm::{vec3, Vec2};

use crate::{
    drawbuffer::drawbuffer::{CanvasCell, Color, DepthBufferCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveElements,
    texturebuffer::{texture_buffer::TextureBuffer, RGBA},
    vertexbuffer::UVBuffer,
};

use super::{calc_2d_uv_coord, RenderMatTrait};

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Texture {
    pub albedo_texture_idx: usize,
    pub glyph_idx: u8,
}
impl Texture {
    pub fn new(albedo_texture_idx: usize, glyph_idx: u8) -> Self {
        Self {
            albedo_texture_idx,
            glyph_idx,
        }
    }
}
impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize, const UVCOUNT: usize>
    RenderMatTrait<TEXTURE_BUFFER_SIZE, DEPTHLAYER, UVCOUNT> for Texture
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        depth_layer: usize,
        pixinfo: &PixInfo<f32>,
        primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        uv_buffer: &UVBuffer<UVCOUNT, f32>,
    ) {
        cell.glyph = self.glyph_idx;
        depth_cell.row;
        depth_cell.col;
        let depth = depth_cell.get_depth(depth_layer);

        let point = vec3(depth_cell.col as f32, depth_cell.row as f32, depth);

        let uvs = uv_buffer.get_uv(primitive_element.get_uv_idx());
        let uv = calc_2d_uv_coord(pixinfo, uvs, 0);
        let texture_color = texture_buffer.get_rgba_at_v(self.albedo_texture_idx, &uv);
        //cell.front_color.copy_from(&front_rgba);
        cell.front_color.copy_from(&texture_color);
        //cell.back_color.copy_from(&texture_color);
    }
}

#[cfg(test)]
mod tests {
    use nalgebra_glm::{vec2, vec3};

    use super::*;
    use crate::drawbuffer::drawbuffer::CanvasCell;
    use crate::primitivbuffer::primitiv_triangle::PTriangle;
    use crate::primitivbuffer::primitivbuffer::{PointInfo, PrimitivReferences, PrimitiveElements};
    use crate::texturebuffer::texture_buffer::TextureBuffer;
    use crate::vertexbuffer::UVBuffer;

    #[test]
    fn test_render_mat() {
        // Create test data

        let glyph_idx = 1;
        let mut canvas_cell = CanvasCell::default();
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();

        let mut pixinfo = PixInfo::new();

        let primitive_element = PrimitiveElements::Triangle(PTriangle::new(
            PrimitivReferences {
                node_id: 0,
                material_id: 0,
                geometry_id: 0,
                primitive_id: 0,
            },
            PointInfo::new(0.0, 0.0, 0.0),
            PointInfo::new(0.0, 0.0, 0.0),
            PointInfo::new(0.0, 0.0, 0.0),
            0,
        ));
        let mut texture_buffer: TextureBuffer<256> = TextureBuffer::new(10);
        let mut uv_buffer: UVBuffer<128, f32> = UVBuffer::new();

        uv_buffer.add_uv(&vec2(0.0, 0.0), &vec2(1.0, 0.0), &vec2(1.0, 1.0));

        texture_buffer.add_texture_from_iter(
            2,
            2,
            vec![
                RGBA::new(10, 0, 0, 255),
                RGBA::new(20, 0, 0, 255),
                RGBA::new(30, 0, 0, 255),
                RGBA::new(40, 0, 0, 255),
            ]
            .into_iter(),
            true,
            true,
        );

        // Create the Texture instance
        let texture_material = Texture::new(0, glyph_idx);

        // close to point a
        // Call the render_mat function
        pixinfo.set_w(vec3(0.8, 0.1, 0.1));
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
        pixinfo.set_w(vec3(0.1, 0.8, 0.1));

        texture_material.render_mat(
            &mut canvas_cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );

        assert_eq!(canvas_cell.glyph, glyph_idx);
        assert_eq!(canvas_cell.front_color, Color::new(20, 0, 0, 255));
        assert_eq!(canvas_cell.back_color, Color::new(20, 0, 0, 255));

        // close to point c
        pixinfo.set_w(vec3(0.1, 0.1, 0.8));

        texture_material.render_mat(
            &mut canvas_cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );

        assert_eq!(canvas_cell.glyph, glyph_idx);
        assert_eq!(canvas_cell.front_color, Color::new(40, 0, 0, 255));
        assert_eq!(canvas_cell.back_color, Color::new(40, 0, 0, 255));
    }
}