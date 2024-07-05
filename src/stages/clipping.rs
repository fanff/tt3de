use nalgebra_glm::{Vec2, Vec4};

fn interpolate(p1: &Vec4, p2: &Vec4, t: f32) -> Vec4 {
    p1 + t * (p2 - p1)
}

// structure to store the clipped triangles
// the content is a list of 9 triangles
// the count is the number of triangles in the list
#[derive(Debug, Clone, Copy)]
pub struct TriangleBuffer {
    pub content: [[Vec4; 3]; 9],
    pub uvs: [[Vec2; 3]; 9],
    pub count: usize,
}

impl TriangleBuffer {
    pub fn new() -> Self {
        Self {
            content: [[Vec4::zeros(); 3]; 9],
            uvs: [[Vec2::zeros(); 3]; 9],
            count: 0,
        }
    }

    fn push(&mut self, a: Vec4, b: Vec4, c: Vec4) {
        self.content[self.count] = [a, b, c];
        self.count += 1;
    }
    fn clear(&mut self) {
        self.count = 0;
    }

    fn len(&self) -> usize {
        self.count
    }
    pub fn iter(&self) -> std::iter::Take<std::slice::Iter<'_, [Vec4; 3]>> {
        // iterate over the triangles
        // up to count
        self.content.iter().take(self.count)
    }
}

// clip triangle to a single plane.
// this can add up to 2 triangles to the output buffer
pub fn clip_triangle_to_plane(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    plane: Vec4,
    output_buffer: &mut TriangleBuffer,
) {
    let pa_dist = plane.dot(pa);
    let pb_dist = plane.dot(pb);
    let pc_dist = plane.dot(pc);

    let inside_pa = pa_dist >= 0.0;
    let inside_pb = pb_dist >= 0.0;
    let inside_pc = pc_dist >= 0.0;

    if inside_pa && inside_pb && inside_pc {
        // All vertices are inside the plane
        output_buffer.push(*pa, *pb, *pc);
    } else if !inside_pa && !inside_pb && !inside_pc {
        // All vertices are outside the plane
        // Do nothing
    } else {
        // Some vertices are inside, some are outside
        let mut inside_points = Vec::new();
        let mut outside_points = Vec::new();

        if inside_pa {
            inside_points.push(pa);
        } else {
            outside_points.push(pa);
        }

        if inside_pb {
            inside_points.push(pb);
        } else {
            outside_points.push(pb);
        }

        if inside_pc {
            inside_points.push(pc);
        } else {
            outside_points.push(pc);
        }

        if inside_points.len() == 1 && outside_points.len() == 2 {
            // One vertex inside, two vertices outside
            let t1 = plane.dot(inside_points[0])
                / (plane.dot(inside_points[0]) - plane.dot(outside_points[0]));
            let t2 = plane.dot(inside_points[0])
                / (plane.dot(inside_points[0]) - plane.dot(outside_points[1]));

            let p1 = interpolate(inside_points[0], outside_points[0], t1);
            let p2 = interpolate(inside_points[0], outside_points[1], t2);

            output_buffer.push(*inside_points[0], p1, p2);
        } else if inside_points.len() == 2 && outside_points.len() == 1 {
            // Two vertices inside, one vertex outside
            let t1 = plane.dot(inside_points[0])
                / (plane.dot(inside_points[0]) - plane.dot(outside_points[0]));
            let t2 = plane.dot(inside_points[1])
                / (plane.dot(inside_points[1]) - plane.dot(outside_points[0]));

            let p1 = interpolate(inside_points[0], outside_points[0], t1);
            let p2 = interpolate(inside_points[1], outside_points[0], t2);

            output_buffer.push(*inside_points[0], *inside_points[1], p1);
            output_buffer.push(*inside_points[1], p1, p2);
        }
    }
}

