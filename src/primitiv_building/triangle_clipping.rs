use nalgebra_glm::{dot, lerp, Vec2, Vec3, Vec4};

fn interpolate(p1: &Vec4, p2: &Vec4, t: f32) -> Vec4 {
    //p1 + t * (p2 - p1)
    lerp(p1, p2, t)
}

fn interpolate_with_uv(p1: &Vec4, p2: &Vec4, uv1: &Vec2, uv2: &Vec2, t: f32) -> (Vec4, Vec2) {
    //p1 + t * (p2 - p1)
    (lerp(p1, p2, t), lerp(uv1, uv2, t))
}

#[derive(Debug, Clone, Copy)]
pub struct TriangleBuffer<const INNER_SIZE: usize> {
    pub content: [[Vec4; 3]; INNER_SIZE],
    pub uvs: [[Vec2; 3]; INNER_SIZE],
    pub count: usize,
}

impl<const INNER_SIZE: usize> TriangleBuffer<INNER_SIZE> {
    pub fn new() -> Self {
        Self {
            content: [[Vec4::zeros(); 3]; INNER_SIZE],
            uvs: [[Vec2::zeros(); 3]; INNER_SIZE],
            count: 0,
        }
    }

    pub fn push_vec4(&mut self, a: Vec4, b: Vec4, c: Vec4, (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2)) {
        self.content[self.count] = [a, b, c];
        self.uvs[self.count] = [uva.clone(), uvb.clone(), uvc.clone()];
        self.count += 1;
    }

    pub fn clear(&mut self) {
        self.count = 0;
    }

    pub fn len(&self) -> usize {
        self.count
    }
    pub fn iter(&self) -> impl Iterator<Item = (&[Vec4; 3], &[Vec2; 3])> {
        // iterate over the triangles
        // up to count
        self.content.iter().zip(self.uvs.iter()).take(self.count)
    }
}

