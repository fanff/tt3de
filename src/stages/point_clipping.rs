use nalgebra_glm::Vec4;

/// Clips a point to the clip space.
/// # Arguments
/// * `point` - The point to clip.
/// # Returns
/// * `bool` - True if the point is in the clip space, false otherwise.
pub fn clip_point_to_clip_space(point: &Vec4) -> bool {
    point.x >= -point.w
        && point.x <= point.w
        && point.y >= -point.w
        && point.y <= point.w
        && point.z >= 0.0
        && point.z <= point.w
}
