use nalgebra_glm::{vec2, Vec3};

use crate::drawbuffer::drawbuffer::DrawBuffer;

use super::{primitivbuffer::PrimitivReferences, rect::PRect, Vertex};

pub fn raster_prect<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    rect: &PRect,
) {
    let prim_ref = rect.primitive_reference;
    let top_left = rect.top_left;
    let bottom_right = rect.bottom_right;

    // calculate delta steping for row and columns
    let delta_row = bottom_right.pos.y - top_left.pos.y;
    let delta_col = bottom_right.pos.x - top_left.pos.x;

    let di_uv_row = vec2(0.0, (bottom_right.uv.y - top_left.uv.y) / delta_row);
    let di_uv_col = vec2((bottom_right.uv.x - top_left.uv.x) / delta_col, 0.0);

    #[cfg(test)]
    {
        println!("row steping : {:?}", di_uv_row);
        println!("column steping : {:?}", di_uv_col);
    }

    // create row interpolator
    let mut it_row = top_left.uv;

    let row_start = (top_left.pos.y - 0.5f32).ceil().max(0.0) as usize;
    let row_end = (bottom_right.pos.y - 0.5f32)
        .ceil()
        .min(drawing_buffer.row_count as f32) as usize;
    let col_start = (top_left.pos.x - 0.5f32).ceil().max(0.0) as usize;
    let col_end = (bottom_right.pos.x - 0.5f32)
        .ceil()
        .min((drawing_buffer.col_count) as f32) as usize;
    #[cfg(test)]
    {
        println!(
            "draw rectangle  : {:?},{:?}  {:?},{:?}",
            row_start, row_end, col_start, col_end
        );
    }

    // calculate delta scaline interpolant / d col

    // do interpolant prestep
    it_row += di_uv_row * ((row_start as f32 + 0.5f32) - top_left.pos.y);
    // create scanline interpolant
    #[cfg(test)]
    {
        println!(" prestep row : {:?}", it_row);
    }
    for row in row_start..row_end {
        #[cfg(test)]
        {
            println!("draw_rectangle cols  : {:?},{:?}", col_start, col_end);
        }
        let mut i_line = it_row;
        i_line += di_uv_col * (col_start as f32 + 0.5f32 - top_left.pos.x);

        #[cfg(test)]
        {
            println!(" prestep col : {:?}", i_line);
        }
        for col in col_start..col_end {
            //recover interpolated z for interpolated 1/z
            //let w = 1.0f32 / i_line.pos.w;
            //let attr = i_line * w;
            let uv = i_line;
            #[cfg(test)]
            {
                println!("draw rectangle pixel : {:?},{:?}", row, col);
                //println!("depth : {:?}, uv : {:?}", i_line.pos.z, attr.uv);
                println!("uv : {:?}", uv);
            }

            drawing_buffer.set_depth_content(
                row,
                col,
                0.01,
                Vec3::new(0.0, 0.0, 1.0),
                uv,
                vec2(0.0, 0.0),
                prim_ref.node_id,
                prim_ref.geometry_id,
                prim_ref.material_id,
                prim_ref.primitive_id,
            );
            // step scanline interpolant
            i_line += di_uv_col;
        }
        it_row += di_uv_row;
    }
}

#[cfg(test)]
mod test_raster_rect {
    use nalgebra_glm::{vec2, vec3, vec4};

    use crate::{
        drawbuffer::drawbuffer::DrawBuffer,
        raster::{primitivbuffer::PrimitivReferences, Vertex},
    };

    use super::raster_prect;

    #[test]
    fn test_raster_rect() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };

        let top_left = Vertex {
            pos: vec4(0.0, 0.0, 1.0, 1.0),
            normal: vec3(0.0, 0.0, 0.0),
            uv: vec2(0.0, 0.0),
        };

        let bottom_right = Vertex {
            pos: vec4(3.0, 4.0, 1.0, 1.0),
            normal: vec3(0.0, 0.0, 0.0),
            uv: vec2(1.0, 1.0),
        };
        let rect = super::PRect {
            top_left,
            bottom_right,
            primitive_reference: prim_ref,
        };

        raster_prect(&mut drawing_buffer, &rect);

        for row in 0..4 {
            for col in 0..3 {
                let content_at_location_layer0 =
                    drawing_buffer.get_pix_buffer_content_at_row_col(row, col, 0);
                //let cell = drawing_buffer.get_depth_buffer_cell(row, col);
                assert_eq!(content_at_location_layer0.node_id, 3);
                assert_eq!(content_at_location_layer0.geometry_id, 1);
                assert_eq!(content_at_location_layer0.material_id, 2);
                assert_eq!(content_at_location_layer0.primitive_id, 4);
                //assert_eq!(content_at_location_layer0.uv.x, 0.01);
            }
        }
    }

    #[test]
    fn test_raster_outbound() {
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 100.0);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 4,
        };

        let top_left = Vertex {
            pos: vec4(-5.0, -6.0, 1.0, 1.0),
            normal: vec3(0.0, 0.0, 0.0),
            uv: vec2(0.0, 0.0),
        };

        let bottom_right = Vertex {
            pos: vec4(13.0, 14.0, 1.0, 1.0),
            normal: vec3(0.0, 0.0, 0.0),
            uv: vec2(1.0, 1.0),
        };
        let rect = super::PRect {
            top_left,
            bottom_right,
            primitive_reference: prim_ref,
        };

        raster_prect(&mut drawing_buffer, &rect);

        // test every pixel of the drawing_buffer
        for row in 0..10 {
            for col in 0..10 {
                let content_at_location_layer0 =
                    drawing_buffer.get_pix_buffer_content_at_row_col(row, col, 0);
                //let cell = drawing_buffer.get_depth_buffer_cell(row, col);
                assert_eq!(content_at_location_layer0.node_id, 3);
                assert_eq!(content_at_location_layer0.geometry_id, 1);
                assert_eq!(content_at_location_layer0.material_id, 2);
                assert_eq!(content_at_location_layer0.primitive_id, 4);
                //assert_eq!(content_at_location_layer0.uv.x, 0.01);
            }
        }
    }
}