// clip triangle into the clip space
// this operation can generate more triangles as the clipping can generate up to 9 triangles
// this function will call clip_triangle_to_plane 6 times
// to clip the triangle to the left, right, top, bottom, front and back planes
pub fn clip_triangle_to_clip_space(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    output_buffer: &mut TriangleBuffer,
) {
    let planes = [
        Vec4::new(1.0, 0.0, 0.0, 1.0),  // left
        Vec4::new(-1.0, 0.0, 0.0, 1.0), // right
        Vec4::new(0.0, 1.0, 0.0, 1.0),  // top
        Vec4::new(0.0, -1.0, 0.0, 1.0), // bottom
        Vec4::new(0.0, 0.0, 1.0, 1.0),  // front
        Vec4::new(0.0, 0.0, -1.0, 1.0), // back
    ];
    output_buffer.clear();
    // create two buffers to store the triangles
    let mut buffer1 = TriangleBuffer::new();
    let mut buffer2 = TriangleBuffer::new();
    buffer1.push(*pa, *pb, *pc);

    let mut input_buffer = &mut buffer1;
    let mut output_buffer_temp = &mut buffer2;

    // clip the triangle to each plane
    for &plane in planes.iter() {
        output_buffer_temp.clear();

        // clip triangles in the input buffer to the current plane
        // writing into the output buffer
        for i in 0..input_buffer.count {
            let tri = input_buffer.content[i];
            clip_triangle_to_plane(&tri[0], &tri[1], &tri[2], plane, output_buffer_temp);
        }
        // swap the input and output buffer
        std::mem::swap(&mut input_buffer, &mut output_buffer_temp);

        // repeat the process for the next plane
    }

    for i in 0..input_buffer.count {
        let tri = input_buffer.content[i];
        output_buffer.push(tri[0], tri[1], tri[2]);
    }
}
#[cfg(test)]
mod tests_clip_triangle_to_space {
    use super::*;

    #[test]
    fn test_clip_triangle_within_clip_space() {
        let pa = Vec4::new(0.0, 0.0, 0.0, 1.0);
        let pb = Vec4::new(1.0, 0.0, 0.0, 1.0);
        let pc = Vec4::new(0.0, 1.0, 0.0, 1.0);
        let mut output_buffer = TriangleBuffer::new();

        clip_triangle_to_clip_space(&pa, &pb, &pc, &mut output_buffer);

        // Expect no clipping if the triangle is fully within clip space
        assert_eq!(output_buffer.len(), 1);

        let clipped_triangle = output_buffer.content[0];
        assert_eq!(clipped_triangle[0], pa);
        assert_eq!(clipped_triangle[1], pb);
        assert_eq!(clipped_triangle[2], pc);
    }

    #[test]
    fn test_clip_triangle_partially_outside_clip_space_right() {
        // Triangle partially outside the clip space
        // pa is inside, pb is outside on the right,
        // pc is outside on the top

        let pa = Vec4::new(0.0, 0.0, 0.0, 1.0);
        let pb = Vec4::new(1.5, 0.0, 0.0, 1.0);
        let pc = Vec4::new(0.0, 1.5, 0.0, 1.0);
        let mut output_buffer = TriangleBuffer::new();

        clip_triangle_to_clip_space(&pa, &pb, &pc, &mut output_buffer);
        assert_eq!(output_buffer.len(), 4);

        // Expect the triangle to be clipped into Tree triangles
        let clipped_triangle = output_buffer.content[0];
        assert_eq!(clipped_triangle[0], pa);
        assert_eq!(clipped_triangle[1], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.0, 1.0, 0.0, 1.0));

        let clipped_triangle = output_buffer.content[1];
        assert_eq!(clipped_triangle[0], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[1], Vec4::new(0.0, 1.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.3333333, 1.0, 0.0, 1.0));

        let clipped_triangle = output_buffer.content[2];
        assert_eq!(clipped_triangle[0], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[1], Vec4::new(1.0, 0.5, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.3333333, 1.0, 0.0, 1.0));

