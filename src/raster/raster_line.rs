use crate::{drawbuffer::drawbuffer::DrawBuffer, raster::vertex::Vertex};

use super::primitivbuffer::{PointInfo, PrimitivReferences};

/// Raster a line between two points
pub fn raster_line<const DEPTHCOUNT: usize>(
    drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
    prim_ref: &PrimitivReferences,
    pa: &Vertex,
    pb: &Vertex,
) {
    let row_count = (pb.pos.y as isize - pa.pos.y as isize).abs();
    let col_count = (pb.pos.x as isize - pa.pos.x as isize).abs();
    let steps = row_count.max(col_count);

    // Degenerate case: just one pixel
    if steps == 0 {
        let row = pa.pos.y as isize;
        let col = pa.pos.x as isize;
        if row >= 0 && col >= 0 {
            let depth = pa.pos.z;
            let normal = pa.normal;
            let uv = pa.uv;
            let uv_1 = uv; // or another UV set if you have it
            drawing_buffer.set_depth_content(
                row as usize,
                col as usize,
                depth,
                normal,
                uv,
                uv_1,
                prim_ref.node_id,
                prim_ref.geometry_id,
                prim_ref.material_id,
                prim_ref.primitive_id,
            );
        }
        return;
    }

    // DDA-style stepping with attribute interpolation

    let step_interpolent = (*pb - *pa) / (steps as f32);

    let mut current_value = pa.clone();

    for i in 0..=steps {
        let row = current_value.pos.y as isize;
        let col = current_value.pos.x as isize;
        if row >= 0 && col >= 0 {
            let depth = current_value.pos.z;
            let normal = current_value.normal;
            let uv = current_value.uv;
            let uv_1 = uv; // or another UV set if you have it
            drawing_buffer.set_depth_content(
                row as usize,
                col as usize,
                depth,
                normal,
                uv,
                uv_1,
                prim_ref.node_id,
                prim_ref.geometry_id,
                prim_ref.material_id,
                prim_ref.primitive_id,
            );
        }
        current_value = current_value + step_interpolent;
    }
}

#[cfg(test)]
mod tests {
    use approx::abs_diff_eq;

    use super::*;

    #[test]
    fn test_raster_line() {
        // Test case 1: pa.row > drawing_buffer.row_count
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 10.0, true, false);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };
        let pav = Vertex {
            pos: nalgebra_glm::vec4(0.0, 1.0, 1.0, 1.0),
            normal: nalgebra_glm::vec3(0.0, 0.0, 1.0),
            uv: nalgebra_glm::vec2(1.0, 0.0),
        };
        let pbv = Vertex {
            pos: nalgebra_glm::vec4(8.0, 9.0, 3.0, 1.0),
            normal: nalgebra_glm::vec3(0.0, 0.0, 1.0),
            uv: nalgebra_glm::vec2(0.0, 1.0),
        };

        raster_line(&mut drawing_buffer, &prim_ref, &pav, &pbv);

        // Assert that raster_line_along_columns is called
    }
    #[test]
    fn test_raster_line_horizontal() {
        // Test case 1: pa.row > drawing_buffer.row_count
        let mut drawing_buffer = DrawBuffer::<2, f32>::new(10, 10, 10.0, true, false);
        let prim_ref = PrimitivReferences {
            geometry_id: 1,
            material_id: 2,
            node_id: 3,
            primitive_id: 0,
        };
        let pav = Vertex {
            pos: nalgebra_glm::vec4(0.0, 0.0, 1.0, 1.0),
            normal: nalgebra_glm::vec3(0.0, 0.0, 1.0),
            uv: nalgebra_glm::vec2(1.0, 0.0),
        };
        let pbv = Vertex {
            pos: nalgebra_glm::vec4(1.0, 0.0, 3.0, 1.0),
            normal: nalgebra_glm::vec3(0.0, 0.0, 1.0),
            uv: nalgebra_glm::vec2(0.0, 1.0),
        };
        raster_line(&mut drawing_buffer, &prim_ref, &pav, &pbv);

        // assert the line is rastered
        // get the point at 0, 0
        let pixinfo = drawing_buffer.get_pix_buffer_content_at_row_col(0, 0, 0);
        assert_eq!(pixinfo.node_id, prim_ref.node_id);
        assert_eq!(pixinfo.geometry_id, prim_ref.geometry_id);
        assert_eq!(pixinfo.material_id, prim_ref.material_id);

        assert_eq!(pixinfo.uv.x, 1.0);
        assert_eq!(pixinfo.uv.y, 0.0);

        let cell = drawing_buffer.get_depth_buffer_cell(0, 0);
        assert_eq!(cell.depth[0], 1.0);
    }
}