pub fn half_clip_triangle_to_plane<const INNER_SIZE: usize>(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    plane: Vec4,
    uv_triplet: (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut TriangleBuffer<INNER_SIZE>,
) {
    let pa_dist = dot(&plane, pa);
    let pb_dist = dot(&plane, pb);
    let pc_dist = dot(&plane, pc);

    let inside_pa = pa_dist >= 0.0;
    let inside_pb = pb_dist >= 0.0;
    let inside_pc = pc_dist >= 0.0;

    if inside_pa || inside_pb || inside_pc {
        output_buffer.push_vec4(*pa, *pb, *pc, uv_triplet);
    }
}

/// Clip triangle to a single plane.
/// this can add up to 2 triangles to the output buffer
pub fn clip_triangle_to_plane<const INNER_SIZE: usize>(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    plane: &Vec4,
    uv_triplet: (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut TriangleBuffer<INNER_SIZE>,
) {
    let pa_dist = dot(&plane, pa);
    let pb_dist = dot(&plane, pb);
    let pc_dist = dot(&plane, pc);

    let inside_pa = pa_dist >= 0.0;
    let inside_pb = pb_dist >= 0.0;
    let inside_pc = pc_dist >= 0.0;

    if inside_pa && inside_pb && inside_pc {
        // All vertices are inside the plane
        output_buffer.push_vec4(*pa, *pb, *pc, uv_triplet);
    } else if !inside_pa && !inside_pb && !inside_pc {
        // All vertices are outside the plane
        // Do nothing
    } else {
        // Some vertices are inside, some are outside
        let mut inside_points = Vec::new();
        let mut inside_uv = Vec::new();
        let mut outside_points = Vec::new();
        let mut outside_uv = Vec::new();

        if inside_pa {
            inside_points.push(pa);
            inside_uv.push(uv_triplet.0);
        } else {
            outside_points.push(pa);
            outside_uv.push(uv_triplet.0);
        }

        if inside_pb {
            inside_points.push(pb);
            inside_uv.push(uv_triplet.1);
        } else {
            outside_points.push(pb);
            outside_uv.push(uv_triplet.1);
        }

        if inside_pc {
            inside_points.push(pc);
            inside_uv.push(uv_triplet.2);
        } else {
            outside_points.push(pc);
            outside_uv.push(uv_triplet.2);
        }

        if inside_points.len() == 1 && outside_points.len() == 2 {
            // One vertex inside, two vertices outside
            let t1 = plane.dot(inside_points[0])
                / (plane.dot(inside_points[0]) - plane.dot(outside_points[0]));
            let t2 = plane.dot(inside_points[0])
                / (plane.dot(inside_points[0]) - plane.dot(outside_points[1]));

            let (p1, uv1) = interpolate_with_uv(
                inside_points[0],
                outside_points[0],
                inside_uv[0],
                outside_uv[0],
                t1,
            );
            let (p2, uv2) = interpolate_with_uv(
                inside_points[0],
                outside_points[1],
                inside_uv[0],
                outside_uv[1],
                t2,
            );

            output_buffer.push_vec4(*inside_points[0], p1, p2, (inside_uv[0], &uv1, &uv2));
        } else if inside_points.len() == 2 && outside_points.len() == 1 {
            // Two vertices inside, one vertex outside
            let t1 = plane.dot(inside_points[0])
                / (plane.dot(inside_points[0]) - plane.dot(outside_points[0]));
            let t2 = plane.dot(inside_points[1])
                / (plane.dot(inside_points[1]) - plane.dot(outside_points[0]));

            let (p1, uv1) = interpolate_with_uv(
                inside_points[0],
                outside_points[0],
                inside_uv[0],
                outside_uv[0],
                t1,
            );
            let (p2, uv2) = interpolate_with_uv(
                inside_points[1],
                outside_points[0],
                inside_uv[1],
                outside_uv[0],
                t2,
            );

            output_buffer.push_vec4(
                *inside_points[0],
                *inside_points[1],
                p1,
                (inside_uv[0], inside_uv[1], &uv1),
            );
            output_buffer.push_vec4(*inside_points[1], p1, p2, (inside_uv[1], &uv1, &uv2));
        }
    }
}

/// Clips a triangle to the view frustum in clip space.
///
/// This function can generate additional triangles as clipping may produce more triangles
/// In clip space, the view frustum is defined by −w ≤ x ≤ w, −w ≤ y ≤ w, and 0 ≤ z ≤ w.
///
/// The algorithm clips the triangle against each of the six planes of the view frustum,
/// assuming the input coordinates are in clip space homogeneous coordinates (before perspective division).
/// It uses the Sutherland-Hodgman clipping algorithm for this purpose.
///
/// # Parameters
///
/// - `pa`: The first vertex of the triangle in clip space.
/// - `pb`: The second vertex of the triangle in clip space.
/// - `pc`: The third vertex of the triangle in clip space.
///
/// - `uva`: The UV coordinates of the first vertex.
/// - `uvb`: The UV coordinates of the second vertex.
/// - `uvc`: The UV coordinates of the third vertex.
///
/// - `output_buffer`: The buffer to store the resulting clipped triangles.
///
/// # Example
///
/// ```
/// let pa = Vec4::new(1.0, 1.0, 1.0, 1.0);
/// let pb = Vec4::new(-1.0, -1.0, 1.0, 1.0);
/// let pc = Vec4::new(0.0, 1.0, 1.0, 1.0);
/// let uva = Vec2::new(0.0, 0.0);
/// let uvb = Vec2::new(1.0, 0.0);
/// let uvc = Vec2::new(0.5, 1.0);
/// let mut output_buffer = TriangleBuffer::new();
/// clip_triangle_to_clip_space(&pa, &pb, &pc, (&uva, &uvb, &uvc), &mut output_buffer);
/// ```
pub fn clip_triangle_to_clip_space(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut TriangleBuffer<12>,
) {
    // defining the plane of the clipping
    let planes = [
        (Vec4::new(0.0, 0.0, -1.0, 1.0), 1), // far
        (Vec4::new(-1.0, 0.0, 0.0, 1.0), 1), //
        (Vec4::new(1.0, 0.0, 0.0, 1.0), 1),  //
        (Vec4::new(0.0, -1.0, 0.0, 1.0), 1), //
        (Vec4::new(0.0, 1.0, 0.0, 1.0), 1),  //
        (Vec4::new(0.0, 0.0, 1.0, 0.0), 0), // near// will use the full clipping method, generating more triangle potentially
    ];

    output_buffer.clear();
    // create two buffers to store the triangles
    let mut buffer1: TriangleBuffer<12> = TriangleBuffer::new();
    let mut buffer2: TriangleBuffer<12> = TriangleBuffer::new();
    buffer1.push_vec4(*pa, *pb, *pc, (uva, uvb, uvc));

    let mut input_buffer = &mut buffer1;
    let mut output_buffer_temp = &mut buffer2;

    // clip the triangle to each plane
    for (plane, method) in planes.iter() {
        output_buffer_temp.clear();

        // clip triangles in the input buffer to the current plane
        // writing into the output buffer
        for (vertex_triplet, uv_triplet) in input_buffer.iter() {
            let tri = vertex_triplet;
            match method {
                1 => {
                    half_clip_triangle_to_plane(
                        &tri[0],
                        &tri[1],
                        &tri[2],
                        *plane,
                        (&uv_triplet[0], &uv_triplet[1], &uv_triplet[2]),
                        output_buffer_temp,
                    );
                }
                _ => {
                    clip_triangle_to_plane(
                        &tri[0],
                        &tri[1],
                        &tri[2],
                        &plane,
                        (&uv_triplet[0], &uv_triplet[1], &uv_triplet[2]),
                        output_buffer_temp,
                    );
                }
            }
        }
        // swap the input and output buffer
        std::mem::swap(&mut input_buffer, &mut output_buffer_temp);

        // repeat the process for the next plane
    }

    // copy the clipped triangles to the output buffer
    for (triangle, uvs) in input_buffer.iter() {
        let cpa: Vec4 = triangle[0];
        let cpb: Vec4 = triangle[1];
        let cpc: Vec4 = triangle[2];

        output_buffer.push_vec4(cpa, cpb, cpc, (&uvs[0], &uvs[1], &uvs[2]));
    }
}

#[cfg(test)]
mod tests_clip_triangle_to_space {

    /// Defining a macro to simplify comparison of vec2
    /// display both content of the vectors if they are not equal
    /// and panic if they are not equal
    macro_rules! assert_eq_vec2 {
        ($a:expr, $b:expr, $eps:expr) => {
            let eps = $eps;
            if ($a - $b).norm() > eps {
                panic!("assertion failed: {:?} != {:?}", $a, $b);
            };
        };
    }

    /// Defining a macro to simplify comparison of vec3
    macro_rules! assert_eq_vec3 {
        ($a:expr, $b:expr, $eps:expr) => {
            let eps = $eps;
            if ($a - $b).norm() > eps {
                panic!("assertion failed: {:?} != {:?}", $a, $b);
            };
        };
    }
    const UVACCURACY_TEST: f32 = 0.001;
    use super::*;

    #[test]
    fn test_clip_triangle_within_clip_space() {
        let pa = Vec4::new(0.0, 0.0, 0.0, 1.0);
        let pb = Vec4::new(1.0, 0.0, 0.0, 1.0);
        let pc = Vec4::new(0.0, 1.0, 0.0, 1.0);
        let mut output_buffer = TriangleBuffer::new();
        let uvs = (
            &Vec2::new(0.0, 0.0),
            &Vec2::new(1.0, 0.0),
            &Vec2::new(0.0, 1.0),
        );
        clip_triangle_to_clip_space(&pa, &pb, &pc, uvs, &mut output_buffer);

        // Expect no clipping if the triangle is fully within clip space
        assert_eq!(output_buffer.len(), 1);

        let clipped_triangle = output_buffer.content[0];
        assert_eq!(clipped_triangle[0], pa);
        assert_eq!(clipped_triangle[1], pb);
        assert_eq!(clipped_triangle[2], pc);

        // testing the uv calculation has changed nothing
        let clipped_uvs = output_buffer.uvs[0];
        assert_eq_vec2!(clipped_uvs[0], *uvs.0, 0.001);
        assert_eq_vec2!(clipped_uvs[1], *uvs.1, 0.001);
        assert_eq_vec2!(clipped_uvs[2], *uvs.2, 0.001);
    }

    #[test]
    fn test_clip_triangle_in_4() {
        // Triangle partially outside the clip space
        // pa is inside,
        // pb is outside on the right,
        // pc is outside on the top

        let pa = Vec4::new(0.0, 0.0, 0.0, 1.0);
        let pb = Vec4::new(1.5, 0.0, 0.0, 1.0);
        let pc = Vec4::new(0.0, 1.5, 0.0, 1.0);
        let mut output_buffer = TriangleBuffer::new();
        let uvs = (
            &Vec2::new(0.0, 0.0),
            &Vec2::new(1.0, 0.0),
            &Vec2::new(0.0, 1.0),
        );
        clip_triangle_to_clip_space(&pa, &pb, &pc, uvs, &mut output_buffer);
        assert_eq!(output_buffer.len(), 4);

        // Expect the triangle to be clipped into 4 triangles
        let clipped_triangle = output_buffer.content[0];
        assert_eq!(clipped_triangle[0], pa);
        assert_eq!(clipped_triangle[1], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.0, 1.0, 0.0, 1.0));
        // testing the uv calculation of  sub triangle
        let clipped_uvs = output_buffer.uvs[0];
        assert_eq_vec2!(clipped_uvs[0], *uvs.0, 0.001);
        assert_eq_vec2!(clipped_uvs[1], Vec2::new(0.66666667, 0.0), UVACCURACY_TEST);
        assert_eq_vec2!(clipped_uvs[2], Vec2::new(0.0, 0.66666667), UVACCURACY_TEST);

        // triangle 1
        let clipped_triangle = output_buffer.content[1];
        assert_eq!(clipped_triangle[0], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[1], Vec4::new(0.0, 1.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.3333333, 1.0, 0.0, 1.0));
        // testing the uv calculation of  sub triangle
        let clipped_uvs = output_buffer.uvs[1];
        assert_eq_vec2!(clipped_uvs[0], Vec2::new(0.666667, 0.0), UVACCURACY_TEST);
        assert_eq_vec2!(clipped_uvs[1], Vec2::new(0.0, 0.666667), UVACCURACY_TEST);
        assert_eq_vec2!(clipped_uvs[2], Vec2::new(0.2222, 0.666667), UVACCURACY_TEST);

        //triangle 2
        let clipped_triangle = output_buffer.content[2];
        assert_eq!(clipped_triangle[0], Vec4::new(1.0, 0.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[1], Vec4::new(1.0, 0.5, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.3333333, 1.0, 0.0, 1.0));
        // testing the uv calculation of  sub triangle
        let clipped_uvs = output_buffer.uvs[2];
        assert_eq_vec2!(clipped_uvs[0], Vec2::new(0.666667, 0.0), UVACCURACY_TEST);
        assert_eq_vec2!(clipped_uvs[1], Vec2::new(0.66667, 0.33333), UVACCURACY_TEST);
        assert_eq_vec2!(clipped_uvs[2], Vec2::new(0.2222, 0.666667), UVACCURACY_TEST);

        let clipped_triangle = output_buffer.content[3];
        assert_eq!(clipped_triangle[0], Vec4::new(1.0, 0.5, 0.0, 1.0));
        assert_eq!(clipped_triangle[1], Vec4::new(0.3333333, 1.0, 0.0, 1.0));
        assert_eq!(clipped_triangle[2], Vec4::new(0.5, 1.0, 0.0, 1.0));
        // testing the uv calculation of  sub triangle
        let clipped_uvs = output_buffer.uvs[3];
        assert_eq_vec2!(clipped_uvs[0], Vec2::new(0.66667, 0.33333), UVACCURACY_TEST);
        assert_eq_vec2!(clipped_uvs[1], Vec2::new(0.2222, 0.666667), UVACCURACY_TEST);
        assert_eq_vec2!(
            clipped_uvs[2],
            Vec2::new(0.33333, 0.666667),
            UVACCURACY_TEST
        );
    }

    #[test]
    fn test_clip_triangle_completely_outside_clip_space() {
        // pa is outside on the left, pb is outside on the right, pc is outside on the top

        let pa = Vec4::new(-2.0, -2.0, -2.0, 1.0);
        let pb = Vec4::new(-3.0, -3.0, -3.0, 1.0);
        let pc = Vec4::new(-4.0, -4.0, -4.0, 1.0);
        let mut output_buffer = TriangleBuffer::new();

        let uvs = (
            &Vec2::new(0.0, 0.0),
            &Vec2::new(1.0, 0.0),
            &Vec2::new(0.0, 1.0),
        );
        clip_triangle_to_clip_space(&pa, &pb, &pc, uvs, &mut output_buffer);

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

        let uvs = (
            &Vec2::new(0.0, 0.0),
            &Vec2::new(1.0, 0.0),
            &Vec2::new(0.0, 1.0),
        );
        clip_triangle_to_clip_space(&pa, &pb, &pc, uvs, &mut output_buffer);

        assert!(output_buffer.len() == 1);
    }
    #[test]
    fn test_clip_triangle_in_1() {
        // pa is inside,
        // pb is outside on the far,
        // pc is outside on the far
        let pa = Vec4::new(0.0, 0.0, 0.0, 1.0);
        let pb = Vec4::new(0.0, 0.0, 2.0, 1.0);
        let pc = Vec4::new(0.1, 0.1, 2.0, 1.0);

        let mut output_buffer = TriangleBuffer::new();
        let uvs = (
            &Vec2::new(0.0, 0.0),
            &Vec2::new(1.0, 0.0),
            &Vec2::new(0.0, 1.0),
        );
        clip_triangle_to_clip_space(&pa, &pb, &pc, uvs, &mut output_buffer);

        // Expect the triangle to be clipped into 1 triangle
        assert_eq!(output_buffer.len(), 1);

        let clipped_triangle = output_buffer.content[0];
        assert_eq!(clipped_triangle[0], pa);
        assert_eq!(clipped_triangle[1], Vec4::new(0.0, 0.0, 1.0, 1.0));
        assert_eq_vec3!(clipped_triangle[2], Vec4::new(0.0, 0.0, 1.0, 1.0), 0.1);

        // test the uv coordinates
        let clipped_uvs = output_buffer.uvs[0];
        assert_eq_vec2!(clipped_uvs[0], *uvs.0, 0.001);
        assert_eq_vec2!(clipped_uvs[1], Vec2::new(0.5, 0.0), 0.1);
        assert_eq_vec2!(clipped_uvs[2], Vec2::new(0.0, 0.5), 0.1);
    }
    #[test]
    fn test_clip_triangle_in_2() {
        // pa is inside,
        // pb is inside,
        // pc is outside on the far
        let pa = Vec4::new(0.1, 0.0, 0.0, 1.0);
        let pb = Vec4::new(-0.1, 0.0, 0.0, 1.0);
        let pc = Vec4::new(0.0, 0.0, 2.0, 1.0);

        let mut output_buffer = TriangleBuffer::new();
        let uvs = (
            &Vec2::new(0.0, 0.0),
            &Vec2::new(1.0, 0.0),
            &Vec2::new(0.0, 1.0),
        );
        clip_triangle_to_clip_space(&pa, &pb, &pc, uvs, &mut output_buffer);

        // Expect the triangle to be clipped into 1 triangle
        assert_eq!(output_buffer.len(), 2);

        let clipped_triangle = output_buffer.content[0];
        assert_eq!(clipped_triangle[0], pa);
        assert_eq!(clipped_triangle[1], pb);
        assert_eq_vec3!(clipped_triangle[2], Vec4::new(0.0, 0.0, 1.0, 1.0), 0.1);

        let clipped_triangle = output_buffer.content[1];
        assert_eq!(clipped_triangle[0], pb);
        assert_eq_vec3!(clipped_triangle[1], Vec4::new(0.0, 0.0, 1.0, 1.0), 0.1);
        assert_eq_vec3!(clipped_triangle[2], Vec4::new(0.0, 0.0, 1.0, 1.0), 0.1);
    }
}
#[cfg(test)]
mod tests_clip_triangle_to_plane {
    use super::*;
    use nalgebra_glm::{vec2, vec4, Vec4};

    #[test]
    fn test_all_vertices_inside() {
        let pa = vec4(0.5, 0.5, 0.5, 1.0);
        let pb = vec4(0.5, -0.5, 0.5, 1.0);
        let pc = vec4(-0.5, 0.5, 0.5, 1.0);
        let plane = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0

        let uv_a = vec2(0.0, 0.0);
        let uv_b = vec2(1.0, 0.0);
        let uv_c = vec2(0.0, 1.0);

        let uv_triplet = (&uv_a, &uv_b, &uv_c);

        let mut output_buffer: TriangleBuffer<12> = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, &plane, uv_triplet, &mut output_buffer);

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

        let uv_a = vec2(0.0, 0.0);
        let uv_b = vec2(1.0, 0.0);
        let uv_c = vec2(0.0, 1.0);

        let uv_triplet = (&uv_a, &uv_b, &uv_c);

        let mut output_buffer: TriangleBuffer<12> = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, &plane_left, uv_triplet, &mut output_buffer);

        assert_eq!(output_buffer.count, 0);

        output_buffer.clear();
        clip_triangle_to_plane(&pa, &pb, &pc, &plane_right, uv_triplet, &mut output_buffer);

        assert_eq!(output_buffer.count, 1);
    }
    #[test]
    fn test_all_vertices_outside_right() {
        let pa = vec4(2.0, 0.5, 0.5, 1.0);
        let pb = vec4(2.0, -0.5, 0.5, 1.0);
        let pc = vec4(2.5, 0.5, 0.5, 1.0);
        let plane_left = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0
        let plane_right = vec4(-1.0, 0.0, 0.0, 1.0); // plane: -x + 1 >= 0

        let uv_a = vec2(0.0, 0.0);
        let uv_b = vec2(1.0, 0.0);
        let uv_c = vec2(0.0, 1.0);

        let uv_triplet = (&uv_a, &uv_b, &uv_c);

        let mut output_buffer: TriangleBuffer<12> = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, &plane_left, uv_triplet, &mut output_buffer);
        // one result on the left
        assert_eq!(output_buffer.count, 1);

        output_buffer.clear();

        // no result on the right
        clip_triangle_to_plane(&pa, &pb, &pc, &plane_right, uv_triplet, &mut output_buffer);

        assert_eq!(output_buffer.count, 0);
    }

    #[test]
    fn test_one_vertex_inside_plane_left() {
        // one vertex inside
        let pa = vec4(-0.5, 0.5, 0.5, 1.0);

        // two vertex outside left plane
        let pb = vec4(-2.0, -0.5, 0.5, 1.0);
        let pc = vec4(-2.5, 0.5, 0.5, 1.0);

        let uv_a = vec2(0.0, 0.0);
        let uv_b = vec2(1.0, 0.0);
        let uv_c = vec2(0.0, 1.0);

        let uv_triplet = (&uv_a, &uv_b, &uv_c);

        // left plane
        let plane = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0

        let mut output_buffer: TriangleBuffer<12> = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, &plane, uv_triplet, &mut output_buffer);
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

        let uv_a = vec2(0.0, 0.0);
        let uv_b = vec2(1.0, 0.0);
        let uv_c = vec2(0.0, 1.0);

        let uv_triplet = (&uv_a, &uv_b, &uv_c);

        // left plane
        let plane = vec4(1.0, 0.0, 0.0, 1.0); // plane: x + 1 >= 0

        let mut output_buffer: TriangleBuffer<12> = TriangleBuffer::new();
        clip_triangle_to_plane(&pa, &pb, &pc, &plane, uv_triplet, &mut output_buffer);

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