        let clipped_triangle = output_buffer.content[3];
        assert_eq!(clipped_triangle[0], Vec4::new(1.0, 0.5, 0.0, 1.0));
        assert_eq!(clipped_triangle[1], Vec4::new(0.3333333, 1.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.5, 1.0, 0.0, 1.0));
    }

    #[test]
    fn test_clip_triangle_completely_outside_clip_space() {
        // pa is outside on the left, pb is outside on the right, pc is outside on the top

        let pa = Vec4::new(-2.0, -2.0, -2.0, 1.0);
        let pb = Vec4::new(-3.0, -3.0, -3.0, 1.0);
        let pc = Vec4::new(-4.0, -4.0, -4.0, 1.0);
        let mut output_buffer = TriangleBuffer::new();

        clip_triangle_to_clip_space(&pa, &pb, &pc, &mut output_buffer);

        // Expect no triangles if the original triangle is completely outside clip space
        assert_eq!(output_buffer.len(), 0);
    }

    #[test]
    fn test_clip_triangle_edge_cases() {
        // Test edge cases such as vertices lying exactly on the clip space boundaries
        let pa = Vec4::new(1.0, 1.0, 1.0, 1.0);
        let pb = Vec4::new(-1.0, 1.0, 1.0, 1.0);
        let pc = Vec4::new(1.0, -1.0, 1.0, 1.0);
        let mut output_buffer = TriangleBuffer::new();

        clip_triangle_to_clip_space(&pa, &pb, &pc, &mut output_buffer);

        assert!(output_buffer.len() == 1);
    }
    #[test]
    fn test_clip_triangle_in_1() {
        // pa is inside,
        // pb is outside on the right,
        // pc is outside on the right
        let pa = Vec4::new(0.0, 0.0, 0.0, 1.0);
        let pb = Vec4::new(1.5, 0.0, 0.0, 1.0);
        let pc = Vec4::new(1.5, 1.0, 0.0, 1.0);

        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_clip_space(&pa, &pb, &pc, &mut output_buffer);

        // Expect the triangle to be clipped into 1 triangle
        assert_eq!(output_buffer.len(), 1);

        let clipped_triangle = output_buffer.content[0];
        assert_eq!(clipped_triangle[0], pa);
        assert_eq!(clipped_triangle[1], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert!((clipped_triangle[2] - Vec4::new(1.0, 0.6666, 0.0, 1.0)).norm() < 0.0001);
    }
    #[test]
    fn test_clip_triangle_in_2() {
        // pa is inside,
        // pb is outside on the right,
        // pc is outside on the right and on the top
        let pa = Vec4::new(0.0, 0.0, 0.0, 1.0);
        let pb = Vec4::new(1.5, 0.0, 0.0, 1.0);
        let pc = Vec4::new(1.5, 2.0, 0.0, 1.0);

        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_clip_space(&pa, &pb, &pc, &mut output_buffer);

        // Expect the triangle to be clipped into 1 triangle
        assert_eq!(output_buffer.len(), 2);

        let clipped_triangle = output_buffer.content[0];
        assert_eq!(clipped_triangle[0], pa);
        assert_eq!(clipped_triangle[1], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.75, 1.0, 0.0, 1.0));

        let clipped_triangle = output_buffer.content[1];
        assert_eq!(clipped_triangle[0], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[1], Vec4::new(0.75, 1.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(1.0, 1.0, 0.0, 1.0));
    }

    #[test]
    fn test_clip_triangle_in_4() {
        // pa is inside, pb is outside on the right, pc is outside on the top
        // the top right corner of the clip space is outside the triangle
        // so you need to clip the triangle into 4 triangles
        let pa = Vec4::new(0.0, 0.0, 0.5, 1.0);
        let pb = Vec4::new(1.2, 0.0, 0.5, 1.0);
        let pc = Vec4::new(0.0, 1.2, 0.5, 1.0);
        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_clip_space(&pa, &pb, &pc, &mut output_buffer);

        // Expect the triangle to be clipped into 4
        assert_eq!(output_buffer.len(), 4);
    }
}
#[cfg(test)]
mod tests_clip_triangle_to_plane {
    use super::*;
    use nalgebra_glm::{vec4, Vec4};

    #[test]
    fn test_all_vertices_inside() {
        let pa = vec4(0.5, 0.5, 0.5, 1.0);
        let pb = vec4(0.5, -0.5, 0.5, 1.0);
        let pc = vec4(-0.5, 0.5, 0.5, 1.0);
        let plane = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0

        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, plane, &mut output_buffer);

        assert_eq!(output_buffer.count, 1);
        assert_eq!(output_buffer.content[0], [pa, pb, pc]);
    }

    #[test]
    fn test_all_vertices_outside_left() {
        let pa = vec4(-2.0, 0.5, 0.5, 1.0);
        let pb = vec4(-2.0, -0.5, 0.5, 1.0);
        let pc = vec4(-2.5, 0.5, 0.5, 1.0);
        let plane_left = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0
        let plane_right = vec4(-1.0, 0.0, 0.0, 1.0); // plane: -x + 1 >= 0

        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, plane_left, &mut output_buffer);

        assert_eq!(output_buffer.count, 0);

        output_buffer.clear();
        clip_triangle_to_plane(&pa, &pb, &pc, plane_right, &mut output_buffer);

        assert_eq!(output_buffer.count, 1);
    }
    #[test]
    fn test_all_vertices_outside_right() {
        let pa = vec4(2.0, 0.5, 0.5, 1.0);
        let pb = vec4(2.0, -0.5, 0.5, 1.0);
        let pc = vec4(2.5, 0.5, 0.5, 1.0);
        let plane_left = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0
        let plane_right = vec4(-1.0, 0.0, 0.0, 1.0); // plane: -x + 1 >= 0

        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, plane_left, &mut output_buffer);
        // one result on the left
        assert_eq!(output_buffer.count, 1);

        output_buffer.clear();

        // no result on the right
        clip_triangle_to_plane(&pa, &pb, &pc, plane_right, &mut output_buffer);

        assert_eq!(output_buffer.count, 0);
    }

    #[test]
    fn test_one_vertex_inside_plane_left() {
        // one vertex inside
        let pa = vec4(-0.5, 0.5, 0.5, 1.0);

        // two vertex outside left plane
        let pb = vec4(-2.0, -0.5, 0.5, 1.0);
        let pc = vec4(-2.5, 0.5, 0.5, 1.0);

        // left plane
        let plane = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0

        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, plane, &mut output_buffer);
        // one triangle is generated
        assert_eq!(output_buffer.count, 1);

        let tri = output_buffer.content[0];

        // first vertex is the one inside
        assert_eq!(tri[0], pa);
        // other two vertices are on the left plane
        assert!(tri[1].x >= -1.0);
        assert!(tri[2].x >= -1.0);
    }

    #[test]
    fn test_two_vertices_inside_plane_left() {
        // two vertices inside
        let pa = vec4(-0.5, 0.5, 0.5, 1.0);
        let pb = vec4(-0.5, -0.5, 0.5, 1.0);
        // one vertex outside left plane
        let pc = vec4(-2.5, 0.5, 0.5, 1.0);

        // left plane
        let plane = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0

        let mut output_buffer = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, plane, &mut output_buffer);

        // two triangles are generated
        assert_eq!(output_buffer.count, 2);

        let tri1 = output_buffer.content[0];
        let tri2 = output_buffer.content[1];
        // first triangle has two vertices inside
        assert_eq!(tri1[0], pa);
        assert_eq!(tri1[1], pb);
        assert!(tri1[2].x >= -1.0);

        // second triangle has two vertices inside
        assert_eq!(tri2[0], pb);
        assert_eq!(tri2[1], tri1[2]);
        assert!(tri2[2].x >= -1.0);
    }
}
